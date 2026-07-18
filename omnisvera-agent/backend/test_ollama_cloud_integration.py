from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
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
from app.narrative_composer import compose_narrative
from app.rag import _clean_answer, _first_section_paragraph


MESSAGES = [{"role": "user", "content": "teste"}]


class CloudConfigurationTests(unittest.TestCase):
    def test_cloud_model_and_local_gateway_are_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = get_settings()
        self.assertEqual("gpt-oss:120b-cloud", settings.ollama_model)
        self.assertNotEqual("qwen3.5:397b-cloud", settings.ollama_model)
        self.assertEqual("qwen2:1.5b", settings.ollama_fallback_model)
        self.assertEqual("http://localhost:11434", settings.ollama_base_url)
        self.assertEqual(180, settings.ollama_request_timeout)
        self.assertEqual("nomic-embed-text", settings.embedding_model)
        self.assertFalse(hasattr(settings, "api_key"))

    def test_environment_overrides_generation_and_fallback_models(self):
        env = {
            "OLLAMA_MODEL": "gpt-oss:120b-cloud",
            "OLLAMA_FALLBACK_MODEL": "local:test",
            "OLLAMA_REQUEST_TIMEOUT": "75",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = get_settings()
        self.assertEqual("gpt-oss:120b-cloud", settings.ollama_model)
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
                "gpt-oss:120b-cloud",
                "qwen2:1.5b",
            )
        self.assertEqual("gpt-oss:120b-cloud", model)

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
            new=AsyncMock(return_value="gpt-oss:120b-cloud"),
        ), patch(
            "app.ollama_client.chat_with_ollama",
            new=AsyncMock(side_effect=[error, "resposta local"]),
        ) as chat:
            result = await chat_with_fallback(
                "http://localhost:11434",
                "gpt-oss:120b-cloud",
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
                new=AsyncMock(return_value="gpt-oss:120b-cloud"),
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
                    "gpt-oss:120b-cloud",
                    "qwen2:1.5b",
                    MESSAGES,
                )
            self.assertEqual(("", "gpt-oss:120b-cloud", False), result)
            self.assertEqual(1, chat.await_count)

    async def test_gpt_oss_reasoning_is_not_exposed_and_response_shape_is_preserved(self):
        captured: dict = {}

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "message": {
                        "content": "resposta",
                        "thinking": "raciocinio interno",
                        "reasoning": "raciocinio alternativo",
                    }
                }

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
                "gpt-oss:120b-cloud",
                MESSAGES,
                options={"num_predict": 24},
            )
        self.assertEqual("resposta", answer)
        self.assertEqual("http://localhost:11434/api/chat", captured["url"])
        self.assertEqual(180.0, captured["timeout"])
        self.assertNotIn("headers", captured)
        self.assertEqual("gpt-oss:120b-cloud", captured["json"]["model"])
        self.assertEqual("low", captured["json"]["think"])
        self.assertEqual(320, captured["json"]["options"]["num_predict"])

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


