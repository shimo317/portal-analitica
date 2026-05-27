import re
import io
import secrets
import string
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.extras import RealDictCursor
import pyotp
import qrcode
import streamlit as st
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

APP_NAME = "Portal de Analítica"

# =========================
# CONFIG POSTGRESQL
# =========================
DATABASE_URL = st.secrets["DATABASE_URL"]

SESSION_MINUTES = 30
SESSION_RENEW_MINUTES = 10
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 0.5
RESET_TOKEN_MINUTES = 15

ph = PasswordHasher()
UTC = timezone.utc


def now_utc():
    return datetime.now(UTC)


def to_iso(dt):
    return dt.astimezone(UTC).replace(tzinfo=None)


def from_iso(value):
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role VARCHAR(20) NOT NULL CHECK (role IN ('admin','analista','usuario')),
        is_active BOOLEAN DEFAULT TRUE,
        failed_attempts INTEGER DEFAULT 0,
        lock_until TIMESTAMP,
        mfa_secret TEXT,
        mfa_enabled BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL
    )
    """)

    cur.execute("""
    ALTER TABLE users ADD COLUMN IF NOT EXISTS allowed_modules TEXT;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        session_token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        last_seen_at TIMESTAMP NOT NULL,
        revoked BOOLEAN DEFAULT FALSE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS access_logs (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        username TEXT,
        email TEXT,
        event_type TEXT NOT NULL,
        event_status TEXT NOT NULL,
        detail TEXT,
        created_at TIMESTAMP NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        token_hash TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP NOT NULL
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


def seed_admin_if_not_exists():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM users")
    total = cur.fetchone()["total"]

    if total == 0:
        ts = to_iso(now_utc())
        cur.execute("""
            INSERT INTO users (username, email, password_hash, role, allowed_modules, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            "admin",
            "admin@portal.local",
            ph.hash("Admin#2026"),
            "admin",
            "Descriptiva,Predictiva,Prescriptiva,Calidad de Datos,Minería / Segmentación",
            ts,
            ts
        ))
        conn.commit()

    cur.close()
    conn.close()


def log_access(user_id, username, email, event_type, event_status, detail=None):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO access_logs (user_id, username, email, event_type, event_status, detail, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id, username, email, event_type, event_status, detail, to_iso(now_utc())
    ))

    conn.commit()
    cur.close()
    conn.close()


def validate_password_policy(password):
    errors = []
    if len(password) < 8:
        errors.append("Debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]", password):
        errors.append("Debe contener al menos una letra.")
    if not re.search(r"\d", password):
        errors.append("Debe contener al menos un número.")
    if not re.search(r"[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]", password):
        errors.append("Debe contener al menos un símbolo.")
    return errors


def get_user_by_identifier(identifier):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM users
        WHERE username = %s OR email = %s
        LIMIT 1
    """, (identifier, identifier))

    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM users
        WHERE id = %s
        LIMIT 1
    """, (user_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def create_user(username, email, password, role="usuario", allowed_modules=None):
    errors = validate_password_policy(password)
    if errors:
        return False, errors

    conn = get_db()
    cur = conn.cursor()

    try:
        ts = to_iso(now_utc())
        cur.execute("""
            INSERT INTO users (username, email, password_hash, role, allowed_modules, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, email, ph.hash(password), role, allowed_modules, ts, ts))

        user_id = cur.fetchone()["id"]
        conn.commit()

        cur.close()
        conn.close()
        return True, user_id

    except Exception:
        conn.rollback()
        cur.close()
        conn.close()
        return False, ["El usuario o correo ya existe."]


