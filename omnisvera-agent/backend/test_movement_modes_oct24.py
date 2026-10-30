"""Declared bestiary movement modes share one native turn budget."""
import json,sqlite3,unittest
from contextlib import closing
import test_spatial_grid as fixture
from app.spatial_grid import movement_m

class MovementModeTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.SpatialGridTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        with closing(sqlite3.connect(self.f.db)) as db,db:
            db.execute("UPDATE session_workspace_tokens SET character_id=NULL,token_type='monster',current_hp=20,maximum_hp=20,sheet_json=? WHERE id=?",
                       (json.dumps({'movement':'9, 21V'}),self.f.token['id']))
        from app.combat_effects import effect_command,readeffects
        state=readeffects(self.f.db)
        effect_command(self.f.db,actor_id='master',actor_role='gm',request_id='mode-combat-start',expected_version=state['version'],action='start',
                       payload={'map_id':self.f.map,'participants':[{'target_type':'token','target_id':self.f.token['id'],'initiative':10}]})

    def test_bestiaried_default_walk_and_explicit_flight(self):
        self.assertEqual(9,movement_m('9, 21V'))
        from app.monster_movement import selected_movement
        self.assertEqual(9,movement_m('9m andando, 12m voando'))
        self.assertEqual(12,selected_movement('9m andando, 12m voando','fly'))
        reply=self.f.command('COMBAT_MOVE',[[1,1],[2,1]],movement_mode='fly')
        self.assertEqual(21,reply['movement']['budget_m'])
        self.assertEqual('fly',reply['movement']['mode'])

    def test_mode_cannot_change_to_reset_or_expand_spent_budget(self):
        self.f.command('COMBAT_MOVE',[[1,1],[2,1]],movement_mode='walk')
        with self.assertRaisesRegex(ValueError,'modo'):
            self.f.command('COMBAT_MOVE',[[2,1],[3,1]],movement_mode='fly',request_id='mode-switch-reject')
        self.assertEqual(2,self.f.position()['cell_x'])

    def test_unknown_mode_rejected_before_position_mutation(self):
        with self.assertRaises(ValueError):self.f.command('COMBAT_MOVE',[[1,1],[2,1]],movement_mode='swim')
        self.assertEqual(1,self.f.position()['cell_x'])

if __name__=='__main__':unittest.main()
