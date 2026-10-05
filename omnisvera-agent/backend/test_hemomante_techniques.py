from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.access import AccessContext
from app.combat import init_combat, resolve_attack, confirm_attack_resolution
from app.combat_effects import effect_command, init_effects, readeffects
from app.character_play import init_character_play
from app.character_creation import init_character_creation
from app.dice_rolls import init_dice_rolls
from app.session_ledger import init_session_ledger
from app.session_workspace import init_session_workspace, save_workspace_token
from app.vault_index import init_db as init_vault_index
import test_combat as fixture


def _blood_state(hp=10, maximum=16, laminas=5):
    return {"current_hp": hp, "maximum_hp": maximum, "temporary_hp": 0,
            "conditions": [], "resources": [{"key": "reserva_de_sangue", "label": "Reserva de Sangue",
                                             "current": laminas, "maximum": 5, "recharge": "inn_rest"}]}


class TechniqueFixture(unittest.TestCase):
    """Shared temp-DB + TestClient scaffolding (no tests here)."""
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "techniques.sqlite3"
        init_character_play(self.db)
        init_character_creation(self.db)
        init_combat(self.db)
        init_effects(self.db)
        init_dice_rolls(self.db)
        init_session_workspace(self.db)
        init_session_ledger(self.db)
        init_vault_index(self.db)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                ("Characters/Individual/Raziel.md", "Raziel", "[]", "character", "[]", "{}", "# Raziel",
                 "2026-09-30T00:00:00+00:00"),
            )
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                ("raziel", json.dumps(_blood_state()), "2026-09-30T00:00:00+00:00"),
            )
            connection.execute(
                "INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) VALUES(?,?,?,?,?,?)",
                ("raziel", "Characters/Individual/Raziel.md", "Raziel", "approved",
                 json.dumps({"attributes": {"strength": 10}, "character_class": {"level": 2},
                             "attacks": {"melee_bonus": 1, "ranged_bonus": 3}}),
                 "2026-09-30T00:00:00+00:00"),
            )
        self.wounded = save_workspace_token(self.db, token_type="monster", name="Lobo",
            latitude=10, longitude=10, current_hp=6, maximum_hp=12, sheet={"armor_class": 10})
        self.healthy = save_workspace_token(self.db, token_type="monster", name="Guarda",
            latitude=20, longitude=20, current_hp=12, maximum_hp=12, sheet={"armor_class": 10})
        settings = replace(main.settings, database_path=self.db, master_token="fixture-master")
        self._patcher = patch.object(main, "settings", settings)
        self._patcher.start()
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="raziel")
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        import gc as _gc
        import time as _time
        try:
            self.client.close()
        finally:
            main.app.dependency_overrides.clear()
            self._patcher.stop()
            _gc.collect()
            last_error: Exception | None = None
            for _ in range(25):
                try:
                    self.temporary.cleanup()
                    last_error = None
                    break
                except PermissionError as error:
                    last_error = error
                    _time.sleep(0.2)
            if last_error is not None:
                raise last_error

    def use(self, profile, technique, payload=None):
        return self.client.post(f"/characters/{profile}/techniques/{technique}", json=payload or {})

    def laminas(self):
        with closing(sqlite3.connect(self.db)) as connection:
            state = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
        return next(r for r in state["resources"] if r["key"] == "reserva_de_sangue")["current"]



