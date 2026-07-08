# SOFIA

**Local-first, whitelabel knowledge-base chat with RAG.**

SOFIA is a small Streamlit application for organizing local documents, building
a semantic index, and chatting with that knowledge base through retrieval
augmented generation. It is closer to a local, customizable NotebookLM-style
tool than to an agent orchestration or workflow automation platform.

The acronym comes from Portuguese: **Sistema de Organização e Filtragem
Inteligente de Arquivos**. That expansion only works naturally in Portuguese,
but the project interface supports both Portuguese and English.

By default, SOFIA is designed to run on the user's machine with local data,
local indexes, Ollama for chat, and Ollama or local embeddings. OpenAI is still
available as an optional BYOK provider.

---

## Features

- Folder-based document upload and management.
- PDF, DOCX, XLSX, PPTX, TXT, JSON, CSV, XML, Markdown, HTML, and image ingestion.
- Docling-based chunking when available, with token-based fallback.
- Local, Ollama, or OpenAI embeddings.
- Local FAISS vector index.
- Simple chat over the knowledge base.
- Retrieved sources appended to answers.
- Configurable response profiles.
- Portuguese/English interface selector.
- Whitelabel branding: app name, Portuguese/English subtitles, logo, site link, and model settings.
- Local conversation history.
- Local user panel.

---

## Local-First Mode

SOFIA can run without sending documents to external APIs when configured with:

- `llm_provider = "ollama"`
- `embedding_provider = "ollama"` or `"local"`

In this mode, documents, FAISS index files, users, conversation history, and
configuration stay on the local machine.

OpenAI can be selected from the settings page or via the `OPENAI_API_KEY`
environment variable. This can provide better answers on weaker machines, but
it uses an external API.

---

## FAISS vs LightRAG

SOFIA currently keeps FAISS as the default RAG engine.

FAISS is lightweight, local, simple to operate, and better aligned with a
community whitelabel project. LightRAG + Docling may become an optional adapter
for larger knowledge bases, but it adds another service/process and more
configuration surface for non-technical users.

Recommended direction:

1. Keep FAISS as the community default.
2. Improve incremental indexing and base status visibility.
3. Add LightRAG later as an optional advanced adapter.

---

## Performance

The default query path avoids multiple serial LLM calls. SOFIA retrieves the
most relevant chunks, builds a bounded context, and performs one final LLM call
for the answer.

Current performance controls:

- FAISS index cache in memory.
- Cache invalidation when index files or document metadata change.
- Retrieved context limit via `max_context_tokens`.
- Final prompt limit via `max_prompt_tokens`.
- Answer limit via `max_response_tokens`.
- Optional `ollama_keep_alive` to keep the local model warm.
- Optional `ollama_disable_thinking` for Ollama/model combinations that support `think=false`.
- Retrieved-context summarization disabled by default to reduce latency.
- Tabular analysis in `auto` mode to avoid extra LLM calls unless the question asks for spreadsheet/CSV-style data.

---

## Quick Start

### macOS

Clone the repository, then either double-click:

- `INSTALADOR.command` for first setup;
- `INICIAR_SOFIA.command` for later starts.

Or run from Terminal:

```bash
git clone https://github.com/caporal-studio/sofia.git
cd sofia
./install.sh
```

After the first setup, start SOFIA with:

```bash
./start.sh
```

### Linux

Clone and run from Terminal:

```bash
git clone https://github.com/caporal-studio/sofia.git
cd sofia
./install.sh
```

After the first setup, start SOFIA with:

```bash
./start.sh
```

### Windows

Clone the repository, then double-click or run:

```bat
INSTALADOR.bat
```

After the first setup, start SOFIA with:

```bat
INICIAR_SOFIA.bat
```

### Manual Setup

