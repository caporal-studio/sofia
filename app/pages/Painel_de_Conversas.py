import streamlit as st
import pandas as pd
import os
import json
import io
from pathlib import Path
from app.utils.ui_utils import show_sidebar, show_footer, fix_menu
from app.utils.auth import require_admin
from app.utils.i18n import t

# Configurações da página
st.set_page_config(page_title=t("conversations"), page_icon="📂")
st.title(t("conversations_title"))
require_admin()
fix_menu()
show_sidebar()

# Caminho da pasta
HIST_DIR = Path("resources/historico_conversas")
HIST_DIR.mkdir(parents=True, exist_ok=True)

# Carrega conversas
conversations = []
file_paths = []
for file in HIST_DIR.glob("*.json"):
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            conversations.append(data)
            file_paths.append(file)
    except Exception as e:
        st.warning(t("load_conversation_error", name=file.name, error=e))

def solicitar_remocao():
    st.session_state[f"confirm_remove_all"] = True

def confirmar_remocao():
    for file in HIST_DIR.glob("*.json"):
        file.unlink()
    st.success(t("conversations_deleted"))
    st.session_state[f"confirm_remove_all"] = False
    st.session_state["_rerun_flag"] = True

def cancelar_remocao():
    st.session_state[f"confirm_remove_all"] = False

# Lista de perfis únicos para filtro
agent_list = list(set([conv["agent"] for conv in conversations]))

# Filtros
all_label = t("all")
selected_agent = st.selectbox(t("filter_by_profile"), [all_label] + agent_list)
search_term = st.text_input(t("search_conversations"))

# Agrupamento
group_options = {
    "none": t("none"),
    "profile": t("group_profile"),
    "theme": t("theme"),
}
group_by = st.radio(
    t("group_conversations_by"),
    options=list(group_options),
    format_func=lambda key: group_options[key],
)

# Aplica filtros
filtered_conversations = conversations
filtered_file_paths = file_paths

if selected_agent != all_label:
    filtered = [(c, f) for c, f in zip(filtered_conversations, filtered_file_paths) if c["agent"] == selected_agent]
    filtered_conversations, filtered_file_paths = zip(*filtered) if filtered else ([], [])

if search_term:
    search_term_lower = search_term.lower()
    filtered = [
        (c, f) for c, f in zip(filtered_conversations, filtered_file_paths)
        if any(search_term_lower in m["content"].lower() for m in c["messages"])
        or search_term_lower in c.get("theme", "").lower()
        or any(search_term_lower in tag.lower() for tag in c.get("tags", []))
    ]
    filtered_conversations, filtered_file_paths = zip(*filtered) if filtered else ([], [])

# Agrupamento
grouped = {}
if group_by == "profile":
    for conv, fpath in zip(filtered_conversations, filtered_file_paths):
        grouped.setdefault(conv["agent"], []).append((conv, fpath))
elif group_by == "theme":
    for conv, fpath in zip(filtered_conversations, filtered_file_paths):
        grouped.setdefault(conv.get("theme", t("untitled")), []).append((conv, fpath))
else:
    grouped = {t("all_conversations"): list(zip(filtered_conversations, filtered_file_paths))}

# Exibição das conversas
for group, convs in grouped.items():
    st.markdown(f"### {group}")
    for idx, (conv, fpath) in enumerate(convs):
        theme = conv.get("theme", t("untitled"))
        tags = ", ".join(conv.get("tags", []))
        date = conv.get("created_at", t("unknown_date"))
        st.markdown(f"**{idx+1}. {theme}** – ({tags}) – {date} – {len(conv['messages'])//2} {t('exchanges')}")

        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            if st.button(f"{t('view')} {group}_{idx}", key=f"ver_{group}_{idx}"):
                st.session_state.messages = conv['messages'].copy()
                st.session_state.current_agent = conv['agent']
                st.success(t("conversation_loaded", agent=conv["agent"]))
        with col2:
            st.download_button(
                t("download_json"),
                data=json.dumps(conv, indent=2),
                file_name=f"{theme}.json",
                key=f"download_json_{group}_{idx}"
            )
        with col3:
            if st.button(t("delete"), key=f"del_{group}_{idx}"):
                os.remove(fpath)
                st.warning(t("conversation_deleted", theme=theme))
                st.rerun()

st.markdown("---")

# Exportar para Excel (filtradas)

# Exibir botão para exportar e apagar conversas
col1, col2 = st.columns([1, 1])
with col1:
    if st.button(t("export_conversations")):
        st.session_state.exportar_excel = True
        export_data = []
        for conv in filtered_conversations:
            agent = conv["agent"]
            theme = conv.get("theme", t("untitled"))
            tags = ", ".join(conv.get("tags", []))
            created_at = conv.get("created_at", t("unknown_date"))
            for idx in range(0, len(conv["messages"]), 2):
                user_msg = conv["messages"][idx]["content"] if idx < len(conv["messages"]) else ""
                assistant_msg = conv["messages"][idx+1]["content"] if (idx+1) < len(conv["messages"]) else ""
                export_data.append({
                    t("export_profile"): agent,
                    t("export_theme"): theme,
                    t("export_tags"): tags,
                    t("export_date"): created_at,
                    t("export_user_message"): user_msg,
                    t("export_system_response"): assistant_msg
                })

        df_export = pd.DataFrame(export_data)

        # Corrigido: usa BytesIO para exportar como Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False)
        buffer.seek(0)

        st.download_button(
            label=t("download_excel"),
            data=buffer,
            file_name="conversas_filtradas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="excel_download_button"
        )

with col2:
    if not st.session_state.get(f"confirm_remove_all", False):
        st.button(t("delete_all_conversations"), on_click=solicitar_remocao)
    else:
        st.warning(t("confirm_delete_all_conversations"))
        bcol1, bcol2 = st.columns([1, 1])
        with bcol1:
            st.button(t("confirm"), on_click=confirmar_remocao)
        with bcol2:
            st.button(t("cancel"), on_click=cancelar_remocao)

if st.session_state.get("_rerun_flag", False):
    st.session_state["_rerun_flag"] = False
    st.rerun()

show_footer()
