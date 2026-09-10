import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.access import AccessContext
from app.combat import resolve_attack, confirm_attack_resolution, CombatExpiredError
from app.combat_effects import effect_command, readeffects, apply_definition_effects
from app.character_play import update_definition_overrides
from app.session_workspace import list_workspace_tokens, save_workspace_token, init_session_workspace, get_workspace_snapshot, update_workspace_token, update_workspace_token_position
import test_combat as fixture


class MultiattackEffectsTests(TestCase):
    def setUp(self):
        self.fixture = fixture.CombatAttackResolutionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.db = self.fixture.database
        self.definition = self.fixture.definition
        self.definition["attacks"][0]["attack_count"] = 2
        self.token = save_workspace_token(self.db, token_type="monster", name="Vampiro", latitude=50, longitude=50,
            current_hp=18, maximum_hp=18, sheet={"armor_class": 14})
        self.target = {"type": "token", "id": self.token["id"], "name": "Vampiro", "armor_class": 14, "current_hp": 18}

    def resolve(self, **kwargs):
        args = dict(request_id="multi-test-001", actor_character_id="vezemir", actor_name="Vezemir", requested_by_id="vezemir",
            requested_by_role="player", definition=self.definition, inventory=self.fixture.inventory, attack_id="melee",
            target=self.target, roll_mode="physical", attack_count=2, physical_d20s=[15, 2], rng=fixture.SequenceRng(6))
        args.update(kwargs)
        return resolve_attack(self.db, **args)[0]

    def confirm(self, resolution):
        return confirm_attack_resolution(self.db, resolution_id=resolution["resolution_id"], requested_by_id="vezemir", requested_by_role="player")

    def apply(self, **fields):
        payload = dict(target_type="character", target_id="vezemir", label="Aceleração", source="Mestre: magia",
                       duration="rounds", rounds=2, modifiers={"attack_bonus": 2, "armor_class_bonus": 2, "extra_attacks": 1, "damage_bonus": 1})
        payload.update(fields)
        state = readeffects(self.db)
        return effect_command(self.db, actor_id="master", actor_role="gm", request_id=f"effect-{state['version']:04}", expected_version=state["version"], action="apply", payload=payload)

    def command(self, action, payload=None, **kwargs):
        state = readeffects(self.db)
        args = dict(actor_id="master", actor_role="gm", request_id=f"command-{state['version']:04}", expected_version=state["version"], action=action, payload=payload or {})
        args.update(kwargs)
        return effect_command(self.db, **args)

    def test_physical_mixed_hits_single_confirmation_concurrent_replay_and_ledger(self):
        result = self.resolve()
        self.assertEqual(["hit", "miss"], [s["result"] for s in result["breakdown"]["strikes"]])
        self.assertEqual(8, result["damage_total"])
        self.assertEqual(18, list_workspace_tokens(self.db)[0]["current_hp"])
        with ThreadPoolExecutor(2) as pool:
            replies = list(pool.map(lambda _: self.confirm(result), range(2)))
        self.assertEqual(1, sum(applied for _, applied in replies))
        self.assertEqual(10, replies[0][0]["hp_after"])
        with closing(sqlite3.connect(self.db)) as db:
            rows = db.execute("SELECT detail_json FROM session_ledger WHERE source_type='combat_action'").fetchall()
            self.assertEqual(1, len(rows))
            detail = json.loads(rows[0][0])
            self.assertEqual(2, len(detail["breakdown"]["strikes"]))
            self.assertEqual((18, 10), (detail["hp_before"], detail["hp_after"]))

    def test_digital_two_hits_and_resolve_replay_without_rng(self):
        result = self.resolve(roll_mode="digital", physical_d20s=None, rng=fixture.SequenceRng(15, 16, 6, 5))
        self.assertEqual(15, result["damage_total"])
        replay = self.resolve(roll_mode="digital", physical_d20s=None, rng=fixture.SequenceRng())
        self.assertEqual(result["resolution_id"], replay["resolution_id"])

    def test_invalid_count_physical_dice_and_permission(self):
        for args in ({"attack_count": 3}, {"physical_d20s": [0, 21]}, {"physical_d20s": [15]}, {"physical_d20s": [True, 15]}, {"physical_d20s": [15.5, 15]}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.resolve(**args)
        with self.assertRaises(PermissionError): self.resolve(requested_by_id="raziel")
        for count in (0, 11, True, 1.5):
            with self.assertRaises(ValueError): update_definition_overrides(self.db, character_id="vezemir", actor_id="master", fields={"attack_count": count})

    def test_effects_change_attack_damage_count_ac_and_expire_by_round(self):
        self.definition["defenses"]["armor_class"] = 14
        snapshot = self.apply()
        effective = apply_definition_effects(self.definition, snapshot["effects"])
        self.assertEqual(16, effective["defenses"]["armor_class"])
        self.assertEqual(3, effective["attacks"][0]["attack_count"])
        result = self.resolve(definition=effective, physical_d20s=[8, 1])
        self.assertEqual(6, result["attack_bonus"])
        self.assertEqual(9, result["damage_total"])
        self.command("round")
        with self.assertRaises(CombatExpiredError): self.confirm(result)
        self.command("round")
        self.assertEqual([], readeffects(self.db)["effects"])

    def test_next_attack_effect_consumed_only_on_confirm(self):
        snapshot = self.apply(duration="next_attack")
        effective = apply_definition_effects(self.definition, snapshot["effects"])
        result = self.resolve(definition=effective)
        self.assertEqual(1, len(readeffects(self.db)["effects"]))
        self.confirm(result); self.confirm(result)
        self.assertEqual([], readeffects(self.db)["effects"])

    def test_periodic_damage_healing_and_round_idempotence(self):
        self.apply(target_type="token", target_id=self.token["id"], modifiers={"hp_per_round": -3})
        version = readeffects(self.db)["version"]
        result = self.command("round", request_id="round-replay", expected_version=version)
        replay = self.command("round", request_id="round-replay", expected_version=version)
        self.assertEqual(result, replay)
        self.assertEqual(15, list_workspace_tokens(self.db)[0]["current_hp"])
        with self.assertRaises(ValueError): self.command("round", request_id="double-click", expected_version=version)
        self.command("round")
        self.assertEqual([], readeffects(self.db)["effects"])
        self.apply(target_type="token", target_id=self.token["id"], modifiers={"hp_per_round": 20}, rounds=1)
        self.command("round")
        self.assertEqual(18, list_workspace_tokens(self.db)[0]["current_hp"])

    def test_edit_refresh_remove_scene_rest_and_scope(self):
        first = self.apply(duration="scene")
        refreshed = self.apply(duration="scene", modifiers={"attack_bonus": 4})
        self.assertEqual(first["effects"][0]["id"], refreshed["effects"][0]["id"])
        self.assertEqual(1, len(refreshed["effects"]))
        self.command("scene")
        self.apply(duration="rest")
        self.command("rest", {"target_type": "character", "target_id": "raziel"})
        self.assertEqual(1, len(readeffects(self.db)["effects"]))
        self.command("rest", {"target_type": "character", "target_id": "vezemir"})
        self.assertEqual([], readeffects(self.db)["effects"])
        current = self.apply(duration="manual")
        self.command("remove", {"id": current["effects"][0]["id"]})
        with self.assertRaises(PermissionError): self.command("round", actor_role="player")

    def test_character_target_honors_temporary_hp(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            row = db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()
            state = json.loads(row[0]); state["temporary_hp"] = 4
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'", (json.dumps(state),))
        result = self.resolve(target={"type": "character", "id": "raziel", "name": "Raziel", "armor_class": 14, "current_hp": 14})
        confirmed, _ = self.confirm(result)
        self.assertEqual(10, confirmed["hp_after"])

    def test_api_gm_control_player_read_filter_and_hidden_location(self):
        self.apply()
        self.apply(target_type="token", target_id=self.token["id"], label="Segredo")
        settings = replace(main.settings, database_path=self.db, master_token="test-master-token")
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")
        self.addCleanup(main.app.dependency_overrides.clear)
        with patch.object(main, "settings", settings), closing(TestClient(main.app)) as client:
            response = client.get("/combat/effects")
            self.assertEqual(200, response.status_code)
            self.assertEqual(["Aceleração"], [e["label"] for e in response.json()["effects"]])
            self.assertEqual(401, client.post("/gm/combat/effects", json={"request_id": "forged-request", "expected_version": 0, "action": "round"}).status_code)
            main.app.dependency_overrides[main.require_master] = lambda: AccessContext(mode="gm")
            response = client.post("/gm/workspace/tokens", json={"token_type": "location", "name": "Frasco", "visible_to_players": False, "sheet": {"marker": "⌖"}})
            self.assertEqual(200, response.status_code)
            self.assertEqual("location", response.json()["token_type"])
            with self.assertRaises(ValueError): main._combat_target("token", response.json()["id"])
            unconfigured = save_workspace_token(self.db, token_type="monster", name="Sem CA", latitude=10, longitude=20)
            self.assertIsNone(main._combat_target("token", unconfigured["id"])["armor_class"])
            with closing(sqlite3.connect(self.db)) as db:
                self.assertEqual(0, db.execute("SELECT COUNT(*) FROM session_workspace_messages").fetchone()[0])

    def test_encounter_initiative_round_restart_and_end(self):
        participants = [{"target_type": "character", "target_id": "vezemir", "name": "Vezemir", "initiative": 8},
                        {"target_type": "token", "target_id": self.token["id"], "name": "Vampiro", "initiative": 12}]
        result = self.command("start", {"participants": participants, "map_id": "default", "title": "Ruínas"})
        self.assertEqual("Vampiro", result["encounter"]["participants"][0]["name"])
        self.assertTrue(readeffects(self.db)["encounter"]["active"])
        with self.assertRaises(ValueError): self.command("start", {"participants": participants})
        self.command("round")
        self.assertEqual(2, readeffects(self.db)["round"])
        self.command("end")
        self.assertFalse(readeffects(self.db)["encounter"]["active"])

    def test_active_encounter_is_visible_only_to_involved_players(self):
        participants = [
            {"target_type": "character", "target_id": "vezemir", "name": "Vezemir", "initiative": 10},
            {"target_type": "character", "target_id": "raziel", "name": "Raziel", "initiative": 8},
            {"target_type": "token", "target_id": self.token["id"], "name": "Vampiro", "initiative": 12},
        ]
        self.command("start", {"participants": participants, "map_id": "default", "title": "Emboscada"})
        settings = replace(main.settings, database_path=self.db, master_token="test-master-token")
        self.addCleanup(main.app.dependency_overrides.clear)
        with patch.object(main, "settings", settings), closing(TestClient(main.app)) as client:
            for profile_id in ("vezemir", "raziel"):
                main.app.dependency_overrides[main.require_any] = lambda profile_id=profile_id: AccessContext(mode="player", profile_id=profile_id)
                response = client.get("/combat/effects")
                self.assertEqual(200, response.status_code)
                self.assertTrue(response.json()["encounter"]["active"])
                self.assertEqual("Emboscada", response.json()["encounter"]["title"])

            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="morthak")
            self.assertEqual({}, client.get("/combat/effects").json()["encounter"])

            update_workspace_token(self.db, token_id=self.token["id"], visible_to_players=False)
            main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")
            visible = client.get("/combat/effects").json()["encounter"]
            self.assertTrue(visible["active"])
            self.assertNotIn("Vampiro", [participant["name"] for participant in visible["participants"]])

    def test_gm_test_mode_previews_each_configured_player_without_impersonation(self):
        from app.session_workspace import update_workspace_table_mode
        participants = [
            {"target_type": "character", "target_id": "vezemir", "name": "Vezemir", "initiative": 10},
            {"target_type": "character", "target_id": "raziel", "name": "Raziel", "initiative": 8},
            {"target_type": "token", "target_id": self.token["id"], "name": "Vampiro", "initiative": 12},
        ]
        self.command("start", {"participants": participants, "map_id": "default", "title": "Prévia solo"})
        update_workspace_table_mode(self.db, "test")
        profiles = {
            profile_id: {"character_title": title, "character_path": f"Characters/{title}.md"}
            for profile_id, title in (("vezemir", "Vezemir"), ("raziel", "Raziel"), ("morthak", "Morthak"))
        }
        profiles["guest"] = {"character_title": "Convidado", "character_path": ""}
        settings = replace(main.settings, database_path=self.db, master_token="test-master-token", player_profiles=profiles)
        main.app.dependency_overrides[main.require_master] = lambda: AccessContext(mode="gm")
        self.addCleanup(main.app.dependency_overrides.clear)
        with patch.object(main, "settings", settings), closing(TestClient(main.app)) as client:
            response = client.get("/gm/combat/test-views")
            self.assertEqual(200, response.status_code, response.text)
            payload = response.json()
            self.assertTrue(payload["enabled"])
            views = {view["profile_id"]: view for view in payload["views"]}
            self.assertEqual({"vezemir", "raziel", "morthak"}, set(views))
            self.assertTrue(views["vezemir"]["receives_combat"])
            self.assertTrue(views["raziel"]["receives_combat"])
            self.assertFalse(views["morthak"]["receives_combat"])
            self.assertEqual({}, views["morthak"]["state"]["encounter"])

            update_workspace_table_mode(self.db, "digital")
            disabled = client.get("/gm/combat/test-views").json()
            self.assertFalse(disabled["enabled"])
            self.assertEqual([], disabled["views"])

    def test_table_mode_is_backend_authority_and_attack_footprint(self):
        from app.session_workspace import update_workspace_table_mode
        settings = replace(main.settings, database_path=self.db, master_token="test-master-token")
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")
        self.addCleanup(main.app.dependency_overrides.clear)
        with patch.object(main,"settings",settings), patch.object(main,"_character_access_level",return_value="owner"), patch.object(main,"_playable_character",return_value={"definition":self.definition,"inventory":self.fixture.inventory}), patch.object(main,"_combat_target",return_value=self.target), closing(TestClient(main.app)) as client:
            body={"request_id":"api-multi-attack", "attack_id":"melee", "target_type":"token", "target_id":self.token["id"], "roll_mode":"physical", "attack_count":2, "d20s":[15,2]}
            self.assertEqual(400,client.post("/characters/vezemir/attacks/resolve",json=body).status_code)
            update_workspace_table_mode(self.db,"physical")
            response=client.post("/characters/vezemir/attacks/resolve",json=body)
            self.assertEqual(200,response.status_code,response.text)
            resolution=response.json()
            self.assertEqual(18,list_workspace_tokens(self.db)[0]["current_hp"])
            for _ in range(2): self.assertEqual(200,client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm").status_code)
            with closing(sqlite3.connect(self.db)) as db:
                self.assertEqual(1,db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='combat_action'").fetchone()[0])
            update_workspace_token(self.db, token_id=self.token["id"], visible_to_players=False)
            body["request_id"] = "hidden-target-attack"
            self.assertEqual(403, client.post("/characters/vezemir/attacks/resolve", json=body).status_code)


class LocationMigrationTests(TestCase):
    def test_old_schema_preserves_tokens_and_visibility(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pins.sqlite3"
            init_session_workspace(path)
            original = save_workspace_token(path, token_type="monster", name="Antigo", latitude=12, longitude=34, current_hp=8, maximum_hp=10)
            with closing(sqlite3.connect(path)) as db, db:
                sql = db.execute("SELECT sql FROM sqlite_master WHERE name='session_workspace_tokens'").fetchone()[0]
                db.execute(sql.replace("session_workspace_tokens", "old_tokens", 1).replace("'character','monster','location'", "'character','monster'"))
                db.execute("INSERT INTO old_tokens SELECT * FROM session_workspace_tokens")
                db.execute("DROP TABLE session_workspace_tokens")
                db.execute("ALTER TABLE old_tokens RENAME TO session_workspace_tokens")
            init_session_workspace(path)
            init_session_workspace(path)
            self.assertEqual(original, list_workspace_tokens(path)[0])
            location = save_workspace_token(path, token_type="location", name="Nimalis", latitude=45, longitude=60, current_hp=10, maximum_hp=20, visible_to_players=False)
            self.assertIsNone(location["current_hp"])
            update_workspace_token_position(path, token_id=location["id"], latitude=20, longitude=30)
            update_workspace_token(path, token_id=location["id"], name="Nimalis editada", visible_to_players=True)
            self.assertEqual(2, len(list_workspace_tokens(path)))
