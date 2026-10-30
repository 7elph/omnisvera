"""Source/approved exposure contracts; no operational state."""
import copy
import unittest
import json
import sqlite3
from contextlib import closing
from unittest.mock import patch
import test_monster_runtime as runtime_fixture
from app.monster_catalog import get_catalog_monster


class MonsterExposureContractTests(unittest.TestCase):
    def spec(self,identity,name):
        from app.monster_exposures import exposure_specs
        return next(s for s in exposure_specs(get_catalog_monster(identity)) if s['name']==name)

    def test_basilisk_and_approved_medusa_require_eye_contact(self):
        for identity,name in [('basilisco','Petrificação'),('medusa','Olhar Petrificante')]:
            s=self.spec(identity,name)
            self.assertEqual(s['activation'],'gaze');self.assertEqual(s['geometry']['radius_m'],15)
            self.assertTrue(s['requires_eye_contact']);self.assertEqual(s['condition']['effect'],'petrified')
            self.assertEqual(s['condition']['duration_unit'],'permanent');self.assertEqual(s['save'],'JPC')
        self.assertTrue(self.spec('basilisco','Petrificação')['reflection_allowed'])
        self.assertFalse(self.spec('medusa','Olhar Petrificante')['reflection_allowed'])

    def test_gorgon_approved_permanent_gas_has_radius_ten(self):
        s=self.spec('gorgon','Baforada Petrificante')
        self.assertEqual(s['activation'],'gas');self.assertEqual(s['geometry']['radius_m'],10)
        self.assertEqual(s['condition']['duration_unit'],'permanent');self.assertIsNone(s['damage_formula'])

    def test_iron_golem_gas_recharges_only_after_seven_attacks(self):
        s=self.spec('golem-de-ferro','Baforada de gás')
        self.assertEqual(s['geometry']['radius_m'],6);self.assertEqual(s['damage_formula'],'3d6')
        self.assertEqual(s['save'],'JPD');self.assertEqual(s['save_effect'],'halves')
        self.assertEqual(s['uses'],{'maximum':1,'recharge':'every_n_attacks','every_n_attacks':7})

    def test_no_default_range_or_save_or_conditional_negation(self):
        from app.monster_exposures import exposure_specs
        for description in ['O alvo dos olhos vira pedra; JPC evita.',
                            'O olhar petrifica permanentemente a até 15 metros.',
                            'O olhar não causa petrificação a até 15 metros. JPC evita.']:
            monster={'id':'custom','abilities':[{'name':'Olhar Petrificante','description':description}]}
            specs=exposure_specs(monster)
            self.assertTrue(not specs or all(s['execution_status']=='assisted' for s in specs))

    def test_approved_override_is_not_applied_to_unrelated_custom_monster(self):
        from app.monster_exposures import exposure_specs
        custom=copy.deepcopy(get_catalog_monster('medusa'));custom['id']='custom'
        self.assertTrue(all(s['execution_status']=='assisted' for s in exposure_specs(custom)))