def verify_password(stored_hash, plain_password):
    try:
        return ph.verify(stored_hash, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception:
        return False


def is_user_locked(user):
    if not user["lock_until"]:
        return False
    lock_until = from_iso(user["lock_until"])
    return now_utc() < lock_until


def format_remaining_lock_time(lock_until):
    if not lock_until:
        return "unos momentos"

    lock_dt = from_iso(lock_until)
    remaining_seconds = max(0, int((lock_dt - now_utc()).total_seconds()))

    if remaining_seconds <= 0:
        return "unos momentos"

    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60

    if minutes == 0:
        return f"{seconds} segundo" if seconds == 1 else f"{seconds} segundos"

    if seconds == 0:
        return f"{minutes} minuto" if minutes == 1 else f"{minutes} minutos"

    min_txt = f"{minutes} minuto" if minutes == 1 else f"{minutes} minutos"
    sec_txt = f"{seconds} segundo" if seconds == 1 else f"{seconds} segundos"
    return f"{min_txt} y {sec_txt}"


def get_remaining_lock_seconds(lock_until):
    if not lock_until:
        return 0

    lock_dt = from_iso(lock_until)
    return max(0, int((lock_dt - now_utc()).total_seconds()))


def register_failed_attempt(user_id):
    user = get_user_by_id(user_id)
    failed = int(user["failed_attempts"]) + 1
    lock_until = None

    if failed >= MAX_FAILED_ATTEMPTS:
        failed = 0
        lock_until = to_iso(now_utc() + timedelta(minutes=LOCKOUT_MINUTES))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET failed_attempts = %s, lock_until = %s, updated_at = %s
        WHERE id = %s
    """, (failed, lock_until, to_iso(now_utc()), user_id))

    conn.commit()
    cur.close()
    conn.close()

    return lock_until


def clear_failed_attempts(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET failed_attempts = 0, lock_until = NULL, updated_at = %s
        WHERE id = %s
    """, (to_iso(now_utc()), user_id))

    conn.commit()
    cur.close()
    conn.close()


def authenticate_step_1(identifier, password):
    user = get_user_by_identifier(identifier)

    if not user:
        log_access(None, identifier, identifier, "login_password", "failure", "Usuario no encontrado")
        return False, "Credenciales inválidas.", None

    if not user["is_active"]:
        return False, "Usuario inactivo.", None

    if is_user_locked(user):
        remaining = format_remaining_lock_time(user["lock_until"])
        return False, f"Cuenta bloqueada temporalmente. Intenta en {remaining}.", None

    if not verify_password(user["password_hash"], password):
        new_lock_until = register_failed_attempt(user["id"])
        log_access(user["id"], user["username"], user["email"], "login_password", "failure", "Contraseña incorrecta")

        if new_lock_until:
            remaining = format_remaining_lock_time(new_lock_until)
            return False, f"Cuenta bloqueada temporalmente. Intenta en {remaining}.", None

        return False, "Credenciales inválidas.", None

    clear_failed_attempts(user["id"])
    return True, "Primer factor correcto.", user


def generate_mfa_secret():
    return pyotp.random_base32()


def set_mfa_secret(user_id, secret):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET mfa_secret = %s, updated_at = %s
        WHERE id = %s
    """, (secret, to_iso(now_utc()), user_id))

    conn.commit()
    cur.close()
    conn.close()


def enable_mfa(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET mfa_enabled = TRUE, updated_at = %s
        WHERE id = %s
    """, (to_iso(now_utc()), user_id))

    conn.commit()
    cur.close()
    conn.close()


def disable_mfa(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET mfa_enabled = FALSE, updated_at = %s
        WHERE id = %s
    """, (to_iso(now_utc()), user_id))

    conn.commit()
    cur.close()
    conn.close()


def get_totp_uri(email, secret):
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=APP_NAME)


def verify_totp(secret, code):
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    except Exception:
        return False


def generate_qr_png_bytes(uri):
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def create_session(user_id):
    token = secrets.token_urlsafe(32)
    created = now_utc()
    expires = created + timedelta(minutes=SESSION_MINUTES)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO sessions (user_id, session_token, created_at, expires_at, last_seen_at, revoked)
        VALUES (%s, %s, %s, %s, %s, FALSE)
    """, (user_id, token, to_iso(created), to_iso(expires), to_iso(created)))

    conn.commit()
    cur.close()
    conn.close()
    return token


