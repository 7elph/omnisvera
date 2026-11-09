from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.combat_consumables import use_inventory_item
from app.player_inventory import init_player_inventory, upsert_inventory


class ArmaduraRapinaTests(unittest.TestCase):
    """Uso de item mágico equipado: Armadura Leve da Rapina (3 ativações/dia, +3 CA por 1d4 rodadas)."""

    def setUp(self) -> None:
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / "rapina.db"
        with closing(sqlite3.connect(self.db, timeout=30)) as connection, connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA busy_timeout=30000")
            connection.executescript("""
                CREATE TABLE character_states(
                  profile_id TEXT PRIMARY KEY, state_json TEXT NOT NULL,
                  version INTEGER DEFAULT 1, updated_at TEXT NOT NULL);
                CREATE TABLE character_sheets(
                  profile_id TEXT PRIMARY KEY, character_path TEXT NOT NULL,
                  character_title TEXT NOT NULL, data_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL);
                CREATE TABLE character_definition_overrides(
                  profile_id TEXT PRIMARY KEY, data_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL);
                CREATE TABLE player_inventory(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  profile_id TEXT NOT NULL, item_path TEXT NOT NULL,
                  item_title TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 1,
                  equipped INTEGER NOT NULL DEFAULT 0, equipment_slot TEXT,
                  charges_current INTEGER, charges_max INTEGER, recharge TEXT,
                  notes TEXT, updated_at TEXT NOT NULL,
                  UNIQUE(profile_id, item_path));
                CREATE TABLE combat_effects(
                  id TEXT PRIMARY KEY, target_type TEXT NOT NULL,
                  target_id TEXT NOT NULL, data_json TEXT NOT NULL,
                  active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE combat_effect_clock(
                  id INTEGER PRIMARY KEY CHECK(id=1), round INTEGER NOT NULL,
                  version INTEGER NOT NULL, encounter_json TEXT NOT NULL DEFAULT '{}',
                  world_phase TEXT NOT NULL DEFAULT 'unset');
                INSERT OR IGNORE INTO combat_effect_clock(id,round,version)
                  VALUES(1,1,0);
                CREATE TABLE combat_effect_commands(
                  request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                  response_json TEXT NOT NULL);
                CREATE TABLE session_ledger(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  source_type TEXT NOT NULL, source_id TEXT NOT NULL,
                  event_kind TEXT NOT NULL, actor_id TEXT NOT NULL,
                  actor_name TEXT NOT NULL, actor_role TEXT NOT NULL,
                  character_id TEXT, title TEXT NOT NULL, detail_json TEXT,
                  visibility TEXT NOT NULL, created_at TEXT NOT NULL,
                  game_session_id TEXT);
                CREATE TABLE inventory_item_conditions(
                  inventory_id INTEGER PRIMARY KEY REFERENCES player_inventory(id)
                    ON DELETE CASCADE,
                  data_json TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
                  updated_at TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS inventory_condition_cleanup
                  AFTER DELETE ON player_inventory BEGIN
                    DELETE FROM inventory_item_conditions WHERE inventory_id=OLD.id;
                  END;
                CREATE TABLE character_events(
                  id INTEGER PRIMARY KEY AUTOINCREMENT, character_id TEXT NOT NULL,
                  session_id TEXT, game_session_id TEXT, actor_id TEXT NOT NULL,
                  actor_role TEXT NOT NULL, event_type TEXT NOT NULL,
                  field TEXT NOT NULL, before_json TEXT, after_json TEXT,
                  reason TEXT, created_at TEXT NOT NULL, reverted_at TEXT,
                  reverted_by TEXT);
                CREATE INDEX IF NOT EXISTS idx_character_events_character
                  ON character_events(character_id, id DESC);
            """)
            connection.execute(
                "INSERT INTO character_states(profile_id, state_json, updated_at) VALUES('vezemir', ?, 'now')",
                (json.dumps({"current_hp":30,"maximum_hp":30}),))
            connection.execute(
                "INSERT INTO character_sheets(profile_id,character_path,character_title,data_json,updated_at)"
                " VALUES('vezemir','p','Vezemir',?, 'now')",
                (json.dumps({"attributes":{},"character_class":{}}),))
            connection.execute("INSERT INTO character_definition_overrides VALUES('vezemir','{}','now')")
            connection.execute(
                "INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,"
                "equipment_slot,charges_current,charges_max,recharge,notes,updated_at) "
                "VALUES('vezemir','compendium:item-magico-armadura-leve-da-rapina','Armadura Leve da Rapina',"
                "1,0,'Armadura',3,3,'inn_rest',NULL,'now')")

    def _item(self) -> dict:
        return {"item_path":"compendium:item-magico-armadura-leve-da-rapina",
                "id":"item-magico-armadura-leve-da-rapina",
                "name":"Armadura Leve da Rapina",
                "item_title":"Armadura Leve da Rapina",
                "quantity":1,"charges_current":3,"charges_max":3,"recharge":"inn_rest",
                "usable":True,
                "effect_rules":[{"id":"item-magico-armadura-leve-da-rapina:activate",
                    "trigger":"on_use","kind":"magic_activation","value":1,
                    "label":"CA +3 por 1d4 rodadas","target":"self",
                    "duration":"instant","stacking":"non_stack"}],
                "mechanics":{"family_schema":1,"family":"magic_activation","kind":"armor",
                    "magical":True,"magic_activation_schema":1,
                    "magic_activation_id":"item-magico-armadura-leve-da-rapina",
                    "equipment_slots":["Armadura"],
                    "approved_equipment_slots":["Armadura"],
                    "slot_limit":1,"charges_max":3,"consume_mode":"charges",
                    "recharge":"inn_rest","family_gap":[]}}

    def _equip(self) -> None:
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE player_inventory SET equipped=1 WHERE profile_id='vezemir' "
                               "AND item_path='compendium:item-magico-armadura-leve-da-rapina'")

    def test_use_equipped_creates_effect_and_decrements(self) -> None:
        self._equip()
        result = use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                                    actor_role="player", request_id="rapina-001", item=self._item())
        self.assertEqual(len(result["rules"]), 1)
        rule = result["rules"][0]
        self.assertEqual(rule["kind"], "magic_activation")
        self.assertEqual(rule["magic_item"], "item-magico-armadura-leve-da-rapina")
        self.assertIn("CA +3", rule["label"])
        with closing(sqlite3.connect(self.db)) as connection:
            connection.row_factory = sqlite3.Row
            charges = connection.execute(
                "SELECT charges_current FROM player_inventory WHERE profile_id='vezemir' "
                "AND item_path='compendium:item-magico-armadura-leve-da-rapina'").fetchone()["charges_current"]
            self.assertEqual(charges, 2)
            effects = connection.execute(
                "SELECT data_json FROM combat_effects WHERE data_json LIKE '%Armadura Leve da Rapina%'").fetchall()
            self.assertGreaterEqual(len(effects), 1)

    def test_use_without_equipped_is_blocked(self) -> None:
        # não equipa
        with self.assertRaises(ValueError):
            use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                               actor_role="player", request_id="rapina-002", item=self._item())

    def test_after_three_activations_is_blocked(self) -> None:
        self._equip()
        for request_id in ("rapina-a","rapina-b","rapina-c"):
            use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                               actor_role="player", request_id=request_id, item=self._item())
            with closing(sqlite3.connect(self.db)) as connection, connection:
                connection.execute("UPDATE combat_effects SET active=0")
        with self.assertRaises(ValueError):
            use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                               actor_role="player", request_id="rapina-d", item=self._item())

    def test_idempotent_replay(self) -> None:
        self._equip()
        first = use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                                   actor_role="player", request_id="rapina-replay", item=self._item())
        second = use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                                    actor_role="player", request_id="rapina-replay", item=self._item())
        self.assertEqual(first, second)
        with closing(sqlite3.connect(self.db)) as connection:
            connection.row_factory = sqlite3.Row
            charges = connection.execute(
                "SELECT charges_current FROM player_inventory WHERE profile_id='vezemir' "
                "AND item_path='compendium:item-magico-armadura-leve-da-rapina'").fetchone()["charges_current"]
            self.assertEqual(charges, 2)


if __name__ == "__main__":
    unittest.main()
