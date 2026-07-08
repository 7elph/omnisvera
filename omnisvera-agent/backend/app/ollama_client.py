from __future__ import annotations

from typing import Any

import httpx


async def check_ollama(base_url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{base_url}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def chat_with_ollama(
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "num_predict": 180,
            "temperature": 0.2,
        },
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(f"{base_url}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
    message = data.get("message") or {}
    return str(message.get("content") or "").strip()
