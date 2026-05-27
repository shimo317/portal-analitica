import streamlit as st
from pathlib import Path
import auth
from ui.login_view import render_login
from admin_panel import render_admin_panel
from ui.sidebar_toggle import sidebar_toggle

# =========================
# Configuración base
# =========================
st.set_page_config(
    page_title="Portal de Analítica",
    layout="wide",
    initial_sidebar_state="expanded"
)

auth.init_db()
auth.seed_admin_if_not_exists()

# Bootstrap icons
st.markdown(
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">',
    unsafe_allow_html=True
)

# =========================
# Saber si ya inició sesión
# =========================
authenticated = auth.is_authenticated()

# =========================
# Cargar CSS según estado
# =========================
base_dir = Path(__file__).parent
global_css_file = base_dir / "styles" / "global.css"
home_css_file = base_dir / "styles" / "home.css"
login_css_file = base_dir / "styles" / "login.css"

css_text = ""

if global_css_file.exists():
    css_text += global_css_file.read_text(encoding="utf-8") + "\n"

if authenticated:
    if home_css_file.exists():
        css_text += home_css_file.read_text(encoding="utf-8") + "\n"
else:
    if login_css_file.exists():
        css_text += login_css_file.read_text(encoding="utf-8") + "\n"

if css_text.strip():
    st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)


def render_home():
    user = auth.load_authenticated_user()

    if not user:
        st.rerun()

    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = True

    # ===== TOP BAR =====
    col_left, col_space, col_right = st.columns([1, 6, 3])

    with col_right:
        st.markdown(
            f"""
            <div class="top-userbar">
                <span>👤 <b>{user['username']}</b> | Rol: <b>{user['role'].replace('analista', 'Operación').replace('usuario', 'Ventas').replace('admin', 'Administrador')}</b></span>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Cerrar sesión",
            use_container_width=True,
            key="logout_btn",
            type="secondary"
        ):
            auth.logout_user()
            st.rerun()

    # ===== OCULTAR SIDEBAR EN HOME =====
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ===== HERO =====
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-wrap">
                <div class="hero-title">Portal de <span class="accent">Analítica</span></div>
                <div class="hero-sub">
                    Ecosistema inteligente para procesamiento, diagnóstico y predicción de datos estratégicos.<br>
                    Selecciona un módulo, sube tu CSV y descarga reportes en segundos.
                </div>
            </div>
        </div>
        <div class="sep"></div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">Nuestras Soluciones Modulares</div>',
        unsafe_allow_html=True
    )

    modules = [
        {
            "title": "Descriptiva",
            "desc": "KPIs, filtros, tendencias y categorías principales para entender tu histórico.",
            "icon": "bi-list-check",
            "path": "pages/1_Descriptiva.py",
            "roles": ["admin", "analista"]
        },
        {
            "title": "Predictiva",
            "desc": "Modelado estadístico y proyecciones de tendencias (regresión lineal simple).",
            "icon": "bi-graph-up",
            "path": "pages/2_Predictiva.py",
            "roles": ["admin", "analista"]
        },
        {
            "title": "Prescriptiva",
            "desc": "Recomendaciones y plan de ajuste por categoría para cumplir un presupuesto.",
            "icon": "bi-lightbulb",
            "path": "pages/3_Prescriptiva.py",
            "roles": ["admin", "analista"]
        },
        {
            "title": "Calidad de Datos",
            "desc": "Auditoría: nulos, duplicados, outliers, score y reporte descargable.",
            "icon": "bi-shield-check",
            "path": "pages/4_Calidad_Datos.py",
            "roles": ["admin"]
        },
        {
            "title": "Minería / Segmentación",
            "desc": "Clustering para descubrir patrones y segmentar comportamientos en tus datos.",
            "icon": "bi-cpu",
            "path": "pages/5_Mineria_Segmentacion.py",
            "roles": ["admin"]
        },
    ]

    def has_module(module_title):
        return module_title in user.get("allowed_modules", [])

    def render_card(m):
        allowed = has_module(m["title"])
        opacity = "1" if allowed else "0.55"
        button_label = "Acceder" if allowed else "Sin permiso"

        st.markdown(
            f"""
            <div class="module-card" style="opacity:{opacity};">
                <div class="icon-badge"><i class="bi {m['icon']}"></i></div>
                <h3>{m['title']}</h3>
                <p>{m['desc']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if allowed:
            if st.button(
                button_label,
                key=f"btn_{m['title']}",
                type="primary",
                use_container_width=False
            ):
                st.switch_page(m["path"])
        else:
            st.button(
                button_label,
                disabled=True,
                key=f"btn_{m['title']}_disabled",
                type="secondary",
                use_container_width=False
            )

    c1, c2, c3 = st.columns(3)
    with c1:
        render_card(modules[0])
    with c2:
        render_card(modules[1])
    with c3:
        render_card(modules[2])

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    c4, c5 = st.columns(2)
    with c4:
        render_card(modules[3])
    with c5:
        render_card(modules[4])

    st.caption("© 2025 Portal de Analítica | UI dark (Streamlit multipage)")

    # ===== PANEL DE ADMINISTRACIÓN (solo admin) =====
    if user["role"] == "admin":
        render_admin_panel(user)


if authenticated:
    render_home()
else:
    render_login()