def revoke_session(token):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE sessions
        SET revoked = TRUE
        WHERE session_token = %s
    """, (token,))

    conn.commit()
    cur.close()
    conn.close()


def get_session(token):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.*, u.username, u.email, u.role, u.is_active, u.allowed_modules
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.session_token = %s
        LIMIT 1
    """, (token,))

    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def touch_or_renew_session(token):
    sess = get_session(token)
    if not sess or sess["revoked"]:
        return None

    if now_utc() >= from_iso(sess["expires_at"]):
        revoke_session(token)
        return None

    expires_at = from_iso(sess["expires_at"])
    minutes_left = (expires_at - now_utc()).total_seconds() / 60

    conn = get_db()
    cur = conn.cursor()

    if minutes_left <= SESSION_RENEW_MINUTES:
        new_token = secrets.token_urlsafe(32)
        new_expires = now_utc() + timedelta(minutes=SESSION_MINUTES)

        cur.execute("""
            UPDATE sessions
            SET revoked = TRUE
            WHERE session_token = %s
        """, (token,))

        cur.execute("""
            INSERT INTO sessions (user_id, session_token, created_at, expires_at, last_seen_at, revoked)
            VALUES (%s, %s, %s, %s, %s, FALSE)
        """, (
            sess["user_id"],
            new_token,
            to_iso(now_utc()),
            to_iso(new_expires),
            to_iso(now_utc())
        ))

        conn.commit()
        cur.close()
        conn.close()
        return new_token

    cur.execute("""
        UPDATE sessions
        SET last_seen_at = %s
        WHERE session_token = %s
    """, (to_iso(now_utc()), token))

    conn.commit()
    cur.close()
    conn.close()
    return token


def load_authenticated_user():
    token = st.session_state.get("session_token")
    if not token:
        return None

    new_token = touch_or_renew_session(token)
    if not new_token:
        st.session_state.pop("session_token", None)
        st.session_state.pop("user", None)
        return None

    st.session_state["session_token"] = new_token
    sess = get_session(new_token)

    if not sess or sess["revoked"] or not sess["is_active"]:
        st.session_state.pop("session_token", None)
        st.session_state.pop("user", None)
        return None

    raw_modules = sess.get("allowed_modules")
    if raw_modules:
        allowed = [m.strip() for m in raw_modules.split(",") if m.strip()]
    else:
        r = sess["role"]
        if r == "admin":
            allowed = ["Descriptiva", "Predictiva", "Prescriptiva", "Calidad de Datos", "Minería / Segmentación"]
        elif r == "analista":
            allowed = ["Descriptiva", "Predictiva", "Prescriptiva"]
        else:
            allowed = ["Descriptiva"]

    st.session_state["user"] = {
        "id": sess["user_id"],
        "username": sess["username"],
        "email": sess["email"],
        "role": sess["role"],
        "allowed_modules": allowed,
    }
    return st.session_state["user"]


def login_user(user):
    token = create_session(user["id"])
    st.session_state["session_token"] = token
    
    raw_modules = user.get("allowed_modules")
    if raw_modules:
        allowed = [m.strip() for m in raw_modules.split(",") if m.strip()]
    else:
        r = user["role"]
        if r == "admin":
            allowed = ["Descriptiva", "Predictiva", "Prescriptiva", "Calidad de Datos", "Minería / Segmentación"]
        elif r == "analista":
            allowed = ["Descriptiva", "Predictiva", "Prescriptiva"]
        else:
            allowed = ["Descriptiva"]

    st.session_state["user"] = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "allowed_modules": allowed,
    }
    log_access(user["id"], user["username"], user["email"], "login_complete", "success", "Inicio de sesión exitoso")


