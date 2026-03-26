"""Lógica de análisis y ranking de prospectos por sucursal."""

import pandas as pd
from pathlib import Path

from config import DATA_PROCESSED, SUCURSALES
from utils.formatters import formatear_monto, formatear_cuit


def cargar_proveedores() -> pd.DataFrame:
    """Carga tabla de proveedores procesados desde parquet."""
    path = DATA_PROCESSED / "proveedores.parquet"
    if not path.exists():
        raise FileNotFoundError(
            "No se encontró proveedores.parquet. Ejecutar data_processor.procesar_todo() primero."
        )
    return pd.read_parquet(path)


def cargar_adjudicaciones() -> pd.DataFrame:
    """Carga tabla de adjudicaciones desde parquet."""
    path = DATA_PROCESSED / "adjudicaciones.parquet"
    if not path.exists():
        raise FileNotFoundError("No se encontró adjudicaciones.parquet.")
    return pd.read_parquet(path)


def prospectos_por_sucursal(sucursal: str, df: pd.DataFrame = None,
                             orden: str = "monto_total",
                             top_n: int = 50) -> pd.DataFrame:
    """
    Retorna los mejores prospectos para una sucursal dada.
    orden: 'monto_total' | 'cantidad_adjudicaciones'
    """
    if df is None:
        df = cargar_proveedores()

    resultado = df[df["sucursal"] == sucursal].copy()

    if orden in resultado.columns:
        resultado = resultado.sort_values(orden, ascending=False)

    return resultado.head(top_n).reset_index(drop=True)


def resumen_sucursal(sucursal: str, df: pd.DataFrame = None) -> dict:
    """Métricas resumen para una sucursal."""
    if df is None:
        df = cargar_proveedores()

    prov = df[df["sucursal"] == sucursal]

    return {
        "sucursal": sucursal,
        "total_prospectos": len(prov),
        "monto_total": prov["monto_total"].sum() if len(prov) > 0 else 0,
        "monto_promedio": prov["monto_total"].mean() if len(prov) > 0 else 0,
        "top_rubro": _top_valor(prov, "rubros"),
        "top_organismo": _top_valor(prov, "organismos"),
    }


def _top_valor(df: pd.DataFrame, col: str) -> str:
    """Retorna el valor más frecuente en una columna de strings separados por ';'."""
    if col not in df.columns or df.empty:
        return ""
    conteo = {}
    for val in df[col].dropna():
        for item in str(val).split(";"):
            item = item.strip()
            if item and item.lower() not in ("", "nan"):
                conteo[item] = conteo.get(item, 0) + 1
    if not conteo:
        return ""
    return max(conteo, key=conteo.get)


def resumen_global(df: pd.DataFrame = None) -> dict:
    """Métricas globales del dataset."""
    if df is None:
        df = cargar_proveedores()

    return {
        "total_proveedores": len(df),
        "con_sucursal": (df["sucursal"] != "").sum(),
        "monto_total": df["monto_total"].sum(),
        "sucursales": {s: int((df["sucursal"] == s).sum()) for s in SUCURSALES},
    }


def adjudicaciones_proveedor(cuit: str, df_adj: pd.DataFrame = None) -> pd.DataFrame:
    """Retorna todas las adjudicaciones de un proveedor específico."""
    if df_adj is None:
        df_adj = cargar_adjudicaciones()

    resultado = df_adj[df_adj["cuit"] == cuit].copy()
    resultado = resultado.sort_values("anio_fuente", ascending=False)
    return resultado


def formatear_fila_prospecto(row: pd.Series) -> dict:
    """Convierte una fila de proveedor a dict formateado para mostrar en UI."""
    domicilio_parts = []
    if pd.notna(row.get("dom_fiscal_calle")) and str(row.get("dom_fiscal_calle", "")).strip():
        domicilio_parts.append(str(row["dom_fiscal_calle"]).strip())
    if pd.notna(row.get("dom_fiscal_numero")) and str(row.get("dom_fiscal_numero", "")).strip():
        domicilio_parts.append(str(row["dom_fiscal_numero"]).strip())
    if pd.notna(row.get("dom_fiscal_localidad")) and str(row.get("dom_fiscal_localidad", "")).strip():
        domicilio_parts.append(str(row["dom_fiscal_localidad"]).strip())

    return {
        "cuit": formatear_cuit(str(row.get("cuit", ""))),
        "razon_social": str(row.get("razon_social", "")).strip(),
        "monto_total": formatear_monto(row.get("monto_total", 0)),
        "cantidad_adj": int(row.get("cantidad_adjudicaciones", 0)),
        "domicilio": ", ".join(domicilio_parts) if domicilio_parts else "Sin domicilio",
        "localidad": str(row.get("dom_fiscal_localidad", "")).strip(),
        "rubros": str(row.get("rubros", "")).strip()[:80],
        "organismos": str(row.get("organismos", "")).strip()[:80],
        "sucursal": str(row.get("sucursal", "")),
        "fuentes": str(row.get("fuentes", "")),
    }
