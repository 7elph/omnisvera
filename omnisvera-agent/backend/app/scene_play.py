from __future__ import annotations

import json
import hashlib
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .session_context import active_game_session_id


ActorRole = Literal["gm", "player"]
Visibility = Literal["table", "gm", "owner", "private"]
SESSION_STATUSES = {"planned", "active", "paused", "completed"}
SCENE_STATUSES = {"draft", "active", "paused", "resolved", "abandoned"}
PARTICIPANT_TYPES = {"player_character", "npc", "creature", "unknown"}
ELEMENT_TYPES = {"clue", "threat", "objective", "object", "exit", "environmental_effect"}
ACTION_TYPES = {"talk", "investigate", "observe", "move", "use_item", "interact", "attack", "other"}
ACTION_STATUSES = {"declared", "awaiting_roll", "resolved", "rejected", "cancelled"}
VISIBILITIES = {"table", "gm", "owner", "private"}
MAX_TEXT = 2000
SCENE_CHECKLIST_KEYS = {
    "identity", "map", "opening", "public_image", "characters", "npcs", "creatures",
    "scenery", "pins", "fog", "clues", "treasure", "interactive_items",
    "initial_states", "private_notes", "transitions", "player_preview",
}
PUBLICATION_TYPES = {"opening", "npc", "creature", "clue", "treasure", "state", "environment", "image", "other"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _text(value: Any, label: str, *, maximum: int = MAX_TEXT, required: bool = False) -> str | None:
    text = str(value or "").strip()
    if required and not text:
        raise ValueError(f"{label} é obrigatório")
    if len(text) > maximum:
        raise ValueError(f"{label} excede {maximum} caracteres")
    return text or None


def _request_id(value: str) -> str:
    request_id = str(value or "").strip()
    if not 8 <= len(request_id) <= 120 or not all(char.isalnum() or char in "._:-" for char in request_id):
        raise ValueError("request_id inválido")
    return request_id


def _visibility(value: str) -> str:
    if value not in VISIBILITIES:
        raise ValueError("Visibilidade inválida")
    return value


def _checklist(value: Any) -> dict[str, bool]:
    if value in (None, ""):
        return {}
    if not isinstance(value, dict):
        raise ValueError("Checklist da cena inválido")
    unknown = set(value) - SCENE_CHECKLIST_KEYS
    if unknown:
        raise ValueError("Item de checklist da cena inválido")
    return {key: bool(value.get(key)) for key in SCENE_CHECKLIST_KEYS if key in value}


def _camera_value(value: Any, label: str, *, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} inválido") from error
    return max(minimum, min(maximum, number))


def init_scene_play(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS game_sessions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT NOT NULL UNIQUE,
              campaign_id TEXT NOT NULL,
              title TEXT NOT NULL,
              session_number INTEGER,
              status TEXT NOT NULL DEFAULT 'planned',
              started_at TEXT,
              ended_at TEXT,
              created_by TEXT NOT NULL,
              private_notes TEXT,
              image_path TEXT,
              public_summary TEXT,
              public_chronicle TEXT,
              gm_summary TEXT,
              narrative_json TEXT NOT NULL DEFAULT '{}',
              gm_analysis_json TEXT NOT NULL DEFAULT '{}',
              source_refs_json TEXT NOT NULL DEFAULT '[]',
              created_at TEXT NOT NULL,
              version INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS scenes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT NOT NULL UNIQUE,
              campaign_id TEXT NOT NULL,
              session_id INTEGER,
              title TEXT NOT NULL,
              location_name TEXT NOT NULL,
              location_source TEXT,
              public_description TEXT,
              objective TEXT,
              private_notes TEXT,
              resolution_summary TEXT,
              status TEXT NOT NULL DEFAULT 'draft',
              visibility TEXT NOT NULL DEFAULT 'table',
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              activated_at TEXT,
              closed_at TEXT,
              order_index INTEGER NOT NULL DEFAULT 0,
              version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(session_id) REFERENCES game_sessions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_scenes_campaign_status ON scenes(campaign_id,status,id DESC);

            CREATE TABLE IF NOT EXISTS scene_participants (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              scene_id INTEGER NOT NULL,
              participant_type TEXT NOT NULL,
              character_id TEXT,
              npc_name TEXT,
              npc_source TEXT,
              public_label TEXT NOT NULL,
              public_status TEXT,
              private_status TEXT,
              visible_to_players INTEGER NOT NULL DEFAULT 1,
              order_index INTEGER NOT NULL DEFAULT 0,
              joined_at TEXT NOT NULL,
              left_at TEXT,
              UNIQUE(scene_id,character_id),
              FOREIGN KEY(scene_id) REFERENCES scenes(id)
            );

            CREATE TABLE IF NOT EXISTS scene_elements (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT NOT NULL UNIQUE,
              scene_id INTEGER NOT NULL,
              element_type TEXT NOT NULL,
              title TEXT NOT NULL,
              public_description TEXT,
              private_description TEXT,
              status TEXT NOT NULL,
              visibility TEXT NOT NULL,
              discovered_at TEXT,
              discovered_by TEXT,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(scene_id) REFERENCES scenes(id)
            );

            CREATE TABLE IF NOT EXISTS scene_actions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT NOT NULL UNIQUE,
              scene_id INTEGER NOT NULL,
              character_id TEXT,
              actor_id TEXT NOT NULL,
              actor_role TEXT NOT NULL,
              action_type TEXT NOT NULL,
              description TEXT NOT NULL,
              target_label TEXT,
              status TEXT NOT NULL DEFAULT 'declared',
              visibility TEXT NOT NULL DEFAULT 'table',
              requested_roll_id INTEGER,
              resulting_roll_id INTEGER,
              resolution TEXT,
              created_at TEXT NOT NULL,
              resolved_at TEXT,
              resolved_by TEXT,
              rejection_reason TEXT,
              FOREIGN KEY(scene_id) REFERENCES scenes(id)
            );
            CREATE INDEX IF NOT EXISTS idx_scene_actions_scene ON scene_actions(scene_id,id DESC);

            CREATE TABLE IF NOT EXISTS scene_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              event_key TEXT UNIQUE,
              scene_id INTEGER NOT NULL,
              session_id INTEGER,
              actor_id TEXT NOT NULL,
              actor_role TEXT NOT NULL,
              event_type TEXT NOT NULL,
              title TEXT NOT NULL,
              public_text TEXT,
              private_text TEXT,
              character_id TEXT,
              roll_id INTEGER,
              character_event_id INTEGER,
              action_id INTEGER,
              visibility TEXT NOT NULL DEFAULT 'table',
              created_at TEXT NOT NULL,
              voided_at TEXT,
              voided_by TEXT,
              void_reason TEXT,
              FOREIGN KEY(scene_id) REFERENCES scenes(id),
              FOREIGN KEY(session_id) REFERENCES game_sessions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_scene_events_scene ON scene_events(scene_id,id DESC);
            """
        )
        participant_columns = {row[1] for row in connection.execute("PRAGMA table_info(scene_participants)")}
        if "order_index" not in participant_columns:
            connection.execute("ALTER TABLE scene_participants ADD COLUMN order_index INTEGER NOT NULL DEFAULT 0")
            connection.execute("UPDATE scene_participants SET order_index=id WHERE order_index=0")
        scene_columns = {row[1] for row in connection.execute("PRAGMA table_info(scenes)")}
        if "image_path" not in scene_columns:
            connection.execute("ALTER TABLE scenes ADD COLUMN image_path TEXT")
        if "map_id" not in scene_columns:
            connection.execute("ALTER TABLE scenes ADD COLUMN map_id TEXT")
        if "checklist_json" not in scene_columns:
            connection.execute("ALTER TABLE scenes ADD COLUMN checklist_json TEXT NOT NULL DEFAULT '{}'")
        if "map_zoom" not in scene_columns:
            connection.execute("ALTER TABLE scenes ADD COLUMN map_zoom REAL NOT NULL DEFAULT 1")
        if "map_scroll_left" not in scene_columns:
            connection.execute("ALTER TABLE scenes ADD COLUMN map_scroll_left REAL NOT NULL DEFAULT 0")
        if "map_scroll_top" not in scene_columns:
            connection.execute("ALTER TABLE scenes ADD COLUMN map_scroll_top REAL NOT NULL DEFAULT 0")
        session_columns = {row[1] for row in connection.execute("PRAGMA table_info(game_sessions)")}
        if "image_path" not in session_columns:
            connection.execute("ALTER TABLE game_sessions ADD COLUMN image_path TEXT")
        if "public_summary" not in session_columns:
            connection.execute("ALTER TABLE game_sessions ADD COLUMN public_summary TEXT")
        if "public_chronicle" not in session_columns:
            connection.execute("ALTER TABLE game_sessions ADD COLUMN public_chronicle TEXT")
        if "gm_summary" not in session_columns:
            connection.execute("ALTER TABLE game_sessions ADD COLUMN gm_summary TEXT")
        if "narrative_json" not in session_columns:
            connection.execute("ALTER TABLE game_sessions ADD COLUMN narrative_json TEXT NOT NULL DEFAULT '{}'")
        if "gm_analysis_json" not in session_columns:
            connection.execute("ALTER TABLE game_sessions ADD COLUMN gm_analysis_json TEXT NOT NULL DEFAULT '{}'")
        if "source_refs_json" not in session_columns:
            connection.execute("ALTER TABLE game_sessions ADD COLUMN source_refs_json TEXT NOT NULL DEFAULT '[]'")
        duplicate_active = connection.execute(
            """
            SELECT COUNT(*) AS total FROM game_sessions
            WHERE status='active' HAVING COUNT(*)>1
            """
        ).fetchone()
        if duplicate_active:
            raise RuntimeError("Existem múltiplas sessões ativas")
        active_index = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND name='uq_game_sessions_one_active'"
        ).fetchone()
        if active_index is None or "ON game_sessions(status)" not in str(active_index["sql"] or ""):
            connection.execute("DROP INDEX IF EXISTS uq_game_sessions_one_active")
            connection.execute(
                """
                CREATE UNIQUE INDEX uq_game_sessions_one_active
                ON game_sessions(status) WHERE status='active'
                """
            )


def _record(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for key in ("visible_to_players",):
        if key in result:
            result[key] = bool(result[key])
    if "voided_at" in result:
        result["voided"] = bool(result["voided_at"])
    if "checklist_json" in result:
        try:
            decoded = json.loads(result.pop("checklist_json") or "{}")
        except json.JSONDecodeError:
            decoded = {}
        result["checklist"] = decoded if isinstance(decoded, dict) else {}
    for column, public_key, fallback in (
        ("narrative_json", "narrative", {}),
        ("gm_analysis_json", "gm_analysis", {}),
        ("source_refs_json", "source_refs", []),
    ):
        if column not in result:
            continue
        try:
            decoded = json.loads(result.pop(column) or json.dumps(fallback))
        except json.JSONDecodeError:
            decoded = fallback
        result[public_key] = decoded if isinstance(decoded, type(fallback)) else fallback
    return result


def _event(
    connection: sqlite3.Connection,
    *,
    scene: dict[str, Any],
    actor_id: str,
    actor_role: ActorRole,
    event_type: str,
    title: str,
    visibility: str = "table",
    public_text: str | None = None,
    private_text: str | None = None,
    character_id: str | None = None,
    roll_id: int | None = None,
    character_event_id: int | None = None,
    action_id: int | None = None,
    event_key: str | None = None,
) -> dict[str, Any]:
    visibility = _visibility(visibility)
    if event_key:
        existing = connection.execute("SELECT * FROM scene_events WHERE event_key=?", (event_key,)).fetchone()
        if existing:
            return _record(existing) or {}
    cursor = connection.execute(
        """
        INSERT INTO scene_events(event_key,scene_id,session_id,actor_id,actor_role,event_type,title,
          public_text,private_text,character_id,roll_id,character_event_id,action_id,visibility,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            event_key, scene["id"], scene.get("session_id"), actor_id, actor_role, event_type,
            _text(title, "Título", maximum=180, required=True), _text(public_text, "Texto público"),
            _text(private_text, "Texto privado"), character_id, roll_id, character_event_id, action_id,
            visibility, _now(),
        ),
    )
    return _record(connection.execute("SELECT * FROM scene_events WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}


def create_session(database_path: Path, *, request_id: str, campaign_id: str, title: str, created_by: str, session_number: int | None = None, private_notes: str | None = None) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    title = _text(title, "Título", maximum=180, required=True) or "Sessão"
    if session_number is not None and not 1 <= int(session_number) <= 10000:
        raise ValueError("Número de sessão inválido")
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM game_sessions WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        cursor = connection.execute(
            "INSERT INTO game_sessions(request_id,campaign_id,title,session_number,status,created_by,private_notes,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (request_id, campaign_id, title, session_number, "planned", created_by, _text(private_notes, "Notas privadas"), _now()),
        )
        row = connection.execute("SELECT * FROM game_sessions WHERE id=?", (cursor.lastrowid,)).fetchone()
    return _record(row) or {}, True


def list_sessions(database_path: Path, campaign_id: str = "omnisvera") -> list[dict[str, Any]]:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT * FROM game_sessions WHERE campaign_id=? ORDER BY id DESC", (campaign_id,)).fetchall()
    return [_record(row) or {} for row in rows]


def historical_sessions_manifest_path() -> Path:
    return Path(__file__).resolve().parents[3] / ".assistant-runtime" / "campaign-sources" / "session-records.json"


def _verified_source_refs(manifest_path: Path, refs: Any) -> list[dict[str, Any]]:
    if not isinstance(refs, list):
        raise ValueError("Proveniência histórica inválida")
    workspace_root = manifest_path.parents[2]
    verified: list[dict[str, Any]] = []
    for raw in refs:
        if not isinstance(raw, dict):
            raise ValueError("Fonte histórica inválida")
        relative = str(raw.get("path") or "").strip().replace("\\", "/")
        expected_hash = str(raw.get("sha256") or "").strip().upper()
        if not relative or relative.startswith("/") or ".." in Path(relative).parts:
            raise ValueError("Caminho de fonte histórica inválido")
        source_path = (workspace_root / relative).resolve()
        try:
            source_path.relative_to(workspace_root.resolve())
        except ValueError as error:
            raise ValueError("Fonte histórica fora do workspace") from error
        if not source_path.is_file():
            raise ValueError(f"Fonte histórica ausente: {relative}")
        actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest().upper()
        if actual_hash != expected_hash:
            raise ValueError(f"Hash divergente para a fonte histórica: {relative}")
        verified.append({
            "path": relative,
            "sha256": actual_hash,
            "evidence": [str(item) for item in raw.get("evidence", []) if str(item).strip()],
        })
    return verified


def sync_historical_sessions(database_path: Path, manifest_path: Path | None = None) -> dict[str, int]:
    """Create missing historical records without overwriting later GM curation.

    The manifest is provenance for an initial import. Transcript hashes are
    still verified on every run, while stable request IDs make later runs
    create-only and idempotent.
    """
    manifest_path = manifest_path or historical_sessions_manifest_path()
    if not manifest_path.is_file():
        return {"created": 0, "updated": 0, "unchanged": 0}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Manifesto histórico inválido") from error
    records = payload.get("sessions") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        raise ValueError("Manifesto histórico sem sessões")
    campaign_id = _text(payload.get("campaign_id"), "Campanha", maximum=120, required=True) or "omnisvera"
    source_status = str(payload.get("source_status") or "historical_evidence")
    counters = {"created": 0, "updated": 0, "unchanged": 0}
    init_scene_play(database_path)
    narrative_keys = (
        "participants", "locations", "missions", "discoveries", "rewards",
        "items_acquired", "world_events", "character_events", "open_threads", "tags",
    )
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        for raw in records:
            if not isinstance(raw, dict):
                raise ValueError("Registro histórico inválido")
            request_id = _request_id(str(raw.get("request_id") or ""))
            title = _text(raw.get("title"), "Título", maximum=180, required=True) or "Sessão"
            session_number = int(raw.get("session_number") or 0)
            if not 1 <= session_number <= 10000:
                raise ValueError("Número de sessão histórica inválido")
            status = str(raw.get("status") or "completed")
            if status not in SESSION_STATUSES:
                raise ValueError("Status de sessão histórica inválido")
            narrative = {key: raw.get(key, []) for key in narrative_keys}
            narrative_json = json.dumps(narrative, ensure_ascii=False, sort_keys=True)
            gm_analysis_json = json.dumps({
                "source_status": source_status,
                "companion_feedback": raw.get("companion_feedback", []),
            }, ensure_ascii=False, sort_keys=True)
            source_refs_json = json.dumps(
                _verified_source_refs(manifest_path, raw.get("source_refs", [])),
                ensure_ascii=False,
                sort_keys=True,
            )
            values = (
                campaign_id,
                title,
                session_number,
                status,
                _text(raw.get("image_path"), "Imagem", maximum=500),
                _text(raw.get("public_summary"), "Resumo público", maximum=4000),
                _text(raw.get("public_chronicle"), "Crônica pública", maximum=12000),
                _text(raw.get("gm_summary"), "Resumo do Mestre", maximum=4000),
                narrative_json,
                gm_analysis_json,
                source_refs_json,
            )
            existing = connection.execute("SELECT * FROM game_sessions WHERE request_id=?", (request_id,)).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO game_sessions(
                      request_id,campaign_id,title,session_number,status,started_at,ended_at,created_by,
                      private_notes,image_path,public_summary,public_chronicle,gm_summary,narrative_json,
                      gm_analysis_json,source_refs_json,created_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        request_id, *values[:4], None, None, "historical-import", None,
                        *values[4:], _now(),
                    ),
                )
                counters["created"] += 1
                continue
            counters["unchanged"] += 1
    return counters


def list_visible_sessions(
    database_path: Path,
    *,
    campaign_id: str = "omnisvera",
    access_mode: str,
) -> list[dict[str, Any]]:
    """Return session chronology without leaking the GM planning surface.

    Sessions are the temporal spine of the campaign.  Players may read only
    sessions which have actually started, and never receive the private notes
    or authorship metadata used by the GM preparation view.
    """
    sessions = list_sessions(database_path, campaign_id)
    if access_mode == "gm":
        return sessions
    visible: list[dict[str, Any]] = []
    for session in sessions:
        if session.get("status") not in {"active", "completed"}:
            continue
        public = dict(session)
        public.pop("private_notes", None)
        public.pop("created_by", None)
        public.pop("gm_summary", None)
        public.pop("gm_analysis", None)
        public.pop("source_refs", None)
        visible.append(public)
    return visible


def get_visible_session(database_path: Path, session_id: int, *, access_mode: str) -> dict[str, Any]:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection:
        row = connection.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
    session = _record(row)
    if not session or (access_mode != "gm" and session.get("status") not in {"active", "completed"}):
        raise ValueError("Sessão não encontrada")
    if access_mode == "gm":
        return session
    for key in ("private_notes", "created_by", "gm_summary", "gm_analysis", "source_refs"):
        session.pop(key, None)
    return session


def change_session_status(database_path: Path, session_id: int, status: str) -> dict[str, Any]:
    if status not in SESSION_STATUSES:
        raise ValueError("Status de sessão inválido")
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            raise ValueError("Sessão não encontrada")
        if status == "active":
            other = connection.execute(
                "SELECT id,title FROM game_sessions WHERE status='active' AND id<>? LIMIT 1",
                (session_id,),
            ).fetchone()
            if other:
                raise ValueError(
                    f"A sessão {other['id']} ({other['title']}) já está ativa; encerre ou pause-a primeiro"
                )
        now = _now()
        connection.execute(
            "UPDATE game_sessions SET status=?,started_at=CASE WHEN ?='active' AND started_at IS NULL THEN ? ELSE started_at END,ended_at=CASE WHEN ?='completed' THEN ? ELSE ended_at END,version=version+1 WHERE id=?",
            (status, status, now, status, now, session_id),
        )
        if status in {"paused", "completed"}:
            active_scenes = connection.execute(
                "SELECT * FROM scenes WHERE session_id=? AND status='active' ORDER BY id",
                (session_id,),
            ).fetchall()
            for scene_row in active_scenes:
                scene = _record(scene_row) or {}
                connection.execute(
                    "UPDATE scenes SET status='paused',version=version+1 WHERE id=?",
                    (scene["id"],),
                )
                _event(
                    connection,
                    scene=scene,
                    actor_id="master",
                    actor_role="gm",
                    event_type="scene_paused",
                    title="Cena pausada com a sessão",
                    visibility="table",
                    event_key=f"session-pause:{session_id}:{scene['id']}:{status}",
                )
        updated = connection.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
    return _record(updated) or {}


def update_session_metadata(database_path: Path, session_id: int, fields: dict[str, Any]) -> dict[str, Any]:
    """Update only the GM-curated presentation metadata of an existing session."""
    allowed = {"played_on", "image_path"}
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Campos inválidos: {', '.join(sorted(unknown))}")
    init_scene_play(database_path)
    updates: dict[str, Any] = {}
    if "played_on" in fields:
        played_on = fields.get("played_on")
        normalized = played_on.isoformat() if hasattr(played_on, "isoformat") else str(played_on or "").strip() or None
        updates["started_at"] = normalized
        updates["ended_at"] = normalized
    if "image_path" in fields:
        updates["image_path"] = _text(fields.get("image_path"), "Imagem", maximum=500)
    with closing(_connect(database_path)) as connection, connection:
        existing = connection.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
        if not existing:
            raise ValueError("Sessão não encontrada")
        if updates:
            clause = ", ".join(f"{key}=?" for key in updates)
            connection.execute(
                f"UPDATE game_sessions SET {clause}, version=version+1 WHERE id=?",
                (*updates.values(), session_id),
            )
        updated = connection.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
    return _record(updated) or {}


def create_scene(
    database_path: Path,
    *,
    request_id: str,
    campaign_id: str,
    title: str,
    location_name: str,
    created_by: str,
    session_id: int | None = None,
    location_source: str | None = None,
    public_description: str | None = None,
    objective: str | None = None,
    private_notes: str | None = None,
    image_path: str | None = None,
    map_id: str | None = None,
    checklist: dict[str, Any] | None = None,
    map_zoom: float = 1,
    map_scroll_left: float = 0,
    map_scroll_top: float = 0,
    visibility: str = "table",
) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    visibility = _visibility(visibility)
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM scenes WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        if session_id is None:
            session_id = active_game_session_id(connection, campaign_id)
        if session_id is not None and not connection.execute("SELECT 1 FROM game_sessions WHERE id=?", (session_id,)).fetchone():
            raise ValueError("Sessão não encontrada")
        order_index = connection.execute("SELECT COALESCE(MAX(order_index),0)+1 FROM scenes WHERE campaign_id=?", (campaign_id,)).fetchone()[0]
        cursor = connection.execute(
            """
            INSERT INTO scenes(request_id,campaign_id,session_id,title,location_name,location_source,
              public_description,objective,private_notes,image_path,map_id,checklist_json,map_zoom,map_scroll_left,map_scroll_top,
              status,visibility,created_by,created_at,order_index)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'draft',?,?,?,?)
            """,
            (
                request_id, campaign_id, session_id, _text(title, "Título", maximum=180, required=True),
                _text(location_name, "Local", maximum=180, required=True), _text(location_source, "Fonte do local", maximum=500),
                _text(public_description, "Descrição pública"), _text(objective, "Objetivo", maximum=500),
                _text(private_notes, "Notas privadas"), _text(image_path, "Imagem", maximum=1000),
                _text(map_id, "Mapa", maximum=180), json.dumps(_checklist(checklist), ensure_ascii=False),
                _camera_value(map_zoom, "Zoom", minimum=1, maximum=3),
                _camera_value(map_scroll_left, "Posição horizontal", minimum=0, maximum=1),
                _camera_value(map_scroll_top, "Posição vertical", minimum=0, maximum=1),
                visibility, created_by, _now(), order_index,
            ),
        )
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}
        _event(connection, scene=scene, actor_id=created_by, actor_role="gm", event_type="scene_created", title="Cena criada", visibility="gm", private_text=scene["title"], event_key=f"scene-created:{scene['id']}")
    return scene, True


