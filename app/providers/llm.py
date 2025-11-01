import os, json, httpx, asyncio, sys
from typing import AsyncGenerator, List, Dict, Any

import os, json, httpx, asyncio
from typing import AsyncGenerator, List, Dict, Any

def _to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            # dict part with possible 'text'/'content'
            if isinstance(part, dict):
                if "text" in part:
                    parts.append(str(part["text"]))
                elif "content" in part:
                    parts.append(str(part["content"]))
                elif "value" in part:
                    parts.append(str(part["value"]))
                else:
                    # last resort
                    parts.append(str(part))
                continue
            # object part with .type/.text
            t = getattr(part, "type", None)
            if t == "text":
                txt = getattr(part, "text", "")
                parts.append(str(txt))
                continue
            if isinstance(part, str):
                parts.append(part)
                continue
            parts.append(str(part))
        return "\n".join(parts).strip()
    return str(content)

def _normalize_messages(messages: list[Any]) -> list[dict[str, str]]:
    norm: list[dict[str, str]] = []
    role_map = {"system": "system", "human": "user", "ai": "assistant", "tool": "tool"}

    for m in messages:
        # Case 1: already OpenAI-shaped
        if isinstance(m, dict) and "role" in m and "content" in m:
            norm.append({"role": m["role"], "content": _to_text(m["content"])})
            continue

        # Case 2: LangChain-serialized dict with 'type' + 'content'
        if isinstance(m, dict) and "type" in m and "content" in m:
            role = role_map.get(m.get("type", ""), "user")
            content = _to_text(m.get("content"))
            norm.append({"role": role, "content": content})
            continue

        # Case 3: LangChain BaseMessage object
        role = role_map.get(getattr(m, "type", ""), "user")
        content = _to_text(getattr(m, "content", ""))
        norm.append({"role": role, "content": content})

    return norm


# def _to_text(content: Any) -> str:
#     """Robustly convert LangChain message content into a plain string."""
#     if content is None:
#         return ""
#     # If content is already a string, return it
#     if isinstance(content, str):
#         return content

#     # If content is a list of parts (LangChain >= 0.3)
#     if isinstance(content, list):
#         chunks: List[str] = []
#         for part in content:
#             # Dict part: {"type": "text", "text": "..."}
#             if isinstance(part, dict):
#                 if "text" in part:
#                     chunks.append(str(part["text"]))
#                 elif "content" in part:
#                     chunks.append(str(part["content"]))
#                 else:
#                     # last resort: stringify the dict
#                     pass
#                 continue

#             # Object part with .type / .text (LC structured content)
#             # e.g., langchain_core.messages.ai.AIMessageChunk content parts
#             t = getattr(part, "type", None)
#             if t == "text":
#                 txt = getattr(part, "text", None)
#                 if txt:
#                     chunks.append(str(txt))
#                     continue

#             # Raw string in the list
#             if isinstance(part, str):
#                 chunks.append(part)
#                 continue

#             # Fallback: just stringify the part
#             chunks.append(str(part))
#         return "\n".join(chunks).strip()

#     # Unknown shape → stringify
#     return str(content)

# def _normalize_messages(messages: List[Any]) -> List[Dict[str, str]]:
#     """
#     Accepts:
#       - LangChain BaseMessage objects (with .type and .content possibly structured)
#       - Already-normalized dicts with 'role'/'content'
#     Returns OpenAI/Ollama-compatible [{"role": ..., "content": ...}]
#     """
#     norm: List[Dict[str, str]] = []
#     role_map = {"system": "system", "human": "user", "ai": "assistant", "tool": "tool"}
#     # print("MESSAGES RECEIVED BY NORMALIZE=", messages)
#     for m in messages:
#         # already normalized?
#         print("m=", m)
#         if isinstance(m, dict) and "role" in m and "content" in m:
#             norm.append({"role": m["role"], "content": _to_text(m["content"])})
#             continue

#         # LangChain BaseMessage-like
#         role = role_map.get(getattr(m, "type", ""), "user")
#         content = _to_text(getattr(m, "content", ""))
#         print("content=", getattr(m, "content", "not found"))
#         norm.append({"role": role, "content": content})

#     # optional: drop empties (but usually keep the user turn even if blank)
#     # norm = [x for x in norm if x["content"].strip()]

#     return norm



# def _normalize_messages(messages: List[Any]) -> List[Dict[str, str]]:
#     """
#     Accepts either:
#       - LangChain BaseMessage objects (with .type and .content)
#       - Already-normalized dicts with 'role'/'content'
#     Returns OpenAI/Ollama-compatible [{"role": ..., "content": ...}, ...]
#     """
#     norm: List[Dict[str, str]] = []
#     for m in messages:
#         if isinstance(m, dict) and "role" in m and "content" in m:
#             norm.append({"role": m["role"], "content": m["content"]})
#             continue
#         # LangChain BaseMessage-like
#         role_map = {"system": "system", "human": "user", "ai": "assistant", "tool": "tool"}
#         role = role_map.get(getattr(m, "type", ""), "user")
#         content = getattr(m, "content", "")
#         # If content is structured (list parts), flatten text parts
#         if isinstance(content, list):
#             text = []
#             for part in content:
#                 if isinstance(part, dict) and "text" in part:
#                     text.append(part["text"])
#                 elif isinstance(part, str):
#                     text.append(part)
#             content = "\n".join(text)
#         norm.append({"role": role, "content": str(content)})
#     return norm

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        if self.provider == "openai":
            self.base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
            self.key = os.getenv("OPENAI_API_KEY")
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        else:
            self.base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
            self.model = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")

    async def complete(self, messages: List[Any]) -> str:
        msgs = _normalize_messages(messages)
        # msgs = messages
        # print("MESSAGES=",msgs)
        # sys.exit("OBSERVE MESSAGES!")
        if self.provider == "openai":
            async with httpx.AsyncClient(timeout=None) as client:
                r = await client.post(
                    f"{self.base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.key}"} if self.key else {},
                    json={"model": self.model, "messages": msgs, "temperature": 0.2},
                )
                try:
                    r.raise_for_status()
                except httpx.HTTPStatusError as e:
                    # surface server message to logs to debug 400s quickly
                    raise RuntimeError(f"OpenAI error {r.status_code}: {r.text}") from e
                data = r.json()
                print("DATA=", data)
                return data["choices"][0]["message"]["content"]
        # Ollama
        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(
                f"{self.base}/api/chat",
                json={"model": self.model, "messages": msgs, "stream": False},
            )
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Ollama error {r.status_code}: {r.text}") from e
            data = r.json()
            # Some Ollama builds reply with {"message":{"content":"..."}}; others with {"choices":[...]}
            if "message" in data:
                return data["message"].get("content", "")
            if "choices" in data and data["choices"]:
                return data["choices"][0].get("message", {}).get("content", "")
            return ""

    async def stream(self, messages: List[Any]) -> AsyncGenerator[str, None]:
        msgs = _normalize_messages(messages)
        if self.provider == "openai":
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.key}"} if self.key else {},
                    json={"model": self.model, "messages": msgs, "temperature": 0.2, "stream": True},
                ) as r:
                    try:
                        r.raise_for_status()
                    except httpx.HTTPStatusError as e:
                        text = await r.aread()
                        raise RuntimeError(f"OpenAI stream error {r.status_code}: {text.decode()}") from e
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
                json={"model": self.model, "messages": msgs, "stream": True},
            ) as r:
                try:
                    r.raise_for_status()
                except httpx.HTTPStatusError as e:
                    text = await r.aread()
                    raise RuntimeError(f"Ollama stream error {r.status_code}: {text.decode()}") from e
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