class MonsterExposureRuntimeTests(unittest.TestCase):
    setUp=runtime_fixture.MonsterRuntimeTests.setUp
    hp=runtime_fixture.MonsterRuntimeTests.hp
    token_hp=runtime_fixture.MonsterRuntimeTests.token_hp
    command=runtime_fixture.MonsterRuntimeTests.command

    def actor(self,identity):
        monster=get_catalog_monster(identity)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=?,name=? WHERE id='gob1'",(json.dumps({**monster,'source':{'monster_id':identity}}),monster['name']))
        return monster

    def payload(self,name,aim='vez-pin'):
        from app.monster_runtime import preview
        from app.combat_effects import effect_snapshot
        with closing(sqlite3.connect(self.db)) as db:
            contract,_,_=preview(db,effect_snapshot(db),'gob1',name,aim)
        return {'token_id':'gob1','ability_name':name,'aim_token_id':aim,'definition_revision':contract['revision'],'area_fingerprint':contract['area_fingerprint']}

    def test_gorgon_area_applies_jp_and_permanent_condition_once(self):
        self.actor('gorgon');payload=self.payload('Baforada Petrificante')
        with patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}) as saving:
            first=self.command(payload=payload);repeat=self.command(payload=payload,version=0)
        self.assertEqual(first,repeat);saving.assert_called_once();self.assertEqual(self.hp(),30)
        self.assertEqual(len(first['protocol_result']['results']),1)
        effect=first['effects'][0];self.assertEqual(effect['monster_condition'],'petrified');self.assertEqual(effect['duration'],'manual')
        self.assertTrue(first['encounter']['action_committed'])

    def test_unregistered_source_is_rejected_as_a_validation_error(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json='{}' WHERE id='gob1'")
        with self.assertRaisesRegex(ValueError,'catálogo'):
            self.command(payload={'token_id':'gob1','ability_name':'Olhar','aim_token_id':'vez-pin'})

    def test_gaze_requires_explicit_contact_and_selects_only_one_target(self):
        self.actor('basilisco');payload=self.payload('Petrificação')
        with self.assertRaisesRegex(ValueError,'contato visual'):self.command(payload=payload)
        payload['eye_contact_confirmed']=True
        with patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}):result=self.command(payload=payload)
        self.assertEqual(len(result['protocol_result']['results']),1)
        self.assertFalse(result['encounter'].get('action_committed',False))

    def test_iron_golem_cannot_emit_gas_without_confirmed_attacks(self):
        self.actor('golem-de-ferro')
        with self.assertRaisesRegex(ValueError,'7 ataques'):self.command(payload=self.payload('Baforada de gás'))

    def test_construct_form_immunity_prevents_petrification_without_rolling_jp(self):
        self.actor('gorgon')
        with patch('app.construct_rules.is_construct',return_value=True),patch('app.dorn_spells.save') as saving:
            result=self.command(payload=self.payload('Baforada Petrificante'))
        saving.assert_not_called();self.assertEqual(result['effects'],[])
        self.assertIn('Forma Imutável',result['protocol_result']['results'][0]['condition']['immune'])

    def test_basilisk_can_only_petrify_itself_after_confirmed_reflection(self):
        self.actor('basilisco');payload=self.payload('Petrificação',aim='gob1');payload['eye_contact_confirmed']=True
        with patch('app.dorn_spells.save',return_value={'success':False,'total':1,'target':14}):result=self.command(payload=payload)
        self.assertEqual(result['effects'][0]['target_id'],'gob1');self.assertEqual(result['effects'][0]['monster_condition'],'petrified')
        self.actor('medusa')
        with self.assertRaisesRegex(ValueError,'própria origem'):self.payload('Olhar Petrificante',aim='gob1')

    def test_recharge_counts_confirmed_strikes_not_previews_or_retries(self):
        from app.combat import monster_attack_definition,resolve_attack,confirm_attack_resolution
        from app.combat_effects import effect_snapshot
        from app.monster_runtime import token_monster,action_contracts
        monster=self.actor('golem-de-ferro')
        with closing(sqlite3.connect(self.db)) as db,db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]);state.update(current_hp=1000,maximum_hp=1000)
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
        for n in range(7):
            with closing(sqlite3.connect(self.db)) as db,db:
                clock=effect_snapshot(db)['encounter'];clock.update(action_committed=False,attacks_used=0);clock.pop('pending_attack',None)
                db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(clock),))
            record,_=resolve_attack(self.db,request_id=f'golem-counter-{n}',actor_character_id='gob1',actor_name=monster['name'],requested_by_id='master',requested_by_role='gm',
                definition=monster_attack_definition({'id':'gob1','name':monster['name'],'sheet':monster},'0'),inventory=[],attack_id='0',target={'type':'character','id':'vezemir','name':'Vezemir','armor_class':1,'current_hp':1000},roll_mode='physical',physical_d20=15,rng=lambda a,b:1)
            confirm_attack_resolution(self.db,resolution_id=record['resolution_id'],requested_by_id='master',requested_by_role='gm')
            confirm_attack_resolution(self.db,resolution_id=record['resolution_id'],requested_by_id='master',requested_by_role='gm')
            with closing(sqlite3.connect(self.db)) as db:
                contracts=action_contracts(db,'gob1');gas=next(s for s in contracts.values() if s['name']=='Baforada de gás')
                self.assertEqual(gas['attacks_until_ready'],max(0,6-n))
        with closing(sqlite3.connect(self.db)) as db,db:
            clock=effect_snapshot(db)['encounter'];clock.update(action_committed=False,attacks_used=0);clock.pop('pending_attack',None)
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(clock),))
        with patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}),patch('app.monster_runtime.roll_formula',return_value={'total':6,'individual_results':[2,2,2]}):
            self.command(payload=self.payload('Baforada de gás'))
        with closing(sqlite3.connect(self.db)) as db:
            gas=next(s for s in action_contracts(db,'gob1').values() if s['name']=='Baforada de gás');self.assertEqual(gas['attacks_until_ready'],7)