def get_scene(database_path: Path, scene_id: int) -> dict[str, Any] | None:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection:
        return _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())


def list_scenes(database_path: Path, campaign_id: str = "omnisvera") -> list[dict[str, Any]]:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT * FROM scenes WHERE campaign_id=? ORDER BY order_index DESC,id DESC", (campaign_id,)).fetchall()
    return [_record(row) or {} for row in rows]


def active_scene(database_path: Path, campaign_id: str = "omnisvera") -> dict[str, Any] | None:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection:
        return _record(connection.execute("SELECT * FROM scenes WHERE campaign_id=? AND status='active' ORDER BY id DESC LIMIT 1", (campaign_id,)).fetchone())


def update_scene(database_path: Path, scene_id: int, *, expected_version: int, fields: dict[str, Any], actor_id: str = "master") -> dict[str, Any]:
    allowed = {"title", "location_name", "location_source", "public_description", "objective", "private_notes", "image_path", "map_id", "checklist", "map_zoom", "map_scroll_left", "map_scroll_top", "visibility", "order_index"}
    if set(fields) - allowed:
        raise ValueError("Campo de cena inválido")
    if "visibility" in fields:
        fields["visibility"] = _visibility(str(fields["visibility"]))
    for key in ("title", "location_name"):
        if key in fields:
            fields[key] = _text(fields[key], key, maximum=180, required=True)
    for key in ("location_source", "public_description", "objective", "private_notes", "image_path", "map_id"):
        if key in fields:
            fields[key] = _text(fields[key], key, maximum=1000 if key == "image_path" else 500 if key in {"location_source", "objective"} else 180 if key == "map_id" else MAX_TEXT)
    if "checklist" in fields:
        fields["checklist_json"] = json.dumps(_checklist(fields.pop("checklist")), ensure_ascii=False)
    if "map_zoom" in fields:
        fields["map_zoom"] = _camera_value(fields["map_zoom"], "Zoom", minimum=1, maximum=3)
    for key, label in (("map_scroll_left", "Posição horizontal"), ("map_scroll_top", "Posição vertical")):
        if key in fields:
            fields[key] = _camera_value(fields[key], label, minimum=0, maximum=1)
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())
        if not scene:
            raise ValueError("Cena não encontrada")
        if scene["version"] != expected_version:
            raise RuntimeError("A cena foi atualizada em outro dispositivo")
        if scene["status"] in {"resolved", "abandoned"}:
            raise ValueError("Cena encerrada não pode ser editada")
        if fields:
            assignments = ",".join(f"{key}=?" for key in fields)
            connection.execute(f"UPDATE scenes SET {assignments},version=version+1 WHERE id=?", [*fields.values(), scene_id])
        updated = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone()) or {}
        _event(connection, scene=updated, actor_id=actor_id, actor_role="gm", event_type="scene_updated", title="Cena atualizada", visibility="gm")
    return updated


