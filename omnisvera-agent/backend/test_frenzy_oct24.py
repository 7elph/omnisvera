import json,sqlite3,unittest
from unittest.mock import patch
from app import vezemir_skills as skills

class FrenzyConditionalTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:');self.addCleanup(self.db.close)
        self.db.executescript('''CREATE TABLE combat_effects(id TEXT,target_type TEXT,target_id TEXT,data_json TEXT,active INTEGER);
          CREATE TABLE combat_effect_clock(id INTEGER,version INTEGER);
          INSERT INTO combat_effect_clock VALUES(1,1);
          CREATE TABLE session_workspace_tokens(id TEXT,character_id TEXT,sheet_json TEXT,current_hp INTEGER,updated_at TEXT);
          INSERT INTO session_workspace_tokens VALUES('vez','vezemir','{}',10,'now');
          CREATE TABLE character_states(profile_id TEXT,state_json TEXT,version INTEGER,updated_at TEXT);''')
        self.state={'current_hp':10,'maximum_hp':20,'resources':[{'key':'frenesi','current':1,'maximum':1}]}
    def test_lifeline_is_consumed_only_when_zero_is_reached_and_records_minus_ten(self):
        with patch.object(skills,'roll_formula',return_value={'total':3}):skills.start_frenzy(self.db,self.state,'now')
        self.assertFalse(self.state['daily_skill_flags'].get('frenesi_lifeline_used'))
        self.assertEqual(0,skills.hp_result(self.db,self.state,0,5,20,'now'))
        self.assertTrue(self.state['daily_skill_flags']['frenesi_lifeline_used'])
        self.assertTrue(skills.survives(self.db,'vezemir',0));self.assertTrue(skills.survives(self.db,'vezemir',-9))
        self.assertEqual(-10,skills.hp_result(self.db,self.state,-14,-9,20,'now'))
        self.assertFalse(skills.survives(self.db,'vezemir',-10))
    def test_failed_provocation_has_a_guaranteed_turn_and_next_save_penalty(self):
        effect=skills.add_effect(self.db,'token','enemy','Provocação','now',skill='provocacao',failed=True,guaranteed_turns=1)
        participant={'target_type':'token','target_id':'enemy','name':'Inimigo'}
        victim={'defenses':{'saving_throw':13,'saving_throw_bonus':0}}
        with patch('app.dorn_spells.target',return_value=victim),patch.object(skills,'roll_formula',return_value={'total':14}) as roll,patch.object(skills,'append_session_ledger_event'):
            skills.target_turn(self.db,participant,'now','forced-turn');roll.assert_not_called()
            skills.target_turn(self.db,participant,'now','next-save')
        saved=json.loads(self.db.execute('SELECT data_json FROM combat_effects WHERE id=?',(effect['id'],)).fetchone()[0])
        self.assertTrue(saved['failed'])

if __name__=='__main__':unittest.main()
