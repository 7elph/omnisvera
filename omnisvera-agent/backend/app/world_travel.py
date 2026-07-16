from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAP_TYPES = {"world", "continent", "territory", "region", "city", "district", "dungeon", "schematic", "custom"}
COORDINATE_SYSTEMS = {"image", "percentage", "geographic", "abstract"}
LOCATION_TYPES = {"realm", "territory", "region", "city", "village", "port", "fortress", "forest", "mountain", "road", "ruin", "dungeon", "building", "district", "landmark", "unknown", "custom"}
ROUTE_TYPES = {"road", "trail", "river", "sea", "mountain_pass", "underground", "portal", "urban", "wilderness", "custom"}
KNOWLEDGE_LEVELS = {"rumored", "approximate", "discovered", "visited", "mapped"}
KNOWLEDGE_RANK = {name: index for index, name in enumerate(("rumored", "approximate", "discovered", "visited", "mapped"))}
JOURNEY_STATUSES = {"planned", "active", "paused", "completed", "cancelled", "failed"}
VISIBILITIES = {"public", "table", "owner", "gm", "private"}
PARTICIPANT_TYPES = {"player_character", "npc", "companion", "vehicle", "unknown"}
MAX_TEXT = 4000


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any, label: str, *, required: bool = False, maximum: int = MAX_TEXT) -> str | None:
    result = str(value or "").strip()
    if required and not result:
        raise ValueError(f"{label} é obrigatório")
    if len(result) > maximum:
        raise ValueError(f"{label} excede {maximum} caracteres")
    return result or None


def _choice(value: Any, allowed: set[str], label: str, default: str | None = None) -> str:
    result = str(value or default or "").strip()
    if result not in allowed:
        raise ValueError(f"{label} inválido")
    return result


def _request_id(value: Any) -> str:
    result = str(value or "").strip()
    if not 8 <= len(result) <= 140 or not all(char.isalnum() or char in "._:-" for char in result):
        raise ValueError("request_id inválido")
    return result


def _number(value: Any, label: str, *, minimum: float | None = None, maximum: float | None = None) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} inválido") from error
    if minimum is not None and result < minimum:
        raise ValueError(f"{label} abaixo do mínimo")
    if maximum is not None and result > maximum:
        raise ValueError(f"{label} acima do máximo")
    return result


def _record(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for key in ("aliases_json", "before_json", "after_json"):
        if key in result:
            raw = result.pop(key)
            result[key.removesuffix("_json")] = json.loads(raw) if raw else ([] if key == "aliases_json" else None)
    for key in ("active", "discovered_by_default", "accessible", "public"):
        if key in result:
            result[key] = bool(result[key])
    if "voided_at" in result:
        result["voided"] = bool(result["voided_at"])
    return result


def _fetch(connection: sqlite3.Connection, table: str, row_id: int) -> dict[str, Any] | None:
    return _record(connection.execute(f"SELECT * FROM {table} WHERE id=?", (row_id,)).fetchone())


def _column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row[1] == column for row in connection.execute(f"PRAGMA table_info({table})"))


