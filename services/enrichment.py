"""Enriquecimiento de prospectos con datos BCRA y búsqueda web."""

import time
import re
import pandas as pd
import requests

from utils.formatters import normalizar_cuit, formatear_cuit


def consultar_bcra_deudores(cuit: str) -> dict:
    """
    Consulta la Central de Deudores del BCRA para un CUIT.
    API pública, sin autenticación.
    Retorna dict con estado de deuda o error.
    """
    cuit = normalizar_cuit(cuit)
    if not cuit:
        return {"error": "CUIT inválido"}

    url = f"https://api.bcra.gob.ar/CentralDeDeudores/v1.0/Deudas/{cuit}"
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "LICITARG/1.0"})
        if resp.status_code == 404:
            return {"sin_deuda": True, "mensaje": "Sin deudas registradas"}
        if resp.status_code == 200:
            data = resp.json()
            return _parsear_respuesta_bcra(data)
        return {"error": f"HTTP {resp.status_code}"}
    except requests.RequestException as e:
        return {"error": str(e)}


def _parsear_respuesta_bcra(data: dict) -> dict:
    """Extrae info relevante de la respuesta BCRA."""
    resultado = {
        "sin_deuda": False,
        "periodo": "",
        "entidades": [],
        "situacion_max": 0,
        "deuda_total": 0.0,
    }

    try:
        resultados = data.get("results", {})
        periodos = resultados.get("periodos", [])

        if not periodos:
            resultado["sin_deuda"] = True
            return resultado

        # Tomar el período más reciente
        ultimo = periodos[-1]
        resultado["periodo"] = str(ultimo.get("periodo", ""))
        entidades = ultimo.get("entidades", [])

        for ent in entidades:
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


def enriquecer_lote(df: pd.DataFrame, col_cuit: str = "cuit",
                    max_consultas: int = 100, delay: float = 0.3) -> pd.DataFrame:
    """
    Enriquece un DataFrame con datos BCRA.
    Limita a max_consultas para no sobrecargar la API.
    """
    df = df.copy()
    df["bcra_situacion"] = ""
    df["bcra_deuda_total"] = 0.0
    df["bcra_periodo"] = ""
    df["bcra_entidades"] = ""
    df["bcra_consultado"] = False

    cuits_unicos = df[col_cuit].dropna().unique()[:max_consultas]
    resultados_cache = {}

    print(f"Consultando BCRA para {len(cuits_unicos)} CUITs...")
    for i, cuit in enumerate(cuits_unicos):
        if i % 10 == 0:
            print(f"  {i}/{len(cuits_unicos)}...")
        resultado = consultar_bcra_deudores(cuit)
        resultados_cache[cuit] = resultado
        time.sleep(delay)

    # Mapear resultados al df
    for idx, row in df.iterrows():
        cuit = row[col_cuit]
        if cuit not in resultados_cache:
            continue
        r = resultados_cache[cuit]
        df.at[idx, "bcra_consultado"] = True
        if r.get("sin_deuda"):
            df.at[idx, "bcra_situacion"] = "Sin deuda"
        elif r.get("error"):
            df.at[idx, "bcra_situacion"] = f"Error: {r['error']}"
        else:
            sit = r.get("situacion_max", 0)
            etiqueta = _etiqueta_situacion(sit)
            df.at[idx, "bcra_situacion"] = etiqueta
            df.at[idx, "bcra_deuda_total"] = r.get("deuda_total", 0.0)
            df.at[idx, "bcra_periodo"] = r.get("periodo", "")
            entidades = r.get("entidades", [])
            if entidades:
                nombres = [e["nombre"] for e in entidades[:3]]
                df.at[idx, "bcra_entidades"] = "; ".join(nombres)

    return df


def _etiqueta_situacion(sit: int) -> str:
    etiquetas = {
        0: "Sin deuda",
        1: "Normal",
        2: "Seguimiento especial",
        3: "Irrecuperable para el sector financiero",
        4: "Alto riesgo de insolvencia",
        5: "Irrecuperable",
        6: "Sin información",
    }
    return etiquetas.get(sit, f"Situacion {sit}")


def consultar_uno(cuit: str) -> dict:
    """Consulta BCRA para un CUIT individual y retorna dict completo."""
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
    return {
        "cuit": formatear_cuit(cuit),
        "estado": _etiqueta_situacion(resultado.get("situacion_max", 0)),
        "situacion_max": resultado.get("situacion_max", 0),
        "deuda_total": resultado.get("deuda_total", 0.0),
        "periodo": resultado.get("periodo", ""),
        "entidades": resultado.get("entidades", []),
    }
