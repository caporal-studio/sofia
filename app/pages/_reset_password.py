import streamlit as st
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from app.utils.ui_utils import fix_menu
from urllib.parse import parse_qs, urlparse
from app.utils.auth import load_users, save_users, hash_password, verify_password, send_recovery_email, reset_user_password
from app.utils.app_config import get_app_info
from app.utils.i18n import language_selector, t

# Caminhos
USERS_FILE = Path("resources/users.json")
TOKENS_FILE = Path("resources/token_recuperacao.json")

# Configuração da página
st.set_page_config(page_title=t("reset_page_title"), page_icon="🔐", initial_sidebar_state="collapsed")
language_selector(st)
st.title(t("reset_title"))
fix_menu()

users = load_users()
info = get_app_info()

# --- 1. USUÁRIO LOGADO ALTERA SENHA --- #
if st.session_state.get("user"):
    st.subheader(t("change_own_password"))
    email = st.session_state.get("user_email") or st.session_state.user.get("email")
    senha_atual = st.text_input(t("current_password"), type="password")
    nova_senha = st.text_input(t("new_password"), type="password")
    confirmar_senha = st.text_input(t("confirm_password_prompt"), type="password")

    if st.button(t("change_password_button")):
        user = users.get(email)
        if not user or not verify_password(senha_atual, user.get("password", "")):
            st.error(t("wrong_current_password"))
        elif nova_senha != confirmar_senha:
            st.error(t("passwords_do_not_match"))
        else:
            user["password"] = hash_password(nova_senha)
            save_users(users)
            st.success(t("password_changed"))

st.markdown("---")

# --- 2. USUÁRIO DESLOGADO RECUPERA SENHA --- #
st.subheader(t("recover_password_email"))
recovery_modes = {
    "request": t("request_recovery_link"),
    "reset": t("reset_with_token"),
}
modo = st.radio(
    t("steps"),
    options=list(recovery_modes),
    format_func=lambda key: recovery_modes[key],
)

if modo == "request":
    email = st.text_input(t("registered_email"))
    if st.button(t("send_link")):
        if email not in users:
            st.error(t("email_not_found"))
        else:
            token = secrets.token_urlsafe(16)
            expiracao = (datetime.utcnow() + timedelta(minutes=15)).isoformat()

            token_data = {"email": email, "token": token, "expira_em": expiracao}
            with open(TOKENS_FILE, "w", encoding="utf-8") as f:
                json.dump(token_data, f)

            base_url = info.get("app_base_url", "http://localhost:8501").rstrip("/")
            link = f"{base_url}/reset_password?token={token}"
            if send_recovery_email(email, link):
                st.success(t("recovery_link_sent"))
            else:
                st.info(t("smtp_not_configured_link", link=link))

elif modo == "reset":
    token_digitado = st.text_input(t("paste_token_link"))
    nova_senha = st.text_input(t("new_password"), type="password")
    confirmar = st.text_input(t("confirm_password_prompt"), type="password")

    if st.button(t("update_password")):
        if not TOKENS_FILE.exists():
            st.error(t("no_token_found"))
        else:
            with open(TOKENS_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)

            token_text = token_digitado.strip()
            parsed_token = parse_qs(urlparse(token_text).query).get("token", [token_text])[0]
            token_valido = parsed_token == dados.get("token")
            expira_em = datetime.fromisoformat(dados.get("expira_em"))

            if not token_valido:
                st.error(t("invalid_or_expired_token"))
            elif datetime.utcnow() > expira_em:
                st.error(t("expired_token_request_new"))
            elif nova_senha != confirmar:
                st.error(t("passwords_do_not_match_short"))
            else:
                email = dados["email"]
                if reset_user_password(email, nova_senha):
                    TOKENS_FILE.unlink(missing_ok=True)
                    st.success(t("password_reset_success"))
                else:
                    st.error(t("user_not_found"))
