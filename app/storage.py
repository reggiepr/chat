import os, shutil
from pathlib import Path
from typing import Iterable

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./data/uploads")).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def client_dir(client_id: str) -> Path:
    d = UPLOAD_DIR / client_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def save_upload(client_id: str, filename: str, fileobj) -> str:
    dest = client_dir(client_id) / filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(fileobj, f)
    return str(dest)

def list_client_pdfs(client_id: str) -> list[str]:
    d = client_dir(client_id)
    return [str(p) for p in d.glob("*.pdf")]
