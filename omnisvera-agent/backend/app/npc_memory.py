from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MEMORY_TYPES = {
    "encounter", "fact", "rumor", "promise", "debt", "favor", "threat",
    "betrayal", "gift", "insult", "secret", "agreement", "conflict",
    "observation", "custom",
}
MEMORY_STATUSES = {"active", "resolved", "contradicted", "forgotten", "voided"}
CONFIDENCE_LEVELS = {"confirmed", "believed", "suspected", "doubtful", "false_known_by_npc"}
IMPORTANCE_LEVELS = {"low", "medium", "high", "critical"}
VISIBILITIES = {"table", "owner", "gm", "private"}
TARGET_TYPES = {"character", "npc", "faction", "group"}
RELATIONSHIP_STATUSES = {"active", "inactive", "resolved", "voided"}
OBLIGATION_STATUSES = {"active", "fulfilled", "broken", "forgiven", "expired", "voided"}
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


def _request_id(value: Any) -> str:
    result = str(value or "").strip()
    if not 8 <= len(result) <= 140 or not all(char.isalnum() or char in "._:-" for char in result):
        raise ValueError("request_id inválido")
    return result


def _choice(value: Any, allowed: set[str], label: str) -> str:
    result = str(value or "").strip()
    if result not in allowed:
        raise ValueError(f"{label} inválido")
    return result


def _optional_score(value: Any, label: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} deve ser inteiro") from error
    if not -100 <= parsed <= 100:
        raise ValueError(f"{label} deve estar entre -100 e 100")
    return parsed


def _json(value: Any) -> str | None:
    return None if value is None else json.dumps(value, ensure_ascii=False)


def _loads(value: Any, fallback: Any = None) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return fallback


def _slug(value: Any) -> str:
    text = str(value or "npc").strip().casefold()
    text = re.sub(r"[^a-z0-9à-ÿ]+", "-", text, flags=re.IGNORECASE).strip("-")
    return text or "npc"


