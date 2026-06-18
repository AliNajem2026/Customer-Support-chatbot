<div align="center">

# Customer Support Bot

### Production-ready multilingual AI customer support chatbot

**English · Arabic · **

</div>

---

## Overview

**Customer Support Bot** is a full-stack AI application that handles customer support inquiries in English and Arabic. It automatically detects the user's language, classifies their intent, retrieves grounded answers from a private knowledge base using RAG, generates responses via the Claude API, and logs every interaction — all through a clean REST API and interactive chat UI.

> Built as a complete end-to-end system: from prompt engineering and vector search to containerised deployment.

---

## Features

| Feature | Description |
|---|---|
| **Multilingual** | Automatic detection of English and Arabic with language-aware responses |
| **Intent Classification** | Claude classifies every message into one of four support intents |
| **RAG Pipeline** | FAISS vector search retrieves the most relevant knowledge base chunks before generation |
| **Safety Filtering** | Blocks PII, prompt injection attempts, and forbidden output patterns at both input and output |
| **Centralized Prompts** | All Claude prompt templates are isolated in `backend/prompts/` for easy iteration |
| **Interaction Logging** | Every conversation is appended to a structured CSV log |
| **REST API** | FastAPI backend with auto-generated Swagger docs |
| **Chat UI** | Streamlit frontend with real-time chat, metadata display, and example queries |
| **Docker Deployment** | Single `docker-compose up --build` to run both services |

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│             Streamlit Chat UI                    │
│         Frontend/app.py · port 8501              │
└─────────────────────┬────────────────────────────┘
                      │  POST /chat
                      │  {"user_id": "...", "message": "..."}
┌─────────────────────▼────────────────────────────┐
│           FastAPI Backend · port 8000            │
│                  main.py                         │
│                                                  │
│  ┌───────────────────────────────────────────┐   │
│  │      CustomerSupportBot (chatbot.py)      │   │
│  │                                           │   │
│  │  1 ▶ SafetyFilter.check_input()           │   │
│  │      Block PII / prompt injection         │   │
│  │                                           │   │
│  │  2 ▶ detect_language()                    │   │
│  │      "en"  or  "ar"                       │   │
│  │                                           │   │
│  │  3 ▶ IntentClassifier.classify()          │   │
│  │      Claude API → JSON intent             │   │
│  │      Prompt: classify_prompts.py          │   │
│  │                                           │   │
│  │  4 ▶ RAGService.retrieve()                │   │
│  │      FAISS similarity search → top-3      │   │
│  │                                           │   │
│  │  5 ▶ ResponseGenerator.generate()         │   │
│  │      Claude API + context + question      │   │
│  │      Prompt: response_prompts.py          │   │
│  │                                           │   │
│  │  6 ▶ SafetyFilter.check_output()          │   │
│  │      Block forbidden terms in response    │   │
│  │                                           │   │
│  │  7 ▶ InteractionLogger.log()              │   │
│  │      Append row to interactions.csv       │   │
│  └───────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

---

## Project Structure

```
Customer-Support-Bot/
│
├── main.py                        # FastAPI application entry point
├── language.py                    # Language detection (Arabic Unicode / English fallback)
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── .gitignore
├── dockerfile
├── docker-compose.yml
├── CLAUDE.md                      # Developer guide for Claude Code
│
├── backend/
│   ├── models.py                  # Pydantic ChatRequest / ChatResponse schemas
│   │
│   ├── prompts/                   # ★ All Claude prompt templates
│   │   ├── response_prompts.py    # classification_prompt() + response_generation_prompt()
│   │   └── classify_prompts.py
│   │
│   ├── core/
│   │   ├── config.py              # Settings loaded from .env
│   │   └── chatbot.py             # Main orchestration logic
│   │
│   ├── api/
│   │   └── routes.py              # POST /chat route definition
│   │
│   ├── services/
│   │   ├── safety.py              # Input / output safety filter
│   │   ├── classifier.py          # Intent classification via Claude API
│   │   ├── rag.py                 # RAG retrieval (FAISS)
│   │   ├── generator.py           # Response generation via Claude API
│   │   └── logger.py              # CSV interaction logger
│   │
│   └── vectorstore/
│       ├── faiss_store.py         # FAISS wrapper (HuggingFace embeddings)
│       └── ingest.py              # Knowledge base → FAISS index script
│
├── Frontend/
│   └── app.py                     # Streamlit chat UI
│
└── knowledge_base/
    ├── en/
    │   └── support.txt            # English support articles
    └── ar/
        └── support.txt            # Arabic support articles
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 or higher |
| Anthropic API Key | `sk-ant-api03-...` — get one at [console.anthropic.com](https://console.anthropic.com) |
| Docker *(optional)* | For containerised deployment |

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/AliNajem2026/Customer-Support-chatbot.git
cd Customer-Support-chatbot
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS / Linux
python -m venv env
source env/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in your Anthropic API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-api03-your-real-key-here
CLAUDE_MODEL=claude-sonnet-4-6
FAISS_INDEX_PATH=backend/vectorstore/faiss_index
LOG_FILE=logs/interactions.csv
BACKEND_URL=http://localhost:8000
```

> **Important:** Anthropic API keys start with `sk-ant-`. Keys from OpenAI (`sk-proj-...`) or other providers will not work.

### 5. Build the FAISS vector index

Run once after setup, and again whenever you update the knowledge base:

```bash
python -m backend.vectorstore.ingest
```

Expected output:
```
Ingested 2 documents → 12 chunks → saved to 'backend/vectorstore/faiss_index'
```

### 6. Start the FastAPI backend

```bash
uvicorn main:app --reload --port 8000
```

