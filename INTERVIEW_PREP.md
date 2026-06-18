# Interview Preparation Report
## Customer Support Bot — AI-Powered Multilingual Chatbot

---

## Project Summary (Your 30-Second Pitch)

> "I built a production-ready multilingual customer support chatbot using Python, FastAPI, and the Anthropic Claude API. It supports English and Arabic, classifies user intent, retrieves grounded answers from a local knowledge base using a RAG pipeline with FAISS vector search, filters harmful inputs and outputs for safety, and logs every conversation to CSV. The backend is a REST API and the frontend is a Streamlit chat UI — both containerised with Docker."

---

## SECTION 1 — Architecture & System Design

---

### Q1: Walk me through the overall architecture of this system.

**Answer:**
The system follows a clean layered architecture split into two services:

**Backend (FastAPI)** handles all AI logic:
```
User Message
    ↓
SafetyFilter.check_input()     → blocks PII, injection, empty messages
    ↓
detect_language()              → returns "en" or "ar"
    ↓
IntentClassifier.classify()    → calls Claude API → returns intent JSON
    ↓
RAGService.retrieve()          → searches FAISS vector store → top-3 chunks
    ↓
ResponseGenerator.generate()   → calls Claude API with context + question
    ↓
SafetyFilter.check_output()    → blocks forbidden terms in response
    ↓
InteractionLogger.log()        → appends row to interactions.csv
    ↓
JSON response to client
```

**Frontend (Streamlit)** is a chat UI that sends POST requests to the FastAPI backend and displays the response with language/intent/safety metadata.

They are decoupled — the frontend only knows the backend's URL, which is configurable via environment variable.

---

### Q2: Why did you separate the frontend and backend instead of building one app?

**Answer:**
Separation of concerns and scalability. By splitting them:
- The backend API can be consumed by any client — web, mobile, Slack bot, or another service — without changing the AI logic.
- The backend can be scaled independently (run multiple instances behind a load balancer) while the frontend stays lightweight.
- In Docker, each service runs in its own container. In production you'd scale the backend, not the UI.
- It also makes testing easier — you can test the API directly with tools like Swagger (`/docs`) without needing the UI at all.

---

### Q3: What is the role of `core/chatbot.py` and why did you put the orchestration logic there?

**Answer:**
`CustomerSupportBot` is the single orchestrator that coordinates all services in the correct order. I isolated it in `core/chatbot.py` for three reasons:
1. **Single responsibility** — the FastAPI route (`api/routes.py`) only handles HTTP concerns. The business logic (what happens with a message) lives entirely in the chatbot class.
2. **Testability** — I can instantiate `CustomerSupportBot` in unit tests without starting an HTTP server.
3. **Replaceability** — if I wanted to swap FastAPI for Django or add a CLI interface, I only add a new entry point; the core logic is untouched.

---

### Q4: How does the request flow from the Streamlit UI to the final response?

**Answer:**
1. User types a message in Streamlit (`core/app.py`)
2. Streamlit sends `POST /chat` with `{"user_id": "...", "message": "..."}` to the FastAPI backend
3. FastAPI's router (`api/routes.py`) receives the request, validates it with Pydantic (`ChatRequest` model)
4. The router calls `bot.process(user_id, message)` on the singleton `CustomerSupportBot`
5. The bot runs the full pipeline (safety → language → classify → retrieve → generate → log)
6. A `ChatResponse` dict is returned → FastAPI serialises it to JSON
7. Streamlit receives the JSON, displays `response` in the chat and shows language/intent/safety as metadata captions

---

## SECTION 2 — RAG Pipeline (Retrieval-Augmented Generation)

---

### Q5: What is RAG and why did you use it here instead of just asking Claude directly?

**Answer:**
RAG stands for Retrieval-Augmented Generation. Instead of relying purely on what the LLM was trained on, you first retrieve relevant documents from your own knowledge base and pass them as context to the model.

