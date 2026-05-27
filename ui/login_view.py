import streamlit as st
import streamlit.components.v1 as components
import auth
import email_service


def render_lock_countdown(remaining_seconds: int):
    components.html(
        f"""
        <div id="lock-box" style="
            background: rgba(127,29,29,0.18);
            border: 1px solid rgba(248,113,113,0.30);
            color: #fecaca;
            padding: 12px 14px;
            border-radius: 14px;
            font-family: Arial, sans-serif;
            font-size: 15px;
            margin-top: 8px;
            margin-bottom: 10px;
            line-height: 1.4;
        ">
            <strong>Cuenta bloqueada temporalmente.</strong><br>
            Intenta de nuevo en <span id="countdown"></span>.
        </div>

        <script>
            let remaining = {remaining_seconds};

            function formatTime(seconds) {{
                if (seconds <= 0) return "0 segundos";

                const minutes = Math.floor(seconds / 60);
                const secs = seconds % 60;

                if (minutes === 0) {{
                    return secs === 1 ? "1 segundo" : secs + " segundos";
                }}

                if (secs === 0) {{
                    return minutes === 1 ? "1 minuto" : minutes + " minutos";
                }}

                const minText = minutes === 1 ? "1 minuto" : minutes + " minutos";
                const secText = secs === 1 ? "1 segundo" : secs + " segundos";
                return minText + " y " + secText;
            }}

            const countdownEl = document.getElementById("countdown");

            function tick() {{
                countdownEl.innerText = formatTime(remaining);

                if (remaining <= 0) {{
                    document.getElementById("lock-box").innerHTML =
                        `<strong>Ya puedes intentar iniciar sesión nuevamente.</strong>`;
                    setTimeout(() => {{
                        window.parent.location.reload();
                    }}, 1200);
                    return;
                }}

                remaining -= 1;
                setTimeout(tick, 1000);
            }}

            tick();
        </script>
        """,
        height=95,
    )


