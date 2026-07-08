import streamlit as st
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from app.utils.ui_utils import show_sidebar, show_footer, fix_menu
from app.utils.auth import require_admin
from app.utils.i18n import t

# Configurações da página
st.set_page_config(page_title=t("documents"), page_icon="📄")
st.title(t("documents_title"))
require_admin()
fix_menu()
show_sidebar()

DOCUMENTS_FOLDER = "documentacao"
script_path = Path("app/scripts/criar_indice.py").resolve()

# Cria a pasta base se não existir
os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)

# Estado para flag de índice
if "indice_desatualizado" not in st.session_state:
    st.session_state["indice_desatualizado"] = False

# Aviso se houver alterações não reindexadas
if st.session_state["indice_desatualizado"]:
    st.warning(t("index_outdated"))

# Recriar Índice
with st.container():
    if st.button(t("recreate_index"), width="stretch"):
        with st.spinner(t("recreating_index")):
            exit_code = os.system(f"{sys.executable} {script_path}")
        if exit_code == 0:
            st.success(t("index_recreated"))
            st.session_state["indice_desatualizado"] = False
        else:
            st.error(t("index_recreate_error"))

st.markdown("---")

# Criar nova subpasta
st.subheader(t("create_folder"))
nova_subpasta = st.text_input(t("folder_name"))
if st.button(t("create_folder_button")):
    if nova_subpasta:
        nova_path = os.path.join(DOCUMENTS_FOLDER, nova_subpasta)
        os.makedirs(nova_path, exist_ok=True)
        st.session_state["indice_desatualizado"] = True
        st.success(t("folder_created", name=nova_subpasta))
        st.rerun()
    else:
        st.warning(t("invalid_folder_name"))

st.markdown("---")

# Upload com seleção de subpasta
def listar_subpastas(base_path):
    subpastas = ["."]
    for root, dirs, _ in os.walk(base_path):
        for d in dirs:
            sub_path = os.path.relpath(os.path.join(root, d), base_path)
            subpastas.append(sub_path)
    return sorted(subpastas)

st.subheader(t("upload_documents"))
subpastas = listar_subpastas(DOCUMENTS_FOLDER)
destino = st.selectbox(t("select_folder"), subpastas)

uploaded_files = st.file_uploader(
    t("choose_files"),
    type=["pdf", "docx", "xlsx", "pptx", "txt", "json", "csv", "xml", "md", "html", "htm", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    destino_path = os.path.join(DOCUMENTS_FOLDER, destino) if destino != "." else DOCUMENTS_FOLDER
    os.makedirs(destino_path, exist_ok=True)
    for uploaded_file in uploaded_files:
        save_path = os.path.join(destino_path, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(t("upload_success", name=uploaded_file.name, folder=destino))
    st.session_state["indice_desatualizado"] = True
    st.rerun()

st.markdown("---")

# Listagem de documentos e operações
st.subheader(t("existing_documents"))

def list_documents_grouped(base_path):
    grouped = {}
    for root, _, files in os.walk(base_path):
        rel_dir = os.path.relpath(root, base_path)
        for file in files:
            full_path = os.path.join(root, file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%d/%m/%Y %H:%M")
            grouped.setdefault(rel_dir, []).append((file, mod_time))
    return grouped

document_groups = list_documents_grouped(DOCUMENTS_FOLDER)

if any(document_groups.values()):
    for folder, files in sorted(document_groups.items()):
        with st.expander(f"📁 {folder}" if folder != "." else t("root_folder")):
            for file_name, mod_time in sorted(files):
                relative_path = os.path.join(folder, file_name) if folder != "." else file_name
                full_path = os.path.join(DOCUMENTS_FOLDER, relative_path)
                col1, col2, col3, col4 = st.columns([5, 2, 2, 1])
                col1.markdown(f"📄 **{file_name}**")
                col2.markdown(f"🕒 *{mod_time}*")
                destino_pastas = listar_subpastas(DOCUMENTS_FOLDER)
                nova_destino = col3.selectbox(t("move_to"), destino_pastas, key=f"move_{relative_path}", label_visibility="collapsed")
                if col3.button("🔄", key=f"btn_move_{relative_path}"):
                    novo_path = os.path.join(DOCUMENTS_FOLDER, nova_destino, file_name)
                    shutil.move(full_path, novo_path)
                    st.session_state["indice_desatualizado"] = True
                    st.success(t("moved_to", folder=nova_destino))
                    st.rerun()
                if col4.button("❌", key=f"del_{relative_path}", help=t("delete_file", name=file_name)):
                    os.remove(full_path)
                    st.session_state["indice_desatualizado"] = True
                    st.success(t("file_removed", name=file_name))
                    st.rerun()

    # Excluir subpastas vazias
    for root, dirs, _ in os.walk(DOCUMENTS_FOLDER, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not os.listdir(dir_path):
                rel_path = os.path.relpath(dir_path, DOCUMENTS_FOLDER)
                if st.button(t("delete_empty_folder", name=rel_path), key=f"del_dir_{rel_path}"):
                    os.rmdir(dir_path)
                    st.session_state["indice_desatualizado"] = True
                    st.success(t("folder_removed", name=rel_path))
                    st.rerun()
else:
    st.info(t("no_documents"))

show_footer()
