import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_battle_mode as fixtures
from app.combat_effects import change_hp,effect_snapshot


class ApprovedCombatSkillTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.BattleModeTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.path=self.fixture.db
        from app.combat_effects import init_effects
        init_effects(self.path)
        with closing(sqlite3.connect(self.path)) as db,db:
            state={'current_hp':20,'maximum_hp':20,'temporary_hp':0,'resources':[{'key':name,'current':1,'maximum':1,'recharge':'inn_rest'} for name in ['frenesi','provocacao']]}
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))

    def test_auto_frenzy_does_not_spend_manual_cast_and_survives_negative_hp(self):
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.vezemir_skills.roll_formula',return_value={'total':3}):
            change_hp(db,'character','vezemir',-11,'now')
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(1,state['resources'][0]['current'])
            self.assertTrue(state['daily_skill_flags']['frenesi_auto_used'])
            change=change_hp(db,'character','vezemir',-12,'now')
            self.assertEqual(-3,change['hp_after'])
            from app.battle_mode import require_actor_alive
            require_actor_alive(db,'vezemir')

    def test_lifeline_cannot_survive_minus_ten(self):
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.vezemir_skills.roll_formula',return_value={'total':3}):
            change_hp(db,'character','vezemir',-11,'now')
            result=change_hp(db,'character','vezemir',-19,'now')
            self.assertEqual(-10,result['hp_after'])
            from app.battle_mode import require_actor_alive
            with self.assertRaises(ValueError):require_actor_alive(db,'vezemir')

    def test_provocation_enforces_target_after_failed_jp_and_retry_is_safe(self):
        from app.vezemir_skills import target_allowed
        from app.spatial_grid import init_spatial
        init_spatial(self.path)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("INSERT INTO session_workspace_map_grids VALUES('arena','square',20,20,1.5,0,0,'chebyshev',1,1)")
            db.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?",(json.dumps({'armor_class':10,'saving_throw':20}),self.fixture.enemy['id']))
        self.fixture.start()
        with closing(sqlite3.connect(self.path)) as db,db:
            for index,(identity,) in enumerate(db.execute("SELECT id FROM session_workspace_tokens WHERE map_id='arena'").fetchall()):
                db.execute("INSERT OR REPLACE INTO session_workspace_entity_positions VALUES('arena',?,?,4,1,1,1)",(identity,4+index))
        with patch('app.vezemir_skills.roll_formula',return_value={'total':1}):self.fixture.command('vezemir_skill',skill='provocacao')
        with patch('app.vezemir_skills.roll_formula',return_value={'total':1}):self.fixture.command('next_turn')
        with closing(sqlite3.connect(self.path)) as db:
            self.assertTrue(target_allowed(db,self.fixture.enemy['id'],'character','vezemir'))
            self.assertFalse(target_allowed(db,self.fixture.enemy['id'],'character','morthak'))

    def test_touch_tick_kills_once_and_cannot_loop_on_an_existing_corpse(self):
        from app.necromancer_spells import add_effect,touch_turn
        participant={'target_type':'token','target_id':self.fixture.enemy['id'],'name':'Alvo'}
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.necromancer_spells.roll_formula',return_value={'total':1}):
            db.execute('UPDATE session_workspace_tokens SET current_hp=1 WHERE id=?',(participant['target_id'],))
            add_effect(db,{'type':'token','id':participant['target_id']},'Toque Sombrio','Morthak','now',dot_hp=True)
            self.assertTrue(touch_turn(db,participant,'now','tick-test-one'))
            self.assertFalse(touch_turn(db,participant,'now','tick-test-two'))
            self.assertEqual(0,db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(participant['target_id'],)).fetchone()[0])

    def test_fear_uses_individual_completed_turns(self):
        from app.necromancer_spells import add_effect,finish_target_turn
        participant={'target_type':'token','target_id':self.fixture.enemy['id']}
        with closing(sqlite3.connect(self.path)) as db,db:
            effect=add_effect(db,{'type':'token','id':participant['target_id']},'Aterrorizar','Morthak','now',target_turn_duration=True,turns_remaining=2)
            finish_target_turn(db,participant)
            self.assertEqual(1,json.loads(db.execute('SELECT data_json FROM combat_effects WHERE id=?',(effect['id'],)).fetchone()[0])['turns_remaining'])
            finish_target_turn(db,participant)
            self.assertEqual(0,db.execute('SELECT active FROM combat_effects WHERE id=?',(effect['id'],)).fetchone()[0])

    def test_native_turn_tick_retry_preserves_order_and_rolls_once(self):
        from app.necromancer_spells import add_effect
        from app.combat_effects import effect_command,readeffects
        self.fixture.start()
        victim=self.fixture.enemy['id']
        with closing(sqlite3.connect(self.path)) as db,db:
            add_effect(db,{'type':'token','id':victim},'Toque Sombrio','Morthak','now',dot_hp=True)
        state=readeffects(self.path)
        args=dict(actor_id='master',actor_role='gm',request_id='native-touch-turn-once',expected_version=state['version'],action='next_turn',payload={})
        with patch('app.necromancer_spells.roll_formula',return_value={'total':1}) as roll:
            first=effect_command(self.path,**args)
            self.assertEqual(first,effect_command(self.path,**args))
            self.assertEqual(1,roll.call_count)
        self.assertEqual(victim,first['encounter']['participants'][first['encounter']['turn_index']]['target_id'])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(17,db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(victim,)).fetchone()[0])
            self.assertEqual(1,db.execute("SELECT count(*) FROM session_ledger WHERE source_type='touch_dot'").fetchone()[0])

    def test_native_dot_death_skips_victim_without_infinite_loop(self):
        from app.necromancer_spells import add_effect
        self.fixture.start()
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=1 WHERE id=?',(self.fixture.enemy['id'],))
            add_effect(db,{'type':'token','id':self.fixture.enemy['id']},'Toque Sombrio','Morthak','now',dot_hp=True)
        with patch('app.necromancer_spells.roll_formula',return_value={'total':1}) as roll:
            result=self.fixture.command('next_turn')
            self.assertEqual(1,roll.call_count)
        self.assertEqual(['vezemir'],[p['target_id'] for p in result['encounter']['participants']])
        self.assertEqual(0,result['encounter']['turn_index'])
        self.assertFalse(any(e.get('dot_hp') for e in result['effects']))

    def test_rejected_turn_does_not_age_fear(self):
        from app.necromancer_spells import add_effect
        from app.combat_effects import effect_command,readeffects
        self.fixture.start()
        with closing(sqlite3.connect(self.path)) as db,db:
            effect=add_effect(db,{'type':'character','id':'vezemir'},'Aterrorizar','Morthak','now',necro_spell='aterrorrizar',target_turn_duration=True,turns_remaining=2)
        state=readeffects(self.path)
        with self.assertRaises(PermissionError):
            effect_command(self.path,actor_id='morthak',actor_role='player',request_id='wrong-owner-next-turn',expected_version=state['version'],action='next_turn',payload={'actor':{'target_type':'character','target_id':'morthak'}},allow_player=True)
        current=next(e for e in readeffects(self.path)['effects'] if e['id']==effect['id'])
        self.assertEqual(2,current['turns_remaining'])

    def test_end_combat_removes_dot_and_individual_fear(self):
        from app.necromancer_spells import add_effect
        self.fixture.start()
        with closing(sqlite3.connect(self.path)) as db,db:
            for data in [{'dot_hp':True},{'necro_spell':'aterrorrizar','target_turn_duration':True,'turns_remaining':6}]:
                add_effect(db,{'type':'token','id':self.fixture.enemy['id']},'Necromante','Morthak','now',**data)
        self.assertEqual([],self.fixture.command('end')['effects'])

    def test_automatic_fear_grid_selection_and_same_payload_retry(self):
        from app.combat_effects import effect_command,readeffects
        from app.spatial_grid import init_spatial
        init_spatial(self.path)
        self.fixture.base._insert_character('morthak',10,10)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("INSERT OR REPLACE INTO character_definition_overrides VALUES('morthak',?,'now')",(json.dumps({'level':5,'specialization':'necromante'}),))
            state={'current_hp':10,'maximum_hp':10,'resources':[{'key':'aterrorrizar','current':1,'maximum':1}]}
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='morthak'",(json.dumps(state),))
            db.execute('UPDATE session_workspace_tokens SET sheet_json=?,visible_to_players=1 WHERE id=?',(json.dumps({'armor_class':10,'saving_throw':99,'hit_dice':1,'attributes':{'wisdom':10}}),self.fixture.enemy['id']))
            db.execute("INSERT INTO session_workspace_map_grids VALUES('arena','square',20,20,1.5,0,0,'chebyshev',1,1)")
        self.fixture.command('start',map_id='arena',battle_mode=True,participants=[{'target_type':'character','target_id':'morthak','name':'Morthak','initiative':20},{'target_type':'token','target_id':self.fixture.enemy['id'],'name':'Alvo','initiative':10}])
        with closing(sqlite3.connect(self.path)) as db,db:
            for index,(identity,) in enumerate(db.execute("SELECT id FROM session_workspace_tokens WHERE map_id='arena'").fetchall()):
                db.execute("INSERT OR REPLACE INTO session_workspace_entity_positions VALUES('arena',?,?,4,1,1,1)",(identity,4+index))
        before=readeffects(self.path);payload={'spell_id':'aterrorizar','targets':[]}
        request=dict(actor_id='morthak',actor_role='player',allow_player=True,request_id='automatic-grid-fear-once',expected_version=before['version'],action='necro_spell_cast',payload=payload)
        with patch('app.necromancer_spells.roll_formula',return_value={'total':1,'individual_results':[1]}) as roll:
            result=effect_command(self.path,**request)
            self.assertEqual(result,effect_command(self.path,**request))
            self.assertEqual(2,roll.call_count)  # duração e uma JPS, nunca novamente no retry
        self.assertEqual({'spell_id':'aterrorizar','targets':[]},payload)
        self.assertEqual('grid',result['protocol_result']['position'])
        self.assertEqual(6,result['effects'][0]['turns_remaining'])

    def test_fear_penalty_is_d20_not_attribute_score(self):
        from app.combat_effects import apply_definition_effects
        from app.dice_rolls import resolve_character_roll
        base={'name':'Alvo','attributes':{'strength':14},'base_attributes':{'strength':14},'attribute_modifiers':{'strength':2},'attacks':[{'id':'melee','attack_bonus':5}], 'defenses':{'saving_throw':15,'initiative':3},'item_effects':{'skill_modifiers':{'perceber':4}}}
        result=apply_definition_effects(base,[{'id':'fear-test','necro_spell':'aterrorrizar','difficult_tests':True,'modifiers':{}}])
        self.assertEqual(14,result['attributes']['strength'])
        self.assertEqual('1d20',resolve_character_roll(result,[],'attribute','strength').formula)
        self.assertEqual('1d20-2',resolve_character_roll(result,[],'saving_throw',None).formula)
        self.assertEqual('1d20+2',resolve_character_roll(result,[],'skill','perceber').formula)
        self.assertEqual(3,result['attacks'][0]['attack_bonus']);self.assertEqual(1,result['defenses']['initiative'])

    def test_manual_frenzy_after_auto_cannot_reuse_daily_lifeline(self):
        from app.vezemir_skills import start_frenzy
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.vezemir_skills.roll_formula',return_value={'total':2}):
            change_hp(db,'character','vezemir',-11,'now')
            change_hp(db,'character','vezemir',-10,'now')  # actually consumes the conditional lifeline
            db.execute("UPDATE combat_effects SET active=0 WHERE json_extract(data_json,'$.skill')='frenesi'")
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            second=start_frenzy(db,state,'now')
            self.assertFalse(second['defy_death']);self.assertFalse(second['automatic'])
            self.assertEqual(0,state['resources'][0]['current'])
            with self.assertRaisesRegex(ValueError,'ativo'):start_frenzy(db,state,'now')

    def test_frenzy_expiry_retires_negative_hp_actor_and_preserves_daily_flag(self):
        from app.vezemir_skills import add_effect
        self.fixture.start()
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.vezemir_skills.roll_formula',return_value={'total':2}):
            change_hp(db,'character','vezemir',-11,'now');change_hp(db,'character','vezemir',-12,'now')
            db.execute("UPDATE combat_effects SET data_json=json_set(data_json,'$.rounds',1) WHERE json_extract(data_json,'$.skill')='frenesi'")
        result=self.fixture.command('round')
        self.assertFalse(any(p['target_id']=='vezemir' for p in result['encounter']['participants']))
        with closing(sqlite3.connect(self.path)) as db:
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
            self.assertEqual(0,state['current_hp']);self.assertTrue(state['daily_skill_flags']['frenesi_lifeline_used'])

    def test_taunted_kill_refunds_once_only_under_frenzy(self):
        from app.vezemir_skills import add_effect,kill_reward
        with closing(sqlite3.connect(self.path)) as db,db,patch('app.vezemir_skills.roll_formula',return_value={'total':2}):
            state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0]);state['resources'][1]['current']=0
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='vezemir'",(json.dumps(state),))
            add_effect(db,'token',self.fixture.enemy['id'],'Provocação','now',skill='provocacao',failed=True)
            kill_reward(db,'vezemir','token',self.fixture.enemy['id'],'now')
            self.assertEqual(0,json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])['resources'][1]['current'])
            change_hp(db,'character','vezemir',-11,'now')
            for _ in range(2):kill_reward(db,'vezemir','token',self.fixture.enemy['id'],'now')
            self.assertEqual(1,json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])['resources'][1]['current'])
            self.assertEqual(1,db.execute("SELECT count(*) FROM session_ledger WHERE source_type='provocation_refund'").fetchone()[0])
