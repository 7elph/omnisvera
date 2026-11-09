import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
import test_morthak_high_spells as high


class SummonDeathFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.fixture=high.HighSpellTests();self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path=self.fixture.path

    def skeleton(self):
        from app.summons import create_summon
        from app import main
        return create_summon(self.path,caster='morthak',technique='levantar-esqueleto',
            spec=main._SUMMON_DEFAULTS['levantar-esqueleto'],request_id='feedback-skeleton',actor_id='morthak',actor_role='player')['token']

    def test_new_skeleton_persists_catalog_movement_hit_dice_and_save(self):
        token=self.skeleton()
        from app.monster_movement import selected_movement
        self.assertEqual(selected_movement(token['sheet'].get('movement')),9)
        with closing(sqlite3.connect(self.path)) as db:
            sheet=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(token['id'],)).fetchone()[0])
        self.assertEqual(sheet['hit_dice'],1)
        self.assertEqual(sheet['saving_throw'],6)

    def test_legacy_profile_completion_preserves_explicit_values_and_unknown_summons(self):
        from app.summon_profiles import complete_sheet
        original={'summon':{'caster':'morthak','technique':'animar-mortos'},'movement':'12 m','dv':4,'saving_throw':15}
        result=complete_sheet(original)
        self.assertEqual(result['movement'],'12 m');self.assertEqual(result['saving_throw'],15)
        self.assertNotIn('hit_dice',result)
        self.assertEqual(result,original)
        legacy={'summon':{'caster':'morthak','technique':'animar-mortos'}}
        result=complete_sheet(legacy)
        self.assertEqual(result['movement'],'6');self.assertEqual(result['hit_dice'],2)
        self.assertNotIn('movement',legacy)
        unknown={'summon':{'caster':'someone-else','technique':'animar-mortos'}}
        self.assertEqual(complete_sheet(unknown),unknown)

    def test_owner_can_move_legacy_skeleton_in_its_native_turn_without_resetting_resources(self):
        from app.combat_effects import effect_command,readeffects
        from app.spatial_grid import move_entity
        token=self.skeleton()
        with closing(sqlite3.connect(self.path)) as db,db:
            sheet=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(token['id'],)).fetchone()[0])
            for key in ('movement','hit_dice','saving_throw'):sheet.pop(key,None)
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(sheet),token['id']))
            before=db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0]
        def gm(action,payload):
            state=readeffects(self.path)
            return effect_command(self.path,actor_id='master',actor_role='gm',request_id='feedback-'+action,
                expected_version=state['version'],action=action,payload=payload)
        gm('start',{'map_id':'default','battle_mode':True,'participants':[
            {'target_type':'character','target_id':'morthak','name':'Morthak','initiative':20},
            {'target_type':'token','target_id':token['id'],'name':'Esqueleto','initiative':10}]})
        state=gm('next_turn',{})
        with closing(sqlite3.connect(self.path)) as db:
            x,y,v=db.execute('SELECT cell_x,cell_y,version FROM session_workspace_entity_positions WHERE token_id=?',(token['id'],)).fetchone()
            gv=db.execute("SELECT version FROM session_workspace_map_grids WHERE map_id='default'").fetchone()[0]
        result=move_entity(self.path,actor_id='morthak',role='player',request_id='feedback-move',map_id='default',token_id=token['id'],
            mode='COMBAT_MOVE',cells=[[x,y],[x,y+1]],expected_position_version=v,expected_grid_version=gv,expected_combat_version=state['version'])
        self.assertIsNotNone(result)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0],before)
            self.assertEqual(db.execute('SELECT cell_y FROM session_workspace_entity_positions WHERE token_id=?',(token['id'],)).fetchone()[0],y+1)

    def test_explicit_backfill_is_idempotent_and_preserves_hp_positions_and_caster_state(self):
        from app.summon_profiles import backfill_active
        token=self.skeleton()
        with closing(sqlite3.connect(self.path)) as db,db:
            raw=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(token['id'],)).fetchone()[0])
            for key in ('movement','hit_dice','saving_throw'):raw.pop(key,None)
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(raw),token['id']))
            before=db.execute('SELECT current_hp,latitude,longitude FROM session_workspace_tokens WHERE id=?',(token['id'],)).fetchone()
            caster=db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0]
        self.assertEqual(len(backfill_active(self.path)),1)
        self.assertEqual(backfill_active(self.path),[])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT current_hp,latitude,longitude FROM session_workspace_tokens WHERE id=?',(token['id'],)).fetchone(),before)
            self.assertEqual(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0],caster)

    def test_death_ring_excludes_creatures_over_four_dv(self):
        from app.action_range import ring_for_action
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=json_set(sheet_json,'$.hit_dice',8) WHERE id=?",(self.fixture.fixture.ogre['id'],))
        ring=ring_for_action(self.path,ref='technique:morthak:magia-da-morte',attacker_token_id=self.fixture.pin['id'],attacker_character_id='morthak',map_id='default',role='player')
        target=next(target for target in ring['targets'] if target['id']==self.fixture.fixture.ogre['id'])
        self.assertFalse(target['valid']);self.assertIn('4 DV',target['reason'])

    def test_death_magic_ignores_statless_scenery_and_reports_roll_saves_and_cost(self):
        from app.session_workspace import save_workspace_token
        save_workspace_token(self.path,token_type='monster',name='Perigo sem ficha',current_hp=999,maximum_hp=999,
            latitude=20,longitude=20,sheet={'statless':True})
        with patch('app.morthak_high_spells.roll_formula',return_value={'formula':'2d6','individual_results':[1,1],'total':2}),patch('app.necromancer_spells.save_difficult',return_value={'success':False,'total':1}):
            response=self.fixture.command('necro_spell_cast',{'spell_id':'magia-da-morte'},'feedback-death')
            replay=self.fixture.command('necro_spell_cast',{'spell_id':'magia-da-morte'},'feedback-death')
        self.assertEqual(response,replay)
        result=response['protocol_result']
        self.assertEqual(result['victim_limit_roll']['individual_results'],[1,1])
        self.assertEqual(result['defeated'],1)
        self.assertEqual(result['resisted'],0)
        self.assertEqual((result['caster_hp_before'],result['caster_hp_after']),(36,3))
        self.assertEqual(result['hp_cost'],33)

    def test_own_summon_missing_dv_and_jp_does_not_block_death_magic(self):
        token=self.skeleton()
        with closing(sqlite3.connect(self.path)) as db,db:
            raw=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(token['id'],)).fetchone()[0])
            for key in ('movement','hit_dice','saving_throw'):raw.pop(key,None)
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(raw),token['id']))
        with patch('app.morthak_high_spells.roll_formula',return_value={'total':2}),patch('app.necromancer_spells.save_difficult',return_value={'success':True,'total':20}):
            response=self.fixture.command('necro_spell_cast',{'spell_id':'magia-da-morte'})
        self.assertEqual(response['protocol_result']['resisted'],2)


class HemomancyStatusArtTests(unittest.TestCase):
    def test_status_uses_current_weapon_image_even_when_generic_catalog_name_matches(self):
        from app.action_cards import active_effect_icons
        for weapon in ('arco','foice','marreta','lanca'):
            effect={'id':'weapon','target_type':'character','target_id':'raziel','label':'Arma de Sangue',
                    'source':'Hemomancia','duration':'scene','hemomancy_kind':'weapon','weapon':weapon}
            result=active_effect_icons([effect],lambda _: [{'id':'legacy','name':'Arma de Sangue','image_path':'old.jpg'}],['raziel'])
            self.assertTrue(result[0]['card']['image_path'].endswith('raziel-'+weapon+'.jpeg'))
