"""Accessory slots fit 3 (campaign rule); an editor-default slot_limit of 1
must not undercut that floor. Other slots stay at 1.
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
from app.combat import init_combat
from app.combat_effects import init_effects
from app.character_play import init_character_play
from app.character_creation import init_character_creation
from app.dice_rolls import init_dice_rolls
from app.session_ledger import init_session_ledger
from app.session_workspace import init_session_workspace
from app.vault_index import init_db as init_vault_index
from app.player_inventory import upsert_inventory


class EquipSlotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "slots.sqlite3"
        for init in (init_character_play, init_character_creation, init_combat, init_effects,
                     init_dice_rolls, init_session_workspace, init_session_ledger, init_vault_index):
            init(self.db)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            for name in ("Medalhao", "Moeda", "Anel", "Broche"):
                connection.execute(
                    "INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at)"
                    " VALUES(?,?,?,?,?,?,?,?)",
                    (f"Items/{name}.md", name, "[]", "item", "[]", "{}", f"# {name}",
                     "2026-09-30T00:00:00+00:00"),
                )
            connection.execute(
                "INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                ("Characters/Individual/Vezemir.md", "Vezemir", "[]", "character", "[]", "{}",
                 "# Vezemir", "2026-09-30T00:00:00+00:00"),
            )
            connection.execute(
                "INSERT INTO character_sheets(profile_id,character_path,character_title,status,"
                "data_json,updated_at) VALUES(?,?,?,?,?,?)",
                ("vezemir", "Characters/Individual/Vezemir.md", "Vezemir", "approved",
                 json.dumps({"attributes": {"strength": 13}, "character_class": {"level": 2}}),
                 "2026-09-30T00:00:00+00:00"),
            )
            # Custom Moeda carrying the editor-default slot_limit of 1.
            connection.execute(
                "INSERT INTO session_custom_items(name,item_type,description,effects_json,usable,"
                "image_path,created_at,updated_at,effect_rules_json,mechanics_json)"
                " VALUES(?,?,?,?,?,?,?,?,?,?)",
                ("Moeda Misteriosa", "item", "", "[]", 0, None,
                 "2026-09-30T00:00:00+00:00", "2026-09-30T00:00:00+00:00", "[]",
                 json.dumps({"equipment_slots": ["Acessório"], "slot_limit": 1})),
            )
            self.moeda_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        upsert_inventory(self.db, profile_id="vezemir", item_path="Items/Medalhao.md",
                         item_title="Medalhao", quantity=1, equipped=True,
                         notes=None, equipment_slot="Acessório")
        upsert_inventory(self.db, profile_id="vezemir",
                         item_path=f"session-item:{self.moeda_id}",
                         item_title="Moeda Misteriosa", quantity=1, equipped=False, notes=None)
        for name in ("Anel", "Broche"):
            upsert_inventory(self.db, profile_id="vezemir", item_path=f"Items/{name}.md",
                             item_title=name, quantity=1, equipped=False, notes=None)
        settings = replace(main.settings, database_path=self.db, master_token="fixture-master")
        self._patcher = patch.object(main, "settings", settings)
        self._patcher.start()
        main.app.dependency_overrides[main.require_any] = lambda: AccessContext(mode="player", profile_id="vezemir")
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
            for _ in range(25):
                try:
                    self.temporary.cleanup()
                    break
                except PermissionError:
                    _time.sleep(0.2)

    def equip(self, item_path):
        return self.client.post("/characters/vezemir/actions",
                                json={"action": "equip_item",
                                      "payload": {"item_path": item_path,
                                                  "equipment_slot": "Acessório"}})

    def test_accessory_floor_is_three_despite_item_limit_one(self):
        response = self.equip(f"session-item:{self.moeda_id}")
        self.assertEqual(200, response.status_code, response.text)
        response = self.equip("Items/Anel.md")
        self.assertEqual(200, response.status_code, response.text)
        response = self.equip("Items/Broche.md")
        self.assertEqual(400, response.status_code)


if __name__ == "__main__":
    unittest.main()
