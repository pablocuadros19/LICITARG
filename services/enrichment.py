"""Enriquecimiento de prospectos con datos BCRA."""

import os
import time
import httpx
import pandas as pd
from dotenv import load_dotenv

from utils.formatters import normalizar_cuit, formatear_cuit

load_dotenv()

BCRA_TOKEN = os.getenv("BCRA_TOKEN", "")
_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}
if BCRA_TOKEN:
    _HEADERS["Authorization"] = f"BEARER {BCRA_TOKEN}"

SITUACION_TEXTOS = {
    0: "Sin deuda",
    1: "Normal",
    2: "Con seguimiento especial",
    3: "Con problemas",
    4: "Alto riesgo de insolvencia",
    5: "Irrecuperable",
    6: "Sin información",
}


def _hacer_request(url: str, max_reintentos: int = 3) -> httpx.Response | None:
    for intento in range(max_reintentos + 1):
        try:
            with httpx.Client(verify=False, timeout=15) as client:
                r = client.get(url, headers=_HEADERS)
                if r.status_code == 429:
                    time.sleep(5 * (intento + 1))
                    continue
                return r
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError):
            if intento < max_reintentos:
                time.sleep(3 * (intento + 1))
                continue
    return None


def consultar_bcra_deudores(cuit: str) -> dict:
    cuit = normalizar_cuit(cuit)
    if not cuit:
        return {"error": "CUIT inválido"}

    url = f"https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/{cuit}"
    r = _hacer_request(url)

    if r is None:
        return {"error": "No se pudo conectar con BCRA"}
    if r.status_code == 404:
        return {"sin_deuda": True}
    if r.status_code == 503:
        return {"error": "API BCRA no disponible (503 — intente más tarde)"}
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}"}

    try:
        data = r.json()
    except Exception:
        return {"error": "Error parseando respuesta BCRA"}

    return _parsear_respuesta_bcra(data)


def _parsear_respuesta_bcra(data: dict) -> dict:
    resultado = {
        "sin_deuda": False,
        "periodo": "",
        "entidades": [],
        "situacion_max": 0,
        "deuda_total": 0.0,
    }
    try:
        periodos = data.get("results", {}).get("periodos", [])
        if not periodos:
            resultado["sin_deuda"] = True
            return resultado

        ultimo = periodos[-1]
        resultado["periodo"] = str(ultimo.get("periodo", ""))
        for ent in ultimo.get("entidades", []):
            sit = ent.get("situacion", 0)
            monto = float(ent.get("monto", 0) or 0)
            resultado["entidades"].append({
                "nombre": ent.get("entidad", ""),
                "situacion": sit,
                "monto": monto,
            })
            if sit > resultado["situacion_max"]:
                resultado["situacion_max"] = sit
            resultado["deuda_total"] += monto
    except (KeyError, TypeError, ValueError):
        pass
    return resultado


def consultar_uno(cuit: str) -> dict:
    """Consulta BCRA para un CUIT individual y retorna dict listo para UI."""
    resultado = consultar_bcra_deudores(cuit)
    if resultado.get("sin_deuda"):
        return {
            "cuit": formatear_cuit(cuit),
            "estado": "Sin deuda registrada",
            "situacion_max": 0,
            "deuda_total": 0.0,
            "periodo": "",
            "entidades": [],
        }
    if resultado.get("error"):
        return {
            "cuit": formatear_cuit(cuit),
            "estado": resultado["error"],
            "situacion_max": -1,
            "deuda_total": 0.0,
            "periodo": "",
            "entidades": [],
        }
    sit = resultado.get("situacion_max", 0)
    return {
        "cuit": formatear_cuit(cuit),
        "estado": SITUACION_TEXTOS.get(sit, f"Situación {sit}"),
        "situacion_max": sit,
        "deuda_total": resultado.get("deuda_total", 0.0),
        "periodo": resultado.get("periodo", ""),
        "entidades": resultado.get("entidades", []),
    }


def enriquecer_lote(df: pd.DataFrame, col_cuit: str = "cuit",
                    max_consultas: int = 100, delay: float = 1.0) -> pd.DataFrame:
    df = df.copy()
    df["bcra_situacion"] = ""
    df["bcra_deuda_total"] = 0.0
    df["bcra_periodo"] = ""
    df["bcra_entidades"] = ""
    df["bcra_consultado"] = False

    cuits_unicos = df[col_cuit].dropna().unique()[:max_consultas]
    cache = {}

    for i, cuit in enumerate(cuits_unicos):
        if i % 10 == 0:
            print(f"  {i}/{len(cuits_unicos)}...")
        cache[cuit] = consultar_bcra_deudores(cuit)
        time.sleep(delay)

    for idx, row in df.iterrows():
        cuit = row[col_cuit]
        if cuit not in cache:
            continue
        r = cache[cuit]
        df.at[idx, "bcra_consultado"] = True
        if r.get("sin_deuda"):
            df.at[idx, "bcra_situacion"] = "Sin deuda"
        elif r.get("error"):
            df.at[idx, "bcra_situacion"] = f"Error: {r['error']}"
        else:
            sit = r.get("situacion_max", 0)
            df.at[idx, "bcra_situacion"] = SITUACION_TEXTOS.get(sit, str(sit))
            df.at[idx, "bcra_deuda_total"] = r.get("deuda_total", 0.0)
            df.at[idx, "bcra_periodo"] = r.get("periodo", "")
            nombres = [e["nombre"] for e in r.get("entidades", [])[:3]]
            df.at[idx, "bcra_entidades"] = "; ".join(nombres)
    return df
