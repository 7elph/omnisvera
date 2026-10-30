"""Alcance no grid + movimento por personagem.

Corpo a corpo/toque exigem adjacência (1 célula) quando atacante e alvo
têm posição lógica no mesmo mapa; à distância respeita max_range_m quando
definido. Sem grid, o Mestre adjudica (passa sem validar).
"""
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.character_play import init_character_play
from app.combat import init_combat
from app.combat_effects import effect_command, effect_snapshot, init_effects
from app.dice_rolls import init_dice_rolls
from app.session_ledger import init_session_ledger
from app.session_workspace import init_session_workspace, save_workspace_token, set_workspace_map
from app.spatial_grid import check_attack_range, configure_grid
from app.spatial_grid import move_entity


class AttackRangeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "range.sqlite3"
        init_character_play(self.db)
        init_combat(self.db)
        init_effects(self.db)
        init_dice_rolls(self.db)
        init_session_workspace(self.db)
        init_session_ledger(self.db)
        self.map = set_workspace_map(self.db, title="Arena", image_path="a.svg",
                                     visible_to_players=True)["id"]
        self.pc = save_workspace_token(self.db, token_type="character", name="Vezemir",
                                       latitude=10, longitude=10, character_id="vezemir",
                                       map_id=self.map)
        self.ogre = save_workspace_token(self.db, token_type="monster", name="Ogro",
                                         latitude=90, longitude=90, current_hp=20, maximum_hp=20,
                                         sheet={"armor_class": 10}, visible_to_players=True,
                                         map_id=self.map)
        configure_grid(self.db, actor_id="master", role="gm", request_id="grid-001",
                       map_id=self.map, config=dict(cols=10, rows=10, cell_size_m=1.5))

    def tearDown(self):
        self.temporary.cleanup()

    def _pos(self, token_id):
        with closing(sqlite3.connect(self.db)) as connection:
            row = connection.execute("SELECT cell_x,cell_y,version FROM session_workspace_entity_positions"
                                     " WHERE map_id=? AND token_id=?", (self.map, token_id)).fetchone()
        return row

    def _place(self, token_id, x, y):
        with closing(sqlite3.connect(self.db)) as connection:
            state = effect_snapshot(connection)["version"]
        cx, cy, ver = self._pos(token_id)
        move_entity(self.db, actor_id="master", role="gm", request_id=f"place-{token_id}-{x}-{y}",
                    map_id=self.map, token_id=token_id, mode="GM_REPOSITION",
                    cells=self._path(cx, cy, x, y),
                    expected_position_version=ver, expected_grid_version=1,
                    expected_combat_version=state, load_movement=lambda _: "9 m")

    @staticmethod
    def _path(x0, y0, x1, y1):
        path = [[x0, y0]]
        x, y = x0, y0
        while x != x1:
            x += 1 if x1 > x else -1
            path.append([x, y])
        while y != y1:
            y += 1 if y1 > y else -1
            path.append([x, y])
        return path

    def test_melee_adjacent_ok_far_rejected(self):
        self._place(self.pc["id"], 2, 2)
        self._place(self.ogre["id"], 3, 2)
        result = check_attack_range(self.db, actor_character_id="vezemir", target_type="token",
                                    target_id=self.ogre["id"], slot="melee")
        self.assertTrue(result["checked"])
        self.assertEqual(1, result["cells"])
        self._place(self.ogre["id"], 6, 2)
        with self.assertRaisesRegex(ValueError, "corpo a corpo"):
            check_attack_range(self.db, actor_character_id="vezemir", target_type="token",
                               target_id=self.ogre["id"], slot="melee")

    def test_touch_requires_adjacency(self):
        self._place(self.pc["id"], 2, 2)
        self._place(self.ogre["id"], 4, 4)
        with self.assertRaisesRegex(ValueError, "corpo a corpo"):
            check_attack_range(self.db, actor_character_id="vezemir", target_type="token",
                               target_id=self.ogre["id"], slot="touch")
        self._place(self.ogre["id"], 3, 2)
        result = check_attack_range(self.db, actor_character_id="vezemir", target_type="token",
                                    target_id=self.ogre["id"], slot="touch")
        self.assertTrue(result["checked"])

    def test_ranged_respects_maximum(self):
        self._place(self.pc["id"], 0, 0)
        self._place(self.ogre["id"], 9, 0)
        with self.assertRaisesRegex(ValueError, "Fora de alcance"):
            check_attack_range(self.db, actor_character_id="vezemir", target_type="token",
                               target_id=self.ogre["id"], slot="ranged", max_range_m=10)
        result = check_attack_range(self.db, actor_character_id="vezemir", target_type="token",
                                    target_id=self.ogre["id"], slot="ranged", max_range_m=20)
        self.assertTrue(result["checked"])

    def test_ranged_without_maximum_passes(self):
        self._place(self.pc["id"], 0, 0)
        self._place(self.ogre["id"], 9, 9)
        result = check_attack_range(self.db, actor_character_id="vezemir", target_type="token",
                                    target_id=self.ogre["id"], slot="ranged")
        self.assertTrue(result["checked"])

    def test_approved_range_uses_each_maps_scale(self):
        from app.combat import attack_slot_and_max
        self._place(self.pc['id'],0,0)
        for scale,edge in ((1.5,6),(3,3)):
            with closing(sqlite3.connect(self.db)) as db,db:
                db.execute('UPDATE session_workspace_map_grids SET cell_size_m=? WHERE map_id=?',(scale,self.map))
            for action in ('pulseira-de-vinhas','adaga-de-osso','lamina-de-sangue'):
                slot,maximum=attack_slot_and_max(action,'ranged',5)
                with closing(sqlite3.connect(self.db)) as db,db:
                    db.execute('UPDATE session_workspace_entity_positions SET cell_x=?,cell_y=0 WHERE token_id=?',(edge,self.ogre['id']))
                self.assertEqual(9,check_attack_range(self.db,actor_character_id='vezemir',target_type='token',
                    target_id=self.ogre['id'],slot=slot,max_range_m=maximum)['meters'])
                with closing(sqlite3.connect(self.db)) as db,db:
                    db.execute('UPDATE session_workspace_entity_positions SET cell_x=? WHERE token_id=?',(edge+1,self.ogre['id']))
                with self.assertRaisesRegex(ValueError,'máximo 9'):
                    check_attack_range(self.db,actor_character_id='vezemir',target_type='token',
                        target_id=self.ogre['id'],slot=slot,max_range_m=maximum)

    def test_without_positions_passes_for_master(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("DELETE FROM session_workspace_entity_positions WHERE token_id=?",
                               (self.ogre["id"],))
        result = check_attack_range(self.db, actor_character_id="vezemir", target_type="token",
                                    target_id=self.ogre["id"], slot="melee")
        self.assertFalse(result["checked"])

    def test_character_target_uses_pin(self):
        friend = save_workspace_token(self.db, token_type="character", name="Morthak",
                                      latitude=10, longitude=10, character_id="morthak", map_id=self.map)
        self._place(self.pc["id"], 5, 5)
        self._place(friend["id"], 5, 6)
        result = check_attack_range(self.db, actor_character_id="vezemir", target_type="character",
                                    target_id="morthak", slot="melee")
        self.assertTrue(result["checked"])

    def test_each_sheet_moves_one_cell_in_battle(self):
        profiles = [("vezemir", "vezemir", "player"), ("morthak", "morthak", "player"),
                    ("raziel", "raziel", "player"), ("dorn7", "master", "gm")]
        for profile_id, actor_id, role in profiles:
            with closing(sqlite3.connect(self.db)) as connection, connection:
                connection.execute("INSERT OR IGNORE INTO character_states(profile_id,state_json,version,updated_at)"
                                   " VALUES(?,?,1,?)",
                                   (profile_id, '{"current_hp": 10, "maximum_hp": 10, "resources": []}', "t"))
            pin = save_workspace_token(self.db, token_type="character", name=profile_id,
                                       latitude=10, longitude=10, character_id=profile_id, map_id=self.map)
            with closing(sqlite3.connect(self.db)) as connection:
                version = effect_snapshot(connection)["version"]
            effect_command(self.db, actor_id="master", actor_role="gm",
                           request_id=f"move-enc-{profile_id}", expected_version=version, action="start",
                           payload={"map_id": self.map,
                                    "participants": [{"target_type": "character", "target_id": profile_id,
                                                      "initiative": 10}]})
            x, y, ver = self._pos(pin["id"])
            with closing(sqlite3.connect(self.db)) as connection:
                combat_version = effect_snapshot(connection)["version"]
            moved = move_entity(self.db, actor_id=actor_id, role=role,
                                request_id=f"move-{profile_id}-1", map_id=self.map, token_id=pin["id"],
                                mode="COMBAT_MOVE", cells=[[x, y], [x + 1, y]],
                                expected_position_version=ver, expected_grid_version=1,
                                expected_combat_version=combat_version, load_movement=lambda _: "9 m")
            self.assertIn("movement", moved)
            with closing(sqlite3.connect(self.db)) as connection:
                version = effect_snapshot(connection)["version"]
            effect_command(self.db, actor_id="master", actor_role="gm", request_id=f"move-end-{profile_id}",
                           expected_version=version, action="end", payload={})

    def test_targets_listing_marks_validity(self):
        from app.spatial_grid import targets_in_range
        self._place(self.pc["id"], 2, 2)
        self._place(self.ogre["id"], 3, 3)
        listed = targets_in_range(self.db, actor_character_id="vezemir", slot="melee", role="gm")
        self.assertTrue(listed["gridded"])
        ogre = next(t for t in listed["targets"] if t["id"] == self.ogre["id"])
        self.assertTrue(ogre["valid"])
        self.assertEqual(1, ogre["cells"])
        self._place(self.ogre["id"], 8, 8)
        listed = targets_in_range(self.db, actor_character_id="vezemir", slot="melee", role="gm")
        ogre = next(t for t in listed["targets"] if t["id"] == self.ogre["id"])
        self.assertFalse(ogre["valid"])
        ranged = targets_in_range(self.db, actor_character_id="vezemir", slot="ranged",
                                  max_range_m=25, role="gm")
        ogre = next(t for t in ranged["targets"] if t["id"] == self.ogre["id"])
        self.assertTrue(ogre["valid"])
        short = targets_in_range(self.db, actor_character_id="vezemir", slot="ranged",
                                 max_range_m=5, role="gm")
        ogre = next(t for t in short["targets"] if t["id"] == self.ogre["id"])
        self.assertFalse(ogre["valid"])

    def test_targets_hide_ungridded_and_enemy_tokens_from_strangers(self):
        from app.spatial_grid import targets_in_range
        hidden = save_workspace_token(self.db, token_type="monster", name="Oculto",
                                      latitude=10, longitude=10, current_hp=5, maximum_hp=5,
                                      sheet={}, visible_to_players=False, map_id=self.map)
        self._place(self.pc["id"], 2, 2)
        self._place(hidden["id"], 2, 3)
        gm_listed = targets_in_range(self.db, actor_character_id="vezemir", slot="melee", role="gm")
        self.assertTrue(any(t["id"] == hidden["id"] for t in gm_listed["targets"]))
        # sem grid no mapa: fallback manual
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("DELETE FROM session_workspace_map_grids WHERE map_id=?", (self.map,))
        fallback = targets_in_range(self.db, actor_character_id="vezemir", slot="melee", role="gm")
        self.assertFalse(fallback["gridded"])
        self.assertEqual([], fallback["targets"])

    def test_slot_mapping_keeps_ranged_max_only_where_approved(self):
        from app.combat import attack_slot_and_max
        self.assertEqual(("melee", None), attack_slot_and_max("melee", None, 5))
        self.assertEqual(("melee", None), attack_slot_and_max("mordida", None, 2))
        self.assertEqual(("touch", None), attack_slot_and_max("toque-sombrio", None, 3))
        self.assertEqual(("ranged", 25), attack_slot_and_max("misseis-magicos", None, 5))
        self.assertEqual(("ranged", 9), attack_slot_and_max("adaga-de-osso", None, 3))
        self.assertEqual(("ranged", 9), attack_slot_and_max("lamina-de-sangue", "ranged", 2))
        self.assertEqual(("ranged", 9), attack_slot_and_max("pulseira-de-vinhas", "ranged", 5))
        self.assertEqual(("melee", None), attack_slot_and_max("lamina-de-sangue", "melee", 2))

    def test_combat_move_within_budget_ok_excess_rejected(self):
        with closing(sqlite3.connect(self.db)) as connection:
            version = effect_snapshot(connection)["version"]
        effect_command(self.db, actor_id="master", actor_role="gm", request_id="range-enc-1",
                       expected_version=version, action="start",
                       payload={"map_id": self.map,
                                "participants": [{"target_type": "character", "target_id": "vezemir", "initiative": 10}]})
        x, y, ver = self._pos(self.pc["id"])
        with closing(sqlite3.connect(self.db)) as connection:
            combat_version = effect_snapshot(connection)["version"]
        moved = move_entity(self.db, actor_id="vezemir", role="player", request_id="range-move-1",
                            map_id=self.map, token_id=self.pc["id"], mode="COMBAT_MOVE",
                            cells=[[x, y], [x + 1, y]], expected_position_version=ver,
                            expected_grid_version=1, expected_combat_version=combat_version,
                            load_movement=lambda _: "9 m")
        self.assertIn("movement", moved)
        long_path = [[x + 1 + i, y] for i in range(9) if x + 1 + i < 10]
        self.assertGreater(len(long_path), 6)
        with self.assertRaisesRegex(ValueError, "limite"):
            move_entity(self.db, actor_id="vezemir", role="player", request_id="range-move-2",
                        map_id=self.map, token_id=self.pc["id"], mode="COMBAT_MOVE",
                        cells=long_path, expected_position_version=ver + 1,
                        expected_grid_version=1,
                        expected_combat_version=moved["combat_version"],
                        load_movement=lambda _: "9 m")


if __name__ == "__main__":
    unittest.main()