The API is now live at:
- **Base URL:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### 7. Start the Streamlit frontend *(new terminal)*

```bash
streamlit run Frontend/app.py
```

The chat UI is now live at `http://localhost:8501`

---

## Docker Deployment

Run the entire stack with one command:

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| FastAPI backend | `http://localhost:8000` |
| Streamlit frontend | `http://localhost:8501` |

To stop:

```bash
docker-compose down
```

---

## API Reference

### `POST /chat`

Submit a customer support message and receive a classified, grounded response.

**Request Body**

```json
{
  "user_id": "user_001",
  "message": "I cannot log in to my account"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `user_id` | string | ✅ | Unique identifier for the user session |
| `message` | string | ✅ | The customer's support message |

**Response**

```json
{
  "response": "To reset your password, visit the login page and click 'Forgot Password'. Check your spam folder if you don't receive the email within 5 minutes.",
  "language": "en",
  "intent": "account_access",
  "safety_status": "Safe"
}
```

| Field | Type | Description |
|---|---|---|
| `response` | string | Generated support answer grounded in the knowledge base |
| `language` | `"en"` \| `"ar"` | Detected language of the input message |
| `intent` | string | Classified intent category |
| `safety_status` | string | `"Safe"`, `"PII detected"`, `"Prompt Injection Detected"`, etc. |

**Example — Arabic input**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_002", "message": "أين أجد الفاتورة؟"}'
```

```json
{
  "response": "يمكنك عرض وتنزيل الفواتير من لوحة التحكم تحت قسم الفوترة.",
  "language": "ar",
  "intent": "billing",
  "safety_status": "Safe"
}
```

---

## Intent Categories

| Intent | Triggers |
|---|---|
| `technical_support` | Bugs, app errors, crashes, performance issues |
| `billing` | Invoices, payments, refunds, subscription pricing |
| `account_access` | Login problems, password reset, 2FA issues |
| `general_inquiry` | Anything else |

---

## Prompt Architecture

All Claude prompts live in `backend/prompts/` — separated from business logic so they can be iterated without touching service code.

| File | Function | Used By |
|---|---|---|
| `response_prompts.py` | `classification_prompt(message)` | `classifier.py` |
| `response_prompts.py` | `response_generation_prompt(question, context, language)` | `generator.py` |

---

## Safety Filtering

Safety checks run at **two points** in every request:

**Input (before any API call)**
- Empty message → rejected
- Email address pattern detected → `"PII detected"`
- Phrases like `"ignore previous instructions"`, `"system prompt"` → `"Prompt Injection Detected"`

**Output (after generation)**
- Scans the generated response for forbidden terms (`"credit card"`, `"password"`)
- If found, replaces the response with a generic safe message

---

## Extending the Knowledge Base

1. Add `.txt` files anywhere under `knowledge_base/` (subdirectories are supported)
2. Rebuild the FAISS index:

```bash
python -m backend.vectorstore.ingest
```

---

## Interaction Log

Every conversation is appended to `logs/interactions.csv`:

| Column | Description |
|---|---|
| `timestamp` | UTC ISO-8601 timestamp |
| `user_id` | Caller-supplied identifier |
| `input_message` | Original user message |
| `detected_language` | `en` or `ar` |
| `predicted_intent` | Classified intent |
| `retrieved_context` | First 300 characters of RAG context |
| `bot_response` | Generated response |
| `safety_status` | Result of input safety check |

---

## Example Queries

**English**

```
I cannot login to my account
Where can I see my invoice?
I found a bug in the app
How do I cancel my subscription?
How do I enable two-factor authentication?
```

**Arabic**

```
لا أستطيع تسجيل الدخول
أين أجد الفاتورة؟
لدي مشكلة في التطبيق
كيف أتواصل مع الدعم؟
كيف أعيد تعيين كلمة المرور؟
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | [Anthropic Claude](https://anthropic.com) `claude-sonnet-4-6` | Intent classification & response generation |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) | REST API server |
| **Frontend** | [Streamlit](https://streamlit.io) | Interactive chat UI |
| **Vector DB** | [FAISS](https://github.com/facebookresearch/faiss) | Semantic similarity search |
| **Embeddings** | [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Text → vector encoding |
| **RAG Framework** | [LangChain](https://www.langchain.com) | Document loading, chunking, retrieval |
| **Validation** | [Pydantic](https://docs.pydantic.dev) | Request/response schema enforcement |
| **Config** | [python-dotenv](https://pypi.org/project/python-dotenv) | Environment variable management |
| **Containerisation** | [Docker](https://docker.com) + Compose | Deployment |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Required.** Anthropic API key (`sk-ant-api03-...`) |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Claude model ID |
| `FAISS_INDEX_PATH` | `backend/vectorstore/faiss_index` | Path to the FAISS index directory |
| `LOG_FILE` | `logs/interactions.csv` | Interaction log file path |
| `BACKEND_URL` | `http://localhost:8000` | Backend URL used by the Streamlit frontend |

---

## Security

- `.env` is excluded from version control via `.gitignore` — API keys are never committed
- `env/` virtualenv is excluded — no package files in the repository
- Input safety filter blocks PII and prompt injection before any LLM call
- Output safety filter screens all generated responses before returning to the client

---

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Build FAISS index (run once, or after updating knowledge_base/)
python -m backend.vectorstore.ingest

# Start backend (with auto-reload)
uvicorn main:app --reload --port 8000

# Start frontend
streamlit run Frontend/app.py

# Run both with Docker
docker-compose up --build
```

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Built with [Anthropic Claude](https://anthropic.com) · [FastAPI](https://fastapi.tiangolo.com) · [Streamlit](https://streamlit.io) · [FAISS](https://github.com/facebookresearch/faiss)

</div>
