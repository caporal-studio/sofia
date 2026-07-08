import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import json
import streamlit as st
from app.utils.app_config import get_app_info, save_app_info
from app.utils.ui_utils import show_sidebar, show_footer, fix_menu
from app.utils.auth import require_admin
from app.utils.i18n import t

# Configurações da página
st.set_page_config(page_title=t("settings"), page_icon="⚙️")
st.title(t("settings_title"))
require_admin()
fix_menu()
show_sidebar()

# Caminho onde salvamos os perfis de resposta
AGENTS_FILE = "resources/profiles_config.json"
AGENTS_EXAMPLE_FILE = "resources/profiles_config.example.json"

def load_agents():
    """Carrega os perfis existentes."""
    if os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    if os.path.exists(AGENTS_EXAMPLE_FILE):
        with open(AGENTS_EXAMPLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_agents(agents):
    """Salva a lista de perfis."""
    os.makedirs(os.path.dirname(AGENTS_FILE), exist_ok=True)
    with open(AGENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)

st.header(t("general_settings"))

info = get_app_info()


def option_index(options, value, default=0):
    try:
        return options.index(value)
    except ValueError:
        return default

# Formulário para alterar configurações gerais
with st.form("config_form"):
    app_name = st.text_input(t("app_name"), value=info["name"])
    subtitle_pt = st.text_input(t("subtitle_pt"), value=info.get("subtitle_pt", info.get("subtitle", "")))
    subtitle_en = st.text_input(t("subtitle_en"), value=info.get("subtitle_en", t("app_subtitle")))
    author = st.text_input(t("brand_author"), value=info.get("author", "Caporal Studio"))
    support_url = st.text_input(t("support_url"), value=info.get("url", "https://caporal.studio"))
    app_base_url = st.text_input(t("app_base_url"), value=info.get("app_base_url", "http://localhost:8501"))
    llm_provider_options = ["ollama", "openai"]
    llm_provider = st.selectbox(
        t("llm_provider"),
        options=llm_provider_options,
        index=option_index(llm_provider_options, info.get("llm_provider", "ollama")),
    )
    openai_model = st.text_input(t("openai_model"), value=info.get("openai_model", "gpt-4o-mini"))
    openai_summary_model = st.text_input(t("openai_summary_model"), value=info.get("openai_summary_model", openai_model))
    openai_api_key = st.text_input(
        t("openai_key"),
        value=info.get("openai_api_key", ""),
        type="password",
    )
    ollama_base_url = st.text_input(t("ollama_url"), value=info.get("ollama_base_url", "http://localhost:11434"))
    ollama_model = st.text_input(t("ollama_model"), value=info.get("ollama_model", "llama3.1:8b"))
    ollama_summary_model = st.text_input(
        t("ollama_summary_model"),
        value=info.get("ollama_summary_model", ollama_model),
    )
    ollama_keep_alive = st.text_input(t("ollama_keep_alive"), value=info.get("ollama_keep_alive", "30m"))
    ollama_num_predict = st.number_input(
        t("ollama_output_tokens"),
        min_value=256,
        max_value=8192,
        value=int(info.get("ollama_num_predict", 2048)),
        step=256,
    )
    ollama_disable_thinking = st.checkbox(
        t("ollama_disable_thinking"),
        value=bool(info.get("ollama_disable_thinking", True)),
    )
    embedding_provider_options = ["local", "ollama", "openai"]
    embedding_provider = st.selectbox(
        t("embedding_provider"),
        options=embedding_provider_options,
        index=option_index(embedding_provider_options, info.get("embedding_provider", "local")),
    )
    local_embedding_model = st.text_input(
        t("local_embedding_model"),
        value=info.get("local_embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
    )
    ollama_embedding_model = st.text_input(
        t("ollama_embedding_model"),
        value=info.get("ollama_embedding_model", "nomic-embed-text"),
    )
    openai_embedding_model = st.text_input(
        t("openai_embedding_model"),
        value=info.get("openai_embedding_model", "text-embedding-3-small"),
    )
    temperature = st.slider(t("temperature"), 0.0, 1.0, value=info["temperature"], step=0.05)
    top_k = st.slider(t("top_k"), 1, 10, value=info["top_k"], step=1)
    score_similaridade = st.slider(t("similarity_score"), 0.0, 1.0, value=info["score_similaridade"], step=0.05)
    max_context_tokens = st.slider(
        t("max_context_tokens"),
        1000,
        16000,
        value=int(info.get("max_context_tokens", 5000)),
        step=500,
    )
    max_prompt_tokens = st.slider(
        t("max_prompt_tokens"),
        2000,
        32000,
        value=int(info.get("max_prompt_tokens", 8000)),
        step=1000,
    )
    max_response_tokens = st.slider(
        t("max_response_tokens"),
        256,
        8192,
        value=int(info.get("max_response_tokens", 2048)),
        step=256,
    )
    summarize_retrieved_context = st.checkbox(
        t("summarize_context"),
        value=bool(info.get("summarize_retrieved_context", False)),
    )
    tabular_modes = ["auto", "always", "off"]
    tabular_analysis_mode = st.selectbox(
        t("tabular_analysis"),
        options=tabular_modes,
        index=option_index(tabular_modes, info.get("tabular_analysis_mode", "auto")),
    )
    logo_file = st.file_uploader(t("upload_logo"), type=["png", "jpg", "jpeg"])
    submit = st.form_submit_button(t("save_settings"))

if submit:
    logo_path = info.get("logo_path", "")
    if logo_file:
        logo_dir = "resources/assets"
        os.makedirs(logo_dir, exist_ok=True)
        logo_path = os.path.join(logo_dir, logo_file.name)
        with open(logo_path, "wb") as f:
            f.write(logo_file.getbuffer())
    save_app_info({
        "name": app_name,
        "subtitle": subtitle_pt,
        "subtitle_pt": subtitle_pt,
        "subtitle_en": subtitle_en,
        "llm_provider": llm_provider,
        "app_base_url": app_base_url,
        "openai_model": openai_model,
        "openai_summary_model": openai_summary_model,
        "openai_api_key": openai_api_key,
        "ollama_base_url": ollama_base_url,
        "ollama_model": ollama_model,
        "ollama_summary_model": ollama_summary_model,
        "ollama_keep_alive": ollama_keep_alive,
        "ollama_num_predict": int(ollama_num_predict),
        "ollama_disable_thinking": ollama_disable_thinking,
        "embedding_provider": embedding_provider,
        "local_embedding_model": local_embedding_model,
        "ollama_embedding_model": ollama_embedding_model,
        "openai_embedding_model": openai_embedding_model,
        "temperature": temperature,
        "top_k": top_k,
        "score_similaridade": score_similaridade,
        "max_context_tokens": max_context_tokens,
        "max_prompt_tokens": max_prompt_tokens,
        "max_response_tokens": max_response_tokens,
        "summarize_retrieved_context": summarize_retrieved_context,
        "tabular_analysis_mode": tabular_analysis_mode,
        "version": info["version"],
        "year": info["year"],
        "author": author,
        "logo_path": logo_path,
        "url": support_url
    })
    st.success(t("settings_saved"))
    st.rerun()

# Seção para gerenciar perfis
st.header(t("manage_profiles"))

agents = load_agents()

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# Lista de perfis existentes
if agents:
    for idx, agent in enumerate(agents):
        st.markdown(f"**{agent['name']}** – {agent['instructions']}")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(t("edit_profile_button", name=agent["name"]), key=f"edit_{idx}"):
                st.session_state.edit_mode = True
                st.session_state.edit_index = idx
        with col2:
            if st.button(t("remove_profile_button", name=agent["name"]), key=f"remove_{idx}"):
                agents.pop(idx)
                save_agents(agents)
                st.success(t("profile_removed", name=agent["name"]))
                st.session_state.edit_mode = False
                st.session_state.edit_index = None
                st.rerun()
else:
    st.info(t("no_profiles_registered"))

st.markdown("---")

# Formulário para criar ou editar perfil
if st.session_state.edit_mode:
    if (
        st.session_state.edit_index is not None and
        0 <= st.session_state.edit_index < len(agents)
    ):
        st.subheader(t("edit_profile"))
        agent_to_edit = agents[st.session_state.edit_index]

        with st.form("edit_agent_form"):
            updated_agent_name = st.text_input(t("profile_name"), value=agent_to_edit["name"])
            updated_agent_instructions = st.text_area(t("profile_instructions"), value=agent_to_edit["instructions"])
            save_edit = st.form_submit_button(t("save_changes"))

        if save_edit:
            agents[st.session_state.edit_index] = {
                "name": updated_agent_name,
                "instructions": updated_agent_instructions
            }
            save_agents(agents)
            st.success(t("profile_updated", name=updated_agent_name))
            st.session_state.edit_mode = False
            st.session_state.edit_index = None
            st.rerun()
    else:
        st.warning(t("selected_profile_missing"))
        st.session_state.edit_mode = False
        st.session_state.edit_index = None
        st.rerun()
else:
    st.subheader(t("create_new_profile"))

    with st.form("create_agent_form"):
        new_agent_name = st.text_input(t("new_profile_name"))
        new_agent_instructions = st.text_area(t("new_profile_instructions"))
        create_agent = st.form_submit_button(t("create_profile"))

    if create_agent:
        if new_agent_name and new_agent_instructions:
            agents.append({
                "name": new_agent_name,
                "instructions": new_agent_instructions
            })
            save_agents(agents)
            st.success(t("profile_created", name=new_agent_name))
            st.rerun()
        else:
            st.error(t("fill_profile_fields"))

show_footer()
