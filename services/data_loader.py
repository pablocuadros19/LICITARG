"""Descarga y carga de datos desde fuentes públicas."""

import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

from config import (
    ADJUDICACIONES_URLS,
    CONTRATAR_URL,
    DATA_RAW,
    SIPRO_URL,
)


def _descargar_csv(url: str, destino: Path, encoding: str = "utf-8") -> Path:
    """Descarga un CSV si no existe localmente."""
    if destino.exists():
        print(f"  Ya existe: {destino.name}")
        return destino

    print(f"  Descargando {destino.name}...")
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(resp.content)
    print(f"  OK: {destino.name} ({len(resp.content) // 1024} KB)")
    return destino


def descargar_adjudicaciones() -> list[Path]:
    """Descarga CSVs de adjudicaciones nacionales 2015-2020."""
    print("Descargando adjudicaciones nacionales...")
    destino_dir = DATA_RAW / "adjudicaciones"
    destino_dir.mkdir(parents=True, exist_ok=True)

    archivos = []
    for anio, url in ADJUDICACIONES_URLS.items():
        destino = destino_dir / f"adjudicaciones-{anio}.csv"
        _descargar_csv(url, destino)
        archivos.append(destino)
    return archivos


def descargar_contratar() -> Path:
    """Descarga CSV de CONTRAT.AR (obra pública)."""
    print("Descargando CONTRAT.AR...")
    destino = DATA_RAW / "contratar" / "onc-contratar-ofertas.csv"
    return _descargar_csv(CONTRATAR_URL, destino)


def descargar_sipro() -> Path:
    """Descarga CSV de proveedores SIPRO."""
    print("Descargando SIPRO proveedores...")
    destino = DATA_RAW / "sipro" / "proveedores.csv"
    return _descargar_csv(SIPRO_URL, destino)


def descargar_sociedades_sample() -> Path:
    """Descarga el muestreo (1000 registros) del Registro Nacional de Sociedades.

    El dataset completo es un ZIP grande. Para el MVP usamos el muestreo
    para validar el esquema y luego se baja el ZIP completo manualmente.
    """
    print("Descargando muestreo Registro Sociedades...")
    url = "https://datos.jus.gob.ar/dataset/ee83de85-4305-4c53-9a9f-fd3d15e42c36/resource/6096331b-0511-4728-b01b-6c6b535f4c2b/download/registro-nacional-sociedades-muestreo.csv"
    destino = DATA_RAW / "sociedades" / "sociedades-muestreo.csv"
    return _descargar_csv(url, destino)


def cargar_adjudicaciones() -> pd.DataFrame:
    """Carga y consolida todos los CSVs de adjudicaciones nacionales."""
    carpeta = DATA_RAW / "adjudicaciones"
    archivos = sorted(carpeta.glob("adjudicaciones-*.csv"))
    if not archivos:
        raise FileNotFoundError("No hay CSVs de adjudicaciones. Ejecutá descargar_adjudicaciones() primero.")

    dfs = []
    for archivo in archivos:
        try:
            df = pd.read_csv(archivo, encoding="utf-8", dtype=str)
        except UnicodeDecodeError:
            df = pd.read_csv(archivo, encoding="latin-1", dtype=str)
        # Extraer año del nombre de archivo
        anio = archivo.stem.split("-")[-1]
        df["anio_fuente"] = anio
        df["fuente"] = "COMPR.AR"
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def cargar_contratar() -> pd.DataFrame:
    """Carga CSV de CONTRAT.AR."""
    archivo = DATA_RAW / "contratar" / "onc-contratar-ofertas.csv"
    if not archivo.exists():
        raise FileNotFoundError("No existe el CSV de CONTRAT.AR. Ejecutá descargar_contratar() primero.")
    try:
        df = pd.read_csv(archivo, encoding="utf-8", dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(archivo, encoding="latin-1", dtype=str)
    df["fuente"] = "CONTRAT.AR"
    return df


def cargar_sipro() -> pd.DataFrame:
    """Carga CSV de proveedores SIPRO."""
    archivo = DATA_RAW / "sipro" / "proveedores.csv"
    if not archivo.exists():
        raise FileNotFoundError("No existe el CSV de SIPRO. Ejecutá descargar_sipro() primero.")
    try:
        df = pd.read_csv(archivo, encoding="utf-8", dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(archivo, encoding="latin-1", dtype=str)
    return df


def cargar_sociedades() -> pd.DataFrame:
    """Carga el Registro Nacional de Sociedades — solo BA/CABA."""
    carpeta = DATA_RAW / "sociedades"

    # Prioridad: archivo filtrado BA/CABA > cualquier otro CSV
    ba_caba = carpeta / "sociedades-ba-caba.csv"
    if ba_caba.exists():
        return pd.read_csv(ba_caba, dtype=str, encoding="utf-8")

    # Fallback: muestreo
    muestreo = carpeta / "sociedades-muestreo.csv"
    if muestreo.exists():
        return pd.read_csv(muestreo, dtype=str, encoding="utf-8")

    raise FileNotFoundError("No hay datos de sociedades. Ejecutá descargar_sociedades_sample() primero.")


def descargar_todo():
    """Descarga todas las fuentes del MVP."""
    descargar_adjudicaciones()
    descargar_contratar()
    descargar_sipro()
    descargar_sociedades_sample()
    print("\nDescarga completa.")


if __name__ == "__main__":
    descargar_todo()
