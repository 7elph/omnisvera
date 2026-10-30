import json
from contextlib import closing
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from app.character_play import init_character_play, _connect, update_definition_overrides, load_definition_overrides
from app.dice_rolls import list_roll_requests, complete_roll_request

class LevelRecalculationTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'test.db'; init_character_play(self.db)
        self.definition = {'id':'test-mage','name':'Mago fixture','class_name':'Mago','level':2,
            'base_attributes':{'constitution':16,'intelligence':16}, 'defenses':{'saving_throw':14},
            'progression':{'base_attack':0,'base_maximum_hp':13}}
        with closing(_connect(self.db)) as db, db:
            db.execute('INSERT INTO character_states VALUES(?,?,?,?)', ('test-mage',json.dumps({'maximum_hp':13,'current_hp':5,'resources':[{'key':'magias_de_1o_circulo','current':1,'maximum':3,'recharge':'inn_rest'}]}),1,'test'))
    def edit(self, level):
        return update_definition_overrides(self.db,character_id='test-mage',actor_id='master',fields={'level':level},definition=self.definition)
    def state(self):
        with closing(_connect(self.db)) as db:
            return json.loads(db.execute('SELECT state_json FROM character_states').fetchone()[0])
    def test_generic_mage_recalculates_and_notifies_owner_without_rolling(self):
        with patch('app.dice_rolls.roll_formula', side_effect=AssertionError('must not roll')):
            result = self.edit(3)
        self.assertEqual((1,14),(result['advancement_base_attack'],result['advancement_saving_throw']))
        self.assertEqual(13,self.state()['maximum_hp'])
        self.assertEqual(1,result['advancement_resources']['magias_de_2o_circulo'])
        self.assertEqual(1,self.state()['resources'][0]['current'])
        request = list_roll_requests(self.db)[0]
        self.assertEqual(('test-mage','owner','1d4'),(request['character_id'],request['visibility'],request['formula']))
    def test_manual_hp_acknowledgement_removes_only_one_pending_die_without_hp_change(self):
        from app.level_recalculation import acknowledge_manual_hp
        self.edit(5);before=self.state()
        with closing(_connect(self.db)) as db,db:
            result=acknowledge_manual_hp(db,'test-mage',3,actor_id='master',actor_role='gm',reason='PV já incluídos manualmente')
            replay=acknowledge_manual_hp(db,'test-mage',3,actor_id='master',actor_role='gm',reason='PV já incluídos manualmente')
        self.assertTrue(result['applied']);self.assertFalse(replay['applied'])
        self.assertEqual(before,self.state())
        self.assertEqual([4,5],[p['level'] for p in load_definition_overrides(self.db,'test-mage')['pending_progression']])
    def test_owner_cannot_acknowledge_manual_hp(self):
        from app.level_recalculation import acknowledge_manual_hp
        self.edit(3)
        with closing(_connect(self.db)) as db,db:
            with self.assertRaises(PermissionError):acknowledge_manual_hp(db,'test-mage',3,actor_id='test-mage',actor_role='player',reason='Não autorizado')

    def test_roll_is_owned_persisted_and_retry_does_not_duplicate_or_heal(self):
        self.edit(3); request=list_roll_requests(self.db)[0]
        with self.assertRaises(PermissionError):
            complete_roll_request(self.db,request_id=request['id'],completion_request_id='other-000',actor_id='other',actor_role='player')
        event,_=complete_roll_request(self.db,request_id=request['id'],completion_request_id='own-00000',actor_id='test-mage',actor_role='player',rng=lambda a,b:2)
        complete_roll_request(self.db,request_id=request['id'],completion_request_id='own-00000',actor_id='test-mage',actor_role='player')
        self.assertEqual((18,5),(self.state()['maximum_hp'],self.state()['current_hp']))
        overrides=load_definition_overrides(self.db,'test-mage')
        self.assertEqual([],overrides['pending_progression'])
        self.assertEqual(event['id'],overrides['level_hp_history'][0]['roll_event_id'])
    def test_reduce_and_restore_reuses_legitimate_roll(self):
        self.edit(3); req=list_roll_requests(self.db)[0]
        complete_roll_request(self.db,request_id=req['id'],completion_request_id='own-00000',actor_id='test-mage',actor_role='player',rng=lambda a,b:2)
        self.definition.update(level=3); self.definition['progression'].update(base_attack=1,base_maximum_hp=18)
        self.edit(2); self.assertEqual(13,self.state()['maximum_hp'])
        self.definition.update(level=2); self.definition['progression'].update(base_attack=0,base_maximum_hp=13)
        self.edit(3); self.assertEqual(18,self.state()['maximum_hp']); self.assertEqual([],list_roll_requests(self.db))
    def test_missing_history_blocks_reduction_and_unknown_rules_leave_no_partial_write(self):
        with self.assertRaisesRegex(ValueError,'Histórico'):
            self.edit(1)
        with self.assertRaisesRegex(ValueError,'tabela'):
            self.edit(16)
        self.assertEqual({},load_definition_overrides(self.db,'test-mage'))
    def test_warrior_same_mechanism_and_repeat_edit_has_no_second_request(self):
        self.definition.update(class_name='Guerreiro',level=1)
        self.definition['progression']['base_attack']=1; self.definition['defenses']['saving_throw']=16
        self.edit(2)
        self.definition.update(level=2); self.definition['progression']['base_attack']=2
        self.edit(2)
        self.assertEqual('1d10',list_roll_requests(self.db)[0]['formula'])
        self.assertEqual(1,len(list_roll_requests(self.db)))
    def test_failed_audit_rolls_back_definition_state_and_pending(self):
        with patch('app.character_play._write_event',side_effect=RuntimeError('disk')):
            with self.assertRaises(RuntimeError): self.edit(3)
        self.assertEqual([],list_roll_requests(self.db)); self.assertEqual(13,self.state()['maximum_hp'])
    def test_lost_hp_application_recovers_same_roll_without_new_dice(self):
        self.edit(3);request=list_roll_requests(self.db)[0]
        args=dict(request_id=request['id'],completion_request_id='recovery-0000',actor_id='test-mage',actor_role='player')
        with patch('app.character_play._write_event',side_effect=RuntimeError('disk')):
            with self.assertRaises(RuntimeError):complete_roll_request(self.db,**args,rng=lambda a,b:2)
        self.assertEqual(13,self.state()['maximum_hp'])
        with patch('app.dice_rolls.roll_formula',side_effect=AssertionError('no reroll')):
            complete_roll_request(self.db,**args)
        self.assertEqual((18,5),(self.state()['maximum_hp'],self.state()['current_hp']))
    def test_reconciliation_of_displayed_level_with_proven_unchanged_hp(self):
        self.definition['level']=3
        self.definition['progression'].update(sheet_level=1,sheet_base_attack=0,sheet_saving_throw=14,sheet_maximum_hp=13)
        result=self.edit(3)
        self.assertEqual(1,result['advancement_base_attack'])
        self.assertEqual([2,3],[p['level'] for p in result['pending_progression']])
        self.assertEqual(13,self.state()['maximum_hp'])
    def test_custom_class_contract_resources_and_unlocks_are_not_character_hardcoded(self):
        self.definition['class_name']='Classe aprovada fixture'
        with closing(_connect(self.db)) as db,db:
            db.execute('INSERT INTO character_definition_overrides VALUES(?,?,?)',('test-mage',json.dumps({'progression_contract':{
                'die':6,'source':'fixture approved','levels':{'2':[0,14],'3':[2,13]},
                'resource_maxima':{'3':{'custom':2}},'abilities':{'3':[{'id':'fixture-ability','name':'Habilidade fixture'}]}}}),'test'))
        result=self.edit(3)
        self.assertEqual(2,result['advancement_base_attack'])
        self.assertEqual('fixture-ability',result['level_abilities'][0]['id'])
        self.assertEqual(2,result['advancement_resources']['custom'])
    def test_aligned_base_advances_by_pure_table_movement(self):
        # S8: with an aligned base, 3->5 grants table values with no offsets.
        self.definition.update(level=3)
        self.definition["progression"].update(base_attack=1, base_maximum_hp=10)
        with closing(_connect(self.db)) as db, db:
            db.execute("UPDATE character_states SET state_json=?",
                       (json.dumps({"maximum_hp": 10, "current_hp": 10, "resources": [
                           {"key": "magias_de_1o_circulo", "current": 3, "maximum": 3, "recharge": "inn_rest"},
                           {"key": "magias_de_2o_circulo", "current": 2, "maximum": 2, "recharge": "inn_rest"}]}),))
        result = self.edit(5)
        self.assertEqual(2, result["advancement_base_attack"])
        self.assertEqual(1, result["advancement_attack_delta"])
        self.assertEqual(3, result["advancement_resources"]["magias_de_1o_circulo"])
        self.assertEqual(1, result["advancement_resources"]["magias_de_3o_circulo"])
        self.assertEqual([4, 5], sorted(p["level"] for p in result["pending_progression"]))

    def test_stale_sheet_plus_delta_converges_and_stays_clean(self):
        # S8 Vezemir shape: sheet base 4 + delta 1 = table 5. Next step must
        # stay on table with no new offset.
        self.definition.update(class_name="Guerreiro", level=5)
        self.definition["progression"].update(base_attack=5, base_maximum_hp=27)
        with closing(_connect(self.db)) as db, db:
            db.execute("UPDATE character_states SET state_json=?",
                       (json.dumps({"maximum_hp": 27, "current_hp": 27, "resources": []}),))
            db.execute("INSERT INTO character_definition_overrides VALUES(?,?,?)",
                       ("test-mage", json.dumps({"level": 5, "maximum_hp": 27, "advancement_base_attack": 5,
                                                 "advancement_attack_delta": 1,
                                                 "advancement_history": []}), "test"))
        result = self.edit(6)
        self.assertEqual(6, result["advancement_base_attack"])
        self.assertEqual(2, result["advancement_attack_delta"])
        # Effective attacks follow table: stale sheet 4 + delta 2 = 6.
        self.assertEqual(6, 4 + result["advancement_attack_delta"])

    def test_master_owned_character_pending_is_not_visible_to_players(self):
        self.definition.update(id='dorn7')
        with closing(_connect(self.db)) as db,db:
            db.execute("UPDATE character_states SET profile_id='dorn7'")
            db.execute('INSERT INTO character_definition_overrides VALUES(?,?,?)',('dorn7',json.dumps({'prepared_magic_override':True,'level_hp_anchor':{'level':2,'maximum_hp':13}}),'test'))
        result=update_definition_overrides(self.db,character_id='dorn7',actor_id='master',fields={'level':3},definition=self.definition)
        req=list_roll_requests(self.db)[0]
        self.assertEqual(('gm','master'),(req['visibility'],result['pending_progression'][0]['controller']))
        with self.assertRaises(PermissionError):complete_roll_request(self.db,request_id=req['id'],completion_request_id='wrong-player',actor_id='dorn7',actor_role='player')
