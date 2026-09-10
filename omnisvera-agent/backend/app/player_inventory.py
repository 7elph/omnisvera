from __future__ import annotations

import sqlite3
import re
import unicodedata
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_DAMAGE_FORMULA_PATTERN = re.compile(r"(?<![a-z0-9])(\d{1,2}\s*d\s*\d{1,4}(?:\s*[+-]\s*\d{1,4})?)(?![a-z0-9])", re.IGNORECASE)


def _normalized_item_text(value: Any) -> str:
    return "".join(
        character for character in unicodedata.normalize("NFD", str(value or "").casefold())
        if unicodedata.category(character) != "Mn"
    )


def normalize_inventory_item_mechanics(item: dict[str, Any]) -> dict[str, Any]:
    """Fill safe mechanics omitted by legacy/custom inventory records."""
    record = dict(item)
    mechanics = dict(record.get("mechanics") or {})
    text = _normalized_item_text(f"{record.get('item_title') or record.get('name') or ''} {record.get('item_type') or ''}")

    damage_formula = str(record.get("damage_formula") or mechanics.get("damage_formula") or "").strip()
    if not damage_formula:
        raw_effects = record.get("effects") or []
        effects = raw_effects if isinstance(raw_effects, list) else [raw_effects]
        candidates = [*effects, record.get("description") or ""]
        match = next((_DAMAGE_FORMULA_PATTERN.search(str(candidate)) for candidate in candidates if candidate), None)
        if match:
            damage_formula = re.sub(r"\s+", "", match.group(1)).lower()
    if damage_formula:
        record["damage_formula"] = damage_formula
        mechanics["damage_formula"] = damage_formula

    is_weapon = (
        "arma" in text
        or any(term in text for term in ("cajado", "bordao", "espada", "machado", "adaga", "lanca", "martelo", "maca", "mangual", "foice", "sabre", "tridente", "arco", "besta"))
        or (bool(damage_formula) and "escudo" not in text and "muralha" not in text)
    )
    if "escudo" in text or "muralha" in text:
        mechanics["equipment_slots"] = ["Mão secundária"]
    elif "armadura" in text or "manto" in text:
        mechanics["equipment_slots"] = ["Armadura"]
    elif is_weapon:
        # Weapon category describes what the item is; the player chooses how it
        # is being used in this loadout. Keep this rule identical for Vault and
        # session-created items so every character gets both combat slots.
        mechanics["equipment_slots"] = ["Corpo a corpo", "À distância"]

    record["mechanics"] = mechanics
    return record


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_player_inventory(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_inventory (
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
              UNIQUE(profile_id, item_path)
            )
            """
        )
        for column, definition in (
            ("equipment_slot", "TEXT"),
            ("charges_current", "INTEGER"),
            ("charges_max", "INTEGER"),
            ("recharge", "TEXT"),
        ):
            try:
                connection.execute(f"ALTER TABLE player_inventory ADD COLUMN {column} {definition}")
            except sqlite3.OperationalError as error:
                if "duplicate column" not in str(error).lower():
                    raise


def upsert_inventory(database_path: Path, *, profile_id: str, item_path: str, item_title: str, quantity: int, equipped: bool, notes: str | None, equipment_slot: str | None = None, charges_current: int | None = None, charges_max: int | None = None, recharge: str | None = None) -> dict[str, Any]:
    init_player_inventory(database_path)
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,equipment_slot,charges_current,charges_max,recharge,notes,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(profile_id,item_path) DO UPDATE SET
              item_title=excluded.item_title, quantity=excluded.quantity, equipped=excluded.equipped,
              equipment_slot=excluded.equipment_slot,
              charges_current=COALESCE(excluded.charges_current,player_inventory.charges_current),
              charges_max=COALESCE(excluded.charges_max,player_inventory.charges_max),
              recharge=COALESCE(excluded.recharge,player_inventory.recharge),
              notes=excluded.notes, updated_at=excluded.updated_at
            """,
            (profile_id, item_path, item_title, max(0, quantity), int(equipped), (equipment_slot or "").strip() or None, charges_current, charges_max, (recharge or "").strip() or None, (notes or "").strip() or None, now),
        )
        row = connection.execute("SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?", (profile_id, item_path)).fetchone()
    result = dict(row) if row else {}
    result["equipped"] = bool(result.get("equipped"))
    return result


def list_inventory(database_path: Path, profile_id: str) -> list[dict[str, Any]]:
    init_player_inventory(database_path)
    with closing(_connect(database_path)) as connection, connection:
        rows = connection.execute("SELECT * FROM player_inventory WHERE profile_id=? AND quantity>0 ORDER BY equipped DESC,item_title", (profile_id,)).fetchall()
    result = [dict(row) for row in rows]
    for item in result:
        item["equipped"] = bool(item["equipped"])
    return result


def recharge_inventory(database_path: Path, recharge: str, profile_id: str | None = None) -> int:
    init_player_inventory(database_path)
    if recharge not in {"inn_rest", "scene", "dawn"}:
        raise ValueError("Tipo de recarga inválido")
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(database_path)) as connection, connection:
        if profile_id:
            cursor = connection.execute("UPDATE player_inventory SET charges_current=charges_max,updated_at=? WHERE profile_id=? AND recharge=? AND charges_max IS NOT NULL", (now, profile_id, recharge))
        else:
            cursor = connection.execute("UPDATE player_inventory SET charges_current=charges_max,updated_at=? WHERE recharge=? AND charges_max IS NOT NULL", (now, recharge))
    return int(cursor.rowcount)
