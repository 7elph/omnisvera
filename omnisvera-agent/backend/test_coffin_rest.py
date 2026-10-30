import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from app.character_play import init_character_play, apply_character_action
from app.combat_effects import init_effects


class CoffinRestTests(TestCase):
    def setUp(self):
        folder=TemporaryDirectory();self.addCleanup(folder.cleanup);self.db=Path(folder.name)/'coffin.sqlite3'
        init_character_play(self.db);init_effects(self.db)
        state={'current_hp':5,'maximum_hp':22,'temporary_hp':3,'conditions':['ferido'],'animal_form':'corvo',
            'resources':[{'key':'caixao','current':1,'maximum':1,'recharge':'inn_rest'},
                         {'key':'reserva_de_sangue','current':2,'maximum':10,'recharge':'inn_rest'}]}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('INSERT INTO character_states VALUES(?,?,?,?)',('raziel',json.dumps(state),1,'fixture'))
    def state(self):
        with closing(sqlite3.connect(self.db)) as db:return json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
    def use(self,**changes):
        return apply_character_action(self.db,**{'character_id':'raziel','actor_id':'raziel','actor_role':'player','action':'rest_in_coffin','payload':{},'request_id':'coffin-use',**changes})
    def test_owner_restores_own_sheet_once_and_only_gm_rest_recharges_use(self):
        self.use();s=self.state();self.assertEqual(22,s['current_hp']);self.assertEqual([],s['conditions']);self.assertNotIn('animal_form',s)
        self.assertEqual([0,10],[r['current'] for r in s['resources']])
        with self.assertRaisesRegex(ValueError,'descanso do Mestre'):self.use(request_id='coffin-second')
        apply_character_action(self.db,character_id='raziel',actor_id='master',actor_role='gm',action='rest_at_inn',payload={},request_id='gm-rest')
        self.assertEqual(1,self.state()['resources'][0]['current']);self.use(request_id='coffin-after-rest')
        self.assertEqual(0,self.state()['resources'][0]['current'])
    def test_concurrent_retry_has_one_event_and_does_not_use_recharged_counter(self):
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:self.use(),range(2)))
        self.assertEqual(1,len({r['event_id'] for r in results}))
        apply_character_action(self.db,character_id='raziel',actor_id='master',actor_role='gm',action='rest_at_inn',payload={},request_id='gm-rest')
        self.assertTrue(self.use()['replayed']);self.assertEqual(1,self.state()['resources'][0]['current'])
    def test_cannot_rest_in_combat_even_if_gm_or_skip_turn_is_set(self):
        with closing(sqlite3.connect(self.db)) as db,db:db.execute("UPDATE combat_effect_clock SET encounter_json=? WHERE id=1",(json.dumps({'active':True}),))
        for changes in ({'skip_battle_turn':True},{'actor_id':'master','actor_role':'gm'}):
            with self.assertRaisesRegex(ValueError,'combate'):self.use(**changes)
        self.assertEqual(5,self.state()['current_hp'])
    def test_no_cross_owner_no_other_character_and_no_unkeyed_rest(self):
        with self.assertRaises(PermissionError):self.use(actor_id='morthak')
        with self.assertRaisesRegex(ValueError,'Raziel'):self.use(character_id='vezemir',actor_id='master',actor_role='gm')
        with self.assertRaisesRegex(ValueError,'idempotente'):self.use(request_id=None)
    def test_zero_hp_is_not_revived_by_owner_rest(self):
        s=self.state();s['current_hp']=0
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE character_states SET state_json=?',(json.dumps(s),))
        with self.assertRaisesRegex(ValueError,'PV'):self.use()
