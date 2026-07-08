import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pathlib import Path
import streamlit as st
from app.utils.embedding_utils import (
    DOCUMENTS_FILE,
    INDEX_FAISS_FILE,
    load_saved_index,
    search_similar,
    create_index,
)
from app.utils.embedding_provider import embedding_signature
from app.utils.ui_utils import show_sidebar, show_footer, fix_menu, custom_css_home
from app.core.agents import create_agents
from app.utils.app_config import ensure_runtime_directories, get_app_info
from app.utils.save_conversations import registrar_conversa_finalizada
from app.utils.structured_agent_helper import gerar_insight_tabular
from app.utils.auth import require_login
from app.utils.llm_provider import chat_completion
from app.utils.i18n import localized_subtitle, t
import tiktoken

# Inicialização
ensure_runtime_directories()
info = get_app_info()

# Configurações de página
st.set_page_config(page_title=info["name"], layout="wide")
require_login()
fix_menu()
show_sidebar()

# Custom CSS
custom_css_home()

# Estado inicial
agents = create_agents()
agent_names = list(agents.keys())

# Sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_agent" not in st.session_state:
    st.session_state.current_agent = None

if "conversations" not in st.session_state:
    st.session_state.conversations = []

if "input_query" not in st.session_state:
    st.session_state.input_query = ""

if "query_ready" not in st.session_state:
    st.session_state.query_ready = ""

# Cabeçalho com seleção de perfil
st.title(info["name"])
st.caption(localized_subtitle(info))

selected_agent_name = None
selected_agent = None
modelo_configurado = info.get("openai_model") if info.get("llm_provider") == "openai" else info.get("ollama_model")


def get_summary_model() -> str:
    if info.get("llm_provider") == "openai":
        return info.get("openai_summary_model") or info.get("openai_model")
    return info.get("ollama_summary_model") or info.get("ollama_model")


def get_int_config(key: str, default: int) -> int:
    try:
        return int(info.get(key, default))
    except (TypeError, ValueError):
        return default


@st.cache_resource(show_spinner=False)
def cached_load_index(index_mtime_ns: int, docs_mtime_ns: int, signature: str):
    return load_saved_index()


def get_index_and_documents():
    index_path = Path(INDEX_FAISS_FILE)
    docs_path = Path(DOCUMENTS_FILE)
    return cached_load_index(
        index_path.stat().st_mtime_ns,
        docs_path.stat().st_mtime_ns,
        embedding_signature(),
    )

col1, col2 = st.columns([4, 1], vertical_alignment="bottom")
with col1:
    if not agents:
        st.warning(t("no_profiles"))
    else:
        selected_agent_name = st.selectbox(t("profile_response"), options=agent_names)
        selected_agent = agents.get(selected_agent_name)
        if selected_agent_name and selected_agent_name != st.session_state.current_agent:
            previous_agent = st.session_state.current_agent
            if previous_agent and st.session_state.messages:
                registrar_conversa_finalizada(
                    agente=previous_agent,
                    mensagens=st.session_state.messages.copy()
                )
            st.session_state.current_agent = selected_agent_name
            st.session_state.messages = []
            if previous_agent:
                st.success(t("new_chat_with", name=selected_agent_name))
with col2:
    if st.button(t("new_chat"), key="nova_conversa"):
        registrar_conversa_finalizada(
            agente=st.session_state.current_agent,
            mensagens=st.session_state.messages.copy()
        )
        st.session_state.messages = []
        st.session_state.query_ready = ""
        st.session_state.input_temp = ""
        st.success(t("new_chat_started"))

st.divider()

# Funções de resumo para o perfil
def resumir_documento(texto: str) -> str:
    if len(texto) > 8000:
        texto = texto[:8000] + f"\n\n{t('partial_text_notice')}"
    try:
        resp = chat_completion(
            [
                {"role": "system", "content": t("summary_system")},
                {"role": "user", "content": texto}
            ],
            model=get_summary_model(),
            timeout=120.0,
            max_tokens=700,
        )
        return resp["text"]
    except Exception as e:
        st.warning(t("summary_error", error=e))
        return texto[:3000] + f"\n\n{t('context_truncated_notice')}"

# Funções auxiliares
def limpar_nome_fonte(path: str) -> str:
    return path.split("[parte")[0].strip()

def obter_contexto_conversacional(max_pares: int | None = None):
    max_pares = max_pares if max_pares is not None else get_int_config("conversation_history_pairs", 3)
    mensagens = st.session_state.messages
    contexto = []

    pares = [mensagens[i:i+2] for i in range(len(mensagens)-1) if mensagens[i]['role'] == 'user']
    ultimos_pares = pares[-max_pares:]

    for par in ultimos_pares:
        if len(par) == 2:
            contexto.append(
                f"👤 {t('conversation_user')}: {par[0]['content']}\n"
                f"🤖 {t('conversation_assistant')}: {par[1]['content']}"
            )

    return "\n\n".join(contexto)

