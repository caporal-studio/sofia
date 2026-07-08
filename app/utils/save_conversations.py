import os
import json
from datetime import datetime

HIST_DIR = "resources/historico_conversas"
os.makedirs(HIST_DIR, exist_ok=True)

def registrar_conversa_finalizada(agente: str, mensagens: list) -> None:
    """
    Salva uma conversa finalizada como um arquivo .json individual em disco.
    Cada arquivo é nomeado com data, hora e nome do perfil de resposta.
    """
    if not mensagens:
        return

    tema = mensagens[0]["content"][:120] if mensagens else "Nova conversa"
    data = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"{data}_{agente}.json"

    conversa = {
        "agent": agente,
        "messages": mensagens,
        "theme": tema,
        "tags": [],
        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    caminho = os.path.join(HIST_DIR, nome_arquivo)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(conversa, f, ensure_ascii=False, indent=2)
