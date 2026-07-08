import json
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Any

import numpy as np
from openai import OpenAI

from app.utils.app_config import get_app_info


class EmbeddingProviderError(RuntimeError):
    pass


def _openai_key(info: dict[str, Any]) -> str:
    key = (info.get("openai_api_key") or "").strip()
    if not key:
        raise EmbeddingProviderError(
            "Embeddings OpenAI selecionados, mas nenhuma chave foi configurada."
        )
    return key


@lru_cache(maxsize=2)
def _load_sentence_transformer(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _embed_openai(texts: list[str], model: str) -> np.ndarray:
    info = get_app_info()
    client = OpenAI(api_key=_openai_key(info))
    response = client.embeddings.create(input=texts, model=model)
    return np.array([item.embedding for item in response.data], dtype="float32")


def _embed_sentence_transformers(texts: list[str], model: str) -> np.ndarray:
    model_obj = _load_sentence_transformer(model)
    vectors = model_obj.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
    return np.asarray(vectors, dtype="float32")


def _embed_ollama(texts: list[str], model: str) -> np.ndarray:
    info = get_app_info()
    base_url = (info.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    embeddings = []
    for text in texts:
        payload = {"model": model, "prompt": text}
        request = urllib.request.Request(
            f"{base_url}/api/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120.0) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise EmbeddingProviderError(
                f"Ollama indisponivel em {base_url}. Baixe o modelo de embeddings '{model}' ou escolha outro provider."
            ) from exc
        embeddings.append(data["embedding"])
    return np.array(embeddings, dtype="float32")


def embedding_signature() -> str:
    info = get_app_info()
    provider = (info.get("embedding_provider") or "local").lower()
    if provider == "openai":
        model = info.get("openai_embedding_model", "text-embedding-3-small")
    elif provider == "ollama":
        model = info.get("ollama_embedding_model", "nomic-embed-text")
    else:
        provider = "local"
        model = info.get("local_embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
    return f"{provider}:{model}"


def embed_texts(texts: list[str], batch_size: int = 16) -> np.ndarray:
    info = get_app_info()
    provider = (info.get("embedding_provider") or "local").lower()
    vectors = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        if provider == "openai":
            model = info.get("openai_embedding_model", "text-embedding-3-small")
            batch_vectors = _embed_openai(batch, model)
        elif provider == "ollama":
            model = info.get("ollama_embedding_model", "nomic-embed-text")
            batch_vectors = _embed_ollama(batch, model)
        else:
            model = info.get("local_embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            batch_vectors = _embed_sentence_transformers(batch, model)
        vectors.append(batch_vectors)

    if not vectors:
        return np.empty((0, 0), dtype="float32")
    return np.vstack(vectors).astype("float32")
