"""Approved high spells share metadata, never a parallel invocation executor."""
import copy
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch

from app.action_library import native_action_contract
from app.combat_effects import effect_command, readeffects


class MorthakActionContractsTests(TestCase):
    def setUp(self):
        import test_morthak_high_spells as fixtures
        self.fixture = fixtures.HighSpellTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path

    def state(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT state_json,version FROM character_states WHERE profile_id='morthak'").fetchone()

    def fragment(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT quantity FROM player_inventory WHERE item_path='fragment-test'").fetchone()[0]

    def cast(self, spell, **payload):
        return self.fixture.command('necro_spell_cast', {'spell_id': spell, **payload}, request='contract-' + spell)

    def test_high_contracts_resolve_approved_range_costs_and_circle_not_character_level(self):
        clone = native_action_contract('technique:morthak:clonagem', 5)
        death = native_action_contract('technique:morthak:magia-da-morte', 5)
        self.assertIsNotNone(clone)
        self.assertIsNotNone(death)
        self.assertEqual(10, clone['range']['meters'])
        self.assertEqual(8, death['range']['meters'])
        self.assertEqual('clonagem_circle', clone['resolution']['clone_count']['source'])
        self.assertEqual((5, 9, 3), tuple(clone['resolution']['clone_count'][k] for k in ('min_circle', 'max_circle', 'subtract')))
        self.assertEqual(1, clone['costs'][1]['amount'])
        self.assertEqual(10, death['costs'][1]['retained_divisor'])
        self.assertEqual('2d6', death['resolution']['victim_limit']['dice'])
        self.assertEqual(4, death['resolution']['max_hit_dice'])
        self.assertTrue(death['resolution']['include_allies'])

    def test_stale_clone_revision_rejects_without_resource_component_effect_or_rng(self):
        before, effects, fragment = self.state(), readeffects(self.path), self.fragment()
        with patch('app.morthak_high_spells.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError, 'revisão|definição'):
                self.cast('clonagem', definition_revision='obsolete')
            dice.assert_not_called()
        self.assertEqual(before, self.state())
        self.assertEqual(effects, readeffects(self.path))
        self.assertEqual(fragment, self.fragment())

    def test_stale_death_revision_rejects_before_dice_save_or_hp_cost(self):
        before, effects = self.state(), readeffects(self.path)
        with patch('app.morthak_high_spells.roll_formula') as dice, \
                patch('app.necromancer_spells.save_difficult', return_value={'success': True, 'total': 20}) as save:
            with self.assertRaisesRegex(ValueError, 'revisão|definição'):
                self.cast('magia-da-morte', definition_revision='obsolete')
            dice.assert_not_called()
            save.assert_not_called()
        self.assertEqual(before, self.state())
        self.assertEqual(effects, readeffects(self.path))

    def test_clone_circle_progression_and_minimum_hp_preserve_native_clamp(self):
        from app.morthak_action_contracts import clone_circle_and_count
        contract = native_action_contract('technique:morthak:clonagem', 5)
        self.assertIsNotNone(contract)
        for value, expected in [(None, (5, 2)), (0, (5, 2)), (4, (5, 2)), (7, (7, 4)), (9, (9, 6)), (12, (9, 6))]:
            self.assertEqual(expected, clone_circle_and_count(contract, value))
        with closing(sqlite3.connect(self.path)) as db, db:
            data = json.loads(db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='morthak'").fetchone()[0])
            data['clonagem_circle'] = 7
            db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='morthak'", (json.dumps(data),))
            db.execute("UPDATE character_states SET state_json=json_set(state_json,'$.maximum_hp',3,'$.current_hp',3) WHERE profile_id='morthak'")
        result = self.cast('clonagem', definition_revision=contract['revision'])
        effect = result['protocol_result']['results'][0]['effect']
        self.assertEqual((7, 4, 1, 5), (effect['spell_circle'], effect['clone_count'], effect['clone_spec']['hp'], effect['rounds']))
        self.assertEqual(contract['revision'], result['protocol_result']['action_contract']['revision'])
        self.assertEqual(0, self.fragment())

    def test_concurrent_clone_retry_spawns_once_and_spends_one_component_and_resource(self):
        args = dict(actor_id='morthak', actor_role='player', request_id='contract-clone-concurrent',
                    expected_version=readeffects(self.path)['version'], action='necro_spell_cast',
                    payload={'spell_id': 'clonagem'}, allow_player=True)
        with ThreadPoolExecutor(2) as pool:
            first, retry = list(pool.map(lambda _: effect_command(self.path, **args), range(2)))
        self.assertEqual(first, retry)
        self.assertEqual(0, self.fragment())
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(2, db.execute("SELECT count(*) FROM session_workspace_tokens WHERE json_extract(sheet_json,'$.summon.technique')='clonagem'").fetchone()[0])
            self.assertEqual(1, db.execute("SELECT count(*) FROM session_ledger WHERE source_type='necro_high_spell'").fetchone()[0])
        self.assertIn('action_contract', first['protocol_result'])

    def test_death_uses_contract_roll_save_and_hp_cost_without_temporary_absorption(self):
        contract = native_action_contract('technique:morthak:magia-da-morte', 5)
        self.assertIsNotNone(contract)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE character_states SET state_json=json_set(state_json,'$.temporary_hp',10) WHERE profile_id='morthak'")
        with patch('app.morthak_high_spells.roll_formula', return_value={'total': 2}) as dice, \
                patch('app.necromancer_spells.save_difficult', return_value={'success': False, 'total': 1}) as save:
            first = self.cast('magia-da-morte', definition_revision=contract['revision'])
            retry = self.cast('magia-da-morte', definition_revision=contract['revision'])
        self.assertEqual(first, retry)
        self.assertEqual(1, dice.call_count)
        self.assertEqual('2d6', dice.call_args.args[0])
        self.assertEqual('constitution', save.call_args.args[2])
        self.assertEqual(3, first['protocol_result']['hp_after'])
        self.assertEqual(10, json.loads(self.state()[0])['temporary_hp'])
        self.assertEqual(contract['revision'], first['protocol_result']['action_contract']['revision'])

    def test_contract_schema_rejects_unknown_fields_cross_binding_cost_and_json_types(self):
        from app.action_contract import resolve_contract
        from app.action_library import _technique_entry
        for spell in ('clonagem', 'magia-da-morte'):
            raw = _technique_entry('morthak', spell).get('action_contract')
            self.assertIsNotNone(raw)
            for path, value in [(('executor', 'binding'), 'eval'), (('resolution', 'code'), 'python'),
                                (('costs', 0, 'amount'), True), (('targeting', 'min_targets'), 1.0),
                                (('costs', 0, 'key'), 'forca_arcana')]:
                bad = copy.deepcopy(raw)
                node = bad
                for part in path[:-1]:
                    node = node[part]
                node[path[-1]] = value
                with self.subTest(spell=spell, path=path), self.assertRaises(ValueError):
                    resolve_contract(bad, 5)
            bad = copy.deepcopy(raw)
            bad['costs'].reverse()
            with self.assertRaises(ValueError):
                resolve_contract(bad, 5)

    def test_http_owner_forwards_revision_without_spending_on_rejection(self):
        before, fragment = self.state(), self.fragment()
        for spell in ('clonagem', 'magia-da-morte'):
            response = self.fixture.fixture.client.post('/characters/morthak/techniques/' + spell,
                json={'request_id': 'http-contract-' + spell, 'definition_revision': 'obsolete'})
            self.assertEqual(400, response.status_code, response.text)
            self.assertIn('revis', response.json()['detail'])
            self.assertEqual(before, self.state())
            self.assertEqual(fragment, self.fragment())

    def test_death_cost_preserves_latest_state_in_same_transaction_and_uses_current_hp(self):
        def save_hook(db, victim, attribute):
            db.execute("UPDATE character_states SET state_json=json_set(state_json,'$.current_hp',21,'$.runtime_hook_flag','preserved') WHERE profile_id='morthak'")
            return {'success': True, 'total': 20}
        with patch('app.morthak_high_spells.roll_formula', return_value={'total': 2}), \
                patch('app.necromancer_spells.save_difficult', side_effect=save_hook):
            result = self.cast('magia-da-morte')
        self.assertEqual(2, result['protocol_result']['hp_after'])
        current = json.loads(self.state()[0])
        self.assertEqual('preserved', current['runtime_hook_flag'])
        self.assertEqual(0, next(r['current'] for r in current['resources'] if r['key'] == 'magia_da_morte'))

    def test_late_component_cast_failure_rolls_back_pins_resource_and_inventory(self):
        before, effects, fragment = self.state(), readeffects(self.path), self.fragment()
        with closing(sqlite3.connect(self.path)) as db:
            pins = db.execute('SELECT count(*) FROM session_workspace_tokens').fetchone()[0]
        with patch('app.action_components.spend_native_resource', side_effect=ValueError('late resource failure')):
            with self.assertRaisesRegex(ValueError, 'late resource failure'):
                self.cast('clonagem')
        self.assertEqual(before, self.state())
        self.assertEqual(effects, readeffects(self.path))
        self.assertEqual(fragment, self.fragment())
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(pins, db.execute('SELECT count(*) FROM session_workspace_tokens').fetchone()[0])
            self.assertEqual(0, db.execute("SELECT count(*) FROM combat_effect_commands WHERE request_id='contract-clonagem'").fetchone()[0])

    def test_death_keeps_nearest_creatures_including_allies_but_filters_range_and_dv(self):
        from app.session_workspace import save_workspace_token
        created = []
        for name, x, dv, role in [('Aliado elegível', 6, 1, 'Aliado'),
                                   ('Fora do alcance', 11, 1, ''), ('DV alto', 6, 5, '')]:
            token = save_workspace_token(self.path, token_type='monster', name=name, map_id='default',
                latitude=20, longitude=20, visible_to_players=True, current_hp=10, maximum_hp=10,
                sheet={'saving_throw':20, 'hit_dice':dv, 'role':role})
            created.append(token)
            with closing(sqlite3.connect(self.path)) as db, db:
                db.execute("INSERT OR REPLACE INTO session_workspace_entity_positions VALUES('default',?,?,5,1,1,1)", (token['id'], x))
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=7 WHERE token_id=?", (self.fixture.fixture.ogre['id'],))
            db.execute("UPDATE session_workspace_tokens SET sheet_json=json_set(sheet_json,'$.hit_dice',4) WHERE id=?", (self.fixture.fixture.ogre['id'],))
        with patch('app.morthak_high_spells.roll_formula', return_value={'total':2}), \
                patch('app.necromancer_spells.save_difficult', return_value={'success':True, 'total':20}) as saves:
            result = self.cast('magia-da-morte', range_m=9999, max_hit_dice=99)
        self.assertEqual([created[0]['name'], self.fixture.fixture.ogre['name']],
                         [v['target'] for v in result['protocol_result']['results']])
        self.assertEqual(2, saves.call_count)