def init_world_travel(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS world_maps (
              id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
              campaign_id TEXT NOT NULL, title TEXT NOT NULL, source_path TEXT UNIQUE,
              image_path TEXT, map_type TEXT NOT NULL, width REAL, height REAL,
              coordinate_system TEXT NOT NULL, public_description TEXT,
              private_description TEXT, visibility TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
              created_by TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              version INTEGER NOT NULL DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_world_maps_campaign ON world_maps(campaign_id,active,title);

            CREATE TABLE IF NOT EXISTS world_locations (
              id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
              campaign_id TEXT NOT NULL, map_id INTEGER, source_path TEXT UNIQUE,
              slug TEXT NOT NULL, name TEXT NOT NULL, aliases_json TEXT,
              location_type TEXT NOT NULL, parent_location_id INTEGER, territory_name TEXT,
              public_description TEXT, private_description TEXT, portrait_or_cover_path TEXT,
              marker_icon TEXT, x REAL, y REAL, latitude REAL, longitude REAL,
              discovered_by_default INTEGER NOT NULL DEFAULT 0, visibility TEXT NOT NULL,
              canon_status TEXT, active INTEGER NOT NULL DEFAULT 1, created_by TEXT NOT NULL,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(map_id) REFERENCES world_maps(id),
              FOREIGN KEY(parent_location_id) REFERENCES world_locations(id)
            );
            CREATE INDEX IF NOT EXISTS idx_world_locations_campaign ON world_locations(campaign_id,map_id,name);

            CREATE TABLE IF NOT EXISTS location_states (
              location_id INTEGER PRIMARY KEY, public_status TEXT, private_status TEXT,
              controlling_faction TEXT, danger_label TEXT, accessible INTEGER NOT NULL DEFAULT 1,
              current_scene_id INTEGER, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(location_id) REFERENCES world_locations(id)
            );

            CREATE TABLE IF NOT EXISTS location_discoveries (
              id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
              campaign_id TEXT NOT NULL, location_id INTEGER NOT NULL, discoverer_type TEXT NOT NULL,
              character_id TEXT, party_id TEXT, discovered INTEGER NOT NULL DEFAULT 1,
              knowledge_level TEXT NOT NULL, public_name_override TEXT, discovered_at TEXT NOT NULL,
              discovered_by TEXT NOT NULL, source_scene_id INTEGER, source_contract_id INTEGER,
              notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(location_id) REFERENCES world_locations(id)
            );
            CREATE INDEX IF NOT EXISTS idx_location_discovery_lookup ON location_discoveries(location_id,discoverer_type,character_id,party_id);

            CREATE TABLE IF NOT EXISTS travel_routes (
              id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
              campaign_id TEXT NOT NULL, origin_location_id INTEGER NOT NULL,
              destination_location_id INTEGER NOT NULL, reverse_route_id INTEGER, title TEXT NOT NULL,
              route_type TEXT NOT NULL, public_description TEXT, private_description TEXT,
              distance_value REAL, distance_unit TEXT, duration_value REAL, duration_unit TEXT,
              difficulty_label TEXT, danger_label TEXT, required_condition TEXT,
              public INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
              created_by TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(origin_location_id) REFERENCES world_locations(id),
              FOREIGN KEY(destination_location_id) REFERENCES world_locations(id),
              FOREIGN KEY(reverse_route_id) REFERENCES travel_routes(id)
            );
            CREATE INDEX IF NOT EXISTS idx_travel_routes_campaign ON travel_routes(campaign_id,origin_location_id,destination_location_id);

            CREATE TABLE IF NOT EXISTS route_discoveries (
              id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
              route_id INTEGER NOT NULL, discoverer_type TEXT NOT NULL, character_id TEXT,
              party_id TEXT, knowledge_level TEXT NOT NULL, discovered_at TEXT NOT NULL,
              source_scene_id INTEGER, source_contract_id INTEGER,
              FOREIGN KEY(route_id) REFERENCES travel_routes(id)
            );

            CREATE TABLE IF NOT EXISTS journeys (
              id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
              campaign_id TEXT NOT NULL, session_id INTEGER, contract_id INTEGER, route_id INTEGER,
              origin_location_id INTEGER NOT NULL, destination_location_id INTEGER NOT NULL,
              title TEXT NOT NULL, status TEXT NOT NULL, visibility TEXT NOT NULL,
              planned_duration_value REAL, planned_duration_unit TEXT,
              progress_current REAL NOT NULL DEFAULT 0, progress_target REAL NOT NULL DEFAULT 1,
              started_at TEXT, paused_at TEXT, completed_at TEXT, cancelled_at TEXT,
              cancellation_reason TEXT, created_by TEXT NOT NULL, created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(route_id) REFERENCES travel_routes(id),
              FOREIGN KEY(origin_location_id) REFERENCES world_locations(id),
              FOREIGN KEY(destination_location_id) REFERENCES world_locations(id)
            );
            CREATE INDEX IF NOT EXISTS idx_journeys_campaign ON journeys(campaign_id,status,id DESC);

            CREATE TABLE IF NOT EXISTS journey_participants (
              id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
              journey_id INTEGER NOT NULL, participant_type TEXT NOT NULL, character_id TEXT,
              npc_id INTEGER, public_label TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active',
              joined_at TEXT NOT NULL, left_at TEXT, created_by TEXT NOT NULL,
              UNIQUE(journey_id,participant_type,character_id,npc_id),
              FOREIGN KEY(journey_id) REFERENCES journeys(id)
            );

            CREATE TABLE IF NOT EXISTS journey_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT, event_key TEXT UNIQUE NOT NULL,
              journey_id INTEGER NOT NULL, actor_id TEXT NOT NULL, actor_role TEXT NOT NULL,
              event_type TEXT NOT NULL, title TEXT NOT NULL, public_text TEXT, private_text TEXT,
              scene_id INTEGER, contract_id INTEGER, character_id TEXT, npc_id INTEGER,
              location_id INTEGER, before_json TEXT, after_json TEXT, visibility TEXT NOT NULL,
              created_at TEXT NOT NULL, voided_at TEXT, voided_by TEXT, void_reason TEXT,
              FOREIGN KEY(journey_id) REFERENCES journeys(id)
            );
            CREATE INDEX IF NOT EXISTS idx_journey_events ON journey_events(journey_id,id DESC);

            CREATE TABLE IF NOT EXISTS journey_scene_links (
              id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
              journey_id INTEGER NOT NULL, scene_id INTEGER NOT NULL, stage_label TEXT,
              progress_value REAL, created_by TEXT NOT NULL, created_at TEXT NOT NULL,
              UNIQUE(journey_id,scene_id), FOREIGN KEY(journey_id) REFERENCES journeys(id)
            );

            CREATE TABLE IF NOT EXISTS scene_location_links (
              id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
              scene_id INTEGER NOT NULL UNIQUE, location_id INTEGER NOT NULL,
              created_by TEXT NOT NULL, created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS contract_location_links (
              id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
              contract_id INTEGER NOT NULL, location_id INTEGER NOT NULL, role TEXT NOT NULL,
              public INTEGER NOT NULL DEFAULT 0, created_by TEXT NOT NULL, created_at TEXT NOT NULL,
              UNIQUE(contract_id,location_id,role)
            );
            """
        )
        if _column_exists(connection, "npc_states", "npc_id") and not _column_exists(connection, "npc_states", "current_location_id"):
            connection.execute("ALTER TABLE npc_states ADD COLUMN current_location_id INTEGER")
        if _column_exists(connection, "npc_states", "npc_id") and not _column_exists(connection, "npc_states", "active_journey_id"):
            connection.execute("ALTER TABLE npc_states ADD COLUMN active_journey_id INTEGER")


def _event(connection: sqlite3.Connection, *, event_key: str, journey_id: int, actor_id: str,
           event_type: str, title: str, public_text: str | None = None,
           private_text: str | None = None, visibility: str = "table", before: Any = None,
           after: Any = None, scene_id: int | None = None, contract_id: int | None = None,
           character_id: str | None = None, npc_id: int | None = None,
           location_id: int | None = None) -> dict[str, Any]:
    existing = connection.execute("SELECT * FROM journey_events WHERE event_key=?", (event_key,)).fetchone()
    if existing:
        return _record(existing) or {}
    connection.execute(
        """INSERT INTO journey_events(event_key,journey_id,actor_id,actor_role,event_type,title,
        public_text,private_text,scene_id,contract_id,character_id,npc_id,location_id,before_json,
        after_json,visibility,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (event_key, journey_id, actor_id, "gm", event_type, title, public_text, private_text,
         scene_id, contract_id, character_id, npc_id, location_id,
         json.dumps(before, ensure_ascii=False) if before is not None else None,
         json.dumps(after, ensure_ascii=False) if after is not None else None,
         _choice(visibility, VISIBILITIES, "visibilidade"), _now()),
    )
    return _record(connection.execute("SELECT * FROM journey_events WHERE event_key=?", (event_key,)).fetchone()) or {}


def _versioned_update(connection: sqlite3.Connection, table: str, row_id: int, expected_version: int,
                      fields: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
    before = _fetch(connection, table, row_id)
    if before is None:
        raise ValueError("Registro inexistente")
    if int(before["version"]) != expected_version:
        raise RuntimeError("Versão desatualizada")
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Campos não editáveis: {', '.join(sorted(unknown))}")
    if not fields:
        return before
    columns: list[str] = []
    values: list[Any] = []
    for key, value in fields.items():
        if key in {"active", "discovered_by_default", "accessible", "public"}:
            value = 1 if value else 0
        elif key == "aliases":
            key = "aliases_json"
            value = json.dumps(list(value or []), ensure_ascii=False)
        columns.append(f"{key}=?")
        values.append(value)
    columns.extend(["updated_at=?", "version=version+1"])
    values.extend([_now(), row_id, expected_version])
    cursor = connection.execute(f"UPDATE {table} SET {','.join(columns)} WHERE id=? AND version=?", values)
    if cursor.rowcount != 1:
        raise RuntimeError("Versão desatualizada")
    return _fetch(connection, table, row_id) or {}


def create_map(database_path: Path, *, request_id: str, campaign_id: str, actor_id: str,
               fields: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    init_world_travel(database_path)
    request_id = _request_id(request_id)
    with closing(_connect(database_path)) as connection, connection:
        existing = connection.execute("SELECT * FROM world_maps WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        source_path = _text(fields.get("source_path"), "fonte", maximum=500)
        if source_path:
            existing = connection.execute("SELECT * FROM world_maps WHERE source_path=?", (source_path,)).fetchone()
            if existing:
                return _record(existing) or {}, False
        now = _now()
        connection.execute(
            """INSERT INTO world_maps(request_id,campaign_id,title,source_path,image_path,map_type,width,height,
            coordinate_system,public_description,private_description,visibility,active,created_by,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (request_id, campaign_id, _text(fields.get("title"), "título", required=True, maximum=180), source_path,
             _text(fields.get("image_path"), "imagem", maximum=500), _choice(fields.get("map_type"), MAP_TYPES, "tipo", "custom"),
             _number(fields.get("width"), "largura", minimum=1), _number(fields.get("height"), "altura", minimum=1),
             _choice(fields.get("coordinate_system"), COORDINATE_SYSTEMS, "coordenadas", "percentage"),
             _text(fields.get("public_description"), "descrição pública"), _text(fields.get("private_description"), "descrição privada"),
             _choice(fields.get("visibility"), VISIBILITIES, "visibilidade", "gm"), 1 if fields.get("active", True) else 0,
             actor_id, now, now),
        )
        return _record(connection.execute("SELECT * FROM world_maps WHERE request_id=?", (request_id,)).fetchone()) or {}, True


def list_maps(database_path: Path, *, campaign_id: str, access_mode: str) -> list[dict[str, Any]]:
    init_world_travel(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT * FROM world_maps WHERE campaign_id=? AND active=1 ORDER BY title", (campaign_id,)).fetchall()
    maps = [_record(row) or {} for row in rows]
    if access_mode != "gm":
        maps = [item for item in maps if item.get("visibility") in {"public", "table"}]
        for item in maps:
            item.pop("private_description", None)
    return maps


def get_map(database_path: Path, map_id: int, *, access_mode: str) -> dict[str, Any] | None:
    init_world_travel(database_path)
    with closing(_connect(database_path)) as connection:
        item = _fetch(connection, "world_maps", map_id)
    if not item or (access_mode != "gm" and item.get("visibility") not in {"public", "table"}):
        return None
    if access_mode != "gm":
        item.pop("private_description", None)
    return item


def update_map(database_path: Path, map_id: int, *, expected_version: int, fields: dict[str, Any]) -> dict[str, Any]:
    with closing(_connect(database_path)) as connection, connection:
        return _versioned_update(connection, "world_maps", map_id, expected_version, fields,
            {"title", "image_path", "map_type", "width", "height", "coordinate_system", "public_description", "private_description", "visibility", "active"})


def create_location(database_path: Path, *, request_id: str, campaign_id: str, actor_id: str,
                    fields: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    init_world_travel(database_path)
    request_id = _request_id(request_id)
    with closing(_connect(database_path)) as connection, connection:
        existing = connection.execute("SELECT * FROM world_locations WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        source_path = _text(fields.get("source_path"), "fonte", maximum=500)
        if source_path:
            existing = connection.execute("SELECT * FROM world_locations WHERE source_path=?", (source_path,)).fetchone()
            if existing:
                return _record(existing) or {}, False
        name = _text(fields.get("name"), "nome", required=True, maximum=180) or "Local"
        slug = _text(fields.get("slug"), "slug", maximum=180) or "-".join(name.casefold().split())
        now = _now()
        x = _number(fields.get("x"), "x", minimum=0, maximum=100)
        y = _number(fields.get("y"), "y", minimum=0, maximum=100)
        cursor = connection.execute(
            """INSERT INTO world_locations(request_id,campaign_id,map_id,source_path,slug,name,aliases_json,
            location_type,parent_location_id,territory_name,public_description,private_description,
            portrait_or_cover_path,marker_icon,x,y,latitude,longitude,discovered_by_default,visibility,
            canon_status,active,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (request_id, campaign_id, fields.get("map_id"), source_path, slug, name,
             json.dumps(list(fields.get("aliases") or []), ensure_ascii=False),
             _choice(fields.get("location_type"), LOCATION_TYPES, "tipo", "unknown"), fields.get("parent_location_id"),
             _text(fields.get("territory_name"), "território", maximum=180), _text(fields.get("public_description"), "descrição pública"),
             _text(fields.get("private_description"), "descrição privada"), _text(fields.get("portrait_or_cover_path"), "imagem", maximum=500),
             _text(fields.get("marker_icon"), "ícone", maximum=100), x, y,
             _number(fields.get("latitude"), "latitude", minimum=-90, maximum=90),
             _number(fields.get("longitude"), "longitude", minimum=-180, maximum=180),
             1 if fields.get("discovered_by_default") else 0,
             _choice(fields.get("visibility"), VISIBILITIES, "visibilidade", "gm"),
             _text(fields.get("canon_status"), "estado canônico", maximum=120), 1 if fields.get("active", True) else 0,
             actor_id, now, now),
        )
        location_id = int(cursor.lastrowid)
        connection.execute("INSERT INTO location_states(location_id,public_status,private_status,controlling_faction,danger_label,accessible,current_scene_id,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (location_id, _text(fields.get("public_status"), "estado público", maximum=500), _text(fields.get("private_status"), "estado privado", maximum=500),
             _text(fields.get("controlling_faction"), "facção", maximum=180), _text(fields.get("danger_label"), "perigo", maximum=180),
             1 if fields.get("accessible", True) else 0, fields.get("current_scene_id"), now))
        return _location_with_state(connection, location_id) or {}, True


def _location_with_state(connection: sqlite3.Connection, location_id: int) -> dict[str, Any] | None:
    row = connection.execute("""SELECT l.*,s.public_status,s.private_status,s.controlling_faction,s.danger_label,
        s.accessible,s.current_scene_id,s.version AS state_version,s.updated_at AS state_updated_at
        FROM world_locations l LEFT JOIN location_states s ON s.location_id=l.id WHERE l.id=?""", (location_id,)).fetchone()
    return _record(row)


def _best_discovery(connection: sqlite3.Connection, location_id: int, profile_id: str | None) -> dict[str, Any] | None:
    rows = connection.execute("SELECT * FROM location_discoveries WHERE location_id=? AND discovered=1 ORDER BY id DESC", (location_id,)).fetchall()
    eligible = []
    for row in rows:
        item = _record(row) or {}
        if item.get("discoverer_type") in {"campaign", "party"} or (profile_id and item.get("character_id") == profile_id):
            eligible.append(item)
    return max(eligible, key=lambda item: KNOWLEDGE_RANK.get(str(item.get("knowledge_level")), -1), default=None)


def _filter_location(item: dict[str, Any], *, access_mode: str, discovery: dict[str, Any] | None) -> dict[str, Any] | None:
    if access_mode == "gm":
        item["knowledge_level"] = "mapped"
        return item
    if not item.get("active"):
        return None
    default_visible = item.get("discovered_by_default") and item.get("visibility") in {"public", "table"}
    if not default_visible and not discovery:
        return None
    level = str((discovery or {}).get("knowledge_level") or "discovered")
    item["knowledge_level"] = level
    item.pop("private_description", None)
    item.pop("private_status", None)
    if discovery and discovery.get("public_name_override"):
        item["name"] = discovery["public_name_override"]
        item["aliases"] = []
    if KNOWLEDGE_RANK.get(level, 0) < KNOWLEDGE_RANK["discovered"]:
        for key in ("x", "y", "latitude", "longitude"):
            item[key] = None
        if level == "rumored" and not (discovery or {}).get("public_name_override"):
            item["name"] = "Local ainda não identificado"
            item["aliases"] = []
    return item


def list_locations(database_path: Path, *, campaign_id: str, access_mode: str, profile_id: str | None = None,
                   map_id: int | None = None, query: str | None = None) -> list[dict[str, Any]]:
    init_world_travel(database_path)
    with closing(_connect(database_path)) as connection:
        sql = "SELECT id FROM world_locations WHERE campaign_id=?"
        params: list[Any] = [campaign_id]
        if map_id is not None:
            sql += " AND map_id=?"; params.append(map_id)
        ids = [int(row[0]) for row in connection.execute(sql + " ORDER BY name", params)]
        results = []
        for location_id in ids:
            item = _location_with_state(connection, location_id) or {}
            filtered = _filter_location(item, access_mode=access_mode, discovery=_best_discovery(connection, location_id, profile_id))
            if not filtered:
                continue
            if query and query.casefold() not in f"{filtered.get('name','')} {filtered.get('territory_name','')} {filtered.get('location_type','')}".casefold():
                continue
            results.append(filtered)
        return results


def get_location(database_path: Path, location_id: int, *, access_mode: str, profile_id: str | None = None) -> dict[str, Any] | None:
    init_world_travel(database_path)
    with closing(_connect(database_path)) as connection:
        item = _location_with_state(connection, location_id)
        if not item:
            return None
        return _filter_location(item, access_mode=access_mode, discovery=_best_discovery(connection, location_id, profile_id))


def update_location(database_path: Path, location_id: int, *, expected_version: int, fields: dict[str, Any]) -> dict[str, Any]:
    if "x" in fields: fields["x"] = _number(fields["x"], "x", minimum=0, maximum=100)
    if "y" in fields: fields["y"] = _number(fields["y"], "y", minimum=0, maximum=100)
    with closing(_connect(database_path)) as connection, connection:
        return _versioned_update(connection, "world_locations", location_id, expected_version, fields,
            {"map_id", "slug", "name", "aliases", "location_type", "parent_location_id", "territory_name", "public_description", "private_description", "portrait_or_cover_path", "marker_icon", "x", "y", "latitude", "longitude", "discovered_by_default", "visibility", "canon_status", "active"})


def update_location_state(database_path: Path, location_id: int, *, expected_version: int, fields: dict[str, Any]) -> dict[str, Any]:
    allowed = {"public_status", "private_status", "controlling_faction", "danger_label", "accessible", "current_scene_id"}
    unknown = set(fields) - allowed
    if unknown: raise ValueError("Campo de estado não editável")
    with closing(_connect(database_path)) as connection, connection:
        before = _record(connection.execute("SELECT * FROM location_states WHERE location_id=?", (location_id,)).fetchone())
        if not before: raise ValueError("Local inexistente")
        if int(before["version"]) != expected_version: raise RuntimeError("Versão desatualizada")
        columns=[]; values=[]
        for key,value in fields.items():
            if key == "accessible": value = 1 if value else 0
            columns.append(f"{key}=?"); values.append(value)
        if columns:
            values.extend([_now(), location_id, expected_version])
            if connection.execute(f"UPDATE location_states SET {','.join(columns)},updated_at=?,version=version+1 WHERE location_id=? AND version=?", values).rowcount != 1:
                raise RuntimeError("Versão desatualizada")
        return _location_with_state(connection, location_id) or {}


def discover_location(database_path: Path, location_id: int, *, request_id: str, campaign_id: str,
                      actor_id: str, fields: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    level = _choice(fields.get("knowledge_level"), KNOWLEDGE_LEVELS, "conhecimento", "discovered")
    with closing(_connect(database_path)) as connection, connection:
        if not _fetch(connection, "world_locations", location_id): raise ValueError("Local inexistente")
        existing = connection.execute("SELECT * FROM location_discoveries WHERE request_id=?", (request_id,)).fetchone()
        if existing: return _record(existing) or {}, False
        now = _now()
        connection.execute("""INSERT INTO location_discoveries(request_id,campaign_id,location_id,discoverer_type,character_id,party_id,discovered,knowledge_level,public_name_override,discovered_at,discovered_by,source_scene_id,source_contract_id,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (request_id,campaign_id,location_id,_text(fields.get("discoverer_type"),"descobridor",required=True,maximum=40),fields.get("character_id"),fields.get("party_id"),1,level,_text(fields.get("public_name_override"),"nome público",maximum=180),now,actor_id,fields.get("source_scene_id"),fields.get("source_contract_id"),_text(fields.get("notes"),"notas"),now,now))
        return _record(connection.execute("SELECT * FROM location_discoveries WHERE request_id=?", (request_id,)).fetchone()) or {}, True


def create_route(database_path: Path, *, request_id: str, campaign_id: str, actor_id: str, fields: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    origin = int(fields.get("origin_location_id") or 0); destination = int(fields.get("destination_location_id") or 0)
    if origin <= 0 or destination <= 0: raise ValueError("Origem e destino são obrigatórios")
    if origin == destination: raise ValueError("Origem e destino devem ser diferentes")
    with closing(_connect(database_path)) as connection, connection:
        if not _fetch(connection,"world_locations",origin) or not _fetch(connection,"world_locations",destination): raise ValueError("Origem ou destino inexistente")
        existing=connection.execute("SELECT * FROM travel_routes WHERE request_id=?",(request_id,)).fetchone()
        if existing: return _record(existing) or {},False
        now=_now()
        connection.execute("""INSERT INTO travel_routes(request_id,campaign_id,origin_location_id,destination_location_id,reverse_route_id,title,route_type,public_description,private_description,distance_value,distance_unit,duration_value,duration_unit,difficulty_label,danger_label,required_condition,public,active,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (request_id,campaign_id,origin,destination,fields.get("reverse_route_id"),_text(fields.get("title"),"título",required=True,maximum=180),_choice(fields.get("route_type"),ROUTE_TYPES,"tipo","custom"),_text(fields.get("public_description"),"descrição"),_text(fields.get("private_description"),"descrição privada"),_number(fields.get("distance_value"),"distância",minimum=0),_text(fields.get("distance_unit"),"unidade",maximum=40),_number(fields.get("duration_value"),"duração",minimum=0),_text(fields.get("duration_unit"),"unidade",maximum=40),_text(fields.get("difficulty_label"),"dificuldade",maximum=120),_text(fields.get("danger_label"),"perigo",maximum=120),_text(fields.get("required_condition"),"condição",maximum=300),1 if fields.get("public") else 0,1 if fields.get("active",True) else 0,actor_id,now,now))
        return _record(connection.execute("SELECT * FROM travel_routes WHERE request_id=?",(request_id,)).fetchone()) or {},True


def list_routes(database_path: Path, *, campaign_id: str, access_mode: str, profile_id: str | None = None) -> list[dict[str, Any]]:
    init_world_travel(database_path)
    with closing(_connect(database_path)) as connection:
        rows=connection.execute("SELECT * FROM travel_routes WHERE campaign_id=? AND active=1 ORDER BY title",(campaign_id,)).fetchall()
        visible_location_ids={item["id"] for item in list_locations(database_path,campaign_id=campaign_id,access_mode=access_mode,profile_id=profile_id)}
        result=[]
        for row in rows:
            item=_record(row) or {}
            explicit=connection.execute("SELECT 1 FROM route_discoveries WHERE route_id=? AND (discoverer_type IN ('campaign','party') OR character_id=?)",(item["id"],profile_id)).fetchone()
            if access_mode != "gm" and not ((item.get("public") or explicit) and item["origin_location_id"] in visible_location_ids and item["destination_location_id"] in visible_location_ids): continue
            if access_mode != "gm": item.pop("private_description",None); item.pop("required_condition",None)
            result.append(item)
        return result


def update_route(database_path: Path, route_id: int, *, expected_version: int, fields: dict[str, Any]) -> dict[str, Any]:
    if "origin_location_id" in fields and "destination_location_id" in fields and fields["origin_location_id"] == fields["destination_location_id"]:
        raise ValueError("Origem e destino devem ser diferentes")
    with closing(_connect(database_path)) as connection, connection:
        return _versioned_update(connection, "travel_routes", route_id, expected_version, fields,
            {"origin_location_id", "destination_location_id", "reverse_route_id", "title", "route_type", "public_description", "private_description", "distance_value", "distance_unit", "duration_value", "duration_unit", "difficulty_label", "danger_label", "required_condition", "public", "active"})


def discover_route(database_path: Path, route_id: int, *, request_id: str, fields: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    with closing(_connect(database_path)) as connection, connection:
        if not _fetch(connection, "travel_routes", route_id): raise ValueError("Rota inexistente")
        existing = connection.execute("SELECT * FROM route_discoveries WHERE request_id=?", (request_id,)).fetchone()
        if existing: return _record(existing) or {}, False
        connection.execute("INSERT INTO route_discoveries(request_id,route_id,discoverer_type,character_id,party_id,knowledge_level,discovered_at,source_scene_id,source_contract_id) VALUES(?,?,?,?,?,?,?,?,?)",
            (request_id, route_id, _text(fields.get("discoverer_type"), "descobridor", required=True, maximum=40), fields.get("character_id"), fields.get("party_id"), _choice(fields.get("knowledge_level"), KNOWLEDGE_LEVELS, "conhecimento", "discovered"), _now(), fields.get("source_scene_id"), fields.get("source_contract_id")))
        return _record(connection.execute("SELECT * FROM route_discoveries WHERE request_id=?", (request_id,)).fetchone()) or {}, True


def create_journey(database_path: Path, *, request_id: str, campaign_id: str, actor_id: str, fields: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    request_id=_request_id(request_id); origin=int(fields.get("origin_location_id") or 0); destination=int(fields.get("destination_location_id") or 0)
    if origin == destination: raise ValueError("Origem e destino devem ser diferentes")
    target=_number(fields.get("progress_target"),"progresso alvo",minimum=0.0001) or 1
    with closing(_connect(database_path)) as connection,connection:
        if not _fetch(connection,"world_locations",origin) or not _fetch(connection,"world_locations",destination): raise ValueError("Origem ou destino inexistente")
        existing=connection.execute("SELECT * FROM journeys WHERE request_id=?",(request_id,)).fetchone()
        if existing: return _record(existing) or {},False
        now=_now(); cursor=connection.execute("""INSERT INTO journeys(request_id,campaign_id,session_id,contract_id,route_id,origin_location_id,destination_location_id,title,status,visibility,planned_duration_value,planned_duration_unit,progress_current,progress_target,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (request_id,campaign_id,fields.get("session_id"),fields.get("contract_id"),fields.get("route_id"),origin,destination,_text(fields.get("title"),"título",required=True,maximum=180),"planned",_choice(fields.get("visibility"),VISIBILITIES,"visibilidade","table"),_number(fields.get("planned_duration_value"),"duração",minimum=0),_text(fields.get("planned_duration_unit"),"unidade",maximum=40),0,target,actor_id,now,now))
        journey_id=int(cursor.lastrowid); _event(connection,event_key=f"journey:create:{request_id}",journey_id=journey_id,actor_id=actor_id,event_type="created",title="Viagem planejada",after={"status":"planned"})
        return _journey_detail(connection,journey_id),True


def _journey_detail(connection: sqlite3.Connection, journey_id: int) -> dict[str, Any]:
    item=_fetch(connection,"journeys",journey_id)
    if not item: raise ValueError("Viagem inexistente")
    item["participants"]=[_record(row) or {} for row in connection.execute("SELECT * FROM journey_participants WHERE journey_id=? ORDER BY id",(journey_id,))]
    item["scene_links"]=[_record(row) or {} for row in connection.execute("SELECT * FROM journey_scene_links WHERE journey_id=? ORDER BY id",(journey_id,))]
    return item


def _can_view_journey(item: dict[str, Any], access_mode: str, profile_id: str | None) -> bool:
    if access_mode == "gm": return True
    if item.get("visibility") in {"public","table"}: return True
    return bool(profile_id and any(p.get("character_id") == profile_id for p in item.get("participants",[])))


def _sanitize_journey(database_path: Path, item: dict[str, Any], *, access_mode: str,
                      profile_id: str | None) -> dict[str, Any]:
    if access_mode == "gm":
        return item
    item.pop("cancellation_reason", None)
    with closing(_connect(database_path)) as connection:
        try:
            visible_scene_ids = {
                int(row[0]) for row in connection.execute(
                    "SELECT id FROM scenes WHERE visibility IN ('public','table')"
                )
            }
        except sqlite3.OperationalError:
            visible_scene_ids = set()
    item["scene_links"] = [
        link for link in item.get("scene_links", [])
        if int(link.get("scene_id") or 0) in visible_scene_ids
    ]
    visible_route_ids = {
        int(route["id"]) for route in list_routes(
            database_path, campaign_id=str(item.get("campaign_id") or "omnisvera"),
            access_mode=access_mode, profile_id=profile_id,
        )
    }
    if item.get("route_id") and int(item["route_id"]) not in visible_route_ids:
        item["route_id"] = None
    return item


def get_journey(database_path: Path, journey_id: int, *, access_mode: str, profile_id: str | None = None) -> dict[str, Any] | None:
    init_world_travel(database_path)
    with closing(_connect(database_path)) as connection:
        try: item=_journey_detail(connection,journey_id)
        except ValueError: return None
    if not _can_view_journey(item,access_mode,profile_id): return None
    return _sanitize_journey(database_path, item, access_mode=access_mode, profile_id=profile_id)


def list_journeys(database_path: Path, *, campaign_id: str, access_mode: str, profile_id: str | None = None) -> list[dict[str, Any]]:
    init_world_travel(database_path)
    with closing(_connect(database_path)) as connection:
        ids=[int(row[0]) for row in connection.execute("SELECT id FROM journeys WHERE campaign_id=? ORDER BY id DESC",(campaign_id,))]
        result=[]
        for journey_id in ids:
            item=_journey_detail(connection,journey_id)
            if _can_view_journey(item,access_mode,profile_id):
                result.append(_sanitize_journey(database_path, item, access_mode=access_mode, profile_id=profile_id))
        return result


def update_planned_journey(database_path: Path, journey_id: int, *, expected_version: int, fields: dict[str, Any]) -> dict[str, Any]:
    with closing(_connect(database_path)) as connection, connection:
        before = _fetch(connection, "journeys", journey_id)
        if not before: raise ValueError("Viagem inexistente")
        if before["status"] != "planned": raise ValueError("Somente viagem planejada pode ser editada")
        updated = _versioned_update(connection, "journeys", journey_id, expected_version, fields,
            {"session_id", "contract_id", "route_id", "origin_location_id", "destination_location_id", "title", "visibility", "planned_duration_value", "planned_duration_unit", "progress_target"})
        return _journey_detail(connection, int(updated["id"]))


def add_journey_participant(database_path: Path, journey_id: int, *, request_id: str, actor_id: str, fields: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    request_id=_request_id(request_id); participant_type=_choice(fields.get("participant_type"),PARTICIPANT_TYPES,"tipo")
    character_id=_text(fields.get("character_id"),"personagem",maximum=180); npc_id=fields.get("npc_id")
    if participant_type=="player_character" and not character_id: raise ValueError("Personagem é obrigatório")
    if participant_type=="npc" and not npc_id: raise ValueError("NPC é obrigatório")
    with closing(_connect(database_path)) as connection,connection:
        journey=_fetch(connection,"journeys",journey_id)
        if not journey: raise ValueError("Viagem inexistente")
        existing=connection.execute("SELECT * FROM journey_participants WHERE request_id=?",(request_id,)).fetchone()
        if existing: return _record(existing) or {},False
        duplicate=connection.execute("SELECT * FROM journey_participants WHERE journey_id=? AND participant_type=? AND character_id IS ? AND npc_id IS ?",(journey_id,participant_type,character_id,npc_id)).fetchone()
        if duplicate: raise ValueError("Participante já incluído")
        now=_now(); connection.execute("INSERT INTO journey_participants(request_id,journey_id,participant_type,character_id,npc_id,public_label,status,joined_at,created_by) VALUES(?,?,?,?,?,?,?,?,?)",(request_id,journey_id,participant_type,character_id,npc_id,_text(fields.get("public_label"),"rótulo",required=True,maximum=180),"active",now,actor_id))
        item=_record(connection.execute("SELECT * FROM journey_participants WHERE request_id=?",(request_id,)).fetchone()) or {}
        _event(connection,event_key=f"journey:participant:{request_id}",journey_id=journey_id,actor_id=actor_id,event_type="participant_added",title=f"{item['public_label']} entrou na viagem",character_id=character_id,npc_id=npc_id,after=item)
        return item,True


def remove_journey_participant(database_path: Path, participant_id: int, *, request_id: str, actor_id: str, reason: str) -> dict[str, Any]:
    request_id = _request_id(request_id)
    with closing(_connect(database_path)) as connection, connection:
        item = _fetch(connection, "journey_participants", participant_id)
        if not item: raise ValueError("Participante inexistente")
        if item.get("left_at"): return item
        journey = _fetch(connection, "journeys", int(item["journey_id"])) or {}
        if journey.get("status") in {"completed", "cancelled", "failed"}: raise ValueError("Viagem encerrada")
        connection.execute("UPDATE journey_participants SET status='removed',left_at=? WHERE id=?", (_now(), participant_id))
        after = _fetch(connection, "journey_participants", participant_id) or {}
        _event(connection, event_key=f"journey:participant-remove:{request_id}", journey_id=int(item["journey_id"]), actor_id=actor_id, event_type="participant_removed", title=f"{item['public_label']} saiu da viagem", public_text=_text(reason, "motivo", required=True, maximum=500), character_id=item.get("character_id"), npc_id=item.get("npc_id"), before=item, after=after)
        return after


def _transition(database_path: Path, journey_id: int, *, request_id: str, actor_id: str, action: str, expected_version: int, reason: str | None = None) -> dict[str, Any]:
    request_id=_request_id(request_id)
    allowed={"start":({"planned"},"active","started"),"pause":({"active"},"paused","paused"),"resume":({"paused"},"active","resumed"),"cancel":({"planned","active","paused"},"cancelled","cancelled"),"fail":({"active","paused"},"failed","failed")}
    if action not in allowed: raise ValueError("Transição inválida")
    sources,target,event_type=allowed[action]
    with closing(_connect(database_path)) as connection,connection:
        before=_fetch(connection,"journeys",journey_id)
        if not before: raise ValueError("Viagem inexistente")
        existing=connection.execute("SELECT * FROM journey_events WHERE event_key=?",(f"journey:{action}:{request_id}",)).fetchone()
        if existing: return _journey_detail(connection,journey_id)
        if int(before["version"])!=expected_version: raise RuntimeError("Versão desatualizada")
        if before["status"] not in sources: raise ValueError(f"Não é possível {action} uma viagem {before['status']}")
        now=_now(); columns=["status=?","updated_at=?","version=version+1"]; values=[target,now]
        if action=="start": columns.append("started_at=?"); values.append(now)
        if action=="pause": columns.append("paused_at=?"); values.append(now)
        if action=="resume": columns.append("paused_at=NULL")
        if action in {"cancel","fail"}: columns.extend(["cancelled_at=?","cancellation_reason=?"]); values.extend([now,_text(reason,"motivo",required=True,maximum=500)])
        values.extend([journey_id,expected_version]); connection.execute(f"UPDATE journeys SET {','.join(columns)} WHERE id=? AND version=?",values)
        if action in {"start", "cancel", "fail"}:
            active_value = journey_id if action == "start" else None
            for participant in connection.execute("SELECT * FROM journey_participants WHERE journey_id=? AND status='active'", (journey_id,)).fetchall():
                if participant["character_id"]:
                    state_row = connection.execute("SELECT * FROM character_states WHERE profile_id=?", (participant["character_id"],)).fetchone()
                    if state_row:
                        state = json.loads(state_row["state_json"]); state["active_journey_id"] = active_value
                        connection.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?", (json.dumps(state, ensure_ascii=False), now, participant["character_id"]))
                if participant["npc_id"]:
                    connection.execute("UPDATE npc_states SET active_journey_id=?,version=version+1,updated_at=? WHERE npc_id=?", (active_value, now, participant["npc_id"]))
        after=_fetch(connection,"journeys",journey_id) or {}; _event(connection,event_key=f"journey:{action}:{request_id}",journey_id=journey_id,actor_id=actor_id,event_type=event_type,title=f"Viagem {target}",public_text=reason if action in {"cancel","fail"} else None,before=before,after=after)
        return _journey_detail(connection,journey_id)


def transition_journey(database_path: Path, journey_id: int, **kwargs: Any) -> dict[str, Any]:
    return _transition(database_path,journey_id,**kwargs)


def advance_journey(database_path: Path, journey_id: int, *, request_id: str, actor_id: str, expected_version: int, amount: float) -> dict[str, Any]:
    request_id=_request_id(request_id); amount=_number(amount,"avanço",minimum=0.0001) or 0
    with closing(_connect(database_path)) as connection,connection:
        before=_fetch(connection,"journeys",journey_id)
        if not before: raise ValueError("Viagem inexistente")
        if connection.execute("SELECT 1 FROM journey_events WHERE event_key=?",(f"journey:advance:{request_id}",)).fetchone(): return _journey_detail(connection,journey_id)
        if int(before["version"])!=expected_version: raise RuntimeError("Versão desatualizada")
        if before["status"]!="active": raise ValueError("Somente viagem ativa pode avançar")
        current=float(before["progress_current"]); target=float(before["progress_target"]); after_value=current+amount
        if after_value>target: raise ValueError("Progresso ultrapassa o alvo; conclua a viagem")
        connection.execute("UPDATE journeys SET progress_current=?,updated_at=?,version=version+1 WHERE id=? AND version=?",(after_value,_now(),journey_id,expected_version))
        after=_fetch(connection,"journeys",journey_id) or {}; _event(connection,event_key=f"journey:advance:{request_id}",journey_id=journey_id,actor_id=actor_id,event_type="advanced",title="Viagem avançou",before={"progress":current},after={"progress":after_value})
        return _journey_detail(connection,journey_id)


def _move_character(connection: sqlite3.Connection, character_id: str, location_id: int, location_name: str, actor_id: str, journey_id: int) -> None:
    row=connection.execute("SELECT * FROM character_states WHERE profile_id=?",(character_id,)).fetchone()
    if not row: return
    state=json.loads(row["state_json"]); before={"location":state.get("location"),"current_location_id":state.get("current_location_id")}
    state["location"]=location_name; state["current_location_id"]=location_id; state["active_journey_id"]=None
    now=_now(); connection.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?",(json.dumps(state,ensure_ascii=False),now,character_id))
    connection.execute("""INSERT INTO character_events(character_id,session_id,actor_id,actor_role,event_type,field,before_json,after_json,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",(character_id,None,actor_id,"gm","journey_arrival","location",json.dumps(before,ensure_ascii=False),json.dumps({"location":location_name,"current_location_id":location_id},ensure_ascii=False),f"Chegada pela viagem {journey_id}",now))


def _move_npc(connection: sqlite3.Connection, npc_id: int, location_id: int, location_name: str, actor_id: str, journey_id: int) -> None:
    row=connection.execute("SELECT * FROM npc_states WHERE npc_id=?",(npc_id,)).fetchone()
    if not row: return
    before=dict(row); now=_now(); connection.execute("UPDATE npc_states SET current_location=?,current_location_id=?,active_journey_id=NULL,version=version+1,updated_at=? WHERE npc_id=?",(location_name,location_id,now,npc_id))
    connection.execute("""INSERT OR IGNORE INTO npc_events(event_key,npc_id,actor_id,actor_role,event_type,title,public_text,before_json,after_json,visibility,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(f"npc:journey:{journey_id}:{npc_id}",npc_id,actor_id,"gm","location_changed","NPC chegou ao destino",location_name,json.dumps(before,ensure_ascii=False),json.dumps({"current_location":location_name,"current_location_id":location_id},ensure_ascii=False),"gm",now))


def complete_journey(database_path: Path, journey_id: int, *, request_id: str, actor_id: str, expected_version: int) -> dict[str, Any]:
    request_id=_request_id(request_id)
    with closing(_connect(database_path)) as connection,connection:
        before=_fetch(connection,"journeys",journey_id)
        if not before: raise ValueError("Viagem inexistente")
        if connection.execute("SELECT 1 FROM journey_events WHERE event_key=?",(f"journey:complete:{request_id}",)).fetchone(): return _journey_detail(connection,journey_id)
        if int(before["version"])!=expected_version: raise RuntimeError("Versão desatualizada")
        if before["status"] not in {"active","paused"}: raise ValueError("Viagem não pode ser concluída")
        destination=_fetch(connection,"world_locations",int(before["destination_location_id"])) or {}; name=str(destination.get("name") or "Destino")
        now=_now(); connection.execute("UPDATE journeys SET status='completed',progress_current=progress_target,completed_at=?,updated_at=?,version=version+1 WHERE id=? AND version=?",(now,now,journey_id,expected_version))
        participants=[_record(row) or {} for row in connection.execute("SELECT * FROM journey_participants WHERE journey_id=? AND status='active'",(journey_id,))]
        for participant in participants:
            if participant.get("character_id"): _move_character(connection,str(participant["character_id"]),int(destination["id"]),name,actor_id,journey_id)
            if participant.get("npc_id"): _move_npc(connection,int(participant["npc_id"]),int(destination["id"]),name,actor_id,journey_id)
        after=_fetch(connection,"journeys",journey_id) or {}; _event(connection,event_key=f"journey:complete:{request_id}",journey_id=journey_id,actor_id=actor_id,event_type="arrival",title=f"Chegada a {name}",location_id=int(destination["id"]),before=before,after=after)
        return _journey_detail(connection,journey_id)


def link_journey_scene(database_path: Path, journey_id: int, *, request_id: str, actor_id: str, scene_id: int, stage_label: str | None = None, progress_value: float | None = None) -> tuple[dict[str, Any], bool]:
    request_id=_request_id(request_id)
    with closing(_connect(database_path)) as connection,connection:
        if not _fetch(connection,"journeys",journey_id): raise ValueError("Viagem inexistente")
        existing=connection.execute("SELECT * FROM journey_scene_links WHERE request_id=?",(request_id,)).fetchone()
        if existing: return _record(existing) or {},False
        duplicate=connection.execute("SELECT * FROM journey_scene_links WHERE journey_id=? AND scene_id=?",(journey_id,scene_id)).fetchone()
        if duplicate: return _record(duplicate) or {},False
        now=_now(); connection.execute("INSERT INTO journey_scene_links(request_id,journey_id,scene_id,stage_label,progress_value,created_by,created_at) VALUES(?,?,?,?,?,?,?)",(request_id,journey_id,scene_id,_text(stage_label,"etapa",maximum=180),_number(progress_value,"progresso",minimum=0),actor_id,now))
        item=_record(connection.execute("SELECT * FROM journey_scene_links WHERE request_id=?",(request_id,)).fetchone()) or {}; _event(connection,event_key=f"journey:scene:{request_id}",journey_id=journey_id,actor_id=actor_id,event_type="scene_linked",title="Cena vinculada à viagem",scene_id=scene_id,after=item)
        return item,True


def list_journey_events(database_path: Path, journey_id: int, *, access_mode: str) -> list[dict[str, Any]]:
    init_world_travel(database_path)
    with closing(_connect(database_path)) as connection:
        rows=connection.execute("SELECT * FROM journey_events WHERE journey_id=? ORDER BY id DESC",(journey_id,)).fetchall()
    result=[]
    for row in rows:
        item=_record(row) or {}
        if access_mode!="gm" and item.get("visibility") not in {"public","table"}: continue
        if access_mode!="gm":
            item.pop("private_text",None)
            item.pop("before_json",None)
            item.pop("after_json",None)
            item.pop("void_reason",None)
        result.append(item)
    return result


def void_journey_event(database_path: Path, event_id: int, *, actor_id: str, reason: str) -> dict[str, Any]:
    reason=_text(reason,"motivo",required=True,maximum=500) or ""
    with closing(_connect(database_path)) as connection,connection:
        item=_fetch(connection,"journey_events",event_id)
        if not item: raise ValueError("Evento inexistente")
        if item.get("voided_at"): return item
        connection.execute("UPDATE journey_events SET voided_at=?,voided_by=?,void_reason=? WHERE id=?",(_now(),actor_id,reason,event_id))
        return _fetch(connection,"journey_events",event_id) or {}


def link_location(database_path: Path, *, kind: str, owner_id: int, location_id: int, request_id: str,
                  actor_id: str, role: str = "related", public: bool = False) -> tuple[dict[str, Any], bool]:
    request_id=_request_id(request_id)
    table="scene_location_links" if kind=="scene" else "contract_location_links"
    owner_column="scene_id" if kind=="scene" else "contract_id"
    with closing(_connect(database_path)) as connection,connection:
        if not _fetch(connection,"world_locations",location_id): raise ValueError("Local inexistente")
        existing=connection.execute(f"SELECT * FROM {table} WHERE request_id=?",(request_id,)).fetchone()
        if existing: return _record(existing) or {},False
        if kind=="scene":
            connection.execute("INSERT INTO scene_location_links(request_id,scene_id,location_id,created_by,created_at) VALUES(?,?,?,?,?)",(request_id,owner_id,location_id,actor_id,_now()))
        else:
            connection.execute("INSERT INTO contract_location_links(request_id,contract_id,location_id,role,public,created_by,created_at) VALUES(?,?,?,?,?,?,?)",(request_id,owner_id,location_id,_text(role,"papel",required=True,maximum=80),1 if public else 0,actor_id,_now()))
        return _record(connection.execute(f"SELECT * FROM {table} WHERE request_id=?",(request_id,)).fetchone()) or {},True


def related_locations(database_path: Path, *, kind: str, owner_id: int, access_mode: str, profile_id: str | None = None) -> list[dict[str, Any]]:
    table="scene_location_links" if kind=="scene" else "contract_location_links"; owner_column="scene_id" if kind=="scene" else "contract_id"
    with closing(_connect(database_path)) as connection:
        rows=connection.execute(f"SELECT * FROM {table} WHERE {owner_column}=?",(owner_id,)).fetchall()
    result=[]
    for row in rows:
        link=_record(row) or {}
        if kind=="contract" and access_mode!="gm" and not link.get("public"): continue
        location=get_location(database_path,int(link["location_id"]),access_mode=access_mode,profile_id=profile_id)
        if location: result.append({"link":link,"location":location})
    return result
