"""Deterministic swarm coverage on the existing temporary grid fixture."""
import json
import sqlite3
import unittest
from contextlib import closing

import test_spatial_grid as fixtures
from app.combat_effects import effect_snapshot
from app.session_workspace import (save_workspace_token, update_workspace_token,
    delete_workspace_token, set_active_workspace_map, set_workspace_map, get_workspace_snapshot)
from app.spatial_grid import move_entity, configure_grid


class BatSwarmTests(unittest.TestCase):
    setUp = fixtures.SpatialGridTests.setUp
    configure = fixtures.SpatialGridTests.configure

    def bat(self, **changes):
        sheet = {'source': {'monster_id': 'morcego'}, 'movement': '9V'}
        sheet.update(changes.pop('sheet', {}))
        return save_workspace_token(self.db, token_type=changes.pop('token_type', 'monster'), name='Morcego',
            latitude=12, longitude=12, map_id=self.map, sheet=sheet,
            current_hp=changes.pop('current_hp', 1), maximum_hp=1, **changes)

    def sync(self):
        from app.bat_swarm import sync
        with closing(sqlite3.connect(self.db)) as db, db:
            result = sync(db, 'fixture-now')
            snapshot = effect_snapshot(db)
        return result, snapshot

    def read(self):
        with closing(sqlite3.connect(self.db)) as db:
            return effect_snapshot(db)

    def test_nine_do_not_confuse_ten_do_and_repeat_is_read_stable(self):
        for _ in range(9): self.bat()
        self.assertEqual(self.sync()[1]['effects'], [])
        self.bat()
        changed, snapshot = self.sync()
        # The tenth native save already reconciles inside its transaction.
        self.assertEqual(changed, [])
        self.assertEqual(len(snapshot['effects']), 1)
        effect = snapshot['effects'][0]
        self.assertEqual(effect['target_id'], 'vezemir')
        self.assertTrue(effect['d20_penalty'])
        self.assertTrue(effect['difficult_tests'])
        self.assertEqual(effect['map_id'], self.map)
        self.assertEqual(effect['duration'], 'manual')
        self.assertIsNone(effect['rounds'])
        self.assertEqual(effect['swarm_count'], 10)
        repeated, after = self.sync()
        self.assertEqual(repeated, [])
        self.assertEqual(after, snapshot)

    def test_dead_missing_source_and_character_bat_forms_are_not_counted(self):
        for _ in range(9): self.bat()
        self.bat(current_hp=0)
        self.bat(sheet={'source': {'monster_id': 'goblin'}})
        self.bat(sheet={'source': {}, 'night_form': {'form': 'morcego'}})
        self.assertEqual(self.sync()[1]['effects'], [])

    def test_character_even_disguised_with_catalog_source_is_never_a_tenth_bat(self):
        for _ in range(9): self.bat()
        self.bat(token_type='character', character_id='raziel',
                 sheet={'source': {'monster_id': 'morcego'}, 'night_form': {'form': 'morcego'}})
        self.assertEqual(self.sync()[1]['effects'], [])

    def test_death_and_movement_remove_condition_without_fixed_timer(self):
        bats = [self.bat() for _ in range(10)]
        self.assertEqual(len(self.sync()[1]['effects']), 1)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=0 WHERE id=?', (bats[0]['id'],))
        self.assertEqual(self.sync()[1]['effects'], [])
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=1 WHERE id=?', (bats[0]['id'],))
        self.assertEqual(len(self.sync()[1]['effects']), 1)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=5 WHERE token_id=?', (self.token['id'],))
        self.assertEqual(self.sync()[1]['effects'], [])

    def test_native_pin_save_hp_update_and_delete_reconcile_without_a_read_mutation(self):
        bats = [self.bat() for _ in range(10)]
        self.assertEqual(len(self.read()['effects']), 1)
        update_workspace_token(self.db, token_id=bats[0]['id'], current_hp=0)
        self.assertEqual(self.read()['effects'], [])
        update_workspace_token(self.db, token_id=bats[0]['id'], current_hp=1)
        self.assertEqual(len(self.read()['effects']), 1)
        delete_workspace_token(self.db, bats[0]['id'])
        self.assertEqual(self.read()['effects'], [])

    def test_native_grid_move_receipt_carries_post_condition_version_and_retry_is_exact(self):
        for _ in range(10): self.bat()
        before = self.read()
        args = dict(actor_id='master', role='gm', request_id='swarm-grid-reposition',
            map_id=self.map, token_id=self.token['id'], mode='GM_REPOSITION',
            cells=[[1,1],[2,1]], expected_position_version=1, expected_grid_version=1)
        moved = move_entity(self.db, **args)
        after = self.read()
        self.assertEqual(after['effects'], [])
        self.assertGreater(after['version'], before['version'])
        self.assertEqual(moved['combat_version'], after['version'])
        self.assertEqual(move_entity(self.db, **args), moved)
        get_workspace_snapshot(self.db, map_id=self.map, is_gm=True)
        self.assertEqual(self.read(), after)

    def test_map_selection_disables_and_restores_condition_only_by_mutation(self):
        for _ in range(10): self.bat()
        self.assertEqual(len(self.read()['effects']), 1)
        other_map = set_workspace_map(self.db, title='Elsewhere', image_path='fixture.svg')['id']
        set_active_workspace_map(self.db, other_map)
        self.assertEqual(self.read()['effects'], [])
        set_active_workspace_map(self.db, self.map)
        self.assertEqual(len(self.read()['effects']), 1)

    def test_configuring_grid_reconciles_legacy_pins_once_positions_are_seeded(self):
        self.map = set_workspace_map(self.db, title='Swarm legacy', image_path='fixture.svg')['id']
        set_active_workspace_map(self.db, self.map)
        save_workspace_token(self.db, token_type='character', character_id='vezemir', name='Vezemir',
            latitude=12, longitude=12, map_id=self.map)
        for _ in range(10): self.bat()
        self.assertEqual(self.read()['effects'], [])
        configure_grid(self.db, actor_id='master', role='gm', request_id='swarm-legacy-grid',
            map_id=self.map, config={'cols':10,'rows':10,'cell_size_m':1.5})
        self.assertEqual(len(self.read()['effects']), 1)

    def test_footprint_coverage_and_different_maps_do_not_combine(self):
        for _ in range(5): self.bat()
        bats = [self.bat() for _ in range(5)]
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_entity_positions SET footprint_w=2 WHERE token_id=?', (self.token['id'],))
            for bat in bats:
                db.execute('UPDATE session_workspace_entity_positions SET cell_x=2 WHERE token_id=?', (bat['id'],))
        self.assertEqual(len(self.sync()[1]['effects']), 1)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET map_id=? WHERE id=?', ('default', bats[0]['id']))
        self.assertEqual(self.sync()[1]['effects'], [])

    def test_no_grid_is_no_inferred_swarm_and_sync_without_tables_is_noop(self):
        from app.bat_swarm import sync
        with sqlite3.connect(':memory:') as empty:
            self.assertEqual(sync(empty, 'now'), [])
        for _ in range(10): self.bat()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('DELETE FROM session_workspace_entity_positions WHERE token_id=?', (self.token['id'],))
        self.assertEqual(self.sync()[1]['effects'], [])

    def test_flight_must_be_declared_and_grounded_bats_do_not_confuse(self):
        for _ in range(9): self.bat()
        grounded = self.bat(sheet={'movement': '3,9V', 'movement_mode': 'walk'})
        self.assertEqual(self.sync()[1]['effects'], [])
        with closing(sqlite3.connect(self.db)) as db, db:
            sheet = json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?', (grounded['id'],)).fetchone()[0])
            sheet['movement_mode'] = 'fly'
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?', (json.dumps(sheet), grounded['id']))
        self.assertEqual(len(self.sync()[1]['effects']), 1)
