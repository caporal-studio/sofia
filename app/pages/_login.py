import streamlit as st
import os
from app.utils.auth import verify_user, salvar_sessao
from app.utils.ui_utils import fix_menu
from app.utils.app_config import get_app_info
from app.utils.i18n import language_selector, localized_subtitle, t
info = get_app_info()

if st.session_state.get("go_home"):
    del st.session_state["go_home"]
    st.switch_page("Home.py")

st.set_page_config(page_title=t("login_page_title"), page_icon="🔐", initial_sidebar_state="collapsed")
language_selector(st)
st.title(t("login_title", name=info["name"]))
if info.get("logo_path") and os.path.exists(info["logo_path"]):
    st.image(info["logo_path"], width=200)
st.subheader(localized_subtitle(info))
fix_menu()

# Inputs do formulário de login
with st.form("login_form"):
    email = st.text_input(t("email"))
    senha = st.text_input(t("password"), type="password")
    login_button = st.form_submit_button(t("sign_in"))

# Valida o login
if login_button:
    if not email or not senha:
        st.warning(t("fill_email_password"))
    else:
        user = verify_user(email, senha)
        if user:
            st.session_state["user"] = user
            st.session_state["user_email"] = user["email"]
            try:
                salvar_sessao(email)
                st.success(t("login_success"))
                st.session_state["go_home"] = True
                print(f"[LOGIN DEBUG] Sessão salva com sucesso para: {email}")
            except Exception as e:
                print(f"[LOGIN DEBUG] Falha ao salvar sessão: {e}")
            import time
            time.sleep(1)
            st.rerun()
        else:
            st.error(t("invalid_login"))

# Link para redefinir senha
st.markdown(f"[{t('forgot_password')}](reset_password)")
