"""Legacy distance declarations cannot override an existing logical grid."""
import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch

import test_necromancer_integrity as fixtures
from app.session_workspace import set_workspace_map, save_workspace_token
from app.spatial_grid import configure_grid


class NecromancerGridAuthorityTests(TestCase):
    def setUp(self):
        self.fixture = fixtures.NecromancerIntegrityTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.db
        self.map_id = set_workspace_map(self.path, title='Current necromancer scene', image_path='fixture.svg', visible_to_players=True)['id']
        mine = save_workspace_token(self.path, token_type='character', character_id='morthak', name='Morthak', map_id=self.map_id, latitude=0, longitude=0, visible_to_players=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET map_id=? WHERE id='gob'", (self.map_id,))
        configure_grid(self.path, actor_id='master', role='gm', request_id='necro-grid-fixture', map_id=self.map_id, config={'cols':40,'rows':20,'cell_size_m':1.5})
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=0,cell_y=0 WHERE token_id=?', (mine['id'],))
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=1,cell_y=0 WHERE token_id='gob'")

    def state(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT state_json,version FROM character_states WHERE profile_id='morthak'").fetchone()

    def test_false_near_distance_cannot_cast_beyond_grid_radius(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE session_workspace_entity_positions SET cell_x=25 WHERE token_id='gob'")
        before = self.state()
        with patch('app.necromancer_spells.roll_formula', return_value={'total':1,'individual_results':[1]}) as dice:
            with self.assertRaisesRegex(ValueError, 'Alcance|alcance'):
                self.fixture.cast(targets=[{'type':'token','id':'gob','distance_meters':1}])
            dice.assert_not_called()
        self.assertEqual(before, self.state())

    def test_true_grid_distance_ignores_wrong_manual_distance(self):
        with patch('app.necromancer_spells.roll_formula', return_value={'total':1,'individual_results':[1]}):
            result = self.fixture.cast(targets=[{'type':'token','id':'gob','distance_meters':999}])
        self.assertEqual('grid', result['protocol_result']['position'])
        self.assertEqual('gob', result['protocol_result']['results'][0]['effect']['target_id'])

    def test_token_on_other_scene_is_rejected_without_spending(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET map_id='default' WHERE id='gob'")
        before = self.state()
        with self.assertRaisesRegex(ValueError, 'mapa|grid'):
            self.fixture.cast(targets=[{'type':'token','id':'gob','distance_meters':1}])
        self.assertEqual(before, self.state())
