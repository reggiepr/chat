# RAGBot (FastAPI + LangChain + Chroma)

A minimal, production-oriented scaffold for a **multi-tenant RAG chatbot**:

- **FastAPI** backend (file upload, ingest, chat with RAG)
- **LangChain** for retrieval
- **Chroma** vector store (per-tenant collections)
- **OpenAI or Ollama** for the LLM
- **OpenAI or HuggingFace** for embeddings
- **Tiny JS widget** to embed on any website

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit values
uvicorn app.main:app --reload --port 8080
```

Open `http://localhost:8080/docs` for the API.

## Endpoints

- `POST /register` -> returns a demo client_id (in production, wire to your DB/IdP).
- `POST /upload` (multipart) -> upload one or more PDFs for a given client.
- `POST /ingest` -> parse + chunk PDFs and upsert into the client's vector store.
- `POST /chat` -> ask a question; returns answer (JSON). Set `stream=true` for SSE.

## Multi-Tenancy

Each client is isolated by `client_id` (you validate it from the API key). Uploaded files go to `UPLOAD_DIR/{client_id}/`. Vector store is stored in Chroma under a **collection** named `client_id`.

## Embedding on a Website

```html
<script src="https://YOUR_HOST/widget.js" data-client="CLIENT_ID" data-api-key="YOUR_PUBLISHED_WIDGET_KEY"></script>
```

A floating chat bubble will appear; it calls your backend's `/chat` endpoint.

## Local LLM via Ollama

Install and run Ollama, then pull a model (e.g., deepseek-r1). Update `.env`:

```bash
ollama pull deepseek-r1:7b
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=deepseek-r1:7b
```

## Notes

- For production, put FastAPI behind **Nginx** with TLS and auth.
- Replace the demo API key handling with a proper user/tenant store.
- Consider moving to **Qdrant** or **Pinecone** when you scale.
