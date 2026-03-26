"""LICITARG — Dashboard de prospectos proveedores del Estado."""

import streamlit as st
import pandas as pd

from config import SUCURSALES
from services.analytics import (
    cargar_proveedores,
    prospectos_por_sucursal,
    resumen_sucursal,
    resumen_global,
    adjudicaciones_proveedor,
    formatear_fila_prospecto,
)
from services.enrichment import consultar_uno
from utils.formatters import formatear_monto, formatear_cuit

# ─── Configuración de página ────────────────────────────────────────────────
st.set_page_config(
    page_title="LICITARG",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Estilos Banco Provincia ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;900&display=swap');

*, body, .stApp { font-family: 'Montserrat', sans-serif !important; }

/* Header */
.hero-header {
    background: linear-gradient(90deg, #fff 0%, #00A651 25%, #00B8D4 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 900;
    color: #fff;
    margin: 0;
    text-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.hero-sub {
    font-size: 0.9rem;
    color: rgba(255,255,255,0.9);
    letter-spacing: 2px;
    margin: 0.3rem 0 0 0;
    font-weight: 400;
}

/* Métricas */
.metric-card {
    background: #f7f9fc;
    border: 1px solid #e0e5ec;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-val {
    font-size: 1.8rem;
    font-weight: 700;
    color: #00A651;
    margin: 0;
}
.metric-lbl {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #555;
    margin: 0.2rem 0 0 0;
}

/* Prospecto card */
.prosp-card {
    background: #f7f9fc;
    border: 1px solid #e0e5ec;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.7rem;
    transition: border-color 0.2s;
}
.prosp-card:hover {
    border-color: #00A651;
    box-shadow: 0 2px 10px rgba(0,132,61,0.1);
}
.prosp-name {
    font-size: 1rem;
    font-weight: 700;
    color: #1a1a2e;
    margin: 0 0 0.3rem 0;
}
.prosp-cuit {
    font-size: 0.78rem;
    color: #999;
    font-family: monospace;
}
.prosp-monto {
    font-size: 1rem;
    font-weight: 700;
    color: #00A651;
}
.tag {
    display: inline-block;
    background: #e8f5ee;
    color: #00A651;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    margin: 0.15rem 0.1rem;
}
.tag-blue {
    background: #e8f3ff;
    color: #0078D4;
}

/* Situación BCRA */
.sit-verde { color: #00A651; font-weight: 600; }
.sit-amarillo { color: #F5A623; font-weight: 600; }
.sit-rojo { color: #D0021B; font-weight: 600; }

/* Sección destacada */
.seccion-dest {
    background: #f0f9f4;
    border: 1px solid #c8e6d5;
    border-left: 4px solid #00A651;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}

/* Divider */
.divider {
    height: 3px;
    background: linear-gradient(90deg, #00A651, #00B8D4);
    border-radius: 2px;
    margin: 1.2rem 0;
}
</style>
""", unsafe_allow_html=True)


# ─── Cache de datos ───────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Cargando base de prospectos...")
def _cargar_datos():
    try:
        df = cargar_proveedores()
        return df
    except FileNotFoundError:
        return None


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏛️ LICITARG")
    st.markdown("---")

    sucursales_lista = list(SUCURSALES.keys())
    sucursal_sel = st.selectbox(
        "Sucursal",
        sucursales_lista,
        help="Filtra prospectos por zona de influencia de la sucursal",
    )

    st.markdown("---")
    orden_sel = st.radio(
        "Ordenar por",
        ["Monto total", "Cantidad de adjudicaciones"],
        index=0,
    )
    orden_col = "monto_total" if orden_sel == "Monto total" else "cantidad_adjudicaciones"

    top_n = st.slider("Mostrar top N prospectos", min_value=10, max_value=200, value=50, step=10)

    st.markdown("---")
    buscar_cuit = st.text_input("Buscar por CUIT o Razón Social", placeholder="Ej: 30-12345678-9")

    st.markdown("---")
    if st.button("Reprocesar datos", help="Descarga y re-procesa todos los datos fuente"):
        with st.spinner("Procesando... (puede tardar 1-2 min)"):
            _cargar_datos.clear()
            from services.data_processor import procesar_todo
            procesar_todo()
            st.success("Datos actualizados.")
            st.rerun()


# ─── Carga de datos ───────────────────────────────────────────────────────────
df_prov = _cargar_datos()

if df_prov is None:
    st.error(
        "No se encontraron datos procesados. "
        "Ejecutá el pipeline primero: `python -c \"from services.data_processor import procesar_todo; procesar_todo()\"`"
    )
    st.stop()

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <p class="hero-title">LICITARG</p>
    <p class="hero-sub">PROVEEDORES DEL ESTADO • PROSPECCIÓN COMERCIAL</p>
</div>
""", unsafe_allow_html=True)

# ─── Métricas globales ────────────────────────────────────────────────────────
resumen = resumen_global(df_prov)
rsuc = resumen_sucursal(sucursal_sel, df_prov)

col1, col2, col3, col4, col5 = st.columns(5)

metricas = [
    (col1, str(resumen["total_proveedores"]), "Total proveedores"),
    (col2, str(resumen["con_sucursal"]), "Con zona asignada"),
    (col3, str(rsuc["total_prospectos"]), f"Prospectos {sucursal_sel}"),
    (col4, formatear_monto(rsuc["monto_total"]), f"Monto adjud. {sucursal_sel}"),
    (col5, formatear_monto(resumen["monto_total"]), "Monto total dataset"),
]

for col, val, lbl in metricas:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-val">{val}</p>
            <p class="metric-lbl">{lbl}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── Búsqueda libre ───────────────────────────────────────────────────────────
if buscar_cuit.strip():
    termino = buscar_cuit.strip().upper()
    cuit_limpio = termino.replace("-", "").replace(" ", "")
    mask = (
        df_prov["cuit"].str.contains(cuit_limpio, na=False) |
        df_prov["razon_social"].str.upper().str.contains(termino, na=False)
    )
    df_filtrado = df_prov[mask].head(20)
    st.markdown(f"#### Resultados para: *{buscar_cuit}* ({len(df_filtrado)} encontrados)")
else:
    df_filtrado = prospectos_por_sucursal(sucursal_sel, df_prov, orden=orden_col, top_n=top_n)
    st.markdown(f"#### Prospectos — Sucursal {sucursal_sel} (top {len(df_filtrado)})")

# ─── Tabla de prospectos ──────────────────────────────────────────────────────
if df_filtrado.empty:
    st.info("Sin prospectos para los filtros seleccionados.")
else:
    # Preparar columnas para tabla
    df_tabla = df_filtrado.copy()
    df_tabla["CUIT"] = df_tabla["cuit"].apply(formatear_cuit)
    df_tabla["Razón Social"] = df_tabla["razon_social"].str.strip()
    df_tabla["Monto Total"] = df_tabla["monto_total"].apply(lambda x: formatear_monto(x))
    df_tabla["Adj."] = df_tabla["cantidad_adjudicaciones"].fillna(0).astype(int)
    df_tabla["Localidad"] = df_tabla["dom_fiscal_localidad"].fillna("").str.strip()
    df_tabla["Rubros"] = df_tabla["rubros"].fillna("").str[:60]

    cols_mostrar = ["CUIT", "Razón Social", "Monto Total", "Adj.", "Localidad", "Rubros"]
    st.dataframe(
        df_tabla[cols_mostrar],
        use_container_width=True,
        height=400,
        hide_index=True,
    )

    # ─── Detalle de prospecto ─────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("#### Ficha del prospecto")

    opciones = ["— Seleccionar —"] + df_tabla["Razón Social"].tolist()
    seleccion = st.selectbox("Seleccioná un prospecto para ver el detalle", opciones)

    if seleccion != "— Seleccionar —":
        row_idx = df_tabla[df_tabla["Razón Social"] == seleccion].index[0]
        row = df_filtrado.loc[row_idx]
        fila = formatear_fila_prospecto(row)

        col_ficha, col_bcra = st.columns([3, 2])

        with col_ficha:
            st.markdown(f"""
            <div class="seccion-dest">
                <p class="prosp-name">{fila['razon_social']}</p>
                <p class="prosp-cuit">CUIT: {fila['cuit']}</p>
                <p class="prosp-monto">{fila['monto_total']}</p>
                <p style="font-size:0.82rem; color:#555; margin: 0.4rem 0 0.3rem 0;">
                    📍 {fila['domicilio']}
                </p>
                <p style="font-size:0.82rem; color:#555;">
                    📋 {fila['cantidad_adj']} adjudicaciones
                </p>
            </div>
            """, unsafe_allow_html=True)

            if fila["rubros"]:
                st.markdown("**Rubros:**")
                for r in fila["rubros"].split(";")[:5]:
                    if r.strip():
                        st.markdown(f'<span class="tag">{r.strip()}</span>', unsafe_allow_html=True)

            if fila["organismos"]:
                st.markdown("<br>**Organismos contratantes:**", unsafe_allow_html=True)
                for org in fila["organismos"].split(";")[:4]:
                    if org.strip():
                        st.markdown(f'<span class="tag tag-blue">{org.strip()}</span>', unsafe_allow_html=True)

            # Historial de adjudicaciones
            with st.expander("Ver historial de adjudicaciones"):
                try:
                    df_adj_hist = adjudicaciones_proveedor(str(row["cuit"]))
                    if not df_adj_hist.empty:
                        hist = df_adj_hist[["anio_fuente", "organismo", "monto", "rubros", "fuente"]].copy()
                        hist["monto"] = hist["monto"].apply(lambda x: formatear_monto(x))
                        hist.columns = ["Año", "Organismo", "Monto", "Rubros", "Fuente"]
                        st.dataframe(hist, use_container_width=True, hide_index=True)
                    else:
                        st.info("Sin historial detallado.")
                except Exception as e:
                    st.warning(f"No se pudo cargar historial: {e}")

        with col_bcra:
            st.markdown("**Situación BCRA**")
            st.markdown("*Central de Deudores del BCRA*")

            bcra_key = f"bcra_{row['cuit']}"
            if bcra_key not in st.session_state:
                if st.button("Consultar BCRA", key=f"btn_{row['cuit']}"):
                    with st.spinner("Consultando..."):
                        resultado = consultar_uno(str(row["cuit"]))
                        st.session_state[bcra_key] = resultado
                        st.rerun()
            else:
                resultado = st.session_state[bcra_key]
                sit = resultado.get("situacion_max", -1)

                if sit == 0:
                    clase = "sit-verde"
                    icono = "✅"
                elif sit == 1:
                    clase = "sit-verde"
                    icono = "✅"
                elif sit == 2:
                    clase = "sit-amarillo"
                    icono = "⚠️"
                else:
                    clase = "sit-rojo"
                    icono = "🔴"

                st.markdown(f"""
                <div class="metric-card" style="text-align:left; margin-bottom:0.8rem;">
                    <p style="font-size:1.3rem; margin:0;">{icono} <span class="{clase}">{resultado['estado']}</span></p>
                    <p style="font-size:0.75rem; color:#999; margin:0.2rem 0 0 0;">
                        Período: {resultado.get('periodo', '-')}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if resultado.get("deuda_total", 0) > 0:
                    st.metric("Deuda total reportada", formatear_monto(resultado["deuda_total"]))

                entidades = resultado.get("entidades", [])
                if entidades:
                    st.markdown("**Entidades con deuda:**")
                    for ent in entidades[:5]:
                        sit_ent = ent.get("situacion", 0)
                        monto_ent = formatear_monto(ent.get("monto", 0))
                        clase_ent = "sit-verde" if sit_ent <= 1 else ("sit-amarillo" if sit_ent == 2 else "sit-rojo")
                        st.markdown(
                            f'<p style="font-size:0.82rem; margin:0.2rem 0;">'
                            f'<span class="{clase_ent}">Sit. {sit_ent}</span> — '
                            f'{ent.get("nombre", "")} ({monto_ent})</p>',
                            unsafe_allow_html=True,
                        )

                if st.button("Actualizar consulta BCRA", key=f"refresh_{row['cuit']}"):
                    del st.session_state[bcra_key]
                    st.rerun()

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="divider"></div>
<p style="text-align:center; font-size:0.72rem; color:#999;">
    LICITARG v0.1 — Datos: COMPR.AR / CONTRAT.AR / SIPRO / BCRA — Solo uso interno
</p>
""", unsafe_allow_html=True)