class CloudNarrativeTests(unittest.IsolatedAsyncioTestCase):
    async def test_short_fact_card_still_calls_cloud_composer(self):
        card = {
            "entidade": "Ruínas de Valthor",
            "tipo": "location",
            "fatos_confirmados": [
                {
                    "texto": "Hoje restam ruínas ao sudeste de Nimalia, associadas a histórias esquecidas.",
                    "fonte": "Locations/Ruínas de Valthor.md",
                    "evidencia": "Hoje restam ruínas ao sudeste de Nimalia, associadas a histórias esquecidas.",
                }
            ],
            "relacoes_confirmadas": [],
            "locais_confirmados": [],
            "eventos_confirmados": [],
            "rumores_publicos": [],
            "teorias": [],
            "informacoes_nao_disponiveis": [],
            "fontes": ["Locations/Ruínas de Valthor.md"],
        }
        memory = SimpleNamespace(
            retrieve=lambda *_args, **_kwargs: SimpleNamespace(
                examples=[], mode="sanitized", retrieval_time_ms=0.0
            )
        )
        with patch("app.narrative_composer.get_behavioral_memory", return_value=memory), patch(
            "app.narrative_composer.chat_with_fallback",
            new=AsyncMock(
                return_value=(
                    "As ruínas de Valthor encontram-se hoje ao sudeste de Nimalia.",
                    "gpt-oss:120b-cloud",
                    False,
                )
            ),
        ) as cloud:
            result = await compose_narrative(
                question="Quem é Valthor?",
                card=card,
                ollama_base_url="http://localhost:11434",
                model="gpt-oss:120b-cloud",
                fallback_model="qwen2:1.5b",
                access_mode="player",
                intent="direct_entity",
            )
        self.assertTrue(result["attempted"])
        self.assertTrue(result["used"])
        self.assertEqual("gpt-oss:120b-cloud", result["model"])
        self.assertEqual(1, cloud.await_count)

    async def test_cloud_answer_keeps_source_backed_fact_omitted_by_model(self):
        card = {
            "entidade": "Ruínas de Valthor",
            "tipo": "location",
            "fatos_confirmados": [
                {
                    "texto": "Valthor foi um reino antigo e próspero.",
                    "fonte": "Locations/Ruínas de Valthor.md",
                    "evidencia": "Valthor foi um reino antigo e próspero.",
                },
                {
                    "texto": "Hoje restam ruínas ao sudeste de Nimalia, associadas a cavernas profundas.",
                    "fonte": "Locations/Ruínas de Valthor.md",
                    "evidencia": "Hoje restam ruínas ao sudeste de Nimalia, associadas a cavernas profundas.",
                },
            ],
            "relacoes_confirmadas": [],
            "locais_confirmados": [],
            "eventos_confirmados": [],
            "rumores_publicos": [],
            "teorias": [],
            "informacoes_nao_disponiveis": [],
            "fontes": ["Locations/Ruínas de Valthor.md"],
        }
        memory = SimpleNamespace(
            retrieve=lambda *_args, **_kwargs: SimpleNamespace(
                examples=[], mode="sanitized", retrieval_time_ms=0.0
            )
        )
        with patch("app.narrative_composer.get_behavioral_memory", return_value=memory), patch(
            "app.narrative_composer.chat_with_fallback",
            new=AsyncMock(
                return_value=("Valthor foi um reino antigo e próspero.", "gpt-oss:120b-cloud", False)
            ),
        ):
            result = await compose_narrative(
                question="Quem é Valthor?",
                card=card,
                ollama_base_url="http://localhost:11434",
                model="gpt-oss:120b-cloud",
                fallback_model="qwen2:1.5b",
                access_mode="player",
                intent="direct_entity",
            )
        self.assertTrue(result["used"])
        self.assertIn("reino antigo e próspero", result["answer"])
        self.assertIn("ruínas ao sudeste de Nimalia", result["answer"])

    def test_editorial_labels_are_removed_from_final_answer(self):
        raw = (
            "### O que se sabe\n"
            "Valthor foi um reino antigo.\n\n"
            "### Como entra na história\n"
            "Como apresentar: ruínas antigas e silenciosas. "
            "O que manter em aberto no ESTADO_DA_CAMPANHA: decisões pendentes."
        )
        cleaned = _clean_answer(raw)
        self.assertNotIn("O que se sabe", cleaned)
        self.assertNotIn("Como entra na história", cleaned)
        self.assertNotIn("Como apresentar", cleaned)
        self.assertNotIn("ESTADO_DA_CAMPANHA", cleaned)
        self.assertIn("Valthor foi um reino antigo", cleaned)

    def test_public_callout_is_available_to_the_fact_card(self):
        content = (
            "> [!world]- SINOPSE PÚBLICA\n"
            "> Valthor foi um reino antigo e próspero. Hoje restam apenas suas ruínas.\n\n"
            "## Uso em Mesa\n"
            "Como apresentar: não deve entrar na resposta."
        )
        synopsis = _first_section_paragraph(content, ("Sinopse Pública",))
        self.assertEqual(
            "Valthor foi um reino antigo e próspero. Hoje restam apenas suas ruínas.",
            synopsis,
        )


if __name__ == "__main__":
    unittest.main()