def change_scene_status(database_path: Path, scene_id: int, status: str, *, actor_id: str = "master", summary: str | None = None) -> dict[str, Any]:
    if status not in SCENE_STATUSES - {"draft"}:
        raise ValueError("Status de cena inválido")
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())
        if not scene:
            raise ValueError("Cena não encontrada")
        now = _now()
        if status == "active":
            current_session_id = active_game_session_id(connection, scene["campaign_id"])
            if current_session_id is None:
                raise ValueError("Inicie uma sessão antes de abrir uma cena na Mesa")
            if scene.get("session_id") is None and current_session_id is not None:
                connection.execute(
                    "UPDATE scenes SET session_id=? WHERE id=?",
                    (current_session_id, scene_id),
                )
                scene["session_id"] = current_session_id
            elif (
                current_session_id is not None
                and scene.get("session_id") is not None
                and int(scene["session_id"]) != current_session_id
            ):
                raise ValueError("A cena pertence a outra sessão operacional")
            others = connection.execute("SELECT * FROM scenes WHERE campaign_id=? AND status='active' AND id<>?", (scene["campaign_id"], scene_id)).fetchall()
            for other_row in others:
                other = _record(other_row) or {}
                connection.execute("UPDATE scenes SET status='paused',version=version+1 WHERE id=?", (other["id"],))
                _event(connection, scene=other, actor_id=actor_id, actor_role="gm", event_type="scene_paused", title="Cena pausada por ativação de outra cena", visibility="table", event_key=f"auto-pause:{other['id']}:{scene_id}")
        closed_at = now if status in {"resolved", "abandoned"} else None
        connection.execute(
            "UPDATE scenes SET status=?,activated_at=CASE WHEN ?='active' AND activated_at IS NULL THEN ? ELSE activated_at END,closed_at=COALESCE(?,closed_at),resolution_summary=COALESCE(?,resolution_summary),version=version+1 WHERE id=?",
            (status, status, now, closed_at, _text(summary, "Resumo"), scene_id),
        )
        updated = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone()) or {}
        event_name = {"active": "scene_activated", "paused": "scene_paused", "resolved": "scene_resolved", "abandoned": "scene_abandoned"}[status]
        title = {"active": "Cena iniciada", "paused": "Cena pausada", "resolved": "Cena encerrada", "abandoned": "Cena abandonada"}[status]
        _event(connection, scene=updated, actor_id=actor_id, actor_role="gm", event_type=event_name, title=title, public_text=summary, visibility="table", event_key=f"scene-status:{scene_id}:{status}:{updated['version']}")
    return updated


