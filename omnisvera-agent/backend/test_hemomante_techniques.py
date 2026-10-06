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

    def test_night_form_three_animals_daily_limit_and_invalid_choice(self):
        from app.character_play import apply_character_action, load_session_abilities
        power = next(p for p in load_session_abilities('raziel') if p['id'] == 'forma-da-noite')
        self.assertEqual(power['uses']['maximum'], 3)
        state = _blood_state()
        state['resources'].append({'key': 'forma_da_noite', 'label': 'Forma da Noite', 'current': 3, 'maximum': 3, 'recharge': 'inn_rest'})
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'", (json.dumps(state),))
        def use(animal):
            return apply_character_action(self.db, character_id='raziel', actor_id='raziel', actor_role='player', action='consume_resource', payload={'resource_key': 'forma_da_noite', 'amount': 1, 'animal': animal})
        with self.assertRaises(ValueError):
            use('lobo')
        for animal in ('corvo', 'coruja', 'morcego'):
            use(animal)
        with self.assertRaises(ValueError):
            use('corvo')
        with closing(sqlite3.connect(self.db)) as db:
            current = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            self.assertEqual(next(r['current'] for r in current['resources'] if r['key'] == 'forma_da_noite'), 0)
            reasons = [r[0] for r in db.execute("SELECT reason FROM character_events WHERE character_id='raziel'")]
            for animal in ('corvo', 'coruja', 'morcego'):
                self.assertTrue(any(animal in (reason or '') for reason in reasons))

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
        confirm_attack_resolution(self.db, resolution_id=body["resolution_id"],
                                  requested_by_id="raziel", requested_by_role="player")
        self.assertEqual(3, self.laminas(), "Repeated confirmation cannot spend blood twice")
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
    def bite(self, request='bite-001', d20=15):
        return self.use('raziel', 'mordida', {'request_id': request, 'target_type': 'token',
            'target_id': self.wounded['id'], 'roll_mode': 'physical', 'd20': d20})

    def test_mordida_is_own_targeted_attack_heals_once_free(self):
        reply = self.bite()
        self.assertEqual(200, reply.status_code, reply.text)
        preview = reply.json()
        self.assertEqual('mordida', preview['attack_id'])
        self.assertEqual('1d4', preview['damage_formula'])
        self.assertEqual(5, self.laminas())
        confirmed, applied = confirm_attack_resolution(self.db, resolution_id=preview['resolution_id'],
            requested_by_id='raziel', requested_by_role='player')
        self.assertTrue(applied)
        drain = confirmed['breakdown']['drain_result']
        self.assertEqual(confirmed['hp_before'] - confirmed['hp_after'], drain['drained'])
        self.assertEqual(min(16, 10 + drain['drained']), drain['hp_after'])
        self.assertEqual(5, self.laminas())
        replay, repeated = confirm_attack_resolution(self.db, resolution_id=preview['resolution_id'],
            requested_by_id='raziel', requested_by_role='player')
        self.assertFalse(repeated)
        self.assertEqual(confirmed, replay)
        self.assertEqual(preview['resolution_id'], self.bite().json()['resolution_id'])

    def test_mordida_rejects_legacy_absorption_and_missing_target(self):
        record = self._confirmed_hit('legacy-hit')
        self.assertEqual(400, self.use('raziel', 'mordida', {'resolution_id': record['resolution_id']}).status_code)
        self.assertEqual(400, self.use('raziel', 'mordida').status_code)

    def test_mordida_rejects_dead_target(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=0 WHERE id=?', (self.wounded['id'],))
        self.assertEqual(400, self.bite().status_code)
        self.assertEqual(5, self.laminas())

    def test_mordida_miss_does_not_heal(self):
        preview = self.bite(d20=1).json()
        confirmed, _ = confirm_attack_resolution(self.db, resolution_id=preview['resolution_id'],
            requested_by_id='raziel', requested_by_role='player')
        self.assertEqual('miss', confirmed['result'])
        self.assertEqual(0, confirmed['breakdown']['drain_result']['healed'])

    def test_mordida_cure_limited_to_remaining_target_hp(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=1 WHERE id=?', (self.wounded['id'],))
        preview = self.bite(d20=20).json()
        confirmed, _ = confirm_attack_resolution(self.db, resolution_id=preview['resolution_id'],
            requested_by_id='raziel', requested_by_role='player')
        self.assertEqual(1, confirmed['breakdown']['drain_result']['healed'])
        self.assertEqual(0, confirmed['hp_after'])
        self.assertEqual(200, self.bite(d20=20).status_code, 'same request remains replayable after target death')

    def test_mordida_consumes_turn_and_new_encounter_allows_next_bite(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT OR REPLACE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('default','Arena','',1,'fixture','fixture')")
            db.execute("INSERT INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES(1,'default','Arena','','fixture')")
        def command(action, **payload):
            state = readeffects(self.db)
            return effect_command(self.db, actor_id='master', actor_role='gm', request_id=f"bite-{action}-{state['version']}",
                expected_version=state['version'], action=action, payload=payload)
        for number in (1, 2):
            with closing(sqlite3.connect(self.db)) as db, db:
                db.execute('UPDATE session_workspace_tokens SET current_hp=12 WHERE id=?', (self.wounded['id'],))
            command('start', map_id='default', battle_mode=True, participants=[
                {'target_type': 'character', 'target_id': 'raziel', 'initiative': 12},
                {'target_type': 'token', 'target_id': self.wounded['id'], 'initiative': 5}])
            preview = self.bite(f'bite-encounter-{number}').json()
            confirm_attack_resolution(self.db, resolution_id=preview['resolution_id'], requested_by_id='raziel', requested_by_role='player')
            self.assertTrue(readeffects(self.db)['encounter']['action_committed'])
            self.assertEqual(400, self.bite(f'bite-extra-{number}').status_code)
            command('end')

    def test_regeneration_spends_one_blood_heals_and_replays_without_double_cost(self):
        reply = self.use('raziel', 'regeneracao-vampirica', {'request_id': 'regenerate-001'})
        self.assertEqual(200, reply.status_code, reply.text)
        self.assertEqual(4, self.laminas())
        self.assertEqual(reply.json()['hp_before'] + reply.json()['healed'], reply.json()['hp_after'])
        self.assertTrue(1 <= reply.json()['heal_roll'] <= 4)
        self.assertEqual(reply.json(), self.use('raziel', 'regeneracao-vampirica', {'request_id': 'regenerate-001'}).json())
        self.assertEqual(4, self.laminas())

    def test_regeneration_blocks_zero_hp_full_hp_and_no_blood_without_writing(self):
        for hp, blood in ((0, 5), (16, 5), (10, 0)):
            with closing(sqlite3.connect(self.db)) as db, db:
                db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'", (json.dumps(_blood_state(hp=hp, laminas=blood)),))
            reply = self.use('raziel', 'regeneracao-vampirica', {'request_id': f'regenerate-block-{hp}-{blood}'})
            self.assertEqual(400, reply.status_code, reply.text)
            self.assertEqual(blood, self.laminas())

    def test_regeneration_respects_owner(self):
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='morthak')
        self.assertEqual(403, self.use('raziel', 'regeneracao-vampirica', {'request_id': 'other-owner'}).status_code)

    def test_regeneration_consumes_action_and_rejects_out_of_turn(self):
        encounter = {'active': True, 'battle_mode': True, 'map_id': 'default', 'turn_index': 1,
            'participants': [{'target_type': 'character', 'target_id': 'raziel'}, {'target_type': 'token', 'target_id': self.wounded['id']}],
            'action_committed': False}
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))
        self.assertEqual(400, self.use('raziel', 'regeneracao-vampirica', {'request_id': 'out-turn'}).status_code)
        self.assertEqual(5, self.laminas())
        encounter['turn_index'] = 0
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))
        self.assertEqual(200, self.use('raziel', 'regeneracao-vampirica', {'request_id': 'own-turn'}).status_code)
        self.assertTrue(readeffects(self.db)['encounter']['action_committed'])
        self.assertEqual(400, self.bite('after-regeneration').status_code)
        self.assertEqual(400, self.use('raziel', 'regeneracao-vampirica', {'request_id': 'extra-regen'}).status_code)
        self.assertEqual(4, self.laminas())

    def test_mordida_zero_hp_and_another_owner_rejected(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'", (json.dumps(_blood_state(hp=0)),))
        self.assertEqual(400, self.bite('dead-raziel').status_code)
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode='player', profile_id='morthak')
        self.assertEqual(403, self.bite('another-owner').status_code)
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
