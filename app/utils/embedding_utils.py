import os
import pickle
from typing import List, Dict
import faiss
import numpy as np
from app.utils.document_loader import load_documents
from app.utils.app_config import get_app_info
from app.utils.embedding_provider import embed_texts as provider_embed_texts, embedding_signature

INDEX_FAISS_FILE = "resources/index.faiss"
DOCUMENTS_FILE = "resources/documents.pkl"

def embed_texts(texts: List[str], batch_size: int = 10) -> np.ndarray:
    """Gera embeddings usando o provider configurado: local, Ollama ou OpenAI."""
    return provider_embed_texts(texts, batch_size=batch_size)


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms

def create_faiss_index(documents: List[Dict[str, str]]):
    """Cria e salva o índice FAISS e os documentos separadamente."""
    texts = [doc["content"] for doc in documents]
    signature = embedding_signature()
    print(f"Gerando vetores com provider/modelo: {signature}")
    vectors = embed_texts(texts)
    print(f"Gerados {len(vectors)} vetores")

    vectors = _normalize(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    print("Index FAISS criado e vetores adicionados")

    # Salva o índice
    faiss.write_index(index, INDEX_FAISS_FILE)
    print("Indice faiss salvo")

    # Salva os documentos com metadados
    metadata = {
        "embedding_signature": signature,
        "documents": documents
    }
    with open(DOCUMENTS_FILE, "wb") as f:
        pickle.dump(metadata, f)

def load_saved_index():
    """Carrega o índice FAISS e os documentos com metadados."""
    if not os.path.exists(INDEX_FAISS_FILE) or not os.path.exists(DOCUMENTS_FILE):
        raise FileNotFoundError("Os arquivos de índice não foram encontrados. Execute a criação do índice primeiro.")

    index = faiss.read_index(INDEX_FAISS_FILE)

    with open(DOCUMENTS_FILE, "rb") as f:
        data = pickle.load(f)
        documents = data["documents"]

    saved_signature = data.get("embedding_signature")
    current_signature = embedding_signature()
    if saved_signature and saved_signature != current_signature:
        raise ValueError(
            f"Indice criado com embeddings '{saved_signature}', mas a configuracao atual usa '{current_signature}'. Recrie o indice."
        )

    print("Indice faiss carregado")
    return index, documents


def search_similar(query: str, index, documents: List[Dict[str, str]], k: int | None = None, score_threshold: float | None = None) -> List[Dict[str, str]]:
    """Realiza busca de documentos similares a uma query."""
    info = get_app_info()
    k = int(k or info.get("top_k", 5))
    score_threshold = float(score_threshold if score_threshold is not None else info.get("score_similaridade", 0.6))
    k = min(k, len(documents), int(index.ntotal))
    if k <= 0:
        return []

    query_vector = embed_texts([query]).astype("float32")
    query_vector = _normalize(query_vector)
    distances, indices = index.search(query_vector, k)

    similar_documents = []
    for i, idx in enumerate(indices[0]):
        if idx < 0 or idx >= len(documents):
            continue
        score = float(distances[0][i])
        if not np.isfinite(score):
            continue
        print(f"Documento: {documents[idx]['source']} | Score: {round(score, 4)}")
        if score >= score_threshold:
            similar_documents.append({
                **documents[idx],
                "similarity_score": round(score, 4)
            })
    return similar_documents

def create_index():
    """Carrega documentos e cria o índice FAISS."""
    print("Carregando documentos da pasta 'documentacao'...")
    documents = load_documents()

    if not documents:
        raise ValueError("Nenhum documento encontrado na pasta 'documentacao'. Adicione documentos antes de criar o índice.")

    print(f"{len(documents)} documentos carregados. Criando índice...")
    create_faiss_index(documents)
    print("Índice criado e salvo com sucesso.")