def add_participant(database_path: Path, scene_id: int, *, participant_type: str, public_label: str, character_id: str | None = None, npc_name: str | None = None, npc_source: str | None = None, public_status: str | None = None, private_status: str | None = None, visible_to_players: bool = True, actor_id: str = "master") -> dict[str, Any]:
    if participant_type not in PARTICIPANT_TYPES:
        raise ValueError("Tipo de participante inválido")
    if participant_type == "player_character" and not character_id:
        raise ValueError("Personagem não informado")
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())
        if not scene:
            raise ValueError("Cena não encontrada")
        if scene["status"] in {"resolved", "abandoned"}:
            raise ValueError("Cena encerrada")
        if character_id:
            existing = connection.execute("SELECT * FROM scene_participants WHERE scene_id=? AND character_id=?", (scene_id, character_id)).fetchone()
            if existing:
                return _record(existing) or {}
        next_order = int(connection.execute("SELECT COALESCE(MAX(order_index),0)+1 FROM scene_participants WHERE scene_id=?", (scene_id,)).fetchone()[0])
        cursor = connection.execute(
            """
            INSERT INTO scene_participants(scene_id,participant_type,character_id,npc_name,npc_source,public_label,
              public_status,private_status,visible_to_players,order_index,joined_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                scene_id, participant_type, character_id, _text(npc_name, "NPC", maximum=180),
                _text(npc_source, "Fonte", maximum=500), _text(public_label, "Nome público", maximum=180, required=True),
                _text(public_status, "Estado público", maximum=180), _text(private_status, "Estado privado", maximum=500),
                int(visible_to_players), next_order, _now(),
            ),
        )
        participant = _record(connection.execute("SELECT * FROM scene_participants WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}
        _event(connection, scene=scene, actor_id=actor_id, actor_role="gm", event_type="participant_joined", title=f"{participant['public_label']} entrou na cena", character_id=character_id, visibility="table" if visible_to_players else "gm")
    return participant


def update_participant(database_path: Path, participant_id: int, fields: dict[str, Any], *, actor_id: str = "master") -> dict[str, Any]:
    allowed = {"public_label", "public_status", "private_status", "visible_to_players", "left_at", "order_index"}
    if set(fields) - allowed:
        raise ValueError("Campo de participante inválido")
    for key in ("public_label", "public_status", "private_status"):
        if key in fields:
            fields[key] = _text(fields[key], key, maximum=500, required=key == "public_label")
    if "visible_to_players" in fields:
        fields["visible_to_players"] = int(bool(fields["visible_to_players"]))
    if "order_index" in fields:
        fields["order_index"] = max(0, int(fields["order_index"]))
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT * FROM scene_participants WHERE id=?", (participant_id,)).fetchone()
        if not row:
            raise ValueError("Participante não encontrado")
        if fields:
            assignments = ",".join(f"{key}=?" for key in fields)
            connection.execute(f"UPDATE scene_participants SET {assignments} WHERE id=?", [*fields.values(), participant_id])
        updated = _record(connection.execute("SELECT * FROM scene_participants WHERE id=?", (participant_id,)).fetchone()) or {}
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (updated["scene_id"],)).fetchone()) or {}
        _event(connection, scene=scene, actor_id=actor_id, actor_role="gm", event_type="participant_updated", title=f"Estado de {updated['public_label']} atualizado", character_id=updated.get("character_id"), visibility="table" if updated.get("visible_to_players") else "gm")
    return updated


def create_element(database_path: Path, scene_id: int, *, request_id: str, element_type: str, title: str, status: str, visibility: str, created_by: str, public_description: str | None = None, private_description: str | None = None) -> tuple[dict[str, Any], bool]:
    if element_type not in ELEMENT_TYPES:
        raise ValueError("Tipo de elemento inválido")
    request_id = _request_id(request_id)
    visibility = _visibility(visibility)
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM scene_elements WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())
        if not scene:
            raise ValueError("Cena não encontrada")
        cursor = connection.execute(
            """
            INSERT INTO scene_elements(request_id,scene_id,element_type,title,public_description,private_description,status,visibility,created_by,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (request_id, scene_id, element_type, _text(title, "Título", maximum=180, required=True), _text(public_description, "Descrição pública"), _text(private_description, "Descrição privada"), _text(status, "Status", maximum=40, required=True), visibility, created_by, _now()),
        )
        element = _record(connection.execute("SELECT * FROM scene_elements WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}
        _event(connection, scene=scene, actor_id=created_by, actor_role="gm", event_type="element_created", title=f"Elemento criado: {element['title']}", visibility="gm", event_key=f"element-created:{element['id']}")
    return element, True


def update_element(database_path: Path, element_id: int, *, fields: dict[str, Any], actor_id: str = "master", reveal: bool = False) -> dict[str, Any]:
    allowed = {"title", "public_description", "private_description", "status", "visibility"}
    if set(fields) - allowed:
        raise ValueError("Campo de elemento inválido")
    if "visibility" in fields:
        fields["visibility"] = _visibility(str(fields["visibility"]))
    for key in ("title", "public_description", "private_description", "status"):
        if key in fields:
            fields[key] = _text(fields[key], key, maximum=180 if key in {"title", "status"} else MAX_TEXT, required=key in {"title", "status"})
    if reveal:
        fields["visibility"] = "table"
        fields.setdefault("status", "revealed")
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT * FROM scene_elements WHERE id=?", (element_id,)).fetchone()
        if not row:
            raise ValueError("Elemento não encontrado")
        original = _record(row) or {}
        extra = ",discovered_at=?,discovered_by=?" if reveal else ""
        assignments = ",".join(f"{key}=?" for key in fields)
        params = [*fields.values()]
        if reveal:
            params.extend([_now(), actor_id])
        params.append(element_id)
        connection.execute(f"UPDATE scene_elements SET {assignments}{extra},version=version+1 WHERE id=?", params)
        updated = _record(connection.execute("SELECT * FROM scene_elements WHERE id=?", (element_id,)).fetchone()) or {}
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (updated["scene_id"],)).fetchone()) or {}
        _event(connection, scene=scene, actor_id=actor_id, actor_role="gm", event_type="element_revealed" if reveal else "element_updated", title=f"{'Pista revelada' if reveal else 'Elemento atualizado'}: {updated['title']}", public_text=updated.get("public_description") if reveal else None, private_text=original.get("private_description"), visibility="table" if reveal else "gm", event_key=f"element-reveal:{element_id}" if reveal else None)
    return updated


def declare_action(database_path: Path, scene_id: int, *, request_id: str, character_id: str | None, actor_id: str, actor_role: ActorRole, action_type: str, description: str, target_label: str | None = None, visibility: str = "table") -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    if action_type not in ACTION_TYPES:
        raise ValueError("Tipo de ação inválido")
    visibility = _visibility(visibility)
    if actor_role != "gm" and visibility == "gm":
        raise PermissionError("Jogadores não podem declarar ações exclusivas do Mestre")
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM scene_actions WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            record = _record(existing) or {}
            if record["actor_id"] != actor_id:
                raise ValueError("request_id já utilizado")
            return record, False
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())
        if not scene:
            raise ValueError("Cena não encontrada")
        if scene["status"] != "active":
            raise ValueError("A cena não está ativa")
        if actor_role != "gm":
            if actor_id != character_id:
                raise PermissionError("Você só pode agir por seu próprio personagem")
            participant = connection.execute("SELECT 1 FROM scene_participants WHERE scene_id=? AND character_id=? AND left_at IS NULL", (scene_id, character_id)).fetchone()
            if not participant:
                raise PermissionError("Seu personagem não participa desta cena")
        cursor = connection.execute(
            """
            INSERT INTO scene_actions(request_id,scene_id,character_id,actor_id,actor_role,action_type,description,target_label,status,visibility,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (request_id, scene_id, character_id, actor_id, actor_role, action_type, _text(description, "Descrição", maximum=600, required=True), _text(target_label, "Alvo", maximum=180), "declared", visibility, _now()),
        )
        action = _record(connection.execute("SELECT * FROM scene_actions WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}
        _event(connection, scene=scene, actor_id=actor_id, actor_role=actor_role, event_type="action_declared", title="Ação declarada", public_text=action["description"], character_id=character_id, action_id=action["id"], visibility=visibility, event_key=f"action-declared:{action['id']}")
    return action, True


def resolve_action(database_path: Path, action_id: int, *, actor_id: str, resolution: str | None = None, reject: bool = False) -> dict[str, Any]:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        action = _record(connection.execute("SELECT * FROM scene_actions WHERE id=?", (action_id,)).fetchone())
        if not action:
            raise ValueError("Ação não encontrada")
        if action["status"] in {"resolved", "rejected", "cancelled"}:
            raise ValueError("Ação já finalizada")
        status = "rejected" if reject else "resolved"
        text = _text(resolution, "Resolução", maximum=1200, required=reject)
        connection.execute(
            "UPDATE scene_actions SET status=?,resolution=?,rejection_reason=?,resolved_at=?,resolved_by=? WHERE id=?",
            (status, None if reject else text, text if reject else None, _now(), actor_id, action_id),
        )
        updated = _record(connection.execute("SELECT * FROM scene_actions WHERE id=?", (action_id,)).fetchone()) or {}
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (updated["scene_id"],)).fetchone()) or {}
        _event(connection, scene=scene, actor_id=actor_id, actor_role="gm", event_type=f"action_{status}", title="Ação rejeitada" if reject else "Ação resolvida", public_text=text, character_id=updated.get("character_id"), action_id=action_id, visibility=updated["visibility"], event_key=f"action-{status}:{action_id}")
    return updated


def get_action(database_path: Path, action_id: int) -> dict[str, Any] | None:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection:
        return _record(connection.execute("SELECT * FROM scene_actions WHERE id=?", (action_id,)).fetchone())


def cancel_action(database_path: Path, action_id: int, *, actor_id: str, actor_role: ActorRole) -> dict[str, Any]:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        action = _record(connection.execute("SELECT * FROM scene_actions WHERE id=?", (action_id,)).fetchone())
        if not action:
            raise ValueError("Ação não encontrada")
        if action["status"] != "declared":
            raise ValueError("Ação não pode mais ser cancelada")
        if actor_role != "gm" and action["actor_id"] != actor_id:
            raise PermissionError("Você não pode cancelar esta ação")
        connection.execute("UPDATE scene_actions SET status='cancelled',resolved_at=?,resolved_by=? WHERE id=?", (_now(), actor_id, action_id))
        return _record(connection.execute("SELECT * FROM scene_actions WHERE id=?", (action_id,)).fetchone()) or {}


def link_roll_request(database_path: Path, action_id: int, roll_request_id: int, *, actor_id: str = "master") -> dict[str, Any]:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        action = _record(connection.execute("SELECT * FROM scene_actions WHERE id=?", (action_id,)).fetchone())
        if not action:
            raise ValueError("Ação não encontrada")
        if action["status"] != "declared" or action.get("requested_roll_id"):
            raise ValueError("A ação já possui resolução ou rolagem")
        connection.execute("UPDATE scene_actions SET status='awaiting_roll',requested_roll_id=? WHERE id=?", (roll_request_id, action_id))
        updated = _record(connection.execute("SELECT * FROM scene_actions WHERE id=?", (action_id,)).fetchone()) or {}
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (updated["scene_id"],)).fetchone()) or {}
        _event(connection, scene=scene, actor_id=actor_id, actor_role="gm", event_type="roll_requested", title="Rolagem solicitada", character_id=updated.get("character_id"), action_id=action_id, visibility=updated["visibility"], event_key=f"action-roll-request:{action_id}:{roll_request_id}")
    return updated


def link_completed_roll(database_path: Path, *, scene_id: int, action_id: int | None, roll_id: int, actor_id: str, actor_role: ActorRole, public_text: str | None = None) -> None:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())
        if not scene:
            return
        visibility = "table"
        character_id = None
        if action_id:
            action = _record(connection.execute("SELECT * FROM scene_actions WHERE id=? AND scene_id=?", (action_id, scene_id)).fetchone())
            if action:
                character_id = action.get("character_id")
                visibility = action.get("visibility") or "table"
                connection.execute("UPDATE scene_actions SET resulting_roll_id=? WHERE id=? AND resulting_roll_id IS NULL", (roll_id, action_id))
        _event(connection, scene=scene, actor_id=actor_id, actor_role=actor_role, event_type="roll_completed", title="Rolagem concluída", public_text=public_text, character_id=character_id, roll_id=roll_id, action_id=action_id, visibility=visibility, event_key=f"scene-roll:{roll_id}")


def record_consequence(database_path: Path, *, scene_id: int, action_id: int | None, character_id: str, character_event_id: int, actor_id: str, title: str, public_text: str | None = None, private_text: str | None = None, visibility: str = "table") -> dict[str, Any]:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())
        if not scene:
            raise ValueError("Cena não encontrada")
        return _event(connection, scene=scene, actor_id=actor_id, actor_role="gm", event_type="character_consequence", title=title, public_text=public_text, private_text=private_text, character_id=character_id, character_event_id=character_event_id, action_id=action_id, visibility=visibility, event_key=f"scene-character-event:{character_event_id}")


def record_manual_event(database_path: Path, *, scene_id: int, actor_id: str, title: str, public_text: str | None, private_text: str | None, visibility: str = "table") -> dict[str, Any]:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())
        if not scene:
            raise ValueError("Cena não encontrada")
        return _event(connection, scene=scene, actor_id=actor_id, actor_role="gm", event_type="manual_note", title=title, public_text=public_text, private_text=private_text, visibility=visibility)


def publish_scene_event(
    database_path: Path,
    *,
    scene_id: int,
    request_id: str,
    publication_type: str,
    actor_id: str,
    title: str,
    public_text: str | None,
    private_text: str | None = None,
) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    if publication_type not in PUBLICATION_TYPES:
        raise ValueError("Tipo de publicação inválido")
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        event_key = f"scene-publication:{request_id}"
        existing = connection.execute("SELECT * FROM scene_events WHERE event_key=?", (event_key,)).fetchone()
        if existing:
            event = _record(existing) or {}
            if int(event["scene_id"]) != int(scene_id):
                raise ValueError("request_id já utilizado")
            return event, False
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())
        if not scene:
            raise ValueError("Cena não encontrada")
        event = _event(
            connection,
            scene=scene,
            actor_id=actor_id,
            actor_role="gm",
            event_type=f"scene_publication_{publication_type}",
            title=title,
            public_text=public_text,
            private_text=private_text,
            visibility="table",
            event_key=event_key,
        )
    return event, True


def void_event(database_path: Path, event_id: int, *, actor_id: str, reason: str) -> dict[str, Any]:
    reason = _text(reason, "Motivo", maximum=500, required=True) or "Anulado"
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT * FROM scene_events WHERE id=?", (event_id,)).fetchone()
        if not row:
            raise ValueError("Evento não encontrado")
        if row["voided_at"]:
            raise ValueError("Evento já anulado")
        connection.execute("UPDATE scene_events SET voided_at=?,voided_by=?,void_reason=? WHERE id=?", (_now(), actor_id, reason, event_id))
        return _record(connection.execute("SELECT * FROM scene_events WHERE id=?", (event_id,)).fetchone()) or {}


def _can_view(visibility: str, *, access_mode: str, profile_id: str | None, character_id: str | None, actor_id: str | None = None) -> bool:
    if access_mode == "gm":
        return True
    if visibility == "table":
        return True
    if visibility == "gm":
        return False
    if visibility == "owner":
        return bool(profile_id and profile_id == character_id)
    if visibility == "private":
        return bool(profile_id and profile_id == actor_id)
    return False


def scene_view(database_path: Path, scene_id: int, *, access_mode: str, profile_id: str | None) -> dict[str, Any] | None:
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection:
        scene = _record(connection.execute("SELECT * FROM scenes WHERE id=?", (scene_id,)).fetchone())
        if not scene:
            return None
        if access_mode != "gm" and (scene["visibility"] != "table" or scene["status"] == "draft"):
            return None
        participants = [_record(row) or {} for row in connection.execute("SELECT * FROM scene_participants WHERE scene_id=? ORDER BY order_index,id", (scene_id,)).fetchall()]
        elements = [_record(row) or {} for row in connection.execute("SELECT * FROM scene_elements WHERE scene_id=? ORDER BY id", (scene_id,)).fetchall()]
        actions = [_record(row) or {} for row in connection.execute("SELECT * FROM scene_actions WHERE scene_id=? ORDER BY id DESC LIMIT 100", (scene_id,)).fetchall()]
        events = [_record(row) or {} for row in connection.execute("SELECT * FROM scene_events WHERE scene_id=? ORDER BY id DESC LIMIT 150", (scene_id,)).fetchall()]
    if access_mode != "gm":
        for key in (
            "request_id", "created_by", "location_source", "private_notes", "checklist",
            "map_zoom", "map_scroll_left", "map_scroll_top",
        ):
            scene.pop(key, None)
        participants = [{key: value for key, value in item.items() if key != "private_status"} for item in participants if item.get("visible_to_players")]
        filtered_elements = []
        for item in elements:
            if not _can_view(item["visibility"], access_mode=access_mode, profile_id=profile_id, character_id=None):
                continue
            if item["status"] == "hidden":
                continue
            item = dict(item)
            item.pop("private_description", None)
            filtered_elements.append(item)
        elements = filtered_elements
        actions = [item for item in actions if _can_view(item["visibility"], access_mode=access_mode, profile_id=profile_id, character_id=item.get("character_id"), actor_id=item.get("actor_id"))]
        events = [item for item in events if _can_view(item["visibility"], access_mode=access_mode, profile_id=profile_id, character_id=item.get("character_id"), actor_id=item.get("actor_id"))]
        for event in events:
            event.pop("private_text", None)
    return {**scene, "participants": participants, "elements": elements, "actions": actions, "events": events}
