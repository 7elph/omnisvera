"""Native monster actions must remain deterministic and fixture-only in tests."""
import unittest
import json
import sqlite3
from contextlib import closing
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
import test_spell_engine as fixture


class MonsterRuntimeContractTests(unittest.TestCase):
    def test_six_source_complete_breaths_keep_their_own_damage_and_element(self):
        from app.monster_runtime import breath_contract
        from app.monster_catalog import get_catalog_monster
        for name,formula,kind in [('azul','9d8','lightning'),('branco','6d6','cold'),
                                  ('dourado','11d10','fire'),('negro','7d4','acid'),
                                  ('verde','8d6','poison'),('vermelho','10d10','fire')]:
            with self.subTest(name=name):
                contract=breath_contract(get_catalog_monster('dragao-'+name),'Baforada')
                self.assertEqual((contract['execution_status'],contract['damage_formula'],contract['damage_type']),('native',formula,kind))
                self.assertEqual(contract['uses'],{'maximum':3,'recharge':'day'})

    def test_metric_area_rotates_and_does_not_invent_line_width(self):
        from app.monster_runtime import _inside
        origin={'x':0,'y':0};aim={'x':1,'y':1}
        cone={'shape':'cone','depth_m':27,'width_m':9}
        self.assertTrue(_inside(origin,aim,{'x':10,'y':10},cone))
        self.assertFalse(_inside(origin,aim,{'x':10,'y':15},cone))
        self.assertFalse(_inside(origin,aim,{'x':-1,'y':-1},cone))
        line={'shape':'line','depth_m':30}
        self.assertTrue(_inside(origin,aim,{'x':2,'y':2},line))
        self.assertFalse(_inside(origin,aim,{'x':2,'y':2.01},line))
        cloud={'shape':'cloud','depth_m':15,'width_m':12}
        self.assertTrue(_inside(origin,{'x':1,'y':0},{'x':10,'y':6},cloud))
        self.assertFalse(_inside(origin,{'x':1,'y':0},{'x':10,'y':6.1},cloud))

    def test_quantified_damage_passives_apply_integer_rounding_only_to_their_type(self):
        from app.monster_runtime import damage_response
        for key,factor,expected in [('damage_resistances',.5,5),('damage_vulnerabilities',2,22)]:
            with self.subTest(key=key),patch('app.monster_runtime.passive_data',return_value={key:[{'type':'fire','factor':factor}]}):
                self.assertEqual(damage_response(None,'token','fixture',11,'fire'),expected)
                self.assertEqual(damage_response(None,'token','fixture',11,'cold'),11)

    def test_gold_dragon_breath_binds_native_executor(self):
        from app.monster_runtime import breath_contract
        from app.monster_catalog import get_catalog_monster
        contract = breath_contract(get_catalog_monster('dragao-dourado'), 'Baforada')
        self.assertEqual(contract['damage_formula'], '11d10')
        self.assertEqual(contract['uses']['maximum'], 3)
        self.assertEqual(contract['geometry']['depth_m'], 27)
        self.assertEqual(contract['execution_status'], 'native')

    def test_black_dragon_explicitly_has_no_lingering_acid_damage(self):
        from app.monster_runtime import breath_contract
        from app.monster_catalog import get_catalog_monster
        contract=breath_contract(get_catalog_monster('dragao-negro'),'Baforada')
        self.assertEqual(contract['execution_status'],'native')
        self.assertEqual(contract['damage_type'],'acid')
        self.assertEqual(contract['damage_formula'],'7d4')


