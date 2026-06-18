# CLAUDE.md — Customer Support Bot

## Project Overview
A multilingual (English / Arabic) AI customer support chatbot built with FastAPI, Streamlit, and the Anthropic Claude API. It uses RAG (FAISS + sentence-transformers) to ground answers in a local knowledge base and logs every interaction to CSV.

## Architecture

```
main.py                        FastAPI entry point (project root)
language.py                    Language detection utility (project root)

backend/
  __init__.py
  models.py                    Pydantic request/response models
  prompts/
    response_prompts.py        All Claude prompt templates (classification + generation)
  core/
    config.py                  Settings loaded from .env
    chatbot.py                 Orchestrator: safety → language → classify → retrieve → generate → log
  api/
    routes.py                  POST /chat endpoint
  services/
    safety.py                  Input/output safety filtering (PII, injection, forbidden words)
    classifier.py              Intent classification via Claude API → JSON
    rag.py                     RAG retrieval using FaissStore
    generator.py               Response generation via Claude API
    logger.py                  CSV interaction logger
  vectorstore/
    faiss_store.py             FAISS vector store wrapper (HuggingFace embeddings)
    ingest.py                  One-time ingestion script: knowledge_base/ → FAISS index

Frontend/
  app.py                       Streamlit chat UI

knowledge_base/
  en/support.txt               English knowledge base
  ar/support.txt               Arabic knowledge base
```

## Environment Variables (.env)
| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Required.** Your Anthropic API key (starts with `sk-ant-`) |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Claude model to use for classification and generation |
| `FAISS_INDEX_PATH` | `vectorstore/faiss_index` | Path to the saved FAISS index (relative to project root) |
| `LOG_FILE` | `logs/interactions.csv` | Path for interaction logs |
| `BACKEND_URL` | `http://localhost:8000` | Backend URL used by the Streamlit frontend |

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your API key
Edit `.env` and replace the placeholder with a real `sk-ant-...` key.

### 3. Build the FAISS index (required once, re-run after updating knowledge_base/)
```bash
python -m backend.vectorstore.ingest
```

### 4. Start the FastAPI backend
```bash
uvicorn main:app --reload --port 8000
```

### 5. Start the Streamlit frontend (separate terminal)
```bash
streamlit run Frontend/app.py
```

### Docker (both services together)
```bash
docker-compose up --build
```

## API
| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/chat` | `{"user_id": "str", "message": "str"}` | Submit a support message |

Response: `{"response": "str", "language": "en|ar", "intent": "str", "safety_status": "str"}`

## Intents
- `technical_support` — bugs, app errors, performance
- `billing` — invoices, payments, refunds
- `account_access` — login, password reset, 2FA
- `general_inquiry` — everything else

## Extending the Knowledge Base
Add `.txt` files anywhere under `knowledge_base/` and re-run:
```bash
python -m backend.vectorstore.ingest
```

## Logs
All interactions are appended to `logs/interactions.csv` with columns:
`timestamp, user_id, input_message, detected_language, predicted_intent, retrieved_context, bot_response, safety_status`

## Common Commands
```bash
# Run backend with auto-reload
uvicorn main:app --reload --port 8000

# Run frontend
streamlit run Frontend/app.py

# Rebuild FAISS index
python -m backend.vectorstore.ingest

# Install / update deps
pip install -r requirements.txt
```
