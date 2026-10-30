"""Poison clock/attribute effects use disposable native sheets only."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_spell_engine as fixture
from app.combat_effects import init_effects,effect_snapshot,apply_definition_effects


class MonsterPoisonRuntimeTests(unittest.TestCase):
    hp=fixture.SpellEngineTests.hp
    def setUp(self):
        fixture.SpellEngineTests.setUp(self);init_effects(self.db)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='vezemir'",(json.dumps({'attributes':{'strength':17,'dexterity':14,'constitution':12,'intelligence':10}}),))

    def spec(self,**fields):
        return {'id':'fixture:poison:0','name':'Veneno','save':'JPC','poison':True,'immunity_races':[],**fields}

    def apply(self,spec,rolls):
        from app.monster_conditions import apply_spec
        from app.dorn_spells import target
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spells.save',return_value={'success':False,'total':1,'target':14}),patch('app.monster_poison_runtime.roll_formula',side_effect=[{'total':r,'individual_results':[r]} for r in rolls]):
            return apply_spec(db,target(db,'character','vezemir'),spec,'gob1','now')

    def state(self):
        from app.monster_poison_runtime import current_attributes
        with closing(sqlite3.connect(self.db)) as db:return current_attributes(db,'character','vezemir'),effect_snapshot(db)

    def advance(self,seconds,rolls=()):
        from app.dorn_spells import elapse
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.monster_poison_runtime.roll_formula',side_effect=[{'total':r,'individual_results':[r]} for r in rolls]):
            elapse(db,effect_snapshot(db),seconds,[],'now')

    def test_immediate_con_loss_is_derived_and_preserves_the_original_sheet(self):
        result=self.apply(self.spec(effect='poison_attribute',attribute='constitution',amount_formula='1d4+2',floor=0),[4])
        self.assertEqual(self.state()[0]['constitution'],8);self.assertEqual(result['attribute_after'],8)
        with closing(sqlite3.connect(self.db)) as db:
            original=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(original['attributes']['constitution'],12)

    def test_delayed_sleep_never_blocks_before_onset_and_expires_after_its_duration(self):
        self.apply(self.spec(effect='delayed_condition',condition='asleep',delay_formula='1d6+5',delay_unit='rounds',duration_formula='1d3',duration_unit='turns'),[6,1])
        self.advance(59);self.assertFalse(self.state()[1]['effects'][0]['blocks_actions'])
        self.advance(1);effect=self.state()[1]['effects'][0];self.assertTrue(effect['blocks_actions']);self.assertEqual(effect['remaining_seconds'],600)
        self.advance(599);self.assertTrue(self.state()[1]['effects'][0]['blocks_actions'])
        self.advance(1);self.assertEqual(self.state()[1]['effects'],[])

    def test_one_large_advance_processes_onset_and_expiration_without_extending_poison(self):
        self.apply(self.spec(effect='delayed_condition',condition='paralyzed',delay_formula='1d6+2',delay_unit='rounds',duration_formula='1d3',duration_unit='turns'),[3,1])
        self.advance(630);self.assertEqual(self.state()[1]['effects'],[])

    def test_periodic_dexterity_drain_clamps_at_three_and_stops_rolling(self):
        self.apply(self.spec(effect='poison_attribute_periodic',attribute='dexterity',amount_formula='1d6',interval_seconds=600,floor=3,lethal_at_floor=False),[])
        self.advance(599);self.assertEqual(self.state()[0]['dexterity'],14)
        self.advance(1,[6]);self.assertEqual(self.state()[0]['dexterity'],8)
        self.advance(600,[6]);self.assertEqual(self.state()[0]['dexterity'],3)
        self.advance(1200);self.assertEqual(self.state()[0]['dexterity'],3);self.assertEqual(self.hp(),30)

    def test_explicit_lethal_periodic_poison_kills_only_when_attribute_reaches_zero(self):
        self.apply(self.spec(effect='poison_attribute_periodic',attribute='intelligence',amount_formula='1d6',interval_seconds=600,floor=0,lethal_at_floor=True),[])
        self.advance(600,[6]);self.assertEqual(self.hp(),30);self.assertEqual(self.state()[0]['intelligence'],4)
        self.advance(600,[6]);self.assertLessEqual(self.hp(),0)
        self.advance(600)

    def test_roper_delay_then_half_strength_duration_and_combat_modifier(self):
        self.apply(self.spec(effect='delayed_attribute',attribute='strength',multiplier=.5,delay_formula='1d3',delay_unit='turns',duration_formula='2d4+1',duration_unit='turns'),[1,3])
        self.advance(599);self.assertEqual(self.state()[0]['strength'],17)
        self.advance(1);attrs,state=self.state();self.assertEqual(attrs['strength'],8)
        projected=apply_definition_effects({'attributes':{'strength':17},'attacks':[{'id':'melee','attack_bonus':10,'damage':'1d8+3'}]},state['effects'])
        self.assertEqual(projected['attacks'][0]['attack_bonus'],6);self.assertEqual(projected['attacks'][0]['damage'],'1d8-1')
        self.advance(1800);self.assertEqual(self.state()[0]['strength'],17)

    def test_removal_or_full_rest_stops_pending_poison(self):
        from app.combat_effects import expire_rest_effects
        self.apply(self.spec(effect='delayed_condition',condition='paralyzed',delay_formula='1d6+2',delay_unit='rounds',duration_formula='1d3',duration_unit='turns'),[3,1])
        with closing(sqlite3.connect(self.db)) as db,db:expire_rest_effects(db,'vezemir',complete=True)
        self.advance(900);self.assertEqual(self.state()[1]['effects'],[])

    def test_poison_boundary_does_not_split_legacy_levitation_round_bookkeeping(self):
        self.apply(self.spec(effect='delayed_condition',condition='asleep',delay_formula='1d6+5',delay_unit='rounds',duration_formula='1d3',duration_unit='turns'),[6,1])
        self.advance(55)
        with closing(sqlite3.connect(self.db)) as db,db:
            effect={'id':'levitation-fixture','target_type':'character','target_id':'vezemir','label':'Levitação','source':'fixture',
                'spell':'levitacao','duration':'fictional_time','remaining_seconds':6000,'modifiers':{},'ranged_attack_round':1,'levitation_ranged_penalty':-1}
            db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],'character','vezemir',json.dumps(effect)))
        self.advance(10)
        effect=next(e for e in self.state()[1]['effects'] if e['id']=='levitation-fixture')
        self.assertEqual(effect['levitation_ranged_penalty'],-2);self.assertNotIn('ranged_attack_round',effect)

    def test_missing_npc_attribute_stays_manual_without_inventing_a_base_score(self):
        from app.monster_conditions import apply_spec
        from app.dorn_spells import target
        spec=self.spec(effect='poison_attribute',attribute='constitution',amount_formula='1d4+2',floor=0)
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spells.save',return_value={'success':False}):
            result=apply_spec(db,target(db,'token','gob1'),spec,'fixture','now')
            self.assertTrue(result['manual'])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM combat_effects WHERE active=1').fetchone()[0],0)

    def test_public_effect_keeps_status_without_revealing_the_technical_source(self):
        from app.monster_conditions import public_effect
        self.apply(self.spec(effect='poison_attribute',attribute='constitution',amount_formula='1d4+2',floor=0),[4])
        effect=self.state()[1]['effects'][0];public=public_effect(effect)
        self.assertEqual(public['attribute_loss'],4)
        self.assertTrue({'poison_spec','source_token_id','rider_id'}.isdisjoint(public))

    def test_dexterity_drain_changes_ranged_accuracy_without_changing_weapon_damage(self):
        self.apply(self.spec(effect='poison_attribute_periodic',attribute='dexterity',amount_formula='1d6',interval_seconds=600,floor=3,lethal_at_floor=False),[])
        self.advance(600,[6]);effects=self.state()[1]['effects']
        definition={'attributes':{'dexterity':14},'attacks':[{'id':'ranged','attack_bonus':8,'damage':'1d6+2'}]}
        projected=apply_definition_effects(definition,effects)
        self.assertEqual(projected['attacks'][0]['attack_bonus'],5)  # DEX 14 (+2) -> 8 (-1).
        self.assertEqual(projected['attacks'][0]['damage'],'1d6+2')
        self.assertEqual(definition['attributes']['dexterity'],14)

    def test_npc_weakness_reaches_the_actual_numbered_monster_attack(self):
        from app.combat import monster_attack_definition
        effect={'id':'weakness','modifiers':{},'poison_runtime':True,'attribute':'strength','attribute_multiplier':.5}
        token={'id':'fixture-npc','name':'Alvo','sheet':{'attributes':{'strength':17},
               'attacks':[{'name':'Mordida','bonus':10,'damage':'1d8+3'}]}}
        projected=apply_definition_effects(monster_attack_definition(token,'0'),[effect])
        self.assertEqual(projected['attacks'][0]['attack_bonus'],6)
        self.assertEqual(projected['attacks'][0]['damage'],'1d8-1')
