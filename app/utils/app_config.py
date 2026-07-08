import json
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

CONFIG_FILE = Path("resources/sofia_config.json")

RUNTIME_DIRS = [
    Path("documentacao"),
    Path("exports"),
    Path("public"),
    Path("resources/assets"),
    Path("resources/historico_conversas"),
]


DEFAULT_CONFIG: dict[str, Any] = {
    "name": "SOFIA",
    "subtitle": "Sistema de Organização e Filtragem Inteligente de Arquivos",
    "subtitle_pt": "Sistema de Organização e Filtragem Inteligente de Arquivos",
    "subtitle_en": "Smart File Organization and Filtering System",
    "version": "1.0",
    "year": "2026",
    "author": "Caporal Studio",
    "url": "https://caporal.studio",
    "app_base_url": "http://localhost:8501",
    "logo_path": "resources/assets/caporal-studio.svg",
    "llm_provider": "ollama",
    "openai_model": "gpt-4o-mini",
    "openai_summary_model": "gpt-4o-mini",
    "openai_embedding_model": "text-embedding-3-small",
    "openai_api_key": "",
    "ollama_base_url": "http://localhost:11434",
    "ollama_model": "llama3.1:8b",
    "ollama_summary_model": "llama3.1:8b",
    "ollama_embedding_model": "nomic-embed-text",
    "ollama_keep_alive": "30m",
    "ollama_num_predict": 2048,
    "ollama_disable_thinking": True,
    "embedding_provider": "ollama",
    "local_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "temperature": 0.4,
    "top_k": 5,
    "score_similaridade": 0.55,
    "max_context_tokens": 5000,
    "max_prompt_tokens": 8000,
    "max_response_tokens": 2048,
    "conversation_history_pairs": 3,
    "summarize_retrieved_context": False,
    "tabular_analysis_mode": "auto",
}


def _with_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    result = dict(config)
    env_map = {
        "SOFIA_LLM_PROVIDER": "llm_provider",
        "SOFIA_APP_BASE_URL": "app_base_url",
        "OPENAI_API_KEY": "openai_api_key",
        "OPENAI_MODEL": "openai_model",
        "OPENAI_SUMMARY_MODEL": "openai_summary_model",
        "OPENAI_EMBEDDING_MODEL": "openai_embedding_model",
        "OLLAMA_BASE_URL": "ollama_base_url",
        "OLLAMA_MODEL": "ollama_model",
        "OLLAMA_SUMMARY_MODEL": "ollama_summary_model",
        "OLLAMA_EMBEDDING_MODEL": "ollama_embedding_model",
        "OLLAMA_KEEP_ALIVE": "ollama_keep_alive",
        "OLLAMA_NUM_PREDICT": "ollama_num_predict",
        "OLLAMA_DISABLE_THINKING": "ollama_disable_thinking",
        "SOFIA_EMBEDDING_PROVIDER": "embedding_provider",
        "SOFIA_LOCAL_EMBEDDING_MODEL": "local_embedding_model",
        "SOFIA_MAX_CONTEXT_TOKENS": "max_context_tokens",
        "SOFIA_MAX_PROMPT_TOKENS": "max_prompt_tokens",
        "SOFIA_MAX_RESPONSE_TOKENS": "max_response_tokens",
        "SOFIA_CONVERSATION_HISTORY_PAIRS": "conversation_history_pairs",
        "SOFIA_SUMMARIZE_RETRIEVED_CONTEXT": "summarize_retrieved_context",
        "SOFIA_TABULAR_ANALYSIS_MODE": "tabular_analysis_mode",
    }
    for env_name, key in env_map.items():
        value = os.getenv(env_name)
        if value:
            default_value = DEFAULT_CONFIG.get(key)
            if isinstance(default_value, bool):
                result[key] = value.lower() in {"1", "true", "yes", "on"}
            elif isinstance(default_value, int):
                try:
                    result[key] = int(value)
                except ValueError:
                    continue
            else:
                result[key] = value
    return result


def get_app_info() -> dict:
    data = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        data.update(saved)
    return _with_env_overrides(data)


def save_app_info(data: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_runtime_directories() -> None:
    for path in RUNTIME_DIRS:
        path.mkdir(parents=True, exist_ok=True)
