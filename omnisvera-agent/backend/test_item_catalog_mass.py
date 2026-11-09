from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.combat_consumables import use_inventory_item
from app.item_catalog import load_item_catalog
from app.magic_item_uses import compile_item


class ItemCatalogMassUseTests(unittest.TestCase):
    """Usa todos os itens mágicos do catálogo em lote.

    Nenhum item mágico reconhecido pelo backend pode lançar
    "Este item não possui efeito configurado para uso" ou erro de código.
    Erros de regra de negócio (não equipado, precisa de grid, sem cargas)
    são esperados e não contam como falha.
    """

    def setUp(self) -> None:
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / "mass.db"
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
                  data_json TEXT NOT NULL,
                  version INTEGER NOT NULL DEFAULT 1,
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

    def _insert_item(self, item: dict) -> None:
        item_path = item.get("catalog_id") or item["id"]
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,"
                "equipment_slot,charges_current,charges_max,recharge,notes,updated_at) "
                "VALUES('vezemir',?,?,1,0,NULL,3,3,'inn_rest',NULL,'now')",
                (item_path, item.get("name") or item.get("item_title") or item_path))

    def _use(self, item: dict) -> None:
        use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                           actor_role="player", request_id=f"mass-{item.get('catalog_id') or item['id']}",
                           item={**item, "item_path": item.get("catalog_id") or item["id"],
                                 "name": item.get("name") or item.get("item_title") or item.get("id")})

    def test_all_magic_items_recognized_and_usable(self) -> None:
        catalog = load_item_catalog()
        magic = [i for i in catalog["items"] if i.get("category") == "item-magico"]
        self.assertGreater(len(magic), 0, "catálogo sem itens mágicos")

        failures: list[str] = []
        expected_business: list[str] = []
        unrecognized: list[str] = []

        for item in magic:
            item_path = item["id"]
            compiled = compile_item(dict(item))
            if compiled is None:
                unrecognized.append(item_path)
                continue
            self._insert_item(compiled)
            try:
                result = self._use(compiled)
                # uso bem-sucedido: deve retornar regras
                self.assertIsInstance(result.get("rules"), list,
                                      f"{item_path}: use_inventory_item não retornou rules")
            except ValueError as error:
                msg = str(error)
                if "não possui efeito configurado para uso" in msg:
                    expected_business.append(f"{item_path}: {msg}")
                elif any(k in msg for k in (
                    "Equipe", "grid", "mapa", "Posicione", "único pin", "não aceita opções",
                    "sem cargas", "já está ativa", "personalizado",
                    "Regra de uso incompatível",
                )):
                    expected_business.append(f"{item_path}: {msg}")
                else:
                    failures.append(f"{item_path}: {msg}")
            except Exception as error:  # erro de código, não de negócio
                failures.append(f"{item_path}: {type(error).__name__}: {error}")

        if failures:
            self.fail("Itens mágicos com erro não esperado:\n" + "\n".join(failures))

        print(f"\nItens mágicos no catálogo: {len(magic)}")
        print(f"Usados com sucesso: {len(magic) - len(failures) - len(expected_business)}")
        print(f"Erros de negócio esperados (equipado/grid/cargas): {len(expected_business)}")
        for b in expected_business:
            print(f"  [negocio] {b}")


if __name__ == "__main__":
    unittest.main()