def render_login_form():
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        # Precargar credenciales si se guardaron en la sesión
        saved_id = st.session_state.get("saved_identifier", "")
        saved_pw = st.session_state.get("saved_password", "")
        
        # Iniciar el estado del checkbox
        if "remember_user" not in st.session_state:
            st.session_state["remember_user"] = bool(saved_id)

        identifier = st.text_input(
            "Usuario o correo",
            value=saved_id,
            key="login_identifier",
            placeholder="Email address or username"
        )

        password = st.text_input(
            "Contraseña",
            value=saved_pw,
            type="password",
            key="login_password",
            placeholder="Password"
        )

        user_locked = None
        remaining_seconds = 0

        if identifier.strip():
            possible_user = auth.get_user_by_identifier(identifier.strip())
            if possible_user and auth.is_user_locked(possible_user):
                user_locked = possible_user
                remaining_seconds = auth.get_remaining_lock_seconds(
                    possible_user["lock_until"]
                )

        if user_locked:
            render_lock_countdown(remaining_seconds)

        st.checkbox("Recordar contraseña", key="remember_user")

        submitted = st.form_submit_button(
            "Iniciar sesión",
            use_container_width=True,
            disabled=bool(user_locked),
            type="primary"
        )

        if submitted:
            ok, msg, user = auth.authenticate_step_1(identifier.strip(), password)

            if not ok:
                st.error(msg)
            else:
                # Lógica de 'Recordar contraseña' en la sesión local
                if st.session_state.get("remember_user"):
                    st.session_state["saved_identifier"] = identifier.strip()
                    st.session_state["saved_password"] = password
                else:
                    st.session_state.pop("saved_identifier", None)
                    st.session_state.pop("saved_password", None)

                if user["mfa_enabled"]:
                    st.session_state["pending_mfa"] = True
                    st.session_state["pending_user_id"] = user["id"]
                    st.success("Primer factor correcto. Ingresa tu código MFA.")
                else:
                    auth.login_user(user)
                    st.rerun()

    if st.session_state.get("pending_mfa"):
        st.markdown('<div class="login-divider"></div>', unsafe_allow_html=True)

        with st.form("mfa_form", clear_on_submit=False):
            code = st.text_input(
                "Código MFA de 6 dígitos",
                max_chars=6,
                key="mfa_code",
                placeholder="Ingrese su código MFA"
            )

            submitted_mfa = st.form_submit_button(
                "Validar MFA",
                use_container_width=True,
                type="primary"
            )

            if submitted_mfa:
                user = auth.get_user_by_id(st.session_state["pending_user_id"])
                if user and auth.verify_totp(user["mfa_secret"], code.strip()):
                    auth.login_user(user)
                    st.session_state.pop("pending_mfa", None)
                    st.session_state.pop("pending_user_id", None)
                    st.rerun()
                else:
                    auth.log_access(
                        user["id"] if user else None,
                        user["username"] if user else None,
                        user["email"] if user else None,
                        "mfa_verification",
                        "failure",
                        "Código inválido"
                    )
                    st.error("Código MFA inválido.")

    st.markdown(
        """
        <div class="login-footer-note">
            Tus datos se usan únicamente para autenticación, control de acceso y seguridad del sistema.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)


def render_recover_password():
    st.markdown('<div class="login-shell" style="margin-top: 15px;">', unsafe_allow_html=True)
    
    if "reset_step" not in st.session_state:
        st.session_state["reset_step"] = 1
        
    if st.session_state["reset_step"] == 1:
        with st.form("forgot_form"):
            st.markdown('<h3 style="color: #0f172a;">Paso 1: Solicitar Token</h3>', unsafe_allow_html=True)
            st.markdown('<p style="color: #475569; font-size: 14px;">Ingresa tu correo o usuario para recibir un token y crear una nueva contraseña.</p>', unsafe_allow_html=True)
            recovery_id = st.text_input("Usuario o correo", key="recovery_id")
            
            if st.form_submit_button("Enviar Token", use_container_width=True, type="primary"):
                user = auth.get_user_by_identifier(recovery_id.strip())
                if user and user["is_active"]:
                    token = auth.create_reset_token_for_user(user["id"])
                    
                    # ENVÍO REAL DEL CORREO SMTP
                    with st.spinner("Enviando código a tu correo..."):
                        sent_ok = email_service.send_recovery_token(user['email'], token)
                        
                    if sent_ok:
                        st.session_state["reset_step"] = 2
                        st.success("✅ ¡Token enviado por correo! Revisa tu bandeja de entrada o spam.")
                        st.rerun()
                    else:
                        st.error("Hubo un error configurando/enviando el correo. Revisa tus credenciales o el archivo secrets.toml")
                else:
                    st.error("El usuario o correo ingresado no existe en el sistema.")
                    
    elif st.session_state["reset_step"] == 2:
        with st.form("reset_form"):
            st.markdown('<h3 style="color: #0f172a;">Paso 2: Crear Nueva Contraseña</h3>', unsafe_allow_html=True)
            token_input = st.text_input("Código de seguridad (Token)", key="reset_token")
            new_pass1 = st.text_input("Nueva contraseña", type="password", key="new_pass1")
            new_pass2 = st.text_input("Confirmar nueva contraseña", type="password", key="new_pass2")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state["reset_step"] = 1
                    st.rerun()
            with c2:
                if st.form_submit_button("Cambiar Contraseña", use_container_width=True, type="primary"):
                    if new_pass1 != new_pass2:
                        st.error("Las contraseñas no coinciden.")
                    elif not token_input.strip():
                        st.error("El token es requerido.")
                    else:
                        row, err_msg = auth.validate_reset_token(token_input.strip())
                        if err_msg:
                            st.error(err_msg)
                        else:
                            success, pass_errors = auth.update_user_password(row["user_id"], new_pass1)
                            if not success:
                                for err in pass_errors:
                                    st.error(err)
                            else:
                                auth.mark_reset_token_used(row["id"])
                                st.session_state["reset_step"] = 1
                                st.success("¡Contraseña actualizada! Ve a 'Iniciar sesión'.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_login():
    st.markdown(
        """
        <style>
        /* Ajuste de color para las pestañas de inicio de sesión */
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            color: #1e3a8a !important;
            font-weight: 600 !important;
            font-size: 16px !important;
        }
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {
            color: #0f172a !important;
        }
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            border-bottom-color: #0f172a !important;
        }
        </style>
        
        <div class="login-page-header">
            <div class="login-small-title">Portal de Analítica</div>
            <div class="login-main-title">Iniciar sesión</div>
            <div class="login-main-subtitle">
                Introduzca su nombre de usuario y su contraseña.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    left, center, right = st.columns([1.2, 1.6, 1.2])

    with center:
        # Pestañas para cambiar entre login y recuperar clave
        tab_login, tab_recover = st.tabs(["Iniciar sesión", "Recuperar contraseña"])
        
        with tab_login:
            render_login_form()
            
        with tab_recover:
            render_recover_password()