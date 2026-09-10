from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .session_context import active_game_session_id, table_exists


ActorRole = Literal["gm", "player"]

CONTRACT_STATUSES = {"draft", "published", "accepted", "active", "completed", "failed", "abandoned", "cancelled"}
TERMINAL_STATUSES = {"completed", "failed", "abandoned", "cancelled"}
CONTRACT_TYPES = {"investigação", "escolta", "recuperação", "caça", "proteção", "exploração", "negociação", "entrega", "resgate", "outro"}
CONTRACT_VISIBILITIES = {"table", "gm", "assigned"}
OBJECTIVE_TYPES = {"narrative", "progress", "scene", "combat", "social", "exploration", "other"}
OBJECTIVE_STATUSES = {"hidden", "available", "active", "completed", "failed", "skipped"}
ASSIGNMENT_STATUSES = {"assigned", "active", "left", "completed"}
SCENE_LINK_TYPES = {"preparation", "investigation", "encounter", "resolution", "aftermath", "other"}
REWARD_TYPES = {"currency", "item", "reputation", "information", "favor", "access", "custom"}
REWARD_STATUSES = {"proposed", "approved", "delivered", "withheld", "cancelled"}
EVENT_VISIBILITIES = {"table", "gm", "owner", "private"}
VALID_TRANSITIONS = {
    "draft": {"published", "cancelled"},
    "published": {"accepted", "cancelled"},
    "accepted": {"active", "cancelled"},
    "active": {"completed", "failed", "abandoned"},
}
MAX_TEXT = 3000


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any, label: str, *, maximum: int = MAX_TEXT, required: bool = False) -> str | None:
    text = str(value or "").strip()
    if required and not text:
        raise ValueError(f"{label} é obrigatório")
    if len(text) > maximum:
        raise ValueError(f"{label} excede {maximum} caracteres")
    return text or None


def _request_id(value: str | None) -> str:
    request_id = str(value or "").strip()
    if not 8 <= len(request_id) <= 140 or not all(char.isalnum() or char in "._:-" for char in request_id):
        raise ValueError("request_id inválido")
    return request_id


def _status(value: str, allowed: set[str], label: str) -> str:
    normalized = str(value or "").strip()
    if normalized not in allowed:
        raise ValueError(f"{label} inválido")
    return normalized


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "sim", "s"}


def _number(value: Any) -> int | float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else float(value)
    match = re.search(r"[-+]?\d+(?:[.,]\d+)?", str(value))
    if not match:
        return None
    parsed = float(match.group(0).replace(",", "."))
    return int(parsed) if parsed.is_integer() else parsed


def _json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _loads(value: Any) -> Any:
    if not value:
        return None
    return json.loads(str(value))


