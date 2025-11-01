import os, json, httpx, asyncio
from typing import AsyncGenerator, List, Dict, Any

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        print("PROVIDER=", self.provider)
        if self.provider == "openai":
            self.base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
            self.key = os.getenv("OPENAI_API_KEY")
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        else:
            self.base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
            self.model = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")

    async def complete(self, messages: List[Dict[str, str]]) -> str:
        if self.provider == "openai":
            async with httpx.AsyncClient(timeout=None) as client:
                print("COMPLETE=",  f"{self.base}/chat/completions")
                r = await client.post(
                    f"{self.base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.key}"} if self.key else {},
                    json={"model": self.model, "messages": messages, "temperature": 0.2},
                )
                r.raise_for_status()
                data = r.json()
                return data["choices"][0]["message"]["content"]
        # Ollama
        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(
                f"{self.base}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("message", {}).get("content", "")

    async def stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        if self.provider == "openai":
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.key}"} if self.key else {},
                    json={"model": self.model, "messages": messages, "temperature": 0.2, "stream": True},
                ) as r:
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if not line or not line.startswith("data:"): 
                            continue
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            payload = json.loads(line.removeprefix("data:").strip())
                            delta = payload["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue
            return
        # Ollama streaming
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base}/api/chat",
                json={"model": self.model, "messages": messages, "stream": True},
            ) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        token = obj.get("message", {}).get("content", "")
                        if token:
                            yield token
                    except Exception:
                        continue
