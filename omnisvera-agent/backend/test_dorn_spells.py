import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch
import test_dorn_mage as fixture
from app.dorn_mage import apply_dorn_mage
from app.combat_effects import effect_command,readeffects,apply_definition_effects
from app.session_workspace import save_workspace_token
from app.dice_rolls import init_dice_rolls
from app.session_ledger import init_session_ledger

class DornSpellTests(TestCase):
    def setUp(self):
        self.base=fixture.DornMageTests(); self.base.setUp(); self.addCleanup(self.base.doCleanups)
        self.db=self.base.db; apply_dorn_mage(self.db); init_dice_rolls(self.db); init_session_ledger(self.db)
        self.enemy=save_workspace_token(self.db,token_type='monster',name='Alvo fixture',latitude=50,longitude=50,current_hp=50,maximum_hp=50,sheet={'armor_class':12,'saving_throw':20})
        self.count=0
    def command(self,action='dorn_spell_cast',**payload):
        self.count+=1
        return effect_command(self.db,actor_id='master',actor_role='gm',request_id=f'spell-fixture-{self.count}',expected_version=readeffects(self.db)['version'],action=action,payload=payload)
    def args(self,spell):
        return dict(spell_id=spell,targets=[{'type':'token','id':self.enemy['id']}],position_confirmed=True,distance_meters=10,weight_kg=100,shape='line')
    def resource(self,spell):
        with closing(sqlite3.connect(self.db)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
            return next(r['current'] for r in state['resources'] if r['key']=='dorn_'+spell)
    def test_lightning_real_damage_half_and_replay(self):
        payload=self.args('relampago'); version=readeffects(self.db)['version']
        kwargs=dict(actor_id='master',actor_role='gm',request_id='lightning-repeat',expected_version=version,action='dorn_spell_cast',payload=payload)
        with patch('app.dorn_spells.roll_formula',side_effect=lambda formula: {'total':9 if formula=='3d6' else 20,'individual_results':[3,3,3] if formula=='3d6' else [20]}):
            result=effect_command(self.db,**kwargs)
        self.assertEqual(4,result['protocol_result']['results'][0]['damage'])
        self.assertEqual(46,result['protocol_result']['results'][0]['hp_after'])
        self.assertEqual(result,effect_command(self.db,**kwargs)); self.assertEqual(0,self.resource('relampago'))
    def test_failed_save_takes_full_damage(self):
        with patch('app.dorn_spells.roll_formula',side_effect=lambda formula:{'total':12 if formula=='3d6' else 1,'individual_results':[1]}):
            result=self.command(**self.args('relampago'))
        self.assertEqual(12,result['protocol_result']['results'][0]['damage'])

    def grid_lightning(self):
        from app.spatial_grid import configure_grid
        with closing(sqlite3.connect(self.db)) as db:
            map_id=db.execute('SELECT map_id FROM session_workspace_tokens WHERE id=?',(self.enemy['id'],)).fetchone()[0]
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT OR IGNORE INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES(?, 'Fixture','fixture.svg',1,'now','now')",(map_id,))
        save_workspace_token(self.db,token_type='character',name='Dorn',character_id='dorn7',map_id=map_id,latitude=0,longitude=0)
        configure_grid(self.db,actor_id='master',role='gm',request_id='lightning-grid',map_id=map_id,config=dict(cols=100,rows=20,cell_size_m=1.5))
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=0,cell_y=0 WHERE token_id IN (SELECT id FROM session_workspace_tokens WHERE character_id='dorn7')")
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=4,cell_y=0 WHERE token_id=?',(self.enemy['id'],))
        return map_id

    def test_grid_lightning_one_to_three_targets_auto_validates_and_replays(self):
        map_id=self.grid_lightning()
        targets=[self.enemy['id']]+[save_workspace_token(self.db,token_type='monster',map_id=map_id,name=f'Alvo {n}',latitude=0,longitude=6+n,current_hp=50,maximum_hp=50,sheet={'armor_class':12,'saving_throw':20})['id'] for n in (1,2)]
        payload={'spell_id':'relampago','grid_selection':True,'targets':[{'type':'token','id':i} for i in targets]}
        kwargs=dict(actor_id='master',actor_role='gm',request_id='grid-lightning-retry',expected_version=readeffects(self.db)['version'],action='dorn_spell_cast',payload=payload)
        with patch('app.dorn_spells.roll_formula',side_effect=lambda formula:{'total':12 if formula=='3d6' else 1,'individual_results':[4,4,4] if formula=='3d6' else [1]}) as roll:
            result=effect_command(self.db,**kwargs)
        self.assertEqual([4]*3,[t['damage'] for t in result['protocol_result']['results']])
        self.assertEqual(4,roll.call_count)
        self.assertEqual(result,effect_command(self.db,**kwargs));self.assertEqual(0,self.resource('relampago'))
        self.assertEqual([4,4,4],result['protocol_result']['damage_roll']['individual_results'])

    def test_grid_lightning_rejects_far_or_four_targets_without_damage_or_cost(self):
        map_id=self.grid_lightning()
        far=save_workspace_token(self.db,token_type='monster',map_id=map_id,name='Distante',latitude=0,longitude=80,current_hp=50,maximum_hp=50,sheet={'armor_class':12,'saving_throw':20})
        payload={'spell_id':'relampago','grid_selection':True,'targets':[{'type':'token','id':self.enemy['id']},{'type':'token','id':far['id']}]}
        with self.assertRaisesRegex(ValueError,'alcance'):self.command(**payload)
        others=[save_workspace_token(self.db,token_type='monster',map_id=map_id,name=f'Alvo {i}',latitude=0,longitude=10+i,current_hp=50,maximum_hp=50,sheet={'armor_class':12,'saving_throw':20})['id'] for i in range(3)]
        payload['targets']=[{'type':'token','id':i} for i in [self.enemy['id'],*others]]
        with self.assertRaisesRegex(ValueError,'3 alvos'):self.command(**payload)
        self.assertEqual(1,self.resource('relampago'))
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(50,db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(self.enemy['id'],)).fetchone()[0])
    def test_lightning_ignores_legacy_multiple_contacts_and_uses_one_save(self):
        args=self.args('relampago'); args['targets'][0]['contacts']=2
        with patch('app.dorn_spells.roll_formula',side_effect=[{'total':12,'individual_results':[4,4,4]},{'total':20,'individual_results':[20]},{'total':1,'individual_results':[1]}]):
            result=self.command(**args)['protocol_result']['results'][0]
        self.assertEqual(1,len(result['contact_saves'])); self.assertEqual(6,result['damage']); self.assertEqual(44,result['hp_after'])
    def test_exploration_time_reopens_vertical_budget_and_ticks_instability(self):
        effect=self.command(**self.args('levitacao'))['effects'][0]
        self.command('dorn_levitate_move',effect_id=effect['id'],vertical_meters=2)
        with self.assertRaises(ValueError):self.command('dorn_levitate_move',effect_id=effect['id'],vertical_meters=2)
        effect=self.command('dorn_spell_time',seconds=10)['effects'][0]
        self.assertEqual(4,self.command('dorn_levitate_move',effect_id=effect['id'],vertical_meters=2)['effects'][0]['altitude_meters'])
        effect['ranged_attack_round']=readeffects(self.db)['round']
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),effect['id']))
        self.assertEqual(-2,self.command('round')['effects'][0]['levitation_ranged_penalty'])
    def test_invalid_late_target_rolls_back_everything(self):
        second=save_workspace_token(self.db,token_type='monster',name='Sem JP',latitude=10,longitude=10,current_hp=10,maximum_hp=10,sheet={})
        args=self.args('relampago'); args['targets'].append({'type':'token','id':second['id']})
        with self.assertRaises(ValueError): self.command(**args)
        self.assertEqual(1,self.resource('relampago'))
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(50,db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(self.enemy['id'],)).fetchone()[0])
    def test_levitation_limits_duration_vertical_and_expiration(self):
        args=self.args('levitacao'); args['weight_kg']=151
        with self.assertRaises(ValueError): self.command(**args)
        args['weight_kg']=150
        result=self.command(**args); effect=result['protocol_result']['results'][0]['effect']
        self.assertEqual(1800,effect['remaining_seconds'])
        with self.assertRaises(ValueError):self.command('dorn_levitate_move',effect_id=effect['id'],vertical_meters=3)
        moved=self.command('dorn_levitate_move',effect_id=effect['id'],vertical_meters=2)
        self.assertEqual(2,moved['protocol_result']['effect']['altitude_meters'])
        self.assertFalse(self.command('dorn_spell_time',seconds=1800)['effects'])
    def test_unwilling_levitation_jpc_resists_but_consumes(self):
        with patch('app.dorn_spells.roll_formula',return_value={'total':20,'individual_results':[20]}):
            result=self.command(**{**self.args('levitacao'),'unwilling':True})
        self.assertIsNone(result['protocol_result']['results'][0]['effect']); self.assertEqual(0,self.resource('levitacao'))
    def test_darkness_uses_approved_three_target_turn_restraint(self):
        result=self.command(**self.args('escuridao')); effect=result['effects'][0]
        self.assertEqual((3,4.5,True),(effect['turns_remaining'],effect['radius_meters'],effect['immobilized']))
        self.assertEqual(3,self.command('round')['effects'][0]['turns_remaining'])
        self.command('start',participants=[{'target_type':'character','target_id':'dorn7','name':'Dorn','initiative':20},{'target_type':'token','target_id':self.enemy['id'],'name':'Alvo','initiative':10}])
        with patch('app.session6_rewards.random.randint',return_value=1) as roll:
            for index in range(3):
                state=self.command('next_turn')
                self.assertEqual('dorn7',state['encounter']['participants'][state['encounter']['turn_index']]['target_id'])
                self.assertEqual(len(state['effects']),1 if index<2 else 0)
            self.assertEqual(3,roll.call_count)
    def test_darkness_no_longer_applies_old_blindness_penalties(self):
        effect=self.command(**self.args('escuridao'))['effects'][0]
        definition=apply_definition_effects({'attacks':[{'id':'melee','attack_bonus':3}],'defenses':{'saving_throw_bonus':1}},[effect,effect])
        self.assertEqual(3,definition['attacks'][0]['attack_bonus'])
        self.assertEqual(1,definition['defenses']['saving_throw_bonus'])
        self.assertFalse(definition.get('vision_blocked'))

    def test_existing_darkness_is_upgraded_once_without_resource_or_hp_changes(self):
        from app.dorn_spells import upgrade_darkness_restraints
        effect=self.command(**self.args('escuridao'))['effects'][0]
        legacy={**effect,'condition':'magical_darkness','duration':'fictional_time','remaining_seconds':630,'modifiers':{'attack_bonus':-5}}
        for key in ('immobilized','turns_remaining','saving_throw','saving_throw_bonus'):legacy.pop(key,None)
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(legacy),effect['id']))
        remaining=self.resource('escuridao');self.assertEqual([effect['id']],upgrade_darkness_restraints(self.db));self.assertEqual([],upgrade_darkness_restraints(self.db))
        new=readeffects(self.db)['effects'][0];self.assertEqual(3,new['turns_remaining']);self.assertEqual({},new['modifiers']);self.assertNotIn('condition',new);self.assertEqual(remaining,self.resource('escuridao'))
    def test_duplicate_character_and_pin_are_refused_before_consumption(self):
        args=self.args('relampago'); args['targets']=[{'type':'character','id':'dorn7'},{'type':'character','id':'dorn7'}]
        with self.assertRaises(ValueError):self.command(**args)
        self.assertEqual(1,self.resource('relampago'))
    def test_levitation_ranged_penalty_and_stabilization(self):
        effect=self.command(**self.args('levitacao'))['effects'][0]
        effect['levitation_ranged_penalty']=-4
        definition=apply_definition_effects({'attacks':[{'id':'ranged','attack_bonus':3},{'id':'melee','attack_bonus':3}]},[effect])
        self.assertEqual([-1,3],[a['attack_bonus'] for a in definition['attacks']])
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),effect['id']))
        result=self.command('dorn_levitate_stabilize',effect_id=effect['id'])
        self.assertEqual(-1,result['protocol_result']['effect']['levitation_ranged_penalty'])
    def test_player_cannot_cast_or_advance_time(self):
        for action in ('dorn_spell_cast','dorn_spell_time','dorn_levitate_move','dorn_spell_end'):
            with self.assertRaises(PermissionError):effect_command(self.db,actor_id='morthak',actor_role='player',request_id='not-authorized',expected_version=0,action=action,payload={},allow_player=True)
    def test_budget_turn_and_spent_resource(self):
        self.command('start',participants=[{'target_type':'character','target_id':'dorn7','name':'Dorn','initiative':20},{'target_type':'token','target_id':self.enemy['id'],'name':'Alvo','initiative':10}])
        result=self.command(**self.args('levitacao')); self.assertTrue(result['encounter']['action_committed'])
        with self.assertRaises(ValueError):self.command(**self.args('escuridao'))
        self.command('next_turn')
        with self.assertRaises(ValueError):self.command(**self.args('escuridao'))
    def test_self_lightning_does_not_restore_own_hp(self):
        args=self.args('relampago'); args['targets']=[{'type':'character','id':'dorn7'}]
        with patch('app.dorn_spells.roll_formula',side_effect=lambda formula:{'total':6 if formula=='3d6' else 1,'individual_results':[1]}):self.command(**args)
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(14,json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])['current_hp'])
