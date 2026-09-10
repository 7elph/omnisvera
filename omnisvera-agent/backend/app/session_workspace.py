from __future__ import annotations

import sqlite3
import json
import uuid
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .session_context import active_game_session_id, table_exists


FOG_COLUMNS = 32
FOG_ROWS = 24
FOG_LAYERS = ("exploration", "battle")
PRESENCE_TIMEOUT_SECONDS = 70
OFFICIAL_WORKSPACE_MAPS = (
    ("official:nimalis", "Nimalis", "zz_media/maps/mapa_de_nimalis.png"),
    ("official:nimalia", "Nimalia", "zz_media/maps/mapa_de_nimalia.png"),
    ("official:earthropo", "Earthropo", "zz_media/maps/earthropo.png"),
)


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_session_workspace(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        map_fog_existed = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='session_workspace_map_fog'"
        ).fetchone() is not None
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS session_workspace_state (
              id INTEGER PRIMARY KEY CHECK (id = 1),
              map_id TEXT NOT NULL DEFAULT 'default',
              map_title TEXT NOT NULL,
              map_image_path TEXT NOT NULL,
              table_mode TEXT NOT NULL DEFAULT 'digital' CHECK (table_mode IN ('digital','physical','test')),
              view_zoom REAL NOT NULL DEFAULT 1,
              view_scroll_left REAL NOT NULL DEFAULT 0,
              view_scroll_top REAL NOT NULL DEFAULT 0,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_workspace_maps (
              id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              image_path TEXT NOT NULL,
              visible_to_players INTEGER NOT NULL DEFAULT 0,
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
              token_type TEXT NOT NULL CHECK (token_type IN ('character','monster','location')),
              map_id TEXT NOT NULL DEFAULT 'default',
              character_id TEXT,
              name TEXT NOT NULL,
              image_path TEXT,
              visible_to_players INTEGER NOT NULL DEFAULT 1,
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
              effect_rules_json TEXT NOT NULL DEFAULT '[]',
              mechanics_json TEXT NOT NULL DEFAULT '{}',
              usable INTEGER NOT NULL DEFAULT 0,
              image_path TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_workspace_icons (
              id TEXT PRIMARY KEY,
              label TEXT NOT NULL,
              category TEXT NOT NULL CHECK (category IN ('map','items')),
              path TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_workspace_fog (
              layer TEXT PRIMARY KEY CHECK (layer IN ('exploration','battle')),
              enabled INTEGER NOT NULL DEFAULT 0,
              revealed_cells_json TEXT NOT NULL DEFAULT '[]',
              mist_density_json TEXT NOT NULL DEFAULT '{}',
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_workspace_map_fog (
              map_id TEXT NOT NULL,
              layer TEXT NOT NULL CHECK (layer IN ('exploration','battle')),
              enabled INTEGER NOT NULL DEFAULT 0,
              revealed_cells_json TEXT NOT NULL DEFAULT '[]',
              mist_density_json TEXT NOT NULL DEFAULT '{}',
              updated_at TEXT NOT NULL,
              PRIMARY KEY(map_id, layer)
            );
            """
        )
        # SQLite cannot alter a CHECK constraint. Preserve rows/indexes/triggers atomically.
        token_sql = connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='session_workspace_tokens'").fetchone()[0]
        if "'location'" not in token_sql:
            connection.execute("BEGIN IMMEDIATE")
            objects = connection.execute("SELECT sql FROM sqlite_master WHERE tbl_name='session_workspace_tokens' AND type IN ('index','trigger') AND sql IS NOT NULL").fetchall()
            next_sql = token_sql.replace("session_workspace_tokens", "session_workspace_tokens_next", 1).replace("'character','monster'", "'character','monster','location'")
            if next_sql == token_sql or "'location'" not in next_sql:
                raise ValueError("Esquema de pins desconhecido; migração interrompida")
            connection.execute(next_sql)
            connection.execute("INSERT INTO session_workspace_tokens_next SELECT * FROM session_workspace_tokens")
            connection.execute("DROP TABLE session_workspace_tokens")
            connection.execute("ALTER TABLE session_workspace_tokens_next RENAME TO session_workspace_tokens")
            for obj in objects:
                connection.execute(obj[0])
        for table, column, definition in (
            ("session_workspace_state", "map_id", "TEXT NOT NULL DEFAULT 'default'"),
            ("session_workspace_state", "table_mode", "TEXT NOT NULL DEFAULT 'digital'"),
            ("session_workspace_state", "view_zoom", "REAL NOT NULL DEFAULT 1"),
            ("session_workspace_state", "view_scroll_left", "REAL NOT NULL DEFAULT 0"),
            ("session_workspace_state", "view_scroll_top", "REAL NOT NULL DEFAULT 0"),
            ("session_workspace_tokens", "map_id", "TEXT NOT NULL DEFAULT 'default'"),
            ("session_workspace_tokens", "sheet_json", "TEXT NOT NULL DEFAULT '{}'"),
            ("session_workspace_tokens", "visible_to_players", "INTEGER NOT NULL DEFAULT 1"),
            ("session_workspace_maps", "visible_to_players", "INTEGER NOT NULL DEFAULT 1"),
            ("session_custom_items", "effect_rules_json", "TEXT NOT NULL DEFAULT '[]'"),
            ("session_custom_items", "mechanics_json", "TEXT NOT NULL DEFAULT '{}'"),
            ("session_workspace_fog", "mist_density_json", "TEXT NOT NULL DEFAULT '{}'"),
            (
                "session_workspace_messages",
                "game_session_id",
                "INTEGER REFERENCES game_sessions(id)" if table_exists(connection, "game_sessions") else "INTEGER",
            ),
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
                """INSERT INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at)
                   VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,image_path=excluded.image_path,updated_at=excluded.updated_at""",
                (state["map_id"], state["map_title"], state["map_image_path"], 1, state["updated_at"], state["updated_at"]),
            )
            if not map_fog_existed:
                connection.execute(
                """INSERT INTO session_workspace_map_fog(map_id,layer,enabled,revealed_cells_json,mist_density_json,updated_at)
                   SELECT ?,layer,enabled,revealed_cells_json,mist_density_json,updated_at FROM session_workspace_fog
                   WHERE 1 ON CONFLICT(map_id,layer) DO NOTHING""",
                    (state["map_id"],),
                )


def _token_record(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["conditions"] = json.loads(item.pop("conditions_json") or "[]")
    item["sheet"] = json.loads(item.pop("sheet_json") or "{}")
    item["visible_to_players"] = bool(item.get("visible_to_players", 1))
    return item


def _map_record(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["visible_to_players"] = bool(item.get("visible_to_players", 0))
    return item


def _item_record(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["effects"] = json.loads(item.pop("effects_json") or "[]")
    item["effect_rules"] = json.loads(item.pop("effect_rules_json") or "[]")
    mechanics = {
        "equipment_slots": [],
        "damage_formula": "",
        "consume_mode": "none",
        "charges_max": 0,
        "recharge": "none",
        "slot_limit": 1,
    }
    mechanics.update(json.loads(item.pop("mechanics_json") or "{}"))
    item["mechanics"] = mechanics
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
    visible_to_players: bool = True,
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
        token_id = f"{token_type}:{uuid.uuid4().hex}"
    if token_type == "location":
        current_hp = maximum_hp = character_id = None
    now = _now()
    values = (
        token_id, token_type, map_id, character_id, name, image_path, int(visible_to_players), color,
        max(0.0, min(100.0, float(latitude))), max(0.0, min(100.0, float(longitude))),
        current_hp, maximum_hp, json.dumps(conditions or [], ensure_ascii=False), json.dumps(sheet or {}, ensure_ascii=False), now, now,
    )
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            INSERT INTO session_workspace_tokens(
              id,token_type,map_id,character_id,name,image_path,visible_to_players,color,latitude,longitude,
              current_hp,maximum_hp,conditions_json,sheet_json,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              map_id=excluded.map_id,
              name=excluded.name,image_path=excluded.image_path,visible_to_players=excluded.visible_to_players,color=excluded.color,
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
    visible_to_players: bool | None = None,
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
    if visible_to_players is not None: updates["visible_to_players"] = int(visible_to_players)
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


def session_item_inventory_holders(database_path: Path, item_id: int) -> list[dict[str, Any]]:
    init_session_workspace(database_path)
    item_path = f"session-item:{item_id}"
    with closing(_connect(database_path)) as connection:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='player_inventory'"
        ).fetchone()
        if table is None:
            return []
        rows = connection.execute(
            "SELECT profile_id,quantity FROM player_inventory WHERE item_path=? AND quantity>0 ORDER BY profile_id",
            (item_path,),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_session_item(database_path: Path, item_id: int) -> bool:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection, connection:
        cursor = connection.execute("DELETE FROM session_custom_items WHERE id=?", (item_id,))
    return cursor.rowcount > 0


def save_workspace_icon(
    database_path: Path,
    *,
    label: str,
    category: str,
    path: str,
) -> dict[str, Any]:
    if category not in {"map", "items"}:
        raise ValueError("Categoria de ícone inválida")
    init_session_workspace(database_path)
    record = {
        "id": f"uploaded-icon:{uuid.uuid4().hex[:18]}",
        "label": label.strip(),
        "category": category,
        "path": path,
        "created_at": _now(),
    }
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            "INSERT INTO session_workspace_icons(id,label,category,path,created_at) VALUES(?,?,?,?,?)",
            (record["id"], record["label"], record["category"], record["path"], record["created_at"]),
        )
    return record


def list_workspace_icons(database_path: Path) -> list[dict[str, Any]]:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(
            "SELECT id,label,category,path,created_at FROM session_workspace_icons ORDER BY created_at DESC,id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def save_session_item(
    database_path: Path,
    *,
    name: str,
    item_type: str,
    description: str | None,
    effects: list[str],
    effect_rules: list[dict[str, Any]] | None = None,
    mechanics: dict[str, Any] | None = None,
    usable: bool,
    image_path: str | None = None,
    item_id: int | None = None,
) -> dict[str, Any]:
    init_session_workspace(database_path)
    now = _now()
    with closing(_connect(database_path)) as connection, connection:
        if item_id is None:
            cursor = connection.execute(
                """INSERT INTO session_custom_items(name,item_type,description,effects_json,effect_rules_json,mechanics_json,usable,image_path,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (name, item_type, description, json.dumps(effects, ensure_ascii=False), json.dumps(effect_rules or [], ensure_ascii=False), json.dumps(mechanics or {}, ensure_ascii=False), int(usable), image_path, now, now),
            )
            item_id = int(cursor.lastrowid)
        else:
            connection.execute(
                """UPDATE session_custom_items SET name=?,item_type=?,description=?,effects_json=?,effect_rules_json=?,mechanics_json=?,usable=?,image_path=?,updated_at=?
                   WHERE id=?""",
                (name, item_type, description, json.dumps(effects, ensure_ascii=False), json.dumps(effect_rules or [], ensure_ascii=False), json.dumps(mechanics or {}, ensure_ascii=False), int(usable), image_path, now, item_id),
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


def set_workspace_map(
    database_path: Path,
    *,
    title: str,
    image_path: str,
    visible_to_players: bool = False,
) -> dict[str, Any]:
    init_session_workspace(database_path)
    updated_at = _now()
    map_id = f"map:{uuid.uuid4().hex[:16]}"
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            "INSERT INTO session_workspace_maps(id,title,image_path,visible_to_players,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            (map_id, title, image_path, int(visible_to_players), updated_at, updated_at),
        )
        if connection.execute("SELECT id FROM session_workspace_state WHERE id=1").fetchone() is None:
            connection.execute(
                "INSERT INTO session_workspace_state(id,map_id,map_title,map_image_path,updated_at) VALUES(1,?,?,?,?)",
                (map_id, title, image_path, updated_at),
            )
    return {
        "id": map_id,
        "title": title,
        "image_path": image_path,
        "visible_to_players": bool(visible_to_players),
        "updated_at": updated_at,
    }


def ensure_official_workspace_maps(database_path: Path, vault_path: Path) -> list[dict[str, Any]]:
    """Register the campaign maps without changing the active map or its state."""
    init_session_workspace(database_path)
    now = _now()
    with closing(_connect(database_path)) as connection, connection:
        for stable_id, title, image_path in OFFICIAL_WORKSPACE_MAPS:
            if not (vault_path / image_path).is_file():
                continue
            existing = connection.execute(
                """SELECT id FROM session_workspace_maps
                   WHERE id=? OR lower(title)=lower(?) OR image_path=?
                   ORDER BY CASE WHEN id=? THEN 0 ELSE 1 END LIMIT 1""",
                (stable_id, title, image_path, stable_id),
            ).fetchone()
            if existing is None:
                connection.execute(
                    """INSERT INTO session_workspace_maps(
                       id,title,image_path,visible_to_players,created_at,updated_at
                       ) VALUES(?,?,?,?,?,?)""",
                    (stable_id, title, image_path, 1, now, now),
                )
            else:
                connection.execute(
                    """UPDATE session_workspace_maps
                       SET title=?,image_path=?,visible_to_players=1,updated_at=? WHERE id=?""",
                    (title, image_path, now, existing["id"]),
                )
    return list_workspace_maps(database_path)


def list_workspace_maps(database_path: Path, *, visible_to_players_only: bool = False) -> list[dict[str, Any]]:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection:
        query = "SELECT id,title,image_path,visible_to_players,created_at,updated_at FROM session_workspace_maps"
        if visible_to_players_only:
            query += " WHERE visible_to_players=1"
        rows = connection.execute(query + " ORDER BY created_at,id").fetchall()
    return [_map_record(row) for row in rows]


def update_workspace_map_visibility(
    database_path: Path, map_id: str, *, visible_to_players: bool
) -> dict[str, Any] | None:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection, connection:
        cursor = connection.execute(
            "UPDATE session_workspace_maps SET visible_to_players=?,updated_at=? WHERE id=?",
            (int(visible_to_players), _now(), map_id),
        )
        if cursor.rowcount == 0:
            return None
        row = connection.execute(
            "SELECT id,title,image_path,visible_to_players,created_at,updated_at FROM session_workspace_maps WHERE id=?",
            (map_id,),
        ).fetchone()
    return _map_record(row) if row is not None else None


def set_active_workspace_map(database_path: Path, map_id: str) -> dict[str, Any] | None:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT id,title,image_path,visible_to_players,created_at,updated_at FROM session_workspace_maps WHERE id=?", (map_id,)).fetchone()
        if row is None:
            return None
        connection.execute("UPDATE session_workspace_state SET map_id=?,map_title=?,map_image_path=?,view_zoom=1,view_scroll_left=0,view_scroll_top=0,updated_at=? WHERE id=1", (row["id"], row["title"], row["image_path"], _now()))
    return _map_record(row)


def update_workspace_view(
    database_path: Path,
    *,
    zoom: float,
    scroll_left: float,
    scroll_top: float,
) -> dict[str, float]:
    init_session_workspace(database_path)
    view = {
        "zoom": max(1.0, min(3.0, round(float(zoom), 1))),
        "scroll_left": max(0.0, min(1.0, float(scroll_left))),
        "scroll_top": max(0.0, min(1.0, float(scroll_top))),
    }
    with closing(_connect(database_path)) as connection, connection:
        cursor = connection.execute(
            "UPDATE session_workspace_state SET view_zoom=?,view_scroll_left=?,view_scroll_top=?,updated_at=? WHERE id=1",
            (view["zoom"], view["scroll_left"], view["scroll_top"], _now()),
        )
        if cursor.rowcount == 0:
            now = _now()
            connection.execute(
                "INSERT INTO session_workspace_state(id,map_id,map_title,map_image_path,view_zoom,view_scroll_left,view_scroll_top,updated_at) VALUES(1,?,?,?,?,?,?,?)",
                ("default", "Mapa de Nimalis", "zz_media/maps/mapa_de_nimalis.png", view["zoom"], view["scroll_left"], view["scroll_top"], now),
            )
    return view


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


def get_workspace_fog(database_path: Path, map_id: str = "default") -> dict[str, dict[str, Any]]:
    init_session_workspace(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(
            "SELECT layer,enabled,revealed_cells_json,mist_density_json,updated_at FROM session_workspace_map_fog WHERE map_id=?",
            (map_id,),
        ).fetchall()
        if not rows and map_id == "default":
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
    map_id: str = "default",
) -> dict[str, Any]:
    if layer not in FOG_LAYERS:
        raise ValueError("Camada de fog inválida")
    init_session_workspace(database_path)
    cells = _normalize_fog_cells(revealed_cells)
    density = _normalize_mist_density(mist_density)
    updated_at = _now()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """INSERT INTO session_workspace_map_fog(map_id,layer,enabled,revealed_cells_json,mist_density_json,updated_at)
               VALUES(?,?,?,?,?,?) ON CONFLICT(map_id,layer) DO UPDATE SET
                 enabled=excluded.enabled,
                 revealed_cells_json=excluded.revealed_cells_json,
                 mist_density_json=excluded.mist_density_json,
                 updated_at=excluded.updated_at""",
            (map_id, layer, int(enabled), json.dumps(cells), json.dumps(density), updated_at),
        )
    return get_workspace_fog(database_path, map_id)[layer]


def _token_fog_cell(latitude: float, longitude: float) -> str:
    column = min(FOG_COLUMNS - 1, max(0, int(float(longitude) / 100 * FOG_COLUMNS)))
    row = min(FOG_ROWS - 1, max(0, int(float(latitude) / 100 * FOG_ROWS)))
    return _cell_key(column, row)


def _token_is_visible(token: dict[str, Any], fog: dict[str, dict[str, Any]]) -> bool:
    if not token.get("visible_to_players", True):
        return False
    cell = _token_fog_cell(token["latitude"], token["longitude"])
    for data in fog.values():
        if not data["enabled"]:
            continue
        density = data.get("mist_density") or {}
        if density:
            if float(density.get(cell, 0) or 0) > 0:
                return False
            continue
        # Compatibilidade com mapas antigos, anteriores à fog por densidade.
        revealed = data.get("revealed_cells") or []
        if revealed and cell not in revealed:
            return False
    return True


def _insert_workspace_message(
    connection: sqlite3.Connection,
    *,
    actor_id: str,
    actor_name: str,
    actor_role: str,
    character_id: str | None,
    text: str,
    message_kind: str,
    created_at: str,
) -> dict[str, Any]:
    game_session_id = active_game_session_id(connection)
    cursor = connection.execute(
        """
        INSERT INTO session_workspace_messages(
          game_session_id,actor_id,actor_name,actor_role,character_id,message_kind,text,created_at
        ) VALUES(?,?,?,?,?,?,?,?)
        """,
        (game_session_id, actor_id, actor_name, actor_role, character_id, message_kind, text, created_at),
    )
    return {
        "id": int(cursor.lastrowid),
        "game_session_id": game_session_id,
        "actor_id": actor_id,
        "actor_name": actor_name,
        "actor_role": actor_role,
        "character_id": character_id,
        "message_kind": message_kind,
        "text": text,
        "created_at": created_at,
    }


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
        return _insert_workspace_message(
            connection,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=actor_role,
            character_id=character_id,
            text=text,
            message_kind=message_kind,
            created_at=created_at,
        )


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
    threshold = datetime.now(timezone.utc) - timedelta(seconds=PRESENCE_TIMEOUT_SECONDS)
    with closing(_connect(database_path)) as connection, connection:
        existing = connection.execute(
            "SELECT actor_id,actor_name,actor_role,character_id,last_seen_at FROM session_workspace_presence WHERE actor_id=?",
            (actor_id,),
        ).fetchone()
        stale_rows = connection.execute(
            "SELECT actor_id,actor_name,actor_role,character_id,last_seen_at FROM session_workspace_presence WHERE actor_role='player' AND actor_id<>?",
            (actor_id,),
        ).fetchall()
        for row in stale_rows:
            try:
                last_seen = datetime.fromisoformat(str(row["last_seen_at"]).replace("Z", "+00:00"))
            except ValueError:
                last_seen = datetime.min.replace(tzinfo=timezone.utc)
            if last_seen >= threshold:
                continue
            _insert_workspace_message(
                connection,
                actor_id=str(row["actor_id"]),
                actor_name=str(row["actor_name"]),
                actor_role="player",
                character_id=row["character_id"],
                text=f"{row['actor_name']} saiu da sessão.",
                message_kind="action",
                created_at=str(row["last_seen_at"]),
            )
            connection.execute("DELETE FROM session_workspace_presence WHERE actor_id=?", (row["actor_id"],))
        current_online = False
        if existing:
            try:
                current_seen = datetime.fromisoformat(str(existing["last_seen_at"]).replace("Z", "+00:00"))
                current_online = current_seen >= threshold
            except ValueError:
                current_online = False
        if actor_role == "player" and not current_online:
            _insert_workspace_message(
                connection,
                actor_id=actor_id,
                actor_name=actor_name,
                actor_role=actor_role,
                character_id=character_id,
                text=f"{actor_name} entrou na sessão.",
                message_kind="action",
                created_at=last_seen_at,
            )
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


def leave_workspace(
    database_path: Path,
    *,
    actor_id: str,
    actor_name: str,
    actor_role: str,
    character_id: str | None,
) -> dict[str, Any]:
    init_session_workspace(database_path)
    left_at = _now()
    with closing(_connect(database_path)) as connection, connection:
        existing = connection.execute(
            "SELECT actor_name,actor_role,character_id FROM session_workspace_presence WHERE actor_id=?",
            (actor_id,),
        ).fetchone()
        if existing:
            if actor_role == "player":
                _insert_workspace_message(
                    connection,
                    actor_id=actor_id,
                    actor_name=str(existing["actor_name"] or actor_name),
                    actor_role="player",
                    character_id=existing["character_id"] or character_id,
                    text=f"{existing['actor_name'] or actor_name} saiu da sessão.",
                    message_kind="action",
                    created_at=left_at,
                )
            connection.execute("DELETE FROM session_workspace_presence WHERE actor_id=?", (actor_id,))
    return {"actor_id": actor_id, "online": False}


def get_workspace_snapshot(
    database_path: Path,
    *,
    message_limit: int = 200,
    is_gm: bool = False,
    map_id: str | None = None,
) -> dict[str, Any]:
    init_session_workspace(database_path)
    threshold = datetime.now(timezone.utc) - timedelta(seconds=70)
    with closing(_connect(database_path)) as connection:
        state_row = connection.execute(
            "SELECT map_id,map_title,map_image_path,table_mode,view_zoom,view_scroll_left,view_scroll_top,updated_at FROM session_workspace_state WHERE id=1"
        ).fetchone()
        active_map_id = None
        if state_row and state_row["map_id"]:
            if is_gm:
                active_map_id = str(state_row["map_id"])
            else:
                visible_active_map = connection.execute(
                    "SELECT 1 FROM session_workspace_maps WHERE id=? AND visible_to_players=1",
                    (state_row["map_id"],),
                ).fetchone()
                if visible_active_map is not None:
                    active_map_id = str(state_row["map_id"])
        selected_map = None
        requested_map_id = map_id or (str(state_row["map_id"]) if state_row else None)
        if requested_map_id:
            visibility_clause = "" if is_gm else " AND visible_to_players=1"
            selected_map = connection.execute(
                f"SELECT id,title,image_path,visible_to_players,updated_at FROM session_workspace_maps WHERE id=?{visibility_clause}",
                (requested_map_id,),
            ).fetchone()
        if selected_map is None and not is_gm:
            selected_map = connection.execute(
                "SELECT id,title,image_path,visible_to_players,updated_at FROM session_workspace_maps WHERE visible_to_players=1 ORDER BY updated_at DESC,id LIMIT 1"
            ).fetchone()
        has_registered_maps = connection.execute("SELECT 1 FROM session_workspace_maps LIMIT 1").fetchone() is not None
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
    map_record = _map_record(selected_map) if selected_map is not None else None
    if map_record is None and is_gm and state_row:
        map_record = {
            "id": state_row["map_id"],
            "title": state_row["map_title"],
            "image_path": state_row["map_image_path"],
            "visible_to_players": False,
            "updated_at": state_row["updated_at"],
        }
    if map_record is None and not has_registered_maps:
        map_record = {
            "id": "default",
            "title": "Mapa de Nimalis",
            "image_path": "zz_media/maps/mapa_de_nimalis.png",
            "visible_to_players": True,
            "updated_at": state_row["updated_at"] if state_row else _now(),
        }
    fog = get_workspace_fog(database_path, str(map_record["id"]) if map_record else "default")
    tokens = list_workspace_tokens(database_path, str(map_record["id"])) if map_record else []
    if not is_gm:
        tokens = [token for token in tokens if _token_is_visible(token, fog)]
    return {
        "table_mode": str(state_row["table_mode"] or "digital") if state_row else "digital",
        "active_map_id": active_map_id,
        "map": map_record,
        "view": {
            "zoom": float(state_row["view_zoom"] or 1) if state_row and map_record and map_record["id"] == state_row["map_id"] else 1.0,
            "scroll_left": float(state_row["view_scroll_left"] or 0) if state_row and map_record and map_record["id"] == state_row["map_id"] else 0.0,
            "scroll_top": float(state_row["view_scroll_top"] or 0) if state_row and map_record and map_record["id"] == state_row["map_id"] else 0.0,
        },
        "messages": [dict(row) for row in message_rows],
        "presence": presence,
        "tokens": tokens,
        "fog": fog,
    }


def update_workspace_table_mode(database_path: Path, table_mode: str) -> str:
    init_session_workspace(database_path)
    normalized = str(table_mode or "").strip().lower()
    if normalized not in {"digital", "physical", "test"}:
        raise ValueError("Modo da mesa inválido.")
    now = _now()
    with closing(_connect(database_path)) as connection, connection:
        state = connection.execute("SELECT id FROM session_workspace_state WHERE id=1").fetchone()
        if state is None:
            connection.execute(
                """INSERT INTO session_workspace_state(
                   id,map_id,map_title,map_image_path,table_mode,updated_at
                   ) VALUES(1,'default','Mapa de Nimalis','zz_media/maps/mapa_de_nimalis.png',?,?)""",
                (normalized, now),
            )
        else:
            connection.execute(
                "UPDATE session_workspace_state SET table_mode=?,updated_at=? WHERE id=1",
                (normalized, now),
            )
    return normalized
