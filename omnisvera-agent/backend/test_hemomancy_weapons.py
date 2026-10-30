"""Five approved weapons use native previews, confirmations and turn effects."""
import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch

from app import main
from app.session_workspace import save_workspace_token
from test_hemomante_techniques import TechniqueFixture


class HemomancyMetadataTests(TestCase):
    def test_exact_five_weapons_and_no_animal_forms(self):
        from app.hemomancy import weapons
        entries = weapons()
        self.assertEqual(['arco','foice','marreta','escudo','lanca'], [w['weapon'] for w in entries])
        self.assertEqual(5, len({w['skill']['id'] for w in entries}))
        self.assertEqual(5, len({w['passive']['id'] for w in entries}))

    def test_bow_critical_doubles_only_base_dice_not_bonuses(self):
        from app.hemomancy import roll_passives
        attack={'hemomancy':{'weapon':'arco','passive_d6':1,'bonus':2}}
        strike={'result':'hit','d20':19,'damage_total':5,'damage_rolls':[5]}
        with patch('app.hemomancy.roll_formula',side_effect=[{'total':3,'individual_results':[3]}, {'total':4,'individual_results':[4]}]) as roll:
            roll_passives(attack,strike,None)
        self.assertEqual(['1d8','1d6'],[c.args[0] for c in roll.call_args_list])
        self.assertEqual(14,strike['damage_total'])
        self.assertTrue(strike['critical'])

    def test_natural_nineteen_that_misses_does_not_roll_critical(self):
        from app.hemomancy import roll_passives
        with patch('app.hemomancy.roll_formula') as roll:
            roll_passives({'hemomancy':{'weapon':'arco'}},{'result':'miss','d20':19},None)
        roll.assert_not_called()

    def test_revenge_requires_a_miss_prevented_by_exactly_the_shield_bonus(self):
        from app.hemomancy import incoming_shield
        snapshot={'effects':[{'id':'shield-fixture','hemomancy_kind':'shield'}]}
        target={'type':'character','id':'raziel','armor_class':14}
        for result,die,total,expected in [
            ('miss',11,11,None), ('miss',12,12,'shield-fixture'),
            ('miss',13,13,'shield-fixture'), ('hit',14,14,None),
            ('miss',1,13,None), ('hit',20,20,None),
        ]:
            with self.subTest(result=result,die=die,total=total):
                self.assertEqual(expected,incoming_shield(snapshot,target,[
                    {'result':result,'d20':die,'attack_total':total}]))
        self.assertIsNone(incoming_shield(snapshot,{**target,'id':'morthak'},[
            {'result':'miss','d20':12,'attack_total':12}]))


