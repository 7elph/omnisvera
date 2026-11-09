from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.combat_consumables import use_inventory_item
from app.magic_item_uses import spec_for
from app.player_inventory import init_player_inventory, upsert_inventory


class CanedoDoBeberrãoTests(unittest.TestCase):
    """Uso de item mágico de ponta a ponta: Canedo do Beberrão (3 cargas/dia, d100)."""

    def setUp(self) -> None:
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / "item_use.db"
        with closing(sqlite3.connect(self.db, timeout=30)) as connection, connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA busy_timeout=30000")
            connection.executescript("""
                CREATE TABLE character_states(
                  profile_id TEXT PRIMARY KEY,
                  state_json TEXT NOT NULL,
                  version INTEGER DEFAULT 1,
                  updated_at TEXT NOT NULL);
                CREATE TABLE character_sheets(
                  profile_id TEXT PRIMARY KEY,
                  character_path TEXT NOT NULL,
                  character_title TEXT NOT NULL,
                  data_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL);
                CREATE TABLE character_definition_overrides(
                  profile_id TEXT PRIMARY KEY,
                  data_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL);
                CREATE TABLE player_inventory(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  profile_id TEXT NOT NULL,
                  item_path TEXT NOT NULL,
                  item_title TEXT NOT NULL,
                  quantity INTEGER NOT NULL DEFAULT 1,
                  equipped INTEGER NOT NULL DEFAULT 0,
                  equipment_slot TEXT,
                  charges_current INTEGER,
                  charges_max INTEGER,
                  recharge TEXT,
                  notes TEXT,
                  updated_at TEXT NOT NULL,
                  UNIQUE(profile_id, item_path));
                CREATE TABLE combat_effects(
                  id TEXT PRIMARY KEY,
                  target_type TEXT NOT NULL,
                  target_id TEXT NOT NULL,
                  data_json TEXT NOT NULL,
                  active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE combat_effect_clock(
                  id INTEGER PRIMARY KEY CHECK(id=1),
                  round INTEGER NOT NULL,
                  version INTEGER NOT NULL,
                  encounter_json TEXT NOT NULL DEFAULT '{}',
                  world_phase TEXT NOT NULL DEFAULT 'unset');
                INSERT OR IGNORE INTO combat_effect_clock(id,round,version)
                  VALUES(1,1,0);
                CREATE TABLE combat_effect_commands(
                  request_id TEXT PRIMARY KEY,
                  fingerprint TEXT NOT NULL,
                  response_json TEXT NOT NULL);
                CREATE TABLE session_ledger(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  source_type TEXT NOT NULL,
                  source_id TEXT NOT NULL,
                  event_kind TEXT NOT NULL,
                  actor_id TEXT NOT NULL,
                  actor_name TEXT NOT NULL,
                  actor_role TEXT NOT NULL,
                  character_id TEXT,
                  title TEXT NOT NULL,
                  detail_json TEXT,
                  visibility TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  game_session_id TEXT);
                CREATE TABLE inventory_item_conditions(
                  inventory_id INTEGER PRIMARY KEY REFERENCES player_inventory(id)
                    ON DELETE CASCADE,
                  data_json TEXT NOT NULL,
                  version INTEGER NOT NULL DEFAULT 1,
                  updated_at TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS inventory_condition_cleanup
                  AFTER DELETE ON player_inventory BEGIN
                    DELETE FROM inventory_item_conditions WHERE inventory_id=OLD.id;
                  END;
                CREATE TABLE character_events(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  character_id TEXT NOT NULL,
                  session_id TEXT,
                  game_session_id TEXT,
                  actor_id TEXT NOT NULL,
                  actor_role TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  field TEXT NOT NULL,
                  before_json TEXT,
                  after_json TEXT,
                  reason TEXT,
                  created_at TEXT NOT NULL,
                  reverted_at TEXT,
                  reverted_by TEXT);
            """)
            connection.execute(
                "INSERT INTO character_states(profile_id, state_json, updated_at) VALUES('vezemir', ?, 'now')",
                (json.dumps({"current_hp": 30, "maximum_hp": 30}),))
            connection.execute(
                "INSERT INTO character_sheets(profile_id, character_path, character_title, data_json, updated_at)"
                " VALUES('vezemir', 'p', 'Vezemir', ?, 'now')",
                (json.dumps({"attributes": {}, "character_class": {}}),))
            connection.execute("INSERT INTO character_definition_overrides VALUES('vezemir', '{}', 'now')")
            connection.execute(
                "INSERT INTO player_inventory(profile_id, item_path, item_title, quantity, equipped, "
                "equipment_slot, charges_current, charges_max, recharge, notes, updated_at) "
                "VALUES('vezemir', 'compendium:item-magico-caneco-do-beberrao', 'Canedo do Beberrão', 1, 0, "
                "NULL, 3, 3, 'inn_rest', NULL, 'now')")

    def _item(self) -> dict:
        return {"item_path": "compendium:item-magico-caneco-do-beberrao",
                "id": "compendium:item-magico-caneco-do-beberrao",
                "name": "Canedo do Beberrão",
                "item_title": "Canedo do Beberrão",
                "quantity": 1,
                "charges_current": 3,
                "charges_max": 3,
                "recharge": "inn_rest",
                "usable": True,
                "effect_rules": [{
                    "id": "compendium:item-magico-caneco-do-beberrao:activate",
                    "trigger": "on_use",
                    "kind": "magic_activation",
                    "value": 1,
                    "label": "Preenche o caneco; rola 1d100, três usos por descanso diário.",
                    "target": "self",
                    "duration": "instant",
                    "stacking": "non_stack",
                }],
                "mechanics": {
                    "family_schema": 1,
                    "family": "magic_activation",
                    "kind": "accessory",
                    "magical": True,
                    "magic_activation_schema": 1,
                    "magic_activation_id": "compendium:item-magico-caneco-do-beberrao",
                    "equipment_slots": ["Acessório"],
                    "approved_equipment_slots": ["Acessório"],
                    "slot_limit": 1,
                    "charges_max": 3,
                    "consume_mode": "charges",
                    "recharge": "inn_rest",
                    "family_gaps": [],
                }}

    def test_use_decrements_charge_and_records_ledger(self) -> None:
        result = use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                                    actor_role="player", request_id="canedo-001", item=self._item())
        self.assertEqual(len(result["rules"]), 1)
        rule = result["rules"][0]
        self.assertEqual(rule["kind"], "magic_activation")
        self.assertEqual(rule["magic_item"], "item-magico-caneco-do-beberrao")
        self.assertIn("d100", rule["label"])
        with closing(sqlite3.connect(self.db)) as connection:
            connection.row_factory = sqlite3.Row
            inventory = connection.execute(
                "SELECT charges_current FROM player_inventory WHERE profile_id='vezemir' "
                "AND item_path='compendium:item-magico-caneco-do-beberrao'").fetchone()
            self.assertEqual(inventory["charges_current"], 2)
            ledger = connection.execute(
                "SELECT title, detail_json FROM session_ledger WHERE event_kind='action' "
                "AND source_type='item_use'").fetchall()
            self.assertEqual(len(ledger), 1)
            self.assertIn("Canedo do Beberrão", ledger[0][0])

    def test_use_after_three_charges_is_blocked(self) -> None:
        for request_id in ("canedo-001", "canedo-002", "canedo-003"):
            use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                               actor_role="player", request_id=request_id, item=self._item())
        with self.assertRaises(ValueError):
            use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                               actor_role="player", request_id="canedo-004", item=self._item())

    def test_idempotent_replay(self) -> None:
        first = use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                                   actor_role="player", request_id="canedo-replay", item=self._item())
        second = use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                                    actor_role="player", request_id="canedo-replay", item=self._item())
        self.assertEqual(first, second)
        with closing(sqlite3.connect(self.db)) as connection:
            connection.row_factory = sqlite3.Row
            charges = connection.execute(
                "SELECT charges_current FROM player_inventory WHERE profile_id='vezemir' "
                "AND item_path='compendium:item-magico-caneco-do-beberrao'").fetchone()["charges_current"]
            self.assertEqual(charges, 2)  # só gastou uma vez


if __name__ == "__main__":
    unittest.main()