**Why it matters here:**
- A general-purpose LLM like Claude has no knowledge of this specific company's refund policy, support hours, or account procedures.
- Without RAG, Claude would either hallucinate (make up policies) or give generic answers.
- With RAG, Claude's prompt includes the actual relevant section from `knowledge_base/`, so its answer is grounded in real, accurate company information.
- It's also cheaper and faster than fine-tuning the model.

**The trade-off:** RAG quality depends on retrieval quality. If the knowledge base has gaps or the chunks are too large/small, the retrieved context won't be helpful.

---

### Q6: Explain the ingestion pipeline — how does text become a searchable vector index?

**Answer:**
The pipeline in `vectorstore/ingest.py` has four steps:

**Step 1 — Load documents**
```python
TextLoader("knowledge_base/en/support.txt")
```
Reads all `.txt` files from `knowledge_base/` recursively into LangChain `Document` objects.

**Step 2 — Chunk**
```python
RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
```
Splits long documents into 500-character chunks with 50-character overlap. Overlap ensures a sentence that spans a boundary isn't split and lost.

**Step 3 — Embed**
```python
HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
```
Each chunk is converted to a 384-dimensional dense vector using a sentence transformer model. Semantically similar text has vectors that are close together in this space.

**Step 4 — Index and save**
```python
FAISS.from_documents(chunks, embeddings)
db.save_local("vectorstore/faiss_index")
```
FAISS builds an index optimised for nearest-neighbour search. It's saved to disk as `index.faiss` + `index.pkl` so it doesn't need to be rebuilt on every startup.

---

### Q7: How does retrieval work at query time?

**Answer:**
When a user asks a question:
1. The question text is embedded using the same `all-MiniLM-L6-v2` model
2. FAISS searches the index for the 3 closest chunk vectors using cosine similarity
3. The top-3 matching text chunks are returned
4. They are joined with double newlines and passed as `context` to the Claude prompt

This means the model only sees the most relevant ~1,500 characters from the knowledge base, not the entire document — which keeps prompts focused and costs low.

---

### Q8: Why did you choose `all-MiniLM-L6-v2` as the embedding model?

**Answer:**
It's a strong default choice for semantic search because:
- It's fast and lightweight (22MB) — runs on CPU without GPU
- It produces high-quality 384-dimensional embeddings that capture semantic meaning
- It's one of the most downloaded sentence-transformer models on HuggingFace
- It supports multilingual content well enough for our EN/AR use case

For a production system handling Arabic more precisely, I'd consider upgrading to `paraphrase-multilingual-MiniLM-L12-v2`, which is explicitly trained for 50+ languages including Arabic.

---

### Q9: Why FAISS instead of a cloud vector database like Pinecone?

**Answer:**
For this project, FAISS is the right choice because:
- The knowledge base is small (fits entirely in memory)
- No network latency — search is local and instant
- Zero infrastructure cost or API keys needed
- FAISS is battle-tested at Facebook/Meta scale

For production at scale, I'd migrate to Pinecone or Weaviate when: the knowledge base grows beyond RAM, multiple servers need to share the same index, or real-time updates to the index are needed without restarting the app.

---

## SECTION 3 — Language Model & Claude API

---

### Q10: How does intent classification work?

**Answer:**
`IntentClassifier.classify()` in `services/classifier.py` sends the user message to Claude with a structured prompt:

```
Classify the customer support message into exactly one intent.

Possible intents:
- technical_support
- billing
- account_access
- general_inquiry

Return JSON only: {"intent": "<intent>"}

Message: {message}
```

Key design choices:
- `temperature=0` — deterministic output, no creativity needed for classification
- `max_tokens=50` — forces a short JSON-only response, reduces cost
- I parse the JSON and extract `intent`, with a fallback to `"general_inquiry"` if parsing fails
- The intent is returned to the chatbot, used in the response log, and shown as metadata in the UI

---

### Q11: How does response generation work? What's in the prompt?

**Answer:**
`ResponseGenerator.generate()` in `services/generator.py` builds this prompt:

