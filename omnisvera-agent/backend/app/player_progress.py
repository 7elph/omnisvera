from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


QUEST_STATUSES = {"available", "accepted", "in_progress", "completed", "failed", "archived"}


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_player_progress(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                note_path TEXT,
                created_at TEXT NOT NULL,
                read_at TEXT
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_player_events_profile ON player_events(profile_id, created_at DESC)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_event_reads (
                event_id INTEGER NOT NULL,
                profile_id TEXT NOT NULL,
                read_at TEXT NOT NULL,
                UNIQUE(event_id, profile_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                note_path TEXT NOT NULL,
                note_title TEXT NOT NULL,
                status TEXT NOT NULL,
                progress TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE(profile_id, note_path)
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_player_quests_profile ON player_quests(profile_id, updated_at DESC)"
        )


def _dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def add_event(
    database_path: Path,
    *,
    profile_id: str,
    kind: str,
    title: str,
    message: str,
    note_path: str | None = None,
    unread: bool = True,
) -> dict[str, Any]:
    init_player_progress(database_path)
    now = datetime.now(timezone.utc).isoformat()
    read_at = None if unread else now
    with closing(_connect(database_path)) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO player_events(profile_id, kind, title, message, note_path, created_at, read_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (profile_id, kind, title, message, note_path, now, read_at),
        )
        row = connection.execute("SELECT * FROM player_events WHERE id = ?", (cursor.lastrowid,)).fetchone()
    if row is None:
        raise RuntimeError("O evento não pôde ser recuperado")
    return _dict(row)


def list_events(database_path: Path, *, profile_id: str | None, limit: int = 80) -> list[dict[str, Any]]:
    init_player_progress(database_path)
    profile_key = profile_id or "group"
    profiles = ["group"] if not profile_id else [profile_key, "group"]
    marks = ",".join("?" for _ in profiles)
    with closing(_connect(database_path)) as connection, connection:
        rows = connection.execute(
            f"""
            SELECT e.id, e.profile_id, e.kind, e.title, e.message, e.note_path, e.created_at,
              CASE WHEN e.profile_id = 'group' AND ? <> 'group' THEN r.read_at ELSE e.read_at END AS read_at
            FROM player_events e
            LEFT JOIN player_event_reads r ON r.event_id = e.id AND r.profile_id = ?
            WHERE e.profile_id IN ({marks})
            ORDER BY e.created_at DESC, e.id DESC LIMIT ?
            """,
            (profile_key, profile_key, *profiles, max(1, min(limit, 250))),
        ).fetchall()
    return [_dict(row) for row in rows]


def mark_events_read(database_path: Path, *, profile_id: str | None, event_ids: list[int]) -> int:
    if not event_ids:
        return 0
    init_player_progress(database_path)
    profile_key = profile_id or "group"
    profiles = ["group"] if not profile_id else [profile_key, "group"]
    id_marks = ",".join("?" for _ in event_ids)
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(database_path)) as connection, connection:
        own_cursor = connection.execute(
            f"UPDATE player_events SET read_at = ? WHERE id IN ({id_marks}) AND profile_id = ?",
            (now, *event_ids, profile_key),
        )
        group_ids = connection.execute(
            f"SELECT id FROM player_events WHERE id IN ({id_marks}) AND profile_id = 'group'",
            event_ids,
        ).fetchall()
        if profile_key != "group":
            connection.executemany(
                "INSERT INTO player_event_reads(event_id, profile_id, read_at) VALUES (?, ?, ?) ON CONFLICT(event_id, profile_id) DO UPDATE SET read_at = excluded.read_at",
                [(row["id"], profile_key, now) for row in group_ids],
            )
    return own_cursor.rowcount + len(group_ids)


def upsert_quest(
    database_path: Path,
    *,
    profile_id: str,
    note_path: str,
    note_title: str,
    status: str,
    progress: str | None,
) -> dict[str, Any]:
    if status not in QUEST_STATUSES:
        raise ValueError("Estado de missão inválido")
    init_player_progress(database_path)
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            INSERT INTO player_quests(profile_id, note_path, note_title, status, progress, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_id, note_path) DO UPDATE SET
              note_title = excluded.note_title,
              status = excluded.status,
              progress = excluded.progress,
              updated_at = excluded.updated_at
            """,
            (profile_id, note_path, note_title, status, (progress or "").strip() or None, now),
        )
        row = connection.execute(
            "SELECT * FROM player_quests WHERE profile_id = ? AND note_path = ?",
            (profile_id, note_path),
        ).fetchone()
    if row is None:
        raise RuntimeError("A missão não pôde ser recuperada")
    return _dict(row)


def list_quests(database_path: Path, *, profile_id: str | None = None) -> list[dict[str, Any]]:
    init_player_progress(database_path)
    profiles = ["group"] if not profile_id else [profile_id, "group"]
    marks = ",".join("?" for _ in profiles)
    with closing(_connect(database_path)) as connection, connection:
        rows = connection.execute(
            f"SELECT * FROM player_quests WHERE profile_id IN ({marks}) ORDER BY updated_at DESC, id DESC",
            profiles,
        ).fetchall()
    return [_dict(row) for row in rows]
