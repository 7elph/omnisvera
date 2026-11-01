"""Read-only deterministic proposals, then the existing authorized executor."""
import hashlib
import json
import sqlite3
import unittest
from contextlib import closing

import test_item_families
from app import main
from app.access import AccessContext
from app.combat_effects import effect_command, readeffects
from app.session_workspace import save_workspace_token, set_workspace_map, update_workspace_table_mode
from app.spatial_grid import configure_grid


class MonsterProposalTests(unittest.TestCase):
    tearDown=test_item_families.ItemFamilyApiTests.tearDown

    def setUp(self):
        test_item_families.ItemFamilyApiTests.setUp(self)
        self.client.get('/characters/vezemir').raise_for_status()
        self.map_id=set_workspace_map(self.db,title='Synthetic planner',image_path='fixture.svg',visible_to_players=True)['id']
        self.actor=save_workspace_token(self.db,map_id=self.map_id,token_type='monster',name='Synthetic fighter',latitude=40,longitude=40,current_hp=10,maximum_hp=10,
            sheet={'armor_class':10,'attacks':[{'name':'Clava','damage':'1d6','bonus':2}]})
        self.target=save_workspace_token(self.db,map_id=self.map_id,token_type='character',name='Synthetic target',character_id='vezemir',latitude=40,longitude=50)
        configure_grid(self.db,actor_id='master',role='gm',request_id='planner-grid',map_id=self.map_id,config={'cols':10,'rows':10,'cell_size_m':1.5})
        effect_command(self.db,actor_id='master',actor_role='gm',request_id='planner-start',expected_version=readeffects(self.db)['version'],action='start',
            payload={'map_id':self.map_id,'battle_mode':True,'participants':[{'target_type':'token','target_id':self.actor['id'],'initiative':20},
                {'target_type':'character','target_id':'vezemir','initiative':10}]})
        with closing(sqlite3.connect(self.db)) as db, db:
            for pin,x in [(self.actor['id'],4),(self.target['id'],5)]:
                db.execute('UPDATE session_workspace_entity_positions SET cell_x=?,cell_y=4 WHERE token_id=?',(x,pin))
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]);state.update(current_hp=20,maximum_hp=20)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))

    def propose(self,access=None,targets=None):
        from app.monster_proposals import propose_actions
        return propose_actions(self.db,access or AccessContext(mode='gm'),token_id=self.actor['id'],target_token_ids=targets or [self.target['id']])

    def test_deterministic_read_only_and_no_credentials_in_result(self):
        before=hashlib.sha256(self.db.read_bytes()).hexdigest()
        first=self.propose();self.assertEqual(self.propose(),first)
        self.assertEqual(first['proposals'][0]['request']['attack_id'],'0')
        self.assertEqual(first['proposals'][0]['request']['target_id'],'vezemir')
        self.assertTrue(first['confirmation_required'])
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(),before)
        self.assertNotIn('fixture-master',json.dumps(first))

    def test_player_cannot_read_gm_proposals(self):
        with self.assertRaises(PermissionError):self.propose(AccessContext(mode='player',profile_id='vezemir'))
        response=self.client.get('/gm/combat/tokens/'+self.actor['id']+'/action-proposals',params={'target_token_ids':self.target['id']})
        self.assertIn(response.status_code,(401,403))

    def test_unknown_or_out_of_range_attacks_are_blocked(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            sheet=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(self.actor['id'],)).fetchone()[0])
            sheet['attacks']=[{'name':'Arma','damage':'Especial','bonus':2},{'name':'Clava','damage':'1d6 + efeito desconhecido','bonus':2},
                {'name':'Arco','slot':'ranged','damage':'1d6','bonus':2}]
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(sheet),self.actor['id']))
        self.assertEqual(self.propose()['proposals'],[])
        with closing(sqlite3.connect(self.db)) as db, db:
            sheet['attacks']=[{'name':'Clava','damage':'1d6','bonus':2}]
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(sheet),self.actor['id']))
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=9 WHERE token_id=?',(self.target['id'],))
        self.assertEqual(self.propose()['proposals'],[])

    def test_budget_dead_and_missing_grid_produce_no_executable_proposal(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            encounter=json.loads(db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()[0])
            encounter['action_committed']=True
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        self.assertEqual(self.propose()['proposals'],[])
        with closing(sqlite3.connect(self.db)) as db, db:
            encounter['action_committed']=False
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
            db.execute('UPDATE session_workspace_tokens SET current_hp=0 WHERE id=?',(self.actor['id'],))
        self.assertEqual(self.propose()['proposals'],[])
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=10 WHERE id=?',(self.actor['id'],))
            db.execute('DELETE FROM session_workspace_map_grids WHERE map_id=?',(self.map_id,))
        self.assertEqual(self.propose()['proposals'],[])

    def test_other_turn_and_dead_target_are_never_proposed(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]);state['current_hp']=0
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
        self.assertEqual(self.propose()['proposals'],[])
        with closing(sqlite3.connect(self.db)) as db, db:
            encounter=json.loads(db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()[0]);encounter['turn_index']=1
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        self.assertEqual(self.propose()['proposals'],[])

    def test_invalid_candidate_list_is_rejected_before_reading_the_database(self):
        from app.monster_proposals import propose_actions
        absent=self.db.with_name('planner-must-not-create.sqlite3')
        for candidates in [[],['x']*21,[True],['x'*181],'x']:
            with self.subTest(candidates=candidates),self.assertRaises(ValueError):
                propose_actions(absent,AccessContext(mode='gm'),token_id=self.actor['id'],target_token_ids=candidates)
        self.assertFalse(absent.exists())

    def test_approved_proposal_uses_native_attack_and_confirmation(self):
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='gm')
        url='/gm/combat/tokens/'+self.actor['id']+'/action-proposals'
        response=self.client.get(url,params={'target_token_ids':self.target['id']},headers={'X-Omnisvera-Token':'fixture-master'})
        self.assertEqual(response.status_code,200,response.text)
        proposal=response.json()['proposals'][0]
        update_workspace_table_mode(self.db,'physical')
        body={**proposal['request'],'request_id':'planner-confirmed-native','roll_mode':'physical','d20':20}
        attack=self.client.post(proposal['resolve_endpoint'],json=body)
        self.assertEqual(attack.status_code,200,attack.text)
        confirmed=self.client.post('/combat/attacks/'+attack.json()['resolution_id']+'/confirm')
        self.assertEqual(confirmed.status_code,200,confirmed.text)
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
        self.assertLess(state['current_hp'],20)


if __name__=='__main__':unittest.main()
