import os
from fastapi import Header, HTTPException

API_KEYS = set([k.strip() for k in os.getenv("API_KEYS", "demo-abc123").split(",") if k.strip()])

def require_api_key(x_api_key: str = Header(default=None)):
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    # In production, you'd map api key -> tenant in DB
    # For demo, we assume client_id is provided in body and consistent
    return x_api_key