```
You are a helpful customer support agent.

Answer ONLY using the provided context. If the context does not contain
enough information, politely say so.

Context:
{retrieved_chunks}

Customer question:
{message}

Respond in {English|Arabic}.
```

Key decisions:
- **"Answer ONLY using the provided context"** — prevents hallucination by constraining Claude to the knowledge base
- **"If context doesn't contain enough, say so"** — makes the bot honest rather than guessing
- **Language instruction** — ensures Arabic questions get Arabic answers, even if the retrieved chunks are in English
- `temperature=0` — consistent, factual responses
- `max_tokens=500` — enough for a detailed support answer without runaway costs

---

### Q12: Why do you call the Claude API twice per request (classify + generate)?

**Answer:**
Two calls serve distinct purposes that would conflict if combined:
1. **Classification call** — needs a short, structured JSON output (`max_tokens=50`). The intent label is used for logging and routing.
2. **Generation call** — needs a long, natural-language response (`max_tokens=500`) grounded in context.

Combining them into one prompt would force the model to produce both a JSON label and prose simultaneously, which is harder to parse reliably and makes the prompt more complex. Keeping them separate makes each task cleaner and the code easier to maintain.

**Cost consideration:** The classification call is tiny (50 tokens max). The real cost is in the generation call. This is acceptable for a support bot where answer quality matters.

---

## SECTION 4 — Safety & Security

---

### Q13: Explain your safety filtering strategy.

**Answer:**
`SafetyFilter` in `services/safety.py` applies checks at two points:

**Input filtering (before any AI call):**
- Rejects empty messages
- Detects email addresses with regex — PII should not be sent to an LLM
- Detects prompt injection phrases like `"ignore previous instructions"`, `"system prompt"`, `"hack"` — these are attempts to hijack the AI's behaviour
- If blocked, returns immediately with `safety_status` explaining why — no API calls are made, saving cost

**Output filtering (after generation):**
- Scans the model's response for forbidden terms like `"credit card"`, `"password"`
- If found, replaces the response with a generic safe message

**Why both?** Input filtering protects against malicious users. Output filtering protects against the model accidentally leaking sensitive patterns even from legitimate queries.

---

### Q14: What are the weaknesses of this safety approach and how would you improve it?

**Answer:**
Current weaknesses:
1. **Keyword-based** — a sophisticated prompt injection like `"Disregard prior context"` would bypass the current list
2. **No rate limiting** — a user could spam thousands of requests
3. **Regex PII detection is brittle** — it catches emails but misses phone numbers, credit card numbers, names
4. **No user authentication** — `user_id` is caller-supplied and unverified

Improvements for production:
- Use a dedicated content moderation model (e.g., `claude-3-haiku` with a classifier prompt) for semantic injection detection
- Add rate limiting per `user_id` with Redis
- Use a proper PII detection library (e.g., `presidio` from Microsoft)
- Add JWT authentication on the FastAPI endpoint
- Log all blocked requests separately for security audit

---

## SECTION 5 — Language Detection

---

### Q15: How does language detection work? Why not use a library like `langdetect`?

**Answer:**
`language.py` uses a simple Unicode range check:

```python
arabic_pattern = re.compile(r'[؀-ۿ]')
if arabic_pattern.search(text):
    return "ar"
return "en"
```

**Why this approach instead of `langdetect`:**
- Arabic script is unique — no other major language uses Unicode block `؀-ۿ`. A regex is 100% reliable and instantaneous.
- `langdetect` has known issues with short texts (common in chat), can be non-deterministic, and adds startup overhead.
- For a two-language system (EN/AR), the simpler approach is strictly better.

**Limitation:** This approach can't distinguish Arabic from Farsi (Persian) or Urdu, which also use Arabic script. For the current scope (two languages), it's the right trade-off.

---

## SECTION 6 — API Design & FastAPI

---

### Q16: Why FastAPI over Flask or Django?

