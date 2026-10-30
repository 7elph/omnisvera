import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

import test_spell_engine as fixture


class SpellDotIntegrityTests(unittest.TestCase):
    def setUp(self):
        fixture.SpellEngineTests.setUp(self)
        from app.combat_effects import init_effects
        init_effects(self.db)
        self.participant={'target_type':'character','target_id':'vezemir','name':'Vezemir'}

    def dot(self,kind='character',identity='vezemir'):
        from app.necromancer_spells import add_effect
        with closing(sqlite3.connect(self.db)) as db,db:
            return add_effect(db,{'type':kind,'id':identity},'Toque Sombrio','Morthak','now',dot_hp=True,necro_spell='toque-sombrio')

    def frenzy(self,hp=1):
        from app.vezemir_skills import add_effect
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            state.update(current_hp=hp,resources=[{'key':'frenesi','current':1,'maximum':1}],daily_skill_flags={'frenesi_auto_used':True})
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
            add_effect(db,'character','vezemir','Frenesi','now',skill='frenesi',defy_death=True)

    def tick(self,participant=None,die=1,sequence=7,request_id='tick-first'):
        from app.necromancer_spells import touch_turn
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.necromancer_spells.roll_formula',return_value={'total':die}) as roll:
            skipped=touch_turn(db,participant or self.participant,'now',request_id,encounter={'started_at':'fight','turn_sequence':sequence})
        return skipped,roll.call_count

    def test_hidden_npc_dot_is_not_published_to_player_ledger(self):
        self.dot('token','gob1')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_tokens SET visible_to_players=0 WHERE id='gob1'")
        self.tick({'target_type':'token','target_id':'gob1','name':'Segredo do Mestre'})
        with closing(sqlite3.connect(self.db)) as db:
            row=db.execute("SELECT visibility FROM session_ledger WHERE source_type='touch_dot'").fetchone()
        self.assertEqual(row[0],'gm')

    def test_frenzy_exact_zero_keeps_turn_and_persistent_dot(self):
        self.frenzy();effect=self.dot()
        skipped,calls=self.tick()
        self.assertFalse(skipped);self.assertEqual(calls,1)
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(state['current_hp'],0)
            self.assertEqual(db.execute('SELECT active FROM combat_effects WHERE id=?',(effect['id'],)).fetchone()[0],1)
        skipped,calls=self.tick(sequence=8,request_id='tick-next')
        self.assertFalse(skipped)
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(state['current_hp'],-1)

    def test_frenzy_expires_and_skips_at_negative_ten(self):
        self.frenzy(-9);effect=self.dot()
        skipped,_=self.tick()
        self.assertTrue(skipped)
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(state['current_hp'],-10)
            self.assertEqual(db.execute('SELECT active FROM combat_effects WHERE id=?',(effect['id'],)).fetchone()[0],0)

    def test_failed_d6_is_deduped_and_next_victim_turn_ticks_once(self):
        self.dot()
        self.assertEqual(self.tick(die=5),(False,1))
        self.assertEqual(self.tick(die=1,request_id='different-retry'),(False,0))
        self.assertEqual(self.tick(die=1,sequence=8,request_id='next-turn'),(False,1))
        self.assertEqual(self.tick(die=1,sequence=8,request_id='different-next-retry'),(False,0))
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(state['current_hp'],29)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='touch_dot'").fetchone()[0],2)

    def test_visible_npc_and_character_dots_still_use_table_ledger(self):
        self.dot('token','gob1')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_tokens SET visible_to_players=1 WHERE id='gob1'")
        self.tick({'target_type':'token','target_id':'gob1','name':'Goblin'})
        self.dot();self.tick(request_id='pc-dot')
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual([row[0] for row in db.execute("SELECT visibility FROM session_ledger WHERE source_type='touch_dot'")],['table','table'])