class HemomanteTechniquesTests(TechniqueFixture):
    """Raziel technique tests (inherited fixture only)."""

    def test_lamina_resolves_Nd4_and_spends_on_confirm(self):
        response = self.use("raziel", "lamina-de-sangue", {
            "request_id": "tech-lam-101", "charges": 2, "attack": "ranged",
            "target_type": "token", "target_id": self.wounded["id"], "roll_mode": "digital"})
        self.assertEqual(200, response.status_code, response.text)
        body = response.json()
        self.assertIn("2d4", body["damage_formula"])
        self.assertEqual(5, self.laminas())
        confirm_attack_resolution(self.db, resolution_id=body["resolution_id"],
                                  requested_by_id="raziel", requested_by_role="player")
        self.assertEqual(3, self.laminas())
    def test_lamina_rejects_bad_charges(self):
        bad = self.use("raziel", "lamina-de-sangue", {
            "request_id": "tech-lam-102", "charges": 6, "attack": "ranged",
            "target_type": "token", "target_id": self.wounded["id"], "roll_mode": "digital"})
        self.assertIn(bad.status_code, (400, 422))
    def test_lamina_rejects_insufficient_on_confirm(self):
        response = self.use("raziel", "lamina-de-sangue", {
            "request_id": "tech-lam-103", "charges": 5, "attack": "melee",
            "target_type": "token", "target_id": self.wounded["id"], "roll_mode": "digital"})
        self.assertEqual(200, response.status_code, response.text)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            state = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            for resource in state["resources"]:
                if resource["key"] == "reserva_de_sangue":
                    resource["current"] = 1
            connection.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",
                               (json.dumps(state),))
        with self.assertRaises(Exception):
            confirm_attack_resolution(self.db, resolution_id=response.json()["resolution_id"],
                                      requested_by_id="raziel", requested_by_role="player")
    def test_marca_requires_wounded_target(self):
        healthy = self.use("raziel", "marca-rubra", {"request_id": "tech-mar-101",
                                                     "target_type": "token", "target_id": self.healthy["id"]})
        self.assertEqual(400, healthy.status_code)
        self.assertEqual(5, self.laminas())
        wounded = self.use("raziel", "marca-rubra", {"request_id": "tech-mar-102",
                                                     "target_type": "token", "target_id": self.wounded["id"]})
        self.assertEqual(200, wounded.status_code, wounded.text)
        self.assertEqual(4, self.laminas())
        marks = [e for e in readeffects(self.db)["effects"] if e["target_id"] == self.wounded["id"]]
        self.assertEqual(1, len(marks))
        self.assertEqual("scene", marks[0]["duration"])
    def _confirmed_hit(self, request_id, d20=15, dmg_rng=(4,)):
        definition = {"attacks": [{"id": "melee", "name": "Corpo a corpo", "attack_bonus": 3,
                                   "damage": "1d6", "weapon_item_path": "Items/Grisalma.md"}],
                      "item_effects": {"totals": {}, "breakdown": []}, "active_effects": []}
        record, _ = resolve_attack(
            self.db, request_id=request_id, actor_character_id="raziel", actor_name="Raziel",
            requested_by_id="raziel", requested_by_role="player", definition=definition, inventory=[],
            attack_id="melee",
            target={"type": "token", "id": self.wounded["id"], "name": "Lobo", "armor_class": 10, "current_hp": 6},
            roll_mode="physical", physical_d20=d20, rng=fixture.SequenceRng(*dmg_rng))
        confirm_attack_resolution(self.db, resolution_id=record["resolution_id"],
                                  requested_by_id="raziel", requested_by_role="player")
        return record
    def test_mordida_existing_d4_healing_once_free(self):
        record = self._confirmed_hit("tech-mor-101")
        self.assertEqual("hit", record["result"])
        response = self.use("raziel", "mordida", {"resolution_id": record["resolution_id"]})
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual(record["damage_total"], response.json()["damage_absorbed"])
        self.assertEqual(5, self.laminas())
        with closing(sqlite3.connect(self.db)) as connection:
            hp = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])["current_hp"]
        self.assertGreaterEqual(response.json()['heal_roll'], 1)
        self.assertLessEqual(response.json()['heal_roll'], 4)
        self.assertEqual(min(16, 10 + response.json()['heal_roll']), hp)
        again = self.use("raziel", "mordida", {"resolution_id": record["resolution_id"]})
        self.assertEqual(400, again.status_code)
    def test_mordida_once_per_turn_in_battle(self):
        def set_turn(index, round_no=1):
            encounter = {"active": True, "battle_mode": True, "map_id": "default", "title": "T",
                         "participants": [{"target_type": "character", "target_id": "raziel", "initiative": 12},
                                          {"target_type": "token", "target_id": self.wounded["id"], "initiative": 5}],
                         "turn_index": index, "turn_sequence": 1, "action_committed": False}
            with closing(sqlite3.connect(self.db)) as connection, connection:
                connection.execute("UPDATE combat_effect_clock SET encounter_json=?, round=?, version=version+1 WHERE id=1",
                                   (json.dumps(encounter), round_no))
        set_turn(0)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE session_workspace_tokens SET current_hp=12 WHERE id=?",
                               (self.wounded["id"],))
        first = self._confirmed_hit("tech-mor-104")
        response = self.use("raziel", "mordida", {"resolution_id": first["resolution_id"]})
        self.assertEqual(200, response.status_code, response.text)
        # Next round, Raziel's turn again: a new absorb is allowed.
        set_turn(0, round_no=2)
        second = self._confirmed_hit("tech-mor-105")
        response2 = self.use("raziel", "mordida", {"resolution_id": second["resolution_id"]})
        self.assertEqual(200, response2.status_code, response2.text)
        # Same turn slot as the first absorb: blocked even with a fresh hit.
        set_turn(0, round_no=1)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE session_workspace_tokens SET current_hp=12 WHERE id=?",
                               (self.wounded["id"],))
        third = self._confirmed_hit("tech-mor-106")
        again = self.use("raziel", "mordida", {"resolution_id": third["resolution_id"]})
        self.assertEqual(400, again.status_code)
        self.assertIn("turno", again.json()["detail"])
    def test_mordida_rejects_dead_target(self):
        record = self._confirmed_hit("tech-mor-103")
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE session_workspace_tokens SET current_hp=0 WHERE id=?",
                               (self.wounded["id"],))
        response = self.use("raziel", "mordida", {"resolution_id": record["resolution_id"]})
        self.assertEqual(400, response.status_code)
        self.assertEqual(5, self.laminas())

    def test_mordida_first_turn_of_new_encounter_does_not_reuse_previous_claim(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("INSERT OR REPLACE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('default','Arena fixture','',1,'fixture','fixture')")
            connection.execute("INSERT INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES(1,'default','Arena fixture','','fixture')")
        def command(action, **payload):
            return effect_command(self.db, actor_id="master", actor_role="gm",
                                  request_id=f"mordida-encounter-{action}-{readeffects(self.db)['version']}",
                                  expected_version=readeffects(self.db)["version"],
                                  action=action, payload=payload)

        for encounter_number in (1, 2):
            with closing(sqlite3.connect(self.db)) as connection, connection:
                connection.execute("UPDATE session_workspace_tokens SET current_hp=12 WHERE id=?",
                                   (self.wounded["id"],))
            command("start", map_id="default", battle_mode=True, participants=[
                {"target_type": "character", "target_id": "raziel", "initiative": 12},
                {"target_type": "token", "target_id": self.wounded["id"], "initiative": 5}])
            self.assertEqual(1, readeffects(self.db)["round"])
            self.assertEqual(0, readeffects(self.db)["encounter"]["turn_index"])
            hit = self._confirmed_hit(f"mordida-new-encounter-{encounter_number}")
            response = self.use("raziel", "mordida", {"resolution_id": hit["resolution_id"]})
            self.assertEqual(200, response.status_code, response.text)
            self.assertEqual(5, self.laminas())
            command("end")

    def test_mordida_rejects_miss(self):
        miss = self._confirmed_hit("tech-mor-102", d20=2)
        response = self.use("raziel", "mordida", {"resolution_id": miss["resolution_id"]})
        self.assertEqual(400, response.status_code)
    def test_wrong_owner_rejected(self):
        response = self.use("vezemir", "lamina-de-sangue", {"request_id": "tech-own-001"})
        self.assertEqual(404, response.status_code)


class VezemirPowersTests(TechniqueFixture):
    def setUp(self) -> None:
        super().setUp()
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                ("vezemir", json.dumps({
                    "current_hp": 17, "maximum_hp": 17, "temporary_hp": 0, "conditions": [],
                    "resources": [
                        {"key": "forca_arcana", "label": "Força Arcana", "current": 1, "maximum": 1, "recharge": "inn_rest"},
                        {"key": "velocidade", "label": "Velocidade", "current": 1, "maximum": 1, "recharge": "inn_rest"},
                    ]}), "2026-09-30T00:00:00+00:00"),
            )
            connection.execute(
                "INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) VALUES(?,?,?,?,?,?)",
                ("vezemir", "Characters/Individual/Vezemir.md", "Vezemir", "approved",
                 json.dumps({"attributes": {"strength": 14}, "character_class": {"level": 2},
                             "attacks": {"melee_bonus": 4}}),
                 "2026-09-30T00:00:00+00:00"),
            )
            connection.execute(
                "INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                ("Characters/Individual/Vezemir.md", "Vezemir", "[]", "character", "[]", "{}", "# Vezemir",
                 "2026-09-30T00:00:00+00:00"),
            )
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")

    def _resource(self, key):
        with closing(sqlite3.connect(self.db)) as connection:
            state = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
        return next(r for r in state["resources"] if r["key"] == key)["current"]

    def test_forca_arcana_raises_strength_and_rounds(self):
        response = self.use("vezemir", "forca-arcana", {"request_id": "tech-for-001"})
        self.assertEqual(200, response.status_code, response.text)
        body = response.json()
        self.assertGreaterEqual(body["duration_rounds"], 3)
        self.assertLessEqual(body["duration_rounds"], 8)
        self.assertEqual(0, self._resource("forca_arcana"))
        effects = [e for e in readeffects(self.db)["effects"] if e["target_id"] == "vezemir"]
        self.assertEqual(1, len(effects))
        # For 14 -> +2 (1 per 5): strength carries attack AND damage via the OD modifier.
        self.assertEqual(2, effects[0]["modifiers"].get("strength_bonus"))
        self.assertNotIn("damage_bonus", effects[0]["modifiers"])
        self.assertEqual(body["duration_rounds"], effects[0]["rounds"])

    def test_master_uses_character_resource_without_spending_master_resource(self):
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='gm')
        response = self.use('vezemir', 'forca-arcana', {'request_id': 'master-forca-session6'})
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual(0, self._resource('forca_arcana'))

    def test_velocidade_applies_triple_buff(self):
        response = self.use("vezemir", "velocidade", {"request_id": "tech-vel-001"})
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual(0, self._resource("velocidade"))
        effects = [e for e in readeffects(self.db)["effects"] if e["target_id"] == "vezemir"]
        self.assertEqual({"movement_multiplier": 2, "armor_class_bonus": 2, "extra_attacks": 1},
                         effects[0]["modifiers"])

    def test_power_rejects_empty_resource(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            state = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            for resource in state["resources"]:
                resource["current"] = 0
            connection.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",
                               (json.dumps(state),))
        response = self.use("vezemir", "velocidade", {"request_id": "tech-vel-002"})
        self.assertEqual(400, response.status_code)


