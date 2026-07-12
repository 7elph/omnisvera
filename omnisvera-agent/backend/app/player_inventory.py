from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
              notes TEXT,
              updated_at TEXT NOT NULL,
              UNIQUE(profile_id, item_path)
            )
            """
        )


def upsert_inventory(database_path: Path, *, profile_id: str, item_path: str, item_title: str, quantity: int, equipped: bool, notes: str | None) -> dict[str, Any]:
    init_player_inventory(database_path)
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,notes,updated_at)
            VALUES(?,?,?,?,?,?,?) ON CONFLICT(profile_id,item_path) DO UPDATE SET
              item_title=excluded.item_title, quantity=excluded.quantity, equipped=excluded.equipped,
              notes=excluded.notes, updated_at=excluded.updated_at
            """,
            (profile_id, item_path, item_title, max(0, quantity), int(equipped), (notes or "").strip() or None, now),
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
