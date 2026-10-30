"""Ficha de Dorn ponta a ponta (aliado do Mestre, com combate).

Visibilidade pública vs Mestre, reparo, fluxo 0 PV (desativado, não
morto), movimento de pin, especializações vazias e isolamento.
"""
from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main
from app.access import AccessContext
from app.character_creation import init_character_creation
from app.character_play import init_character_play
from app.combat import init_combat, resolve_attack
from app.combat_effects import init_effects
from app.dice_rolls import init_dice_rolls
from app.player_inventory import init_player_inventory
from app.session_ledger import init_session_ledger
from app.session_workspace import init_session_workspace, save_workspace_token
from app.vault_index import init_db as init_vault_index


def _gm():
    return AccessContext(mode="gm")


class DornSheetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "dorn_sheet.sqlite3"
        init_character_play(self.db)
        init_character_creation(self.db)
        init_combat(self.db)
        init_effects(self.db)
        init_dice_rolls(self.db)
        init_player_inventory(self.db)
        init_session_workspace(self.db)
        init_session_ledger(self.db)
        init_vault_index(self.db)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                ("Characters/Individual/Dorn7.md", "Dorn 7", "[]", "character", "[]", "{}",
                 "# Dorn 7", "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                ("dorn7", json.dumps({"current_hp": 10, "maximum_hp": 13, "temporary_hp": 0,
                                      "conditions": [], "resources": []}),
                 "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO character_definition_overrides(profile_id,data_json,updated_at) VALUES(?,?,?)",
                ("dorn7", json.dumps({"construct_traits": True, "level": 3}), "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,equipment_slot,notes,updated_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                ("dorn7", "Items/Kit.md", "Kit de Reparo", 2, 0, "", "", "2026-09-30T00:00:00+00:00"))
            connection.execute(
                "INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) VALUES(?,?,?,?,?,?)",
                ("dorn7", "Characters/Individual/Dorn7.md", "Dorn 7", "approved",
                 json.dumps({"attributes": {"strength": 14}, "character_class": {"level": 3, "class_name": "Mago"},
                             "attacks": {"melee_bonus": 1}}),
                 "2026-09-30T00:00:00+00:00"))
        self.dorn_pin = save_workspace_token(self.db, token_type="character", name="Dorn 7",
                                             latitude=10, longitude=10, character_id="dorn7",
                                             current_hp=13, maximum_hp=13)
        self.goblin = save_workspace_token(self.db, token_type="monster", name="Goblin",
                                           latitude=12, longitude=12, current_hp=6, maximum_hp=6,
                                           sheet={"armor_class": 10}, visible_to_players=True)
        settings = replace(main.settings, database_path=self.db, master_token="fixture-master")
        self._patcher = patch.object(main, "settings", settings)
        self._patcher.start()
        main.app.dependency_overrides[main.require_any] = _gm
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        import gc as _gc
        import time as _time
        try:
            self.client.close()
        finally:
            main.app.dependency_overrides.clear()
            self._patcher.stop()
            _gc.collect()
            last_error = None
            for _ in range(25):
                try:
                    self.temporary.cleanup()
                    last_error = None
                    break
                except PermissionError as error:
                    last_error = error
                    _time.sleep(0.2)
            if last_error is not None:
                raise last_error

    def _as_player(self):
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")

    def _as_gm(self):
        main.app.dependency_overrides[main.require_any] = _gm

    def test_gm_sees_state_player_sees_public(self):
        full = self.client.get("/characters/dorn7")
        self.assertEqual(200, full.status_code, full.text)
        self.assertEqual(10, full.json()["state"]["current_hp"])
        self._as_player()
        try:
            public = self.client.get("/characters/dorn7")
        finally:
            self._as_gm()
        self.assertEqual(200, public.status_code)
        self.assertIsNone(public.json().get("state"))

    def test_repair_heals_and_player_is_rejected(self):
        response = self.client.post("/characters/dorn7/techniques/dorn-reparo",
                                    json={"request_id": "sheet-rep-1"})
        self.assertEqual(200, response.status_code, response.text)
        with closing(sqlite3.connect(self.db)) as connection:
            hp = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])["current_hp"]
        self.assertGreater(hp, 10)
        self._as_player()
        try:
            denied = self.client.post("/characters/dorn7/techniques/dorn-reparo",
                                      json={"request_id": "sheet-rep-2"})
        finally:
            self._as_gm()
        self.assertEqual(403, denied.status_code)

    def test_zero_hp_disables_instead_of_killing(self):
        definition = {"id": "melee", "attacks": [{"id": "melee", "name": "Clava", "attack_bonus": 20,
                                                  "damage": "6d6", "weapon_item_path": "w"}]}
        resolution, _ = resolve_attack(
            self.db, request_id="sheet-zero-1", actor_character_id="vezemir", actor_name="Vezemir",
            requested_by_id="master", requested_by_role="gm", definition=definition, inventory=[],
            attack_id="melee",
            target={"type": "token", "id": self.dorn_pin["id"], "armor_class": 5, "current_hp": 13},
            roll_mode="physical", physical_d20=18, rng=lambda minimum,maximum: maximum)
        confirm = self.client.post(f"/combat/attacks/{resolution['resolution_id']}/confirm")
        self.assertEqual(200, confirm.status_code, confirm.text)
        with closing(sqlite3.connect(self.db)) as connection:
            token_hp = connection.execute("SELECT current_hp FROM session_workspace_tokens WHERE id=?",
                                          (self.dorn_pin["id"],)).fetchone()[0]
            state = json.loads(connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
        self.assertEqual(0, token_hp)
        self.assertIn("desativado", state.get("conditions", []))

    def test_pin_move_gm_ok_player_rejected(self):
        moved = self.client.patch(f"/gm/workspace/tokens/{self.dorn_pin['id']}/position",
                                  json={"latitude": 30, "longitude": 30})
        self.assertEqual(200, moved.status_code, moved.text)
        self._as_player()
        try:
            denied = self.client.patch(f"/gm/workspace/tokens/{self.dorn_pin['id']}/position",
                                       json={"latitude": 31, "longitude": 31})
        finally:
            self._as_gm()
        self.assertEqual(403, denied.status_code)

    def test_no_specializations_for_gm_ally(self):
        options = self.client.get("/characters/dorn7/specializations")
        self.assertEqual(200, options.status_code, options.text)
        self.assertEqual([], options.json()["options"])

    def test_player_cannot_act_as_dorn(self):
        self._as_player()
        try:
            response = self.client.post("/characters/dorn7/techniques/dorn-reparo",
                                        json={"request_id": "sheet-rep-x"})
        finally:
            self._as_gm()
        self.assertEqual(403, response.status_code)


if __name__ == "__main__":
    unittest.main()
