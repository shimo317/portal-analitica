import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def send_recovery_token(to_email: str, token: str) -> bool:
    try:
        smtp_server = st.secrets["email"]["SMTP_SERVER"]
        smtp_port = st.secrets["email"]["SMTP_PORT"]
        smtp_user = st.secrets["email"]["SMTP_USER"]
        smtp_password = st.secrets["email"]["SMTP_PASSWORD"]
    except Exception as e:
        print(f"Error cargando credenciales de correo (revisa el archivo .streamlit/secrets.toml): {e}")
        return False

    if not smtp_user or "pon_aqui_tu_correo" in smtp_user:
        print("El correo de remitente no ha sido configurado en secrets.toml")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Código de Recuperación - Portal de Analítica"
    msg["From"] = smtp_user
    msg["To"] = to_email

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f7fb; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h2 style="color: #0f172a; text-align: center;">Recuperación de Contraseña</h2>
            <p style="color: #334155; font-size: 16px;">Has solicitado restablecer tu contraseña en el Portal de Analítica.</p>
            <p style="color: #334155; font-size: 16px;">Para continuar, copia y pega el siguiente código de seguridad:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <span style="display: inline-block; background-color: #eff6ff; color: #1e3a8a; font-size: 24px; font-weight: bold; padding: 15px 25px; border-radius: 8px; letter-spacing: 2px;">
                    {token}
                </span>
            </div>
            
            <p style="color: #64748b; font-size: 14px; text-align: center;">Este código caducará en 15 minutos.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 25px 0;">
            <p style="color: #94a3b8; font-size: 12px; text-align: center;">Si no solicitaste este código, puedes ignorar este correo de forma segura.</p>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_content, "html"))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo vía SMTP: {e}")
        return False
