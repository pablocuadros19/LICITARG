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
from ui.theme import inject_css
from ui.components import (
    render_header,
    render_sidebar_brand,
    render_metric_card,
    render_perrito_loader,
    render_footer,
)

# ─── Configuración de página ────────────────────────────────────────────────
st.set_page_config(
    page_title="LICITARG",
    page_icon="assets/logolic.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


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
    render_sidebar_brand()

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
        render_perrito_loader("Olfateando proveedores...")
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
render_header()

# ─── Métricas globales ────────────────────────────────────────────────────────
resumen = resumen_global(df_prov)
rsuc = resumen_sucursal(sucursal_sel, df_prov)

col1, col2, col3, col4, col5 = st.columns(5)

render_metric_card(str(resumen["total_proveedores"]), "Total proveedores", col1)
render_metric_card(str(resumen["con_sucursal"]), "Con zona asignada", col2)
render_metric_card(str(rsuc["total_prospectos"]), f"Prospectos {sucursal_sel}", col3)
render_metric_card(formatear_monto(rsuc["monto_total"]), f"Monto adjud. {sucursal_sel}", col4)
render_metric_card(formatear_monto(resumen["monto_total"]), "Monto total dataset", col5)

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
    df_tabla = df_filtrado.copy()
    df_tabla["CUIT"] = df_tabla["cuit"].apply(formatear_cuit)
    df_tabla["Razón Social"] = df_tabla["razon_social"].str.strip()
    df_tabla["Monto Total"] = df_tabla["monto_total"].apply(lambda x: formatear_monto(x))
    df_tabla["Adj."] = df_tabla["cantidad_adjudicaciones"].fillna(0).astype(int)
    df_tabla["Localidad"] = df_tabla["dom_fiscal_localidad"].fillna("").str.strip()
    df_tabla["Actividad"] = df_tabla["actividad_descripcion"].fillna("").str[:45]

    cols_mostrar = ["CUIT", "Razón Social", "Monto Total", "Adj.", "Localidad", "Actividad"]
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
            actividad_html = f'<p style="font-size:0.82rem; color:#00A651; margin:0.3rem 0 0 0;">🏭 {fila["actividad"]}</p>' if fila["actividad"] else ""
            tipo_html = f'<span style="font-size:0.72rem; color:#888;">{fila["tipo_societario"]}</span>' if fila["tipo_societario"] else ""
            st.markdown(f"""
            <div class="seccion-dest">
                <p class="prosp-name">{fila['razon_social']} {tipo_html}</p>
                <p class="prosp-cuit">CUIT: {fila['cuit']}</p>
                <p class="prosp-monto">{fila['monto_total']}</p>
                {actividad_html}
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

            st.markdown("**Historial de adjudicaciones:**")
            try:
                df_adj_hist = adjudicaciones_proveedor(str(row["cuit"]))
                if not df_adj_hist.empty:
                    cols_hist = ["anio_fuente", "organismo", "monto", "tipo_procedimiento", "rubros", "fuente"]
                    cols_hist = [c for c in cols_hist if c in df_adj_hist.columns]
                    hist = df_adj_hist[cols_hist].copy()
                    hist["monto"] = hist["monto"].apply(lambda x: formatear_monto(x))
                    rename = {"anio_fuente": "Año", "organismo": "Organismo", "monto": "Monto",
                              "tipo_procedimiento": "Tipo", "rubros": "Rubros", "fuente": "Fuente"}
                    hist.columns = [rename.get(c, c) for c in hist.columns]
                    st.dataframe(hist, use_container_width=True, hide_index=True, height=220)
                else:
                    st.caption("Sin historial detallado.")
            except Exception as e:
                st.warning(f"No se pudo cargar historial: {e}")

        with col_bcra:
            st.markdown("**Situación BCRA**")
            st.markdown("*Central de Deudores del BCRA*")

            bcra_key = f"bcra_{row['cuit']}"
            if bcra_key not in st.session_state:
                if st.button("Consultar BCRA", key=f"btn_{row['cuit']}"):
                    render_perrito_loader("Consultando deudas...")
                    resultado = consultar_uno(str(row["cuit"]))
                    st.session_state[bcra_key] = resultado
                    st.rerun()
            else:
                resultado = st.session_state[bcra_key]
                sit = resultado.get("situacion_max", -1)

                if sit == -1:
                    clase = "sit-rojo"
                    icono = "⚠️"
                elif sit <= 1:
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
render_footer()
