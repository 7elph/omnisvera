from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx


_MODEL_CACHE: dict[str, Any] = {"base_url": "", "expires": 0.0, "names": set()}
_LOGGER = logging.getLogger(__name__)
_FALLBACK_STATUS_CODES = {429, 502, 503}


class OllamaRequestError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, fallback_allowed: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.fallback_allowed = fallback_allowed


def _configured_request_timeout(value: float | None) -> float:
    if value is not None:
        return max(1.0, float(value))
    try:
        return max(1.0, float(os.getenv("OLLAMA_REQUEST_TIMEOUT", "180")))
    except ValueError:
        return 180.0


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
    if preferred.strip().lower().endswith("-cloud"):
        return preferred
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
    request_timeout: float | None = None,
    raise_on_error: bool = False,
) -> str:
    request_timeout = _configured_request_timeout(request_timeout)
    is_qwen3 = model.strip().lower().startswith("qwen3")
    normalized_model = model.strip().lower()
    is_gpt_oss = normalized_model.startswith("gpt-oss")
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
    if is_gpt_oss:
        default_options["num_predict"] = max(int(default_options["num_predict"]), 320)
    elif is_qwen3:
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
    elif is_gpt_oss:
        payload["think"] = "low"
    if response_format is not None:
        payload["format"] = response_format
    try:
        async with httpx.AsyncClient(timeout=request_timeout) as client:
            response = await client.post(f"{base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        message = data.get("message") or {}
    except httpx.TimeoutException as exc:
        if raise_on_error:
            raise OllamaRequestError("Ollama request timed out", fallback_allowed=True) from exc
        return ""
    except httpx.ConnectError as exc:
        if raise_on_error:
            raise OllamaRequestError("Ollama gateway unavailable", fallback_allowed=True) from exc
        return ""
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if raise_on_error:
            raise OllamaRequestError(
                f"Ollama returned HTTP {status_code}",
                status_code=status_code,
                fallback_allowed=status_code in _FALLBACK_STATUS_CODES,
            ) from exc
        return ""
    except (httpx.RequestError, ValueError, TypeError, KeyError) as exc:
        if raise_on_error:
            raise OllamaRequestError("Invalid Ollama response", fallback_allowed=False) from exc
        return ""
    return str(message.get("content") or "").strip()


async def chat_with_fallback(
    base_url: str,
    preferred_model: str,
    fallback_model: str,
    messages: list[dict[str, str]],
    options: dict[str, Any] | None = None,
    response_format: str | dict[str, Any] | None = None,
    request_timeout: float | None = None,
) -> tuple[str, str, bool]:
    """Tenta o modelo selecionado e usa um unico fallback em falhas transitorias."""
    selected = await resolve_ollama_model(base_url, preferred_model, fallback_model)
    started = time.perf_counter()
    status_code: int | None = None
    fallback_used = False
    effective_model = selected
    answer = ""
    try:
        answer = await chat_with_ollama(
            base_url,
            selected,
            messages,
            options,
            response_format,
            request_timeout=request_timeout,
            raise_on_error=True,
        )
    except OllamaRequestError as exc:
        status_code = exc.status_code
        if exc.fallback_allowed and selected != fallback_model:
            fallback_used = True
            effective_model = fallback_model
            try:
                answer = await chat_with_ollama(
                    base_url,
                    fallback_model,
                    messages,
                    options,
                    response_format,
                    request_timeout=request_timeout,
                    raise_on_error=True,
                )
            except OllamaRequestError as fallback_exc:
                status_code = fallback_exc.status_code or status_code
                answer = ""
    duration_ms = round((time.perf_counter() - started) * 1000)
    _LOGGER.info(
        "ollama_chat model=%s duration_ms=%s success=%s fallback=%s status=%s",
        effective_model,
        duration_ms,
        bool(answer),
        fallback_used,
        status_code,
    )
    return answer, effective_model, fallback_used


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
