from contextlib import closing
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import json

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.character_play import init_character_play, _connect, load_definition_overrides, build_character_definition, get_or_create_state
from app.level_advancement import preview, apply
from app.level_routes import register


class LevelAdvancementTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "test.sqlite3"
        init_character_play(self.db)
        self.character = {"definition": {"id": "vezemir", "class_name": "Guerreiro", "level": 1,
            "base_attributes": {"constitution": 16}, "defenses": {"saving_throw": "16"},
            "progression": {"base_maximum_hp": 12, "maximum_hp_modifier": 0, "base_attack": 1}}}
        with closing(_connect(self.db)) as connection, connection:
            connection.execute("INSERT INTO character_states VALUES(?,?,?,?)", ("vezemir", json.dumps({"maximum_hp": 12, "current_hp": 4, "resources": [{"key": "custom", "current": 1, "maximum": 5}]}), 1, "test"))
            connection.execute("INSERT INTO character_definition_overrides VALUES(?,?,?)", ("vezemir", json.dumps({"armor_class": 22, "attributes": {"strength": 13}}), "test"))

    def test_preview_is_read_only_and_promotes_atomically_without_healing(self):
        plan = preview(self.db, self.character, 3, hp_policy='preserve_current')
        self.assertEqual("ready", plan["status"])
        self.assertEqual(18, plan["changes"][1]["after"])
        self.assertNotIn("level", load_definition_overrides(self.db, "vezemir"))
        self.assertTrue(apply(self.db, self.character, plan["fingerprint"], 3, hp_policy='preserve_current'))
        self.assertFalse(apply(self.db, self.character, plan["fingerprint"], 3, hp_policy='preserve_current'))
        overrides = load_definition_overrides(self.db, "vezemir")
        self.assertEqual(22, overrides["armor_class"])
        self.assertEqual({"strength": 13}, overrides["attributes"])
        with closing(_connect(self.db)) as connection:
            state = json.loads(connection.execute("SELECT state_json FROM character_states").fetchone()[0])
            self.assertEqual((18, 4), (state["maximum_hp"], state["current_hp"]))
            self.assertEqual(1, state["resources"][0]["current"])
            self.assertEqual(1, connection.execute("SELECT count(*) FROM character_events").fetchone()[0])

    def test_already_level_two_preserves_hp_and_does_not_add_ba_twice(self):
        self.character["definition"].update(level=2)
        self.character["definition"]["progression"].update(base_attack=2, base_maximum_hp=17)
        plan = preview(self.db, self.character)
        self.assertEqual(17, plan["changes"][1]["after"])
        apply(self.db, self.character, plan["fingerprint"])
        self.assertEqual(0, load_definition_overrides(self.db, "vezemir")["advancement_attack_delta"])

    def test_session6_preserve_wounds_is_explicit_and_idempotent(self):
        with closing(_connect(self.db)) as connection, connection:
            connection.execute("UPDATE character_states SET state_json=?", (json.dumps({'maximum_hp': 12, 'current_hp': 3, 'resources': []}),))
        plan = preview(self.db, self.character, 3, hp_policy='preserve_wounds')
        self.assertTrue(apply(self.db, self.character, plan['fingerprint'], 3, hp_policy='preserve_wounds'))
        self.assertFalse(apply(self.db, self.character, plan['fingerprint'], 3, hp_policy='preserve_wounds'))
        with closing(_connect(self.db)) as connection:
            state = json.loads(connection.execute('SELECT state_json FROM character_states').fetchone()[0])
        self.assertEqual((18, 9), (state['maximum_hp'], state['current_hp']))

    def test_preserve_wounds_does_not_revive_at_zero_hp(self):
        with closing(_connect(self.db)) as connection, connection:
            connection.execute("UPDATE character_states SET state_json=?", (json.dumps({'maximum_hp': 12, 'current_hp': 0, 'resources': []}),))
        plan = preview(self.db, self.character, 3, hp_policy='preserve_wounds')
        apply(self.db, self.character, plan['fingerprint'], 3, hp_policy='preserve_wounds')
        with closing(_connect(self.db)) as connection:
            self.assertEqual(0, json.loads(connection.execute('SELECT state_json FROM character_states').fetchone()[0])['current_hp'])

    def test_stale_preview_is_rejected(self):
        plan = preview(self.db, self.character, 3)
        with closing(_connect(self.db)) as connection, connection:
            connection.execute("UPDATE character_states SET version=version+1")
        with self.assertRaisesRegex(ValueError, "mudou"):
            apply(self.db, self.character, plan["fingerprint"], 3)
        self.assertNotIn("level", load_definition_overrides(self.db, "vezemir"))

    def test_raziel_approved_adaptation_preserves_spent_blood_and_locked_sense(self):
        self.character["definition"].update(id="raziel", class_name="Hemomante", level=2)
        self.character["definition"]["defenses"]["saving_throw"] = "15"
        resources = [{"key": "reserva-de-sangue", "maximum": 5, "current": 2},
                     {"key": "sentido-do-sangue", "maximum": 1, "current": 1, "blocked": True}]
        with closing(_connect(self.db)) as connection, connection:
            connection.execute("UPDATE character_states SET profile_id=?,state_json=?", ("raziel", json.dumps({"maximum_hp": 12, "current_hp": 4, "resources": resources})))
        plan = preview(self.db, self.character)
        self.assertEqual("ready", plan["status"])
        apply(self.db, self.character, plan["fingerprint"])
        with closing(_connect(self.db)) as connection:
            state = json.loads(connection.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
        self.assertEqual(resources, state["resources"])

    def test_failure_rolls_back_definition_state_and_audit(self):
        plan = preview(self.db, self.character, 3)
        with patch("app.level_advancement._write_event", side_effect=RuntimeError("disk failure")):
            with self.assertRaises(RuntimeError):
                apply(self.db, self.character, plan["fingerprint"], 3)
        self.assertNotIn("level", load_definition_overrides(self.db, "vezemir"))
        with closing(_connect(self.db)) as connection:
            self.assertEqual(12, json.loads(connection.execute("SELECT state_json FROM character_states").fetchone()[0])["maximum_hp"])

    def test_missing_choice_and_ambiguous_custom_ba_block(self):
        self.assertEqual("blocked", preview(self.db, self.character)["status"])
        self.character["definition"]["progression"]["base_attack"] = 7
        self.assertEqual("blocked", preview(self.db, self.character, 3)["status"])

    def test_unknown_character_is_not_modified(self):
        self.character["definition"]["id"] = "morthak"
        with self.assertRaises(ValueError):
            preview(self.db, self.character)

    def test_attack_offset_preserves_existing_bonuses(self):
        plan = preview(self.db, self.character, 3)
        apply(self.db, self.character, plan["fingerprint"], 3)
        sheet = {"steps": [{"key": "character_class", "fields": {"base_attack": 1}}, {"key": "attacks", "fields": {"melee_bonus": 4, "ranged_bonus": 3}}]}
        definition = build_character_definition(profile_id="vezemir", note={"frontmatter": {}, "content": ""}, sheet=sheet, inventory=[], overrides=load_definition_overrides(self.db, "vezemir"))
        self.assertEqual(2, definition["progression"]["base_attack"])
        self.assertEqual([5, 4], [a["attack_bonus"] for a in definition["attacks"]])

    def test_route_requires_master_and_rejects_identity_injection(self):
        app = FastAPI()
        def deny():
            raise HTTPException(403, "GM only")
        register(app, deny, lambda *args: self.character, lambda: self.db)
        with closing(TestClient(app)) as client:
            self.assertEqual(403, client.post("/gm/characters/vezemir/level/preview", json={}).status_code)
        app = FastAPI()
        register(app, lambda: "gm", lambda *args: self.character, lambda: self.db)
        with closing(TestClient(app)) as client:
            self.assertEqual(422, client.post("/gm/characters/vezemir/level/preview", json={"actor": "master"}).status_code)
            response = client.post("/gm/characters/vezemir/level/preview", json={"hp_roll": 3})
            self.assertEqual(200, response.status_code)
            self.assertNotIn("_baseline", response.json())

    def test_manual_morthak_level_requires_roll_and_updates_slots_without_refill(self):
        definition = self.character['definition']
        definition.update(id='morthak', class_name='Mago', level=2)
        definition['base_attributes'] = {'constitution': 10, 'intelligence': 20}
        definition['progression'].update(base_maximum_hp=4, base_attack=0)
        definition['defenses']['saving_throw'] = '14'
        before = {'level': 1, 'maximum_hp': 4}
        after = {'level': 2, 'maximum_hp': 4}
        resources = [{'key': 'magias_de_1o_circulo', 'label': 'Magias de 1º círculo', 'maximum': 1, 'current': 0},
                     {'key': 'misseis_magicos', 'maximum': 3, 'current': 1}]
        with closing(_connect(self.db)) as c, c:
            c.execute('UPDATE character_states SET profile_id=?,state_json=?', ('morthak', json.dumps({'current_hp': 3, 'maximum_hp': 4, 'resources': resources})))
            c.execute('UPDATE character_definition_overrides SET profile_id=?,data_json=?', ('morthak', json.dumps(after)))
            from app.character_play import _write_event
            _write_event(c, character_id='morthak', actor_id='master', actor_role='gm', event_type='definition_update',
                         field='definition', before=before, after=after, reason='manual', session_id=None)
        self.assertEqual('blocked', preview(self.db, self.character, hp_policy='preserve_current')['status'])
        plan = preview(self.db, self.character, 3, hp_policy='preserve_current')
        self.assertTrue(plan['requires_hp_roll'])
        self.assertEqual(7, plan['changes'][1]['after'])
        self.assertTrue(apply(self.db, self.character, plan['fingerprint'], 3, hp_policy='preserve_current'))
        self.assertFalse(apply(self.db, self.character, plan['fingerprint'], 3, hp_policy='preserve_current'))
        overrides = load_definition_overrides(self.db, 'morthak')
        self.assertEqual(4, overrides['advancement_resources']['magias_de_1o_circulo'])
        sheet = {'steps': [{'key': 'character_class', 'fields': {'base_attack': 0, 'saving_throw': 14},
                           'guide': {'sources': []}}]}
        definition = build_character_definition(profile_id='morthak', note={'frontmatter': {}, 'content': ''}, sheet=sheet, inventory=[], overrides=overrides)
        with patch('app.character_play.seed_all_resources', return_value=resources):
            for _ in range(2):
                state = get_or_create_state(self.db, profile_id='morthak', sheet=sheet, definition=definition)
                self.assertEqual((7, 3), (state['maximum_hp'], state['current_hp']))
                self.assertEqual((4, 0), (state['resources'][0]['maximum'], state['resources'][0]['current']))
                self.assertEqual((3, 1), (state['resources'][1]['maximum'], state['resources'][1]['current']))

    def test_successive_levels_accumulate_attack_delta_and_change_saving_throw(self):
        for target in (2, 3, 4):
            plan = preview(self.db, self.character, 2, target)
            apply(self.db, self.character, plan['fingerprint'], 2, target)
            overrides = load_definition_overrides(self.db, 'vezemir')
            d = self.character['definition']
            d['level'] = target
            d['defenses']['saving_throw'] = overrides['advancement_saving_throw']
            d['progression'].update(base_attack=overrides['advancement_base_attack'], base_maximum_hp=overrides['maximum_hp'])
        self.assertEqual(3, overrides['advancement_attack_delta'])
        self.assertEqual(15, overrides['advancement_saving_throw'])
        self.assertEqual(3, len(overrides['advancement_history']))
        first = overrides['advancement_history'][0]
        self.assertFalse(apply(self.db, self.character, first['fingerprint'], 2, 2))
        blocked = preview(self.db, self.character, 2, 5)
        self.assertEqual('blocked', blocked['status'])

    def _manual_bump(self, profile_id, before, after):
        from app.character_play import _write_event
        with closing(_connect(self.db)) as connection, connection:
            connection.execute("UPDATE character_states SET profile_id=?", (profile_id,))
            connection.execute("UPDATE character_definition_overrides SET profile_id=?,data_json=?",
                               (profile_id, json.dumps(after)))
            _write_event(connection, character_id=profile_id, actor_id='master', actor_role='gm',
                         event_type='definition_update', field='definition',
                         before=before, after=after, reason='manual', session_id=None)

    def test_manual_level_proof_unlocks_advance_without_system_grant(self):
        self.character["definition"].update(level=2)
        self.character["definition"]["progression"].update(base_attack=2, base_maximum_hp=17)
        self._manual_bump("vezemir", {"level": 1, "maximum_hp": 12}, {"level": 2, "maximum_hp": 17})
        self.assertEqual("blocked", preview(self.db, self.character, target_level=3)["status"])
        plan = preview(self.db, self.character, 6, 3)
        self.assertEqual("ready", plan["status"])
        self.assertTrue(plan["requires_hp_roll"])
        self.assertEqual(26, plan["changes"][1]["after"])
        self.assertTrue(any("dado de vida" in w for w in plan["warnings"]))
        self.assertTrue(apply(self.db, self.character, plan["fingerprint"], 6, 3))
        overrides = load_definition_overrides(self.db, "vezemir")
        self.assertEqual(3, overrides["level"])
        self.assertEqual(3, overrides["advancement_base_attack"])

    def test_dorn_reconcile_grants_missing_level_three_benefits(self):
        definition = self.character["definition"]
        definition.update(id="dorn7", class_name="Mago", level=3,
                          base_attributes={"constitution": 16, "intelligence": 16})
        definition["progression"].update(base_maximum_hp=13, base_attack=0)
        definition["defenses"]["saving_throw"] = "14"
        with closing(_connect(self.db)) as connection, connection:
            connection.execute("UPDATE character_states SET profile_id=?,state_json=?",
                               ("dorn7", json.dumps({"maximum_hp": 13, "current_hp": 5, "resources": []})))
            connection.execute("UPDATE character_definition_overrides SET profile_id=?,data_json=?",
                               ("dorn7", json.dumps({"level": 3, "maximum_hp": 13})))
        self._manual_bump("dorn7", {"level": 2, "maximum_hp": 13}, {"level": 3, "maximum_hp": 13})
        plan = preview(self.db, self.character, 4, 3)
        self.assertEqual("ready", plan["status"])
        self.assertEqual(20, plan["changes"][1]["after"])
        by_field = {c["field"]: c for c in plan["changes"]}
        self.assertEqual(1, by_field["base_attack"]["after"])
        self.assertTrue(by_field["saving_throw"]["noop"])
        self.assertEqual(20, by_field["maximum_hp_final"]["after"])
        self.assertTrue(apply(self.db, self.character, plan["fingerprint"], 4, 3))
        overrides = load_definition_overrides(self.db, "dorn7")
        self.assertEqual(1, overrides["advancement_attack_delta"])
        with closing(_connect(self.db)) as connection:
            state = json.loads(connection.execute("SELECT state_json FROM character_states").fetchone()[0])
        self.assertEqual((20, 12), (state["maximum_hp"], state["current_hp"]))

    def test_xp_requirement_is_shown_as_warning_not_blocker(self):
        self.character["definition"].update(level=2)
        self.character["definition"]["progression"].update(base_attack=2, base_maximum_hp=17)
        self._manual_bump("vezemir", {"level": 1, "maximum_hp": 12}, {"level": 2, "maximum_hp": 17})
        plan = preview(self.db, self.character, 6, 3)
        self.assertEqual(4000, plan["xp_required"])
        self.assertTrue(any("XP" in w for w in plan["warnings"]))
        self.assertEqual("ready", plan["status"])

    def test_default_policy_preserves_wounds(self):
        plan = preview(self.db, self.character, 3)
        self.assertEqual("preserve_wounds", plan["hp_policy"])

    def test_skipped_level_and_unreviewed_raziel_choices_do_not_grant(self):
        with self.assertRaises(ValueError):
            preview(self.db, self.character, 2, 3)
        self.character['definition'].update(id='raziel', class_name='Hemomante', level=2)
        with closing(_connect(self.db)) as connection, connection:
            connection.execute("UPDATE character_states SET profile_id='raziel'")
            connection.execute("UPDATE character_definition_overrides SET profile_id='raziel'")
        blocked = preview(self.db, self.character, 2, 3)
        self.assertEqual('blocked', blocked['status'])
        self.assertIsNone(blocked['fingerprint'])
        self.assertTrue(any('Mestre' in b for b in blocked['blockers']))
