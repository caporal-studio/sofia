import streamlit as st
import pandas as pd
import os
import re
from pathlib import Path
from typing import Optional
from functools import lru_cache
from app.utils.app_config import get_app_info
from app.utils.llm_provider import chat_completion
from app.utils.i18n import t

BASE_FOLDER = "documentacao"

# === Utilitários ===
def listar_arquivos_estruturados():
    arquivos = []
    for root, _, files in os.walk(BASE_FOLDER):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in [".xlsx", ".csv", ".json"]:
                arquivos.append(Path(root) / file)
    return arquivos


def _folder_signature() -> tuple[tuple[str, int, int], ...]:
    files = []
    for path in listar_arquivos_estruturados():
        try:
            stat = path.stat()
            files.append((str(path), stat.st_mtime_ns, stat.st_size))
        except FileNotFoundError:
            continue
    return tuple(sorted(files))

def carregar_arquivo_como_dataframe(caminho: Path) -> Optional[pd.DataFrame]:
    try:
        if caminho.suffix == ".xlsx":
            return pd.read_excel(caminho)
        elif caminho.suffix == ".csv":
            return pd.read_csv(caminho)
        elif caminho.suffix == ".json":
            return pd.read_json(caminho)
    except Exception as e:
        print(f"Erro ao carregar {caminho}: {e}")
    return None


@lru_cache(maxsize=4)
def carregar_dataframes_cached(signature: tuple[tuple[str, int, int], ...]) -> tuple[tuple[str, pd.DataFrame], ...]:
    dataframes = []
    for path_str, _, _ in signature:
        df = carregar_arquivo_como_dataframe(Path(path_str))
        if df is not None:
            dataframes.append((Path(path_str).name, df))
    return tuple(dataframes)

def detectar_intencao_tabular(pergunta: str) -> str | None:
    padroes = {
        r"\btabela\b": "tabela",
        r"\btable\b": "table",
        r"\bbase de dados\b": "base de dados",
        r"\bdatabase\b": "database",
        r"\bplanilha\b": "planilha",
        r"\bspreadsheet\b": "spreadsheet",
        r"\bcsv\b": "csv",
        r"\bexcel\b": "excel",
        r"\bdados\b": "dados",
        r"\bdata\b": "data",
        r"\bcoluna\b": "coluna",
        r"\bcolumn\b": "column",
        r"\blinha\b": "linha",
        r"\brow\b": "row",
        r"\bm[eé]dia\b": "média",
        r"\baverage\b": "average",
        r"\bmean\b": "mean",
        r"\btotal\b": "total",
        r"\bsoma\b": "soma",
        r"\bsum\b": "sum",
    }
    for regex, termo in padroes.items():
        if re.search(regex, pergunta.lower()):
            return termo
    return None

def gerar_insight_tabular(pergunta: str) -> Optional[str]:
    info = get_app_info()
    mode = (info.get("tabular_analysis_mode") or "auto").lower()
    if mode == "off":
        return None

    termo_detectado = detectar_intencao_tabular(pergunta)
    if mode == "auto" and not termo_detectado:
        return None

    for file_name, df in carregar_dataframes_cached(_folder_signature()):
        if df is not None:
            try:
                preview = df.head(30).to_markdown(index=False)
                describe = df.describe(include="all").fillna("").to_string()
                response = chat_completion(
                    [
                        {
                            "role": "system",
                            "content": t("tabular_system", language=t("language_name")),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"{t('tabular_question')}: {pergunta}\n\n"
                                f"{t('tabular_file')}: {file_name}\n\n"
                                f"{t('tabular_sample')}:\n{preview}\n\n"
                                f"{t('tabular_stats')}:\n{describe}"
                            ),
                        },
                    ],
                    max_tokens=600,
                )
                insight = response["text"]
                return t("tabular_result", file_name=file_name, insight=insight)
            except Exception as e:
                print(f"Erro na análise tabular: {e}")
    return None
