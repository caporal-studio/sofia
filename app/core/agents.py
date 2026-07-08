import os
import json
from typing import Callable, Dict
from app.utils.app_config import get_app_info
from app.utils.llm_provider import chat_completion

AGENTS_FILE = "resources/profiles_config.json"
AGENTS_EXAMPLE_FILE = "resources/profiles_config.example.json"

def load_agent_configs() -> Dict[str, Dict[str, str]]:
    """Carrega a lista de perfis de resposta a partir do JSON de configuração."""
    if os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE, "r", encoding="utf-8") as f:
            agents = json.load(f)
    elif os.path.exists(AGENTS_EXAMPLE_FILE):
        with open(AGENTS_EXAMPLE_FILE, "r", encoding="utf-8") as f:
            agents = json.load(f)
    else:
        agents = []
    if agents:
        return {
            agent["name"]: {
                "instructions": agent["instructions"]
            } for agent in agents
        }
    return {}

def create_agents() -> Dict[str, Callable[[str, str], str]]:
    """Cria funções para cada perfil de resposta configurado."""
    configs = load_agent_configs()
    agent_funcs = {}

    for agent_name, config in configs.items():
        def make_agent(instructions=config["instructions"]):
            def agent(*, pergunta: str, contexto: str) -> str:
                """Recebe prompt completo já preparado pela Home (com contexto documentacional + pergunta + histórico + dado estruturado + fonte)."""
                info = get_app_info()
                response = chat_completion(
                    [
                        {"role": "system", "content": instructions},
                        {"role": "user", "content": contexto}
                    ],
                    max_tokens=int(info.get("max_response_tokens", 2048)),
                )
                return response["text"]

            agent.instructions = instructions
            return agent

        agent_funcs[agent_name] = make_agent()

    return agent_funcs