**Answer:**
Three main reasons:
1. **Automatic validation** — Pydantic models (`ChatRequest`, `ChatResponse`) validate and type-check every request/response automatically. Flask requires manual validation.
2. **Auto-generated docs** — Swagger UI at `/docs` and ReDoc at `/redoc` are created from the code with zero extra work. Essential for an API that other developers or services will consume.
3. **Async-first** — FastAPI is built on Starlette and supports `async`/`await` natively. When the Claude API calls are slow, the server can handle other requests concurrently. Flask is synchronous by default.

Django would be overkill — it brings an ORM, admin panel, and templating engine we don't need for a pure API service.

---

### Q17: What do the Pydantic models in `models.py` do?

**Answer:**
```python
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    language: str
    intent: str
    safety_status: str
```

They serve as a contract between client and server:
- **Request validation** — FastAPI automatically returns HTTP 422 with a clear error message if `user_id` or `message` is missing or the wrong type. No manual `if` checks needed.
- **Response serialisation** — declaring `response_model=ChatResponse` on the route ensures the returned dict is validated and serialised correctly. Extra fields in the dict are stripped.
- **Documentation** — Pydantic models appear directly in the Swagger UI with field names and types, so consumers know exactly what to send and expect.

---

## SECTION 7 — Configuration & Environment

---

### Q18: How do you manage configuration and why use environment variables?

**Answer:**
`core/config.py` defines a `Settings` class that reads from environment variables via `python-dotenv`:

```python
class Settings:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL      = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    FAISS_INDEX_PATH  = os.getenv("FAISS_INDEX_PATH", "vectorstore/faiss_index")
    LOG_FILE          = os.getenv("LOG_FILE", "logs/interactions.csv")
    BACKEND_URL       = os.getenv("BACKEND_URL", "http://localhost:8000")
```

**Why environment variables:**
- **Security** — the API key never appears in source code. `.env` is in `.gitignore` so it's never committed to git.
- **Portability** — the same codebase runs locally (`.env` file), in Docker (`env_file` in compose), and in cloud (injected by the platform like AWS Secrets Manager or Heroku config vars).
- **12-Factor App** principle — configuration belongs in the environment, not the code.

---

## SECTION 8 — Docker & Deployment

---

### Q19: Walk me through your Docker setup.

**Answer:**
The `dockerfile` builds a single image used by both services:

```dockerfile
FROM python:3.12-slim          # minimal base image
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.yml` defines two services from that image:

```yaml
backend:
  ports: ["8000:8000"]
  env_file: .env               # injects all env vars

frontend:
  command: streamlit run core/app.py --server.address=0.0.0.0
  ports: ["8501:8501"]
  environment:
    BACKEND_URL: http://backend:8000   # internal Docker network name
  depends_on: [backend]
```

Key points:
- `BACKEND_URL=http://backend:8000` — inside Docker, services talk to each other by container name, not `localhost`
- `depends_on` ensures the backend starts before the frontend attempts to connect
- `python:3.12-slim` is used instead of the full image to keep the container small (~150MB vs ~900MB)

---

### Q20: What would you change to make this production-ready?

**Answer:**
Several things:

| Area | Current | Production |
|---|---|---|
| API Security | No auth | JWT / OAuth2 bearer tokens |
| Rate limiting | None | Redis-backed per-user limits |
| Logging | CSV file | Structured JSON logs → ELK stack or CloudWatch |
| Secrets | `.env` file | AWS Secrets Manager / Vault |
| Scaling | Single process | Multiple Uvicorn workers behind Nginx, auto-scaled |
| FAISS index | Local file | Shared storage (EFS/S3) or migrate to Pinecone |
| Error monitoring | None | Sentry |
| CI/CD | None | GitHub Actions: lint → test → build → deploy |
| Health check | None | `GET /health` endpoint for load balancer |
| HTTPS | None | TLS termination at Nginx or load balancer |

---

## SECTION 9 — General Engineering Questions

---

### Q21: How would you add a new intent, e.g. "shipping_inquiry"?

