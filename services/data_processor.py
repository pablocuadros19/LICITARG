"""Normalización, unificación y cruce geográfico de datos."""

import pandas as pd
from pathlib import Path

from config import DATA_PROCESSED, SUCURSALES
from services.data_loader import (
    cargar_adjudicaciones,
    cargar_contratar,
    cargar_sipro,
    cargar_sociedades,
)
from utils.formatters import normalizar_cuit, normalizar_provincia, normalizar_localidad


def _unificar_adjudicaciones_nuevas(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica esquema de adjudicaciones 2017-2020 (formato nuevo)."""
    cols_map = {
        "CUIT": "cuit_raw",
        "Descripción Proveedor": "razon_social",
        "Monto": "monto",
        "Moneda": "moneda",
        "Fecha de Adjudicación": "fecha_adjudicacion",
        "Rubros": "rubros",
        "Descripcion SAF": "organismo",
        "Tipo de Procedimiento": "tipo_procedimiento",
        "Ejercicio": "ejercicio",
    }
    # Renombrar solo columnas que existen
    cols_existentes = {k: v for k, v in cols_map.items() if k in df.columns}
    resultado = df.rename(columns=cols_existentes)
    return resultado


def _unificar_adjudicaciones_legacy(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica esquema de adjudicaciones 2015-2016 (formato legacy)."""
    cols_map = {
        "cuit": "cuit_raw",
        "prov_razon_social": "razon_social",
        "monto_adjudicacion": "monto",
        "fecha_acto": "fecha_adjudicacion",
        "rubro_contratacion_desc": "rubros",
        "uoc_desc": "organismo",
        "proc_ejercicio": "ejercicio",
    }
    cols_existentes = {k: v for k, v in cols_map.items() if k in df.columns}
    resultado = df.rename(columns=cols_existentes)
    if "moneda" not in resultado.columns:
        resultado["moneda"] = "ARS"
    if "tipo_procedimiento" not in resultado.columns:
        resultado["tipo_procedimiento"] = ""
    return resultado


def _leer_csv(path: Path) -> pd.DataFrame:
    """Lee CSV con fallback de encoding."""
    for enc in ["utf-8", "latin-1"]:
        try:
            return pd.read_csv(path, dtype=str, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, dtype=str, encoding="latin-1", errors="replace")


def unificar_adjudicaciones() -> pd.DataFrame:
    """Carga y unifica todas las adjudicaciones en un esquema común."""
    from config import DATA_RAW
    print("Unificando adjudicaciones...")

    COLUMNAS_FINALES = [
        "cuit_raw", "razon_social", "monto", "moneda",
        "fecha_adjudicacion", "rubros", "organismo",
        "tipo_procedimiento", "ejercicio", "fuente", "anio_fuente",
    ]

    dfs = []
    adj_dir = DATA_RAW / "adjudicaciones"

    for csv_path in sorted(adj_dir.glob("adjudicaciones-*.csv")):
        anio_str = csv_path.stem.replace("adjudicaciones-", "")
        try:
            anio = int(anio_str)
        except ValueError:
            continue

        df = _leer_csv(csv_path)
        df.columns = [c.strip() for c in df.columns]

        if anio <= 2016:
            unificado = _unificar_adjudicaciones_legacy(df)
        else:
            unificado = _unificar_adjudicaciones_nuevas(df)

        # Garantizar columnas finales
        for col in COLUMNAS_FINALES:
            if col not in unificado.columns:
                unificado[col] = ""

        unificado["anio_fuente"] = str(anio)
        unificado["fuente"] = "COMPR.AR"
        dfs.append(unificado[COLUMNAS_FINALES])

    if not dfs:
        raise FileNotFoundError("No se encontraron archivos de adjudicaciones")

    df = pd.concat(dfs, ignore_index=True)

    # Normalizar CUIT
    df["cuit"] = df["cuit_raw"].apply(normalizar_cuit)
    df = df[df["cuit"] != ""].copy()
    df["razon_social"] = df["razon_social"].str.strip()
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce")

    print(f"  Adjudicaciones unificadas: {len(df)} registros, {df['cuit'].nunique()} CUITs únicos")
    return df


def agregar_contratar(df_adj: pd.DataFrame) -> pd.DataFrame:
    """Agrega datos de CONTRAT.AR al dataset de adjudicaciones."""
    print("Agregando CONTRAT.AR...")
    try:
        df_c = cargar_contratar()
    except FileNotFoundError:
        print("  CONTRAT.AR no disponible, saltando.")
        return df_adj

    df_c = df_c.rename(columns={
        "oferente_cuit": "cuit_raw",
        "oferente_razon_social": "razon_social",
        "oferta_monto": "monto",
        "organismo_nombre": "organismo",
    })
    df_c["cuit"] = df_c["cuit_raw"].apply(normalizar_cuit)
    df_c["moneda"] = "ARS"
    df_c["fecha_adjudicacion"] = ""
    df_c["rubros"] = ""
    df_c["tipo_procedimiento"] = "Obra Pública"
    df_c["ejercicio"] = ""
    df_c["anio_fuente"] = ""
    df_c["monto"] = pd.to_numeric(df_c["monto"], errors="coerce")
    df_c = df_c[df_c["cuit"] != ""].copy()

    columnas = df_adj.columns.tolist()
    for col in columnas:
        if col not in df_c.columns:
            df_c[col] = ""

    resultado = pd.concat([df_adj, df_c[columnas]], ignore_index=True)
    print(f"  +{len(df_c)} registros de CONTRAT.AR -> total {len(resultado)}")
    return resultado


def cruzar_con_sociedades(df_adj: pd.DataFrame) -> pd.DataFrame:
    """Cruza adjudicaciones con Registro de Sociedades para obtener domicilio."""
    print("Cruzando con Registro Nacional de Sociedades...")
    try:
        df_soc = cargar_sociedades()
    except FileNotFoundError:
        print("  Sociedades no disponible, intentando SIPRO...")
        return cruzar_con_sipro(df_adj)

    # Normalizar CUIT en sociedades
    df_soc["cuit_norm"] = df_soc["cuit"].apply(normalizar_cuit)
    df_soc = df_soc[df_soc["cuit_norm"] != ""].copy()

    # Tomar solo columnas de domicilio, deduplicar por CUIT
    cols_geo = [
        "cuit_norm", "dom_fiscal_provincia", "dom_fiscal_localidad",
        "dom_fiscal_calle", "dom_fiscal_numero", "dom_fiscal_cp",
        "dom_fiscal_estado_domicilio", "tipo_societario",
        "actividad_codigo", "actividad_descripcion",
        "fecha_hora_contrato_social", "fecha_hora_actualizacion",
    ]
    cols_disponibles = [c for c in cols_geo if c in df_soc.columns]
    # Deduplicar por CUIT — cada empresa puede tener varias actividades, tomar la principal (orden 1)
    if "actividad_codigo" in df_soc.columns:
        df_soc_dedup = df_soc.sort_values("actividad_codigo").drop_duplicates(subset=["cuit_norm"], keep="first")
    else:
        df_soc_dedup = df_soc
    df_geo = df_soc_dedup[cols_disponibles].drop_duplicates(subset=["cuit_norm"], keep="first")

    # Merge
    resultado = df_adj.merge(df_geo, left_on="cuit", right_on="cuit_norm", how="left")

    matched = resultado["dom_fiscal_provincia"].notna().sum()
    print(f"  Match sociedades: {matched}/{len(resultado)} ({matched/len(resultado)*100:.1f}%)")

    # Completar con SIPRO lo que no matcheó
    resultado = _completar_con_sipro(resultado)

    return resultado


def cruzar_con_sipro(df_adj: pd.DataFrame) -> pd.DataFrame:
    """Cruza con SIPRO como fuente alternativa de geo."""
    print("Cruzando con SIPRO...")
    try:
        df_sipro = cargar_sipro()
    except FileNotFoundError:
        print("  SIPRO no disponible.")
        return df_adj

    df_sipro["cuit_norm"] = df_sipro["cuit___nit"].apply(normalizar_cuit)
    df_sipro = df_sipro[df_sipro["cuit_norm"] != ""].copy()

    cols = ["cuit_norm", "localidad", "provincia", "codigo_postal", "rubros"]
    cols_disponibles = [c for c in cols if c in df_sipro.columns]
    df_sipro_geo = df_sipro[cols_disponibles].drop_duplicates(subset=["cuit_norm"], keep="first")
    df_sipro_geo = df_sipro_geo.rename(columns={
        "localidad": "dom_fiscal_localidad",
        "provincia": "dom_fiscal_provincia",
        "codigo_postal": "dom_fiscal_cp",
    })

    resultado = df_adj.merge(df_sipro_geo, left_on="cuit", right_on="cuit_norm", how="left")
    matched = resultado["dom_fiscal_provincia"].notna().sum()
    print(f"  Match SIPRO: {matched}/{len(resultado)} ({matched/len(resultado)*100:.1f}%)")
    return resultado


def _completar_con_sipro(df: pd.DataFrame) -> pd.DataFrame:
    """Completa registros sin match de sociedades usando SIPRO."""
    sin_geo = df["dom_fiscal_provincia"].isna()
    if sin_geo.sum() == 0:
        return df

    print(f"  Completando {sin_geo.sum()} registros sin geo con SIPRO...")
    try:
        df_sipro = cargar_sipro()
    except FileNotFoundError:
        return df

    df_sipro["cuit_norm"] = df_sipro["cuit___nit"].apply(normalizar_cuit)
    df_sipro = df_sipro[df_sipro["cuit_norm"] != ""].copy()
    sipro_geo = df_sipro[["cuit_norm", "localidad", "provincia", "codigo_postal"]].drop_duplicates(
        subset=["cuit_norm"], keep="first"
    )

    # Hacer merge solo para los que no tienen geo
    faltantes = df[sin_geo][["cuit"]].drop_duplicates()
    completados = faltantes.merge(sipro_geo, left_on="cuit", right_on="cuit_norm", how="inner")

    if len(completados) > 0:
        geo_map = completados.set_index("cuit")
        mask = sin_geo & df["cuit"].isin(geo_map.index)
        df.loc[mask, "dom_fiscal_localidad"] = df.loc[mask, "cuit"].map(geo_map["localidad"])
        df.loc[mask, "dom_fiscal_provincia"] = df.loc[mask, "cuit"].map(geo_map["provincia"])
        df.loc[mask, "dom_fiscal_cp"] = df.loc[mask, "cuit"].map(geo_map["codigo_postal"])
        print(f"  Completados con SIPRO: {mask.sum()} registros")

    return df


def asignar_sucursal(df: pd.DataFrame) -> pd.DataFrame:
    """Asigna sucursal según localidad del domicilio fiscal."""
    print("Asignando sucursales...")

    df["provincia_norm"] = df["dom_fiscal_provincia"].apply(
        lambda x: normalizar_provincia(str(x)) if pd.notna(x) else ""
    )
    df["localidad_norm"] = df["dom_fiscal_localidad"].apply(
        lambda x: normalizar_localidad(str(x)) if pd.notna(x) else ""
    )

    df["sucursal"] = ""
    for nombre_suc, config_suc in SUCURSALES.items():
        localidades_upper = [normalizar_localidad(loc) for loc in config_suc["localidades"]]
        mask = df["localidad_norm"].isin(localidades_upper)
        df.loc[mask, "sucursal"] = nombre_suc

    asignados = (df["sucursal"] != "").sum()
    print(f"  Asignados a sucursal: {asignados}/{len(df)} ({asignados/len(df)*100:.1f}%)")
    for suc in SUCURSALES:
        n = (df["sucursal"] == suc).sum()
        if n > 0:
            print(f"    {suc}: {n}")

    return df


def construir_tabla_proveedores(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega datos por proveedor: monto total, cantidad, organismos."""
    print("Construyendo tabla de proveedores...")

    # Agrupar por CUIT
    agg = df.groupby("cuit").agg(
        razon_social=("razon_social", "first"),
        monto_total=("monto", "sum"),
        cantidad_adjudicaciones=("monto", "count"),
        monto_promedio=("monto", "mean"),
        organismos=("organismo", lambda x: "; ".join(sorted(set(str(v) for v in x if pd.notna(v) and str(v).strip())))),
        rubros=("rubros", lambda x: "; ".join(sorted(set(str(v) for v in x if pd.notna(v) and str(v).strip())))),
        fuentes=("fuente", lambda x: "; ".join(sorted(set(str(v) for v in x if pd.notna(v))))),
        dom_fiscal_provincia=("dom_fiscal_provincia", "first"),
        dom_fiscal_localidad=("dom_fiscal_localidad", "first"),
        dom_fiscal_calle=("dom_fiscal_calle", "first") if "dom_fiscal_calle" in df.columns else ("dom_fiscal_provincia", "first"),
        dom_fiscal_numero=("dom_fiscal_numero", "first") if "dom_fiscal_numero" in df.columns else ("dom_fiscal_provincia", "first"),
        dom_fiscal_cp=("dom_fiscal_cp", "first"),
        dom_fiscal_estado_domicilio=("dom_fiscal_estado_domicilio", "first") if "dom_fiscal_estado_domicilio" in df.columns else ("dom_fiscal_provincia", "first"),
        actividad_codigo=("actividad_codigo", "first") if "actividad_codigo" in df.columns else ("dom_fiscal_provincia", "first"),
        actividad_descripcion=("actividad_descripcion", "first") if "actividad_descripcion" in df.columns else ("dom_fiscal_provincia", "first"),
        fecha_contrato_social=("fecha_hora_contrato_social", "first") if "fecha_hora_contrato_social" in df.columns else ("dom_fiscal_provincia", "first"),
        fecha_actualizacion=("fecha_hora_actualizacion", "first") if "fecha_hora_actualizacion" in df.columns else ("dom_fiscal_provincia", "first"),
        sucursal=("sucursal", "first"),
    ).reset_index()

    # Si no había columnas de calle/numero, limpiar
    if "dom_fiscal_calle" not in df.columns:
        agg["dom_fiscal_calle"] = ""
        agg["dom_fiscal_numero"] = ""

    agg = agg.sort_values("monto_total", ascending=False)
    print(f"  Proveedores únicos: {len(agg)}")
    print(f"  Con sucursal asignada: {(agg['sucursal'] != '').sum()}")
    return agg


def procesar_todo() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pipeline completo: descarga → normalización → cruce → asignación."""
    print("=" * 60)
    print("PIPELINE DE PROCESAMIENTO LICITARG")
    print("=" * 60)

    # 1. Unificar adjudicaciones
    df_adj = unificar_adjudicaciones()

    # 2. Agregar CONTRAT.AR
    df_adj = agregar_contratar(df_adj)

    # 3. Cruzar con sociedades/SIPRO para obtener domicilio
    df_adj = cruzar_con_sociedades(df_adj)

    # 4. Asignar sucursal por localidad
    df_adj = asignar_sucursal(df_adj)

    # 5. Construir tabla de proveedores
    df_prov = construir_tabla_proveedores(df_adj)

    # 6. Guardar resultados
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    adj_path = DATA_PROCESSED / "adjudicaciones.parquet"
    prov_path = DATA_PROCESSED / "proveedores.parquet"

    df_adj.to_parquet(adj_path, index=False)
    df_prov.to_parquet(prov_path, index=False)
    print(f"\nGuardados:")
    print(f"  {adj_path} ({len(df_adj)} registros)")
    print(f"  {prov_path} ({len(df_prov)} proveedores)")

    return df_adj, df_prov


if __name__ == "__main__":
    procesar_todo()