def logout_user():
    token = st.session_state.get("session_token")
    user = st.session_state.get("user")

    if token:
        revoke_session(token)

    if user:
        log_access(user["id"], user["username"], user["email"], "logout", "success", "Cierre de sesión")

    for key in ["session_token", "user", "pending_mfa", "pending_user_id", "new_mfa_secret"]:
        st.session_state.pop(key, None)


def is_authenticated():
    return load_authenticated_user() is not None


def create_reset_token_for_user(user_id):
    raw_token = secrets.token_urlsafe(32)
    token_hash = ph.hash(raw_token)
    expires = now_utc() + timedelta(minutes=RESET_TOKEN_MINUTES)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO password_reset_tokens (user_id, token_hash, expires_at, used, created_at)
        VALUES (%s, %s, %s, FALSE, %s)
    """, (user_id, token_hash, to_iso(expires), to_iso(now_utc())))

    conn.commit()
    cur.close()
    conn.close()
    return raw_token


def validate_reset_token(raw_token):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM password_reset_tokens
        WHERE used = FALSE
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    for row in rows:
        try:
            if ph.verify(row["token_hash"], raw_token):
                if now_utc() > from_iso(row["expires_at"]):
                    return None, "Token expirado."
                return row, None
        except Exception:
            continue

    return None, "Token inválido."


def mark_reset_token_used(token_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE password_reset_tokens
        SET used = TRUE
        WHERE id = %s
    """, (token_id,))

    conn.commit()
    cur.close()
    conn.close()


def update_user_password(user_id, new_password):
    errors = validate_password_policy(new_password)
    if errors:
        return False, errors

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET password_hash = %s, updated_at = %s
        WHERE id = %s
    """, (ph.hash(new_password), to_iso(now_utc()), user_id))

    cur.execute("""
        UPDATE sessions
        SET revoked = TRUE
        WHERE user_id = %s
    """, (user_id,))

    conn.commit()
    cur.close()
    conn.close()
    return True, []


# ==============================================
# FUNCIONES DE ADMINISTRACIÓN DE USUARIOS
# ==============================================

def generate_temp_password():
    """
    Genera una contraseña temporal segura que cumple la política del sistema.
    Formato: Letras + números + símbolo. Ej: Kx7#mPq2
    """
    chars_upper = string.ascii_uppercase
    chars_lower = string.ascii_lowercase
    chars_digits = string.digits
    chars_symbols = "!@#$%&*"

    password = [
        secrets.choice(chars_upper),
        secrets.choice(chars_lower),
        secrets.choice(chars_digits),
        secrets.choice(chars_symbols),
    ]
    all_chars = chars_upper + chars_lower + chars_digits + chars_symbols
    password += [secrets.choice(all_chars) for _ in range(4)]
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def get_all_users():
    """
    Devuelve todos los usuarios ordenados por fecha de creación descendente.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, username, email, role, is_active, mfa_enabled, created_at, allowed_modules
        FROM users
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def admin_create_user(username, email, role, allowed_modules_str, admin_user):
    """
    Crea un usuario nuevo con contraseña temporal generada automáticamente.
    Retorna (ok: bool, mensaje: str, temp_password: str | None)
    """
    username = username.strip()
    email = email.strip()

    if not username or not email:
        return False, "El nombre de usuario y el correo son obligatorios.", None

    if role not in ("admin", "analista", "usuario"):
        return False, "Rol inválido.", None

    temp_password = generate_temp_password()
    ok, result = create_user(username, email, temp_password, role, allowed_modules_str)

    if not ok:
        return False, " ".join(result) if isinstance(result, list) else result, None

    log_access(
        admin_user["id"],
        admin_user["username"],
        admin_user["email"],
        "admin_create_user",
        "success",
        f"Creó usuario '{username}' con rol '{role}'"
    )
    return True, f"Usuario '{username}' creado correctamente.", temp_password


