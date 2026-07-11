from __future__ import annotations

import time
from typing import Any

import httpx


_MODEL_CACHE: dict[str, Any] = {"base_url": "", "expires": 0.0, "names": set()}


async def available_ollama_models(base_url: str) -> set[str]:
    now = time.monotonic()
    if _MODEL_CACHE["base_url"] == base_url and float(_MODEL_CACHE["expires"]) > now:
        return set(_MODEL_CACHE["names"])
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
        names = {str(item.get("name") or "").strip() for item in data.get("models") or []}
        names.discard("")
    except Exception:
        names = set()
    _MODEL_CACHE.update({"base_url": base_url, "expires": now + 60.0, "names": names})
    return names


async def resolve_ollama_model(base_url: str, preferred: str, fallback: str) -> str:
    names = await available_ollama_models(base_url)
    if not names or preferred in names:
        return preferred
    if fallback in names:
        return fallback
    return preferred


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
    is_qwen3 = model.strip().lower().startswith("qwen3")
    default_options: dict[str, Any] = {
        "num_ctx": 4096,
        "num_predict": 420,
        "temperature": 0.25,
        "top_p": 0.9,
        "repeat_penalty": 1.12,
    }
    if options:
        default_options.update(options)
    if is_qwen3:
        # The 4B model runs at roughly 3 tokens/s on this notebook. Keep a
        # bounded budget so open questions cannot freeze the UI indefinitely.
        default_options["num_predict"] = min(int(default_options["num_predict"]), 190)

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "keep_alive": "15m",
        "options": default_options,
    }
    # Keep Qwen's reasoning in the dedicated `thinking` field. Only the final
    # answer in `content` is returned to the Companion/player.
    if is_qwen3:
        payload["think"] = True
    if response_format is not None:
        payload["format"] = response_format
    request_timeout = 70.0 if is_qwen3 else 30.0
    try:
        async with httpx.AsyncClient(timeout=request_timeout) as client:
            response = await client.post(f"{base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        message = data.get("message") or {}
    except Exception:
        return ""
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