class NecromanteSummonTests(TechniqueFixture):
    def setUp(self) -> None:
        super().setUp()
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                ("morthak", json.dumps({
                    "current_hp": 4, "maximum_hp": 4, "temporary_hp": 0, "conditions": [],
                    "resources": [
                        {"key": "animar_mortos", "label": "Animar Mortos", "current": 1, "maximum": 1, "recharge": "inn_rest"},
                        {"key": "levantar_um_esqueleto", "label": "Levantar Esqueleto", "current": 1, "maximum": 1, "recharge": "inn_rest"},
                    ]}), "2026-09-30T00:00:00+00:00"),
            )
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="morthak")
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("INSERT INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES(1,'default','Teste','fixture.png','now')")

    def _resource(self, key):
        with closing(sqlite3.connect(self.db)) as connection:
            state = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
        return next(r for r in state["resources"] if r["key"] == key)["current"]

    def test_levantar_esqueleto_spawns_movable_pin(self):
        response = self.use("morthak", "levantar-esqueleto", {"request_id": "tech-nec-001"})
        self.assertEqual(200, response.status_code, response.text)
        body = response.json()
        token = body["token"]
        self.assertIsNone(token["character_id"])
        self.assertEqual('morthak', token['sheet']['summon']['caster'])
        self.assertEqual(10, token["current_hp"])
        self.assertEqual(16, token['sheet']['armor_class'])
        self.assertEqual('1d6+1', token['sheet']['attacks'][0]['damage'])
        self.assertIn("1 semana", body["defaults_note"])
        self.assertEqual("week", body["duration"])
        self.assertEqual(0, self._resource("levantar_um_esqueleto"))

    def test_sheet_exposes_bone_dagger_as_real_attack_without_weapon(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) VALUES(?,?,?,?,?,?)", ('morthak', 'Characters/Individual/Morthak.md', 'Morthak', 'approved', json.dumps({'attributes': {'dexterity': 10}, 'character_class': {'level': 2}, 'attacks': {'ranged_bonus': 0}}), 'now'))
            connection.execute("INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at) VALUES(?,?,?,?,?,?,?,?)", ('Characters/Individual/Morthak.md', 'Morthak', '[]', 'character', '[]', '{}', '# Morthak', 'now'))
        response = self.client.get('/characters/morthak')
        self.assertEqual(200, response.status_code, response.text)
        attacks = response.json()['definition']['attacks']
        dagger = next(a for a in attacks if a['id'] == 'adaga-de-osso')
        self.assertEqual('1d4', dagger['damage'])
        self.assertEqual('technique:adaga-de-osso', dagger['weapon_item_path'])

    def test_animar_mortos_spawns_after_caster_in_turn_order(self):
        encounter = {"active": True, "map_id": "default", "title": "T",
                     "participants": [{"target_type": "character", "target_id": "morthak", "initiative": 12}],
                     "turn_index": 0, "turn_sequence": 1, "action_committed": False}
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE combat_effect_clock SET encounter_json=?, version=version+1 WHERE id=1",
                               (json.dumps(encounter),))
        corpse = save_workspace_token(self.db, token_type='monster', name='Lobo morto', latitude=30, longitude=30,
            current_hp=0, maximum_hp=8, sheet={'reanimation_allowed': True})
        response = self.use("morthak", "animar-mortos", {"request_id": "tech-nec-002", 'target_type': 'token', 'target_id': corpse['id']})
        self.assertEqual(200, response.status_code, response.text)
        token_id = response.json()["token"]["id"]
        with closing(sqlite3.connect(self.db)) as connection:
            order = [ (p["target_type"], p["target_id"])
                      for p in json.loads(connection.execute(
                          "SELECT encounter_json FROM combat_effect_clock WHERE id=1").fetchone()[0])["participants"]]
        self.assertEqual([("character", "morthak"), ("token", token_id)], order)

    def test_summon_rejects_empty_resource(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            state = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            for resource in state["resources"]:
                resource["current"] = 0
            connection.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'",
                               (json.dumps(state),))
        response = self.use("morthak", "levantar-esqueleto", {"request_id": "tech-nec-003"})
        self.assertEqual(400, response.status_code)


if __name__ == "__main__":
    unittest.main()
