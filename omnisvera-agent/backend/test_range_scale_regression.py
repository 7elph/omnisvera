"""One-metre campaign grids and authoritative formula/weapon ranges."""
import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

import test_action_range as _fixtures


class RangeScaleRegressionTests(unittest.TestCase):
    setUp = _fixtures.ActionRangeTests.setUp

    def test_all_literal_level_formula_variants(self):
        from app.spell_engine import scaled_spell_mechanic
        for text, level, expected in [('3m + nível', 1, 4), ('3m + nível', 5, 8),
                ('10 metros/nível', 5, 50), ('30 + 10 metros/nível', 5, 80),
                ('3 metros + 1 metro por nível', 5, 8), ('1,5 m + 0,5 m/nível', 3, 3)]:
            with self.subTest(text=text, level=level):
                self.assertEqual(expected, scaled_spell_mechanic({'alcance':text}, level)['range_m'])

    def test_level_formula_never_silently_defaults_to_level_one(self):
        from app.spell_engine import scaled_spell_mechanic
        with self.assertRaises(ValueError):
            scaled_spell_mechanic({'alcance':'10 metros/nível'}, None)

    def test_preview_uses_same_level_formula_as_execution(self):
        from app.action_range import declared_range
        with patch('app.spell_catalog.get_catalog_spell', return_value={'alcance':'3m + nível'}), \
             patch('app.action_library.describe_action', return_value={'kind':'spell'}):
            self.assertEqual(8, declared_range(self.db, 'spell:fixture', caster_level=5)['range_m'])

    def test_bandit_weapons_have_automatic_maximum_ranges(self):
        from app.action_range import declared_range
        for ref, maximum in [('monster:bandido:attack:1',27),
                             ('monster:bandido-campeao:attack:0',30),
                             ('monster:bandido-lider:attack:0',60)]:
            with self.subTest(ref=ref):
                value=declared_range(self.db,ref)
                self.assertEqual('ranged',value['mode'])
                self.assertEqual(maximum,value['range_m'])

    def test_token_actor_cannot_skip_native_grid_validation(self):
        from app.spatial_grid import check_attack_range
        with self.assertRaisesRegex(ValueError,'Fora de alcance'):
            check_attack_range(self.db, actor_character_id='gob1',target_type='token',
                               target_id='gob2',slot='ranged',max_range_m=4)

    def test_bandit_resolution_retries_and_rejects_distance_changes(self):
        from app.character_play import init_character_play
        from app.dice_rolls import init_dice_rolls
        from app.session_ledger import init_session_ledger
        from app.combat import monster_attack_definition,resolve_attack,confirm_attack_resolution,CombatExpiredError
        init_character_play(self.db);init_dice_rolls(self.db);init_session_ledger(self.db)
        definition=monster_attack_definition({'id':'gob1','name':'Bandido','sheet':{'attacks':[
            {'name':'Funda','bonus':1,'damage':'1d3'}]}},'0')
        target={'type':'token','id':'gob2','name':'Alvo','armor_class':10,'current_hp':9,'maximum_hp':9}
        kwargs=dict(request_id='bandit-native-range',actor_character_id='gob1',actor_name='Bandido',
            requested_by_id='master',requested_by_role='gm',definition=definition,inventory=[],
            attack_id='0',target=target,roll_mode='physical',physical_d20=20)
        first,_=resolve_attack(self.db,**kwargs)
        self.assertEqual(4.5,first['breakdown']['native_range']['meters'])
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=19,version=version+1 WHERE token_id='gob2'")
        self.assertEqual(first,resolve_attack(self.db,**kwargs)[0])
        with self.assertRaises(CombatExpiredError):
            confirm_attack_resolution(self.db,resolution_id=first['resolution_id'],requested_by_id='master',requested_by_role='gm')
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=8,version=version+1 WHERE token_id='gob2'")
        second,_=resolve_attack(self.db,**{**kwargs,'request_id':'bandit-valid-confirm'})
        confirmed,_=confirm_attack_resolution(self.db,resolution_id=second['resolution_id'],requested_by_id='master',requested_by_role='gm')
        self.assertLess(confirmed['hp_after'],9)
        self.assertEqual(confirmed,confirm_attack_resolution(self.db,resolution_id=second['resolution_id'],requested_by_id='master',requested_by_role='gm')[0])
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=0 WHERE token_id='gob1'")
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=19 WHERE token_id='gob2'")
        with self.assertRaisesRegex(ValueError,'Fora de alcance'):
            resolve_attack(self.db,**{**kwargs,'request_id':'bandit-too-far'})

    def test_one_metre_migration_preserves_positions_and_active_turn(self):
        from app.character_play import init_character_play
        from app.dice_rolls import init_dice_rolls
        init_character_play(self.db)
        init_dice_rolls(self.db)
        from app.spatial_grid import set_campaign_cell_scale
        from app.combat_effects import init_effects
        init_effects(self.db)
        encounter={'active':True,'map_id':'default','movement':{'spent_m':3,'budget_m':9},'turn_index':2}
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
            before=db.execute('SELECT * FROM session_workspace_entity_positions').fetchall()
        result=set_campaign_cell_scale(self.db,actor_id='master',role='gm',request_id='scale-test-1m')
        self.assertEqual(1,len(result['maps']))
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(1,db.execute('SELECT cell_size_m FROM session_workspace_map_grids').fetchone()[0])
            self.assertEqual(before,db.execute('SELECT * FROM session_workspace_entity_positions').fetchall())
            self.assertEqual(encounter,json.loads(db.execute('SELECT encounter_json FROM combat_effect_clock').fetchone()[0]))
        self.assertEqual(result,set_campaign_cell_scale(self.db,actor_id='master',role='gm',request_id='scale-test-1m'))
        with self.assertRaises(PermissionError):
            set_campaign_cell_scale(self.db,actor_id='raziel',role='player',request_id='scale-player')


if __name__=='__main__':unittest.main()
