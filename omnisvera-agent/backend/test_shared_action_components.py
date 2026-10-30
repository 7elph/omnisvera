import json
import copy
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch

from app.action_library import native_action_contract


class SharedActionComponentsTests(TestCase):
    def setUp(self):
        import test_dorn_approved_pack as fixtures
        self.fixture=fixtures.DornApprovedPackTests();self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups);self.db=self.fixture.path

    def test_second_contract_resolves_self_effect_without_fabricated_damage(self):
        contract=native_action_contract('technique:dorn7:reflexos',5)
        self.assertIsNotNone(contract)
        self.assertEqual('self',contract['range']['mode'])
        self.assertEqual('mirror_images',contract['resolution']['effect'])
        self.assertNotIn('damage',contract['resolution'])
        self.assertEqual('fictional_time',contract['duration'])

    def test_reflexos_uses_contract_and_native_receipt_and_budget(self):
        with patch('app.dorn_spells.roll_formula',side_effect=[{'total':2},{'total':4}]) as dice:
            first=self.fixture.cast('reflexos')
            retry=self.fixture.cast('reflexos')
        self.assertEqual(first,retry);self.assertEqual(2,dice.call_count)
        effect=first['protocol_result']['results'][0]['effect']
        self.assertEqual((3,4200),(effect['images_remaining'],effect['remaining_seconds']))
        self.assertEqual('dorn-reflexos-campaign-v2',first['protocol_result']['action_contract']['revision'])

    def test_stale_reflexos_revision_never_rolls_or_spends(self):
        with patch('app.dorn_spells.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError,'revisão|definição'):
                self.fixture.cast('reflexos',definition_revision='obsolete')
            dice.assert_not_called()
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
        self.assertEqual(1,next(r['current'] for r in state['resources'] if r['key']=='dorn_reflexos'))

    def test_shared_resource_consumer_preserves_current_hp_and_rejects_overspend(self):
        from app.action_components import spend_native_resource
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0]);state['current_hp']=7
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='dorn7'",(json.dumps(state),))
            self.assertEqual(0,spend_native_resource(db,'dorn7','dorn_reflexos',1,'now'))
            with self.assertRaises(ValueError):spend_native_resource(db,'dorn7','dorn_reflexos',1,'now')
            self.assertEqual(7,json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])['current_hp'])

    def test_reflexos_metadata_is_separate_from_granted_abilities_and_generic_execution(self):
        from app.dorn_mage import SPEC
        from app.action_library import describe_action
        self.assertFalse(any(a['id']=='reflexos' for a in SPEC['abilities']))
        self.assertIn('reflexos',SPEC['action_contracts'])
        described=describe_action(self.db,'technique:dorn7:reflexos')
        self.assertFalse(described['executable'])
        self.assertEqual('reflexos',described['execute']['payload']['spell_id'])
        self.assertEqual('mirror_images',described['blocks'][0]['effect'])

    def test_reflexos_schema_rejects_unknown_fields_and_malformed_executor(self):
        from app.dorn_mage import SPEC
        from app.action_contract import resolve_contract
        raw=SPEC['action_contracts']['reflexos']
        for location in [(),('resolution',),('range',),('resolution','images')]:
            bad=copy.deepcopy(raw);node=bad
            for part in location:node=node[part]
            node['ignored_rule']='not allowed'
            with self.subTest(location=location),self.assertRaises(ValueError):resolve_contract(bad,3)
        bad=copy.deepcopy(raw);bad['executor']=['dorn_reflexos']
        with self.assertRaises(ValueError):resolve_contract(bad,3)
        for location,value in [(('range','meters'),False),(('costs',0,'amount'),True),
                               (('targeting','include_self'),1),(('schema_version',),1.0)]:
            bad=copy.deepcopy(raw);node=bad
            for part in location[:-1]:node=node[part]
            node[location[-1]]=value
            with self.subTest(location=location),self.assertRaises(ValueError):resolve_contract(bad,3)

    def test_resource_consumer_increments_version_without_committing_callers_transaction(self):
        from app.action_components import spend_native_resource
        with closing(sqlite3.connect(self.db)) as db:
            before=db.execute("SELECT version,state_json FROM character_states WHERE profile_id='dorn7'").fetchone()
            db.execute('BEGIN IMMEDIATE')
            spend_native_resource(db,'dorn7','dorn_reflexos',1,'now')
            self.assertTrue(db.in_transaction)
            self.assertEqual(before[0]+1,db.execute("SELECT version FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
            db.rollback()
            self.assertEqual(before,db.execute("SELECT version,state_json FROM character_states WHERE profile_id='dorn7'").fetchone())

    def test_resource_consumer_rejects_bad_cost_or_missing_transaction(self):
        from app.action_components import spend_native_resource
        with closing(sqlite3.connect(self.db)) as db:
            with self.assertRaises(ValueError):spend_native_resource(db,'dorn7','dorn_reflexos',1,'now')
            db.execute('BEGIN IMMEDIATE')
            for amount in [True,0,-1,1.0,101]:
                with self.subTest(amount=amount),self.assertRaises(ValueError):
                    spend_native_resource(db,'dorn7','dorn_reflexos',amount,'now')
            db.rollback()
