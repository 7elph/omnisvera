from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import unittest

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from app.system_routes import build_system_router


class SystemRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = SimpleNamespace(
            vault_path=Path("vault"),
            database_path=Path("companion.sqlite3"),
            ollama_base_url="http://127.0.0.1:11434",
            ollama_model="quality",
            fast_model="fast",
            quality_model="quality",
            candidate_model="candidate",
            production_model="production",
            model_mode="baseline",
            production_approved=False,
            embedding_model="embed",
            response_mode="grounded",
            rag_mode="hybrid",
            semantic_index_path=Path("index"),
            auto_refresh_index=False,
            auto_refresh_interval_seconds=12,
            player_token="player-token",
            player_profiles={"raziel": {}},
            training_capture_mode="manual",
            behavior_memory_enabled=True,
            behavior_memory_mode="sanitized",
            behavior_memory_ab_mode="behavioral",
        )
        self.calls = 0

        async def ollama_check(base_url: str) -> bool:
            self.calls += 1
            return True

        def require_any(x_test_role: str | None = Header(default=None)):
            if x_test_role is None:
                raise HTTPException(status_code=401, detail="Token necessário")
            if x_test_role not in {"gm", "player"}:
                raise HTTPException(status_code=403, detail="Acesso negado")
            return SimpleNamespace(
                mode=x_test_role,
                profile_id="raziel" if x_test_role == "player" else None,
                character_path="player/raziel" if x_test_role == "player" else None,
                character_title="Raziel" if x_test_role == "player" else None,
            )

        app = FastAPI()
        app.include_router(build_system_router(
            self.settings,
            require_any,
            ollama_check,
            lambda: True,
            lambda: "/nimalis/nimalis.html",
        ))
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def get(self, role: str):
        return self.client.get("/health", headers={"X-Test-Role": role})

    def test_health_requires_auth_before_ollama_probe(self) -> None:
        self.assertEqual(self.client.get("/health").status_code, 401)
        self.assertEqual(self.get("other").status_code, 403)
        self.assertEqual(self.calls, 0)

    def test_gm_health_exposes_gm_only_fields(self) -> None:
        response = self.get("gm")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["backend"], "ok")
        self.assertEqual(payload["access_mode"], "gm")
        self.assertEqual(payload["training_capture_mode"], "manual")
        self.assertEqual(payload["behavior_memory_mode"], "sanitized")
        self.assertEqual(payload["behavior_memory_ab_mode"], "behavioral")
        self.assertTrue(payload["ollama_accessible"])
        self.assertTrue(payload["game_web_available"])
        self.assertEqual(payload["game_web_url"], "/nimalis/nimalis.html")
        self.assertEqual(self.calls, 1)

    def test_player_health_hides_gm_only_fields(self) -> None:
        response = self.get("player")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["access_mode"], "player")
        self.assertEqual(payload["player_profile_id"], "raziel")
        self.assertEqual(payload["player_character_path"], "player/raziel")
        self.assertIsNone(payload["training_capture_mode"])
        self.assertIsNone(payload["behavior_memory_mode"])
        self.assertIsNone(payload["behavior_memory_ab_mode"])

    def test_ollama_timeout_is_reported_as_unavailable(self) -> None:
        async def timeout_check(base_url: str) -> bool:
            raise TimeoutError

        self.settings.ollama_base_url = "http://127.0.0.1:11434"
        app = FastAPI()
        app.include_router(build_system_router(
            self.settings,
            lambda: SimpleNamespace(mode="gm", profile_id=None, character_path=None, character_title=None),
            timeout_check,
            lambda: False,
            lambda: "/nimalis/nimalis.html",
        ))
        client = TestClient(app)
        self.addCleanup(client.close)
        payload = client.get("/health").json()
        self.assertFalse(payload["ollama_accessible"])
        self.assertFalse(payload["game_web_available"])
        self.assertIsNone(payload["game_web_url"])

    def test_main_app_registers_health(self) -> None:
        from app.main import app

        self.assertIn("/health", app.openapi()["paths"])
