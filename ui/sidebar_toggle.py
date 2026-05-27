import streamlit as st

def sidebar_toggle(user=None):
    # Estado
    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = True

    # Botón (mismo diseño que Home)
    col_btn, col_space = st.columns([0.06, 0.94])
    with col_btn:
        label = "«" if st.session_state.sidebar_open else "☰"
        if st.button(label, help="Mostrar / Ocultar menú"):
            st.session_state.sidebar_open = not st.session_state.sidebar_open
            st.rerun()

    # Asegura render del sidebar y links manuales 
    with st.sidebar:
        st.markdown("### Navegación")
        st.page_link("Home.py", label="Home")
        
        if user:
            allowed = user.get("allowed_modules", [])
            
            # Todos los módulos disponibles
            modulos = [
                ("Descriptiva", "pages/1_Descriptiva.py"),
                ("Predictiva", "pages/2_Predictiva.py"),
                ("Prescriptiva", "pages/3_Prescriptiva.py"),
                ("Calidad de Datos", "pages/4_Calidad_Datos.py"),
                ("Minería / Segmentación", "pages/5_Mineria_Segmentacion.py")
            ]
            
            for nombre, path in modulos:
                tiene_acceso = nombre in allowed
                st.page_link(path, label=nombre, disabled=not tiene_acceso)

    # CSS fuerte: Ocultar menú nativo de Streamlit SIEMPRE
    css = """
    <style>
    [data-testid="stSidebarNav"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    """
    
    # CSS para abrir/cerrar el layout completo
    if st.session_state.sidebar_open:
        css += """
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            transform: translateX(0) !important;
            width: 21rem !important;
            min-width: 21rem !important;
            max-width: 21rem !important;
        }
        [data-testid="stSidebar"] > div:first-child{ width: 21rem !important; }
        """
    else:
        css += """
        [data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
        }
        """
        
    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)
