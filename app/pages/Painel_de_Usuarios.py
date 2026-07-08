import streamlit as st
import secrets
from app.utils.ui_utils import show_sidebar, show_footer, fix_menu
from app.utils.auth import require_admin, hash_password, load_users, save_users
from app.utils.i18n import t
import re

# Configuração da página
st.set_page_config(page_title=t("users"), page_icon="👥")
st.title(t("users_title"))
require_admin()
fix_menu()
show_sidebar()

#Custom CSS
st.markdown("""
<style>
div[class*="stSelectbox"] [data-testid="stWidgetLabel"] {
    display:none;
}
</style>
""", unsafe_allow_html=True)

def generate_temp_password():
    return secrets.token_urlsafe(8)

def persist_users(users) -> bool:
    try:
        save_users(users)
        return True
    except OSError as exc:
        st.error(t("save_users_error", error=exc))
        return False

users = load_users()

# Estado inicial para remoção
def solicitar_remocao(email):
    st.session_state[f"confirm_remove_{email}"] = True

def confirmar_remocao(email):
    removed_user = users.pop(email)
    if persist_users(users):
        st.success(t("user_removed", email=email))
        st.session_state[f"confirm_remove_{email}"] = False
        st.session_state["_rerun_flag"] = True
    else:
        users[email] = removed_user

def cancelar_remocao(email):
    st.session_state[f"confirm_remove_{email}"] = False

# Adicionar novo usuário
with st.expander(t("add_user")):
    if "new_user_email_temp" not in st.session_state:
        st.session_state.new_user_email_temp = ""

    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    # Input separado do session_state para não dar conflito de atualização
    new_email = st.text_input(t("new_user_email"), value=st.session_state.new_user_email_temp, key="email_input_box")
    new_role = st.selectbox(t("role"), options=["user", "admin"], key="new_user_role")

    if st.button(t("create_user")):
        if new_email in users:
            st.warning(t("email_already_exists"))
        elif not new_email:
            st.warning(t("email_required"))
        elif not re.match(email_pattern, new_email):
            st.warning(t("invalid_email"))
        else:
            temp_password = generate_temp_password()
            users[new_email] = {
                "password": hash_password(temp_password),
                "role": new_role,
                "active": True
            }
            if persist_users(users):
                st.success(t("user_created", email=new_email))
                st.info(t("temp_password", password=temp_password))

                # Limpa campo após criar
                st.session_state.new_user_email_temp = ""
            else:
                users.pop(new_email, None)

st.markdown("---")
st.subheader(t("existing_users"))

if not users:
    st.info(t("no_users"))
else:
    for email, data in users.items():
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        col1.markdown(f"**{email}**")
        # Toggle ativo/inativo
        current_status = data.get("active", True)
        new_status = col2.toggle(t("status"), value=current_status, key=f"toggle_{email}")
        if new_status != current_status:
            users[email]["active"] = new_status
            if persist_users(users):
                st.rerun()
            users[email]["active"] = current_status

        # Seleção de perfil com atualização
        current_role = data.get("role", "user")
        new_role = col3.selectbox(t("role"), ["user", "admin"], index=["user", "admin"].index(current_role), key=f"role_{email}")
        if new_role != current_role:
            users[email]["role"] = new_role
            if persist_users(users):
                st.success(t("role_changed", email=email, role=new_role))
            else:
                users[email]["role"] = current_role

        # Reset password
        if col4.button(t("password_button"), key=f"reset_{email}"):
            new_temp = generate_temp_password()
            old_password = users[email]["password"]
            users[email]["password"] = hash_password(new_temp)
            if persist_users(users):
                st.success(t("new_temp_password", email=email, password=new_temp))
            else:
                users[email]["password"] = old_password

        # Remover usuário
        if not st.session_state.get(f"confirm_remove_{email}", False):
            col5.button("🗑️", key=f"remove_{email}", on_click=solicitar_remocao, args=(email,))
        else:
            st.warning(t("confirm_remove_user", email=email))
            bcol1, bcol2 = st.columns([1, 1])
            with bcol1:
                st.button(t("confirm"), key=f"confirm_final_{email}", on_click=confirmar_remocao, args=(email,))
            with bcol2:
                st.button(t("cancel"), key=f"cancel_{email}", on_click=cancelar_remocao, args=(email,))

if st.session_state.get("_rerun_flag", False):
    st.session_state["_rerun_flag"] = False
    st.rerun()

show_footer()
