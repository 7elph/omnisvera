import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch
import test_dorn_spells as fixtures
from app.combat_effects import effect_command,readeffects,apply_definition_effects


class DornApprovedPackTests(TestCase):
    def setUp(self):
        self.fixture=fixtures.DornSpellTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.path=self.fixture.db
        with closing(sqlite3.connect(self.path)) as db,db:
            row=db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone();state=json.loads(row[0])
            for key in ['reflexos','teia','forca_arcana','dissipar_magia']:
                state['resources'].append({'key':'dorn_'+key,'current':1,'maximum':1,'recharge':'inn_rest'})
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='dorn7'",(json.dumps(state),))

    def cast(self,spell,**payload):
        state=readeffects(self.path)
        return effect_command(self.path,actor_id='master',actor_role='gm',request_id='approved-dorn-'+spell,expected_version=state['version'],action='dorn_spell_cast',payload={'spell_id':spell,**payload})

    def test_reflexos_self_count_and_exploration_duration(self):
        with patch('app.dorn_spells.roll_formula',side_effect=[{'total':2},{'total':4}]):
            result=self.cast('reflexos')
        effect=result['effects'][0]
        self.assertEqual(3,effect['images_remaining'])
        self.assertEqual(4200,effect['remaining_seconds'])
        self.assertEqual('dorn7',effect['target_id'])

    def test_ended_combat_does_not_block_outside_combat_reflexos(self):
        with closing(sqlite3.connect(self.path)) as db,db:db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps({'active':False,'attacks_used':1,'action_committed':True}),))
        with patch('app.dorn_spells.roll_formula',return_value={'total':2}):result=self.cast('reflexos')
        self.assertEqual('Reflexos',result['protocol_result']['spell'])

    def test_forca_uses_original_strength_and_not_other_effects(self):
        with patch('app.dorn_spells.roll_formula',return_value={'total':2}):
            result=self.cast('forca-arcana',targets=[{'type':'character','id':'dorn7'}])
        effect=result['effects'][0]
        self.assertEqual(2,effect['modifiers']['strength_bonus'])
        self.assertEqual(3000,effect['remaining_seconds'])
        self.assertEqual(14,effect['original_strength'])
        definition=apply_definition_effects({'attributes':{'strength':14},'attacks':[{'id':'melee','attack_bonus':4,'damage':'1d6+2'}]},[effect])
        self.assertEqual(16,definition['attributes']['strength'])

    def test_dispel_uses_persisted_circle_level_and_replay(self):
        from app.necromancer_spells import add_effect
        with closing(sqlite3.connect(self.path)) as db,db:
            effect=add_effect(db,{'type':'character','id':'dorn7'},'Proteção arcana','fixture','now',magic_type='arcane',spell_circle=2,caster_level=5)
        payload={'spell_id':'dissipar-magia','effect_id':effect['id']}
        state=readeffects(self.path);args=dict(actor_id='master',actor_role='gm',request_id='approved-dispel-once',expected_version=state['version'],action='dorn_spell_cast',payload=payload)
        with patch('app.dorn_spells.roll_formula',return_value={'total':10}) as dice:
            first=effect_command(self.path,**args);second=effect_command(self.path,**args)
            self.assertEqual(first,second);self.assertEqual(1,dice.call_count)
        self.assertEqual(12,first['protocol_result']['results'][0]['difficulty'])
        self.assertTrue(first['protocol_result']['results'][0]['success'])
        self.assertEqual([],first['effects'])

    def test_reflection_redirects_one_hit_only_and_not_area_damage(self):
        from app.dorn_spell_pack import redirect_hits
        with patch('app.dorn_spells.roll_formula',side_effect=[{'total':1},{'total':1}]):self.cast('reflexos')
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.dorn_spell_pack.roll_formula',return_value={'total':1}) as dice:
            total,detail=redirect_hits(db,'character','dorn7',[{'result':'hit','damage_total':6},{'result':'hit','damage_total':7}],'now',area=True)
            self.assertEqual(13,total);dice.assert_not_called()
            total,detail=redirect_hits(db,'character','dorn7',[{'result':'miss','damage_total':0},{'result':'hit','damage_total':6}],'now')
            self.assertEqual(0,total);self.assertEqual(1,detail['images_remaining']);self.assertEqual(1,dice.call_count)

    def grid(self):
        from app.session_workspace import set_workspace_map,save_workspace_token
        from app.spatial_grid import init_spatial
        init_spatial(self.path)
        map_id=set_workspace_map(self.path,title='Teia fixture',image_path='fixture.svg',visible_to_players=True)['id']
        mine=save_workspace_token(self.path,token_type='character',character_id='dorn7',name='Dorn',map_id=map_id,latitude=20,longitude=20,visible_to_players=True)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET map_id=? WHERE id=?',(map_id,self.fixture.enemy['id']))
            db.execute("INSERT INTO session_workspace_map_grids VALUES(?,'square',20,20,1.5,0,0,'chebyshev',1,1)",(map_id,))
            for identity,x in [(mine['id'],4),(self.fixture.enemy['id'],5)]:
                db.execute('INSERT OR REPLACE INTO session_workspace_entity_positions VALUES(?,?,?,5,1,1,1)',(map_id,identity,x))
        return map_id,mine['id']

    def test_web_projects_penalties_only_in_area_and_expires(self):
        from app.dorn_spells import save,target
        map_id,mine=self.grid()
        result=self.cast('teia',targets=[{'type':'token','id':self.fixture.enemy['id']}])
        environmental=[e for e in result['effects'] if e.get('environmental')]
        self.assertEqual(1,len(environmental));self.assertEqual(-2,environmental[0]['modifiers']['armor_class_bonus'])
        from app.dice_rolls import parse_formula
        with closing(sqlite3.connect(self.path)) as db,patch('app.dorn_spells.roll_formula',side_effect=lambda formula:{'total':20+parse_formula(formula).modifier,'individual_results':[20]}):
            self.assertEqual(18,save(db,target(db,'token',self.fixture.enemy['id']),'dexterity')['total'])
            self.assertEqual(20,save(db,target(db,'token',self.fixture.enemy['id']),'constitution')['total'])
        state=readeffects(self.path)
        ended=effect_command(self.path,actor_id='master',actor_role='gm',request_id='web-time-fixture',expected_version=state['version'],action='dorn_spell_time',payload={'seconds':9000})
        self.assertFalse(any(e.get('environmental') for e in ended['effects']))

    def test_web_move_spends_three_times_only_inside_and_retry_is_safe(self):
        from app.spatial_grid import move_entity
        map_id,mine=self.grid()
        state=readeffects(self.path)
        effect_command(self.path,actor_id='master',actor_role='gm',request_id='web-fight-start',expected_version=state['version'],action='start',payload={'map_id':map_id,'battle_mode':True,'participants':[{'target_type':'character','target_id':'dorn7','name':'Dorn','initiative':20},{'target_type':'token','target_id':self.fixture.enemy['id'],'name':'Alvo','initiative':1}]})
        state=self.cast('teia',targets=[{'type':'token','id':self.fixture.enemy['id']}])
        args=dict(actor_id='master',role='gm',request_id='web-grid-move-once',map_id=map_id,token_id=mine,mode='COMBAT_MOVE',cells=[[4,5],[5,5]],expected_position_version=1,expected_grid_version=1,expected_combat_version=state['version'],load_movement=lambda _:9)
        first=move_entity(self.path,**args)
        self.assertEqual(4.5,first['movement']['spent_m']);self.assertEqual(first,move_entity(self.path,**args))

    def test_unknown_dispel_metadata_never_spends(self):
        from app.necromancer_spells import add_effect
        with closing(sqlite3.connect(self.path)) as db,db:
            effect=add_effect(db,{'type':'character','id':'dorn7'},'Desconhecido','fixture','now')
        with self.assertRaisesRegex(ValueError,'círculo'):
            self.cast('dissipar-magia',effect_id=effect['id'])
        with closing(sqlite3.connect(self.path)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
            self.assertEqual(1,next(r['current'] for r in state['resources'] if r['key']=='dorn_dissipar_magia'))
