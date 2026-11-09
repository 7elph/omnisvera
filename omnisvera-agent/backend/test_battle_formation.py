import sqlite3
import unittest
from contextlib import closing
from app.combat_effects import effect_command, readeffects
from app.session_workspace import get_workspace_snapshot
from app.spatial_grid import configure_grid, init_spatial
from test_battle_mode import BattleModeTests


class BattleFormationTests(unittest.TestCase):
    """Companion 3.0 face-to-face screen: optional opening cells, start only."""
    def setUp(self):
        self.base = BattleModeTests('test_start_preserves_existing_pin_positions')
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.db, self.enemy = self.base.db, self.base.enemy
        self.command, self.start = self.base.command, self.base.start
        init_spatial(self.db)
        configure_grid(self.db, actor_id='master', role='gm', request_id='formation-grid', map_id='arena',
                       config={'cols': 12, 'rows': 8, 'cell_size_m': 1})

    def start_with(self, formation):
        return self.command('start', map_id='arena', battle_mode=True, formation=formation, participants=[
            {'target_type': 'character', 'target_id': 'vezemir', 'name': 'Vezemir', 'initiative': 20},
            {'target_type': 'token', 'target_id': self.enemy['id'], 'name': 'Aranha', 'initiative': 10}])

    def cells(self):
        with closing(sqlite3.connect(self.db)) as db:
            return {row[0]: (row[1], row[2]) for row in db.execute("SELECT token_id,cell_x,cell_y FROM session_workspace_entity_positions WHERE map_id='arena'")}

    def test_formation_places_both_sides_and_end_restores_exploration(self):
        self.start_with([{'target_type': 'character', 'target_id': 'vezemir', 'cell': [5, 4]},
                         {'target_type': 'token', 'target_id': self.enemy['id'], 'cell': [6, 4]}])
        state = readeffects(self.db)['encounter']
        vezemir = next(p['token_id'] for p in state['participants'] if p['target_id'] == 'vezemir')
        self.assertEqual(self.cells()[vezemir], (5, 4))
        self.assertEqual(self.cells()[self.enemy['id']], (6, 4))
        self.command('end')
        restored = get_workspace_snapshot(self.db, is_gm=True)
        enemy = next(t for t in restored['tokens'] if t['id'] == self.enemy['id'])
        self.assertEqual((enemy['latitude'], enemy['longitude']), (35, 60))

    def test_invalid_formation_rolls_back_the_whole_start(self):
        for formation in ([{'target_type': 'token', 'target_id': 'intruso', 'cell': [1, 1]}],
                          [{'target_type': 'token', 'target_id': self.enemy['id'], 'cell': [40, 1]}],
                          [{'target_type': 'character', 'target_id': 'vezemir', 'cell': [2, 2]},
                           {'target_type': 'token', 'target_id': self.enemy['id'], 'cell': [2, 2]}]):
            with self.assertRaises(ValueError):
                self.start_with(formation)
            self.assertFalse(readeffects(self.db)['encounter'].get('active'))
            self.assertEqual(get_workspace_snapshot(self.db, is_gm=True)['map']['id'], 'default')

    def test_without_formation_behaviour_is_unchanged(self):
        self.start()
        self.assertTrue(readeffects(self.db)['encounter']['active'])


if __name__ == '__main__':
    unittest.main()
