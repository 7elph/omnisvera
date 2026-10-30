from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.action_range import approach_preview, declared_range, enforce_action_range, ring_for_action


class ActionRangeTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / "range.db"
        from app.session_workspace import init_session_workspace
        from app.spatial_grid import init_spatial
        init_session_workspace(self.db)
        init_spatial(self.db)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("INSERT INTO session_workspace_maps(id, title, image_path, created_at, updated_at) VALUES('default', 'T', 'x', 'now', 'now')")
            connection.execute(
                "INSERT INTO session_workspace_tokens(id, token_type, map_id, name, current_hp, maximum_hp, sheet_json, created_at, updated_at)"
                " VALUES('gob1', 'monster', 'default', 'Goblin', 12, 12, ?, 'now', 'now')",
                (json.dumps({"movement": "1.5 m", "saving_throw": 10}),))
            connection.execute(
                "INSERT INTO session_workspace_tokens(id, token_type, map_id, name, current_hp, maximum_hp, sheet_json, created_at, updated_at)"
                " VALUES('gob2', 'monster', 'default', 'Goblin B', 9, 9, ?, 'now', 'now')",
                (json.dumps({"saving_throw": 8}),))
            connection.execute(
                "INSERT INTO session_workspace_map_grids(map_id, grid_type, cols, rows, cell_size_m, origin_x, origin_y, distance_rule, version)"
                " VALUES('default', 'square', 20, 20, 1.5, 0, 0, 'chebyshev', 1)")
            connection.execute(
                "INSERT INTO session_workspace_entity_positions(map_id, token_id, cell_x, cell_y, footprint_w, footprint_h, version)"
                " VALUES('default', 'gob1', 5, 5, 1, 1, 1)")
            connection.execute(
                "INSERT INTO session_workspace_entity_positions(map_id, token_id, cell_x, cell_y, footprint_w, footprint_h, version)"
                " VALUES('default', 'gob2', 8, 5, 1, 1, 1)")

    def test_declared_ranges(self) -> None:
        melee = declared_range(self.db, "monster:vampiro:attack:0")
        self.assertEqual((melee["mode"], melee["range_cells"]), ("melee", 1))
        ranged = declared_range(self.db, "monster:elfo:attack:0")
        self.assertEqual(ranged["mode"], "unknown")
        touch = declared_range(self.db, "spell:arcana-bola-de-fogo")
        self.assertEqual(touch["mode"], "ranged")
        breath = declared_range(self.db, "monster:golem-de-ferro:ability:Baforada de gás")
        self.assertEqual(breath["range_m"], 6)

    def test_enforce_melee_and_ranged(self) -> None:
        ok = enforce_action_range(self.db, attacker_token_id="gob1", target_type="token", target_id="gob2",
                                  mode="ranged", range_m=10.0)
        self.assertTrue(ok["checked"])
        self.assertAlmostEqual(ok["meters"], 4.5)
        with self.assertRaises(ValueError):
            enforce_action_range(self.db, attacker_token_id="gob1", target_type="token", target_id="gob2",
                                 mode="melee")
        with self.assertRaises(ValueError):
            enforce_action_range(self.db, attacker_token_id="gob1", target_type="token", target_id="gob2",
                                 mode="ranged", range_m=2.0)

    def test_approach_stops_inside_ring(self) -> None:
        preview = approach_preview(self.db, map_id="default", token_id="gob1", target_type="token",
                                   target_id="gob2", mode="melee")
        self.assertFalse(preview["already_in_range"])
        self.assertTrue(preview["lands_in_range"])
        # 3 células -> para na adjacência: [5,5] -> [6,5] -> [7,5]
        self.assertEqual(preview["path"], [[5, 5], [6, 5], [7, 5]])
        self.assertIsNone(preview["remaining_m"])  # sem encontro: sem orçamento

    def test_approach_respects_budget(self) -> None:
        from app.combat_effects import init_effects
        init_effects(self.db)
        encounter = {"active": True, "battle_mode": True, "map_id": "default",
                     "participants": [{"target_type": "token", "target_id": "gob1"}],
                     "turn_index": 0, "attack_limit": 1, "attacks_used": 0,
                     "movement": {"turn_key": [None, None, "token", "gob1"], "budget_m": 1.5, "spent_m": 0.0}}
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE combat_effect_clock SET encounter_json=? WHERE id=1", (__import__("json").dumps(encounter),))
        preview = approach_preview(self.db, map_id="default", token_id="gob1", target_type="token",
                                   target_id="gob2", mode="melee")
        self.assertEqual(preview["remaining_m"], 1.5)
        self.assertFalse(preview["lands_in_range"])
        self.assertEqual(preview["path"], [[5, 5], [6, 5]])

    def test_ring_without_grid_reports_assisted(self) -> None:
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("DELETE FROM session_workspace_map_grids WHERE map_id='default'")
        ring = ring_for_action(self.db, ref="monster:vampiro:attack:0", attacker_token_id="gob1", map_id="default")
        self.assertFalse(ring["gridded"])

    def test_character_liveness_uses_sheet_hp_instead_of_a_stale_pin_copy(self):
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute('CREATE TABLE IF NOT EXISTS character_states(profile_id TEXT PRIMARY KEY,state_json TEXT,updated_at TEXT)')
            db.execute("INSERT INTO character_states VALUES('raziel',?, 'now')",(json.dumps({'current_hp':9}),))
            db.execute("UPDATE session_workspace_tokens SET token_type='character',character_id='raziel',current_hp=0 WHERE id='gob2'")
        params=dict(attacker_token_id='gob1',map_id='default',slot_override='ranged',max_override=9)
        target=ring_for_action(self.db,**params)['targets'][0]
        self.assertTrue(target['valid']);self.assertEqual(target['current_hp'],9)
        with closing(sqlite3.connect(self.db)) as db,db:
            db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'",(json.dumps({'current_hp':0}),))
            db.execute("UPDATE session_workspace_tokens SET current_hp=9 WHERE id='gob2'")
        target=ring_for_action(self.db,**params)['targets'][0]
        self.assertFalse(target['valid']);self.assertEqual(target['reason'],'Alvo sem PV')

    def test_player_ring_resolves_own_pin_and_never_lists_hidden_targets(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_maps SET visible_to_players=1")
            db.execute("UPDATE session_workspace_tokens SET token_type='character',character_id='morthak',visible_to_players=1 WHERE id='gob1'")
            db.execute("UPDATE session_workspace_tokens SET visible_to_players=0 WHERE id='gob2'")
        ring = ring_for_action(self.db, attacker_token_id='', attacker_character_id='morthak',
                               map_id='default', slot_override='touch', role='player')
        self.assertTrue(ring['gridded'])
        self.assertEqual('gob1', ring['origin']['token_id'])
        self.assertEqual([], ring['targets'])

    def test_player_cannot_use_hidden_attacker(self):
        with self.assertRaises(PermissionError):
            ring_for_action(self.db, attacker_token_id='gob1', map_id='default', slot_override='touch', role='player')

    def test_corpse_selection_excludes_living_and_used_or_unauthorized_bodies(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET current_hp=0,sheet_json=? WHERE id='gob2'",(json.dumps({'reanimation_allowed':True}),))
        params=dict(attacker_token_id='gob1',map_id='default',slot_override='ranged',max_override=9)
        self.assertFalse(ring_for_action(self.db,**params)['targets'][0]['valid'])
        self.assertTrue(ring_for_action(self.db,**params,target_kind='corpse')['targets'][0]['valid'])
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET sheet_json=? WHERE id='gob2'",(json.dumps({'reanimation_allowed':True,'reanimated_by':'another'}),))
        self.assertFalse(ring_for_action(self.db,**params,target_kind='corpse')['targets'][0]['valid'])

    def test_range_route_owner_can_aim_other_player_cannot_and_hidden_stays_private(self):
        from dataclasses import replace
        from unittest.mock import patch
        from fastapi.testclient import TestClient
        from app import main
        from app.access import AccessContext
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE session_workspace_maps SET visible_to_players=1")
            db.execute("UPDATE session_workspace_tokens SET token_type='character',character_id='morthak',visible_to_players=1 WHERE id='gob1'")
            db.execute("UPDATE session_workspace_tokens SET visible_to_players=0 WHERE id='gob2'")
        owner=AccessContext(mode='player',profile_id='morthak')
        main.app.dependency_overrides[main.require_any]=lambda:owner
        self.addCleanup(main.app.dependency_overrides.clear)
        self.addCleanup(__import__('gc').collect)
        with patch.object(main,'settings',replace(main.settings,database_path=self.db)), patch.object(main,'_playable_character',return_value={'definition':{'level':5}}):
            with TestClient(main.app) as client:
                route='/gm/grid/range?ref=technique:morthak:toque-sombrio&map_id=default'
                response=client.get(route)
                self.assertEqual(200,response.status_code,response.text)
                self.assertEqual('gob1',response.json()['origin']['token_id'])
                self.assertEqual([],response.json()['targets'])
                self.assertEqual(403,client.get(route+'&range_override_m=999').status_code)
                self.assertEqual(403,client.get('/gm/grid/range?ref=technique:raziel:mordida&map_id=default').status_code)


if __name__ == "__main__":
    unittest.main()