def _record(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for key in ("aliases_json", "faction_names_json", "before_json", "after_json"):
        if key in result:
            result[key.removesuffix("_json")] = _loads(result.pop(key), [] if key.endswith("names_json") or key == "aliases_json" else None)
    for key in ("visible_to_players", "active"):
        if key in result:
            result[key] = bool(result[key])
    if "voided_at" in result:
        result["voided"] = bool(result["voided_at"])
    return result


def _fetch(connection: sqlite3.Connection, table: str, row_id: int) -> dict[str, Any] | None:
    return _record(connection.execute(f"SELECT * FROM {table} WHERE id=?", (row_id,)).fetchone())


def _npc_or_error(connection: sqlite3.Connection, npc_id: int) -> dict[str, Any]:
    npc = _fetch(connection, "npc_definitions", npc_id)
    if npc is None:
        raise ValueError("NPC inexistente")
    return npc


def _event(
    connection: sqlite3.Connection,
    *,
    event_key: str,
    npc_id: int,
    actor_id: str,
    actor_role: str,
    event_type: str,
    title: str,
    public_text: str | None = None,
    private_text: str | None = None,
    relationship_id: int | None = None,
    memory_id: int | None = None,
    encounter_id: int | None = None,
    scene_id: int | None = None,
    contract_id: int | None = None,
    character_id: str | None = None,
    before: Any = None,
    after: Any = None,
    visibility: str = "gm",
) -> dict[str, Any]:
    existing = connection.execute("SELECT * FROM npc_events WHERE event_key=?", (event_key,)).fetchone()
    if existing:
        return _record(existing) or {}
    connection.execute(
        """
        INSERT INTO npc_events (
          event_key,npc_id,actor_id,actor_role,event_type,title,public_text,private_text,
          relationship_id,memory_id,encounter_id,scene_id,contract_id,character_id,
          before_json,after_json,visibility,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            event_key, npc_id, actor_id, actor_role, event_type, title, public_text,
            private_text, relationship_id, memory_id, encounter_id, scene_id,
            contract_id, character_id, _json(before), _json(after),
            _choice(visibility, VISIBILITIES, "visibilidade"), _now(),
        ),
    )
    return _record(connection.execute("SELECT * FROM npc_events WHERE event_key=?", (event_key,)).fetchone()) or {}


def init_npc_memory(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS npc_definitions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE NOT NULL,
              campaign_id TEXT NOT NULL,
              source_path TEXT UNIQUE,
              slug TEXT NOT NULL,
              name TEXT NOT NULL,
              aliases_json TEXT,
              portrait_path TEXT,
              race TEXT,
              class_or_role TEXT,
              occupation TEXT,
              faction_names_json TEXT,
              public_description TEXT,
              private_description TEXT,
              canonical_status TEXT,
              visible_to_players INTEGER NOT NULL DEFAULT 0,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              version INTEGER NOT NULL DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_npc_definition_campaign ON npc_definitions(campaign_id,name);

            CREATE TABLE IF NOT EXISTS npc_states (
              npc_id INTEGER PRIMARY KEY,
              current_location TEXT,
              public_status TEXT,
              private_status TEXT,
              disposition_summary TEXT,
              active INTEGER NOT NULL DEFAULT 1,
              last_seen_at TEXT,
              last_scene_id INTEGER,
              version INTEGER NOT NULL DEFAULT 1,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(npc_id) REFERENCES npc_definitions(id)
            );

            CREATE TABLE IF NOT EXISTS npc_relationships (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE NOT NULL,
              npc_id INTEGER NOT NULL,
              target_type TEXT NOT NULL,
              target_id TEXT,
              target_label TEXT NOT NULL,
              public_label TEXT,
              private_label TEXT,
              attitude_value INTEGER,
              trust_value INTEGER,
              fear_value INTEGER,
              respect_value INTEGER,
              status TEXT NOT NULL DEFAULT 'active',
              public_notes TEXT,
              private_notes TEXT,
              visible_to_players INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(npc_id) REFERENCES npc_definitions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_npc_relationship_target ON npc_relationships(npc_id,target_type,target_id);

            CREATE TABLE IF NOT EXISTS npc_memories (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE NOT NULL,
              npc_id INTEGER NOT NULL,
              memory_type TEXT NOT NULL,
              title TEXT NOT NULL,
              summary TEXT NOT NULL,
              private_details TEXT,
              subject_type TEXT,
              subject_id TEXT,
              subject_label TEXT,
              scene_id INTEGER,
              contract_id INTEGER,
              character_id TEXT,
              importance TEXT NOT NULL DEFAULT 'medium',
              confidence TEXT NOT NULL DEFAULT 'believed',
              visibility TEXT NOT NULL DEFAULT 'gm',
              status TEXT NOT NULL DEFAULT 'active',
              occurred_at TEXT,
              learned_at TEXT NOT NULL,
              forgotten_at TEXT,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              version INTEGER NOT NULL DEFAULT 1,
              contradicts_memory_id INTEGER,
              responsible_party TEXT,
              beneficiary TEXT,
              due_text TEXT,
              fulfilled_at TEXT,
              obligation_status TEXT,
              linked_contract_id INTEGER,
              linked_scene_id INTEGER,
              FOREIGN KEY(npc_id) REFERENCES npc_definitions(id),
              FOREIGN KEY(contradicts_memory_id) REFERENCES npc_memories(id)
            );
            CREATE INDEX IF NOT EXISTS idx_npc_memory_npc ON npc_memories(npc_id,status,importance);

            CREATE TABLE IF NOT EXISTS npc_encounters (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE NOT NULL,
              npc_id INTEGER NOT NULL,
              scene_id INTEGER NOT NULL,
              contract_id INTEGER,
              session_id INTEGER,
              title TEXT NOT NULL,
              public_summary TEXT,
              private_summary TEXT,
              occurred_at TEXT NOT NULL,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              unlinked_at TEXT,
              unlinked_by TEXT,
              unlink_reason TEXT,
              UNIQUE(npc_id,scene_id),
              FOREIGN KEY(npc_id) REFERENCES npc_definitions(id)
            );

            CREATE TABLE IF NOT EXISTS npc_contract_links (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE NOT NULL,
              npc_id INTEGER NOT NULL,
              contract_id INTEGER NOT NULL,
              role TEXT,
              visible_to_players INTEGER NOT NULL DEFAULT 0,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              unlinked_at TEXT,
              UNIQUE(npc_id,contract_id),
              FOREIGN KEY(npc_id) REFERENCES npc_definitions(id)
            );

            CREATE TABLE IF NOT EXISTS npc_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              event_key TEXT UNIQUE NOT NULL,
              npc_id INTEGER NOT NULL,
              actor_id TEXT NOT NULL,
              actor_role TEXT NOT NULL,
              event_type TEXT NOT NULL,
              title TEXT NOT NULL,
              public_text TEXT,
              private_text TEXT,
              relationship_id INTEGER,
              memory_id INTEGER,
              encounter_id INTEGER,
              scene_id INTEGER,
              contract_id INTEGER,
              character_id TEXT,
              before_json TEXT,
              after_json TEXT,
              visibility TEXT NOT NULL,
              created_at TEXT NOT NULL,
              voided_at TEXT,
              voided_by TEXT,
              void_reason TEXT,
              FOREIGN KEY(npc_id) REFERENCES npc_definitions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_npc_event_npc ON npc_events(npc_id,created_at DESC);
            """
        )


def create_npc(
    database_path: Path,
    *,
    request_id: str,
    campaign_id: str,
    actor_id: str,
    fields: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    with closing(_connect(database_path)) as connection, connection:
        existing = connection.execute("SELECT * FROM npc_definitions WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        source_path = _text(fields.get("source_path"), "fonte", maximum=500)
        if source_path:
            duplicate = connection.execute("SELECT * FROM npc_definitions WHERE source_path=?", (source_path,)).fetchone()
            if duplicate:
                return _record(duplicate) or {}, False
        name = _text(fields.get("name"), "nome", required=True, maximum=180) or "NPC"
        now = _now()
        connection.execute(
            """
            INSERT INTO npc_definitions (
              request_id,campaign_id,source_path,slug,name,aliases_json,portrait_path,race,
              class_or_role,occupation,faction_names_json,public_description,private_description,
              canonical_status,visible_to_players,created_by,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                request_id, campaign_id, source_path, _slug(fields.get("slug") or name), name,
                _json(list(fields.get("aliases") or [])), _text(fields.get("portrait_path"), "retrato", maximum=500),
                _text(fields.get("race"), "raça", maximum=120), _text(fields.get("class_or_role"), "função", maximum=180),
                _text(fields.get("occupation"), "ocupação", maximum=180), _json(list(fields.get("faction_names") or [])),
                _text(fields.get("public_description"), "descrição pública"), _text(fields.get("private_description"), "descrição privada"),
                _text(fields.get("canonical_status"), "estado canônico", maximum=120), 1 if fields.get("visible_to_players") else 0,
                actor_id, now, now,
            ),
        )
        npc_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
        connection.execute(
            "INSERT INTO npc_states (npc_id,current_location,public_status,private_status,disposition_summary,active,last_seen_at,last_scene_id,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                npc_id, _text(fields.get("current_location"), "localização", maximum=180),
                _text(fields.get("public_status"), "estado público", maximum=300),
                _text(fields.get("private_status"), "estado privado", maximum=500),
                _text(fields.get("disposition_summary"), "disposição", maximum=500),
                1 if fields.get("active", True) else 0, fields.get("last_seen_at"), fields.get("last_scene_id"), now,
            ),
        )
        npc = _fetch(connection, "npc_definitions", npc_id) or {}
        _event(connection, event_key=f"npc:create:{request_id}", npc_id=npc_id, actor_id=actor_id, actor_role="gm", event_type="npc_created", title="Perfil jogável criado", after=npc)
        return npc, True


def _filter_npc(npc: dict[str, Any], access_mode: str) -> dict[str, Any] | None:
    if access_mode == "gm":
        return npc
    if not npc.get("visible_to_players"):
        return None
    allowed = {"id", "campaign_id", "slug", "name", "aliases", "portrait_path", "race", "class_or_role", "occupation", "faction_names", "public_description", "canonical_status", "visible_to_players", "current_location", "public_status", "active", "last_seen_at", "last_scene_id", "state_version", "state_updated_at", "created_at", "updated_at", "version"}
    return {key: value for key, value in npc.items() if key in allowed}


def list_npcs(
    database_path: Path,
    *,
    campaign_id: str,
    access_mode: str,
    query: str | None = None,
    faction: str | None = None,
    location: str | None = None,
    role: str | None = None,
    status: str | None = None,
    character_id: str | None = None,
) -> list[dict[str, Any]]:
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(
            """SELECT d.*,s.current_location,s.public_status,s.private_status,s.disposition_summary,s.active,
                      s.last_seen_at,s.last_scene_id,s.version AS state_version,s.updated_at AS state_updated_at
               FROM npc_definitions d JOIN npc_states s ON s.npc_id=d.id
               WHERE d.campaign_id=? ORDER BY d.name COLLATE NOCASE""",
            (campaign_id,),
        ).fetchall()
        result: list[dict[str, Any]] = []
        needle = str(query or "").casefold().strip()
        for row in rows:
            npc = _record(row) or {}
            visible = _filter_npc(npc, access_mode)
            if visible is None:
                continue
            if access_mode != "gm":
                visible.pop("private_status", None)
                visible.pop("disposition_summary", None)
            haystack = " ".join([str(npc.get("name") or ""), " ".join(npc.get("aliases") or []), str(npc.get("class_or_role") or ""), str(npc.get("occupation") or "")]).casefold()
            if needle and needle not in haystack:
                continue
            if faction and faction.casefold() not in " ".join(npc.get("faction_names") or []).casefold():
                continue
            if location and location.casefold() not in str(npc.get("current_location") or "").casefold():
                continue
            if role and role.casefold() not in f"{npc.get('class_or_role') or ''} {npc.get('occupation') or ''}".casefold():
                continue
            if status and status.casefold() not in str(npc.get("public_status") or "").casefold():
                continue
            if character_id:
                relationship = connection.execute(
                    "SELECT 1 FROM npc_relationships WHERE npc_id=? AND target_type='character' AND target_id=? AND status='active'",
                    (npc["id"], character_id),
                ).fetchone()
                if not relationship:
                    continue
            result.append(visible)
        return result


def _visible_relationship(record: dict[str, Any], access_mode: str) -> dict[str, Any] | None:
    if access_mode == "gm":
        return record
    if not record.get("visible_to_players") or record.get("status") == "voided":
        return None
    allowed = {"id", "npc_id", "target_type", "target_id", "target_label", "public_label", "status", "public_notes", "visible_to_players", "created_at", "updated_at", "version"}
    return {key: value for key, value in record.items() if key in allowed}


def _visible_memory(record: dict[str, Any], access_mode: str) -> dict[str, Any] | None:
    if access_mode == "gm":
        return record
    if record.get("visibility") != "table" or record.get("status") == "voided":
        return None
    allowed = {
        "id", "npc_id", "memory_type", "title", "summary", "subject_type", "subject_id", "subject_label",
        "scene_id", "contract_id", "character_id", "importance", "visibility", "status", "occurred_at",
        "learned_at", "forgotten_at", "created_at", "updated_at", "version", "responsible_party", "beneficiary", "due_text",
        "fulfilled_at", "obligation_status", "linked_contract_id", "linked_scene_id",
    }
    return {key: value for key, value in record.items() if key in allowed}


def get_npc(database_path: Path, npc_id: int, *, access_mode: str) -> dict[str, Any] | None:
    with closing(_connect(database_path)) as connection:
        npc = _record(connection.execute(
            """SELECT d.*,s.current_location,s.public_status,s.private_status,s.disposition_summary,s.active,
                      s.last_seen_at,s.last_scene_id,s.version AS state_version,s.updated_at AS state_updated_at
               FROM npc_definitions d JOIN npc_states s ON s.npc_id=d.id WHERE d.id=?""",
            (npc_id,),
        ).fetchone())
        if npc is None:
            return None
        visible = _filter_npc(npc, access_mode)
        if visible is None:
            return None
        if access_mode != "gm":
            visible.pop("private_status", None)
            visible.pop("disposition_summary", None)
        visible["relationships"] = [item for row in connection.execute("SELECT * FROM npc_relationships WHERE npc_id=? ORDER BY updated_at DESC", (npc_id,)).fetchall() if (item := _visible_relationship(_record(row) or {}, access_mode))]
        visible["memories"] = [item for row in connection.execute("SELECT * FROM npc_memories WHERE npc_id=? ORDER BY CASE importance WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, learned_at DESC", (npc_id,)).fetchall() if (item := _visible_memory(_record(row) or {}, access_mode))]
        encounters = [_record(row) or {} for row in connection.execute("SELECT * FROM npc_encounters WHERE npc_id=? AND unlinked_at IS NULL ORDER BY occurred_at DESC", (npc_id,)).fetchall()]
        if access_mode != "gm":
            encounters = [{key: value for key, value in row.items() if key not in {"private_summary", "created_by", "unlinked_by", "unlink_reason"}} for row in encounters if row.get("public_summary")]
        visible["encounters"] = encounters
        links = [_record(row) or {} for row in connection.execute("SELECT * FROM npc_contract_links WHERE npc_id=? AND unlinked_at IS NULL ORDER BY created_at DESC", (npc_id,)).fetchall()]
        if access_mode != "gm":
            links = [row for row in links if row.get("visible_to_players")]
            links = [{key: value for key, value in row.items() if key not in {"created_by"}} for row in links]
        visible["contract_links"] = links
        visible["events"] = list_events(database_path, npc_id, access_mode=access_mode, limit=100)
        return visible


def update_npc(database_path: Path, npc_id: int, *, expected_version: int, fields: dict[str, Any], actor_id: str) -> dict[str, Any]:
    allowed = {"slug", "name", "aliases", "portrait_path", "race", "class_or_role", "occupation", "faction_names", "public_description", "private_description", "canonical_status", "visible_to_players"}
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Campos não editáveis: {', '.join(sorted(unknown))}")
    with closing(_connect(database_path)) as connection, connection:
        before = _npc_or_error(connection, npc_id)
        if int(before["version"]) != expected_version:
            raise RuntimeError("Versão desatualizada do NPC")
        columns: list[str] = []
        values: list[Any] = []
        for key, value in fields.items():
            column = {"aliases": "aliases_json", "faction_names": "faction_names_json"}.get(key, key)
            if key in {"aliases", "faction_names"}:
                value = _json(list(value or []))
            elif key == "visible_to_players":
                value = 1 if value else 0
            elif key == "slug":
                value = _slug(value)
            else:
                value = _text(value, key, required=key == "name", maximum=500 if key == "portrait_path" else MAX_TEXT)
            columns.append(f"{column}=?")
            values.append(value)
        columns.extend(["updated_at=?", "version=version+1"])
        values.extend([_now(), npc_id, expected_version])
        cursor = connection.execute(f"UPDATE npc_definitions SET {','.join(columns)} WHERE id=? AND version=?", values)
        if cursor.rowcount != 1:
            raise RuntimeError("Versão desatualizada do NPC")
        after = _fetch(connection, "npc_definitions", npc_id) or {}
        _event(connection, event_key=f"npc:update:{npc_id}:{after['version']}", npc_id=npc_id, actor_id=actor_id, actor_role="gm", event_type="npc_updated", title="Perfil do NPC atualizado", before=before, after=after)
        return after


def update_npc_state(database_path: Path, npc_id: int, *, expected_version: int, fields: dict[str, Any], actor_id: str) -> dict[str, Any]:
    allowed = {"current_location", "public_status", "private_status", "disposition_summary", "active", "last_seen_at", "last_scene_id"}
    if set(fields) - allowed:
        raise ValueError("Campo de estado não editável")
    with closing(_connect(database_path)) as connection, connection:
        _npc_or_error(connection, npc_id)
        before = _record(connection.execute("SELECT * FROM npc_states WHERE npc_id=?", (npc_id,)).fetchone()) or {}
        if int(before.get("version", 0)) != expected_version:
            raise RuntimeError("Versão desatualizada do estado do NPC")
        columns: list[str] = []
        values: list[Any] = []
        for key, value in fields.items():
            if key == "active":
                value = 1 if value else 0
            elif key == "last_scene_id":
                value = int(value) if value not in (None, "") else None
            else:
                value = _text(value, key, maximum=500)
            columns.append(f"{key}=?")
            values.append(value)
        columns.extend(["updated_at=?", "version=version+1"])
        values.extend([_now(), npc_id, expected_version])
        cursor = connection.execute(f"UPDATE npc_states SET {','.join(columns)} WHERE npc_id=? AND version=?", values)
        if cursor.rowcount != 1:
            raise RuntimeError("Versão desatualizada do estado do NPC")
        after = _record(connection.execute("SELECT * FROM npc_states WHERE npc_id=?", (npc_id,)).fetchone()) or {}
        _event(connection, event_key=f"npc:state:{npc_id}:{after['version']}", npc_id=npc_id, actor_id=actor_id, actor_role="gm", event_type="state_updated", title="Estado do NPC atualizado", public_text=after.get("public_status"), private_text=after.get("private_status"), scene_id=after.get("last_scene_id"), before=before, after=after)
        return after


def create_relationship(database_path: Path, npc_id: int, *, request_id: str, fields: dict[str, Any], actor_id: str, reason: str) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    reason = _text(reason, "motivo", required=True, maximum=500) or ""
    with closing(_connect(database_path)) as connection, connection:
        _npc_or_error(connection, npc_id)
        existing = connection.execute("SELECT * FROM npc_relationships WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        now = _now()
        values = (
            request_id, npc_id, _choice(fields.get("target_type"), TARGET_TYPES, "tipo de alvo"),
            _text(fields.get("target_id"), "id do alvo", maximum=180), _text(fields.get("target_label"), "alvo", required=True, maximum=180),
            _text(fields.get("public_label"), "relação pública", maximum=180), _text(fields.get("private_label"), "relação privada", maximum=180),
            _optional_score(fields.get("attitude_value"), "atitude"), _optional_score(fields.get("trust_value"), "confiança"),
            _optional_score(fields.get("fear_value"), "medo"), _optional_score(fields.get("respect_value"), "respeito"),
            _choice(fields.get("status", "active"), RELATIONSHIP_STATUSES, "estado"), _text(fields.get("public_notes"), "notas públicas"),
            _text(fields.get("private_notes"), "notas privadas"), 1 if fields.get("visible_to_players") else 0, now, now,
        )
        connection.execute("""INSERT INTO npc_relationships (request_id,npc_id,target_type,target_id,target_label,public_label,private_label,attitude_value,trust_value,fear_value,respect_value,status,public_notes,private_notes,visible_to_players,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", values)
        relationship_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
        relationship = _fetch(connection, "npc_relationships", relationship_id) or {}
        _event(connection, event_key=f"relationship:create:{request_id}", npc_id=npc_id, actor_id=actor_id, actor_role="gm", event_type="relationship_created", title=f"Relação com {relationship['target_label']} registrada", public_text=relationship.get("public_label"), private_text=reason, relationship_id=relationship_id, character_id=relationship.get("target_id") if relationship.get("target_type") == "character" else None, after=relationship, visibility="table" if relationship.get("visible_to_players") else "gm")
        return relationship, True


def update_relationship(database_path: Path, relationship_id: int, *, expected_version: int, fields: dict[str, Any], actor_id: str, reason: str) -> dict[str, Any]:
    allowed = {"public_label", "private_label", "attitude_value", "trust_value", "fear_value", "respect_value", "status", "public_notes", "private_notes", "visible_to_players"}
    if set(fields) - allowed:
        raise ValueError("Campo de relação não editável")
    reason = _text(reason, "motivo", required=True, maximum=500) or ""
    with closing(_connect(database_path)) as connection, connection:
        before = _fetch(connection, "npc_relationships", relationship_id)
        if before is None:
            raise ValueError("Relação inexistente")
        if int(before["version"]) != expected_version:
            raise RuntimeError("Versão desatualizada da relação")
        columns: list[str] = []
        values: list[Any] = []
        for key, value in fields.items():
            if key.endswith("_value"):
                value = _optional_score(value, key)
            elif key == "visible_to_players":
                value = 1 if value else 0
            elif key == "status":
                value = _choice(value, RELATIONSHIP_STATUSES, "estado")
            else:
                value = _text(value, key, maximum=MAX_TEXT)
            columns.append(f"{key}=?")
            values.append(value)
        columns.extend(["updated_at=?", "version=version+1"])
        values.extend([_now(), relationship_id, expected_version])
        cursor = connection.execute(f"UPDATE npc_relationships SET {','.join(columns)} WHERE id=? AND version=?", values)
        if cursor.rowcount != 1:
            raise RuntimeError("Versão desatualizada da relação")
        after = _fetch(connection, "npc_relationships", relationship_id) or {}
        _event(connection, event_key=f"relationship:update:{relationship_id}:{after['version']}", npc_id=int(after["npc_id"]), actor_id=actor_id, actor_role="gm", event_type="relationship_updated", title=f"Relação com {after['target_label']} alterada", public_text=after.get("public_label"), private_text=reason, relationship_id=relationship_id, character_id=after.get("target_id") if after.get("target_type") == "character" else None, before=before, after=after, visibility="table" if after.get("visible_to_players") else "gm")
        return after


def create_memory(database_path: Path, npc_id: int, *, request_id: str, fields: dict[str, Any], actor_id: str) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    memory_type = _choice(fields.get("memory_type"), MEMORY_TYPES, "tipo de memória")
    status = _choice(fields.get("status", "active"), MEMORY_STATUSES, "estado")
    obligation_status = fields.get("obligation_status")
    if memory_type in {"promise", "debt", "favor", "agreement"}:
        obligation_status = _choice(obligation_status or "active", OBLIGATION_STATUSES, "estado da obrigação")
    elif obligation_status:
        obligation_status = _choice(obligation_status, OBLIGATION_STATUSES, "estado da obrigação")
    with closing(_connect(database_path)) as connection, connection:
        _npc_or_error(connection, npc_id)
        existing = connection.execute("SELECT * FROM npc_memories WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        now = _now()
        connection.execute(
            """INSERT INTO npc_memories (request_id,npc_id,memory_type,title,summary,private_details,subject_type,subject_id,subject_label,scene_id,contract_id,character_id,importance,confidence,visibility,status,occurred_at,learned_at,forgotten_at,created_by,created_at,updated_at,contradicts_memory_id,responsible_party,beneficiary,due_text,fulfilled_at,obligation_status,linked_contract_id,linked_scene_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                request_id, npc_id, memory_type, _text(fields.get("title"), "título", required=True, maximum=180),
                _text(fields.get("summary"), "resumo", required=True), _text(fields.get("private_details"), "detalhes privados"),
                _text(fields.get("subject_type"), "tipo de assunto", maximum=80), _text(fields.get("subject_id"), "id do assunto", maximum=180),
                _text(fields.get("subject_label"), "assunto", maximum=180), fields.get("scene_id"), fields.get("contract_id"),
                _text(fields.get("character_id"), "personagem", maximum=180), _choice(fields.get("importance", "medium"), IMPORTANCE_LEVELS, "importância"),
                _choice(fields.get("confidence", "believed"), CONFIDENCE_LEVELS, "confiança"), _choice(fields.get("visibility", "gm"), VISIBILITIES, "visibilidade"),
                status, fields.get("occurred_at"), fields.get("learned_at") or now, fields.get("forgotten_at"), actor_id, now, now,
                fields.get("contradicts_memory_id"), _text(fields.get("responsible_party"), "responsável", maximum=180),
                _text(fields.get("beneficiary"), "beneficiário", maximum=180), _text(fields.get("due_text"), "prazo", maximum=300),
                fields.get("fulfilled_at"), obligation_status, fields.get("linked_contract_id") or fields.get("contract_id"), fields.get("linked_scene_id") or fields.get("scene_id"),
            ),
        )
        memory_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
        memory = _fetch(connection, "npc_memories", memory_id) or {}
        _event(connection, event_key=f"memory:create:{request_id}", npc_id=npc_id, actor_id=actor_id, actor_role="gm", event_type="memory_created", title=f"Memória registrada: {memory['title']}", public_text=memory.get("summary") if memory.get("visibility") == "table" else None, private_text=memory.get("private_details"), memory_id=memory_id, scene_id=memory.get("scene_id"), contract_id=memory.get("contract_id"), character_id=memory.get("character_id"), after=memory, visibility=memory.get("visibility") or "gm")
        return memory, True


def update_memory(database_path: Path, memory_id: int, *, expected_version: int, fields: dict[str, Any], actor_id: str, reason: str) -> dict[str, Any]:
    allowed = {"title", "summary", "private_details", "importance", "confidence", "visibility", "status", "forgotten_at", "responsible_party", "beneficiary", "due_text", "fulfilled_at", "obligation_status"}
    if set(fields) - allowed:
        raise ValueError("Campo de memória não editável")
    reason = _text(reason, "motivo", required=True, maximum=500) or ""
    with closing(_connect(database_path)) as connection, connection:
        before = _fetch(connection, "npc_memories", memory_id)
        if before is None:
            raise ValueError("Memória inexistente")
        if int(before["version"]) != expected_version:
            raise RuntimeError("Versão desatualizada da memória")
        columns: list[str] = []
        values: list[Any] = []
        for key, value in fields.items():
            if key == "importance": value = _choice(value, IMPORTANCE_LEVELS, "importância")
            elif key == "confidence": value = _choice(value, CONFIDENCE_LEVELS, "confiança")
            elif key == "visibility": value = _choice(value, VISIBILITIES, "visibilidade")
            elif key == "status": value = _choice(value, MEMORY_STATUSES, "estado")
            elif key == "obligation_status": value = _choice(value, OBLIGATION_STATUSES, "estado da obrigação")
            else: value = _text(value, key, required=key in {"title", "summary"})
            columns.append(f"{key}=?"); values.append(value)
        columns.extend(["updated_at=?", "version=version+1"]); values.extend([_now(), memory_id, expected_version])
        cursor = connection.execute(f"UPDATE npc_memories SET {','.join(columns)} WHERE id=? AND version=?", values)
        if cursor.rowcount != 1:
            raise RuntimeError("Versão desatualizada da memória")
        after = _fetch(connection, "npc_memories", memory_id) or {}
        _event(connection, event_key=f"memory:update:{memory_id}:{after['version']}", npc_id=int(after["npc_id"]), actor_id=actor_id, actor_role="gm", event_type="memory_updated", title=f"Memória atualizada: {after['title']}", public_text=after.get("summary") if after.get("visibility") == "table" else None, private_text=reason, memory_id=memory_id, scene_id=after.get("scene_id"), contract_id=after.get("contract_id"), character_id=after.get("character_id"), before=before, after=after, visibility=after.get("visibility") or "gm")
        return after


def contradict_memory(database_path: Path, memory_id: int, *, request_id: str, fields: dict[str, Any], actor_id: str, reason: str) -> dict[str, Any]:
    request_id = _request_id(request_id)
    with closing(_connect(database_path)) as connection, connection:
        previous = _fetch(connection, "npc_memories", memory_id)
        if previous is None:
            raise ValueError("Memória inexistente")
        if previous.get("status") == "contradicted":
            existing = connection.execute("SELECT * FROM npc_memories WHERE contradicts_memory_id=? ORDER BY id DESC LIMIT 1", (memory_id,)).fetchone()
            if existing:
                return _record(existing) or {}
        connection.execute("UPDATE npc_memories SET status='contradicted',updated_at=?,version=version+1 WHERE id=?", (_now(), memory_id))
    new_fields = dict(fields)
    new_fields["contradicts_memory_id"] = memory_id
    new_fields.setdefault("memory_type", previous["memory_type"])
    new_fields.setdefault("importance", previous["importance"])
    new_fields.setdefault("visibility", previous["visibility"])
    memory, _ = create_memory(database_path, int(previous["npc_id"]), request_id=request_id, fields=new_fields, actor_id=actor_id)
    with closing(_connect(database_path)) as connection, connection:
        _event(connection, event_key=f"memory:contradict:{request_id}", npc_id=int(previous["npc_id"]), actor_id=actor_id, actor_role="gm", event_type="memory_contradicted", title=f"Memória contradita: {previous['title']}", private_text=reason, memory_id=memory_id, before=previous, after=memory)
    return memory


def record_encounter(database_path: Path, npc_id: int, *, request_id: str, fields: dict[str, Any], actor_id: str) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    scene_id = int(fields.get("scene_id") or 0)
    if scene_id <= 0:
        raise ValueError("scene_id inválido")
    with closing(_connect(database_path)) as connection, connection:
        _npc_or_error(connection, npc_id)
        existing = connection.execute("SELECT * FROM npc_encounters WHERE request_id=? OR (npc_id=? AND scene_id=?)", (request_id, npc_id, scene_id)).fetchone()
        if existing:
            return _record(existing) or {}, False
        now = _now()
        connection.execute("""INSERT INTO npc_encounters (request_id,npc_id,scene_id,contract_id,session_id,title,public_summary,private_summary,occurred_at,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (request_id,npc_id,scene_id,fields.get("contract_id"),fields.get("session_id"),_text(fields.get("title"),"título",required=True,maximum=180),_text(fields.get("public_summary"),"resumo público"),_text(fields.get("private_summary"),"resumo privado"),fields.get("occurred_at") or now,actor_id,now))
        encounter_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
        encounter = _fetch(connection, "npc_encounters", encounter_id) or {}
        connection.execute("UPDATE npc_states SET last_seen_at=?,last_scene_id=?,updated_at=?,version=version+1 WHERE npc_id=?", (encounter["occurred_at"], scene_id, now, npc_id))
        _event(connection, event_key=f"encounter:create:{request_id}", npc_id=npc_id, actor_id=actor_id, actor_role="gm", event_type="encounter_recorded", title=encounter["title"], public_text=encounter.get("public_summary"), private_text=encounter.get("private_summary"), encounter_id=encounter_id, scene_id=scene_id, contract_id=encounter.get("contract_id"), after=encounter, visibility="table" if encounter.get("public_summary") else "gm")
        return encounter, True


def unlink_encounter(database_path: Path, encounter_id: int, *, actor_id: str, reason: str) -> dict[str, Any]:
    reason = _text(reason, "motivo", required=True, maximum=500) or ""
    with closing(_connect(database_path)) as connection, connection:
        encounter = _fetch(connection, "npc_encounters", encounter_id)
        if encounter is None:
            raise ValueError("Encontro inexistente")
        if not encounter.get("unlinked_at"):
            connection.execute("UPDATE npc_encounters SET unlinked_at=?,unlinked_by=?,unlink_reason=? WHERE id=?", (_now(), actor_id, reason, encounter_id))
        after = _fetch(connection, "npc_encounters", encounter_id) or {}
        _event(connection, event_key=f"encounter:unlink:{encounter_id}", npc_id=int(after["npc_id"]), actor_id=actor_id, actor_role="gm", event_type="encounter_unlinked", title="Vínculo de encontro removido", private_text=reason, encounter_id=encounter_id, scene_id=after.get("scene_id"), before=encounter, after=after)
        return after


def link_contract(database_path: Path, npc_id: int, *, request_id: str, contract_id: int, role: str | None, visible_to_players: bool, actor_id: str) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    with closing(_connect(database_path)) as connection, connection:
        _npc_or_error(connection, npc_id)
        existing = connection.execute("SELECT * FROM npc_contract_links WHERE request_id=? OR (npc_id=? AND contract_id=? AND unlinked_at IS NULL)", (request_id,npc_id,contract_id)).fetchone()
        if existing:
            return _record(existing) or {}, False
        connection.execute("INSERT INTO npc_contract_links (request_id,npc_id,contract_id,role,visible_to_players,created_by,created_at) VALUES (?,?,?,?,?,?,?)", (request_id,npc_id,contract_id,_text(role,"papel",maximum=180),1 if visible_to_players else 0,actor_id,_now()))
        link_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
        link = _fetch(connection, "npc_contract_links", link_id) or {}
        _event(connection, event_key=f"contract:link:{request_id}", npc_id=npc_id, actor_id=actor_id, actor_role="gm", event_type="contract_linked", title="NPC vinculado a contrato", public_text=link.get("role") if visible_to_players else None, contract_id=contract_id, after=link, visibility="table" if visible_to_players else "gm")
        return link, True


def list_contract_npcs(database_path: Path, contract_id: int, *, access_mode: str) -> list[dict[str, Any]]:
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("""SELECT l.*,d.name,d.portrait_path,d.class_or_role,d.occupation,d.visible_to_players AS npc_visible FROM npc_contract_links l JOIN npc_definitions d ON d.id=l.npc_id WHERE l.contract_id=? AND l.unlinked_at IS NULL ORDER BY d.name""", (contract_id,)).fetchall()
        result = []
        for row in rows:
            record = _record(row) or {}
            if access_mode != "gm" and (not record.get("visible_to_players") or not record.get("npc_visible")):
                continue
            if access_mode != "gm":
                record = {key: record.get(key) for key in ("id","npc_id","contract_id","role","visible_to_players","name","portrait_path","class_or_role","occupation","created_at")}
            result.append(record)
        return result


def list_events(database_path: Path, npc_id: int, *, access_mode: str, limit: int = 100) -> list[dict[str, Any]]:
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT * FROM npc_events WHERE npc_id=? ORDER BY created_at DESC LIMIT ?", (npc_id, max(1,min(limit,500)))).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            event = _record(row) or {}
            if access_mode != "gm":
                if event.get("visibility") != "table" or event.get("voided"):
                    continue
                event = {key: value for key, value in event.items() if key not in {"private_text","before","after","voided_by","void_reason","event_key"}}
            result.append(event)
        return result


def void_event(database_path: Path, event_id: int, *, actor_id: str, reason: str) -> dict[str, Any]:
    reason = _text(reason, "motivo", required=True, maximum=500) or ""
    with closing(_connect(database_path)) as connection, connection:
        event = _fetch(connection, "npc_events", event_id)
        if event is None:
            raise ValueError("Evento inexistente")
        if not event.get("voided_at"):
            connection.execute("UPDATE npc_events SET voided_at=?,voided_by=?,void_reason=? WHERE id=?", (_now(),actor_id,reason,event_id))
        return _fetch(connection, "npc_events", event_id) or {}


def structured_summary(database_path: Path, npc_id: int, *, access_mode: str, character_id: str | None = None) -> dict[str, Any] | None:
    npc = get_npc(database_path, npc_id, access_mode=access_mode)
    if npc is None:
        return None
    relationships = npc.get("relationships") or []
    if character_id:
        relationships = [item for item in relationships if item.get("target_type") != "character" or item.get("target_id") == character_id]
    memories = npc.get("memories") or []
    return {
        "npc": {key: npc.get(key) for key in ("id","name","aliases","race","class_or_role","occupation","faction_names","current_location","public_status")},
        "relationships": relationships[:20],
        "memories": memories[:20],
        "encounters": (npc.get("encounters") or [])[:10],
        "obligations": [item for item in memories if item.get("memory_type") in {"promise","debt","favor","agreement"}][:20],
        "access_profile": access_mode,
        "source": "structured_npc_memory",
        "canonical": False,
    }
