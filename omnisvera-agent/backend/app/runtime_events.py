from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNTIME_EVENT_TYPES = {
    "session_connected",
    "tour_started",
    "tour_stopped",
    "tour_completed",
    "tour_blocked",
    "automatic_tour_changed",
    "world_incident",
    "weekly_report",
    "navigation_view",
    "reconnected",
    "notification_opened",
}


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_runtime_events(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                profile_id TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                actor_role TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_runtime_events_profile ON runtime_events(profile_id, id DESC)"
        )


def _record(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))
    return result


def record_runtime_event(
    database_path: Path,
    *,
    event_id: str,
    profile_id: str,
    actor_id: str,
    actor_role: str,
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if event_type not in RUNTIME_EVENT_TYPES:
        raise ValueError("Tipo de evento de runtime invÃ¡lido")
    init_runtime_events(database_path)
    now = datetime.now(timezone.utc).isoformat()
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO runtime_events(
                event_id,profile_id,actor_id,actor_role,event_type,payload_json,created_at
            ) VALUES(?,?,?,?,?,?,?)
            """,
            (event_id, profile_id, actor_id, actor_role, event_type, payload_json, now),
        )
        row = connection.execute(
            "SELECT * FROM runtime_events WHERE event_id=?", (event_id,)
        ).fetchone()
    if row is None:
        raise RuntimeError("O evento de runtime nÃ£o pÃ´de ser recuperado")
    return _record(row)


def list_runtime_events(database_path: Path, *, profile_id: str | None, limit: int = 100) -> list[dict[str, Any]]:
    init_runtime_events(database_path)
    with closing(_connect(database_path)) as connection:
        if profile_id:
            rows = connection.execute(
                "SELECT * FROM runtime_events WHERE profile_id=? ORDER BY id DESC LIMIT ?",
                (profile_id, max(1, min(limit, 500))),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM runtime_events ORDER BY id DESC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
    return [_record(row) for row in rows]
