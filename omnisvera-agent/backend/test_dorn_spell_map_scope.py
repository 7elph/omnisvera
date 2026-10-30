"""Spell range must use the current scene, never an older copy of a PC pin."""
import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch

import test_dorn_approved_pack as fixtures
from app.dorn_spell_pack import grid_distance
from app.session_workspace import save_workspace_token, set_workspace_map


class DornSpellMapScopeTests(TestCase):
    def setUp(self):
        self.fixture = fixtures.DornApprovedPackTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        self.map_id, self.mine = self.fixture.grid()
        self.old_map = set_workspace_map(self.path, title='Old scene', image_path='old.svg', visible_to_players=True)['id']
        self.ally = self.pin('zz-current-ally', 'vezemir', self.map_id, 5)
        self.old_ally = self.pin('aa-old-ally', 'vezemir', self.old_map, 15)
        self.pin('aa-old-dorn', 'dorn7', self.old_map, 0)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE session_workspace_state SET map_id=? WHERE id=1', (self.map_id,))
            # A second real character DTO in this disposable fixture.
            db.execute("INSERT INTO character_states(profile_id,state_json,version,updated_at) SELECT 'vezemir',state_json,version,updated_at FROM character_states WHERE profile_id='dorn7'")
            columns = [r[1] for r in db.execute('PRAGMA table_info(character_sheets)') if r[1] != 'profile_id']
            names = ','.join(columns)
            db.execute(f"INSERT INTO character_sheets(profile_id,{names}) SELECT 'vezemir',{names} FROM character_sheets WHERE profile_id='dorn7'")

    def pin(self, identity, character, map_id, x):
        pin = save_workspace_token(self.path, token_type='character', character_id=character,
                                   name=character, map_id=map_id, latitude=20, longitude=20,
                                   visible_to_players=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DELETE FROM session_workspace_entity_positions WHERE token_id=?', (pin['id'],))
            db.execute('UPDATE session_workspace_tokens SET id=? WHERE id=?', (identity, pin['id']))
            db.execute("INSERT OR IGNORE INTO session_workspace_map_grids VALUES(?,'square',30,30,1.5,0,0,'chebyshev',1,1)", (map_id,))
            db.execute('INSERT INTO session_workspace_entity_positions VALUES(?,?,?,5,1,1,1)', (map_id, identity, x))
        return identity

    def state(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT state_json,version FROM character_states WHERE profile_id='dorn7'").fetchone()

    def test_character_distance_ignores_old_map_pins(self):
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(1.5, grid_distance(db, 'dorn7', 'character', 'vezemir'))

    def test_selected_current_pin_can_receive_strength_despite_old_pin(self):
        with patch('app.dorn_spells.roll_formula', return_value={'total':2}):
            result = self.fixture.cast('forca-arcana', targets=[{'type':'token','id':self.ally}])
        self.assertEqual('vezemir', result['protocol_result']['results'][0]['effect']['target_id'])

    def test_old_map_token_rejected_without_cost_or_dice(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=1 WHERE token_id=?', (self.old_ally,))
        before = self.state()
        with patch('app.dorn_spells.roll_formula') as dice:
            with self.assertRaisesRegex(ValueError, 'mapa|grid'):
                self.fixture.cast('teia', targets=[{'type':'token','id':self.old_ally}])
            dice.assert_not_called()
        self.assertEqual(before, self.state())

    def test_combat_map_has_priority_over_browsed_map(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE session_workspace_state SET map_id=? WHERE id=1', (self.old_map,))
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps({'active':True,'map_id':self.map_id}),))
            self.assertEqual(1.5, grid_distance(db, 'dorn7', 'character', 'vezemir'))

    def test_current_map_scale_used_for_touch_not_old_map_scale(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE session_workspace_map_grids SET cell_size_m=0.5 WHERE map_id=?', (self.old_map,))
        with patch('app.dorn_spells.roll_formula', return_value={'total':2}):
            result = self.fixture.cast('forca-arcana', targets=[{'type':'token','id':self.ally}])
        self.assertEqual('Força Arcana', result['protocol_result']['spell'])
