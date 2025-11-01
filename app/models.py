from pydantic import BaseModel, Field
from typing import List, Optional

class RegisterResponse(BaseModel):
    client_id: str
    api_key: str

class IngestRequest(BaseModel):
    client_id: str
    files: Optional[List[str]] = Field(default=None, description="Optional explicit filenames to ingest (defaults to all uploaded PDFs).")
    chunk_size: int = 800
    chunk_overlap: int = 120

class ChatRequest(BaseModel):
    client_id: str
    question: str
    top_k: int = 4
    stream: bool = False

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