class MonsterRuntimeTests(unittest.TestCase):
    hp=fixture.SpellEngineTests.hp
    token_hp=fixture.SpellEngineTests.token_hp

    def setUp(self):
        fixture.SpellEngineTests.setUp(self)
        from app.combat_effects import init_effects
        from app.spatial_grid import configure_grid
        from app.session_workspace import set_workspace_map
        from app.monster_catalog import get_catalog_monster
        init_effects(self.db)
        self.map=set_workspace_map(self.db,title='Ensaio baforada',image_path='fixture.svg',visible_to_players=True)['id']
        gold=get_catalog_monster('dragao-dourado')
        sheet={**gold,'source':{'monster_id':'dragao-dourado'}}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=?,current_hp=66,maximum_hp=66,visible_to_players=1 WHERE id='gob1'",(json.dumps(sheet),))
            db.execute("INSERT INTO session_workspace_tokens(id,token_type,name,character_id,current_hp,maximum_hp,visible_to_players,created_at,updated_at) VALUES('vez-pin','character','Vezemir','vezemir',30,30,1,'now','now')")
            db.execute("INSERT INTO session_workspace_tokens(id,token_type,name,current_hp,maximum_hp,sheet_json,visible_to_players,created_at,updated_at) VALUES('other','monster','Aliado do dragão',1000,1000,?,1,'now','now')",(json.dumps({'saving_throw':10}),))
        with closing(sqlite3.connect(self.db)) as db,db:db.execute('UPDATE session_workspace_tokens SET map_id=?',(self.map,))
        configure_grid(self.db,actor_id='master',role='gm',request_id='monster-test-grid',map_id=self.map,config={'cols':40,'rows':40,'cell_size_m':1.5})
        with closing(sqlite3.connect(self.db)) as db,db:
            for pin,x,y in [('gob1',4,4),('vez-pin',8,4),('other',12,4)]:
                db.execute('UPDATE session_workspace_entity_positions SET cell_x=?,cell_y=? WHERE token_id=?',(x,y,pin))
            members=[{'target_type':'token','target_id':'gob1'},{'target_type':'character','target_id':'vezemir'},{'target_type':'token','target_id':'other'}]
            encounter={'active':True,'battle_mode':True,'map_id':self.map,'started_at':'fixture-battle','turn_sequence':0,'turn_index':0,'participants':members}
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))

    def payload(self):
        from app.monster_runtime import token_monster,breath_contract,preview
        from app.combat_effects import effect_snapshot
        with closing(sqlite3.connect(self.db)) as db:
            monster,_=token_monster(db,'gob1')
            context,_,_=preview(db,effect_snapshot(db),'gob1','Baforada','vez-pin')
        return {'token_id':'gob1','ability_name':'Baforada','aim_token_id':'vez-pin','definition_revision':breath_contract(monster,'Baforada')['revision'],'area_fingerprint':context['area_fingerprint']}

    def command(self,key='monster-breath-first',payload=None,role='gm',version=None):
        from app.combat_effects import effect_command,readeffects
        return effect_command(self.db,actor_id='master' if role=='gm' else 'vezemir',actor_role=role,allow_player=role=='player',request_id=key,
            expected_version=readeffects(self.db)['version'] if version is None else version,action='monster_breath',payload=payload or self.payload())

    def test_one_damage_roll_all_area_creatures_and_retry_no_duplicate(self):
        payload=self.payload()
        with (patch('app.monster_runtime.roll_formula',return_value={'total':12,'individual_results':[1]*11}) as damage,
              patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]})):
            result=self.command(payload=payload)
            replay=self.command(payload=payload,version=0)
        self.assertEqual(result,replay);damage.assert_called_once()
        self.assertEqual(self.hp(),18);self.assertEqual(self.token_hp('other'),988)
        self.assertEqual(len(result['protocol_result']['results']),2)
        self.assertEqual(result['protocol_result']['uses_remaining'],2)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='monster_breath'").fetchone()[0],1)

    def test_outside_cone_not_affected_and_success_halves_shared_damage(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_y=20 WHERE token_id='other'")
        with patch('app.monster_runtime.roll_formula',return_value={'total':13,'individual_results':[13]}),patch('app.dorn_spells.roll_formula',return_value={'total':30,'individual_results':[20]}):
            result=self.command()
        self.assertEqual(self.hp(),24);self.assertEqual(self.token_hp('other'),1000)
        self.assertEqual(len(result['protocol_result']['results']),1)

    def test_version_bounds_turn_and_role_are_authoritative(self):
        payload=self.payload()
        for wrong in [{**payload,'definition_revision':'stale'},{**payload,'damage':999},{**payload,'aim_token_id':'missing'}]:
            with self.assertRaises(ValueError):self.command(payload=wrong)
        with self.assertRaises(PermissionError):self.command(role='player')
        with closing(sqlite3.connect(self.db)) as db,db:
            e=json.loads(db.execute('SELECT encounter_json FROM combat_effect_clock').fetchone()[0]);e['turn_index']=1
            db.execute('UPDATE combat_effect_clock SET encounter_json=?',(json.dumps(e),))
        with self.assertRaises(ValueError):self.command()
        self.assertEqual(self.hp(),30)

    def test_area_movement_between_preview_and_confirmation_rejects_without_cost(self):
        payload=self.payload()
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_y=20 WHERE token_id='other'")
        with self.assertRaisesRegex(ValueError,'Posições mudaram'):self.command(payload=payload)
        self.assertEqual(self.hp(),30)

    def test_parallel_retry_has_one_receipt_one_cost_one_damage(self):
        payload=self.payload()
        with patch('app.monster_runtime.roll_formula',return_value={'total':2,'individual_results':[2]}),patch('app.dorn_spells.roll_formula',return_value={'total':1,'individual_results':[1]}):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(lambda _:self.command(key='same-concurrent-command',payload=payload,version=0),range(2)))
        self.assertEqual(results[0],results[1]);self.assertEqual(self.hp(),28)
        self.assertEqual(results[0]['protocol_result']['uses_remaining'],2)

    def test_failure_halfway_through_area_rolls_back_damage_cost_and_ledger(self):
        with patch('app.monster_runtime.roll_formula',return_value={'total':12,'individual_results':[12]}),patch('app.dorn_spells.save',side_effect=[{'success':False},ValueError('fixture second JP failed')]):
            with self.assertRaisesRegex(ValueError,'second JP failed'):self.command()
        self.assertEqual(self.hp(),30);self.assertEqual(self.token_hp('other'),1000)
        with closing(sqlite3.connect(self.db)) as db:
            sheet=json.loads(db.execute("SELECT sheet_json FROM session_workspace_tokens WHERE id='gob1'").fetchone()[0])
            self.assertEqual(sheet.get('monster_runtime',{}).get('usage',{}),{})
            self.assertEqual(db.execute("SELECT COUNT(*) FROM session_ledger WHERE source_type='monster_breath'").fetchone()[0],0)

    def test_player_cannot_reset_monster_daily_resources_through_rest(self):
        from app.character_play import apply_character_action
        with self.assertRaises(PermissionError):
            apply_character_action(self.db,character_id='vezemir',actor_id='vezemir',actor_role='player',action='rest_at_inn',payload={'reset_monsters':True},request_id='unauthorized-npc-reset')

    def test_maximum_daily_uses_persist_and_full_rest_only_resets_usage(self):
        from app.monster_runtime import full_rest
        with patch('app.monster_runtime.roll_formula',return_value={'total':1,'individual_results':[1]}),patch('app.dorn_spells.roll_formula',return_value={'total':30,'individual_results':[20]}):
            for n in range(3):
                self.command(key=f'monster-day-use-{n}')
                with closing(sqlite3.connect(self.db)) as db,db:
                    e=json.loads(db.execute('SELECT encounter_json FROM combat_effect_clock').fetchone()[0]);e.update(action_committed=False,attacks_used=0)
                    db.execute('UPDATE combat_effect_clock SET encounter_json=?',(json.dumps(e),))
            with self.assertRaisesRegex(ValueError,'Sem usos'):self.command(key='monster-day-fourth')
        with closing(sqlite3.connect(self.db)) as db,db:full_rest(db,'tomorrow')
        self.assertEqual(self.hp(),30)
        self.assertEqual(self.command(key='monster-new-day')['protocol_result']['uses_remaining'],2)

    def test_native_hp_applies_immunity_and_regeneration_excludes_fire_wounds(self):
        from app.combat_effects import change_hp
        from app.monster_runtime import turn_start
        from app.monster_catalog import get_catalog_monster
        with closing(sqlite3.connect(self.db)) as db,db:
            change_hp(db,'token','gob1',-10,'now',damage_type='fire')
            self.assertEqual(db.execute("SELECT current_hp FROM session_workspace_tokens WHERE id='gob1'").fetchone()[0],66)
            troll={**get_catalog_monster('troll'),'source':{'monster_id':'troll'}}
            db.execute("UPDATE session_workspace_tokens SET sheet_json=?,current_hp=35,maximum_hp=35 WHERE id='other'",(json.dumps(troll),))
            change_hp(db,'token','other',-4,'now',damage_type='fire')
            change_hp(db,'token','other',-2,'now')
            for round_number in [1,1,2,3,4]:turn_start(db,{'target_type':'token','target_id':'other'},{'started_at':'battle'},round_number,'now',f'regen-request-{round_number}')
            self.assertEqual(db.execute("SELECT current_hp FROM session_workspace_tokens WHERE id='other'").fetchone()[0],31)
            change_hp(db,'token','other',2,'now')  # Real healing may restore fire wounds.
            turn_start(db,{'target_type':'token','target_id':'other'},{'started_at':'battle'},5,'now','regen-request-next')
            self.assertEqual(db.execute("SELECT current_hp FROM session_workspace_tokens WHERE id='other'").fetchone()[0],33)
