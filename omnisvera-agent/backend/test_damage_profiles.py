"""Typed damage reaches native HP without changing the operational database."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_spell_engine as fixture
import test_combat as attacks_fixture


class DamageProfileTests(unittest.TestCase):
    def test_only_explicit_offensive_elements_are_inferred(self):
        from app.damage_profiles import infer_damage_type
        self.assertEqual(infer_damage_type('Bola de Fogo','Causa 1d6 de dano.'),'fire')
        self.assertEqual(infer_damage_type('Toque','Causa 1d6 de dano de frio.'),'cold')
        for name,text in [('Proteção','É imune a fogo.'),('Teste','Não causa dano de fogo.'),
                          ('Teste','Causa dano de fogo e frio.')]:
            self.assertIsNone(infer_damage_type(name,text))

    def test_approved_magic_weapons_and_attack_bonus_are_distinct(self):
        from app.damage_profiles import attack_profile
        mundane={'item_path':'dagger','item_title':'Adaga','mechanics':{},'effect_rules':[{'kind':'attack_bonus','value':2}]}
        self.assertFalse(attack_profile({'weapon_item_path':'dagger'},[mundane])['magical'])
        for path in ['Items/Grisalma.md','Items/Adagas de Espectro Fantasma.md']:
            self.assertTrue(attack_profile({'weapon_item_path':path},[{'item_path':path}])['magical'])
        blood=attack_profile({'hemomancy':{'damage_type':'piercing'},'weapon_item_path':'hemomancy:lanca'},[])
        self.assertTrue(blood['magical']);self.assertEqual(blood['damage_type'],'piercing')

    def test_structured_type_and_material_override_prose(self):
        from app.damage_profiles import attack_profile
        profile=attack_profile({'weapon_item_path':'custom'},[{'item_path':'custom','item_title':'Adaga de fogo',
            'mechanics':{'damage_type':'cold','magical':True,'material':'silver'}}])
        self.assertEqual((profile['damage_type'],profile['magical'],profile['material']),('cold',True,'silver'))


class TypedDamageRuntimeTests(unittest.TestCase):
    setUp=fixture.SpellEngineTests.setUp
    hp=fixture.SpellEngineTests.hp
    token_hp=fixture.SpellEngineTests.token_hp

    def monster(self,identity,hp=100):
        from app.monster_catalog import get_catalog_monster
        with closing(sqlite3.connect(self.db)) as db,db:
            sheet={**get_catalog_monster(identity),'source':{'monster_id':identity}}
            db.execute("UPDATE session_workspace_tokens SET sheet_json=?,current_hp=?,maximum_hp=? WHERE id='gob1'",(json.dumps(sheet),hp,hp))

    def test_catalog_fire_spell_honors_immunity_and_reports_actual_damage(self):
        from app.spell_engine import cast_spell
        self.monster('dragao-dourado')
        with patch('app.spell_engine.roll_formula',return_value={'total':6}):
            result=cast_spell(self.db,spell_id='arcana-bola-de-fogo',caster_type='character',caster_id='vezemir',
                targets=[{'type':'token','id':'gob1'}],roll_mode='physical',d20=[1])
        self.assertEqual(self.token_hp(),100)
        self.assertEqual(result['results'][0]['damage_dealt'],0)
        self.assertEqual(result['mechanic']['damage_type'],'fire')

    def test_fire_spell_wounds_do_not_regenerate(self):
        from app.spell_engine import cast_spell
        from app.monster_runtime import turn_start
        self.monster('troll')
        with patch('app.spell_engine.roll_formula',return_value={'total':6}):
            cast_spell(self.db,spell_id='arcana-bola-de-fogo',caster_type='character',caster_id='vezemir',
                targets=[{'type':'token','id':'gob1'}],roll_mode='physical',d20=[1])
        with closing(sqlite3.connect(self.db)) as db,db:
            turn_start(db,{'target_type':'token','target_id':'gob1'},{'started_at':'test'},1,'now','typed-fire-regen')
        self.assertEqual(self.token_hp(),94)

    def test_weapon_immunity_uses_context_not_all_damage(self):
        from app.combat_effects import change_hp,init_effects
        init_effects(self.db);self.monster('golem-de-carne')
        with closing(sqlite3.connect(self.db)) as db,db:
            for kind,magical,expected in [('weapon',False,100),('weapon',True,90),('spell',True,80)]:
                result=change_hp(db,'token','gob1',-10,'now',damage_type='physical',damage_context={'kind':kind,'magical':magical})
                self.assertEqual(result['hp_after'],expected)

    def test_natural_twenty_unavoidable_part_survives_weapon_immunity(self):
        from app.combat_effects import change_hp,init_effects
        init_effects(self.db);self.monster('golem-de-carne')
        with closing(sqlite3.connect(self.db)) as db,db:
            result=change_hp(db,'token','gob1',-12,'now',damage_type='physical',
                damage_context={'kind':'weapon','magical':False,'unavoidable_damage':5})
        self.assertEqual(result['hp_after'],95)


class TypedAttackRuntimeTests(unittest.TestCase):
    setUp=attacks_fixture.CombatAttackResolutionTests.setUp
    tearDown=attacks_fixture.CombatAttackResolutionTests.tearDown
    _insert_character=attacks_fixture.CombatAttackResolutionTests._insert_character
    _resolve=attacks_fixture.CombatAttackResolutionTests._resolve

    def test_confirmed_mundane_weapon_cannot_hurt_a_golem(self):
        from app.session_workspace import save_workspace_token
        from app.combat import confirm_attack_resolution
        self.inventory[0]['item_title']='Adaga de treino'
        target=save_workspace_token(self.database,token_type='monster',name='Golem',latitude=50,longitude=50,
            current_hp=50,maximum_hp=50,sheet={'armor_class':1,'source':{'monster_id':'golem-de-carne'}})
        result=self._resolve(target={'type':'token','id':target['id'],'name':'Golem','armor_class':1,'current_hp':50},
            request_id='typed-weapon-mundane',rng=attacks_fixture.SequenceRng(6))
        confirmed,_=confirm_attack_resolution(self.database,resolution_id=result['resolution_id'],requested_by_id='vezemir',requested_by_role='player')
        self.assertEqual(confirmed['hp_after'],50)
        self.assertFalse(confirmed['breakdown']['damage_profile']['magical'])
