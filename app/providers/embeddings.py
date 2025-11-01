import os
from typing import Any
from langchain.embeddings.base import Embeddings
from langchain_openai import OpenAIEmbeddings as LCOpenAIEmbeddings  # type: ignore
from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore

def build_embeddings() -> Embeddings:
    provider = os.getenv("EMBEDDINGS_PROVIDER", "hf").lower()
    if provider == "openai":
        model = os.getenv("OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small")
        return LCOpenAIEmbeddings(model=model, api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL") or None)
    # default HF
    model = os.getenv("HF_EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    return HuggingFaceEmbeddings(model_name=model)
