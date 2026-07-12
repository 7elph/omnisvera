from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_player_ideas(path: Path) -> None:
    with closing(_connect(path)) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS player_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                title TEXT NOT NULL,
                concept TEXT NOT NULL,
                appearance TEXT,
                motivation TEXT,
                world_connection TEXT,
                status TEXT NOT NULL DEFAULT 'submitted',
                gm_feedback TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def create_idea(path: Path, *, author: str, title: str, concept: str, appearance: str | None, motivation: str | None, world_connection: str | None) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    init_player_ideas(path)
    with closing(_connect(path)) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO player_ideas(author,title,concept,appearance,motivation,world_connection,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (author, title.strip(), concept.strip(), appearance, motivation, world_connection, now, now),
        )
        row = connection.execute("SELECT * FROM player_ideas WHERE id=?", (cursor.lastrowid,)).fetchone()
    return dict(row) if row else {}


def list_ideas(path: Path) -> list[dict[str, Any]]:
    init_player_ideas(path)
    with closing(_connect(path)) as connection:
        rows = connection.execute("SELECT * FROM player_ideas ORDER BY updated_at DESC,id DESC").fetchall()
    return [dict(row) for row in rows]


def review_idea(path: Path, idea_id: int, *, status: str, feedback: str | None) -> dict[str, Any] | None:
    if status not in {"submitted", "reviewing", "approved", "archived"}:
        raise ValueError("Estado inválido")
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(path)) as connection, connection:
        connection.execute("UPDATE player_ideas SET status=?,gm_feedback=?,updated_at=? WHERE id=?", (status, feedback, now, idea_id))
        row = connection.execute("SELECT * FROM player_ideas WHERE id=?", (idea_id,)).fetchone()
    return dict(row) if row else None