def admin_toggle_active(target_user_id, admin_user):
    """
    Activa o desactiva un usuario. No puede desactivarse a sí mismo.
    Retorna (ok: bool, mensaje: str)
    """
    if target_user_id == admin_user["id"]:
        return False, "No puedes desactivar tu propia cuenta."

    target = get_user_by_id(target_user_id)
    if not target:
        return False, "Usuario no encontrado."

    new_state = not target["is_active"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET is_active = %s, updated_at = %s
        WHERE id = %s
    """, (new_state, to_iso(now_utc()), target_user_id))

    # Si se desactiva, revocar todas sus sesiones activas
    if not new_state:
        cur.execute("""
            UPDATE sessions
            SET revoked = TRUE
            WHERE user_id = %s
        """, (target_user_id,))

    conn.commit()
    cur.close()
    conn.close()

    accion = "activó" if new_state else "desactivó"
    log_access(
        admin_user["id"],
        admin_user["username"],
        admin_user["email"],
        "admin_toggle_active",
        "success",
        f"{accion.capitalize()} al usuario '{target['username']}'"
    )

    estado = "activado" if new_state else "desactivado"
    return True, f"Usuario '{target['username']}' {estado} correctamente."


def admin_change_role(target_user_id, new_role, admin_user):
    """
    Cambia el rol de un usuario. No puede cambiar su propio rol.
    Retorna (ok: bool, mensaje: str)
    """
    if target_user_id == admin_user["id"]:
        return False, "No puedes cambiar tu propio rol."

    if new_role not in ("admin", "analista", "usuario"):
        return False, "Rol inválido."

    target = get_user_by_id(target_user_id)
    if not target:
        return False, "Usuario no encontrado."

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET role = %s, updated_at = %s
        WHERE id = %s
    """, (new_role, to_iso(now_utc()), target_user_id))

    conn.commit()
    cur.close()
    conn.close()

    log_access(
        admin_user["id"],
        admin_user["username"],
        admin_user["email"],
        "admin_change_role",
        "success",
        f"Cambió rol de '{target['username']}' de '{target['role']}' a '{new_role}'"
    )
    return True, f"Rol de '{target['username']}' cambiado a '{new_role}'."


def admin_update_modules(target_user_id, allowed_modules_str, admin_user):
    """
    Actualiza la lista de módulos permitidos de un usuario existente.
    Retorna (ok: bool, mensaje: str)
    """
    if target_user_id == admin_user["id"]:
        return False, "No puedes editar tus propios módulos desde esta vista."

    target = get_user_by_id(target_user_id)
    if not target:
        return False, "Usuario no encontrado."

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET allowed_modules = %s, updated_at = %s
        WHERE id = %s
    """, (allowed_modules_str, to_iso(now_utc()), target_user_id))

    conn.commit()
    cur.close()
    conn.close()

    log_access(
        admin_user["id"],
        admin_user["username"],
        admin_user["email"],
        "admin_update_modules",
        "success",
        f"Actualizó los módulos de '{target['username']}' a '{allowed_modules_str}'"
    )
    return True, f"Módulos de '{target['username']}' guardados correctamente."


def admin_delete_user(target_user_id, admin_user):
    """
    Elimina un usuario permanentemente. No puede eliminarse a sí mismo.
    Elimina en cascada: sesiones y tokens de reset.
    Retorna (ok: bool, mensaje: str)
    """
    if target_user_id == admin_user["id"]:
        return False, "No puedes eliminar tu propia cuenta."

    target = get_user_by_id(target_user_id)
    if not target:
        return False, "Usuario no encontrado."

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM sessions WHERE user_id = %s", (target_user_id,))
        cur.execute("DELETE FROM password_reset_tokens WHERE user_id = %s", (target_user_id,))
        cur.execute("DELETE FROM users WHERE id = %s", (target_user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Error al eliminar: {str(e)}"

    cur.close()
    conn.close()

    log_access(
        admin_user["id"],
        admin_user["username"],
        admin_user["email"],
        "admin_delete_user",
        "success",
        f"Eliminó al usuario '{target['username']}'"
    )
    return True, f"Usuario '{target['username']}' eliminado permanentemente."
