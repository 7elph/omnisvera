"""Every migrated range projects units without client overrides or zero-radius leaks."""
import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from unittest import TestCase
from unittest.mock import patch

from app import main
from app.access import AccessContext
from app.action_library import native_action_contract
from app.action_range import declared_range, ring_for_action
from app.combat_effects import readeffects


class ContractRangeProjectionTests(TestCase):
    def setUp(self):
        import test_dorn_approved_pack as fixtures
        self.fixture = fixtures.DornApprovedPackTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        self.map_id, self.mine = self.fixture.grid()
        self.enemy = self.fixture.fixture.enemy['id']
        with closing(sqlite3.connect(self.path)) as db, db:
            overrides = json.loads(db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='dorn7'").fetchone()[0])
            overrides['level'] = 5
            db.execute("UPDATE character_definition_overrides SET data_json=? WHERE profile_id='dorn7'", (json.dumps(overrides),))
            db.execute('UPDATE session_workspace_map_grids SET cell_size_m=4 WHERE map_id=?', (self.map_id,))

    def preview(self, spell):
        with patch.object(main, 'settings', replace(main.settings, database_path=self.path)), \
                patch.object(main, '_playable_character', return_value={'definition': {'level': 5}}):
            return main.gm_grid_range(ref='technique:dorn7:' + spell, attacker_token_id='',
                attacker_character_id='dorn7', map_id=self.map_id, slot='ranged',
                max_range_m=9999, range_override_m=9999, access=AccessContext(mode='gm'))

    def enemy_at(self, cells):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=? WHERE token_id=?', (4 + cells, self.enemy))

    def test_declared_touch_uses_cells_and_self_zero_is_not_unknown(self):
        touch = declared_range(self.path, 'technique:dorn7:forca-arcana')
        self.assertEqual(('touch', 1), (touch['mode'], touch['range_cells']))
        self.assertNotIn('range_m', touch)
        own = declared_range(self.path, 'technique:dorn7:reflexos')
        self.assertEqual(('self', 0), (own['mode'], own['range_m']))

    def test_touch_preview_uses_one_real_cell_and_ignores_overrides(self):
        before = readeffects(self.path)
        self.enemy_at(1)
        adjacent = self.preview('forca-arcana')
        self.assertEqual(('touch', 1, 4, 1),
                         (adjacent['mode'], adjacent['range_cells'], adjacent['cell_size_m'], adjacent['max_targets']))
        self.assertEqual(native_action_contract('technique:dorn7:forca-arcana', 5), adjacent['contract'])
        self.assertTrue(next(t for t in adjacent['targets'] if t['id'] == self.enemy)['valid'])
        self.assertEqual(1, sum(t['id'] == self.mine for t in adjacent['targets']))
        self.enemy_at(2)
        distant = self.preview('forca-arcana')
        self.assertFalse(next(t for t in distant['targets'] if t['id'] == self.enemy)['valid'])
        self.assertEqual(before, readeffects(self.path))

    def test_ranged_pack_previews_use_level_and_do_not_trust_client_range(self):
        for spell, meters, cells in [('teia', 8, 3), ('dissipar-magia', 25, 7)]:
            with self.subTest(spell=spell):
                self.enemy_at(cells)
                result = self.preview(spell)
                self.assertEqual(('ranged', meters, 1), (result['mode'], result['range_m'], result['max_targets']))
                self.assertEqual(native_action_contract('technique:dorn7:' + spell, 5), result['contract'])
                self.assertFalse(next(t for t in result['targets'] if t['id'] == self.enemy)['valid'])
                self.assertEqual(len(result['targets']), len({t['id'] for t in result['targets']}))

    def test_self_preview_never_exposes_other_pins_as_valid_zero_radius_targets(self):
        result = ring_for_action(self.path, ref='technique:dorn7:reflexos', attacker_token_id=self.mine,
                                 attacker_character_id='dorn7', map_id=self.map_id, include_self=True)
        self.assertEqual(('self', 0, 0), (result['mode'], result['range_m'], result['range_cells']))
        self.assertEqual([self.mine], [t['id'] for t in result['targets'] if t['valid']])

    def test_web_own_anchor_preview_does_not_apply_until_selected_native_command(self):
        before = readeffects(self.path)
        preview = self.preview('teia')
        self.assertEqual(1, preview['max_targets'])
        self.assertTrue(next(t for t in preview['targets'] if t['id'] == self.mine)['valid'])
        self.assertEqual(before, readeffects(self.path))
        result = self.fixture.cast('teia', targets=[{'type': 'token', 'id': self.mine}],
                                   definition_revision=preview['contract']['revision'])
        effect = result['protocol_result']['results'][0]['effect']
        self.assertEqual((self.map_id, 16, 20),
                         (effect['web_area']['map_id'], effect['web_area']['x_m'], effect['web_area']['y_m']))
        self.assertEqual(0, result['protocol_result']['resource_remaining'])
