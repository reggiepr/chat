import os
from typing import List, Tuple
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from .providers.embeddings import build_embeddings
from .providers.llm import LLMClient

CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma")

def _load_pdfs(paths: List[str]) -> List[Document]:
    docs = []
    for p in paths:
        loader = PyPDFLoader(p)
        docs.extend(loader.load())
    return docs

def _split(docs: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(docs)

def upsert_collection(client_id: str, docs: List[Document]):
    embeddings = build_embeddings()
    Chroma.from_documents(
        docs, embedding=embeddings, 
        collection_name=client_id,
        persist_directory=CHROMA_DIR
    )

def get_retriever(client_id: str, k: int):
    embeddings = build_embeddings()
    vs = Chroma(
        collection_name=client_id,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )
    return vs.as_retriever(search_kwargs={"k": k})

PROMPT = ChatPromptTemplate.from_template(
    """You are a helpful assistant. Use the following context to answer.
    Context:
{context}

Question: {question}


    If the answer is not in the context, say you don't know."""
)

async def answer_question(client_id: str, question: str, top_k: int = 4) -> Tuple[str, List[str]]:
    print("TRYING TO ANSWER QUESTION")
    retriever = get_retriever(client_id, top_k)
    docs = retriever.get_relevant_documents(question)
    print(docs)
    context = "\n\n".join(d.page_content for d in docs)
    sources = list({(d.metadata.get('source') or d.metadata.get('file_path') or 'unknown') for d in docs})

    llm = LLMClient()
    prompt = PROMPT.format_messages(context=context, question=question)
    print("PROMPT=",prompt)
    # exit(1)
    content = await llm.complete([m.dict() for m in prompt])
    return content, sources

async def stream_answer(client_id: str, question: str, top_k: int = 4):
    retriever = get_retriever(client_id, top_k)
    docs = retriever.get_relevant_documents(question)
    context = "\n\n".join(d.page_content for d in docs)
    llm = LLMClient()
    prompt = PROMPT.format_messages(context=context, question=question)
    async for chunk in llm.stream([m.dict() for m in prompt]):
        yield chunk
