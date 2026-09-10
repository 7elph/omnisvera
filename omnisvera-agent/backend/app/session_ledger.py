from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from .access import AccessContext
from .session_context import active_game_session_id, table_exists


PUBLIC_CHARACTER_EVENTS = {
    "damage", "heal", "set_hp", "add_condition", "remove_condition",
    "consume_resource", "equip_item", "unequip_item", "change_quantity",
    "rest_at_inn", "grant_item", "remove_item",
}


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def init_session_ledger(database_path: Path) -> None:
    public_types = ",".join(f"'{item}'" for item in sorted(PUBLIC_CHARACTER_EVENTS))
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS session_ledger (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source_type TEXT NOT NULL,
              source_id TEXT NOT NULL,
              event_kind TEXT NOT NULL,
              actor_id TEXT NOT NULL,
              actor_name TEXT NOT NULL,
              actor_role TEXT NOT NULL,
              character_id TEXT,
              title TEXT NOT NULL,
              detail_json TEXT,
              visibility TEXT NOT NULL DEFAULT 'table',
              created_at TEXT NOT NULL,
              voided_at TEXT,
              UNIQUE(source_type, source_id)
            )
            """
        )
        ledger_columns = {row[1] for row in connection.execute("PRAGMA table_info(session_ledger)")}
        if "game_session_id" not in ledger_columns:
            connection.execute(
                "ALTER TABLE session_ledger ADD COLUMN game_session_id INTEGER"
                + (" REFERENCES game_sessions(id)" if table_exists(connection, "game_sessions") else "")
            )
        connection.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS session_ledger (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              game_session_id INTEGER REFERENCES game_sessions(id),
              source_type TEXT NOT NULL,
              source_id TEXT NOT NULL,
              event_kind TEXT NOT NULL,
              actor_id TEXT NOT NULL,
              actor_name TEXT NOT NULL,
              actor_role TEXT NOT NULL,
              character_id TEXT,
              title TEXT NOT NULL,
              detail_json TEXT,
              visibility TEXT NOT NULL DEFAULT 'table',
              created_at TEXT NOT NULL,
              voided_at TEXT,
              UNIQUE(source_type, source_id)
            );
            CREATE INDEX IF NOT EXISTS idx_session_ledger_created
              ON session_ledger(id DESC, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_session_ledger_visibility
              ON session_ledger(visibility, character_id, id DESC);

            DROP TRIGGER IF EXISTS trg_ledger_workspace_message;
            DROP TRIGGER IF EXISTS trg_ledger_character_event;
            DROP TRIGGER IF EXISTS trg_ledger_character_event_revert;
            DROP TRIGGER IF EXISTS trg_ledger_dice_roll;
            DROP TRIGGER IF EXISTS trg_ledger_dice_roll_void;

            INSERT OR IGNORE INTO session_ledger(
              game_session_id,source_type,source_id,event_kind,actor_id,actor_name,actor_role,
              character_id,title,detail_json,visibility,created_at
            )
            SELECT game_session_id,'workspace_message',CAST(id AS TEXT),message_kind,actor_id,actor_name,
              actor_role,character_id,text,NULL,'table',created_at
            FROM session_workspace_messages;

            INSERT OR IGNORE INTO session_ledger(
              game_session_id,source_type,source_id,event_kind,actor_id,actor_name,actor_role,
              character_id,title,detail_json,visibility,created_at,voided_at
            )
            SELECT game_session_id,'character_event',CAST(id AS TEXT),'state',actor_id,character_id,
              actor_role,character_id,COALESCE(NULLIF(reason,''),REPLACE(event_type,'_',' ')),
              json_object('event_type',event_type,'field',field,'before',before_json,'after',after_json),
              CASE WHEN event_type IN ({public_types}) THEN 'table' ELSE 'gm' END,
              created_at,reverted_at
            FROM character_events;

            INSERT OR IGNORE INTO session_ledger(
              game_session_id,source_type,source_id,event_kind,actor_id,actor_name,actor_role,
              character_id,title,detail_json,visibility,created_at,voided_at
            )
            SELECT game_session_id,'dice_roll',CAST(id AS TEXT),'roll',actor_id,actor_id,actor_role,
              character_id,label,
              json_object('formula',formula,'dice',dice,'modifier',modifier,
                'results',individual_results_json,'subtotal',subtotal,'total',total,
                'target_value',target_value,'target_hidden',target_hidden,'outcome',outcome),
              visibility,created_at,voided_at
            FROM dice_roll_events;

            CREATE TRIGGER IF NOT EXISTS trg_ledger_workspace_message
            AFTER INSERT ON session_workspace_messages BEGIN
              INSERT OR IGNORE INTO session_ledger(
                game_session_id,source_type,source_id,event_kind,actor_id,actor_name,actor_role,
                character_id,title,detail_json,visibility,created_at
              ) VALUES(
                NEW.game_session_id,'workspace_message',CAST(NEW.id AS TEXT),NEW.message_kind,NEW.actor_id,
                NEW.actor_name,NEW.actor_role,NEW.character_id,NEW.text,NULL,'table',NEW.created_at
              );
            END;

            CREATE TRIGGER IF NOT EXISTS trg_ledger_character_event
            AFTER INSERT ON character_events BEGIN
              INSERT OR IGNORE INTO session_ledger(
                game_session_id,source_type,source_id,event_kind,actor_id,actor_name,actor_role,
                character_id,title,detail_json,visibility,created_at,voided_at
              ) VALUES(
                NEW.game_session_id,'character_event',CAST(NEW.id AS TEXT),'state',NEW.actor_id,NEW.character_id,
                NEW.actor_role,NEW.character_id,COALESCE(NULLIF(NEW.reason,''),REPLACE(NEW.event_type,'_',' ')),
                json_object('event_type',NEW.event_type,'field',NEW.field,'before',NEW.before_json,'after',NEW.after_json),
                CASE WHEN NEW.event_type IN ({public_types}) THEN 'table' ELSE 'gm' END,
                NEW.created_at,NEW.reverted_at
              );
            END;

            CREATE TRIGGER IF NOT EXISTS trg_ledger_character_event_revert
            AFTER UPDATE OF reverted_at ON character_events BEGIN
              UPDATE session_ledger SET voided_at=NEW.reverted_at
              WHERE source_type='character_event' AND source_id=CAST(NEW.id AS TEXT);
            END;

            CREATE TRIGGER IF NOT EXISTS trg_ledger_dice_roll
            AFTER INSERT ON dice_roll_events BEGIN
              INSERT OR IGNORE INTO session_ledger(
                game_session_id,source_type,source_id,event_kind,actor_id,actor_name,actor_role,
                character_id,title,detail_json,visibility,created_at,voided_at
              ) VALUES(
                NEW.game_session_id,'dice_roll',CAST(NEW.id AS TEXT),'roll',NEW.actor_id,NEW.actor_id,NEW.actor_role,
                NEW.character_id,NEW.label,
                json_object('formula',NEW.formula,'dice',NEW.dice,'modifier',NEW.modifier,
                  'results',NEW.individual_results_json,'subtotal',NEW.subtotal,'total',NEW.total,
                  'target_value',NEW.target_value,'target_hidden',NEW.target_hidden,'outcome',NEW.outcome),
                NEW.visibility,NEW.created_at,NEW.voided_at
              );
            END;

            CREATE TRIGGER IF NOT EXISTS trg_ledger_dice_roll_void
            AFTER UPDATE OF voided_at ON dice_roll_events BEGIN
              UPDATE session_ledger SET voided_at=NEW.voided_at
              WHERE source_type='dice_roll' AND source_id=CAST(NEW.id AS TEXT);
            END;
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_ledger_game_session ON session_ledger(game_session_id,id DESC)"
        )


def append_session_ledger_event(
    connection: sqlite3.Connection,
    *,
    source_type: str,
    source_id: str,
    event_kind: str,
    actor_id: str,
    actor_name: str,
    actor_role: str,
    character_id: str | None,
    title: str,
    detail: dict[str, Any] | None,
    visibility: str = "table",
    created_at: str,
    game_session_id: int | None = None,
) -> int:
    """Append one ledger entry using the caller's transaction."""
    if game_session_id is None:
        game_session_id = active_game_session_id(connection)
    cursor = connection.execute(
        """
        INSERT INTO session_ledger(
          game_session_id,source_type,source_id,event_kind,actor_id,actor_name,actor_role,
          character_id,title,detail_json,visibility,created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            game_session_id,
            source_type,
            source_id,
            event_kind,
            actor_id,
            actor_name,
            actor_role,
            character_id,
            title,
            json.dumps(detail, ensure_ascii=False) if detail is not None else None,
            visibility,
            created_at,
        ),
    )
    return int(cursor.lastrowid)


def _decode_detail(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        detail = json.loads(raw)
    except json.JSONDecodeError:
        return {"text": raw}
    if not isinstance(detail, dict):
        return {"value": detail}
    for key in ("before", "after", "results"):
        value = detail.get(key)
        if isinstance(value, str):
            try:
                detail[key] = json.loads(value)
            except json.JSONDecodeError:
                pass
    return detail


def list_session_ledger(database_path: Path, access: AccessContext, *, limit: int = 500) -> list[dict[str, Any]]:
    init_session_ledger(database_path)
    clauses = ["voided_at IS NULL"]
    params: list[Any] = []
    if access.mode != "gm":
        clauses.append("(visibility IN ('table','public') OR (visibility='owner' AND character_id=?) OR (visibility='private' AND actor_id=?))")
        params.extend([access.profile_id or "", access.profile_id or ""])
    params.append(max(1, min(int(limit), 1000)))
    query = f"""
      SELECT * FROM (
        SELECT * FROM session_ledger WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT ?
      ) ORDER BY id ASC
    """
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(query, params).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["detail"] = _decode_detail(item.pop("detail_json"))
        if access.mode != "gm" and item["event_kind"] == "roll" and item.get("detail", {}).get("target_hidden"):
            item["detail"].pop("target_value", None)
        result.append(item)
    return result


def session_ledger_version(database_path: Path) -> int:
    with closing(_connect(database_path)) as connection:
        row = connection.execute("SELECT COALESCE(MAX(id),0) AS version FROM session_ledger").fetchone()
    return int(row["version"] if row else 0)