def _record(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for key in ("required", "revealed_to_players"):
        if key in result:
            result[key] = bool(result[key])
    if "voided_at" in result:
        result["voided"] = bool(result["voided_at"])
    if "reverted_at" in result:
        result["reverted"] = bool(result["reverted_at"])
    return result


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return bool(connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone())


def init_contract_play(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS contracts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE,
              campaign_id TEXT NOT NULL,
              session_id INTEGER,
              title TEXT NOT NULL,
              slug TEXT,
              contract_type TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'draft',
              issuer_name TEXT NOT NULL,
              issuer_type TEXT,
              issuer_source TEXT,
              location_name TEXT,
              location_source TEXT,
              public_summary TEXT NOT NULL,
              public_briefing TEXT NOT NULL,
              private_briefing TEXT,
              risk_label TEXT NOT NULL,
              recommended_level TEXT,
              deadline_text TEXT,
              visibility TEXT NOT NULL DEFAULT 'table',
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              published_at TEXT,
              accepted_at TEXT,
              started_at TEXT,
              resolved_at TEXT,
              version INTEGER NOT NULL DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_contracts_campaign_status ON contracts(campaign_id,status,id DESC);

            CREATE TABLE IF NOT EXISTS contract_objectives (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE,
              contract_id INTEGER NOT NULL,
              title TEXT NOT NULL,
              public_description TEXT NOT NULL,
              private_description TEXT,
              objective_type TEXT NOT NULL DEFAULT 'narrative',
              status TEXT NOT NULL DEFAULT 'hidden',
              required INTEGER NOT NULL DEFAULT 1,
              order_index INTEGER NOT NULL DEFAULT 0,
              progress_current REAL,
              progress_target REAL,
              revealed_to_players INTEGER NOT NULL DEFAULT 0,
              completed_at TEXT,
              completed_by TEXT,
              created_at TEXT NOT NULL,
              version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_contract_objectives_contract ON contract_objectives(contract_id,order_index,id);

            CREATE TABLE IF NOT EXISTS contract_assignments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE,
              contract_id INTEGER NOT NULL,
              character_id TEXT NOT NULL,
              assigned_by TEXT NOT NULL,
              assigned_at TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'assigned',
              left_at TEXT,
              public_role TEXT,
              FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
              UNIQUE(contract_id, character_id)
            );

            CREATE TABLE IF NOT EXISTS contract_scene_links (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE,
              contract_id INTEGER NOT NULL,
              scene_id INTEGER NOT NULL,
              objective_id INTEGER,
              link_type TEXT NOT NULL DEFAULT 'other',
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
              FOREIGN KEY(objective_id) REFERENCES contract_objectives(id) ON DELETE SET NULL,
              UNIQUE(contract_id, scene_id, objective_id, link_type)
            );

            CREATE TABLE IF NOT EXISTS contract_rewards (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE,
              contract_id INTEGER NOT NULL,
              reward_type TEXT NOT NULL,
              label TEXT NOT NULL,
              description TEXT,
              quantity REAL,
              currency_type TEXT,
              item_source TEXT,
              item_name TEXT,
              reputation_faction TEXT,
              reputation_amount INTEGER,
              visibility TEXT NOT NULL DEFAULT 'table',
              status TEXT NOT NULL DEFAULT 'proposed',
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              approved_at TEXT,
              approved_by TEXT,
              delivered_at TEXT,
              version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_contract_rewards_contract ON contract_rewards(contract_id,status,id);

            CREATE TABLE IF NOT EXISTS contract_reward_deliveries (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT NOT NULL UNIQUE,
              contract_id INTEGER NOT NULL,
              reward_id INTEGER NOT NULL,
              delivered_by TEXT NOT NULL,
              delivered_at TEXT NOT NULL,
              response_json TEXT NOT NULL,
              FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
              FOREIGN KEY(reward_id) REFERENCES contract_rewards(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS reputation_ledger (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              request_id TEXT UNIQUE,
              campaign_id TEXT NOT NULL,
              character_id TEXT,
              party_id TEXT,
              faction_name TEXT NOT NULL,
              delta INTEGER NOT NULL,
              resulting_value INTEGER NOT NULL,
              reason TEXT NOT NULL,
              contract_id INTEGER,
              actor_id TEXT NOT NULL,
              actor_role TEXT NOT NULL,
              created_at TEXT NOT NULL,
              reverted_at TEXT,
              reverted_by TEXT,
              FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_reputation_scope ON reputation_ledger(campaign_id,faction_name,character_id,party_id,id DESC);

            CREATE TABLE IF NOT EXISTS contract_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              event_key TEXT UNIQUE,
              contract_id INTEGER NOT NULL,
              actor_id TEXT NOT NULL,
              actor_role TEXT NOT NULL,
              event_type TEXT NOT NULL,
              title TEXT NOT NULL,
              public_text TEXT,
              private_text TEXT,
              objective_id INTEGER,
              scene_id INTEGER,
              character_id TEXT,
              reward_id INTEGER,
              visibility TEXT NOT NULL DEFAULT 'table',
              created_at TEXT NOT NULL,
              voided_at TEXT,
              voided_by TEXT,
              void_reason TEXT,
              FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_contract_events_contract ON contract_events(contract_id,id DESC);
            """
        )
        event_columns = {row[1] for row in connection.execute("PRAGMA table_info(contract_events)")}
        if "game_session_id" not in event_columns:
            connection.execute(
                "ALTER TABLE contract_events ADD COLUMN game_session_id INTEGER"
                + (" REFERENCES game_sessions(id)" if table_exists(connection, "game_sessions") else "")
            )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_contract_events_game_session ON contract_events(game_session_id,id DESC)"
        )
        connection.execute(
            """
            UPDATE contract_events
            SET game_session_id=(
              SELECT contracts.session_id FROM contracts WHERE contracts.id=contract_events.contract_id
            )
            WHERE game_session_id IS NULL AND EXISTS(
              SELECT 1 FROM contracts
              WHERE contracts.id=contract_events.contract_id AND contracts.session_id IS NOT NULL
            )
            """
        )


def _event(
    connection: sqlite3.Connection,
    *,
    contract_id: int,
    actor_id: str,
    actor_role: ActorRole,
    event_type: str,
    title: str,
    visibility: str = "table",
    public_text: str | None = None,
    private_text: str | None = None,
    objective_id: int | None = None,
    scene_id: int | None = None,
    character_id: str | None = None,
    reward_id: int | None = None,
    event_key: str | None = None,
) -> dict[str, Any]:
    visibility = _status(visibility, EVENT_VISIBILITIES, "Visibilidade")
    if event_key:
        existing = connection.execute("SELECT * FROM contract_events WHERE event_key=?", (event_key,)).fetchone()
        if existing:
            return _record(existing) or {}
    contract_context = connection.execute(
        "SELECT campaign_id,session_id FROM contracts WHERE id=?",
        (contract_id,),
    ).fetchone()
    if not contract_context:
        raise ValueError("Contrato inexistente")
    game_session_id = (
        int(contract_context["session_id"])
        if contract_context["session_id"] is not None
        else active_game_session_id(connection, str(contract_context["campaign_id"]))
    )
    cursor = connection.execute(
        """
        INSERT INTO contract_events(event_key,contract_id,game_session_id,actor_id,actor_role,event_type,title,public_text,
          private_text,objective_id,scene_id,character_id,reward_id,visibility,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            event_key,
            contract_id,
            game_session_id,
            actor_id,
            actor_role,
            event_type,
            _text(title, "Título", maximum=180, required=True),
            _text(public_text, "Texto público"),
            _text(private_text, "Texto privado"),
            objective_id,
            scene_id,
            character_id,
            reward_id,
            visibility,
            _now(),
        ),
    )
    return _record(connection.execute("SELECT * FROM contract_events WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}


def _contract(connection: sqlite3.Connection, contract_id: int) -> dict[str, Any]:
    record = _record(connection.execute("SELECT * FROM contracts WHERE id=?", (contract_id,)).fetchone())
    if not record:
        raise ValueError("Contrato inexistente")
    return record


def _objective(connection: sqlite3.Connection, objective_id: int) -> dict[str, Any]:
    record = _record(connection.execute("SELECT * FROM contract_objectives WHERE id=?", (objective_id,)).fetchone())
    if not record:
        raise ValueError("Objetivo inexistente")
    return record


def _reward(connection: sqlite3.Connection, reward_id: int) -> dict[str, Any]:
    record = _record(connection.execute("SELECT * FROM contract_rewards WHERE id=?", (reward_id,)).fetchone())
    if not record:
        raise ValueError("Recompensa inexistente")
    return record


def _ensure_open(contract: dict[str, Any]) -> None:
    if contract["status"] in TERMINAL_STATUSES:
        raise ValueError("Contrato encerrado não aceita novas ações oficiais")


def _assigned_ids(connection: sqlite3.Connection, contract_id: int) -> set[str]:
    rows = connection.execute(
        "SELECT character_id FROM contract_assignments WHERE contract_id=? AND left_at IS NULL",
        (contract_id,),
    ).fetchall()
    return {str(row["character_id"]) for row in rows}


def _can_view_contract(connection: sqlite3.Connection, contract: dict[str, Any], *, access_mode: str, profile_id: str | None) -> bool:
    if access_mode == "gm":
        return True
    if contract["status"] == "draft":
        return False
    if contract["visibility"] == "gm":
        return False
    if contract["visibility"] == "assigned":
        return bool(profile_id and profile_id in _assigned_ids(connection, int(contract["id"])))
    return True


def _can_view_event(event: dict[str, Any], *, access_mode: str, profile_id: str | None) -> bool:
    if access_mode == "gm":
        return True
    if event.get("voided_at"):
        return False
    visibility = event.get("visibility")
    if visibility == "table":
        return True
    if visibility == "owner":
        return bool(profile_id and event.get("character_id") == profile_id)
    return False


def _public_contract_payload(connection: sqlite3.Connection, contract: dict[str, Any], *, access_mode: str, profile_id: str | None) -> dict[str, Any] | None:
    if not _can_view_contract(connection, contract, access_mode=access_mode, profile_id=profile_id):
        return None
    is_gm = access_mode == "gm"
    contract_id = int(contract["id"])
    payload = dict(contract)
    if not is_gm:
        for key in ("private_briefing", "issuer_source", "location_source"):
            payload.pop(key, None)

    objectives = [_record(row) or {} for row in connection.execute(
        "SELECT * FROM contract_objectives WHERE contract_id=? ORDER BY order_index,id",
        (contract_id,),
    ).fetchall()]
    if not is_gm:
        objectives = [
            {key: value for key, value in objective.items() if key != "private_description"}
            for objective in objectives
            if objective.get("revealed_to_players") and objective.get("status") != "hidden"
        ]

    assignments = [_record(row) or {} for row in connection.execute(
        "SELECT * FROM contract_assignments WHERE contract_id=? ORDER BY id",
        (contract_id,),
    ).fetchall()]
    if not is_gm:
        assignments = [
            {key: value for key, value in assignment.items() if key not in {"assigned_by"}}
            for assignment in assignments
            if not assignment.get("left_at")
        ]

    rewards = [_record(row) or {} for row in connection.execute(
        "SELECT * FROM contract_rewards WHERE contract_id=? ORDER BY id",
        (contract_id,),
    ).fetchall()]
    if not is_gm:
        rewards = [
            {key: value for key, value in reward.items() if key not in {"item_source"}}
            for reward in rewards
            if reward.get("visibility") == "table"
        ]

    if _table_exists(connection, "scenes"):
        scene_rows = connection.execute(
            """
            SELECT l.*, s.title AS scene_title, s.status AS scene_status, s.visibility AS scene_visibility,
                   o.title AS objective_title, o.revealed_to_players AS objective_revealed, o.status AS objective_status
            FROM contract_scene_links l
            LEFT JOIN scenes s ON s.id = l.scene_id
            LEFT JOIN contract_objectives o ON o.id = l.objective_id
            WHERE l.contract_id=?
            ORDER BY l.id
            """,
            (contract_id,),
        ).fetchall()
    else:
        scene_rows = connection.execute(
            """
            SELECT l.*, NULL AS scene_title, NULL AS scene_status, NULL AS scene_visibility,
                   o.title AS objective_title, o.revealed_to_players AS objective_revealed, o.status AS objective_status
            FROM contract_scene_links l
            LEFT JOIN contract_objectives o ON o.id = l.objective_id
            WHERE l.contract_id=?
            ORDER BY l.id
            """,
            (contract_id,),
        ).fetchall()
    scene_links = [_record(row) or {} for row in scene_rows]
    if not is_gm:
        visible_objective_ids = {int(item["id"]) for item in objectives}
        scene_links = [
            link
            for link in scene_links
            if link.get("scene_visibility") == "table"
            and link.get("scene_status") != "draft"
            and (link.get("objective_id") is None or int(link["objective_id"]) in visible_objective_ids)
        ]

    events = [_record(row) or {} for row in connection.execute(
        "SELECT * FROM contract_events WHERE contract_id=? ORDER BY id DESC LIMIT 200",
        (contract_id,),
    ).fetchall()]
    events = [event for event in events if _can_view_event(event, access_mode=access_mode, profile_id=profile_id)]
    if not is_gm:
        events = [{key: value for key, value in event.items() if key != "private_text"} for event in events]

    payload["objectives"] = objectives
    payload["assignments"] = assignments
    payload["scene_links"] = scene_links
    payload["rewards"] = rewards
    payload["events"] = events
    payload["revealed_objective_count"] = len(objectives)
    payload["assigned_character_ids"] = [assignment["character_id"] for assignment in assignments if not assignment.get("left_at")]
    return payload


def list_contracts(database_path: Path, *, campaign_id: str = "omnisvera", access_mode: str, profile_id: str | None = None) -> list[dict[str, Any]]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT * FROM contracts WHERE campaign_id=? ORDER BY id DESC", (campaign_id,)).fetchall()
        result = []
        for row in rows:
            payload = _public_contract_payload(connection, _record(row) or {}, access_mode=access_mode, profile_id=profile_id)
            if payload is not None:
                result.append(payload)
        return result


def current_operational_contract(contracts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Select mission focus from operational contract state, never UI selection."""
    return next((item for item in contracts if item.get("status") == "active"), None) or next(
        (item for item in contracts if item.get("status") == "accepted"),
        None,
    )


def get_contract(database_path: Path, contract_id: int, *, access_mode: str, profile_id: str | None = None) -> dict[str, Any] | None:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection:
        contract = _record(connection.execute("SELECT * FROM contracts WHERE id=?", (contract_id,)).fetchone())
        if not contract:
            return None
        return _public_contract_payload(connection, contract, access_mode=access_mode, profile_id=profile_id)


def create_contract(database_path: Path, *, request_id: str, campaign_id: str, actor_id: str, fields: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    contract_type = _status(str(fields.get("contract_type") or "outro"), CONTRACT_TYPES, "Tipo")
    visibility = _status(str(fields.get("visibility") or "table"), CONTRACT_VISIBILITIES, "Visibilidade")
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM contracts WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            payload = _public_contract_payload(connection, _record(existing) or {}, access_mode="gm", profile_id=None) or {}
            return payload, False
        cursor = connection.execute(
            """
            INSERT INTO contracts(request_id,campaign_id,session_id,title,slug,contract_type,status,issuer_name,
              issuer_type,issuer_source,location_name,location_source,public_summary,public_briefing,
              private_briefing,risk_label,recommended_level,deadline_text,visibility,created_by,created_at)
            VALUES(?,?,?,?,?,?,'draft',?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                request_id,
                campaign_id,
                fields.get("session_id"),
                _text(fields.get("title"), "Título", maximum=180, required=True),
                _text(fields.get("slug"), "Slug", maximum=180),
                contract_type,
                _text(fields.get("issuer_name"), "Contratante", maximum=180, required=True),
                _text(fields.get("issuer_type"), "Tipo do contratante", maximum=120),
                _text(fields.get("issuer_source"), "Fonte do contratante", maximum=500),
                _text(fields.get("location_name"), "Local", maximum=180),
                _text(fields.get("location_source"), "Fonte do local", maximum=500),
                _text(fields.get("public_summary"), "Resumo público", maximum=500, required=True),
                _text(fields.get("public_briefing"), "Briefing público", required=True),
                _text(fields.get("private_briefing"), "Briefing privado"),
                _text(fields.get("risk_label") or "Não informado", "Risco", maximum=120, required=True),
                _text(fields.get("recommended_level"), "Nível recomendado", maximum=80),
                _text(fields.get("deadline_text"), "Prazo", maximum=180),
                visibility,
                actor_id,
                _now(),
            ),
        )
        contract_id = int(cursor.lastrowid)
        _event(
            connection,
            contract_id=contract_id,
            actor_id=actor_id,
            actor_role="gm",
            event_type="contract_created",
            title="Contrato criado",
            visibility="gm",
            private_text=fields.get("title"),
            event_key=f"contract-created:{contract_id}",
        )
        payload = _public_contract_payload(connection, _contract(connection, contract_id), access_mode="gm", profile_id=None) or {}
        return payload, True


def update_contract(database_path: Path, contract_id: int, *, expected_version: int, fields: dict[str, Any], actor_id: str) -> dict[str, Any]:
    allowed = {
        "session_id", "title", "slug", "contract_type", "issuer_name", "issuer_type", "issuer_source",
        "location_name", "location_source", "public_summary", "public_briefing", "private_briefing",
        "risk_label", "recommended_level", "deadline_text", "visibility",
    }
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Campos inválidos: {', '.join(sorted(unknown))}")
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        contract = _contract(connection, contract_id)
        if int(contract["version"]) != int(expected_version):
            raise RuntimeError("versão desatualizada")
        if contract["status"] in TERMINAL_STATUSES:
            raise ValueError("Contrato encerrado não pode ser editado")
        updates: dict[str, Any] = {}
        for key, value in fields.items():
            if key == "contract_type":
                updates[key] = _status(str(value), CONTRACT_TYPES, "Tipo")
            elif key == "visibility":
                updates[key] = _status(str(value), CONTRACT_VISIBILITIES, "Visibilidade")
            elif key in {"title", "issuer_name", "public_summary", "public_briefing", "risk_label"}:
                updates[key] = _text(value, key, required=True)
            elif key == "session_id":
                updates[key] = value
            else:
                updates[key] = _text(value, key)
        if updates:
            clause = ", ".join(f"{key}=?" for key in updates)
            connection.execute(
                f"UPDATE contracts SET {clause}, version=version+1 WHERE id=?",
                (*updates.values(), contract_id),
            )
            _event(
                connection,
                contract_id=contract_id,
                actor_id=actor_id,
                actor_role="gm",
                event_type="contract_updated",
                title="Contrato atualizado",
                visibility="gm",
                private_text=", ".join(sorted(updates)),
            )
        return _public_contract_payload(connection, _contract(connection, contract_id), access_mode="gm", profile_id=None) or {}


def transition_contract(
    database_path: Path,
    contract_id: int,
    *,
    status: str,
    actor_id: str,
    actor_role: ActorRole,
    request_id: str,
    reason: str | None = None,
) -> dict[str, Any]:
    request_id = _request_id(request_id)
    status = _status(status, CONTRACT_STATUSES, "Status")
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        contract = _contract(connection, contract_id)
        current = str(contract["status"])
        if current == status:
            return _public_contract_payload(connection, contract, access_mode="gm", profile_id=None) or contract
        if status not in VALID_TRANSITIONS.get(current, set()):
            raise ValueError("Transição inválida")
        if current == "accepted" and status == "cancelled" and not _text(reason, "Motivo", maximum=500):
            raise ValueError("Motivo obrigatorio para cancelar contrato aceito")
        now = _now()
        timestamps = {
            "published": ("published_at", now),
            "accepted": ("accepted_at", now),
            "active": ("started_at", now),
            "completed": ("resolved_at", now),
            "failed": ("resolved_at", now),
            "abandoned": ("resolved_at", now),
            "cancelled": ("resolved_at", now),
        }
        column, value = timestamps[status]
        connection.execute(
            f"UPDATE contracts SET status=?, {column}=COALESCE({column}, ?), version=version+1 WHERE id=?",
            (status, value, contract_id),
        )
        labels = {
            "published": "Contrato publicado",
            "accepted": "Contrato aceito",
            "active": "Contrato iniciado",
            "completed": "Contrato concluído",
            "failed": "Contrato falhou",
            "abandoned": "Contrato abandonado",
            "cancelled": "Contrato cancelado",
        }
        visibility = "table" if status in {"published", "accepted", "active", "completed", "failed", "abandoned"} else "gm"
        _event(
            connection,
            contract_id=contract_id,
            actor_id=actor_id,
            actor_role=actor_role,
            event_type=f"contract_{status}",
            title=labels[status],
            public_text=reason if visibility == "table" else None,
            private_text=reason,
            visibility=visibility,
            event_key=f"contract-transition:{contract_id}:{status}:{request_id}",
        )
        return _public_contract_payload(connection, _contract(connection, contract_id), access_mode="gm", profile_id=None) or {}


def accept_contract(
    database_path: Path,
    contract_id: int,
    *,
    request_id: str,
    actor_id: str,
    actor_role: ActorRole,
    character_id: str | None = None,
    public_role: str | None = None,
) -> dict[str, Any]:
    request_id = _request_id(request_id)
    if actor_role != "gm" and character_id and character_id != actor_id:
        raise PermissionError("Personagem não autorizado")
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        contract = _contract(connection, contract_id)
        if contract["status"] != "published":
            if contract["status"] == "accepted":
                return _public_contract_payload(connection, contract, access_mode="gm", profile_id=None) or contract
            raise ValueError("Contrato não publicado")
        now = _now()
        connection.execute(
            "UPDATE contracts SET status='accepted', accepted_at=COALESCE(accepted_at, ?), version=version+1 WHERE id=?",
            (now, contract_id),
        )
        _event(
            connection,
            contract_id=contract_id,
            actor_id=actor_id,
            actor_role=actor_role,
            event_type="contract_accepted",
            title="Contrato aceito",
            public_text="O contrato foi aceito.",
            visibility="table",
            event_key=f"contract-accepted:{contract_id}:{request_id}",
        )
        if character_id:
            _add_assignment_in_connection(
                connection,
                contract_id=contract_id,
                request_id=f"{request_id}:assignment",
                character_id=character_id,
                assigned_by=actor_id,
                public_role=public_role,
                actor_role=actor_role,
            )
        return _public_contract_payload(connection, _contract(connection, contract_id), access_mode="gm", profile_id=None) or {}


def _next_objective_order(connection: sqlite3.Connection, contract_id: int) -> int:
    return int(connection.execute("SELECT COALESCE(MAX(order_index),0)+1 FROM contract_objectives WHERE contract_id=?", (contract_id,)).fetchone()[0])


def create_objective(database_path: Path, contract_id: int, *, request_id: str, actor_id: str, fields: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    objective_type = _status(str(fields.get("objective_type") or "narrative"), OBJECTIVE_TYPES, "Tipo de objetivo")
    status = _status(str(fields.get("status") or "hidden"), OBJECTIVE_STATUSES, "Status do objetivo")
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM contract_objectives WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        contract = _contract(connection, contract_id)
        _ensure_open(contract)
        progress_current = _number(fields.get("progress_current"))
        progress_target = _number(fields.get("progress_target"))
        if progress_target is not None and progress_target <= 0:
            raise ValueError("Progresso alvo inválido")
        cursor = connection.execute(
            """
            INSERT INTO contract_objectives(request_id,contract_id,title,public_description,private_description,
              objective_type,status,required,order_index,progress_current,progress_target,revealed_to_players,
              created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                request_id,
                contract_id,
                _text(fields.get("title"), "Título", maximum=180, required=True),
                _text(fields.get("public_description"), "Descrição pública", required=True),
                _text(fields.get("private_description"), "Descrição privada"),
                objective_type,
                status,
                int(_bool(fields.get("required", True))),
                int(fields.get("order_index") or _next_objective_order(connection, contract_id)),
                progress_current,
                progress_target,
                int(_bool(fields.get("revealed_to_players")) or status in {"available", "active", "completed"}),
                _now(),
            ),
        )
        objective = _record(connection.execute("SELECT * FROM contract_objectives WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}
        _event(
            connection,
            contract_id=contract_id,
            actor_id=actor_id,
            actor_role="gm",
            event_type="objective_created",
            title="Objetivo criado",
            private_text=objective["title"],
            objective_id=int(objective["id"]),
            visibility="gm" if not objective["revealed_to_players"] else "table",
        )
        return objective, True


def update_objective(database_path: Path, objective_id: int, *, expected_version: int, fields: dict[str, Any], actor_id: str) -> dict[str, Any]:
    allowed = {"title", "public_description", "private_description", "objective_type", "status", "required", "order_index", "progress_current", "progress_target", "revealed_to_players"}
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Campos inválidos: {', '.join(sorted(unknown))}")
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        objective = _objective(connection, objective_id)
        contract = _contract(connection, int(objective["contract_id"]))
        _ensure_open(contract)
        if int(objective["version"]) != int(expected_version):
            raise RuntimeError("versão desatualizada")
        if objective["status"] in {"completed", "failed", "skipped"}:
            raise ValueError("Objetivo já encerrado")
        updates: dict[str, Any] = {}
        for key, value in fields.items():
            if key == "objective_type":
                updates[key] = _status(str(value), OBJECTIVE_TYPES, "Tipo de objetivo")
            elif key == "status":
                updates[key] = _status(str(value), OBJECTIVE_STATUSES, "Status do objetivo")
            elif key in {"required", "revealed_to_players"}:
                updates[key] = int(_bool(value))
            elif key in {"progress_current", "progress_target"}:
                updates[key] = _number(value)
            elif key == "order_index":
                updates[key] = int(value)
            elif key in {"title", "public_description"}:
                updates[key] = _text(value, key, required=True)
            else:
                updates[key] = _text(value, key)
        if updates:
            clause = ", ".join(f"{key}=?" for key in updates)
            connection.execute(f"UPDATE contract_objectives SET {clause}, version=version+1 WHERE id=?", (*updates.values(), objective_id))
            _event(connection, contract_id=int(objective["contract_id"]), actor_id=actor_id, actor_role="gm", event_type="objective_updated", title="Objetivo atualizado", objective_id=objective_id, visibility="gm", private_text=", ".join(sorted(updates)))
        return _record(connection.execute("SELECT * FROM contract_objectives WHERE id=?", (objective_id,)).fetchone()) or {}


def set_objective_status(database_path: Path, objective_id: int, *, status: str, request_id: str, actor_id: str) -> dict[str, Any]:
    request_id = _request_id(request_id)
    status = _status(status, OBJECTIVE_STATUSES, "Status do objetivo")
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        objective = _objective(connection, objective_id)
        contract = _contract(connection, int(objective["contract_id"]))
        _ensure_open(contract)
        current = str(objective["status"])
        event_key = f"objective-status:{objective_id}:{status}:{request_id}"
        existing_event = connection.execute("SELECT 1 FROM contract_events WHERE event_key=?", (event_key,)).fetchone()
        if current == status:
            if existing_event:
                return objective
            if current in {"completed", "failed", "skipped"}:
                raise ValueError("Objetivo ja encerrado")
            return objective
        if current in {"completed", "failed", "skipped"}:
            raise ValueError("Objetivo já encerrado")
        if status == "skipped" and objective["required"]:
            raise ValueError("Objetivo obrigatório não pode ser pulado")
        updates = {
            "status": status,
            "revealed_to_players": int(status in {"available", "active", "completed", "failed", "skipped"} or objective["revealed_to_players"]),
            "completed_at": _now() if status in {"completed", "failed", "skipped"} else objective.get("completed_at"),
            "completed_by": actor_id if status in {"completed", "failed", "skipped"} else objective.get("completed_by"),
        }
        connection.execute(
            """
            UPDATE contract_objectives
            SET status=?, revealed_to_players=?, completed_at=?, completed_by=?, version=version+1
            WHERE id=?
            """,
            (updates["status"], updates["revealed_to_players"], updates["completed_at"], updates["completed_by"], objective_id),
        )
        label = {
            "available": "Objetivo revelado",
            "active": "Objetivo ativado",
            "completed": "Objetivo concluído",
            "failed": "Objetivo falhou",
            "skipped": "Objetivo pulado",
            "hidden": "Objetivo ocultado",
        }[status]
        visibility = "table" if updates["revealed_to_players"] else "gm"
        _event(
            connection,
            contract_id=int(objective["contract_id"]),
            actor_id=actor_id,
            actor_role="gm",
            event_type=f"objective_{status}",
            title=label,
            public_text=objective["title"] if visibility == "table" else None,
            private_text=objective["title"],
            objective_id=objective_id,
            visibility=visibility,
            event_key=event_key,
        )
        return _record(connection.execute("SELECT * FROM contract_objectives WHERE id=?", (objective_id,)).fetchone()) or {}


def reorder_objectives(database_path: Path, contract_id: int, order: list[int], *, actor_id: str) -> list[dict[str, Any]]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        contract = _contract(connection, contract_id)
        _ensure_open(contract)
        current_ids = {int(row["id"]) for row in connection.execute("SELECT id FROM contract_objectives WHERE contract_id=?", (contract_id,)).fetchall()}
        requested_ids = [int(item) for item in order]
        if set(requested_ids) != current_ids:
            raise ValueError("Lista de objetivos inválida")
        for index, objective_id in enumerate(requested_ids, 1):
            connection.execute("UPDATE contract_objectives SET order_index=?, version=version+1 WHERE id=?", (index, objective_id))
        _event(connection, contract_id=contract_id, actor_id=actor_id, actor_role="gm", event_type="objectives_reordered", title="Objetivos reordenados", visibility="gm")
        rows = connection.execute("SELECT * FROM contract_objectives WHERE contract_id=? ORDER BY order_index,id", (contract_id,)).fetchall()
        return [_record(row) or {} for row in rows]


def _add_assignment_in_connection(
    connection: sqlite3.Connection,
    *,
    contract_id: int,
    request_id: str,
    character_id: str,
    assigned_by: str,
    public_role: str | None,
    actor_role: ActorRole = "gm",
) -> dict[str, Any]:
    normalized_request_id = _request_id(request_id)
    existing_request = connection.execute(
        "SELECT * FROM contract_assignments WHERE request_id=?",
        (normalized_request_id,),
    ).fetchone()
    if existing_request:
        return _record(existing_request) or {}
    existing = connection.execute(
        "SELECT * FROM contract_assignments WHERE contract_id=? AND character_id=?",
        (contract_id, character_id),
    ).fetchone()
    if existing:
        record = _record(existing) or {}
        if record.get("left_at"):
            raise ValueError("Personagem já abandonou este contrato")
        raise ValueError("Personagem ja atribuido")
    cursor = connection.execute(
        """
        INSERT INTO contract_assignments(request_id,contract_id,character_id,assigned_by,assigned_at,status,public_role)
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            normalized_request_id,
            contract_id,
            _text(character_id, "Personagem", maximum=120, required=True),
            assigned_by,
            _now(),
            "assigned",
            _text(public_role, "Papel público", maximum=180),
        ),
    )
    assignment = _record(connection.execute("SELECT * FROM contract_assignments WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}
    _event(
        connection,
        contract_id=contract_id,
        actor_id=assigned_by,
        actor_role=actor_role,
        event_type="character_assigned",
        title="Personagem atribuído",
        public_text=assignment["public_role"] or assignment["character_id"],
        character_id=assignment["character_id"],
        visibility="table",
        event_key=f"assignment:{contract_id}:{assignment['character_id']}:{request_id}",
    )
    return assignment


def add_assignment(database_path: Path, contract_id: int, *, request_id: str, character_id: str, assigned_by: str, public_role: str | None = None) -> dict[str, Any]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        contract = _contract(connection, contract_id)
        _ensure_open(contract)
        return _add_assignment_in_connection(connection, contract_id=contract_id, request_id=request_id, character_id=character_id, assigned_by=assigned_by, public_role=public_role)


def remove_assignment(database_path: Path, assignment_id: int, *, actor_id: str, reason: str | None = None) -> dict[str, Any]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        assignment = _record(connection.execute("SELECT * FROM contract_assignments WHERE id=?", (assignment_id,)).fetchone())
        if not assignment:
            raise ValueError("Atribuição inexistente")
        contract = _contract(connection, int(assignment["contract_id"]))
        _ensure_open(contract)
        if assignment.get("left_at"):
            return assignment
        now = _now()
        connection.execute("UPDATE contract_assignments SET status='left', left_at=? WHERE id=?", (now, assignment_id))
        _event(connection, contract_id=int(assignment["contract_id"]), actor_id=actor_id, actor_role="gm", event_type="character_left", title="Personagem removido do contrato", public_text=reason, private_text=reason, character_id=assignment["character_id"], visibility="table")
        return _record(connection.execute("SELECT * FROM contract_assignments WHERE id=?", (assignment_id,)).fetchone()) or {}


def link_scene(database_path: Path, contract_id: int, *, request_id: str, scene_id: int, created_by: str, objective_id: int | None = None, link_type: str = "other") -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    link_type = _status(link_type, SCENE_LINK_TYPES, "Tipo de vínculo")
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM contract_scene_links WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        contract = _contract(connection, contract_id)
        _ensure_open(contract)
        if not connection.execute("SELECT 1 FROM scenes WHERE id=?", (scene_id,)).fetchone():
            raise ValueError("Cena inexistente")
        if objective_id is not None:
            objective = _objective(connection, int(objective_id))
            if int(objective["contract_id"]) != contract_id:
                raise ValueError("Objetivo não pertence ao contrato")
        try:
            cursor = connection.execute(
                "INSERT INTO contract_scene_links(request_id,contract_id,scene_id,objective_id,link_type,created_by,created_at) VALUES(?,?,?,?,?,?,?)",
                (request_id, contract_id, scene_id, objective_id, link_type, created_by, _now()),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Cena já vinculada") from error
        link = _record(connection.execute("SELECT * FROM contract_scene_links WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}
        _event(connection, contract_id=contract_id, actor_id=created_by, actor_role="gm", event_type="scene_linked", title="Cena vinculada", public_text="Cena relacionada ao contrato.", scene_id=scene_id, objective_id=objective_id, visibility="table", event_key=f"scene-link:{contract_id}:{scene_id}:{objective_id}:{link_type}")
        return link, True


def unlink_scene(database_path: Path, link_id: int, *, actor_id: str) -> dict[str, Any]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        link = _record(connection.execute("SELECT * FROM contract_scene_links WHERE id=?", (link_id,)).fetchone())
        if not link:
            raise ValueError("Vínculo inexistente")
        contract_id = int(link["contract_id"])
        contract = _contract(connection, contract_id)
        _ensure_open(contract)
        connection.execute("DELETE FROM contract_scene_links WHERE id=?", (link_id,))
        _event(connection, contract_id=contract_id, actor_id=actor_id, actor_role="gm", event_type="scene_unlinked", title="Cena desvinculada", scene_id=link.get("scene_id"), visibility="gm")
        return link


def scene_contract_links(database_path: Path, scene_id: int, *, access_mode: str, profile_id: str | None = None) -> list[dict[str, Any]]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(
            """
            SELECT l.*, c.title AS contract_title, c.status AS contract_status, c.visibility AS contract_visibility,
                   o.title AS objective_title, o.revealed_to_players AS objective_revealed, o.status AS objective_status
            FROM contract_scene_links l
            JOIN contracts c ON c.id = l.contract_id
            LEFT JOIN contract_objectives o ON o.id = l.objective_id
            WHERE l.scene_id=?
            ORDER BY l.id
            """,
            (scene_id,),
        ).fetchall()
        result = []
        for row in rows:
            link = _record(row) or {}
            contract = _contract(connection, int(link["contract_id"]))
            if not _can_view_contract(connection, contract, access_mode=access_mode, profile_id=profile_id):
                continue
            if access_mode != "gm" and link.get("objective_id") and not link.get("objective_revealed"):
                continue
            result.append(link)
        return result


def record_scene_contract_event(database_path: Path, *, scene_id: int, actor_id: str, status: str, summary: str | None = None) -> list[dict[str, Any]]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        rows = connection.execute("SELECT DISTINCT contract_id FROM contract_scene_links WHERE scene_id=?", (scene_id,)).fetchall()
        events = []
        for row in rows:
            contract_id = int(row["contract_id"])
            events.append(_event(
                connection,
                contract_id=contract_id,
                actor_id=actor_id,
                actor_role="gm",
                event_type="linked_scene_closed",
                title="Cena vinculada encerrada",
                public_text=summary or f"Cena {scene_id} atualizada para {status}.",
                scene_id=scene_id,
                visibility="table",
                event_key=f"scene-closed:{contract_id}:{scene_id}:{status}",
            ))
        return events


def create_reward(database_path: Path, contract_id: int, *, request_id: str, actor_id: str, fields: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    request_id = _request_id(request_id)
    reward_type = _status(str(fields.get("reward_type") or "custom"), REWARD_TYPES, "Tipo de recompensa")
    visibility = _status(str(fields.get("visibility") or "table"), EVENT_VISIBILITIES, "Visibilidade")
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM contract_rewards WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing) or {}, False
        _contract(connection, contract_id)
        quantity = _number(fields.get("quantity"))
        reputation_amount = _number(fields.get("reputation_amount"))
        if quantity is not None and quantity < 0:
            raise ValueError("Quantidade inválida")
        cursor = connection.execute(
            """
            INSERT INTO contract_rewards(request_id,contract_id,reward_type,label,description,quantity,currency_type,
              item_source,item_name,reputation_faction,reputation_amount,visibility,status,created_by,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                request_id,
                contract_id,
                reward_type,
                _text(fields.get("label"), "Rótulo", maximum=180, required=True),
                _text(fields.get("description"), "Descrição"),
                quantity,
                _text(fields.get("currency_type") or ("moeda" if reward_type == "currency" else None), "Tipo de moeda", maximum=80),
                _text(fields.get("item_source"), "Fonte do item", maximum=500),
                _text(fields.get("item_name"), "Nome do item", maximum=180),
                _text(fields.get("reputation_faction"), "Facção", maximum=180),
                int(reputation_amount) if reputation_amount is not None else None,
                visibility,
                "proposed",
                actor_id,
                _now(),
            ),
        )
        reward = _record(connection.execute("SELECT * FROM contract_rewards WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}
        _event(connection, contract_id=contract_id, actor_id=actor_id, actor_role="gm", event_type="reward_created", title="Recompensa proposta", public_text=reward["label"] if visibility == "table" else None, private_text=reward["label"], reward_id=int(reward["id"]), visibility=visibility)
        return reward, True


def update_reward(database_path: Path, reward_id: int, *, expected_version: int, fields: dict[str, Any], actor_id: str) -> dict[str, Any]:
    allowed = {"label", "description", "quantity", "currency_type", "item_source", "item_name", "reputation_faction", "reputation_amount", "visibility", "status"}
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Campos inválidos: {', '.join(sorted(unknown))}")
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        reward = _reward(connection, reward_id)
        if int(reward["version"]) != int(expected_version):
            raise RuntimeError("versão desatualizada")
        if reward["status"] == "delivered":
            raise ValueError("Recompensa já entregue")
        updates: dict[str, Any] = {}
        for key, value in fields.items():
            if key == "visibility":
                updates[key] = _status(str(value), EVENT_VISIBILITIES, "Visibilidade")
            elif key == "status":
                updates[key] = _status(str(value), REWARD_STATUSES, "Status da recompensa")
            elif key in {"quantity", "reputation_amount"}:
                number = _number(value)
                updates[key] = int(number) if key == "reputation_amount" and number is not None else number
            elif key == "label":
                updates[key] = _text(value, "Rótulo", maximum=180, required=True)
            else:
                updates[key] = _text(value, key)
        if updates:
            clause = ", ".join(f"{key}=?" for key in updates)
            connection.execute(f"UPDATE contract_rewards SET {clause}, version=version+1 WHERE id=?", (*updates.values(), reward_id))
            _event(connection, contract_id=int(reward["contract_id"]), actor_id=actor_id, actor_role="gm", event_type="reward_updated", title="Recompensa revisada", reward_id=reward_id, visibility="gm", private_text=", ".join(sorted(updates)))
        return _record(connection.execute("SELECT * FROM contract_rewards WHERE id=?", (reward_id,)).fetchone()) or {}


def approve_reward(database_path: Path, reward_id: int, *, request_id: str, actor_id: str) -> dict[str, Any]:
    request_id = _request_id(request_id)
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        reward = _reward(connection, reward_id)
        if reward["status"] == "approved":
            return reward
        if reward["status"] != "proposed":
            raise ValueError("Recompensa não pode ser aprovada neste estado")
        now = _now()
        connection.execute("UPDATE contract_rewards SET status='approved', approved_at=?, approved_by=?, version=version+1 WHERE id=?", (now, actor_id, reward_id))
        _event(connection, contract_id=int(reward["contract_id"]), actor_id=actor_id, actor_role="gm", event_type="reward_approved", title="Recompensa aprovada", public_text=reward["label"] if reward["visibility"] == "table" else None, reward_id=reward_id, visibility=reward["visibility"], event_key=f"reward-approved:{reward_id}:{request_id}")
        return _record(connection.execute("SELECT * FROM contract_rewards WHERE id=?", (reward_id,)).fetchone()) or {}


def _load_character_state(connection: sqlite3.Connection, character_id: str) -> tuple[sqlite3.Row, dict[str, Any]]:
    row = connection.execute("SELECT * FROM character_states WHERE profile_id=?", (character_id,)).fetchone()
    if not row:
        raise ValueError("Estado do personagem ainda não foi inicializado")
    return row, json.loads(row["state_json"])


def _write_character_event(
    connection: sqlite3.Connection,
    *,
    character_id: str,
    actor_id: str,
    event_type: str,
    field: str,
    before: Any,
    after: Any,
    reason: str,
    session_id: str | None,
    game_session_id: int | None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO character_events(character_id,session_id,game_session_id,actor_id,actor_role,event_type,field,before_json,after_json,reason,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (character_id, session_id, game_session_id, actor_id, "gm", event_type, field, _json(before), _json(after), reason, _now()),
    )
    return int(cursor.lastrowid)


def _grant_currency(connection: sqlite3.Connection, *, character_id: str, amount: int | float, actor_id: str, reason: str, session_id: str | None, game_session_id: int | None) -> int:
    if amount <= 0:
        raise ValueError("Quantidade de moeda inválida")
    _row, state = _load_character_state(connection, character_id)
    before = state.get("coins") or 0
    after = before + amount
    state["coins"] = after
    connection.execute("UPDATE character_states SET state_json=?, version=version+1, updated_at=? WHERE profile_id=?", (_json(state), _now(), character_id))
    return _write_character_event(connection, character_id=character_id, actor_id=actor_id, event_type="change_coins", field="coins", before=before, after=after, reason=reason, session_id=session_id, game_session_id=game_session_id)


def _inventory_row(connection: sqlite3.Connection, character_id: str, item_path: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?", (character_id, item_path)).fetchone()
    if not row:
        return None
    record = dict(row)
    record["equipped"] = bool(record["equipped"])
    return record


def _grant_item(connection: sqlite3.Connection, *, character_id: str, item_path: str, item_title: str, quantity: int, actor_id: str, reason: str, session_id: str | None, game_session_id: int | None) -> int:
    if quantity <= 0:
        raise ValueError("Quantidade de item inválida")
    before = _inventory_row(connection, character_id, item_path)
    after = {
        **(before or {}),
        "profile_id": character_id,
        "item_path": item_path,
        "item_title": item_title,
        "quantity": (int(before.get("quantity") or 0) if before else 0) + quantity,
        "equipped": bool(before.get("equipped")) if before else False,
        "notes": before.get("notes") if before else None,
    }
    connection.execute(
        """
        INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,notes,updated_at)
        VALUES(?,?,?,?,?,?,?) ON CONFLICT(profile_id,item_path) DO UPDATE SET
          item_title=excluded.item_title,quantity=excluded.quantity,equipped=excluded.equipped,
          notes=excluded.notes,updated_at=excluded.updated_at
        """,
        (character_id, item_path, item_title, int(after["quantity"]), int(after["equipped"]), after.get("notes"), _now()),
    )
    after = _inventory_row(connection, character_id, item_path)
    return _write_character_event(connection, character_id=character_id, actor_id=actor_id, event_type="grant_item", field=f"inventory.{item_path}", before=before, after=after, reason=reason, session_id=session_id, game_session_id=game_session_id)


def _current_reputation(connection: sqlite3.Connection, *, campaign_id: str, faction_name: str, character_id: str | None, party_id: str | None) -> int:
    row = connection.execute(
        """
        SELECT resulting_value FROM reputation_ledger
        WHERE campaign_id=? AND faction_name=? AND COALESCE(character_id,'')=COALESCE(?, '')
          AND COALESCE(party_id,'')=COALESCE(?, '') AND reverted_at IS NULL
        ORDER BY id DESC LIMIT 1
        """,
        (campaign_id, faction_name, character_id, party_id),
    ).fetchone()
    return int(row["resulting_value"]) if row else 0


def _insert_reputation(
    connection: sqlite3.Connection,
    *,
    request_id: str,
    campaign_id: str,
    faction_name: str,
    delta: int,
    reason: str,
    actor_id: str,
    actor_role: ActorRole,
    contract_id: int | None,
    character_id: str | None = None,
    party_id: str | None = None,
) -> dict[str, Any]:
    existing = connection.execute("SELECT * FROM reputation_ledger WHERE request_id=?", (request_id,)).fetchone()
    if existing:
        return _record(existing) or {}
    before = _current_reputation(connection, campaign_id=campaign_id, faction_name=faction_name, character_id=character_id, party_id=party_id)
    resulting = before + int(delta)
    cursor = connection.execute(
        """
        INSERT INTO reputation_ledger(request_id,campaign_id,character_id,party_id,faction_name,delta,resulting_value,
          reason,contract_id,actor_id,actor_role,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (_request_id(request_id), campaign_id, character_id, party_id, faction_name, int(delta), resulting, reason, contract_id, actor_id, actor_role, _now()),
    )
    return _record(connection.execute("SELECT * FROM reputation_ledger WHERE id=?", (cursor.lastrowid,)).fetchone()) or {}


def deliver_reward(database_path: Path, reward_id: int, *, request_id: str, actor_id: str, character_ids: list[str] | None = None) -> dict[str, Any]:
    request_id = _request_id(request_id)
    character_ids = list(dict.fromkeys(str(item).strip() for item in (character_ids or []) if str(item).strip()))
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT response_json FROM contract_reward_deliveries WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _loads(existing["response_json"])
        reward = _reward(connection, reward_id)
        contract = _contract(connection, int(reward["contract_id"]))
        if contract["status"] not in {"completed", "failed", "abandoned"}:
            raise ValueError("Contrato ainda não está pronto para entrega de recompensas")
        if reward["status"] == "delivered":
            raise ValueError("Recompensa já entregue")
        if reward["status"] != "approved":
            raise ValueError("Recompensa precisa ser aprovada antes da entrega")
        reward_type = reward["reward_type"]
        quantity = _number(reward.get("quantity")) or 0
        reason = f"Recompensa do contrato: {contract['title']}"
        game_session_id = int(contract["session_id"]) if contract.get("session_id") is not None else active_game_session_id(connection, contract["campaign_id"])
        character_events: list[int] = []
        reputation_entries: list[dict[str, Any]] = []
        if reward_type == "currency":
            if not character_ids:
                raise ValueError("Destinatário inválido")
            for character_id in character_ids:
                character_events.append(_grant_currency(connection, character_id=character_id, amount=quantity, actor_id=actor_id, reason=reason, session_id=f"contract:{contract['id']}", game_session_id=game_session_id))
        elif reward_type == "item":
            if not character_ids:
                raise ValueError("Destinatário inválido")
            item_name = str(reward.get("item_name") or reward.get("label") or "").strip()
            item_path = str(reward.get("item_source") or f"custom-items/{item_name}").strip()
            if not item_name or not item_path:
                raise ValueError("Item inválido")
            for character_id in character_ids:
                character_events.append(_grant_item(connection, character_id=character_id, item_path=item_path, item_title=item_name, quantity=int(quantity or 1), actor_id=actor_id, reason=reason, session_id=f"contract:{contract['id']}", game_session_id=game_session_id))
        elif reward_type == "reputation":
            faction = str(reward.get("reputation_faction") or "").strip()
            delta = int(reward.get("reputation_amount") or quantity or 0)
            if not faction or delta == 0:
                raise ValueError("Reputação inválida")
            targets = character_ids or [""]
            for target in targets:
                reputation_entries.append(_insert_reputation(
                    connection,
                    request_id=f"{request_id}:rep:{target or 'party'}",
                    campaign_id=contract["campaign_id"],
                    faction_name=faction,
                    delta=delta,
                    reason=reason,
                    actor_id=actor_id,
                    actor_role="gm",
                    contract_id=int(contract["id"]),
                    character_id=target or None,
                    party_id=None if target else "group",
                ))
        else:
            if not character_ids and reward_type in {"favor", "access", "information", "custom"}:
                character_ids = []
        now = _now()
        connection.execute("UPDATE contract_rewards SET status='delivered', delivered_at=?, version=version+1 WHERE id=?", (now, reward_id))
        contract_event = _event(
            connection,
            contract_id=int(contract["id"]),
            actor_id=actor_id,
            actor_role="gm",
            event_type="reward_delivered",
            title="Recompensa entregue",
            public_text=reward["label"] if reward["visibility"] == "table" else None,
            private_text=reward["label"],
            reward_id=reward_id,
            visibility=reward["visibility"],
            event_key=f"reward-delivered:{reward_id}:{request_id}",
        )
        response = {
            "reward": _record(connection.execute("SELECT * FROM contract_rewards WHERE id=?", (reward_id,)).fetchone()),
            "character_event_ids": character_events,
            "reputation_entries": reputation_entries,
            "contract_event": contract_event,
        }
        connection.execute(
            "INSERT INTO contract_reward_deliveries(request_id,contract_id,reward_id,delivered_by,delivered_at,response_json) VALUES(?,?,?,?,?,?)",
            (request_id, int(contract["id"]), reward_id, actor_id, now, _json(response)),
        )
        return response


def apply_reputation(database_path: Path, *, request_id: str, campaign_id: str, faction_name: str, delta: int, reason: str, actor_id: str, actor_role: ActorRole, contract_id: int | None = None, character_id: str | None = None, party_id: str | None = "group") -> dict[str, Any]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        if contract_id:
            _contract(connection, int(contract_id))
        entry = _insert_reputation(connection, request_id=request_id, campaign_id=campaign_id, faction_name=_text(faction_name, "Facção", maximum=180, required=True) or faction_name, delta=int(delta), reason=_text(reason, "Motivo", maximum=500, required=True) or reason, actor_id=actor_id, actor_role=actor_role, contract_id=contract_id, character_id=character_id, party_id=None if character_id else party_id)
        if contract_id:
            _event(connection, contract_id=int(contract_id), actor_id=actor_id, actor_role=actor_role, event_type="reputation_changed", title="Reputação alterada", public_text=f"{faction_name}: {delta:+d}", visibility="table", event_key=f"reputation:{entry['id']}")
        return entry


def list_reputation(database_path: Path, *, campaign_id: str = "omnisvera", character_id: str | None = None, party_id: str | None = None) -> list[dict[str, Any]]:
    init_contract_play(database_path)
    clauses = ["campaign_id=?"]
    params: list[Any] = [campaign_id]
    if character_id is not None:
        clauses.append("character_id=?")
        params.append(character_id)
    if party_id is not None:
        clauses.append("party_id=?")
        params.append(party_id)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(
            f"SELECT * FROM reputation_ledger WHERE {' AND '.join(clauses)} ORDER BY id DESC",
            params,
        ).fetchall()
        return [_record(row) or {} for row in rows]


def revert_reputation(database_path: Path, ledger_id: int, *, actor_id: str) -> dict[str, Any]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT * FROM reputation_ledger WHERE id=?", (ledger_id,)).fetchone()
        if not row:
            raise ValueError("Registro de reputação inexistente")
        record = _record(row) or {}
        if record.get("reverted_at"):
            return record
        connection.execute("UPDATE reputation_ledger SET reverted_at=?, reverted_by=? WHERE id=?", (_now(), actor_id, ledger_id))
        if record.get("contract_id"):
            _event(connection, contract_id=int(record["contract_id"]), actor_id=actor_id, actor_role="gm", event_type="reputation_reverted", title="Reputação revertida", private_text=record["reason"], visibility="gm")
        return _record(connection.execute("SELECT * FROM reputation_ledger WHERE id=?", (ledger_id,)).fetchone()) or {}


def list_events(database_path: Path, contract_id: int, *, access_mode: str, profile_id: str | None = None) -> list[dict[str, Any]]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection:
        contract = _contract(connection, contract_id)
        if not _can_view_contract(connection, contract, access_mode=access_mode, profile_id=profile_id):
            raise ValueError("Contrato inexistente")
        rows = connection.execute("SELECT * FROM contract_events WHERE contract_id=? ORDER BY id DESC", (contract_id,)).fetchall()
        events = [_record(row) or {} for row in rows]
    events = [event for event in events if _can_view_event(event, access_mode=access_mode, profile_id=profile_id)]
    if access_mode != "gm":
        events = [{key: value for key, value in event.items() if key != "private_text"} for event in events]
    return events


def void_contract_event(database_path: Path, event_id: int, *, actor_id: str, reason: str) -> dict[str, Any]:
    init_contract_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        event = _record(connection.execute("SELECT * FROM contract_events WHERE id=?", (event_id,)).fetchone())
        if not event:
            raise ValueError("Evento inexistente")
        if event.get("voided_at"):
            return event
        connection.execute("UPDATE contract_events SET voided_at=?, voided_by=?, void_reason=? WHERE id=?", (_now(), actor_id, _text(reason, "Motivo", maximum=500, required=True), event_id))
        return _record(connection.execute("SELECT * FROM contract_events WHERE id=?", (event_id,)).fetchone()) or {}
