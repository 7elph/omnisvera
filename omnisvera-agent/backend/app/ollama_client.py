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
    normalized_model = model.strip().lower()
    is_compact_local = (
        is_qwen3
        or normalized_model.startswith("qwen2:")
        or normalized_model.startswith("omnisvera-fast")
        or normalized_model.startswith("omnisvera-entity")
    )
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
        # With reasoning disabled, the token budget is spent on the answer
        # instead of an internal chain that never reaches the player.
        default_options["num_predict"] = min(int(default_options["num_predict"]), 240)
    elif is_compact_local:
        default_options["num_predict"] = min(int(default_options["num_predict"]), 220)

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "keep_alive": "15m",
        "options": default_options,
    }
    # Qwen 3 can consume the entire small token budget in `thinking` and leave
    # `content` empty. The RAG already validates evidence separately, so the
    # Companion needs the concise final answer, not a visible reasoning trace.
    if is_qwen3:
        payload["think"] = False
    if response_format is not None:
        payload["format"] = response_format
    request_timeout = 90.0 if is_qwen3 or normalized_model.startswith("omnisvera-entity") else (65.0 if is_compact_local else 45.0)
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
