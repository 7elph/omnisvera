from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACTION_TYPES = {"investigate", "talk", "mission", "rumor", "destination", "theory"}
ACTION_STATUSES = {"submitted", "in_review", "answered", "canonized", "rejected"}


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_player_actions(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_path TEXT NOT NULL,
                character_title TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_path TEXT NOT NULL,
                target_title TEXT NOT NULL,
                intent TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'submitted',
                gm_response TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_player_actions_status ON player_actions(status, updated_at DESC)"
        )


def _as_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def create_player_action(
    database_path: Path,
    *,
    character_path: str,
    character_title: str,
    action_type: str,
    target_path: str,
    target_title: str,
    intent: str,
) -> dict[str, Any]:
    if action_type not in ACTION_TYPES:
        raise ValueError("Tipo de ação inválido")
    now = datetime.now(timezone.utc).isoformat()
    init_player_actions(database_path)
    with closing(_connect(database_path)) as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO player_actions (
                character_path, character_title, action_type,
                target_path, target_title, intent,
                status, gm_response, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'submitted', NULL, ?, ?)
            """,
            (character_path, character_title, action_type, target_path, target_title, intent, now, now),
        )
        row = connection.execute("SELECT * FROM player_actions WHERE id = ?", (cursor.lastrowid,)).fetchone()
    if row is None:
        raise RuntimeError("A ação não pôde ser recuperada")
    return _as_dict(row)


def list_player_actions(
    database_path: Path, *, limit: int = 100, character_path: str | None = None
) -> list[dict[str, Any]]:
    init_player_actions(database_path)
    with closing(_connect(database_path)) as connection, connection:
        if character_path:
            rows = connection.execute(
                "SELECT * FROM player_actions WHERE character_path = ? ORDER BY updated_at DESC, id DESC LIMIT ?",
                (character_path, max(1, min(limit, 500))),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM player_actions ORDER BY updated_at DESC, id DESC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
    return [_as_dict(row) for row in rows]


def update_player_action(
    database_path: Path,
    action_id: int,
    *,
    status: str,
    gm_response: str | None,
) -> dict[str, Any] | None:
    if status not in ACTION_STATUSES:
        raise ValueError("Estado de ação inválido")
    response = (gm_response or "").strip() or None
    now = datetime.now(timezone.utc).isoformat()
    init_player_actions(database_path)
    with closing(_connect(database_path)) as connection, connection:
        existing = connection.execute("SELECT id FROM player_actions WHERE id = ?", (action_id,)).fetchone()
        if existing is None:
            return None
        connection.execute(
            "UPDATE player_actions SET status = ?, gm_response = ?, updated_at = ? WHERE id = ?",
            (status, response, now, action_id),
        )
        row = connection.execute("SELECT * FROM player_actions WHERE id = ?", (action_id,)).fetchone()
    return _as_dict(row) if row is not None else None
