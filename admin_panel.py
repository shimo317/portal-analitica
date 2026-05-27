import streamlit as st
import auth


# Etiquetas legibles para roles
ROLE_LABELS = {
    "admin":    "Administrador",
    "analista": "Operación",
    "usuario":  "Ventas",
}

ROLE_COLORS = {
    "admin":    "#0B548B",
    "analista": "#1E7A5E",
    "usuario":  "#7A5C1E",
}

ROLE_BG = {
    "admin":    "#D6E3FA",
    "analista": "#D6F0E6",
    "usuario":  "#FAF0D6",
}


def _badge(role: str) -> str:
    color  = ROLE_COLORS.get(role, "#445")
    bg     = ROLE_BG.get(role, "#eee")
    label  = ROLE_LABELS.get(role, role)
    return (
        f'<span style="'
        f'background:{bg};color:{color};'
        f'border-radius:999px;padding:2px 12px;'
        f'font-size:12px;font-weight:700;'
        f'border:1px solid {color}33;'
        f'">{label}</span>'
    )


def _estado_badge(is_active: bool) -> str:
    if is_active:
        return (
            '<span style="background:#D6F0E6;color:#1E7A5E;'
            'border-radius:999px;padding:2px 10px;'
            'font-size:12px;font-weight:700;'
            'border:1px solid #1E7A5E33;">Activo</span>'
        )
    return (
        '<span style="background:#FAD6D6;color:#8B0B0B;'
        'border-radius:999px;padding:2px 10px;'
        'font-size:12px;font-weight:700;'
        'border:1px solid #8B0B0B33;">Inactivo</span>'
    )


