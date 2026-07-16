from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


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


def _record(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for key in ("visible_to_players",):
        if key in result:
            result[key] = bool(result[key])
    if "voided_at" in result:
        result["voided"] = bool(result["voided_at"])
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


def change_session_status(database_path: Path, session_id: int, status: str) -> dict[str, Any]:
    if status not in SESSION_STATUSES:
        raise ValueError("Status de sessão inválido")
    init_scene_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            raise ValueError("Sessão não encontrada")
        now = _now()
        connection.execute(
            "UPDATE game_sessions SET status=?,started_at=CASE WHEN ?='active' AND started_at IS NULL THEN ? ELSE started_at END,ended_at=CASE WHEN ?='completed' THEN ? ELSE ended_at END,version=version+1 WHERE id=?",
            (status, status, now, status, now, session_id),
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
        if session_id and not connection.execute("SELECT 1 FROM game_sessions WHERE id=?", (session_id,)).fetchone():
            raise ValueError("Sessão não encontrada")
        order_index = connection.execute("SELECT COALESCE(MAX(order_index),0)+1 FROM scenes WHERE campaign_id=?", (campaign_id,)).fetchone()[0]
        cursor = connection.execute(
            """
            INSERT INTO scenes(request_id,campaign_id,session_id,title,location_name,location_source,
              public_description,objective,private_notes,status,visibility,created_by,created_at,order_index)
            VALUES(?,?,?,?,?,?,?,?,?,'draft',?,?,?,?)
            """,
            (
                request_id, campaign_id, session_id, _text(title, "Título", maximum=180, required=True),
                _text(location_name, "Local", maximum=180, required=True), _text(location_source, "Fonte do local", maximum=500),
                _text(public_description, "Descrição pública"), _text(objective, "Objetivo", maximum=500),
                _text(private_notes, "Notas privadas"), visibility, created_by, _now(), order_index,
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
    allowed = {"title", "location_name", "location_source", "public_description", "objective", "private_notes", "visibility", "order_index"}
    if set(fields) - allowed:
        raise ValueError("Campo de cena inválido")
    if "visibility" in fields:
        fields["visibility"] = _visibility(str(fields["visibility"]))
    for key in ("title", "location_name"):
        if key in fields:
            fields[key] = _text(fields[key], key, maximum=180, required=True)
    for key in ("location_source", "public_description", "objective", "private_notes"):
        if key in fields:
            fields[key] = _text(fields[key], key, maximum=500 if key in {"location_source", "objective"} else MAX_TEXT)
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
        cursor = connection.execute(
            """
            INSERT INTO scene_participants(scene_id,participant_type,character_id,npc_name,npc_source,public_label,
              public_status,private_status,visible_to_players,joined_at) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                scene_id, participant_type, character_id, _text(npc_name, "NPC", maximum=180),
                _text(npc_source, "Fonte", maximum=500), _text(public_label, "Nome público", maximum=180, required=True),
                _text(public_status, "Estado público", maximum=180), _text(private_status, "Estado privado", maximum=500),
                int(visible_to_players), _now(),
            ),
        )
        participant = _record(connection.execute("SELECT * FROM scene_participants WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}
        _event(connection, scene=scene, actor_id=actor_id, actor_role="gm", event_type="participant_joined", title=f"{participant['public_label']} entrou na cena", character_id=character_id, visibility="table" if visible_to_players else "gm")
    return participant


def update_participant(database_path: Path, participant_id: int, fields: dict[str, Any], *, actor_id: str = "master") -> dict[str, Any]:
    allowed = {"public_label", "public_status", "private_status", "visible_to_players", "left_at"}
    if set(fields) - allowed:
        raise ValueError("Campo de participante inválido")
    for key in ("public_label", "public_status", "private_status"):
        if key in fields:
            fields[key] = _text(fields[key], key, maximum=500, required=key == "public_label")
    if "visible_to_players" in fields:
        fields["visible_to_players"] = int(bool(fields["visible_to_players"]))
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
        participants = [_record(row) or {} for row in connection.execute("SELECT * FROM scene_participants WHERE scene_id=? ORDER BY id", (scene_id,)).fetchall()]
        elements = [_record(row) or {} for row in connection.execute("SELECT * FROM scene_elements WHERE scene_id=? ORDER BY id", (scene_id,)).fetchall()]
        actions = [_record(row) or {} for row in connection.execute("SELECT * FROM scene_actions WHERE scene_id=? ORDER BY id DESC LIMIT 100", (scene_id,)).fetchall()]
        events = [_record(row) or {} for row in connection.execute("SELECT * FROM scene_events WHERE scene_id=? ORDER BY id DESC LIMIT 150", (scene_id,)).fetchall()]
    if access_mode != "gm":
        scene.pop("private_notes", None)
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
