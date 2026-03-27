"""Tokens de diseño y CSS centralizado — Sistema BP para LICITARG."""

import streamlit as st

COLORS = {
    "primary": "#00A651",
    "primary_dark": "#00a34d",
    "secondary": "#00B8D4",
    "bg_primary": "#ffffff",
    "bg_secondary": "#f7f9fc",
    "bg_accent": "#f0f9f4",
    "text_primary": "#1a1a2e",
    "text_secondary": "#555555",
    "text_muted": "#666666",
    "text_very_muted": "#999999",
    "border_default": "#e0e5ec",
    "border_light": "#d0d5dd",
    "border_green": "#c8e6d5",
    "tag_bg": "#e8f5ee",
    "tag_text": "#00A651",
    "hover_bg": "#f0f9f4",
}


def inject_css():
    """Inyecta CSS global con estilo BP para LICITARG."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Header con gradiente */
    .header-gradient {
        background: linear-gradient(90deg, #ffffff 0%, #00A651 25%, #00B8D4 100%);
        border-radius: 12px;
        padding: 2rem 2rem;
        margin-bottom: 1.5rem;
        color: white;
        text-shadow: 0 1px 3px rgba(0,0,0,.15);
        text-align: center;
    }
    .header-gradient h1 {
        font-weight: 900;
        font-size: 2.8rem;
        margin: 0;
        color: white !important;
    }
    .header-gradient p {
        font-weight: 400;
        font-size: 0.9rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }

    /* Metric card */
    .metric-card {
        background: #f7f9fc;
        border: 1px solid #e0e5ec;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00A651;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #666666;
        margin-top: 0.3rem;
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

    /* Tags */
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

    /* Divider decorativo */
    .bp-divider {
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #00A651, #00B8D4);
        border-radius: 2px;
        margin: 0.8rem 0;
    }
    .divider {
        height: 3px;
        background: linear-gradient(90deg, #00A651, #00B8D4);
        border-radius: 2px;
        margin: 1.2rem 0;
    }

    /* Sidebar */
    .sidebar-logo {
        text-align: center;
        padding: 0.5rem 0 1rem 0;
    }
    .sidebar-logo img {
        max-width: 200px;
    }
    .sidebar-brand {
        text-align: center;
        padding: 1rem 0;
    }
    .sidebar-brand h2 {
        font-weight: 900;
        font-size: 1.6rem;
        color: #00A651;
        margin: 0;
        letter-spacing: 1px;
    }
    .sidebar-brand p {
        font-size: 0.65rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #999;
        margin: 0.2rem 0 0 0;
    }

    /* Sidebar radio -> botones 3D */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
        gap: 0.4rem !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label {
        background: linear-gradient(180deg, #f7f9fc 0%, #e8ecf1 100%);
        border: 1px solid #d0d5dd;
        border-radius: 10px;
        padding: 0.55rem 0.9rem !important;
        margin: 0 !important;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,.08), inset 0 1px 0 rgba(255,255,255,.9);
        display: flex !important;
        align-items: center;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:hover {
        background: linear-gradient(180deg, #e8f5ee 0%, #d4edda 100%);
        border-color: #00A651;
        box-shadow: 0 3px 8px rgba(0,166,81,.15), inset 0 1px 0 rgba(255,255,255,.9);
        transform: translateY(-1px);
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:active {
        transform: translateY(1px);
        box-shadow: inset 0 2px 4px rgba(0,0,0,.1);
    }
    /* Radio seleccionado */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label[data-checked="true"],
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:has(input:checked) {
        background: linear-gradient(180deg, #00A651 0%, #008a44 100%);
        border-color: #007a3d;
        color: white !important;
        box-shadow: 0 3px 8px rgba(0,166,81,.3), inset 0 1px 0 rgba(255,255,255,.15);
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:has(input:checked) p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:has(input:checked) span,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:has(input:checked) div {
        color: white !important;
    }
    /* Ocultar el circulo del radio */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label > div:first-child {
        display: none !important;
    }
    /* Texto del label */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label p {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600;
        font-size: 0.85rem;
        margin: 0;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00A651, #00B8D4) !important;
    }

    /* Botones */
    .stButton > button {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 15px rgba(0,132,61,.25);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00A651, #00a34d);
        color: white;
        border: none;
    }

    /* Loader perrito */
    @keyframes olfatear {
        0%   { transform: translateX(-80px) scaleX(-1); }
        45%  { transform: translateX(80px) scaleX(-1); }
        50%  { transform: translateX(80px) scaleX(1); }
        95%  { transform: translateX(-80px) scaleX(1); }
        100% { transform: translateX(-80px) scaleX(-1); }
    }
    .perrito-loader {
        text-align: center;
        padding: 2rem;
        overflow: hidden;
    }
    .perrito-loader img {
        width: 120px;
        animation: olfatear 3s ease-in-out infinite;
    }
    .perrito-loader p {
        color: #666666;
        font-size: 0.85rem;
        margin-top: 0.8rem;
    }

    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Responsive */
    @media (max-width: 768px) {
        .header-gradient h1 { font-size: 1.5rem; }
        .metric-value { font-size: 1.3rem; }
    }
    </style>
    """, unsafe_allow_html=True)
