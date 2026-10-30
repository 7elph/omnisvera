from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from app.action_audit_routes import build_action_audit_router


class ActionAuditRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.access = {"mode": "gm"}
        self.sheet = {
            "definition": {
                "id": "raziel", "private_objective": "SECRET_GM_OBJECTIVE",
                "attacks": [{"id": "melee", "name": "Arma efetivamente equipada", "damage": "1d8", "attack_bonus": 8}],
                "session_abilities": [
                    {"id": "arma-de-sangue", "name": "Arma de Sangue"},
                    {"id": "new-unapproved", "name": "Proposta", "mechanics_status": "automatic"},
                ],
                "raw_specification": {"attacks": [{"id": "unapproved-hidden-attack"}]},
            },
            "state": {"resources": [{"key": "reserva_de_sangue", "current": 0}], "secret": "PRIVATE_STATE"},
            "inventory": [{"item_title": "PRIVATE_INVENTORY", "quantity": 1, "notes": "SECRET_NOTES"}],
            "annotations": "PRIVATE_TRANSCRIPT",
        }
        self.token = {"id": "npc:1", "name": "Guardião", "secret": "TOKEN_PRIVATE_DATA",
                      "sheet": {"attacks": [{"name": "Espada", "bonus": 2, "damage": "1d6"}],
                                "abilities": ["Imune a veneno"], "notes": "TOKEN_PRIVATE_NOTES"}}
        self.playable = Mock(side_effect=lambda identity, access: deepcopy(self.sheet) if identity == "raziel" else None)
        self.token_loader = Mock(side_effect=lambda identity, access: deepcopy(self.token) if identity == "npc:1" else None)
        self.database_provider = Mock(side_effect=AssertionError("Audit route must not open game database"))

        def require_master(x_test_role: str | None = Header(default=None)):
            if x_test_role != "gm":
                raise HTTPException(status_code=403 if x_test_role else 401, detail="Mestre necessário")
            return self.access

        app = FastAPI()
        app.include_router(build_action_audit_router(self.database_provider, require_master,
                                                     self.playable, self.token_loader))
        client = TestClient(app)
        self.addCleanup(client.close)
        self.client = client

    def get(self, path: str):
        return self.client.get(path, headers={"X-Test-Role": "gm"})

    def test_all_endpoints_are_gm_only_before_callbacks(self) -> None:
        paths = ["/gm/actions/manifest/raziel", "/gm/workspace/tokens/npc:1/action-manifest",
                 "/gm/compendium/provenance?kind=spell",
                 "/gm/compendium/provenance/spell/arcana-reflexos"]
        for path in paths:
            for role, expected in ((None, 401), ("player", 403)):
                with self.subTest(path=path, role=role):
                    headers = {"X-Test-Role": role} if role else {}
                    response = self.client.get(path, headers=headers)
                    self.assertEqual(response.status_code, expected)
        self.playable.assert_not_called()
        self.token_loader.assert_not_called()
        self.database_provider.assert_not_called()

    def test_effective_sheet_not_raw_spec_is_manifest_source(self) -> None:
        response = self.get("/gm/actions/manifest/raziel")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload), {"character_id", "source", "execution_approved", "actions"})
        self.assertEqual(payload["character_id"], "raziel")
        self.assertEqual(payload["source"], "effective_sheet")
        self.assertIs(payload["execution_approved"], False)
        actions = {item["ref"]: item for item in payload["actions"]}
        self.assertIn("attack:raziel:melee", actions)
        self.assertNotIn("unapproved-hidden-attack", response.text)
        self.assertEqual(actions["technique:raziel:arma-de-sangue"]["availability"]["state"], "unavailable")
        self.assertIsNone(actions["technique:raziel:new-unapproved"]["execution"])
        self.playable.assert_called_once_with("raziel", self.access)

    def test_manifest_never_returns_original_sheet_inventory_or_private_fields(self) -> None:
        response = self.get("/gm/actions/manifest/raziel")
        for secret in ("SECRET_GM_OBJECTIVE", "PRIVATE_STATE", "PRIVATE_INVENTORY", "SECRET_NOTES", "PRIVATE_TRANSCRIPT"):
            self.assertNotIn(secret, response.text)
        response = self.get("/gm/workspace/tokens/npc:1/action-manifest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"token_id", "source", "execution_approved", "actions"})
        self.assertEqual(response.json()["source"], "native_token")
        self.assertIs(response.json()["execution_approved"], False)
        self.assertTrue(response.json()["actions"])
        self.assertNotIn("TOKEN_PRIVATE", response.text)
        self.token_loader.assert_called_once_with("npc:1", self.access)

    def test_unknown_entities_and_provenance_are_404(self) -> None:
        for path in ("/gm/actions/manifest/missing", "/gm/workspace/tokens/missing/action-manifest",
                     "/gm/compendium/provenance/spell/not-in-batch",
                     "/gm/compendium/provenance/item/arcana-reflexos"):
            with self.subTest(path=path):
                self.assertEqual(self.get(path).status_code, 404)

    def test_mismatched_owner_callback_result_is_not_exposed(self) -> None:
        self.playable.side_effect = None
        self.playable.return_value = {**self.sheet, "definition": {**self.sheet["definition"], "id": "someone-else"}}
        self.assertEqual(self.get("/gm/actions/manifest/raziel").status_code, 404)
        self.token_loader.side_effect = None
        self.token_loader.return_value = {**self.token, "id": "other-token"}
        self.assertEqual(self.get("/gm/workspace/tokens/npc:1/action-manifest").status_code, 404)

    def test_provenance_filters_and_single_response_never_approve_execution(self) -> None:
        response = self.get("/gm/compendium/provenance?kind=spell")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload), {"kind", "count", "execution_approved", "entries"})
        self.assertEqual(payload["count"], 4)
        self.assertEqual(payload["kind"], "spell")
        self.assertTrue(all(entry["execution_approved"] is False for entry in payload["entries"]))
        self.assertEqual(self.get("/gm/compendium/provenance?kind=item").json()["count"], 0)
        single = self.get("/gm/compendium/provenance/spell/arcana-reflexos").json()
        self.assertEqual(single["physical_pages"], [64])
        self.assertEqual(single["review_state"], "source_verified")
        self.assertIs(single["execution_approved"], False)
        self.assertNotIn("C:\\", response.text)

    def test_requests_do_not_mutate_callbacks_dtos_or_open_game_database(self) -> None:
        before_sheet, before_token = deepcopy(self.sheet), deepcopy(self.token)
        with TemporaryDirectory() as root:
            database = Path(root) / "fixture.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE marker(value TEXT)")
                connection.execute("INSERT INTO marker VALUES('unchanged')")
            connection.close()
            before_database = database.read_bytes()
            for path in ("/gm/actions/manifest/raziel", "/gm/workspace/tokens/npc:1/action-manifest",
                         "/gm/compendium/provenance?kind=spell"):
                self.assertEqual(self.get(path).status_code, 200)
            self.assertEqual(database.read_bytes(), before_database)
        self.assertEqual(self.sheet, before_sheet)
        self.assertEqual(self.token, before_token)
        self.database_provider.assert_not_called()


if __name__ == "__main__":
    unittest.main()
