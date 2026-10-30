"""A hidden old-map skeleton must not strand the player's one-button summon."""
import json
import sqlite3
import unittest
from contextlib import closing
from app.summons import create_summon
from app.combat_effects import readeffects
import test_session6_combat


class SkeletonReplacementTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_session6_combat.Session6CombatTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.db=self.fixture.db
        self.old=self.summon()['token']['id']
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET map_id=?,visible_to_players=0 WHERE id=?',('secret-old-map',self.old))
        self.refill()

    def summon(self,**kwargs):
        return self.fixture.summon(**kwargs)

    def refill(self, amount=1):
        with closing(sqlite3.connect(self.db)) as db, db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            state['resources'][0]['current']=amount
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'",(json.dumps(state),))

    def current(self):
        with closing(sqlite3.connect(self.db)) as db:
            return json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])['resources'][0]['current']

    def test_reuse_reports_replacement_without_leaking_hidden_pin_or_spending(self):
        result=self.summon(request_id='open-hidden-skeleton',reuse_existing=True)
        self.assertTrue(result['needs_replacement']);self.assertEqual(result['existing_token_id'],self.old)
        self.assertNotIn('token',result);self.assertNotIn('secret-old-map',json.dumps(result))
        self.assertEqual(self.current(),1)
        self.assertEqual(result,self.summon(request_id='open-hidden-skeleton',reuse_existing=True))

    def test_replace_is_atomic_and_idempotent_and_retires_only_this_skeleton(self):
        first=self.summon(request_id='replace-hidden-skeleton',replace_token_id=self.old)
        self.assertEqual(first,self.summon(request_id='replace-hidden-skeleton',replace_token_id=self.old))
        self.assertNotEqual(first['token']['id'],self.old);self.assertEqual(self.current(),0)
        with closing(sqlite3.connect(self.db)) as db:
            row=db.execute('SELECT current_hp,sheet_json FROM session_workspace_tokens WHERE id=?',(self.old,)).fetchone()
            self.assertEqual(row[0],0);self.assertTrue(json.loads(row[1])['summon']['dismissed'])
            self.assertEqual(db.execute("SELECT count(*) FROM session_workspace_tokens WHERE current_hp>0 AND json_extract(sheet_json,'$.summon.technique')='levantar-esqueleto'").fetchone()[0],1)
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='summon' AND source_id='replace-hidden-skeleton'").fetchone()[0],1)

    def test_no_daily_use_leaves_old_skeleton_alive(self):
        self.refill(0)
        with self.assertRaisesRegex(ValueError,'Sem usos'):
            self.summon(request_id='replacement-without-uses',replace_token_id=self.old)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(self.old,)).fetchone()[0],5)

    def test_other_player_cannot_discover_or_replace_morthaks_hidden_skeleton(self):
        for options in ({'reuse_existing':True},{'replace_token_id':self.old}):
            with self.assertRaises(PermissionError):
                self.summon(request_id='foreign-skeleton-command',actor_id='raziel',**options)

    def test_replacement_during_combat_uses_native_turn_and_removes_old_participant(self):
        self.fixture.start_morthak()
        encounter=readeffects(self.db)['encounter']
        encounter['participants'].insert(1,{'target_type':'token','target_id':self.old,'name':'Velho','initiative':20,'controller_id':'morthak'})
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        first=self.summon(request_id='replace-on-native-turn',replace_token_id=self.old)
        encounter=readeffects(self.db)['encounter']
        self.assertTrue(encounter['action_committed'])
        self.assertNotIn(self.old,[p['target_id'] for p in encounter['participants']])
        self.assertEqual(first['token']['id'],encounter['participants'][1]['target_id'])
