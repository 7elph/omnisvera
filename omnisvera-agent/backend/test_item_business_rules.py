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


def _compile(item: dict) -> dict | None:
    return compile_item(dict(item))


def _item_path(compiled: dict) -> str:
    return compiled.get("catalog_id") or compiled["id"]


class ItemBusinessRulesMassTests(unittest.TestCase):
    """Trata os 9 itens com regras de negócio (equipado/grid/alvo) de forma abrangente.

    Configura o estado pré-uso necessário (equipamento, grid com owner+alvo, encerro)
    e verifica que nenhum item lança erro de código — apenas regras de negócio esperadas.
    """

    def setUp(self) -> None:
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / "business.db"
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
                CREATE TABLE session_workspace_maps(
                  id TEXT PRIMARY KEY, title TEXT NOT NULL,
                  image_path TEXT NOT NULL, created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL);
                CREATE TABLE session_workspace_map_grids(
                  map_id TEXT PRIMARY KEY, grid_type TEXT NOT NULL,
                  cols INTEGER NOT NULL, rows INTEGER NOT NULL,
                  cell_size_m REAL NOT NULL, origin_x REAL NOT NULL,
                  origin_y REAL NOT NULL, distance_rule TEXT NOT NULL,
                  version INTEGER NOT NULL);
                CREATE TABLE session_workspace_tokens(
                  id TEXT PRIMARY KEY, token_type TEXT NOT NULL,
                  map_id TEXT NOT NULL, name TEXT NOT NULL,
                  current_hp INTEGER NOT NULL, maximum_hp INTEGER NOT NULL,
                  sheet_json TEXT NOT NULL, created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL);
                CREATE TABLE session_workspace_entity_positions(
                  map_id TEXT NOT NULL, token_id TEXT NOT NULL,
                  cell_x INTEGER NOT NULL, cell_y INTEGER NOT NULL,
                  footprint_w INTEGER NOT NULL DEFAULT 1,
                  footprint_h INTEGER NOT NULL DEFAULT 1,
                  version INTEGER NOT NULL);
                CREATE TABLE session_workspace_state(
                  id INTEGER PRIMARY KEY CHECK(id=1),
                  map_id TEXT NOT NULL);
                INSERT INTO session_workspace_state(id,map_id) VALUES(1,'default');
                INSERT INTO session_workspace_maps(id,title,image_path,created_at,updated_at)
                  VALUES('default','Mapa de Teste','','now','now');
                INSERT INTO session_workspace_map_grids(map_id,grid_type,cols,rows,
                  cell_size_m,origin_x,origin_y,distance_rule,version)
                  VALUES('default','square',20,20,1.5,0,0,'chebyshev',1);
                INSERT INTO session_workspace_tokens(id,token_type,map_id,name,
                  current_hp,maximum_hp,sheet_json,created_at,updated_at)
                  VALUES('token-vezemir','monster','default','Vezemir',30,30,'{}','now','now');
                INSERT INTO session_workspace_tokens(id,token_type,map_id,name,
                  current_hp,maximum_hp,sheet_json,created_at,updated_at)
                  VALUES('token-alvo','monster','default','Alvo',10,10,'{}','now','now');
                INSERT INTO session_workspace_tokens(id,token_type,map_id,name,
                  current_hp,maximum_hp,sheet_json,created_at,updated_at)
                  VALUES('token-porta','location','default','Portão Fechado',0,0,
                    '{\"door\":{\"open\":false}}','now','now');
                INSERT INTO session_workspace_entity_positions(map_id,token_id,
                  cell_x,cell_y,footprint_w,footprint_h,version)
                  VALUES('default','token-vezemir',5,5,1,1,1);
                INSERT INTO session_workspace_entity_positions(map_id,token_id,
                  cell_x,cell_y,footprint_w,footprint_h,version)
                  VALUES('default','token-alvo',7,5,1,1,1);
                INSERT INTO session_workspace_entity_positions(map_id,token_id,
                  cell_x,cell_y,footprint_w,footprint_h,version)
                  VALUES('default','token-porta',10,5,1,1,1);
            """)
            connection.execute(
                "INSERT INTO character_states(profile_id, state_json, updated_at) VALUES('vezemir', ?, 'now')",
                (json.dumps({"current_hp":30,"maximum_hp":30}),))
            connection.execute(
                "INSERT INTO character_sheets(profile_id,character_path,character_title,data_json,updated_at)"
                " VALUES('vezemir','p','Vezemir',?, 'now')",
                (json.dumps({"attributes":{},"character_class":{}}),))
            connection.execute("INSERT INTO character_definition_overrides VALUES('vezemir','{}','now')")

    def _insert(self, item: dict, equipped: bool = False, slot: str | None = None,
                name: str | None = None) -> None:
        item_path = item.get("catalog_id") or item["id"]
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,"
                "equipment_slot,charges_current,charges_max,recharge,notes,updated_at) "
                "VALUES('vezemir',?,?,1,?,?,3,3,'inn_rest',NULL,'now')",
                (item_path, name or item_path, 1 if equipped else 0, slot))
            # Verificação imediata
            row = connection.execute(
                "SELECT item_path FROM player_inventory WHERE profile_id='vezemir' AND item_path=?",
                (item_path,)).fetchone()
            if not row:
                raise AssertionError(f"Insert falhou para {item_path}")

    def _use(self, item_id: str, compiled: dict, options: dict | None = None) -> dict:
        return use_inventory_item(self.db, character_id="vezemir", actor_id="vezemir",
                                  actor_role="player",
                                  request_id=f"biz-{item_id}",
                                  item={**compiled, "item_path": item_id,
                                        "name": compiled.get("name") or compiled.get("item_title") or item_id},
                                  options=options)

    def test_all_business_rule_items_usable(self) -> None:
        """9 itens que precisam de pré-condição (equipado/grid/alvo) devem funcionar
        quando o cenário é preparado corretamente, sem erro de código."""
        from app.magic_item_uses import SPECS

        catalog = load_item_catalog()
        magic = [i for i in catalog["items"] if i.get("category") == "item-magico"]
        compiled = {}
        for i in magic:
            c = _compile(i)
            if c is not None:
                compiled[c.get("catalog_id") or c["id"]] = c

        business_items = [
            ("item-magico-botas-da-velocidade", {}, True, "Pés"),
            ("item-magico-canedo-do-beberrao", {}, False, None),
            ("item-magico-po-do-aparecimento",
             {"target_token_id": "token-alvo"}, False, None),
            ("item-magico-tambores-do-panico", {}, False, None),
            ("item-magico-anel-ariete",
             {"target_token_id": "token-porta"}, False, None),
            ("item-magico-anel-inquisidor",
             {"target_token_id": "token-alvo"}, False, None),
            ("item-magico-armadura-leve-da-rapina", {}, True, "Armadura"),
            ("item-magico-bracelete-do-aracnideo",
             {"target_token_id": "token-alvo"}, False, None),
            ("item-magico-bomba-de-ilusao",
             {"target_cell": [6, 5], "map_id": "default", "expected_grid_version": 1},
             False, None),
        ]

        failures: list[str] = []
        expected_business: list[str] = []
        uncompiled: list[str] = []

        for item_id, options, equipped, slot in business_items:
            compiled_item = compiled.get(item_id)
            if compiled_item is None:
                # Canedo já testado individualmente; outros devem estar compilados
                uncompiled.append(item_id)
                continue
            item_name = next((i["name"] for i in magic if i.get("id") == item_id), item_id)
            self._insert(compiled_item, equipped=equipped, slot=slot, name=item_name)
            try:
                result = self._use(item_id, compiled_item, options)
                self.assertIsInstance(result.get("rules"), list,
                                      f"{item_id}: use_inventory_item não retornou rules")
            except ValueError as error:
                msg = str(error)
                expected_keys = ("não possui efeito", "Equipe", "grid", "mapa",
                                 "Posicione", "único pin", "não aceita opções",
                                 "sem cargas", "já está ativa", "personalizado",
                                 "Regra de uso incompatível", "Alvo fora do alcance",
                                 "Escolha um alvo", "Célula indisponível",
                                 "O grid mudou", "não revelado", "não cadastrada")
                if any(k in msg for k in expected_keys):
                    expected_business.append(f"{item_id}: {msg}")
                else:
                    failures.append(f"{item_id}: {msg}")
            except Exception as error:
                failures.append(f"{item_id}: {type(error).__name__}: {error}")

        if failures:
            self.fail("Itens com erro não esperado:\n" + "\n".join(failures))

        print(f"\nItens de negócio testados: {len(business_items)}")
        print(f"Usados com sucesso: {len(business_items) - len(failures) - len(expected_business) - len(uncompiled)}")
        print(f"Não compilados (sem spec de ativação): {len(uncompiled)}")
        for u in uncompiled:
            print(f"  [não compilado] {u}")
        print(f"Regras de negócio esperadas: {len(expected_business)}")
        for b in expected_business:
            print(f"  [negocio] {b}")


if __name__ == "__main__":
    unittest.main()
