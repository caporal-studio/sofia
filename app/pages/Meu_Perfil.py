import streamlit as st
from app.utils.ui_utils import show_sidebar, show_footer, fix_menu
from app.utils.auth import require_login, hash_password, verify_password, load_users, save_users
from app.utils.i18n import t

# Configurações da página
st.set_page_config(page_title=t("profile"), page_icon="🙋")
st.title(t("profile_title"))
require_login()
fix_menu()
show_sidebar()

# Validação de login
if "user_email" not in st.session_state:
    st.warning(t("not_logged_in"))
    st.stop()

user_email = st.session_state["user_email"]
users = load_users()
user_data = users.get(user_email)

if not user_data:
    st.error(t("user_not_found"))
    st.stop()

# Informações básicas
st.subheader(t("user_info"))
st.markdown(f"- **Email:** `{user_email}`")
st.markdown(f"- **{t('role')}:** `{user_data.get('role', 'user')}`")
st.markdown(f"- **{t('status')}:** {t('active') if user_data.get('active', False) else t('inactive')}")

st.markdown("---")

# Alteração de senha
st.subheader(t("change_password"))

with st.form("form_change_password"):
    current_password = st.text_input(t("current_password"), type="password")
    new_password = st.text_input(t("new_password"), type="password")
    confirm_password = st.text_input(t("confirm_new_password"), type="password")
    submitted = st.form_submit_button(t("update_password"))

    if submitted:
        if not verify_password(current_password, user_data["password"]):
            st.error(t("wrong_current_password"))
        elif new_password != confirm_password:
            st.error(t("passwords_do_not_match"))
        elif len(new_password) < 6:
            st.warning(t("password_too_short"))
        else:
            user_data["password"] = hash_password(new_password)
            users[user_email] = user_data
            save_users(users)
            st.success(t("password_changed"))

show_footer()
