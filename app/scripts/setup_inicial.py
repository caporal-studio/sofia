import json
import secrets
import re
from pathlib import Path
from app.utils.app_config import DEFAULT_CONFIG, ensure_runtime_directories
from app.utils.auth import hash_password, save_users

CONFIG_FILE = Path("resources/sofia_config.json")
USERS_FILE = Path("resources/users.json")
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
ensure_runtime_directories()

def generate_temp_password():
    return secrets.token_urlsafe(8)

def is_valid_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)

def main():
    # Config LLM
    print("Let's configure SOFIA's AI provider.")
    if not CONFIG_FILE.exists():
        provider = input("Provider [ollama/openai] (default: ollama): ").strip().lower() or "ollama"
        if provider not in {"ollama", "openai"}:
            print("Invalid provider. Use 'ollama' or 'openai'.")
            return

        config = dict(DEFAULT_CONFIG)
        config["llm_provider"] = provider

        if provider == "openai":
            api_key = input("OpenAI key (example: sk-...): ").strip()
            if not api_key.startswith("sk-"):
                print("Invalid key. The key must start with 'sk-'.")
                return
            config["openai_api_key"] = api_key
            config["embedding_provider"] = "openai"
        else:
            model = input("Ollama model (default: llama3.1:8b): ").strip()
            if model:
                config["ollama_model"] = model

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("Local configuration saved.")

    # Primeiro admin
    print("Let's create the first administrator user.")
    if not USERS_FILE.exists():
        email = input("Administrator email: ").strip().lower()
        if not is_valid_email(email):
            print("Invalid email.")
            return

        temp_password = generate_temp_password()
        users = {
            email: {
                "password": hash_password(temp_password),
                "role": "admin",
                "active": True
            }
        }
        save_users(users)
        print("Admin user created successfully!")
        print(f"Temporary password: {temp_password}")
        print("Save this temporary password now. It will not be shown again.")

if __name__ == "__main__":
    main()
