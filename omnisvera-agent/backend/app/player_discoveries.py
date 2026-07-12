from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_player_discoveries(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_discoveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                note_path TEXT NOT NULL,
                note_title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(profile_id, note_path)
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_player_discoveries_profile ON player_discoveries(profile_id, created_at DESC)"
        )


def _as_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def reveal_discovery(
    database_path: Path, *, profile_id: str, note_path: str, note_title: str
) -> dict[str, Any]:
    init_player_discoveries(database_path)
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            INSERT INTO player_discoveries(profile_id, note_path, note_title, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(profile_id, note_path) DO UPDATE SET note_title = excluded.note_title
            """,
            (profile_id, note_path, note_title, now),
        )
        row = connection.execute(
            "SELECT * FROM player_discoveries WHERE profile_id = ? AND note_path = ?",
            (profile_id, note_path),
        ).fetchone()
    if row is None:
        raise RuntimeError("A descoberta não pôde ser recuperada")
    return _as_dict(row)


def list_discoveries(database_path: Path, *, profile_id: str | None = None) -> list[dict[str, Any]]:
    init_player_discoveries(database_path)
    with closing(_connect(database_path)) as connection, connection:
        if profile_id:
            rows = connection.execute(
                "SELECT * FROM player_discoveries WHERE profile_id = ? ORDER BY created_at DESC, id DESC",
                (profile_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM player_discoveries ORDER BY created_at DESC, id DESC"
            ).fetchall()
    return [_as_dict(row) for row in rows]


def revoke_discovery(database_path: Path, discovery_id: int) -> bool:
    init_player_discoveries(database_path)
    with closing(_connect(database_path)) as connection, connection:
        cursor = connection.execute("DELETE FROM player_discoveries WHERE id = ?", (discovery_id,))
    return cursor.rowcount > 0
