from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from app.architecture import ArchitectureContractError, COMPONENT_MAP_PATH, load_component_map
from app.architecture_routes import build_architecture_router


class ArchitectureRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        def require_master(x_test_role: str | None = Header(default=None)):
            if x_test_role != "gm":
                raise HTTPException(status_code=403 if x_test_role else 401, detail="Mestre necessário")
            return {"mode": "gm"}

        app = FastAPI()
        app.include_router(build_architecture_router(require_master))
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def get(self, path: str):
        return self.client.get(path, headers={"X-Test-Role": "gm"})

    def test_requires_master_before_returning_contracts(self) -> None:
        paths = (
            "/gm/architecture/components",
            "/gm/architecture/components/character_sheet",
            "/gm/architecture/routes",
        )
        for path in paths:
            for role, expected in ((None, 401), ("player", 403)):
                with self.subTest(path=path, role=role):
                    headers = {"X-Test-Role": role} if role else {}
                    self.assertEqual(self.client.get(path, headers=headers).status_code, expected)

    def test_component_list_is_code_only_and_matches_manifest(self) -> None:
        response = self.get("/gm/architecture/components")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            set(payload),
            {"schema_version", "kind", "campaign_data", "scope", "count", "approval_policy", "components"},
        )
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["kind"], "code_component_index")
        self.assertIs(payload["campaign_data"], False)
        self.assertEqual(payload["scope"], "omnisvera-agent")
        self.assertEqual(payload["count"], 12)
        ids = [component["id"] for component in payload["components"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("character_sheet", ids)
        self.assertIn("private_scene_lab", ids)
        self.assertNotIn("SECRET_GM_OBJECTIVE", response.text)
        self.assertNotIn("campaign_data\": true", response.text)

    def test_component_detail_exposes_contract_only(self) -> None:
        response = self.get("/gm/architecture/components/character_sheet")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], "character_sheet")
        self.assertTrue(payload["backend"])
        self.assertTrue(payload["frontend"])
        self.assertTrue(payload["routes"])
        self.assertEqual(self.get("/gm/architecture/components/missing").status_code, 404)

    def test_route_ownership_keeps_shared_routes(self) -> None:
        response = self.get("/gm/architecture/routes")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload), {"count", "routes"})
        self.assertEqual(payload["count"], len(payload["routes"]))
        by_key = {(route["method"], route["path"]): route["component_ids"] for route in payload["routes"]}
        self.assertIn("character_sheet", by_key[("GET", "/characters/{profile_id}")])
        self.assertIn("spell_and_ability_catalogue", by_key[("GET", "/characters/{profile_id}")])
        self.assertIn("attack_resolution", by_key[("POST", "/characters/{profile_id}/techniques/{technique_id}")])
        self.assertIn("summons", by_key[("POST", "/characters/{profile_id}/techniques/{technique_id}")])

    def test_main_app_registers_architecture_routes(self) -> None:
        from app.main import app

        paths = app.openapi()["paths"]
        self.assertIn("/gm/architecture/components", paths)
        self.assertIn("/gm/architecture/components/{component_id}", paths)
        self.assertIn("/gm/architecture/routes", paths)

    def test_manifest_rejects_campaign_data_and_duplicate_ids(self) -> None:
        base = json.loads(COMPONENT_MAP_PATH.read_text(encoding="utf-8"))
        with TemporaryDirectory() as directory:
            root = Path(directory)
            campaign = root / "campaign.json"
            campaign.write_text(json.dumps({**base, "campaign_data": True}), encoding="utf-8")
            with self.assertRaises(ArchitectureContractError):
                load_component_map(campaign)
            duplicate = root / "duplicate.json"
            duplicated = {**base, "components": [base["components"][0], base["components"][0]]}
            duplicate.write_text(json.dumps(duplicated), encoding="utf-8")
            with self.assertRaises(ArchitectureContractError):
                load_component_map(duplicate)
