"""Approved combo/boost rules on native disposable combat fixtures."""
import json,sqlite3,unittest
from contextlib import closing
import test_hemomancy_weapons as fixture
from unittest.mock import patch

class RazielPipelineTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.HemomancyWeaponsTests();self.f.setUp();self.addCleanup(self.f.tearDown)
        self.f.durable_target()
    def test_spear_accumulates_one_die_per_distinct_condition(self):
        from app.hemomancy import _put
        with closing(sqlite3.connect(self.f.db)) as db,db:
            _put(db,'exposed','Exposto','now',target_type='token',target_id=self.f.wounded['id'],map_id='default')
            _put(db,'bleed','Sangramento','now',target_type='token',target_id=self.f.wounded['id'],map_id='default',remaining_turns=2)
        result=self.f.attack('lanca','skill')
        self.assertEqual(200,result.status_code,result.text)
        self.assertEqual(2,result.json()['breakdown']['hemomancy']['passive_d6'])
    def test_boost_cost_duration_and_retry_use_native_command(self):
        body={'request_id':'pipeline-boost-idempotent','mode':'x2'}
        first=self.f.use('raziel','reforco',body)
        self.assertEqual(200,first.status_code,first.text)
        self.assertEqual(first.json(),self.f.use('raziel','reforco',body).json())
        self.assertEqual(3,self.f.laminas())
        effect=next(e for e in first.json()['effects'] if e.get('hemomancy_kind')=='boost')
        self.assertEqual((2,2),(effect['multiplier'],effect['turns_remaining']))
    def test_mark_is_ranged_cross_and_accepts_healthy_blood_targets(self):
        with closing(sqlite3.connect(self.f.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=maximum_hp WHERE id=?',(self.f.wounded['id'],))
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=10 WHERE token_id=?',(self.f.wounded['id'],))
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=10,cell_y=6 WHERE token_id=?',(self.f.healthy['id'],))
        reply=self.f.use('raziel','marca-rubra',{'request_id':'mark-cross-ranged-healthy','target_type':'token','target_id':self.f.wounded['id']})
        self.assertEqual(200,reply.status_code,reply.text)
        effects=self.f.effects('mark')
        self.assertEqual({self.f.wounded['id'],self.f.healthy['id']},{e['target_id'] for e in effects})
        self.assertEqual(4,self.f.laminas())
    def test_speed_is_available_to_raziel_and_does_not_grant_extra_blood(self):
        reply=self.f.use('raziel','velocidade',{'request_id':'raziel-speed-native'})
        self.assertEqual(200,reply.status_code,reply.text)
        self.assertEqual(5,self.f.laminas())
        effect=next(e for e in reply.json()['effects'] if e.get('skill')=='raziel_speed')
        self.assertEqual(1,effect['modifiers']['extra_attacks'])

    def test_boost_expires_after_two_owner_turns_and_cancel_never_refunds(self):
        self.f.start_combat()
        reply=self.f.use('raziel','reforco',{'request_id':'two-turn-boost','mode':'x2'})
        self.assertEqual(200,reply.status_code,reply.text)
        for turn in range(4):
            self.f.command('next_turn',f'boost-turn-{turn}')
            if turn==1:self.assertEqual(1,self.f.effects('boost')[0]['turns_remaining'])
        self.assertEqual([],self.f.effects('boost'))
        self.f.use('raziel','reforco',{'request_id':'boost-to-cancel','mode':'x2'})
        before=self.f.laminas()
        cancel=self.f.use('raziel','reforco',{'request_id':'cancel-boost','mode':'x1'})
        self.assertEqual(200,cancel.status_code,cancel.text)
        self.assertEqual(before,self.f.laminas());self.assertEqual([],self.f.effects('boost'))

    def test_both_blocks_unlock_one_conditional_and_retries_never_duplicate_it(self):
        with closing(sqlite3.connect(self.f.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            state['resources'][0].update(current=10,maximum=10)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",(json.dumps(state),))
        mark=self.f.use('raziel','marca-rubra',{'request_id':'combo-cross-mark','target_type':'token','target_id':self.f.wounded['id']})
        self.assertEqual(200,mark.status_code,mark.text)
        with patch('app.combat.roll_formula',return_value={'total':1,'individual_results':[1],'modifier':0}):
            bow=self.f.attack('arco','skill',request='combo-bow');self.assertEqual(200,self.f.confirm(bow).status_code)
            shield=self.f.use('raziel','hemomancia-escudo',{'request_id':'combo-shield'});self.assertEqual(200,shield.status_code,shield.text)
            for weapon in ('marreta','foice','lanca'):
                result=self.f.attack(weapon,'skill',request='combo-'+weapon)
                self.assertEqual(200,result.status_code,result.text)
                confirmed=self.f.confirm(result);self.assertEqual(200,confirmed.status_code,confirmed.text)
        self.assertEqual(1,len(self.f.effects('convergence')))
        self.assertEqual(confirmed.json(),self.f.confirm(result).json())
        self.assertEqual(1,len(self.f.effects('convergence')))

    def test_boost_multiplies_bonus_and_final_damage_without_multiplying_the_d20(self):
        self.f.use('raziel','reforco',{'request_id':'boost-damage-math','mode':'x2'})
        result=self.f.attack('arco',request='boosted-bow',die=15)
        self.assertEqual(200,result.status_code,result.text)
        data=result.json();strike=data['breakdown']['strikes'][0]
        self.assertEqual(15,data['d20']);self.assertGreaterEqual(data['attack_bonus'],12)
        self.assertEqual(2*strike['unmultiplied_damage'],strike['damage_total'])

if __name__=='__main__':unittest.main()
