from __future__ import annotations

import sqlite3


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone() is not None


def active_game_session_id(
    connection: sqlite3.Connection,
    campaign_id: str = "omnisvera",
) -> int | None:
    """Return the one active operational session without inventing context."""
    if not table_exists(connection, "game_sessions"):
        return None
    rows = connection.execute(
        "SELECT id FROM game_sessions WHERE campaign_id=? AND status='active' ORDER BY id",
        (campaign_id,),
    ).fetchall()
    if len(rows) > 1:
        raise RuntimeError("Existem múltiplas sessões ativas para a campanha")
    return int(rows[0][0]) if rows else None
