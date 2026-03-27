"""Componentes reutilizables — header, sidebar, perrito loader, footer, metric card."""

import base64
import streamlit as st
from pathlib import Path


def render_header():
    """Header con gradiente BP y branding LICITARG."""
    logo_path = Path("assets/logolic.png")
    if logo_path.exists():
        img_bytes = logo_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode()
        logo_html = f'<img src="data:image/png;base64,{img_b64}" alt="LICITARG" style="max-height:60px;">'
    else:
        logo_html = '<h1>LICITARG</h1>'

    st.markdown(f"""
    <div class="header-gradient">
        {logo_html}
        <p>Proveedores del Estado · Prospección comercial</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_brand():
    """Logo y marca en sidebar."""
    logo_path = Path("assets/licitarg.png")
    if logo_path.exists():
        img_bytes = logo_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode()
        st.sidebar.markdown(f"""
        <div class="sidebar-logo">
            <img src="data:image/png;base64,{img_b64}" alt="LICITARG">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
        <div class="sidebar-brand">
            <h2>LICITARG</h2>
            <p>Proveedores del estado</p>
        </div>
        """, unsafe_allow_html=True)


def render_metric_card(value, label, col=None):
    """Card de métrica."""
    html = f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """
    target = col if col else st
    target.markdown(html, unsafe_allow_html=True)


def render_perrito_loader(message="Olfateando proveedores..."):
    """Loader del perrito con animación."""
    perrito_path = Path("assets/perrito_bp.png")
    if perrito_path.exists():
        img_bytes = perrito_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode()
        img_tag = f'<img src="data:image/png;base64,{img_b64}" alt="Cargando...">'
    else:
        img_tag = '<div style="font-size:3rem;">🐕</div>'

    st.markdown(f"""
    <div class="perrito-loader">
        {img_tag}
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Footer con firma."""
    firma_path = Path("assets/firma_pablo.png")
    if firma_path.exists():
        img_bytes = firma_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode()
        firma_tag = f'<img src="data:image/png;base64,{img_b64}" alt="@Pablocuadros19" style="max-width:180px; opacity:0.85;">'
    else:
        firma_tag = '<span style="font-style:italic; color:#999;">@Pablocuadros19</span>'

    st.markdown(f"""
    <div style="text-align:center; padding:2rem 0 1rem; margin-top:3rem;
                border-top:1px solid #e0e5ec;">
        {firma_tag}
        <p style="font-size:0.7rem; color:#999; margin-top:0.5rem;">
            LICITARG v0.1 — Banco Provincia
        </p>
    </div>
    """, unsafe_allow_html=True)
