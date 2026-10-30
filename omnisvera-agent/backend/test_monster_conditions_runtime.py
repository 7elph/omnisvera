import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_spell_engine as fixture
from app.monster_catalog import get_catalog_monster
from app.combat_effects import init_effects,effect_snapshot


class MonsterConditionRuntimeTests(unittest.TestCase):
    setUp=fixture.SpellEngineTests.setUp
    hp=fixture.SpellEngineTests.hp
    token_hp=fixture.SpellEngineTests.token_hp

    def setup_monster(self,identity):
        init_effects(self.db)
        monster=get_catalog_monster(identity)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=?,name=?,current_hp=100,maximum_hp=100 WHERE id='gob1'",(json.dumps({**monster,'source':{'monster_id':identity}}),monster['name']))
        return {'id':'gob1','name':monster['name'],'sheet':monster}

    def record(self,identity,attack=0):
        from app.monster_conditions import attack_contract
        self.setup_monster(identity)
        with closing(sqlite3.connect(self.db)) as db:
            contract=attack_contract(db,'gob1',str(attack))
        return {'actor_character_id':'gob1','attack_id':str(attack),'target_type':'character','target_id':'vezemir',
            'result':'hit','breakdown':{'monster_on_hit':contract,'strikes':[{'result':'hit','damage_total':1}]}}

    def effects(self):
        with closing(sqlite3.connect(self.db)) as db:return effect_snapshot(db)['effects']

    def test_paralysis_uses_exploration_clock_and_blocks_actions_without_retiring(self):
        from app.monster_conditions import apply_on_hit,assert_can_act
        from app.session6_rewards import vine_turn
        record=self.record('ghoul')
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}),patch('app.monster_conditions.roll_formula',return_value={'total':2,'individual_results':[2]}):
            apply_on_hit(db,record,'now')
            with self.assertRaisesRegex(ValueError,'Paralisia'):assert_can_act(db,'vezemir')
            self.assertFalse(vine_turn(db,{'target_type':'character','target_id':'vezemir','name':'Vezemir'},'now','paralysis-turn',{}))
        effect=self.effects()[0];self.assertEqual(effect['remaining_seconds'],1200)
        self.assertEqual(effect['source_duration_unit'],'turns')

    def test_native_confirmation_and_retry_apply_one_save_and_one_condition(self):
        from app.combat import monster_attack_definition,resolve_attack,confirm_attack_resolution
        actor=self.setup_monster('ghoul');definition=monster_attack_definition(actor,'0')
        result,_=resolve_attack(self.db,request_id='ghoul-native-attack',actor_character_id='gob1',actor_name=actor['name'],
            requested_by_id='master',requested_by_role='gm',definition=definition,inventory=[],attack_id='0',
            target={'type':'character','id':'vezemir','name':'Vezemir','armor_class':1,'current_hp':30},
            roll_mode='physical',physical_d20=15,rng=lambda a,b:1)
        with patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}) as save,patch('app.monster_conditions.roll_formula',return_value={'total':2,'individual_results':[2]}) as duration:
            first,_=confirm_attack_resolution(self.db,resolution_id=result['resolution_id'],requested_by_id='master',requested_by_role='gm')
            repeat,created=confirm_attack_resolution(self.db,resolution_id=result['resolution_id'],requested_by_id='master',requested_by_role='gm')
        self.assertFalse(created);self.assertEqual(first,repeat);self.assertEqual(len(self.effects()),1)
        save.assert_called_once();duration.assert_called_once()

    def test_elf_immunity_is_not_granted_to_half_elf(self):
        from app.monster_conditions import apply_on_hit
        record=self.record('ghoul')
        for race,expected in [('Elfo',0),('Meio-Elfo',1)]:
            with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}),patch('app.monster_conditions.roll_formula',return_value={'total':2,'individual_results':[2]}):
                db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='vezemir'",(json.dumps({'race':race}),))
                db.execute('DELETE FROM combat_effects')
                apply_on_hit(db,record,'now')
            self.assertEqual(len(self.effects()),expected)

    def test_successful_jp_and_miss_do_not_add_effects(self):
        from app.monster_conditions import apply_on_hit
        record=self.record('ghoul')
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spells.roll_formula',return_value={'total':30,'individual_results':[20]}):
            apply_on_hit(db,record,'now');record['result']='miss';record['breakdown']['strikes']=[{'result':'miss'}]
            apply_on_hit(db,record,'now')
        self.assertEqual(self.effects(),[])

    def test_poison_damage_is_separate_and_halved_by_save(self):
        from app.monster_conditions import apply_on_hit
        record=self.record('diabrete')
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spells.roll_formula',return_value={'total':30,'individual_results':[20]}),patch('app.monster_conditions.roll_formula',return_value={'total':6,'individual_results':[6]}):
            results=apply_on_hit(db,record,'now')
        self.assertEqual(self.hp(),27);self.assertEqual(results[0]['damage_dealt'],3)

    def test_poison_death_waits_for_actual_fictional_time_and_expires_once(self):
        from app.monster_conditions import apply_on_hit
        from app.dorn_spells import elapse
        record=self.record('cobra-venenosa')
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}),patch('app.monster_conditions.roll_formula',return_value={'total':1,'individual_results':[1]}):
            apply_on_hit(db,record,'now');changes=[]
            elapse(db,effect_snapshot(db),599,changes);self.assertEqual(self.hp(),30)
            elapse(db,effect_snapshot(db),1,changes)
            elapse(db,effect_snapshot(db),1,changes)
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='monster_condition_expiry'").fetchone()[0],1)
        self.assertLessEqual(self.hp(),0);self.assertEqual(self.effects(),[])

    def test_reflected_hit_has_no_save_or_condition(self):
        from app.monster_conditions import apply_on_hit
        record=self.record('ghoul');record['breakdown']['reflection_result']={'rolls':[{'strike':0,'intercepted':True}]}
        with closing(sqlite3.connect(self.db)) as db,patch('app.dorn_spells.save') as saving:
            self.assertEqual(apply_on_hit(db,record,'now'),[])
        saving.assert_not_called()

    def test_changed_source_contract_rejects_confirmation_before_hp_changes(self):
        from app.monster_conditions import validate_confirm
        record=self.record('ghoul')
        with closing(sqlite3.connect(self.db)) as db,db:
            sheet=json.loads(db.execute("SELECT sheet_json FROM session_workspace_tokens WHERE id='gob1'").fetchone()[0])
            sheet['abilities']=[];db.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob1'",(json.dumps(sheet),))
            with self.assertRaisesRegex(ValueError,'mudaram'):validate_confirm(db,record)
        self.assertEqual(self.hp(),30);self.assertEqual(self.effects(),[])

    def test_petrification_is_permanent_until_removal_and_full_rest_clears_it(self):
        from app.monster_conditions import apply_on_hit,public_effect
        from app.combat_effects import expire_rest_effects
        record=self.record('cocatriz')
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spells.save',return_value={'success':False}):
            apply_on_hit(db,record,'now')
            effect=effect_snapshot(db)['effects'][0]
            self.assertEqual(effect['duration'],'manual');self.assertTrue(effect['blocks_actions'])
            self.assertNotIn('source_token_id',public_effect(effect));self.assertNotIn('rider_id',public_effect(effect))
            expire_rest_effects(db,'vezemir',complete=True)
        self.assertEqual(self.effects(),[])

    def test_dorn_is_immune_to_common_poison_and_cocatriz_to_petrification(self):
        from app.monster_conditions import _immune
        from app.monster_riders import rider_specs
        self.setup_monster('cocatriz')
        with closing(sqlite3.connect(self.db)) as db,patch('app.construct_rules.is_construct',return_value=True):
            self.assertIsNotNone(_immune(db,'character','vezemir',rider_specs(get_catalog_monster('cobra-venenosa'))['on_hit'][0]))
            self.assertIsNotNone(_immune(db,'token','gob1',rider_specs(get_catalog_monster('cocatriz'))['on_hit'][0]))

    def test_hidden_map_or_fog_never_makes_condition_source_public(self):
        from app.monster_runtime import public_token
        from app.session_workspace import _token_fog_cell
        self.setup_monster('ghoul')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("INSERT INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES('test-map','Test','x',0,'now','now')")
            db.execute("UPDATE session_workspace_tokens SET map_id='test-map',latitude=50,longitude=50,visible_to_players=1 WHERE id='gob1'")
            self.assertFalse(public_token(db,'gob1'))
            db.execute("UPDATE session_workspace_maps SET visible_to_players=1 WHERE id='test-map'")
            self.assertTrue(public_token(db,'gob1'))
            db.execute("INSERT INTO session_workspace_map_fog VALUES('test-map','battle',1,'[]',?,'now')",(json.dumps({_token_fog_cell(50,50):1}),))
            self.assertFalse(public_token(db,'gob1'))

    def test_session_closure_does_not_cure_and_incapacity_keeps_initiative(self):
        from app.monster_conditions import apply_on_hit
        from app.combat_effects import expire_session_effects
        from app.battle_mode import retire_defeated
        record=self.record('ghoul')
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spells.save',return_value={'success':False}),patch('app.monster_conditions.roll_formula',return_value={'total':1}):
            apply_on_hit(db,record,'now')
            battle={'active':True,'participants':[{'target_type':'character','target_id':'vezemir','name':'Vezemir'}],'turn_index':0}
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(battle),))
            self.assertEqual(retire_defeated(db,'now'),[])
            db.execute('CREATE TABLE IF NOT EXISTS game_sessions(id INTEGER PRIMARY KEY,status TEXT)')
            expire_session_effects(db,1,'now',current_session=True)
            self.assertEqual(len(effect_snapshot(db)['effects']),1)

    def test_end_combat_keeps_bodily_conditions(self):
        from app.monster_conditions import apply_on_hit
        from app.combat_effects import effect_command
        record=self.record('ghoul')
        with closing(sqlite3.connect(self.db)) as db,db,patch('app.dorn_spells.save',return_value={'success':False}),patch('app.monster_conditions.roll_formula',return_value={'total':1}):
            apply_on_hit(db,record,'now')
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps({'active':True,'participants':[{'target_type':'character','target_id':'vezemir','name':'Vezemir'}],'turn_index':0}),))
            version=effect_snapshot(db)['version']
        result=effect_command(self.db,actor_id='master',actor_role='gm',request_id='end-paralysis-test',expected_version=version,action='end',payload={})
        self.assertFalse(result['encounter']['active']);self.assertEqual(len(result['effects']),1)
