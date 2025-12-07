import os, secrets, asyncio
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import RegisterResponse, IngestRequest, ChatRequest, ChatResponse
from .auth import require_api_key
from .storage import save_upload, list_client_pdfs
from .rag import _load_pdfs, _split, upsert_collection, answer_question, stream_answer
from pathlib import Path

from dotenv import load_dotenv
# load_dotenv()
env_path = Path('..') /  '.env'
load_dotenv(dotenv_path=env_path)

# for key, value in os.environ.items():
#     print(f"{key} = {value}")

app = FastAPI(title="RAGBot API", version="0.1.0")

# CORS (adjust for your frontend domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500","https://reginald.ledainsolutions.com", "http://reginald.ledainsolutions.com"],  # lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
def status():
    return {"ok": True}

@app.post("/register", response_model=RegisterResponse)
def register():
    # Demo only: in prod, create a tenant in DB and issue a key
    client_id = secrets.token_hex(6)
    api_key = secrets.token_urlsafe(24)
    return RegisterResponse(client_id=client_id, api_key=api_key)

@app.post("/upload")
async def upload_pdf(client_id: str = Form(...), files: list[UploadFile] = File(...), api_key: str = Depends(require_api_key)):
    # In prod: verify api_key belongs to client_id
    saved = []
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")
        path = save_upload(client_id, f.filename, f.file)
        saved.append(path)
    return {"uploaded": saved}

@app.post("/ingest")
def ingest(req: IngestRequest, api_key: str = Depends(require_api_key)):
    # In prod: verify api_key belongs to req.client_id
    paths = req.files or list_client_pdfs(req.client_id)
    if not paths:
        raise HTTPException(status_code=400, detail="No PDFs found to ingest")
    docs = _load_pdfs(paths)
    chunks = _split(docs, chunk_size=req.chunk_size, chunk_overlap=req.chunk_overlap)
    upsert_collection(req.client_id, chunks)
    return {"ingested": len(chunks), "files": paths}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, api_key: str = Depends(require_api_key)):
    # In prod: verify api_key belongs to req.client_id
    if req.stream:
        async def eventgen():
            async for token in stream_answer(req.client_id, req.question, req.top_k):
                yield f"data: {token}\n\n"
        return StreamingResponse(eventgen(), media_type="text/event-stream")
    answer, sources = await answer_question(req.client_id, req.question, req.top_k)
    return ChatResponse(answer=answer, sources=sources)
