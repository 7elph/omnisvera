"""Typed Vezemir adapters preserve native apply receipts, costs and turn rules."""
import copy
import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch

from app import main
from app.action_library import native_action_contract, describe_action
from app.combat_effects import readeffects


class VezemirBuffContractsTests(TestCase):
    def setUp(self):
        import test_vezemir_techniques as fixtures
        self.fixture = fixtures.VezemirTechniquesTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.path = self.fixture.db

    def state(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT state_json,version FROM character_states WHERE profile_id='vezemir'").fetchone()

    def use(self, skill, **payload):
        return self.fixture.client.post('/characters/vezemir/techniques/' + skill,
                                        json={'request_id': 'vezemir-contract-' + skill, **payload})

    def test_both_contracts_resolve_actual_level_cost_and_effect(self):
        strength = native_action_contract('technique:vezemir:forca-arcana', 5)
        speed = native_action_contract('technique:vezemir:velocidade', 5)
        self.assertIsNotNone(strength)
        self.assertIsNotNone(speed)
        self.assertEqual('self', strength['targeting']['kind'])
        self.assertEqual({'mode': 'self', 'meters': 0}, speed['range'])
        self.assertEqual('forca_arcana', strength['costs'][0]['key'])
        self.assertEqual({'dice': '1d6', 'add': 5, 'multiplier': 1}, strength['resolution']['lifetime'])
        self.assertEqual({'dice': '1d4', 'add': 5, 'multiplier': 1}, speed['resolution']['lifetime'])
        self.assertEqual({'movement_multiplier': 2, 'armor_class_bonus': 2, 'extra_attacks': 1}, speed['resolution']['modifiers'])
        before = self.state()
        for skill in ('forca-arcana', 'velocidade'):
            action = describe_action(self.path, 'technique:vezemir:' + skill)
            self.assertFalse(action['executable'])
            self.assertEqual('/characters/vezemir/techniques/' + skill, action['execute']['endpoint'])
            self.assertEqual('native_resource_turn_gate', action['contract']['action_budget'])
        self.assertEqual(before, self.state())

    def test_stale_revision_never_rolls_or_spends(self):
        before = self.state()
        for skill in ('forca-arcana', 'velocidade'):
            with self.subTest(skill=skill), patch('app.combat_effects.roll_formula') as dice:
                result = self.use(skill, definition_revision='obsolete')
                self.assertEqual(400, result.status_code, result.text)
                self.assertIn('revis', result.json()['detail'])
                dice.assert_not_called()
                self.assertEqual(before, self.state())
                self.assertEqual([], readeffects(self.path)['effects'])

    def test_speed_contract_drives_duration_modifiers_cost_and_legacy_retry(self):
        contract = native_action_contract('technique:vezemir:velocidade', 2)
        self.assertIsNotNone(contract)
        with patch('app.combat_effects.roll_formula', return_value={'total': 5}) as dice:
            first = self.use('velocidade', definition_revision=contract['revision'])
            second = self.use('velocidade', definition_revision=contract['revision'])
        self.assertEqual(200, first.status_code, first.text)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(1, dice.call_count)
        self.assertEqual('1d4+2', dice.call_args.args[0])
        effect = first.json()['effect']['effects'][0]
        self.assertEqual(5, first.json()['duration_rounds'])
        self.assertEqual(contract['resolution']['modifiers'], effect['modifiers'])
        self.assertEqual(0, next(r['current'] for r in json.loads(self.state()[0])['resources'] if r['key'] == 'velocidade'))

    def test_strength_contract_uses_effective_strength_and_preserves_hp(self):
        contract = native_action_contract('technique:vezemir:forca-arcana', 5)
        self.assertIsNotNone(contract)
        with patch.object(main, '_playable_character', return_value={'definition': {'level': 5, 'attributes': {'strength': 19}}}), \
                patch('app.combat_effects.roll_formula', return_value={'total': 7}) as dice:
            result = self.use('forca-arcana', definition_revision=contract['revision'])
        self.assertEqual(200, result.status_code, result.text)
        effect = result.json()['effect']['effects'][0]
        self.assertEqual({'strength_bonus': 3}, effect['modifiers'])
        self.assertIn('19→22', effect['label'])
        self.assertEqual('1d6+5', dice.call_args.args[0])
        self.assertEqual(17, json.loads(self.state()[0])['current_hp'])

    def test_schema_rejects_script_binding_wrong_cost_and_json_types(self):
        from app.action_contract import resolve_contract
        from app.action_library import _technique_entry
        for skill in ('forca-arcana', 'velocidade'):
            raw = _technique_entry('vezemir', skill).get('action_contract')
            self.assertIsNotNone(raw)
            for path, value in [(('executor', 'binding'), 'eval'), (('resolution', 'code'), 'python'),
                                (('costs', 0, 'amount'), True), (('range', 'meters'), False)]:
                bad = copy.deepcopy(raw)
                node = bad
                for part in path[:-1]:
                    node = node[part]
                node[path[-1]] = value
                with self.subTest(skill=skill, path=path), self.assertRaises(ValueError):
                    resolve_contract(bad, 5)
            bad = copy.deepcopy(raw)
            bad['costs'][0]['key'] = 'velocidade' if skill == 'forca-arcana' else 'forca_arcana'
            with self.assertRaises(ValueError):
                resolve_contract(bad, 5)