contexto_conversacional = obter_contexto_conversacional()

def limitar_prompt_por_token(prompt: str, modelo=modelo_configurado, max_tokens=8000) -> str:
    try:
        enc = tiktoken.encoding_for_model(modelo)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    tokens = enc.encode(prompt)
    if len(tokens) > max_tokens:
        tokens = tokens[-max_tokens:]
    return enc.decode(tokens)


def montar_contexto_documentos(top_docs: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    unique_docs = list({doc["source"]: doc for doc in top_docs}.values())
    if not unique_docs:
        return "", []

    raw_context = "\n\n---\n\n".join(
        f"Fonte: {doc['source']}\nSimilaridade: {doc.get('similarity_score', '')}\n\n{doc['content']}"
        for doc in unique_docs
    )
    contexto = limitar_prompt_por_token(
        raw_context,
        modelo=modelo_configurado,
        max_tokens=get_int_config("max_context_tokens", 5000),
    )

    if info.get("summarize_retrieved_context", False):
        with st.spinner(t("summarizing_context")):
            contexto = resumir_documento(contexto)

    return contexto, unique_docs

# Processamento da pergunta
if st.session_state.query_ready:
    query = st.session_state.query_ready
    st.session_state.query_ready = ""

    if st.session_state.current_agent in agents:
        selected_agent = agents[st.session_state.current_agent]
    else:
        st.warning(t("no_profile_selected"))
        st.stop()
    st.session_state.messages.append({"role": "user", "content": query})

    # Detecta pergunta tabular
    insight_tabular = gerar_insight_tabular(query)
    contexto_extra = insight_tabular or ""

    selected_agent = agents.get(st.session_state.current_agent)
    with st.spinner(t("analyzing_documents")):
        try:
            index, documents = get_index_and_documents()
        except (FileNotFoundError, ValueError):
            create_index()
            cached_load_index.clear()
            index, documents = get_index_and_documents()
            st.success(t("index_created"))

        top_docs = search_similar(query, index, documents, k=info["top_k"])

        if not top_docs:
            st.warning(t("no_relevant_docs"))
            contexto_resumido = ""
            retrieved_docs = []
        else:
            contexto_resumido, retrieved_docs = montar_contexto_documentos(top_docs)

        fontes_unicas = sorted({limpar_nome_fonte(doc["source"]) for doc in retrieved_docs}) if retrieved_docs else []
        sources = "\n".join(f"- {fonte}" for fonte in fontes_unicas)
        footer = f"\n\n---\n{t('sources_used')}\n{sources}" if sources else ""
        contexto_tabular = f"\n\n{contexto_extra}" if contexto_extra else ""
        prompt_completo = (
            f"{contexto_conversacional}\n\n"
            f"{t('answer_language')}: {t('language_name')}\n\n"
            f"{t('response_language_instruction', language=t('language_name'))}\n\n"
            f"{t('current_question')}: {query}\n\n"
            f"{t('document_context')}:\n{contexto_resumido}"
            f"{contexto_tabular}"
        )
        prompt_completo = limitar_prompt_por_token(
            prompt_completo,
            modelo=modelo_configurado,
            max_tokens=get_int_config("max_prompt_tokens", 8000),
        )
        resposta_final = selected_agent(pergunta="", contexto=prompt_completo) + footer
        st.session_state.messages.append({"role": "assistant", "content": resposta_final})
        st.session_state.last_query = query
        st.session_state.last_context = contexto_resumido
        st.session_state.last_prompt = prompt_completo
        st.session_state.last_footer = footer
        registrar_conversa_finalizada(st.session_state.current_agent, st.session_state.messages)
        st.rerun()

# Interface do chat
for i, m in enumerate(st.session_state.messages):
    avatar = "👤" if m["role"] == "user" else "🤖"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"])
        if m["role"] == "assistant" and i == len(st.session_state.messages) - 1 and "last_query" in st.session_state:
            if st.button(t("regenerate"), key="nova_resposta"):
                with st.spinner(t("loading_new_answer")):
                    prompt_regeneracao = st.session_state.get("last_prompt", st.session_state.last_context)
                    nova_resposta = selected_agent(contexto=prompt_regeneracao, pergunta=st.session_state.last_query)
                    nova_resposta += st.session_state.get("last_footer", "")
                    st.session_state.messages[-1] = {"role": "assistant", "content": nova_resposta}
                    registrar_conversa_finalizada(st.session_state.current_agent, st.session_state.messages)
                    st.rerun()

prompt = st.chat_input(t("chat_input"))
if prompt and prompt.strip():
    st.session_state.query_ready = prompt.strip()
    st.rerun()

show_footer()
