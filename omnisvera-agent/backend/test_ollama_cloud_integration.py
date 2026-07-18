from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


BACKEND_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings
from app.ollama_client import (
    OllamaRequestError,
    chat_with_fallback,
    chat_with_ollama,
    check_ollama,
    embed_with_ollama,
    resolve_ollama_model,
)


MESSAGES = [{"role": "user", "content": "teste"}]


class CloudConfigurationTests(unittest.TestCase):
    def test_cloud_model_and_local_gateway_are_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = get_settings()
        self.assertEqual("qwen3.5:397b-cloud", settings.ollama_model)
        self.assertEqual("qwen2:1.5b", settings.ollama_fallback_model)
        self.assertEqual("http://localhost:11434", settings.ollama_base_url)
        self.assertEqual(180, settings.ollama_request_timeout)
        self.assertEqual("nomic-embed-text", settings.embedding_model)
        self.assertFalse(hasattr(settings, "api_key"))

    def test_environment_overrides_generation_and_fallback_models(self):
        env = {
            "OLLAMA_MODEL": "qwen3.5:397b-cloud",
            "OLLAMA_FALLBACK_MODEL": "local:test",
            "OLLAMA_REQUEST_TIMEOUT": "75",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = get_settings()
        self.assertEqual("qwen3.5:397b-cloud", settings.ollama_model)
        self.assertEqual("local:test", settings.ollama_fallback_model)
        self.assertEqual(75, settings.ollama_request_timeout)


class CloudResolutionTests(unittest.IsolatedAsyncioTestCase):
    async def test_cloud_model_is_not_rejected_when_absent_from_local_tags(self):
        with patch(
            "app.ollama_client.available_ollama_models",
            new=AsyncMock(return_value={"qwen2:1.5b"}),
        ):
            model = await resolve_ollama_model(
                "http://localhost:11434",
                "qwen3.5:397b-cloud",
                "qwen2:1.5b",
            )
        self.assertEqual("qwen3.5:397b-cloud", model)

    async def test_health_check_only_reads_tags(self):
        calls: list[tuple[str, str]] = []

        class Response:
            status_code = 200

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return None

            async def get(self, url: str):
                calls.append(("GET", url))
                return Response()

            async def post(self, *_args, **_kwargs):
                raise AssertionError("health check must not generate")

        with patch("app.ollama_client.httpx.AsyncClient", return_value=Client()):
            self.assertTrue(await check_ollama("http://localhost:11434"))
        self.assertEqual([("GET", "http://localhost:11434/api/tags")], calls)


class SelectiveFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def _run_transient(self, error: OllamaRequestError):
        with patch(
            "app.ollama_client.resolve_ollama_model",
            new=AsyncMock(return_value="qwen3.5:397b-cloud"),
        ), patch(
            "app.ollama_client.chat_with_ollama",
            new=AsyncMock(side_effect=[error, "resposta local"]),
        ) as chat:
            result = await chat_with_fallback(
                "http://localhost:11434",
                "qwen3.5:397b-cloud",
                "qwen2:1.5b",
                MESSAGES,
            )
        self.assertEqual(("resposta local", "qwen2:1.5b", True), result)
        self.assertEqual(2, chat.await_count)

    async def test_timeout_uses_one_local_fallback(self):
        await self._run_transient(OllamaRequestError("timeout", fallback_allowed=True))

    async def test_transient_http_statuses_use_one_local_fallback(self):
        for status in (429, 502, 503):
            with self.subTest(status=status):
                await self._run_transient(
                    OllamaRequestError(
                        f"HTTP {status}",
                        status_code=status,
                        fallback_allowed=True,
                    )
                )

    async def test_validation_and_permission_errors_do_not_use_fallback(self):
        for status in (400, 401, 403):
            with self.subTest(status=status), patch(
                "app.ollama_client.resolve_ollama_model",
                new=AsyncMock(return_value="qwen3.5:397b-cloud"),
            ), patch(
                "app.ollama_client.chat_with_ollama",
                new=AsyncMock(
                    side_effect=OllamaRequestError(
                        f"HTTP {status}",
                        status_code=status,
                        fallback_allowed=False,
                    )
                ),
            ) as chat:
                result = await chat_with_fallback(
                    "http://localhost:11434",
                    "qwen3.5:397b-cloud",
                    "qwen2:1.5b",
                    MESSAGES,
                )
            self.assertEqual(("", "qwen3.5:397b-cloud", False), result)
            self.assertEqual(1, chat.await_count)

    async def test_chat_payload_requires_no_api_key_and_keeps_response_shape(self):
        captured: dict = {}

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {"message": {"content": "resposta"}}

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return None

            async def post(self, url: str, **kwargs):
                captured["url"] = url
                captured.update(kwargs)
                return Response()

        def client_factory(*, timeout):
            captured["timeout"] = timeout
            return Client()

        with patch("app.ollama_client.httpx.AsyncClient", side_effect=client_factory):
            answer = await chat_with_ollama(
                "http://localhost:11434",
                "qwen3.5:397b-cloud",
                MESSAGES,
            )
        self.assertEqual("resposta", answer)
        self.assertEqual("http://localhost:11434/api/chat", captured["url"])
        self.assertEqual(180.0, captured["timeout"])
        self.assertNotIn("headers", captured)
        self.assertEqual("qwen3.5:397b-cloud", captured["json"]["model"])

    async def test_embeddings_keep_their_own_local_model(self):
        captured: dict = {}

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {"embeddings": [[0.1, 0.2]]}

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return None

            async def post(self, url: str, **kwargs):
                captured["url"] = url
                captured.update(kwargs)
                return Response()

        with patch("app.ollama_client.httpx.AsyncClient", return_value=Client()):
            vectors = await embed_with_ollama(
                "http://localhost:11434",
                "nomic-embed-text",
                "texto",
            )
        self.assertEqual([[0.1, 0.2]], vectors)
        self.assertEqual("http://localhost:11434/api/embed", captured["url"])
        self.assertEqual("nomic-embed-text", captured["json"]["model"])


if __name__ == "__main__":
    unittest.main()