def render_admin_panel(current_user: dict):
    """
    Renderiza el panel de administración de usuarios.
    Solo debe llamarse cuando current_user['role'] == 'admin'.
    """

    st.markdown(
        """
        <style>
        /* Fondo y borde del campo selectbox */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background-color: #F3F6F9 !important;
            border-radius: 8px !important;
            border: 1px solid #c2d5eb !important;
            color: #1D496D !important;
        }
        /* Icono flechita */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
            fill: #1D496D !important;
        }
        /* Color del texto */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] div[class*="singleValue"] {
            color: #1D496D !important;
        }
        /* Lista desplegable (Popover) */
        div[data-baseweb="popover"] > div {
            background-color: #F3F6F9 !important;
            border: 1px solid #c2d5eb !important;
        }
        ul[data-baseweb="menu"] li {
            color: #1D496D !important;
            background-color: transparent !important;
        }
        ul[data-baseweb="menu"] li:hover,
        ul[data-baseweb="menu"] li[aria-selected="true"] {
            background-color: #D6E3FA !important;
            color: #005187 !important;
        }

        /* ================= MULTISELECT ================= */
        /* Fondo gris para la barra de despliegue */
        div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
            background-color: #F1F5F9 !important;
            border-radius: 8px !important;
            border: 1px solid #c2d5eb !important;
        }
        /* Icono flechita multi-select */
        div[data-testid="stMultiSelect"] div[data-baseweb="select"] svg {
            fill: #1D496D !important;
        }
        /* Etiquetas de cada módulo (azul claro) */
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
            background-color: #5386BF !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        /* Hover de la 'x' en las etiquetas */
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] span[role="presentation"]:hover {
            background-color: #3A6999 !important;
        }

        /* ================= BOTON CREAR USUARIO ================= */
        /* Botón azul marino */
        div[data-testid="stFormSubmitButton"] button {
            background-color: #003366 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 10px rgba(0, 51, 102, 0.3) !important;
            font-weight: bold !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            background-color: #002244 !important;
            color: #FFFFFF !important;
        }
        div[data-testid="stFormSubmitButton"] button p {
            color: #FFFFFF !important;
        }

        /* Color y peso de las etiquetas (Buscador y Filtro) */
        div[data-testid="stTextInput"] label p,
        div[data-testid="stMultiSelect"] label p {
            color: #005187 !important;
            font-weight: 700 !important;
            font-size: 14px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Separador visual ──────────────────────────────────────────
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="
            width:100%;height:2px;
            background:linear-gradient(90deg,#005187 0%,#005187 7.5%,
            rgba(132,182,244,0.18) 7.5%,rgba(132,182,244,0.18) 100%);
            border-radius:999px;margin-bottom:28px;
        "></div>
        """,
        unsafe_allow_html=True,
    )

    # ── Título del panel ──────────────────────────────────────────
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:24px;">
            <div style="
                width:48px;height:48px;border-radius:16px;
                background:linear-gradient(135deg,#5386BF,#4A7EB8);
                display:flex;align-items:center;justify-content:center;
                color:#fff;font-size:22px;border:1px solid rgba(255,255,255,.22);
                box-shadow:0 6px 16px rgba(77,130,188,.22);
            "><i class="bi bi-people-fill"></i></div>
            <div>
                <div style="font-size:22px;font-weight:800;color:#005187;
                            letter-spacing:-.01em;">
                    Administración de Usuarios
                </div>
                <div style="font-size:14px;color:#476E95;margin-top:2px;">
                    Gestiona las cuentas del sistema
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Tabs ──────────────────────────────────────────────────────
    tab_lista, tab_crear = st.tabs(["👥  Lista de usuarios", "➕  Crear nuevo usuario"])

    # ═══════════════════════════════════════════════════
    # TAB 1 — LISTA DE USUARIOS
    # ═══════════════════════════════════════════════════
    with tab_lista:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            search_query = st.text_input(
                "Buscador de usuario",
                placeholder="⌕ Buscar por nombre o correo...",
                key="search_user"
            ).strip().lower()
        with col_s2:
            role_filter = st.multiselect(
                "Filtrar por rol",
                options=["admin", "analista", "usuario"],
                format_func=lambda r: ROLE_LABELS.get(r, r),
                key="filter_roles"
            )

        users = auth.get_all_users()

        # Aplicar filtros
        if search_query:
            users = [u for u in users if search_query in u["username"].lower() or search_query in u["email"].lower()]
        if role_filter:
            users = [u for u in users if u["role"] in role_filter]

        if not users:
            st.info("No hay usuarios registrados.")
        else:
            # Cabecera de tabla
            st.markdown(
                """
                <div style="
                    display:grid;
                    grid-template-columns:2.5fr 2fr 1fr 2fr 1fr;
                    gap:8px;
                    background:#D6E3FA;
                    border-radius:12px 12px 0 0;
                    padding:10px 16px;
                    font-size:13px;font-weight:700;color:#005187;
                    border:1px solid rgba(132,182,244,.28);
                    border-bottom:none;
                    margin-top:8px;
                ">
                    <span>Usuario</span>
                    <span>Correo</span>
                    <span>Rol</span>
                    <span>Módulos</span>
                    <span>Estado</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for u in users:
                is_self = u["id"] == current_user["id"]
                mfa_txt = "✅ Activo" if u["mfa_enabled"] else "—"

                raw_modules = u.get("allowed_modules")
                if raw_modules:
                    allowed = [m.strip() for m in raw_modules.split(",") if m.strip()]
                else:
                    if u["role"] == "admin":
                        allowed = ["Descriptiva", "Predictiva", "Prescriptiva", "Calidad de Datos", "Minería / Segmentación"]
                    elif u["role"] == "analista":
                        allowed = ["Descriptiva", "Predictiva", "Prescriptiva"]
                    else:
                        allowed = ["Descriptiva"]
                
                modulos_tooltip = ", ".join(allowed)
                pills_html = "".join([f'<span style="background-color: #D6E3FA; color: #005187; border: 1px solid rgba(132,182,244,.5); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; margin-right: 4px; margin-bottom: 4px; display: inline-block; white-space: nowrap;">{m}</span>' for m in allowed])

                # Fila info
                st.markdown(
                    f"""
                    <div style="
                        display:grid;
                        grid-template-columns:2.5fr 2fr 1fr 2fr 1fr;
                        gap:8px;
                        background:{'rgba(214,227,250,0.35)' if is_self else 'rgba(255,255,255,0.7)'};
                        padding:10px 16px;
                        font-size:13px;color:#1D496D;
                        border:1px solid rgba(132,182,244,.18);
                        border-top:none;
                        align-items:center;
                    ">
                        <span style="font-weight:600;">
                            {u['username']}{"&nbsp;<span style='font-size:11px;color:#4D82BC;'>(tú)</span>" if is_self else ""}
                        </span>
                        <span style="color:#476E95; word-break: break-all;">{u['email']}</span>
                        <span>{_badge(u['role'])}</span>
                        <div style="display: flex; flex-wrap: wrap; margin-top: 4px;" title="{modulos_tooltip}">{pills_html}</div>
                        <span>{_estado_badge(u['is_active'])}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Fila acciones (solo si no es el propio admin)
                if not is_self:
                    col_rol, col_mod, col_toggle, col_del = st.columns([1.5, 3.5, 1.2, 1.2])

                    with col_rol:
                        nuevo_rol = st.selectbox(
                            "Cambiar rol",
                            options=["admin", "analista", "usuario"],
                            index=["admin", "analista", "usuario"].index(u["role"]),
                            format_func=lambda r: ROLE_LABELS[r],
                            key=f"rol_{u['id']}",
                            label_visibility="collapsed",
                        )
                        if st.button(
                            "Guardar rol",
                            key=f"save_rol_{u['id']}",
                            type="primary",
                            use_container_width=True,
                        ):
                            ok, msg = auth.admin_change_role(u["id"], nuevo_rol, current_user)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    
                    with col_mod:
                        mod_opciones = ["Descriptiva", "Predictiva", "Prescriptiva", "Calidad de Datos", "Minería / Segmentación"]
                        edit_modulos = st.multiselect(
                            "Editar módulos",
                            options=mod_opciones,
                            default=allowed,
                            key=f"edit_mod_{u['id']}",
                            label_visibility="collapsed"
                        )
                        if st.button("Guardar módulos", key=f"save_mod_{u['id']}", type="primary", use_container_width=True):
                            modulos_str = ",".join(edit_modulos)
                            ok, msg = auth.admin_update_modules(u["id"], modulos_str, current_user)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                    with col_toggle:
                        toggle_label = "🔴 Desact." if u["is_active"] else "🟢 Activar"
                        if st.button(
                            toggle_label,
                            key=f"toggle_{u['id']}",
                            use_container_width=True,
                        ):
                            ok, msg = auth.admin_toggle_active(u["id"], current_user)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                    with col_del:
                        if st.button(
                            "🗑 Elim.",
                            key=f"del_{u['id']}",
                            use_container_width=True,
                        ):
                            st.session_state[f"confirm_del_{u['id']}"] = True

                    # Confirmación de eliminación
                    if st.session_state.get(f"confirm_del_{u['id']}"):
                        st.warning(
                            f"⚠️ ¿Eliminar permanentemente a **{u['username']}**? Esta acción no se puede deshacer."
                        )
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button(
                                "Sí, eliminar",
                                key=f"confirm_yes_{u['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                ok, msg = auth.admin_delete_user(u["id"], current_user)
                                st.session_state.pop(f"confirm_del_{u['id']}", None)
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        with c2:
                            if st.button(
                                "Cancelar",
                                key=f"confirm_no_{u['id']}",
                                use_container_width=True,
                            ):
                                st.session_state.pop(f"confirm_del_{u['id']}", None)
                                st.rerun()

                # Línea divisora entre usuarios
                st.markdown(
                    "<hr style='margin:20px 0 20px 0; border:none; border-bottom: 2px solid #84B6F4;'>",
                    unsafe_allow_html=True,
                )

    # ═══════════════════════════════════════════════════
    # TAB 2 — CREAR NUEVO USUARIO
    # ═══════════════════════════════════════════════════
    with tab_crear:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div style="
                background:rgba(214,227,250,0.4);
                border:1px solid rgba(132,182,244,.3);
                border-radius:16px;padding:16px 20px;
                margin-bottom:20px;font-size:13px;color:#385F84;
            ">
                <b>ℹ️ Contraseña temporal:</b> el sistema genera una contraseña segura automáticamente.
                Cópiala y entrégala al usuario. Deberá cambiarla en su primer uso.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("form_crear_usuario", clear_on_submit=True):
            col_a, col_b = st.columns(2)

            with col_a:
                nuevo_username = st.text_input(
                    "Nombre de usuario *",
                    placeholder="ej. juan.perez",
                    key="new_username",
                )
            with col_b:
                nuevo_email = st.text_input(
                    "Correo electrónico *",
                    placeholder="ej. juan@empresa.com",
                    key="new_email",
                )

            nuevo_rol = st.selectbox(
                "Rol del usuario *",
                options=["analista", "usuario", "admin"],
                format_func=lambda r: ROLE_LABELS[r],
                key="new_role",
            )

            modulos_opciones = ["Descriptiva", "Predictiva", "Prescriptiva", "Calidad de Datos", "Minería / Segmentación"]
            if nuevo_rol == "admin":
                default_mods = modulos_opciones
            elif nuevo_rol == "analista":
                default_mods = ["Descriptiva", "Predictiva", "Prescriptiva"]
            else:
                default_mods = ["Descriptiva"]

            modulos_seleccionados = st.multiselect(
                "Módulos permitidos *",
                options=modulos_opciones,
                default=default_mods,
                key=f"modules_{nuevo_rol}" # Change key based on role to force re-render with new defaults
            )

            submitted = st.form_submit_button(
                "Crear usuario",
                use_container_width=True,
                type="primary",
            )

            if submitted:
                modulos_str = ",".join(modulos_seleccionados)
                ok, msg, temp_pw = auth.admin_create_user(
                    nuevo_username, nuevo_email, nuevo_rol, modulos_str, current_user
                )
                if ok:
                    st.success(msg)
                    st.markdown(
                        f"""
                        <div style="
                            margin-top:14px;
                            background:#F3FAFF;
                            border:1px solid rgba(132,182,244,.45);
                            border-radius:12px;
                            padding:18px 22px;
                            box-shadow: 0 6px 16px rgba(0, 81, 135, 0.06);
                        ">
                            <div style="font-size:13px;font-weight:900;color:#005187;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px;">
                                Contraseña temporal generada
                            </div>
                            <div style="
                                font-size:20px;
                                font-weight:800;color:#1D496D;
                                letter-spacing:.15em;
                                background:#FFFFFF;border-radius:8px;
                                padding:12px 18px;display:inline-block;
                                border:1px solid rgba(132,182,244,.35);
                            ">{temp_pw}</div>
                            <div style="font-size:13px;color:#4D82BC;margin-top:10px;font-weight:600;">
                                Copia esta contraseña y entrégala al usuario. No se volverá a mostrar.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.error(msg)
