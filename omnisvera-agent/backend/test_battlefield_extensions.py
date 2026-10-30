import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_battle_mode as fixture
from app.session_workspace import save_workspace_token,list_workspace_tokens
from app.summons import create_summon


class CorpseTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.BattleModeTests();self.f.setUp();self.addCleanup(self.f.doCleanups);self.db=self.f.db
        self.f.base._insert_character('morthak',10,10)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'",(json.dumps({'current_hp':10,'maximum_hp':10,'resources':[{'key':'animar-mortos','current':2,'maximum':2}]}),))
            db.execute('UPDATE session_workspace_tokens SET current_hp=0 WHERE id=?',(self.f.enemy['id'],))
        self.spec=dict(name='Zumbi de Morthak',hp=10,ac=13,marker='🧟',attack_name='Pancada',attack_bonus=2,damage='1d6',resource_key='animar-mortos',duration='1 cena',note='Perfil existente de reanimação')

    def summon(self,request='corpse-test-001'):
        return create_summon(self.db,caster='morthak',technique='animar-mortos',spec=self.spec,request_id=request,actor_id='morthak',actor_role='player',corpse_id=self.f.enemy['id'])

    def test_dead_body_is_corpse_and_automatically_available(self):
        corpse=next(t for t in list_workspace_tokens(self.db) if t['id']==self.f.enemy['id'])
        self.assertTrue(corpse['sheet']['corpse']);self.assertTrue(corpse['sheet']['reanimation_allowed'])
        first=self.summon();self.assertEqual(first,self.summon())
        self.assertNotEqual(first['token']['id'],corpse['id']);self.assertEqual(first['token']['current_hp'],10)
        with self.assertRaises(ValueError):self.summon('corpse-second-command')
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
            self.assertEqual(1,state['resources'][0]['current'])

    def test_living_body_and_explicit_gm_veto_do_not_spend(self):
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE session_workspace_tokens SET current_hp=1 WHERE id=?',(self.f.enemy['id'],))
        with self.assertRaises(ValueError):self.summon()
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE session_workspace_tokens SET current_hp=0,sheet_json=? WHERE id=?',(json.dumps({'reanimation_allowed':False}),self.f.enemy['id']))
        with self.assertRaises(ValueError):self.summon()

    def test_construct_and_summon_corpses_are_not_reusable(self):
        for sheet in ({'is_construct':True},{'is_undead':True},{'summon':{'caster':'morthak','technique':'levantar-esqueleto'}}):
            with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(sheet),self.f.enemy['id']))
            with self.assertRaises(ValueError):self.summon()


class DiagonalTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.BattleModeTests();self.f.setUp();self.addCleanup(self.f.doCleanups);self.db=self.f.db
        self.f.base._insert_character('morthak',10,10)
        self.f.command('start',map_id='arena',battle_mode=True,participants=[
            {'target_type':'character','target_id':'vezemir','name':'Vezemir','initiative':20},
            {'target_type':'character','target_id':'morthak','name':'Morthak','initiative':15},
            {'target_type':'token','target_id':self.f.enemy['id'],'name':'Alvo','initiative':1}])
        from app.spatial_grid import init_spatial
        init_spatial(self.db)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO session_workspace_map_grids VALUES('arena','square',20,20,1.5,0,0,'chebyshev',1,1)")
            for token, in db.execute("SELECT id FROM session_workspace_tokens WHERE map_id='arena'").fetchall():db.execute("INSERT INTO session_workspace_entity_positions VALUES('arena',?,0,0,1,1,1)",(token,))
        self.place('vezemir',4,4);self.place('morthak',5,5);self.place(self.f.enemy['id'],10,10)

    def place(self,identity,x,y):
        with closing(sqlite3.connect(self.db)) as db,db:
            token=db.execute('SELECT id FROM session_workspace_tokens WHERE id=? OR character_id=?',(identity,identity)).fetchone()[0]
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=?,cell_y=?,version=version+1 WHERE token_id=?',(x,y,token))

    def bonus(self):
        from app.spatial_grid import connect,diagonal_bonus
        with closing(connect(self.db)) as db:return diagonal_bonus(db,'vezemir','token',self.f.enemy['id'])['bonus']

    def test_adjacent_diagonal_ally_grants_two_and_movement_removes(self):
        self.assertEqual(2,self.bonus());self.place('morthak',7,7);self.assertEqual(0,self.bonus())

    def test_opposite_diagonal_flank_grants_two(self):
        self.place('vezemir',4,4);self.place(self.f.enemy['id'],5,5);self.place('morthak',6,6)
        self.assertEqual(2,self.bonus())

    def test_dead_ally_never_grants_bonus(self):
        with closing(sqlite3.connect(self.db)) as db,db:db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'",(json.dumps({'current_hp':0,'maximum_hp':10}),))
        self.assertEqual(0,self.bonus())

    def test_bonus_enters_attack_resolution_without_changing_sheet(self):
        attack=self.f.attack();self.assertEqual(2,attack['breakdown']['attack']['tactical_bonus'])

    def test_natural_one_misses_even_with_diagonal_and_high_attack_bonus(self):
        from app.combat import resolve_attack
        definition={'id':'melee','attacks':[{'id':'melee','name':'Ataque','attack_bonus':20,'damage':'1d4','weapon_item_path':'w'}]}
        result,_=resolve_attack(self.db,request_id='diagonal-natural-one',actor_character_id='vezemir',actor_name='Vezemir',requested_by_id='vezemir',requested_by_role='player',definition=definition,inventory=[],attack_id='melee',target={'type':'token','id':self.f.enemy['id'],'armor_class':10,'current_hp':18},roll_mode='physical',physical_d20=1,rng=fixture.fixture.SequenceRng(3))
        self.assertEqual(2,result['breakdown']['attack']['tactical_bonus'])
        self.assertEqual('miss',result['result']);self.assertEqual(0,result['damage_total'])

    def test_moving_ally_invalidates_bonus_preview(self):
        from app.combat import confirm_attack_resolution,CombatExpiredError
        attack=self.f.attack();self.place('morthak',7,7)
        with self.assertRaises(CombatExpiredError):confirm_attack_resolution(self.db,resolution_id=attack['resolution_id'],requested_by_id='vezemir',requested_by_role='player')


class RacialTests(unittest.TestCase):
    def test_vezemir_approved_passives_are_visible_without_extra_attributes(self):
        from app.character_play import build_character_definition
        sheet={'race':{'race':'Meio-Elfo'},'character_class':{'level':5,'hit_points':27},'attributes':{'strength':16}}
        view=build_character_definition(profile_id='vezemir',note={'title':'Vezemir'},sheet=sheet,inventory=[],overrides={'attributes':{'strength':16}})
        traits=view['progression']['racial_traits'];self.assertTrue(traits['darkvision']);self.assertTrue(traits['secret_door_detection']);self.assertEqual(.5,traits['rest_duration_multiplier'])
        names={a['name'] for a in view['session_abilities']};self.assertTrue({'Visão no escuro','Detecção de portas escondidas','Descanso élfico'}<=names)
        self.assertEqual(16,view['attributes']['strength'])
