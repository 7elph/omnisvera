from __future__ import annotations

import sqlite3
import json
import uuid
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


FOG_COLUMNS = 32
FOG_ROWS = 24
FOG_LAYERS = ("exploration", "battle")


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_session_workspace(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS session_workspace_state (
              id INTEGER PRIMARY KEY CHECK (id = 1),
              map_id TEXT NOT NULL DEFAULT 'default',
              map_title TEXT NOT NULL,
              map_image_path TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_workspace_maps (
              id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              image_path TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_workspace_messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              actor_id TEXT NOT NULL,
              actor_name TEXT NOT NULL,
              actor_role TEXT NOT NULL,
              character_id TEXT,
              message_kind TEXT NOT NULL DEFAULT 'message',
              text TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_workspace_messages_created
              ON session_workspace_messages(created_at, id);
            CREATE TABLE IF NOT EXISTS session_workspace_presence (
              actor_id TEXT PRIMARY KEY,
              actor_name TEXT NOT NULL,
              actor_role TEXT NOT NULL,
              character_id TEXT,
              last_seen_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_workspace_tokens (
              id TEXT PRIMARY KEY,
              token_type TEXT NOT NULL CHECK (token_type IN ('character','monster')),
              map_id TEXT NOT NULL DEFAULT 'default',
              character_id TEXT,
              name TEXT NOT NULL,
              image_path TEXT,
              color TEXT NOT NULL DEFAULT '#d6a858',
              latitude REAL NOT NULL DEFAULT 50,
              longitude REAL NOT NULL DEFAULT 50,
              current_hp INTEGER,
              maximum_hp INTEGER,
              conditions_json TEXT NOT NULL DEFAULT '[]',
              sheet_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_workspace_tokens_character
              ON session_workspace_tokens(character_id);
            CREATE TABLE IF NOT EXISTS session_custom_items (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              item_type TEXT NOT NULL DEFAULT 'item',
              description TEXT,
              effects_json TEXT NOT NULL DEFAULT '[]',
              usable INTEGER NOT NULL DEFAULT 0,
              image_path TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_workspace_fog (
              layer TEXT PRIMARY KEY CHECK (layer IN ('exploration','battle')),
              enabled INTEGER NOT NULL DEFAULT 0,
              revealed_cells_json TEXT NOT NULL DEFAULT '[]',
              mist_density_json TEXT NOT NULL DEFAULT '{}',
              updated_at TEXT NOT NULL
            );
            """
        )
        for table, column, definition in (
            ("session_workspace_state", "map_id", "TEXT NOT NULL DEFAULT 'default'"),
            ("session_workspace_tokens", "map_id", "TEXT NOT NULL DEFAULT 'default'"),
            ("session_workspace_tokens", "sheet_json", "TEXT NOT NULL DEFAULT '{}'"),
            ("session_workspace_fog", "mist_density_json", "TEXT NOT NULL DEFAULT '{}'"),
        ):
            try:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            except sqlite3.OperationalError as error:
                if "duplicate column" not in str(error).lower():
                    raise
        now = _now()
        for layer in FOG_LAYERS:
            connection.execute(
                """INSERT INTO session_workspace_fog(layer,enabled,revealed_cells_json,mist_density_json,updated_at)
                   VALUES(?,?,?,?,?) ON CONFLICT(layer) DO NOTHING""",
                (layer, 0, "[]", "{}", now),
            )
        state = connection.execute("SELECT map_id,map_title,map_image_path,updated_at FROM session_workspace_state WHERE id=1").fetchone()
        if state:
            connection.execute(
                """INSERT INTO session_workspace_maps(id,title,image_path,created_at,updated_at)
                   VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,image_path=excluded.image_path,updated_at=excluded.updated_at""",
                (state["map_id"], state["map_title"], state["map_image_path"], state["updated_at"], state["updated_at"]),
            )


def _token_record(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["conditions"] = json.loads(item.pop("conditions_json") or "[]")
    item["sheet"] = json.loads(item.pop("sheet_json") or "{}")
    return item


def _item_record(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["effects"] = json.loads(item.pop("effects_json") or "[]")
    item["usable"] = bool(item["usable"])
    item["item_path"] = f"session-item:{item['id']}"
    return item


def list_workspace_tokens(database_path: Path, map_id: str | None = None) -> list[dict[str, Any]]:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT * FROM session_workspace_tokens WHERE map_id=? ORDER BY created_at,id", (map_id,)).fetchall() if map_id else connection.execute("SELECT * FROM session_workspace_tokens ORDER BY created_at,id").fetchall()
    return [_token_record(row) for row in rows]


def save_workspace_token(
    database_path: Path,
    *,
    token_type: str,
    name: str,
    latitude: float,
    longitude: float,
    character_id: str | None = None,
    image_path: str | None = None,
    color: str = "#d6a858",
    current_hp: int | None = None,
    maximum_hp: int | None = None,
    conditions: list[str] | None = None,
    sheet: dict[str, Any] | None = None,
    map_id: str = "default",
) -> dict[str, Any]:
    init_session_workspace(database_path)
    if token_type == "character" and character_id:
        token_id = f"character:{character_id}" if map_id == "default" else f"character:{map_id}:{character_id}"
    else:
        token_id = f"monster:{uuid.uuid4().hex}"
    now = _now()
    values = (
        token_id, token_type, map_id, character_id, name, image_path, color,
        max(0.0, min(100.0, float(latitude))), max(0.0, min(100.0, float(longitude))),
        current_hp, maximum_hp, json.dumps(conditions or [], ensure_ascii=False), json.dumps(sheet or {}, ensure_ascii=False), now, now,
    )
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            INSERT INTO session_workspace_tokens(
              id,token_type,map_id,character_id,name,image_path,color,latitude,longitude,
              current_hp,maximum_hp,conditions_json,sheet_json,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              map_id=excluded.map_id,
              name=excluded.name,image_path=excluded.image_path,color=excluded.color,
              current_hp=excluded.current_hp,maximum_hp=excluded.maximum_hp,
              conditions_json=excluded.conditions_json,sheet_json=excluded.sheet_json,updated_at=excluded.updated_at
            """,
            values,
        )
        row = connection.execute("SELECT * FROM session_workspace_tokens WHERE id=?", (token_id,)).fetchone()
    if row is None:
        raise RuntimeError("Marcador não pôde ser salvo")
    return _token_record(row)


def update_workspace_token_position(
    database_path: Path, *, token_id: str, latitude: float, longitude: float
) -> dict[str, Any] | None:
    init_session_workspace(database_path)
    latitude = max(0.0, min(100.0, float(latitude)))
    longitude = max(0.0, min(100.0, float(longitude)))
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            "UPDATE session_workspace_tokens SET latitude=?,longitude=?,updated_at=? WHERE id=?",
            (latitude, longitude, _now(), token_id),
        )
        row = connection.execute("SELECT * FROM session_workspace_tokens WHERE id=?", (token_id,)).fetchone()
    return _token_record(row) if row else None


def update_workspace_token(
    database_path: Path,
    *,
    token_id: str,
    name: str | None = None,
    image_path: str | None = None,
    color: str | None = None,
    current_hp: int | None = None,
    maximum_hp: int | None = None,
    conditions: list[str] | None = None,
    sheet: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    init_session_workspace(database_path)
    updates: dict[str, Any] = {"updated_at": _now()}
    if name is not None: updates["name"] = name.strip()
    if image_path is not None: updates["image_path"] = image_path.strip() or None
    if color is not None: updates["color"] = color
    if current_hp is not None: updates["current_hp"] = current_hp
    if maximum_hp is not None: updates["maximum_hp"] = maximum_hp
    if conditions is not None: updates["conditions_json"] = json.dumps(conditions, ensure_ascii=False)
    if sheet is not None: updates["sheet_json"] = json.dumps(sheet, ensure_ascii=False)
    assignments = ",".join(f"{key}=?" for key in updates)
    with closing(_connect(database_path)) as connection, connection:
        cursor = connection.execute(
            f"UPDATE session_workspace_tokens SET {assignments} WHERE id=?",
            (*updates.values(), token_id),
        )
        row = connection.execute("SELECT * FROM session_workspace_tokens WHERE id=?", (token_id,)).fetchone()
    return _token_record(row) if cursor.rowcount and row else None


def delete_workspace_token(database_path: Path, token_id: str) -> bool:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection, connection:
        cursor = connection.execute("DELETE FROM session_workspace_tokens WHERE id=?", (token_id,))
    return cursor.rowcount > 0


def list_session_items(database_path: Path) -> list[dict[str, Any]]:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT * FROM session_custom_items ORDER BY name COLLATE NOCASE,id").fetchall()
    return [_item_record(row) for row in rows]


def get_session_item(database_path: Path, item_id: int) -> dict[str, Any] | None:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection:
        row = connection.execute("SELECT * FROM session_custom_items WHERE id=?", (item_id,)).fetchone()
    return _item_record(row) if row else None


def get_session_item_by_path(database_path: Path, item_path: str) -> dict[str, Any] | None:
    if not item_path.startswith("session-item:"):
        return None
    try:
        item_id = int(item_path.split(":", 1)[1])
    except (TypeError, ValueError):
        return None
    return get_session_item(database_path, item_id)


def save_session_item(
    database_path: Path,
    *,
    name: str,
    item_type: str,
    description: str | None,
    effects: list[str],
    usable: bool,
    image_path: str | None = None,
    item_id: int | None = None,
) -> dict[str, Any]:
    init_session_workspace(database_path)
    now = _now()
    with closing(_connect(database_path)) as connection, connection:
        if item_id is None:
            cursor = connection.execute(
                """INSERT INTO session_custom_items(name,item_type,description,effects_json,usable,image_path,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (name, item_type, description, json.dumps(effects, ensure_ascii=False), int(usable), image_path, now, now),
            )
            item_id = int(cursor.lastrowid)
        else:
            connection.execute(
                """UPDATE session_custom_items SET name=?,item_type=?,description=?,effects_json=?,usable=?,image_path=?,updated_at=?
                   WHERE id=?""",
                (name, item_type, description, json.dumps(effects, ensure_ascii=False), int(usable), image_path, now, item_id),
            )
            try:
                connection.execute(
                    "UPDATE player_inventory SET item_title=?,updated_at=? WHERE item_path=?",
                    (name, now, f"session-item:{item_id}"),
                )
            except sqlite3.OperationalError:
                pass
        row = connection.execute("SELECT * FROM session_custom_items WHERE id=?", (item_id,)).fetchone()
    if row is None:
        raise ValueError("Item da sessão não encontrado")
    return _item_record(row)


def set_workspace_map(database_path: Path, *, title: str, image_path: str) -> dict[str, Any]:
    init_session_workspace(database_path)
    updated_at = _now()
    map_id = f"map:{uuid.uuid4().hex[:16]}"
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("INSERT INTO session_workspace_maps(id,title,image_path,created_at,updated_at) VALUES(?,?,?,?,?)", (map_id, title, image_path, updated_at, updated_at))
        connection.execute(
            """
            INSERT INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at)
            VALUES(1,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              map_id=excluded.map_id,
              map_title=excluded.map_title,
              map_image_path=excluded.map_image_path,
              updated_at=excluded.updated_at
            """,
            (map_id, title, image_path, updated_at),
        )
    return {"id": map_id, "title": title, "image_path": image_path, "updated_at": updated_at}


def list_workspace_maps(database_path: Path) -> list[dict[str, Any]]:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT id,title,image_path,created_at,updated_at FROM session_workspace_maps ORDER BY created_at,id").fetchall()
    return [dict(row) for row in rows]


def set_active_workspace_map(database_path: Path, map_id: str) -> dict[str, Any] | None:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT id,title,image_path,created_at,updated_at FROM session_workspace_maps WHERE id=?", (map_id,)).fetchone()
        if row is None:
            return None
        connection.execute("UPDATE session_workspace_state SET map_id=?,map_title=?,map_image_path=?,updated_at=? WHERE id=1", (row["id"], row["title"], row["image_path"], _now()))
    return dict(row)


def _cell_key(column: int, row: int) -> str:
    return f"{max(0, min(FOG_COLUMNS - 1, int(column)))}:{max(0, min(FOG_ROWS - 1, int(row)))}"


def _normalize_fog_cells(cells: list[str] | None) -> list[str]:
    normalized: set[str] = set()
    for value in cells or []:
        try:
            column_text, row_text = str(value).split(":", 1)
            column, row = int(column_text), int(row_text)
        except (TypeError, ValueError):
            continue
        if 0 <= column < FOG_COLUMNS and 0 <= row < FOG_ROWS:
            normalized.add(_cell_key(column, row))
    return sorted(normalized, key=lambda value: (int(value.split(":")[1]), int(value.split(":")[0])))


def _normalize_mist_density(density: dict[str, Any] | None) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for value, raw_amount in (density or {}).items():
        try:
            column_text, row_text = str(value).split(":", 1)
            column, row = int(column_text), int(row_text)
            amount = max(0.0, min(1.0, float(raw_amount)))
        except (TypeError, ValueError):
            continue
        if 0 <= column < FOG_COLUMNS and 0 <= row < FOG_ROWS and amount > 0:
            normalized[_cell_key(column, row)] = round(amount, 3)
    return normalized


def get_workspace_fog(database_path: Path) -> dict[str, dict[str, Any]]:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(
            "SELECT layer,enabled,revealed_cells_json,mist_density_json,updated_at FROM session_workspace_fog"
        ).fetchall()
    by_layer = {row["layer"]: row for row in rows}
    result: dict[str, dict[str, Any]] = {}
    for layer in FOG_LAYERS:
        row = by_layer.get(layer)
        try:
            cells = _normalize_fog_cells(json.loads(row["revealed_cells_json"] or "[]")) if row else []
        except (TypeError, ValueError, json.JSONDecodeError):
            cells = []
        try:
            mist_density = _normalize_mist_density(json.loads(row["mist_density_json"] or "{}")) if row else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            mist_density = {}
        result[layer] = {
            "enabled": bool(row["enabled"]) if row else False,
            "revealed_cells": cells,
            "mist_density": mist_density,
            "columns": FOG_COLUMNS,
            "rows": FOG_ROWS,
            "updated_at": row["updated_at"] if row else None,
        }
    return result


def update_workspace_fog(
    database_path: Path,
    *,
    layer: str,
    enabled: bool,
    revealed_cells: list[str] | None,
    mist_density: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if layer not in FOG_LAYERS:
        raise ValueError("Camada de fog inválida")
    init_session_workspace(database_path)
    cells = _normalize_fog_cells(revealed_cells)
    density = _normalize_mist_density(mist_density)
    updated_at = _now()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """INSERT INTO session_workspace_fog(layer,enabled,revealed_cells_json,mist_density_json,updated_at)
               VALUES(?,?,?,?,?) ON CONFLICT(layer) DO UPDATE SET
                 enabled=excluded.enabled,
                 revealed_cells_json=excluded.revealed_cells_json,
                 mist_density_json=excluded.mist_density_json,
                 updated_at=excluded.updated_at""",
            (layer, int(enabled), json.dumps(cells), json.dumps(density), updated_at),
        )
    return get_workspace_fog(database_path)[layer]


def _token_fog_cell(latitude: float, longitude: float) -> str:
    column = min(FOG_COLUMNS - 1, max(0, int(float(longitude) / 100 * FOG_COLUMNS)))
    row = min(FOG_ROWS - 1, max(0, int(float(latitude) / 100 * FOG_ROWS)))
    return _cell_key(column, row)


def _token_is_visible(token: dict[str, Any], fog: dict[str, dict[str, Any]]) -> bool:
    cell = _token_fog_cell(token["latitude"], token["longitude"])
    return all(not data["enabled"] or cell in data["revealed_cells"] for data in fog.values())


def record_workspace_message(
    database_path: Path,
    *,
    actor_id: str,
    actor_name: str,
    actor_role: str,
    character_id: str | None,
    text: str,
    message_kind: str = "message",
) -> dict[str, Any]:
    init_session_workspace(database_path)
    created_at = _now()
    with closing(_connect(database_path)) as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO session_workspace_messages(
              actor_id,actor_name,actor_role,character_id,message_kind,text,created_at
            ) VALUES(?,?,?,?,?,?,?)
            """,
            (actor_id, actor_name, actor_role, character_id, message_kind, text, created_at),
        )
        message_id = int(cursor.lastrowid)
    return {
        "id": message_id,
        "actor_id": actor_id,
        "actor_name": actor_name,
        "actor_role": actor_role,
        "character_id": character_id,
        "message_kind": message_kind,
        "text": text,
        "created_at": created_at,
    }


def heartbeat_workspace(
    database_path: Path,
    *,
    actor_id: str,
    actor_name: str,
    actor_role: str,
    character_id: str | None,
) -> dict[str, Any]:
    init_session_workspace(database_path)
    last_seen_at = _now()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            INSERT INTO session_workspace_presence(actor_id,actor_name,actor_role,character_id,last_seen_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(actor_id) DO UPDATE SET
              actor_name=excluded.actor_name,
              actor_role=excluded.actor_role,
              character_id=excluded.character_id,
              last_seen_at=excluded.last_seen_at
            """,
            (actor_id, actor_name, actor_role, character_id, last_seen_at),
        )
    return {
        "actor_id": actor_id,
        "actor_name": actor_name,
        "actor_role": actor_role,
        "character_id": character_id,
        "last_seen_at": last_seen_at,
        "online": True,
    }


def get_workspace_snapshot(
    database_path: Path, *, message_limit: int = 200, is_gm: bool = False
) -> dict[str, Any]:
    init_session_workspace(database_path)
    threshold = datetime.now(timezone.utc) - timedelta(seconds=70)
    with closing(_connect(database_path)) as connection:
        state_row = connection.execute(
            "SELECT map_id,map_title,map_image_path,updated_at FROM session_workspace_state WHERE id=1"
        ).fetchone()
        message_rows = connection.execute(
            """
            SELECT * FROM (
              SELECT id,actor_id,actor_name,actor_role,character_id,message_kind,text,created_at
              FROM session_workspace_messages ORDER BY id DESC LIMIT ?
            ) ORDER BY id ASC
            """,
            (max(1, min(int(message_limit), 500)),),
        ).fetchall()
        presence_rows = connection.execute(
            "SELECT actor_id,actor_name,actor_role,character_id,last_seen_at FROM session_workspace_presence"
        ).fetchall()
    presence = []
    for row in presence_rows:
        item = dict(row)
        try:
            seen = datetime.fromisoformat(str(item["last_seen_at"]).replace("Z", "+00:00"))
        except ValueError:
            seen = datetime.min.replace(tzinfo=timezone.utc)
        item["online"] = seen >= threshold
        presence.append(item)
    map_record = None
    if state_row:
        map_record = {
            "id": state_row["map_id"],
            "title": state_row["map_title"],
            "image_path": state_row["map_image_path"],
            "updated_at": state_row["updated_at"],
        }
    fog = get_workspace_fog(database_path)
    tokens = list_workspace_tokens(database_path, state_row["map_id"] if state_row else "default")
    if not is_gm:
        tokens = [token for token in tokens if _token_is_visible(token, fog)]
    return {
        "map": map_record,
        "messages": [dict(row) for row in message_rows],
        "presence": presence,
        "tokens": tokens,
        "fog": fog,
    }
