from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from app.scene_lab_routes import build_scene_lab_router
from app.scene_lab_store import init_lab
from app.character_play import init_character_play
from app.dice_rolls import init_dice_rolls
from app.session_workspace import init_session_workspace
from app.scene_play import create_scene


RUN_ID = "test-" + "a" * 32


class SceneLabRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "lab.sqlite3"
        init_session_workspace(self.database)
        init_character_play(self.database)
        init_dice_rolls(self.database)
        scene, created = create_scene(self.database, request_id="lab-native-scene-fixture",
                                      campaign_id="omnisvera", title="Native scene unchanged",
                                      location_name="TEMP", created_by="master")
        self.assertTrue(created)
        self.assertEqual(scene["id"], 1)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.executescript("CREATE TABLE game_marker(value TEXT); INSERT INTO game_marker VALUES('unchanged');")
            self.scene_before = connection.execute("SELECT * FROM scenes").fetchall()
            self.actions_before = connection.execute("SELECT * FROM scene_actions").fetchall()
            self.tokens_before = connection.execute("SELECT * FROM session_workspace_tokens").fetchall()
            self.characters_before = connection.execute("SELECT * FROM character_states").fetchall()
        init_lab(self.database)
        self.summary = {"run_id": RUN_ID, "state": "COMPLETED", "verdict": "PASS", "scenario_counts": {"PASS": 1},
                        "actors": ["raziel"], "ui_suite": "full", "ui_status": "PASS", "certification_ready": False,
                        "scope": "existing_code_only_not_proposal_execution", "report_sha256": "a" * 64}
        self.reader = Mock(return_value=self.summary)
        self.provider = Mock(return_value=self.database)

        def require_master(x_test_role: str | None = Header(default=None)):
            if x_test_role != "gm":
                raise HTTPException(status_code=403 if x_test_role else 401)
            return {"mode": "gm", "profile_id": "trusted-master"}

        app = FastAPI()
        app.include_router(build_scene_lab_router(self.provider, require_master, self.reader))
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.headers = {"X-Test-Role": "gm"}

    def request(self, method: str, path: str, **kwargs):
        return self.client.request(method, path, headers=kwargs.pop("headers", self.headers), **kwargs)

    def create(self, **extra):
        return self.request("POST", "/gm/scenes/1/lab/proposals", json={"request_id": "create-request-001",
                            "title": "Teste privado", "kind": "action", "content": {"damage": "1d6"}, **extra})

    def test_all_routes_require_gm_before_storage_or_evidence_access(self) -> None:
        paths = [("GET", "/gm/scenes/1/lab/proposals"), ("POST", "/gm/scenes/1/lab/proposals"),
                 ("GET", "/gm/scene-lab/proposals/1"), ("PUT", "/gm/scene-lab/proposals/1"),
                 ("POST", "/gm/scene-lab/proposals/1/evidence"), ("POST", "/gm/scene-lab/proposals/1/decision")]
        for method, path in paths:
            for role, code in ((None, 401), ("player", 403)):
                response = self.client.request(method, path, headers={"X-Test-Role": role} if role else {}, json={})
                self.assertEqual(response.status_code, code, (method, path, role))
        self.provider.assert_not_called()
        self.reader.assert_not_called()

    def test_crud_version_retry_conflict_and_author_are_server_controlled(self) -> None:
        response = self.create()
        self.assertEqual(response.status_code, 200, response.text)
        proposal = response.json()
        self.assertEqual(proposal["created_by"], "trusted-master")
        self.assertEqual(self.create().json(), proposal)
        url = f'/gm/scene-lab/proposals/{proposal["id"]}'
        payload = {"request_id": "update-request-001", "expected_version": 1,
                   "title": "Revisada", "content": {"damage": "1d8"}}
        updated = self.request("PUT", url, json=payload)
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["version"], 2)
        self.assertEqual(self.request("PUT", url, json=payload).json(), updated.json())
        self.assertEqual(self.request("PUT", url, json={**payload, "request_id": "update-request-stale"}).status_code, 409)
        self.assertEqual(self.request("GET", "/gm/scenes/1/lab/proposals").json()[0]["id"], proposal["id"])

    def test_evidence_is_read_server_side_bound_to_revision_and_not_proposal_execution(self) -> None:
        proposal = self.create().json()
        url = f'/gm/scene-lab/proposals/{proposal["id"]}'
        payload = {"request_id": "evidence-request-001", "expected_version": 1, "run_id": RUN_ID}
        response = self.request("POST", url + "/evidence", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        evidence = response.json()["evidence"]
        self.assertEqual(evidence["version"], 1)
        self.assertEqual(evidence["content_snapshot"], proposal["content"])
        self.assertIs(evidence["summary"]["certification_ready"], False)
        self.assertEqual(evidence["summary"]["scope"], "existing_code_only_not_proposal_execution")
        self.reader.assert_called_once_with(RUN_ID)
        self.assertEqual(self.request("POST", url + "/evidence", json=payload).json(), response.json())
        decision = {"request_id": "decision-request-001", "expected_version": 1,
                    "decision": "approved", "reason": "Revisão apenas; não publicar"}
        approved = self.request("POST", url + "/decision", json=decision)
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["status"], "approved")
        self.assertEqual(self.request("POST", url + "/decision", json=decision).json(), approved.json())
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT * FROM scenes").fetchall(), self.scene_before)
            self.assertEqual(connection.execute("SELECT * FROM scene_actions").fetchall(), self.actions_before)
            self.assertEqual(connection.execute("SELECT * FROM session_workspace_tokens").fetchall(), self.tokens_before)
            self.assertEqual(connection.execute("SELECT * FROM character_states").fetchall(), self.characters_before)
            self.assertEqual(connection.execute("SELECT * FROM game_marker").fetchall(), [("unchanged",)])
            self.assertEqual(set(row[0] for row in connection.execute("SELECT visibility FROM session_ledger")), {"gm"})

    def test_forged_author_summary_unknown_fields_nan_and_limits_are_rejected(self) -> None:
        for extra in ({"created_by": "forged"}, {"title": "x" * 181}, {"content": {"x": "y" * 50000}},
                      {"content": {"x": float("nan")}}, {"request_id": "bad"}, {"unknown": True}):
            if "content" in extra and isinstance(extra["content"].get("x"), float):
                raw = json.dumps({"request_id": "nan-request-001", "title": "Bad", "kind": "action", **extra})
                response = self.request("POST", "/gm/scenes/1/lab/proposals", content=raw,
                                        headers={"X-Test-Role": "gm", "Content-Type": "application/json"})
            else:
                response = self.create(**extra)
            self.assertEqual(response.status_code, 400, response.text)
        proposal = self.create().json()
        response = self.request("POST", f'/gm/scene-lab/proposals/{proposal["id"]}/evidence',
                                json={"request_id": "forge-summary-001", "expected_version": 1,
                                      "run_id": RUN_ID, "summary": {"certification_ready": True}})
        self.assertEqual(response.status_code, 400)
        self.reader.assert_not_called()
        response = self.request("POST", f'/gm/scene-lab/proposals/{proposal["id"]}/decision',
                                json={"request_id": "long-reason-001", "expected_version": 1,
                                      "decision": "approved", "reason": "x" * 2001})
        self.assertEqual(response.status_code, 400)

    def test_missing_scene_proposal_and_run_errors_are_safe(self) -> None:
        self.assertEqual(self.request("GET", "/gm/scenes/999/lab/proposals").status_code, 404)
        self.assertEqual(self.request("GET", "/gm/scene-lab/proposals/999").status_code, 404)
        proposal = self.create().json()
        self.reader.side_effect = FileNotFoundError("C:/private/path/secret.json")
        payload = {"request_id": "missing-run-001", "expected_version": 1, "run_id": RUN_ID}
        response = self.request("POST", f'/gm/scene-lab/proposals/{proposal["id"]}/evidence', json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("private", response.text)
        self.reader.side_effect = ValueError("Invalid report C:/secret")
        response = self.request("POST", f'/gm/scene-lab/proposals/{proposal["id"]}/evidence', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("secret", response.text)

    def test_strict_versions_and_path_like_run_ids_are_rejected_before_reader(self) -> None:
        proposal = self.create().json()
        url = f'/gm/scene-lab/proposals/{proposal["id"]}/evidence'
        for extra in ({"expected_version": True}, {"expected_version": "1"},
                      {"run_id": "../secret"}, {"run_id": RUN_ID + "/.."}):
            response = self.request("POST", url, json={"request_id": "strict-input-001",
                                    "expected_version": 1, "run_id": RUN_ID, **extra})
            self.assertEqual(response.status_code, 400)
        self.reader.assert_not_called()

    def test_evidence_receipt_replays_without_rereading_removed_or_changed_run(self) -> None:
        proposal = self.create().json()
        url = f'/gm/scene-lab/proposals/{proposal["id"]}/evidence'
        payload = {"request_id": "evidence-stable-retry", "expected_version": 1, "run_id": RUN_ID}
        first = self.request("POST", url, json=payload)
        self.assertEqual(first.status_code, 200, first.text)
        before = self.database.read_bytes()
        self.reader.side_effect = FileNotFoundError("removed temporary MCP report")
        retry = self.request("POST", url, json=payload)
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertEqual(retry.json(), first.json())
        self.assertEqual(self.database.read_bytes(), before)
        self.reader.assert_called_once_with(RUN_ID)
        for path, extra in ((url, {"expected_version": 2}),
                            (url, {"run_id": "test-" + "b" * 32}),
                            ("/gm/scene-lab/proposals/999/evidence", {})):
            conflict = self.request("POST", path, json={**payload, **extra})
            self.assertEqual(conflict.status_code, 409, conflict.text)
        self.reader.assert_called_once_with(RUN_ID)
        self.assertEqual(self.database.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