**Answer:**
Three steps:
1. **Update the classifier prompt** in `services/classifier.py` — add `"shipping_inquiry"` to the list of possible intents in the prompt string.
2. **Add knowledge base content** — create or extend a `.txt` file under `knowledge_base/` with shipping-related FAQs.
3. **Rebuild the FAISS index** — run `python -m vectorstore.ingest` to re-embed the new content.

No code changes needed in the chatbot, router, or generator. The architecture is open for extension.

---

### Q22: How would you add a new language, e.g. French?

**Answer:**
1. **`language.py`** — add a French detection branch. French uses Latin script so a simple regex won't work; I'd use `langdetect` for this third language while keeping the Arabic Unicode check.
2. **`knowledge_base/fr/support.txt`** — add French knowledge base content.
3. **`services/generator.py`** — the prompt already passes the language label dynamically (`Respond in {language_label}`), so French would be picked up automatically.
4. **Rebuild the FAISS index** — re-run ingest.

---

### Q23: How would you test this application?

**Answer:**
Three levels:

**Unit tests** — test each service in isolation:
- `SafetyFilter` — test known PII strings, injection phrases, clean inputs
- `detect_language` — test Arabic text, English text, mixed text
- `IntentClassifier` — mock the Anthropic client, assert JSON parsing and fallback

**Integration tests** — test the chatbot pipeline end-to-end:
- Instantiate `CustomerSupportBot` with a real FAISS index and a mocked Anthropic client
- Assert the response dict has the right keys and structure

**API tests** — use FastAPI's `TestClient`:
```python
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
response = client.post("/chat", json={"user_id": "test", "message": "billing question"})
assert response.status_code == 200
assert "response" in response.json()
```

---

### Q24: What happens if the FAISS index doesn't exist when the server starts?

**Answer:**
Currently, `FaissStore.__init__` calls `FAISS.load_local()` immediately on startup. If the index file is missing, it raises a `FileNotFoundError` and the entire FastAPI application fails to start — the bot singleton in `routes.py` is created at import time.

**How to handle it better:**
- Add a startup check: if the index doesn't exist, log a clear error message telling the operator to run `python -m vectorstore.ingest`
- Or make `RAGService.retrieve()` return an empty string gracefully if the store isn't loaded, so the bot can still operate without RAG (just less accurately)
- Add a `GET /health` endpoint that reports index status so a load balancer or CI pipeline can detect this before routing traffic

---

### Q25: What did you learn from this project?

**Answer (personalise this):**
- **RAG pipeline design** — understanding chunking strategy, overlap, and embedding model choice directly impacts answer quality
- **LLM prompt engineering** — small changes to the system prompt (like "Answer ONLY using context") dramatically change model behaviour
- **Python package structure** — keeping imports consistent across a multi-folder project requires discipline with `__init__.py` files and avoiding circular imports
- **Separation of concerns** — splitting the orchestrator (`chatbot.py`), transport (`routes.py`), and each service made the code much easier to debug and extend
- **Safety by design** — filtering at both input and output is more robust than filtering at only one point

---

## Quick-Reference Cheat Sheet

| Concept | What it is | File |
|---|---|---|
| RAG | Retrieve relevant docs before generating answer | `services/rag.py`, `vectorstore/` |
| FAISS | Vector similarity search index | `vectorstore/faiss_store.py` |
| Embeddings | Text → dense vector for semantic search | `vectorstore/ingest.py` |
| Intent | Category of user's request | `services/classifier.py` |
| Safety Filter | Block PII, injection, forbidden output | `services/safety.py` |
| Settings | All config from `.env` | `core/config.py` |
| Orchestrator | Coordinates all services | `core/chatbot.py` |
| API route | Receives HTTP request, calls bot | `api/routes.py` |
| Frontend | Streamlit chat UI | `core/app.py` |
| Logger | CSV append per interaction | `services/logger.py` |

---

*Prepared for interview use — Customer Support Bot project*
