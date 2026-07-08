import streamlit as st
import os
from app.utils.auth import encerrar_sessao, carregar_sessao
from app.utils.app_config import get_app_info
from app.utils.i18n import language_selector, localized_subtitle, t

def _current_user_is_admin():
    return st.session_state.get("user", {}).get("role") == "admin"

def _page_link(page: str, *, label: str, icon: str):
    try:
        st.sidebar.page_link(page, label=label, icon=icon)
    except KeyError:
        st.sidebar.markdown(f"{icon} {label}")

def _render_navigation():
    _page_link("Home.py", label=t("home"), icon="🏠")

    if _current_user_is_admin():
        _page_link("pages/Configuracoes.py", label=t("settings"), icon="⚙️")
        _page_link("pages/Gerenciar_Documentos.py", label=t("documents"), icon="📄")
        _page_link("pages/Painel_de_Conversas.py", label=t("conversations"), icon="📂")
        _page_link("pages/Painel_de_Usuarios.py", label=t("users"), icon="👥")

    _page_link("pages/Meu_Perfil.py", label=t("profile"), icon="🙋")

def show_sidebar():
    """Exibe o menu lateral com logo, mensagem padrão e menu de navegação."""
    info = get_app_info()
    _render_navigation()
    st.sidebar.markdown("---")
    language_selector(st.sidebar)
    st.sidebar.markdown("---")

    # Mostra logo se existir
    if info.get("logo_path") and os.path.exists(info["logo_path"]):
        st.sidebar.image(info["logo_path"], width="stretch")

    # Mensagem de boas-vindas
    st.sidebar.markdown(f"## {info['name']}")
    st.sidebar.markdown(localized_subtitle(info))

def show_footer():
    """Exibe o rodapé da página."""
    info = get_app_info()
    url = info.get("url", "https://caporal.studio")
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"<div style='font-size: 0.8rem;'>"
        f"{t('developed_by')} <a href='{url}' target='_blank' style='text-decoration: none; color: inherit;'>{info['author']}</a><br>"
        f"{t('version')} {info['version']} - {info['year']}"
        f"</div>",
        unsafe_allow_html=True
    )
    autenticado, usuario = carregar_sessao()
    sessao_ativa = autenticado or bool(st.session_state.get("user"))

    if sessao_ativa:
        st.sidebar.markdown("---")
        if st.sidebar.button(t("logout"), key="sair"):
            st.sidebar.markdown("""
            <style>
            div.st-key-sair button[data-testid="stBaseButton-secondary"] {
                all: unset; /* reseta completamente */
                font-size: 0.8rem!important;
                padding: 0.25rem 0.5rem!important;
                color: #4a90e2!important;
                cursor: pointer!important;
                text-decoration: underline!important;
            }
            div.st-key-sair button[data-testid="stBaseButton-secondary"]:hover {
                color: #3366cc !important;
            }
            [data-testid="stTextInput"] + div[aria-live="polite"] {
                display: none !important;
            }
            </style>
            """, unsafe_allow_html=True)
            encerrar_sessao()
            st.rerun()
    else:
        st.error(t("session_expired"))
        st.stop()

def fix_menu():
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    [data-testid="stSidebarNavLinkContainer"] a[href$="login"],
    [data-testid="stSidebarNavLinkContainer"] a[href$="reset_password"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)
    from app.utils.compat import apply_runtime_fixes
    apply_runtime_fixes()

def custom_css_home():
    st.markdown("""
    <style>
    .stMainBlockContainer {
        padding-top: 2rem;
        max-width: 1180px;
    }
    </style>
    """, unsafe_allow_html=True)
