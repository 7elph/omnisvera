"""Pilot equivalence: approved metadata delegates to native effect commands."""
import copy
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from unittest import TestCase
from unittest.mock import patch

from app.action_library import describe_action
from app.combat_effects import effect_command, readeffects
from app.session_workspace import save_workspace_token

REF = 'technique:dorn7:relampago'


class LightningContractTests(TestCase):
    def setUp(self):
        import test_dorn_spells as fixtures
        self.fixture = fixtures.DornSpellTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db

    def contract(self):
        return describe_action(self.db, REF)['contract']

    def set_level(self, level):
        with closing(sqlite3.connect(self.db)) as db, db:
            overrides = json.loads(db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='dorn7'").fetchone()[0])
            overrides['level'] = level
            db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='dorn7'", (json.dumps(overrides),))

    def command_args(self, targets, **extra):
        return dict(actor_id='master', actor_role='gm', request_id='contract-lightning-01',
                    expected_version=readeffects(self.db)['version'], action='dorn_spell_cast',
                    payload={'spell_id':'relampago', 'grid_selection':True,
                             'definition_revision':self.contract()['revision'], **extra,
                             'targets':[{'type':'token','id':identity} for identity in targets]})

    def test_library_contract_matches_level_and_does_not_enable_generic_executor(self):
        for level, meters, dice in [(3,70,'3d6'), (5,90,'5d6'), (12,160,'10d6')]:
            self.set_level(level)
            action = describe_action(self.db, REF)
            contract = action['contract']
            self.assertEqual(1, contract['schema_version'])
            self.assertEqual('dorn_relampago', contract['executor']['binding'])
            self.assertEqual((meters,dice), (contract['range']['meters'],contract['resolution']['damage']['formula']))
            self.assertEqual(3, contract['targeting']['max_targets'])
            self.assertEqual('dorn_relampago', action['costs'][0]['key'])
            self.assertFalse(action['executable'], 'Generic GM action endpoint is not a new player executor')
            self.assertEqual('/gm/combat/effects', action['execute']['endpoint'])

    def test_native_roll_shared_saves_half_floor_and_concurrent_retry_once(self):
        map_id = self.fixture.grid_lightning()
        second = save_workspace_token(self.db,token_type='monster',map_id=map_id,name='Second',
            latitude=0,longitude=5,current_hp=50,maximum_hp=50,sheet={'saving_throw':20})
        self.set_level(5)
        args = self.command_args([self.fixture.enemy['id'],second['id']],map_id=map_id)
        with patch('app.dorn_spells.roll_formula',side_effect=[
                {'total':15,'individual_results':[3]*5},
                {'total':20,'individual_results':[20]}, {'total':1,'individual_results':[1]}]) as dice:
            with ThreadPoolExecutor(2) as pool:
                first, retry = list(pool.map(lambda _:effect_command(self.db,**args), range(2)))
        self.assertEqual(first,retry)
        self.assertEqual(3,dice.call_count)
        self.assertEqual([4,7],[r['damage'] for r in first['protocol_result']['results']])
        self.assertEqual(self.contract()['revision'],first['protocol_result']['action_contract']['revision'])
        self.assertEqual(0,self.fixture.resource('relampago'))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(1,db.execute('SELECT count(*) FROM combat_effect_commands WHERE request_id=?',(args['request_id'],)).fetchone()[0])
            self.assertEqual(1,db.execute("SELECT count(*) FROM session_ledger WHERE source_type='combat_effect' AND source_id=?",(args['request_id'],)).fetchone()[0])
            self.assertEqual(43,db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(second['id'],)).fetchone()[0])
        # Retry returns the stored result before reading new level/revision.
        self.set_level(12)
        self.assertEqual(first,effect_command(self.db,**args))

    def test_old_revision_rejected_before_any_roll_or_consumption(self):
        self.fixture.grid_lightning()
        args = self.command_args([self.fixture.enemy['id']])
        args['payload']['definition_revision'] = 'obsolete'
        with patch('app.dorn_spells.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError,'revisão|definição'):
                effect_command(self.db,**args)
            dice.assert_not_called()
        self.assertEqual(1,self.fixture.resource('relampago'))

    def test_grid_can_hit_a_character_pin_but_cannot_double_hit_its_entity(self):
        map_id = self.fixture.grid_lightning()
        pin = save_workspace_token(self.db,token_type='character',character_id='dorn7',map_id=map_id,
            name='Second Dorn pin',latitude=0,longitude=2)
        args = self.command_args([pin['id']])
        with patch('app.dorn_spells.roll_formula',side_effect=[{'total':6,'individual_results':[2]*3},{'total':1,'individual_results':[1]}]):
            result = effect_command(self.db,**args)
        self.assertEqual('Unidade DORN-7',result['protocol_result']['results'][0]['target'])
        self.assertEqual(14,result['protocol_result']['results'][0]['hp_after'])

    def test_duplicate_character_pins_rejected_without_roll(self):
        map_id = self.fixture.grid_lightning()
        pin = save_workspace_token(self.db,token_type='character',character_id='dorn7',map_id=map_id,
            name='Second Dorn pin',latitude=0,longitude=2)
        with closing(sqlite3.connect(self.db)) as db:
            other = db.execute("SELECT id FROM session_workspace_tokens WHERE character_id='dorn7' AND id!=?",(pin['id'],)).fetchone()[0]
        args=self.command_args([pin['id'],other])
        with patch('app.dorn_spells.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError,'repetido'):
                effect_command(self.db,**args)
            dice.assert_not_called()

    def test_client_formula_never_changes_native_damage_and_stale_map_rejects(self):
        map_id = self.fixture.grid_lightning()
        args=self.command_args([self.fixture.enemy['id']],map_id='not-current')
        with patch('app.dorn_spells.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError,'mapa'):
                effect_command(self.db,**args)
            dice.assert_not_called()
        args['payload'].update(map_id=map_id,damage='999d20',range_m=99999,cost=0)
        with patch('app.dorn_spells.roll_formula',side_effect=[{'total':9,'individual_results':[3]*3},{'total':1,'individual_results':[1]}]) as dice:
            result=effect_command(self.db,**args)
        self.assertEqual('3d6',dice.call_args_list[0].args[0])
        self.assertEqual(9,result['protocol_result']['results'][0]['damage'])
        self.assertEqual(0,self.fixture.resource('relampago'))

    def test_definition_rejects_code_unknown_binding_and_unbounded_formula(self):
        from app.action_contract import resolve_contract
        from app.dorn_mage import SPEC
        raw = next(a['action_contract'] for a in SPEC['abilities'] if a['id']=='relampago')
        for key,value in [('executor',{'binding':'eval'}),('range',{'mode':'ranged','meters':'__import__("os")'})]:
            bad=copy.deepcopy(raw);bad[key]=value
            with self.assertRaises(ValueError):resolve_contract(bad,5)
        bad=copy.deepcopy(raw);bad['resolution']['damage']['count']['cap']=1000000
        with self.assertRaises(ValueError):resolve_contract(bad,5)

    def test_preview_uses_contract_at_real_scale_and_ignores_client_overrides(self):
        from app import main
        from app.access import AccessContext
        map_id=self.fixture.grid_lightning()
        self.set_level(5)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_map_grids SET cell_size_m=4 WHERE map_id=?',(map_id,))
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=23 WHERE token_id=?',(self.fixture.enemy['id'],))
        before=readeffects(self.db)
        with patch.object(main,'settings',replace(main.settings,database_path=self.db)), patch.object(main,'_playable_character',return_value={'definition':{'level':5}}):
            ring=main.gm_grid_range(ref=REF,attacker_token_id='',attacker_character_id='dorn7',
                map_id=map_id,slot='touch',max_range_m=9999,range_override_m=9999,access=AccessContext(mode='gm'))
        self.assertEqual((90,3,4),(ring['range_m'],ring['max_targets'],ring['cell_size_m']))
        self.assertEqual(self.contract(),ring['contract'])
        self.assertFalse(next(t for t in ring['targets'] if t['id']==self.fixture.enemy['id'])['valid'])
        self.assertEqual(before,readeffects(self.db))
        self.assertEqual(1,self.fixture.resource('relampago'))

    def test_sheet_uses_same_resolved_contract_without_reconciling_resources(self):
        from app.character_creation import list_sheets
        from app.character_play import build_character_definition, load_definition_overrides
        self.set_level(5)
        before=self.fixture.resource('relampago')
        sheet=next(s for s in list_sheets(self.db) if s['profile_id']=='dorn7')
        result=build_character_definition(profile_id='dorn7',note=self.fixture.base.note,sheet=sheet,
            inventory=[],overrides=load_definition_overrides(self.db,'dorn7'))
        ability=next(a for a in result['session_abilities'] if a['id']=='relampago')
        self.assertEqual(self.contract(),ability['action_contract'])
        self.assertIn('90 m',ability['description']);self.assertIn('5d6',ability['description'])
        self.assertEqual(before,self.fixture.resource('relampago'))
