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
    options: dict[str, Any] | None = None,
    response_format: str | dict[str, Any] | None = None,
) -> str:
    default_options: dict[str, Any] = {
        "num_ctx": 4096,
        "num_predict": 420,
        "temperature": 0.25,
        "top_p": 0.9,
        "repeat_penalty": 1.12,
    }
    if options:
        default_options.update(options)

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "keep_alive": "15m",
        "options": default_options,
    }
    if response_format is not None:
        payload["format"] = response_format
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(f"{base_url}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
    message = data.get("message") or {}
    return str(message.get("content") or "").strip()


async def embed_with_ollama(
    base_url: str,
    model: str,
    inputs: str | list[str],
) -> list[list[float]]:
    payload: dict[str, Any] = {
        "model": model,
        "input": inputs,
        "keep_alive": "15m",
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(f"{base_url}/api/embed", json=payload)
        response.raise_for_status()
        data = response.json()
    embeddings = data.get("embeddings") or []
    return [[float(value) for value in embedding] for embedding in embeddings]
