import json, hashlib, os
from pathlib import Path
import streamlit as st
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode
import secrets
import time
from datetime import datetime
from app.utils.i18n import t

USERS_FILE = Path("resources/users.json")
COOKIE_FILE = Path("resources/session_cookie.json")
RECOVERY_TOKENS = {}  # Em memória

# Funções auxiliares
def hash_password(password: str) -> str:
    iterations = 260_000
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def verify_password(raw: str, hashed: str) -> bool:
    if not hashed:
        return False
    if hashed.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, digest = hashed.split("$", 3)
            candidate = hashlib.pbkdf2_hmac(
                "sha256",
                raw.encode(),
                salt.encode(),
                int(iterations),
            ).hex()
            return secrets.compare_digest(candidate, digest)
        except ValueError:
            return False
    # Compatibilidade para instalações antigas; novas senhas usam PBKDF2.
    legacy = hashlib.sha256(raw.encode()).hexdigest()
    return secrets.compare_digest(legacy, hashed)

def generate_temp_password():
    return secrets.token_urlsafe(8)

# Sessão
def salvar_sessao(email):
    try:
        COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
        COOKIE_FILE.write_text(json.dumps({
            "email": email,
            "timestamp": str(datetime.now())
        }, indent=2, ensure_ascii=False))
        print(f"[AUTH] Sessão salva com sucesso em {COOKIE_FILE}")
    except Exception as e:
        print(f"[AUTH] Erro ao salvar sessão: {e}")

def carregar_sessao():
    if not COOKIE_FILE.exists():
        return False, None
    try:
        data = json.loads(COOKIE_FILE.read_text())
        if "email" in data:
            return True, data["email"]
    except json.JSONDecodeError:
        COOKIE_FILE.unlink()
    return False, None

def encerrar_sessao():
    if COOKIE_FILE.exists():
        COOKIE_FILE.unlink()
    st.session_state.clear()

# Validação de usuário
def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = USERS_FILE.with_name(f".{USERS_FILE.name}.tmp")
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_file, USERS_FILE)
    except Exception:
        tmp_file.unlink(missing_ok=True)
        raise

def authenticate(email: str, password: str):
    users = load_users()
    user = users.get(email)
    if user and verify_password(password, user.get("password", "")):
        if user.get("active", True):
            return {**user, "email": email}
        else:
            return "inactive"
    return None

def is_admin():
    return st.session_state.get("user", {}).get("role") == "admin"

def require_login():
    autenticado, usuario = carregar_sessao()
    if autenticado and "user" not in st.session_state:
        users = load_users()
        user_data = users.get(usuario)
        if user_data:
            st.session_state["user"] = user_data
            st.session_state["user_email"] = usuario

    if "user" not in st.session_state or not st.session_state["user"]:
        st.warning(t("login_required"))
        import time
        time.sleep(1)
        st.switch_page("pages/_login.py")

def require_admin():
    require_login()
    if not is_admin():
        st.error(t("admin_required"))
        st.stop()

def verify_user(email: str, password: str):
    users = load_users()
    user = users.get(email)
    if user and verify_password(password, user.get("password", "")) and user.get("active", True):
        return {**user, "email": email}
    return None

def reset_user_password(email: str, new_password: str) -> bool:
    users = load_users()
    user = users.get(email)
    if user:
        user["password"] = hash_password(new_password)
        save_users(users)
        return True
    return False

# --- Recuperação de Senha --- #
def generate_recovery_link(user_email: str, base_url: str) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = time.time() + 3600  # 1 hora
    RECOVERY_TOKENS[token] = {"email": user_email, "expires_at": expires_at}
    query = urlencode({"token": token})
    return f"{base_url}?{query}"

def is_valid_token(token: str) -> bool:
    token_data = RECOVERY_TOKENS.get(token)
    if not token_data:
        return False
    if time.time() > token_data["expires_at"]:
        RECOVERY_TOKENS.pop(token, None)
        return False
    return True

def get_email_by_token(token: str) -> str:
    return RECOVERY_TOKENS.get(token, {}).get("email", "")

def send_recovery_email(user_email: str, recovery_link: str):
    msg = EmailMessage()
    msg["Subject"] = t("recovery_email_subject")
    msg["From"] = os.getenv("SOFIA_SMTP_FROM", "noreply@localhost")
    msg["To"] = user_email
    msg.set_content(t("recovery_email_body", link=recovery_link))

    try:
        host = os.getenv("SOFIA_SMTP_HOST")
        user = os.getenv("SOFIA_SMTP_USER")
        password = os.getenv("SOFIA_SMTP_PASSWORD")
        port = int(os.getenv("SOFIA_SMTP_PORT", "465"))
        if not host or not user or not password:
            print(f"SMTP não configurado. Link de recuperação para {user_email}: {recovery_link}")
            return False
        with smtplib.SMTP_SSL(host, port) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
        print("E-mail enviado com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False