class HemomancyGridFixture(TechniqueFixture):
    def setUp(self):
        super().setUp()
        from app.spatial_grid import init_spatial
        init_spatial(self.db)
        self.pin = save_workspace_token(self.db, token_type='character',character_id='raziel',
            name='Raziel',latitude=10,longitude=10,current_hp=10,maximum_hp=16,visible_to_players=True)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT OR IGNORE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('default','Arena','fixture.png',1,'now','now')")
            db.execute("INSERT OR IGNORE INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES(1,'default','Arena','fixture.png','now')")
            db.execute("INSERT INTO session_workspace_map_grids VALUES('default','square',20,20,1.5,0,0,'chebyshev',1,1)")
            for identity,x in [(self.pin['id'],5),(self.wounded['id'],6),(self.healthy['id'],7)]:
                db.execute("INSERT OR REPLACE INTO session_workspace_entity_positions VALUES('default',?,?,5,1,1,1)",(identity,x))

    def attack(self, weapon='arco', mode='basic', request='hemomancy-native-01', die=15):
        return self.use('raziel','hemomancia-'+weapon,dict(request_id=request,mode=mode,
            target_type='token',target_id=self.wounded['id'],roll_mode='physical',d20=die))

    def confirm(self, reply):
        self.assertEqual(200,reply.status_code,reply.text)
        return self.client.post('/combat/attacks/'+reply.json()['resolution_id']+'/confirm',json={})

    def effects(self,kind):
        from app.combat_effects import readeffects
        return [e for e in readeffects(self.db)['effects'] if e.get('hemomancy_kind')==kind]

    def durable_target(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=100,maximum_hp=100 WHERE id=?',(self.wounded['id'],))

    def command(self,action,request,**payload):
        from app.combat_effects import readeffects,effect_command
        return effect_command(self.db,actor_id='master',actor_role='gm',request_id=request,
            expected_version=readeffects(self.db)['version'],action=action,payload=payload)

    def start_combat(self):
        self.command('start','hemomancy-start',map_id='default',battle_mode=True,participants=[
            {'target_type':'character','target_id':'raziel','initiative':20,'name':'Raziel'},
            {'target_type':'token','target_id':self.wounded['id'],'initiative':1,'name':'Lobo'}])

class HemomancyWeaponsTests(HemomancyGridFixture):
    def test_preview_does_not_spend_and_confirm_retry_spends_once(self):
        reply=self.attack()
        self.assertEqual(200,reply.status_code,reply.text)
        self.assertEqual(5,self.laminas())
        first=self.confirm(reply);self.assertEqual(200,first.status_code,first.text)
        self.assertEqual(4,self.laminas())
        self.assertEqual(first.json(),self.confirm(reply).json())
        self.assertEqual(4,self.laminas())

    def test_miss_still_invokes_and_charges_once(self):
        reply=self.attack(weapon='marreta',die=2)
        confirmed=self.confirm(reply);self.assertEqual(200,confirmed.status_code,confirmed.text)
        self.assertEqual('miss',confirmed.json()['result'])
        self.assertEqual(4,self.laminas())

    def test_endpoint_rejects_wrong_owner(self):
        reply=self.use('morthak','hemomancia-arco',{'request_id':'hemomancy-owner-01'})
        self.assertIn(reply.status_code,(403,404))

    def test_sheet_http_projection_exposes_pack_only_to_authorized_view(self):
        from app.access import AccessContext
        reply=self.client.get('/characters/raziel')
        self.assertEqual(200,reply.status_code,reply.text)
        self.assertEqual(5,len(reply.json()['definition']['hemomancy']['weapons']))
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='player',profile_id='morthak')
        public=self.client.get('/characters/raziel')
        self.assertEqual(200,public.status_code,public.text)
        self.assertNotIn('hemomancy',public.json()['definition'])

    def test_out_of_range_rejects_without_spending_or_receipt(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=18 WHERE token_id=?',(self.wounded['id'],))
        reply=self.attack('lanca')
        self.assertEqual(400,reply.status_code,reply.text)
        self.assertEqual(5,self.laminas())
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(0,db.execute('SELECT COUNT(*) FROM combat_attack_resolutions').fetchone()[0])

    def test_held_basic_is_free_and_switch_replaces_one_weapon(self):
        for weapon,request,expected in [('arco','held-bow-001',4),('arco','held-bow-002',4),('lanca','held-spear-01',3)]:
            result=self.confirm(self.attack(weapon,request=request,die=2))
            self.assertEqual(200,result.status_code,result.text)
            self.assertEqual(expected,self.laminas())
            self.assertEqual([weapon],[e['weapon'] for e in self.effects('weapon')])

    def test_skill_cost_is_additional_and_failed_confirmation_rolls_back(self):
        reply=self.attack('foice','skill',request='scythe-cost-01')
        self.assertEqual(200,reply.status_code,reply.text)
        self.assertEqual(5,self.laminas())
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=5 WHERE id=?',(self.wounded['id'],))
        rejected=self.confirm(reply)
        self.assertIn(rejected.status_code,(400,409),rejected.text)
        self.assertEqual(5,self.laminas());self.assertFalse(self.effects('weapon'))

    def test_retry_survives_form_change_without_new_roll_or_charge(self):
        reply=self.attack(die=1);confirmed=self.confirm(reply)
        self.assertEqual(200,confirmed.status_code,confirmed.text)
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0]);state['animal_form']='corvo'
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",(json.dumps(state),))
        self.assertEqual(confirmed.json(),self.attack(die=1).json())
        self.assertEqual(4,self.laminas())
        self.assertEqual(400,self.attack(die=2).status_code)

    def test_mace_exposes_spear_consumes_and_stacks_two_distinct_conditions(self):
        self.durable_target()
        first=self.confirm(self.attack('marreta',request='mace-expose-01'))
        self.assertEqual(200,first.status_code,first.text);self.assertEqual(1,len(self.effects('exposed')))
        from app.hemomancy import _put
        with closing(sqlite3.connect(self.db)) as db,db:
            _put(db,'bleed','Sangramento de ensaio','now',target_type='token',target_id=self.wounded['id'],map_id='default',remaining_turns=2)
        reply=self.attack('lanca',request='spear-expose-01')
        self.assertEqual(200,reply.status_code,reply.text)
        self.assertEqual(2,reply.json()['breakdown']['hemomancy']['passive_d6'])
        self.assertEqual(2,reply.json()['breakdown']['hemomancy']['bonus'])
        self.assertEqual(2,reply.json()['damage_modifier'])
        self.assertEqual(sum(reply.json()['damage_rolls'])+2,reply.json()['damage_total'])
        self.assertEqual(200,self.confirm(reply).status_code);self.assertFalse(self.effects('exposed'))

    def test_estocada_adds_one_d4_only_to_the_skill_hit(self):
        self.durable_target()
        basic=self.attack('lanca',request='spear-basic-formula')
        self.assertEqual(200,basic.status_code,basic.text)
        self.assertEqual('1d8',basic.json()['damage_formula'])
        with patch('app.hemomancy.roll_formula',return_value={'total':3,'individual_results':[3]}) as roll:
            skill=self.attack('lanca','skill',request='spear-skill-formula')
        self.assertEqual(200,skill.status_code,skill.text)
        self.assertEqual(['1d4'],[call.args[0] for call in roll.call_args_list])
        result=skill.json()
        self.assertEqual('1d8+1d4',result['damage_formula'])
        self.assertEqual(sum(result['damage_rolls'])+result['damage_modifier'],result['damage_total'])
        self.assertEqual('Estocada Transfixante',result['breakdown']['strikes'][0]['hemomancy_rolls'][0]['label'])

    def test_estocada_and_arterial_keep_separate_bonus_dice(self):
        self.durable_target()
        from app.hemomancy import _put
        with closing(sqlite3.connect(self.db)) as db,db:
            _put(db,'exposed','Exposto','now',target_type='token',target_id=self.wounded['id'],map_id='default')
            _put(db,'bleed','Sangramento','now',target_type='token',target_id=self.wounded['id'],map_id='default',remaining_turns=2)
        with patch('app.hemomancy.roll_formula',side_effect=[{'total':3,'individual_results':[3]},{'total':4,'individual_results':[4]}]) as roll:
            reply=self.attack('lanca','skill',request='spear-skill-combo',die=20)
        self.assertEqual(200,reply.status_code,reply.text)
        self.assertEqual(['1d4','2d6'],[call.args[0] for call in roll.call_args_list])
        result=reply.json()
        self.assertEqual('1d8+1d8+1d4+2d6+2',result['damage_formula'])
        self.assertEqual(sum(result['damage_rolls'])+2,result['damage_total'])
        self.assertTrue(result['breakdown']['strikes'][0]['critical'])

    def test_estocada_retry_reuses_roll_and_charges_only_once(self):
        self.durable_target()
        with patch('app.hemomancy.roll_formula',return_value={'total':3,'individual_results':[3]}) as roll:
            reply=self.attack('lanca','skill',request='spear-skill-replay')
            self.assertEqual(5,self.laminas())
            confirmed=self.confirm(reply)
            self.assertEqual(200,confirmed.status_code,confirmed.text)
            self.assertEqual(4,self.laminas())
            self.assertEqual(confirmed.json(),self.attack('lanca','skill',request='spear-skill-replay').json())
            self.assertEqual(4,self.laminas())
            self.assertEqual(1,roll.call_count)
            next_reply=self.attack('lanca','skill',request='spear-skill-next')
            self.assertEqual(200,self.confirm(next_reply).status_code)
            self.assertEqual(3,self.laminas())

    def test_estocada_miss_spends_skill_cost_without_rolling_damage(self):
        with patch('app.hemomancy.roll_formula') as roll:
            reply=self.attack('lanca','skill',request='spear-skill-miss',die=2)
            confirmed=self.confirm(reply)
        self.assertEqual(200,confirmed.status_code,confirmed.text)
        self.assertEqual(0,confirmed.json()['damage_total'])
        self.assertEqual(4,self.laminas())
        roll.assert_not_called()

    def test_previous_weapon_revision_is_rejected_without_spending(self):
        reply=self.use('raziel','hemomancia-lanca',dict(request_id='spear-old-revision',
            mode='skill',definition_revision='raziel-five-weapons-v1',target_type='token',
            target_id=self.wounded['id'],roll_mode='physical',d20=15))
        self.assertEqual(400,reply.status_code,reply.text)
        self.assertEqual(5,self.laminas())

    def test_scythe_bleeds_exactly_two_target_turns_and_retry_does_not_tick(self):
        self.durable_target();self.start_combat()
        result=self.confirm(self.attack('foice','skill',request='bleed-in-combat'))
        self.assertEqual(200,result.status_code,result.text);self.assertEqual(4,self.laminas())
        for request in ('bleed-turn-one','bleed-turn-two'):
            with patch('app.hemomancy.roll_formula',return_value={'total':2,'individual_results':[2]}):
                first=self.command('next_turn',request)
                self.assertEqual(first,self.command('next_turn',request))
            self.command('next_turn',request+'-return')
        self.assertFalse(self.effects('bleed'))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(2,db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='hemomancy_bleed'").fetchone()[0])
            detail=json.loads(db.execute("SELECT detail_json FROM session_ledger WHERE source_type='hemomancy_bleed' LIMIT 1").fetchone()[0])
            self.assertEqual('1d4',detail['formula']);self.assertEqual([2],detail['results']);self.assertEqual(2,detail['total'])

    def test_shield_cost_once_no_attack_consumption_and_end_cleanup(self):
        self.start_combat()
        payload={'request_id':'shield-native-01'}
        reply=self.use('raziel','hemomancia-escudo',payload)
        self.assertEqual(200,reply.status_code,reply.text);self.assertEqual(4,self.laminas())
        self.assertEqual(reply.json(),self.use('raziel','hemomancia-escudo',payload).json())
        self.assertFalse(reply.json()['encounter'].get('action_committed'))
        self.assertEqual(1,len(self.effects('shield')))
        self.command('end','hemomancy-end-01')
        self.assertFalse(self.effects('shield'))

    def test_complete_rest_clears_own_weapon_and_riders_on_others(self):
        from app.combat_effects import expire_rest_effects
        self.durable_target()
        result=self.confirm(self.attack('marreta',request='rest-expose-01'))
        self.assertEqual(200,result.status_code,result.text)
        with closing(sqlite3.connect(self.db)) as db,db:expire_rest_effects(db,'raziel',complete=True)
        self.assertFalse(self.effects('weapon'));self.assertFalse(self.effects('exposed'))

    def test_hemomancy_effects_stay_on_their_map_without_deleting_them(self):
        reply=self.use('raziel','hemomancia-escudo',{'request_id':'map-shield-test'})
        self.assertEqual(200,reply.status_code,reply.text)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_state SET map_id='other-map' WHERE id=1")
        self.assertFalse(self.effects('shield'))
        with closing(sqlite3.connect(self.db)) as db,db:
            self.assertEqual(1,db.execute("SELECT COUNT(*) FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.hemomancy_kind')='shield'").fetchone()[0])
            db.execute("UPDATE session_workspace_state SET map_id='default' WHERE id=1")
        self.assertEqual(1,len(self.effects('shield')))

    def test_range_rechecked_after_preview_and_no_charge_on_failure(self):
        reply=self.attack('lanca')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=18 WHERE token_id=?',(self.wounded['id'],))
        rejected=self.confirm(reply)
        self.assertIn(rejected.status_code,(400,409));self.assertEqual(5,self.laminas())

    def test_shield_revanche_uses_existing_native_incoming_attack(self):
        from app.combat import resolve_attack,confirm_attack_resolution
        from app.combat_effects import readeffects
        shield=self.use('raziel','hemomancia-escudo',{'request_id':'shield-revenge-01'})
        self.assertEqual(200,shield.status_code,shield.text)
        native={'id':'enemy','name':'Inimigo','attacks':[{'id':'claw','attack_bonus':0,'damage':'1d4','weapon_item_path':'natural:claw'}]}
        preview,_=resolve_attack(self.db,request_id='incoming-revenge-01',actor_character_id='enemy',actor_name='Inimigo',requested_by_id='master',requested_by_role='gm',definition=native,inventory=[],attack_id='claw',target={'type':'character','id':'raziel','armor_class':12,'current_hp':10,'maximum_hp':16},roll_mode='physical',physical_d20=11)
        confirm_attack_resolution(self.db,resolution_id=preview['resolution_id'],requested_by_id='master',requested_by_role='gm')
        self.assertEqual(1,len(self.effects('revenge')))
        reply=self.attack('arco',request='revenge-bow-01')
        self.assertEqual(1,reply.json()['breakdown']['hemomancy']['passive_d6'])
        self.assertEqual(200,self.confirm(reply).status_code);self.assertFalse(self.effects('revenge'))

    def test_rupture_ignores_two_reduction_not_immunity(self):
        from app.hemomancy import damage_after_mitigation
        record={'target_type':'token','target_id':self.wounded['id'],'breakdown':{'hemomancy':{'damage_type':'bludgeoning','ignore_reduction':2}}}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps({'damage_reduction':4}),self.wounded['id']))
            self.assertEqual(8,damage_after_mitigation(db,record,10))
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps({'damage_reduction':4,'damage_immunities':['bludgeoning']}),self.wounded['id']))
            self.assertEqual(0,damage_after_mitigation(db,record,10))

    def test_grid_ring_uses_server_range_even_with_gm_override(self):
        from app.access import AccessContext
        main.app.dependency_overrides[main.require_any]=lambda:AccessContext(mode='gm')
        reply=self.client.get('/gm/grid/range',params={'ref':'technique:raziel:hemomancia-arco','map_id':'default','attacker_token_id':self.pin['id'],'range_override_m':99,'max_range_m':99})
        self.assertEqual(200,reply.status_code,reply.text);self.assertEqual(9,reply.json()['range_m'])

    def test_insufficient_blood_and_hidden_target_do_not_create_preview(self):
        reply=self.attack('foice','skill',request='insufficient-01',die=2)
        self.assertEqual(200,self.confirm(reply).status_code);self.assertEqual(4,self.laminas())
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0]);state['resources'][0]['current']=0
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",(json.dumps(state),))
        self.assertEqual(400,self.attack('marreta',request='insufficient-02').status_code)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET visible_to_players=0 WHERE id=?',(self.wounded['id'],))
        self.assertEqual(400,self.attack(request='hidden-attack-01').status_code)
        self.assertEqual(0,self.laminas())

    def test_shield_can_follow_attack_but_weapon_switch_does_not_grant_another_attack(self):
        self.start_combat()
        self.assertEqual(200,self.confirm(self.attack(die=1)).status_code)
        self.assertEqual(400,self.attack('lanca',request='no-extra-attack').status_code)
        reply=self.use('raziel','hemomancia-escudo',{'request_id':'shield-after-hit'})
        self.assertEqual(200,reply.status_code,reply.text)
        self.assertTrue(reply.json()['encounter']['action_committed']);self.assertEqual(1,reply.json()['encounter']['attacks_used'])

    def test_scythe_does_not_bleed_targets_without_blood(self):
        self.durable_target()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps({'armor_class':10,'has_blood':False}),self.wounded['id']))
        result=self.confirm(self.attack('foice','skill',request='undead-no-bleed'))
        self.assertEqual(200,result.status_code,result.text);self.assertFalse(self.effects('bleed'))

    def test_concurrent_retries_share_native_preview_and_one_confirmation(self):
        from concurrent.futures import ThreadPoolExecutor
        self.durable_target()
        with ThreadPoolExecutor(max_workers=2) as executor:
            replies=list(executor.map(lambda _:self.attack(request='concurrent-bow-01',die=1),range(2)))
            self.assertEqual(replies[0].json(),replies[1].json())
            results=list(executor.map(self.confirm,replies))
        for result in results:self.assertEqual(200,result.status_code,result.text)
        self.assertEqual(results[0].json(),results[1].json());self.assertEqual(4,self.laminas())
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(1,db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='combat_action'").fetchone()[0])

    def test_same_identity_cannot_be_reused_between_shield_and_attack(self):
        shield=self.use('raziel','hemomancia-escudo',{'request_id':'cross-command-01'})
        self.assertEqual(200,shield.status_code,shield.text)
        self.assertEqual(400,self.attack(request='cross-command-01').status_code)
        self.assertEqual(4,self.laminas())

    def test_native_flat_damage_buffs_apply_once_even_on_bow_critical(self):
        self.command('apply','flat-buff-hemomancy',target_type='character',target_id='raziel',label='Bônus de ensaio',source='fixture',duration='scene',modifiers={'damage_bonus':2})
        reply=self.attack(die=19,request='critical-flat-01')
        self.assertEqual(200,reply.status_code,reply.text)
        result=reply.json()
        self.assertTrue(result['breakdown']['strikes'][0]['critical'])
        self.assertEqual(2,result['damage_modifier'])
        self.assertEqual(sum(result['damage_rolls'])+2,result['damage_total'])

    def test_heartshot_reads_the_existing_rubra_mark(self):
        plain=self.attack('arco','skill',request='heartshot-no-mark')
        self.assertEqual(200,plain.status_code,plain.text)
        marked=self.use('raziel','marca-rubra',{'request_id':'heartshot-native-mark','target_type':'token','target_id':self.wounded['id']})
        self.assertEqual(200,marked.status_code,marked.text)
        shot=self.attack('arco','skill',request='heartshot-with-mark')
        self.assertEqual(200,shot.status_code,shot.text)
        self.assertEqual(plain.json()['attack_bonus']+2,shot.json()['attack_bonus'])

    def test_carrasco_uses_pre_hit_quarter_hp_not_the_attack_damage(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=3 WHERE id=?',(self.wounded['id'],))
        low=self.attack('foice',request='quarter-hp-01')
        self.assertEqual(200,low.status_code,low.text)
        self.assertEqual(1,low.json()['breakdown']['hemomancy']['passive_d6'])
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=4 WHERE id=?',(self.wounded['id'],))
        higher=self.attack('foice',request='above-quarter-01')
        self.assertEqual(200,higher.status_code,higher.text)
        self.assertEqual(0,higher.json()['breakdown']['hemomancy']['passive_d6'])

    def test_shield_expires_with_existing_round_clock(self):
        self.start_combat()
        reply=self.use('raziel','hemomancia-escudo',{'request_id':'shield-round-01'})
        self.assertEqual(200,reply.status_code,reply.text)
        self.command('next_turn','shield-round-02');self.command('next_turn','shield-round-03')
        self.assertFalse(self.effects('shield'));self.assertEqual(4,self.laminas())

    def test_scythe_finisher_is_visible_in_native_result_details(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=1 WHERE id=?',(self.wounded['id'],))
        result=self.confirm(self.attack('foice',request='scythe-finisher-01'))
        self.assertEqual(200,result.status_code,result.text)
        self.assertEqual(0,result.json()['hp_after'])
        self.assertTrue(any('desmembramento' in text for text in result.json()['breakdown']['manual_effects']))

    def test_personal_shield_preserves_use_outside_a_tactical_grid(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('DELETE FROM session_workspace_entity_positions')
            db.execute('DELETE FROM session_workspace_map_grids')
        result=self.use('raziel','hemomancia-escudo',{'request_id':'shield-no-grid-01'})
        self.assertEqual(200,result.status_code,result.text)
        self.assertEqual(4,self.laminas());self.assertEqual(1,len(self.effects('shield')))

    def test_command_reads_persisted_sheet_without_normalizing_state(self):
        with patch.object(main,'_playable_character',wraps=main._playable_character) as read:
            reply=self.attack(die=1)
        self.assertEqual(200,reply.status_code,reply.text)
        self.assertIs(read.call_args.kwargs.get('read_only'),True)

    def test_missing_humanoid_attack_is_rejected_without_spending(self):
        with patch.object(main,'_playable_character',return_value={'definition':{'attacks':[]},'inventory':[]}):
            reply=self.attack()
        self.assertEqual(400,reply.status_code,reply.text);self.assertEqual(5,self.laminas())

    def test_existing_speed_budget_is_preserved_without_extra_attacks_from_switching(self):
        self.command('apply','native-speed-hemo',target_type='character',target_id='raziel',label='Velocidade',source='fixture',duration='scene',modifiers={'extra_attacks':1})
        self.start_combat()
        first=self.confirm(self.attack('arco',request='speed-hemo-first',die=2))
        self.assertEqual(200,first.status_code,first.text)
        from app.combat_effects import readeffects
        self.assertFalse(readeffects(self.db)['encounter']['action_committed'])
        second=self.confirm(self.attack('lanca',request='speed-hemo-second',die=2))
        self.assertEqual(200,second.status_code,second.text)
        self.assertEqual(2,readeffects(self.db)['encounter']['attacks_used'])
        self.assertEqual(400,self.attack('foice',request='speed-hemo-third',die=1).status_code)

    def test_miss_consumes_exposed_and_revenge_once_without_bonus_damage(self):
        from app.hemomancy import _put
        self.durable_target()
        self.assertEqual(200,self.confirm(self.attack('marreta',request='edge-expose')).status_code)
        with closing(sqlite3.connect(self.db)) as db,db:
            _put(db,'revenge','Revanche Rubra','now',map_id='default')
        with patch('app.hemomancy.roll_formula') as roll:
            preview=self.attack('lanca',request='edge-miss',die=1)
            first=self.confirm(preview)
            again=self.confirm(preview)
        self.assertEqual(200,first.status_code,first.text)
        self.assertEqual(first.json(),again.json())
        self.assertEqual(0,first.json()['damage_total'])
        roll.assert_not_called()
        self.assertFalse(self.effects('exposed'));self.assertFalse(self.effects('revenge'))
        self.assertEqual(3,self.laminas())

    def test_arterial_each_condition_grants_one_die_and_both_still_one(self):
        from app.hemomancy import _put
        self.durable_target()
        for kinds in [('exposed',),('bleed',),('exposed','bleed')]:
            with self.subTest(kinds=kinds):
                with closing(sqlite3.connect(self.db)) as db,db:
                    db.execute("UPDATE combat_effects SET active=0")
                    for kind in kinds:
                        _put(db,kind,kind,'now',target_type='token',target_id=self.wounded['id'],map_id='default',remaining_turns=2)
                preview=self.attack('lanca',request='arterial-edge-'+'-'.join(kinds))
                self.assertEqual(200,preview.status_code,preview.text)
                self.assertEqual(len(kinds),preview.json()['breakdown']['hemomancy']['passive_d6'])
                self.assertEqual(2 if 'exposed' in kinds else 0,preview.json()['damage_modifier'])

    def test_immune_target_does_not_become_exposed_on_mace_hit(self):
        self.durable_target()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',
                (json.dumps({'armor_class':10,'damage_immunities':['physical']}),self.wounded['id']))
        result=self.confirm(self.attack('marreta',request='immune-trauma'))
        self.assertEqual(200,result.status_code,result.text)
        self.assertEqual(100,result.json()['hp_after'])
        self.assertFalse(self.effects('exposed'))

    def test_reapplying_ceifa_refreshes_one_bleed_instead_of_stacking(self):
        self.durable_target()
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()[0])
            state['resources'][0].update(current=10,maximum=10)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",(json.dumps(state),))
        for request in ('ceifa-refresh-first','ceifa-refresh-second'):
            result=self.confirm(self.attack('foice','skill',request=request))
            self.assertEqual(200,result.status_code,result.text)
            effects=self.effects('bleed')
            self.assertEqual(1,len(effects));self.assertEqual(2,effects[0]['remaining_turns'])
        self.assertEqual(8,self.laminas())
        self.start_combat()
        for request in ('ceifa-refresh-tick-one','ceifa-refresh-tick-two'):
            with patch('app.hemomancy.roll_formula',return_value={'total':2,'individual_results':[2]}):
                first=self.command('next_turn',request)
                self.assertEqual(first,self.command('next_turn',request))
            self.command('next_turn',request+'-return')
        self.assertFalse(self.effects('bleed'))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(2,db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='hemomancy_bleed'").fetchone()[0])