If you prefer to run the steps manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r app/install/requirements.txt
python app/scripts/setup_inicial.py
streamlit run app/Home.py
```

On Windows, activate the environment with:

```bat
venv\Scripts\activate.bat
```

Open:

```text
http://localhost:8501
```

### First Login

SOFIA does not ship with a hardcoded default email or password.

During `./install.sh`, `INSTALADOR.bat`, or `python app/scripts/setup_inicial.py`,
the setup script asks for the first administrator email and prints a temporary
password in the terminal.

Use those credentials for the first login, then change the password from
**My Profile**.

If you lose the temporary password before logging in, delete the local ignored
file `resources/users.json` and run the setup script again:

```bash
python app/scripts/setup_inicial.py
```

### Ollama

Install Ollama and pull a chat model:

```bash
ollama pull llama3.1:8b
```

Optional, for Ollama embeddings:

```bash
ollama pull nomic-embed-text
```

SOFIA uses Ollama embeddings with `nomic-embed-text` by default. To use local
`sentence-transformers` embeddings without Ollama, install the optional
requirements:

```bash
pip install -r app/install/requirements-optional.txt
```

### Manual Configuration

Copy the examples if you want to edit configuration manually instead of using
the setup script:

```bash
cp resources/sofia_config.example.json resources/sofia_config.json
cp resources/profiles_config.example.json resources/profiles_config.json
```

---

## Configuration

Local configuration is intentionally ignored by Git:

```text
resources/sofia_config.json
```

Main fields:

```json
{
  "llm_provider": "ollama",
  "ollama_base_url": "http://localhost:11434",
  "ollama_model": "llama3.1:8b",
  "ollama_summary_model": "llama3.1:8b",
  "embedding_provider": "ollama",
  "local_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "openai_model": "gpt-4o-mini",
  "openai_summary_model": "gpt-4o-mini",
  "openai_embedding_model": "text-embedding-3-small",
  "openai_api_key": "",
  "ollama_keep_alive": "30m",
  "ollama_num_predict": 2048,
  "ollama_disable_thinking": true,
  "max_context_tokens": 5000,
  "max_prompt_tokens": 8000,
  "max_response_tokens": 2048,
  "conversation_history_pairs": 3,
  "summarize_retrieved_context": false,
  "tabular_analysis_mode": "auto"
}
```

The `*_summary_model` fields allow cheaper or faster models for optional
retrieved-context summarization. That summarization is disabled by default
because it increases latency on small and medium-sized knowledge bases.

Environment variables are also supported. See `.env.example`.

---

## Repository Structure

```text
app/
  Home.py                         # Main Streamlit chat screen
  core/agents.py                  # Response profile wiring
  pages/                          # Streamlit pages
  scripts/setup_inicial.py        # Local setup script
  utils/app_config.py             # Local config and defaults
  utils/i18n.py                   # Portuguese/English UI strings
  utils/llm_provider.py           # OpenAI/Ollama chat providers
  utils/embedding_provider.py     # OpenAI/Ollama/local embeddings
  utils/document_loader.py        # File extraction and chunking
  utils/embedding_utils.py        # FAISS indexing and semantic search

resources/
  sofia_config.example.json
  profiles_config.example.json
  assets/caporal-studio.svg

documentacao/                    # Local user documents, contents ignored
exports/                         # Local exports, contents ignored
public/                          # Local temporary/public files, contents ignored
resources/historico_conversas/   # Local conversation history, JSON ignored
```

These runtime folders are included with `.gitkeep` files so a fresh clone has
the expected structure. Their user-generated contents are ignored by Git.
Local indexes, users, sessions, private config, and conversation JSON files are
also ignored.

---

## Security

Do not commit:

- `resources/sofia_config.json`
- `resources/users.json`
- `resources/session_cookie.json`
- `resources/index.faiss`
- `resources/documents.pkl`
- `resources/historico_conversas/`
- User documents in `documentacao/`

The public repository should contain only examples, code, and assets without
real API keys, email addresses, passwords, user data, or indexed documents.

If you are migrating from an old version that ever contained a real OpenAI key
in Git history, revoke that key in the OpenAI dashboard before reusing the
project.

---

## Whitelabel

SOFIA can be customized from the settings page:

- application name;
- Portuguese and English subtitles;
- logo;
- site/support URL;
- LLM provider;
- embedding provider;
- model names;
- interface language;
- temperature;
- number of retrieved documents;
- minimum similarity score;
- context, prompt, and answer limits;
- tabular analysis strategy;
- response profiles.

---

## Caporal Studio

SOFIA is maintained by Caporal Studio.

Site: https://caporal.studio

## License

MIT. See `LICENSE`.
