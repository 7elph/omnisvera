"""Estúdio de preparação (Cenas com IA): drafts are validated, idempotent and never touch the table by themselves."""
import json
import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main, prep_studio
from app.access import AccessContext
from app.session_workspace import init_session_workspace, list_workspace_tokens

MONSTER = {"name": "Lobo Cinzento de Nimalis", "category": "Animal", "hit_dice": "2", "average_hp": 11, "armor_class": "13",
           "movement": 15, "saving_throw": 16, "morale": 7, "treasure": "-",
           "attacks": [{"name": "Mordida", "bonus": 2, "damage": "1d6", "count": 1, "slot": "melee"},
                       {"name": "Uivo", "bonus": "x", "damage": "rola dado", "slot": "distância", "range_m": 9999}],
           "abilities": ["Matilha: +1 no ataque com aliado adjacente"], "description": "Um lobo magro."}
NPC = {"name": "Irmã Velka", "race": "humana", "class_name": "clériga", "level": 4,
       "attributes": {"strength": 11, "dexterity": 9, "constitution": 13, "intelligence": 12, "wisdom": 17, "charisma": 99},
       "maximum_hp": 22, "armor_class": 15, "saving_throw": 13, "base_attack": 2,
       "attacks": [{"name": "Maça", "bonus": 2, "damage": "1d6+1", "slot": "melee"}],
       "spells": [{"name": "Curar Ferimentos", "circle": 1, "daily_uses": 2}],
       "inventory": [{"name": "Símbolo sagrado", "quantity": 1}, "Bálsamo"], "coins": {"po": 40},
       "personality": "Severa, mas justa.", "secret": "Deve favores ao Conclave."}


def fake_chat(answer):
    return lambda messages: (json.dumps(answer, ensure_ascii=False), "fake-model")


class PrepStudioTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.db = self.root / "prep.sqlite3"
        init_session_workspace(self.db)
        prep_studio.init_prep_studio(self.db)

    def draft(self, kind, answer, image=None, prompt="um lobo para a estrada"):
        draft, created = prep_studio.create_draft(self.db, request_id="req-" + kind + "-0001", kind=kind, prompt=prompt)
        self.assertTrue(created)
        prep_studio.generate(self.db, draft["id"], chat=fake_chat(answer), image=image, media_root=self.root,
                             campaign="Resumo", party=[{"name": "Raziel", "level": 3}], existing=[])
        return prep_studio.get_draft(self.db, draft["id"])

    def test_monster_is_clamped_to_table_shapes(self):
        result = self.draft("monster", MONSTER)
        self.assertEqual("ready", result["status"], result["error"])
        payload = result["payload"]
        self.assertEqual(13, payload["armor_class"])
        self.assertEqual("1d6", payload["attacks"][1]["damage"])         # invalid dice falls back
        self.assertEqual(1, payload["attacks"][1]["bonus"])
        self.assertEqual(300, payload["attacks"][1]["range_m"])          # clamped
        self.assertEqual("ranged", payload["attacks"][1]["slot"])
        self.assertEqual("Matilha", payload["abilities"][0]["name"])

    def test_npc_has_full_sheet_with_clamped_attributes(self):
        result = self.draft("npc", NPC, prompt="uma clériga severa do templo")
        payload = result["payload"]
        self.assertEqual("ready", result["status"], result["error"])
        self.assertEqual(20, payload["attributes"]["charisma"])
        self.assertEqual(11, payload["attributes"]["strength"])
        self.assertEqual([{"name": "Símbolo sagrado", "quantity": 1}, {"name": "Bálsamo", "quantity": 1}], payload["inventory"])
        self.assertEqual(40, payload["coins"]["po"])

    def test_bad_answer_fails_with_reason_and_never_spins(self):
        draft, _ = prep_studio.create_draft(self.db, request_id="req-bad-00001", kind="monster", prompt="qualquer")
        prep_studio.generate(self.db, draft["id"], chat=lambda m: ("sem json aqui", "fake"), image=None,
                             media_root=self.root, campaign="", party=[], existing=[])
        result = prep_studio.get_draft(self.db, draft["id"])
        self.assertEqual("failed", result["status"])
        self.assertIn("JSON", result["error"])

    def test_map_needs_image_and_stores_preview_under_media(self):
        def image(prompt, path):
            from PIL import Image
            Image.new("RGB", (64, 64), "gray").save(path, format="PNG")
        result = self.draft("map", {"title": "Cripta Afogada", "image_prompt": "a flooded crypt with broken pillars and a stone altar"}, image)
        self.assertEqual("ready", result["status"], result["error"])
        self.assertTrue(result["preview_path"].startswith("zz_media/prep/"))
        self.assertTrue((self.root / result["preview_path"]).exists())

    def test_same_request_id_never_generates_twice(self):
        first, created = prep_studio.create_draft(self.db, request_id="req-dupe-0001", kind="item", prompt="uma chave")
        again, created_again = prep_studio.create_draft(self.db, request_id="req-dupe-0001", kind="item", prompt="uma chave")
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first["id"], again["id"])
        with self.assertRaises(ValueError):
            prep_studio.create_draft(self.db, request_id="req-dupe-0001", kind="item", prompt="outra coisa")

    def test_applied_is_recorded_once_per_request(self):
        result = self.draft("item", {"name": "Chave de Ferro", "item_type": "chave", "description": "Abre a cripta."})
        prep_studio.record_applied(self.db, result["id"], request_id="apply-0001", target="item", ref="7")
        after = prep_studio.record_applied(self.db, result["id"], request_id="apply-0001", target="item", ref="7")
        self.assertEqual("applied", after["status"])
        self.assertEqual(1, len(after["applied"]))

    def test_context_is_versioned(self):
        saved = prep_studio.set_context(self.db, "Sessão 9: o grupo saiu de Nimalis.", 0)
        self.assertEqual(1, saved["version"])
        with self.assertRaises(LookupError):
            prep_studio.set_context(self.db, "outra", 0)


class PrepRouteTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.db = self.root / "routes.sqlite3"
        init_session_workspace(self.db)
        patcher = patch.object(main, "settings", replace(main.settings, database_path=self.db, vault_path=self.root))
        patcher.start()
        self.addCleanup(patcher.stop)
        main._prep_initialized = False
        self.client = TestClient(main.app)
        self.addCleanup(self.client.close)
        main.app.dependency_overrides[main.require_master] = lambda: AccessContext(mode="gm")
        self.addCleanup(main.app.dependency_overrides.pop, main.require_master, None)

    def test_generate_starts_once_and_map_apply_is_idempotent(self):
        def run_now(database, draft_id, **kwargs):
            kwargs["chat"] = fake_chat({"title": "Ponte Quebrada", "image_prompt": "a broken stone bridge over a dark river gorge"})

            def image(prompt, path):
                from PIL import Image
                Image.new("RGB", (32, 32), "green").save(path, format="PNG")
            kwargs["image"] = image
            prep_studio.generate(database, draft_id, **kwargs)
        with patch.object(main, "prep_start_generation", side_effect=run_now) as started, \
                patch.object(main, "playable_characters", return_value=[]):
            body = {"request_id": "route-map-0001", "kind": "map", "prompt": "uma ponte quebrada"}
            first = self.client.post("/gm/prep/generate", json=body)
            second = self.client.post("/gm/prep/generate", json=body)
        self.assertEqual(200, first.status_code, first.text)
        self.assertEqual(1, started.call_count)
        draft_id = second.json()["id"]
        drafts = self.client.get("/gm/prep/drafts").json()
        self.assertEqual("ready", drafts[0]["status"], drafts[0]["error"])
        one = self.client.post(f"/gm/prep/drafts/{draft_id}/apply-map", json={"request_id": "apply-map-0001"})
        two = self.client.post(f"/gm/prep/drafts/{draft_id}/apply-map", json={"request_id": "apply-map-0001"})
        self.assertEqual(200, one.status_code, one.text)
        self.assertEqual(one.json()["map_id"], two.json()["map_id"])
        with closing(sqlite3.connect(self.db)) as db:
            titles = [row[0] for row in db.execute("SELECT title FROM session_workspace_maps")]
        self.assertEqual(1, titles.count("Ponte Quebrada"))
        self.assertEqual([], list_workspace_tokens(self.db))  # nothing placed on the table

    def test_every_studio_route_requires_the_gm(self):
        routes = [route for route in main.app.routes if getattr(route, "path", "").startswith("/gm/prep/")]
        self.assertEqual(11, len(routes))
        for route in routes:
            calls = [dependency.call for dependency in route.dependant.dependencies]
            self.assertIn(main.require_master, calls, route.path)

    def test_routes_precede_frontend_catchall(self):
        paths = [getattr(route, "path", "") for route in main.app.routes]
        self.assertLess(paths.index("/gm/prep/generate"), paths.index("/{full_path:path}"))


class PrepSessionTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.db = self.root / "prep.sqlite3"
        from app.scene_play import create_session, init_scene_play
        init_scene_play(self.db)
        init_session_workspace(self.db)
        prep_studio.init_prep_studio(self.db)
        self.s9, _ = create_session(self.db, request_id="sess-9-000001", campaign_id="omnisvera", title="Sessão 9",
                                    created_by="master", session_number=9)
        self.s10, _ = create_session(self.db, request_id="sess-10-00001", campaign_id="omnisvera", title="Sessão 10",
                                     created_by="master", session_number=10)

    def test_record_is_versioned_and_cannot_start_a_session(self):
        record = prep_studio.write_session_record(self.db, self.s9["id"], {"title": "O Conclave", "gm_summary": "Resumo"},
                                                  version=self.s9["version"])
        self.assertEqual("O Conclave", record["title"])
        with self.assertRaises(ValueError):
            prep_studio.write_session_record(self.db, self.s9["id"], {"title": "x"}, version=self.s9["version"])
        with self.assertRaises(ValueError):
            prep_studio.write_session_record(self.db, self.s9["id"], {"status": "active"}, version=record["version"])

    def test_plan_writes_outline_and_linked_drafts(self):
        answers = iter([{"title": "A Torre", "outline": "Cena 1: chegada.", "npcs": ["uma clériga"], "monsters": ["um lobo"],
                         "items": [], "maps": []}, NPC, MONSTER])
        chat = lambda messages: (json.dumps(next(answers), ensure_ascii=False), "fake-model")
        kwargs = {"chat": chat, "image": None, "media_root": self.root, "campaign": "Resumo", "party": [], "existing": []}
        prep_studio.plan_session(self.db, self.s10["id"], request_id="plan-10-00001", brief="torre", chat=chat,
                                 generate_kwargs=kwargs, party=[])
        plan = prep_studio.get_plan(self.db, self.s10["id"])
        self.assertIn("# A Torre", plan["outline"])
        drafts = prep_studio.list_drafts(self.db, session_id=self.s10["id"])
        self.assertEqual({"npc", "monster"}, {d["kind"] for d in drafts})
        self.assertTrue(all(d["status"] == "ready" for d in drafts))
        self.assertEqual([], prep_studio.list_drafts(self.db, session_id=self.s9["id"]))
        listed = {s["id"]: s for s in prep_studio.list_session_plans(self.db)}
        self.assertEqual({"npc": 1, "monster": 1}, listed[self.s10["id"]]["draft_counts"])

    def test_outline_edit_needs_current_version(self):
        plan = prep_studio.write_plan(self.db, self.s10["id"], outline="Roteiro", version=0)
        self.assertEqual(1, plan["version"])
        with self.assertRaises(ValueError):
            prep_studio.write_plan(self.db, self.s10["id"], outline="Outro", version=0)


if __name__ == "__main__":
    unittest.main()
