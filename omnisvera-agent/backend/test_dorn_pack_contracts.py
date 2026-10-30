"""Approved Dorn pack uses typed metadata inside existing native transactions."""
import copy
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch

from app.action_library import native_action_contract, describe_action


class DornPackContractsTests(TestCase):
    def setUp(self):
        import test_dorn_approved_pack as fixtures
        self.fixture = fixtures.DornApprovedPackTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path

    def state(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT state_json,version FROM character_states WHERE profile_id='dorn7'").fetchone()

    def test_pack_contracts_resolve_existing_rules_and_do_not_grant(self):
        from app.dorn_mage import SPEC
        strength = native_action_contract('technique:dorn7:forca-arcana', 5)
        web = native_action_contract('technique:dorn7:teia', 5)
        dispel = native_action_contract('technique:dorn7:dissipar-magia', 5)
        self.assertIsNotNone(strength)
        self.assertIsNotNone(web)
        self.assertIsNotNone(dispel)
        self.assertEqual({'mode': 'touch', 'cells': 1}, strength['range'])
        self.assertEqual(5, strength['resolution']['strength_divisor'])
        self.assertEqual({'dice': '1d6', 'add': 5, 'multiplier': 600}, strength['resolution']['lifetime'])
        self.assertEqual(8, web['range']['meters'])
        self.assertEqual(6600, web['resolution']['lifetime_seconds'])
        self.assertEqual({'width_m': 3, 'height_m': 3, 'vertical_m': 6}, web['resolution']['dimensions'])
        self.assertEqual(25, dispel['range']['meters'])
        self.assertEqual({'dice': '1d20', 'add': 5, 'multiplier': 1}, dispel['resolution']['check'])
        for spell in ('forca-arcana', 'teia', 'dissipar-magia'):
            self.assertFalse(any(a['id'] == spell for a in SPEC['abilities']))
            description = describe_action(self.path, 'technique:dorn7:' + spell)
            self.assertFalse(description['executable'])
            self.assertEqual(spell, description['execute']['payload']['spell_id'])
            self.assertEqual('dorn_' + spell.replace('-', '_'), description['contract']['executor']['binding'])

    def test_stale_pack_revisions_reject_before_target_lookup_rng_or_cost(self):
        before = self.state()
        for spell in ('forca-arcana', 'teia', 'dissipar-magia'):
            with self.subTest(spell=spell), patch('app.dorn_spells.roll_formula') as dice:
                with self.assertRaisesRegex(ValueError, 'revisão|definição'):
                    self.fixture.cast(spell, definition_revision='obsolete')
                dice.assert_not_called()
                self.assertEqual(before, self.state())

    def test_strength_native_duration_bonus_receipt_and_contract(self):
        contract = native_action_contract('technique:dorn7:forca-arcana', 3)
        self.assertIsNotNone(contract)
        payload = {'targets': [{'type': 'character', 'id': 'dorn7'}], 'definition_revision': contract['revision'],
                   'strength_divisor': 1, 'duration_seconds': 999999, 'cost': 0}
        with patch('app.dorn_spells.roll_formula', return_value={'total': 2}) as dice:
            first = self.fixture.cast('forca-arcana', **payload)
            retry = self.fixture.cast('forca-arcana', **payload)
        self.assertEqual(first, retry)
        self.assertEqual(1, dice.call_count)
        effect = first['protocol_result']['results'][0]['effect']
        self.assertEqual((14, 2, 3000), (effect['original_strength'], effect['modifiers']['strength_bonus'], effect['remaining_seconds']))
        self.assertEqual(contract['revision'], first['protocol_result']['action_contract']['revision'])
        self.assertEqual(0, first['protocol_result']['resource_remaining'])

    def test_web_native_area_duration_and_retry_without_dice(self):
        self.fixture.grid()
        contract = native_action_contract('technique:dorn7:teia', 3)
        self.assertIsNotNone(contract)
        payload = {'targets': [{'type': 'token', 'id': self.fixture.fixture.enemy['id']}],
                   'definition_revision': contract['revision'], 'width_m': 1000, 'cost': 0}
        with patch('app.dorn_spells.roll_formula') as dice:
            first = self.fixture.cast('teia', **payload)
            retry = self.fixture.cast('teia', **payload)
        self.assertEqual(first, retry)
        dice.assert_not_called()
        effect = first['protocol_result']['results'][0]['effect']
        self.assertEqual(5400, effect['remaining_seconds'])
        self.assertEqual((3, 3, 6), tuple(effect['web_area'][key] for key in ('width_m', 'height_m', 'vertical_m')))
        self.assertEqual(contract['revision'], first['protocol_result']['action_contract']['revision'])

    def test_dispel_native_check_and_persisted_difficulty(self):
        from app.necromancer_spells import add_effect
        with closing(sqlite3.connect(self.path)) as db, db:
            effect = add_effect(db, {'type': 'character', 'id': 'dorn7'}, 'Proteção', 'fixture', 'now',
                                magic_type='arcane', spell_circle=2, caster_level=5)
        contract = native_action_contract('technique:dorn7:dissipar-magia', 3)
        self.assertIsNotNone(contract)
        payload = {'effect_id': effect['id'], 'definition_revision': contract['revision'], 'difficulty': 0, 'cost': 0}
        with patch('app.dorn_spells.roll_formula', return_value={'total': 10}) as dice:
            first = self.fixture.cast('dissipar-magia', **payload)
            retry = self.fixture.cast('dissipar-magia', **payload)
        self.assertEqual(first, retry)
        self.assertEqual(1, dice.call_count)
        result = first['protocol_result']['results'][0]
        self.assertEqual((10, 13, 12, True), (result['d20'], result['total'], result['difficulty'], result['success']))
        self.assertEqual(contract['revision'], first['protocol_result']['action_contract']['revision'])

    def test_concurrent_strength_retry_uses_one_effect_one_resource_one_ledger_entry(self):
        from app.combat_effects import effect_command, readeffects
        args = dict(actor_id='master', actor_role='gm', request_id='contract-strength-concurrent',
                    expected_version=readeffects(self.path)['version'], action='dorn_spell_cast',
                    payload={'spell_id': 'forca-arcana', 'targets': [{'type': 'character', 'id': 'dorn7'}]})
        with patch('app.dorn_spells.roll_formula', return_value={'total': 2}) as dice:
            with ThreadPoolExecutor(2) as pool:
                first, retry = list(pool.map(lambda _: effect_command(self.path, **args), range(2)))
        self.assertEqual(first, retry)
        self.assertEqual(1, dice.call_count)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(1, db.execute("SELECT count(*) FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.spell')='forca-arcana'").fetchone()[0])
            self.assertEqual(1, db.execute('SELECT count(*) FROM combat_effect_commands WHERE request_id=?', (args['request_id'],)).fetchone()[0])
            self.assertEqual(1, db.execute("SELECT count(*) FROM session_ledger WHERE source_type='combat_effect' AND source_id=?", (args['request_id'],)).fetchone()[0])

    def test_late_native_cost_failure_rolls_back_effect_and_resource_version(self):
        from app.combat_effects import readeffects
        before = self.state()
        effects = readeffects(self.path)
        with patch('app.dorn_spells.roll_formula', return_value={'total': 2}), \
                patch('app.action_components.spend_native_resource', side_effect=ValueError('late cost failure')):
            with self.assertRaisesRegex(ValueError, 'late cost failure'):
                self.fixture.cast('forca-arcana', targets=[{'type': 'character', 'id': 'dorn7'}])
        self.assertEqual(before, self.state())
        self.assertEqual(effects, readeffects(self.path))

    def test_strength_consumes_existing_main_action_and_prevents_a_second_spell(self):
        from app.combat_effects import effect_command, readeffects
        map_id, _ = self.fixture.grid()
        effect_command(self.path, actor_id='master', actor_role='gm', request_id='contract-pack-start',
                       expected_version=readeffects(self.path)['version'], action='start',
                       payload={'map_id': map_id, 'battle_mode': True, 'participants': [
                           {'target_type': 'character', 'target_id': 'dorn7', 'name': 'Dorn', 'initiative': 20},
                           {'target_type': 'token', 'target_id': self.fixture.fixture.enemy['id'], 'name': 'Alvo', 'initiative': 1}]})
        with patch('app.dorn_spells.roll_formula', return_value={'total': 2}):
            result = self.fixture.cast('forca-arcana', targets=[{'type': 'character', 'id': 'dorn7'}])
        self.assertTrue(result['encounter']['action_committed'])
        self.assertEqual(1, result['encounter']['attacks_used'])
        before = self.state()
        with patch('app.dorn_spells.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError, 'ação|turno'):
                self.fixture.cast('reflexos')
            dice.assert_not_called()
        self.assertEqual(before, self.state())

    def test_pack_schema_rejects_extra_fields_types_and_unbounded_formulas(self):
        from app.action_contract import resolve_contract
        from app.dorn_mage import SPEC
        for spell in ('forca-arcana', 'teia', 'dissipar-magia'):
            raw = SPEC['action_contracts'].get(spell)
            self.assertIsNotNone(raw)
            for path, value in [(('costs', 0, 'amount'), True), (('resolution', 'code'), 'eval'),
                                (('targeting', 'max_targets'), 1.0), (('executor', 'binding'), 'eval')]:
                bad = copy.deepcopy(raw)
                node = bad
                for part in path[:-1]:
                    node = node[part]
                node[path[-1]] = value
                with self.subTest(spell=spell, path=path), self.assertRaises(ValueError):
                    resolve_contract(bad, 5)
        bad = copy.deepcopy(SPEC['action_contracts']['teia'])
        bad['range']['meters']['base'] = 10000
        with self.assertRaises(ValueError):
            resolve_contract(bad, 5)
