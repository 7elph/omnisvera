from __future__ import annotations

import json
import re
import secrets
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Literal


RollVisibility = Literal["table", "gm", "owner", "private"]
RollType = Literal["free", "attribute", "saving_throw", "attack", "damage", "ability", "item"]
Rng = Callable[[int, int], int]

MAX_FORMULA_LENGTH = 32
MAX_DICE = 20
MAX_SIDES = 1000
MAX_ABS_MODIFIER = 1000
MAX_TARGET = 100_000
FORMULA_PATTERN = re.compile(r"^(?P<count>\d{1,2})d(?P<sides>\d{1,4})(?P<modifier>[+-]\d{1,4})?$", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedFormula:
    formula: str
    dice: str
    count: int
    sides: int
    modifier: int


@dataclass(frozen=True)
class RollSpec:
    roll_type: RollType
    label: str
    formula: str
    source: str
    source_id: str | None = None
    target_value: int | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_dice_rolls(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS dice_roll_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL UNIQUE,
                session_id TEXT,
                campaign_id TEXT NOT NULL,
                character_id TEXT,
                actor_id TEXT NOT NULL,
                actor_role TEXT NOT NULL,
                roll_type TEXT NOT NULL,
                label TEXT NOT NULL,
                formula TEXT NOT NULL,
                dice TEXT NOT NULL,
                modifier INTEGER NOT NULL,
                individual_results_json TEXT NOT NULL,
                subtotal INTEGER NOT NULL,
                total INTEGER NOT NULL,
                target_value INTEGER,
                target_hidden INTEGER NOT NULL DEFAULT 0,
                outcome TEXT,
                visibility TEXT NOT NULL,
                source TEXT NOT NULL,
                source_id TEXT,
                scene_id INTEGER,
                action_id INTEGER,
                reason TEXT,
                created_at TEXT NOT NULL,
                voided_at TEXT,
                voided_by TEXT,
                void_reason TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_dice_roll_events_created
              ON dice_roll_events(id DESC);
            CREATE INDEX IF NOT EXISTS idx_dice_roll_events_character
              ON dice_roll_events(character_id, id DESC);

            CREATE TABLE IF NOT EXISTS dice_roll_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL UNIQUE,
                session_id TEXT,
                campaign_id TEXT NOT NULL,
                character_id TEXT NOT NULL,
                requested_by TEXT NOT NULL,
                roll_type TEXT NOT NULL,
                label TEXT NOT NULL,
                formula TEXT NOT NULL,
                visibility TEXT NOT NULL,
                source TEXT NOT NULL,
                source_id TEXT,
                scene_id INTEGER,
                action_id INTEGER,
                target_value INTEGER,
                target_hidden INTEGER NOT NULL DEFAULT 0,
                reason TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                completed_at TEXT,
                completed_by TEXT,
                completion_request_id TEXT UNIQUE,
                roll_event_id INTEGER,
                FOREIGN KEY(roll_event_id) REFERENCES dice_roll_events(id)
            );

            CREATE INDEX IF NOT EXISTS idx_dice_roll_requests_character
              ON dice_roll_requests(character_id, status, id DESC);
            """
        )
        event_columns = {row[1] for row in connection.execute("PRAGMA table_info(dice_roll_events)")}
        request_columns = {row[1] for row in connection.execute("PRAGMA table_info(dice_roll_requests)")}
        if "target_hidden" not in event_columns:
            connection.execute("ALTER TABLE dice_roll_events ADD COLUMN target_hidden INTEGER NOT NULL DEFAULT 0")
        if "scene_id" not in event_columns:
            connection.execute("ALTER TABLE dice_roll_events ADD COLUMN scene_id INTEGER")
        if "action_id" not in event_columns:
            connection.execute("ALTER TABLE dice_roll_events ADD COLUMN action_id INTEGER")
        if "target_hidden" not in request_columns:
            connection.execute("ALTER TABLE dice_roll_requests ADD COLUMN target_hidden INTEGER NOT NULL DEFAULT 0")
        if "scene_id" not in request_columns:
            connection.execute("ALTER TABLE dice_roll_requests ADD COLUMN scene_id INTEGER")
        if "action_id" not in request_columns:
            connection.execute("ALTER TABLE dice_roll_requests ADD COLUMN action_id INTEGER")


def parse_formula(formula: str) -> ParsedFormula:
    if not isinstance(formula, str):
        raise ValueError("Fórmula de dados inválida")
    compact = re.sub(r"\s+", "", formula).lower()
    if not compact or len(compact) > MAX_FORMULA_LENGTH:
        raise ValueError("Fórmula de dados inválida")
    match = FORMULA_PATTERN.fullmatch(compact)
    if not match:
        raise ValueError("Use uma fórmula simples como 1d20+2")
    count = int(match.group("count"))
    sides = int(match.group("sides"))
    modifier = int(match.group("modifier") or 0)
    if not 1 <= count <= MAX_DICE:
        raise ValueError(f"A quantidade de dados deve ficar entre 1 e {MAX_DICE}")
    if not 2 <= sides <= MAX_SIDES:
        raise ValueError(f"O dado deve ter entre 2 e {MAX_SIDES} lados")
    if abs(modifier) > MAX_ABS_MODIFIER:
        raise ValueError(f"O modificador máximo é {MAX_ABS_MODIFIER}")
    normalized = f"{count}d{sides}{modifier:+d}" if modifier else f"{count}d{sides}"
    return ParsedFormula(normalized, f"{count}d{sides}", count, sides, modifier)


def roll_formula(formula: str, rng: Rng | None = None) -> dict[str, Any]:
    parsed = parse_formula(formula)
    roller = rng or secrets.SystemRandom().randint
    results = [int(roller(1, parsed.sides)) for _ in range(parsed.count)]
    if any(result < 1 or result > parsed.sides for result in results):
        raise ValueError("O gerador retornou um valor fora dos limites do dado")
    subtotal = sum(results)
    return {
        "formula": parsed.formula,
        "dice": parsed.dice,
        "modifier": parsed.modifier,
        "individual_results": results,
        "subtotal": subtotal,
        "total": subtotal + parsed.modifier,
    }


def _signed_formula(base: str, modifier: int | float | None) -> str:
    value = int(modifier or 0)
    return f"{base}{value:+d}" if value else base


def _integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"[-+]?\d+", str(value or ""))
    return int(match.group(0)) if match else None


def resolve_character_roll(
    definition: dict[str, Any],
    inventory: list[dict[str, Any]],
    roll_type: str,
    source_id: str | None,
) -> RollSpec:
    character_name = str(definition.get("name") or "Personagem")
    if roll_type == "attribute":
        key = str(source_id or "").strip().lower()
        labels = {
            "strength": "Força",
            "dexterity": "Destreza",
            "constitution": "Constituição",
            "intelligence": "Inteligência",
            "wisdom": "Sabedoria",
            "charisma": "Carisma",
        }
        if key not in labels:
            raise ValueError("Atributo inválido")
        modifier = (definition.get("attribute_modifiers") or {}).get(key)
        if modifier is None:
            raise ValueError("Este teste de atributo não está configurado")
        return RollSpec("attribute", f"{character_name} — Teste de {labels[key]}", _signed_formula("1d20", modifier), "character_attribute", key)

    if roll_type == "saving_throw":
        target = _integer((definition.get("defenses") or {}).get("saving_throw"))
        if target is None or target <= 0:
            raise ValueError("A Jogada de Proteção não está configurada")
        return RollSpec("saving_throw", f"{character_name} — Jogada de Proteção", "1d20", "character_saving_throw", "saving_throw", target)

    if roll_type == "attack":
        attacks = list(definition.get("attacks") or [])
        attack = next((item for item in attacks if item.get("id") == source_id), None)
        if attack is None and not source_id and attacks:
            attack = attacks[0]
        if attack is None or attack.get("attack_bonus") is None:
            raise ValueError("Este ataque não está configurado")
        attack_id = str(attack.get("id") or "attack")
        return RollSpec("attack", f"{character_name} — {attack.get('name') or 'Ataque'}", _signed_formula("1d20", attack.get("attack_bonus")), "character_attack", attack_id)

    if roll_type in {"damage", "item"}:
        candidates = [item for item in inventory if item.get("damage_formula")]
        item = next((entry for entry in candidates if entry.get("item_path") == source_id or str(entry.get("id")) == str(source_id)), None)
        if item is None and not source_id:
            item = next((entry for entry in candidates if entry.get("equipped")), None) or (candidates[0] if candidates else None)
        if item is None:
            raise ValueError("Este item não possui fórmula confirmada")
        formula = parse_formula(str(item["damage_formula"])).formula
        return RollSpec("damage" if roll_type == "damage" else "item", f"{character_name} — Dano de {item['item_title']}", formula, "inventory_item", str(item["item_path"]))

    if roll_type == "ability":
        raise ValueError("Esta habilidade ainda não possui fórmula estruturada confirmada")
    raise ValueError("Tipo de rolagem de personagem inválido")


def validate_target(target_value: int | None) -> int | None:
    if target_value is None:
        return None
    target = int(target_value)
    if not 1 <= target <= MAX_TARGET:
        raise ValueError(f"A dificuldade deve ficar entre 1 e {MAX_TARGET}")
    return target


def validate_visibility(visibility: str, actor_role: str, character_id: str | None) -> RollVisibility:
    allowed = {"table", "gm", "owner", "private"}
    if visibility not in allowed:
        raise ValueError("Visibilidade de rolagem inválida")
    if actor_role != "gm" and visibility == "gm":
        raise PermissionError("Jogadores não podem criar rolagens exclusivas do Mestre")
    if actor_role != "gm" and visibility == "owner" and not character_id:
        raise PermissionError("A visibilidade de proprietário exige um personagem")
    return visibility  # type: ignore[return-value]


def _roll_record(row: sqlite3.Row) -> dict[str, Any]:
    record = dict(row)
    record["individual_results"] = json.loads(record.pop("individual_results_json"))
    record["voided"] = bool(record.get("voided_at"))
    record["target_hidden"] = bool(record.get("target_hidden"))
    return record


def can_view_roll(record: dict[str, Any], *, access_mode: str, profile_id: str | None, actor_id: str) -> bool:
    if access_mode == "gm":
        return True
    visibility = record.get("visibility")
    if visibility == "table":
        return True
    if visibility == "gm":
        return False
    if visibility == "owner":
        return bool(profile_id and record.get("character_id") == profile_id)
    if visibility == "private":
        return record.get("actor_id") == actor_id
    return False


def create_roll(
    database_path: Path,
    *,
    request_id: str,
    campaign_id: str,
    actor_id: str,
    actor_role: str,
    roll_type: str,
    label: str,
    formula: str,
    visibility: str,
    character_id: str | None = None,
    session_id: str | None = None,
    target_value: int | None = None,
    target_hidden: bool = False,
    source: str = "free",
    source_id: str | None = None,
    scene_id: int | None = None,
    action_id: int | None = None,
    reason: str | None = None,
    rng: Rng | None = None,
    target_hidden_authorized: bool = False,
) -> tuple[dict[str, Any], bool]:
    request_id = str(request_id or "").strip()
    if not 8 <= len(request_id) <= 120 or not re.fullmatch(r"[A-Za-z0-9._:-]+", request_id):
        raise ValueError("request_id inválido")
    visibility = validate_visibility(visibility, actor_role, character_id)
    target = validate_target(target_value)
    if target_hidden and actor_role != "gm" and not target_hidden_authorized:
        raise PermissionError("Somente o Mestre pode ocultar a dificuldade")
    clean_label = str(label or "Rolagem").strip()[:160] or "Rolagem"
    clean_reason = str(reason or "").strip()[:500] or None
    parsed_formula = parse_formula(formula).formula
    init_dice_rolls(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM dice_roll_events WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            record = _roll_record(existing)
            if record["actor_id"] != actor_id:
                raise ValueError("request_id já utilizado")
            return record, False
        rolled = roll_formula(parsed_formula, rng)
        outcome = None if target is None else ("success" if rolled["total"] >= target else "failure")
        cursor = connection.execute(
            """
            INSERT INTO dice_roll_events(
              request_id,session_id,campaign_id,character_id,actor_id,actor_role,roll_type,label,
              formula,dice,modifier,individual_results_json,subtotal,total,target_value,target_hidden,outcome,
              visibility,source,source_id,scene_id,action_id,reason,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                request_id, session_id, campaign_id, character_id, actor_id, actor_role, roll_type,
                clean_label, rolled["formula"], rolled["dice"], rolled["modifier"],
                json.dumps(rolled["individual_results"]), rolled["subtotal"], rolled["total"],
                target, int(bool(target_hidden)), outcome, visibility, source, source_id,
                scene_id, action_id, clean_reason, _now(),
            ),
        )
        row = connection.execute("SELECT * FROM dice_roll_events WHERE id=?", (cursor.lastrowid,)).fetchone()
    if row is None:
        raise RuntimeError("A rolagem não pôde ser armazenada")
    return _roll_record(row), True


def get_roll(database_path: Path, roll_id: int) -> dict[str, Any] | None:
    init_dice_rolls(database_path)
    with closing(_connect(database_path)) as connection:
        row = connection.execute("SELECT * FROM dice_roll_events WHERE id=?", (roll_id,)).fetchone()
    return _roll_record(row) if row else None


def list_rolls(database_path: Path, limit: int = 50) -> list[dict[str, Any]]:
    init_dice_rolls(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT * FROM dice_roll_events ORDER BY id DESC LIMIT ?", (max(1, min(limit, 250)),)).fetchall()
    return [_roll_record(row) for row in rows]


def void_roll(database_path: Path, *, roll_id: int, actor_id: str, reason: str) -> dict[str, Any]:
    clean_reason = str(reason or "").strip()
    if not clean_reason or len(clean_reason) > 500:
        raise ValueError("Informe um motivo para anular a rolagem")
    init_dice_rolls(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT * FROM dice_roll_events WHERE id=?", (roll_id,)).fetchone()
        if row is None:
            raise ValueError("Rolagem não encontrada")
        if row["voided_at"]:
            raise ValueError("Rolagem já anulada")
        now = _now()
        connection.execute(
            "UPDATE dice_roll_events SET voided_at=?,voided_by=?,void_reason=? WHERE id=?",
            (now, actor_id, clean_reason, roll_id),
        )
        updated = connection.execute("SELECT * FROM dice_roll_events WHERE id=?", (roll_id,)).fetchone()
    if updated is None:
        raise RuntimeError("Falha ao anular a rolagem")
    return _roll_record(updated)


def _request_record(row: sqlite3.Row) -> dict[str, Any]:
    record = dict(row)
    record["target_hidden"] = bool(record.get("target_hidden"))
    return record


def create_roll_request(
    database_path: Path,
    *,
    request_id: str,
    campaign_id: str,
    character_id: str,
    requested_by: str,
    spec: RollSpec,
    visibility: str,
    session_id: str | None = None,
    scene_id: int | None = None,
    action_id: int | None = None,
    target_value: int | None = None,
    target_hidden: bool = False,
    reason: str | None = None,
    expires_in_hours: int = 24,
) -> tuple[dict[str, Any], bool]:
    request_id = str(request_id or "").strip()
    if not 8 <= len(request_id) <= 120 or not re.fullmatch(r"[A-Za-z0-9._:-]+", request_id):
        raise ValueError("request_id inválido")
    visibility = validate_visibility(visibility, "gm", character_id)
    target = validate_target(target_value if target_value is not None else spec.target_value)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=max(1, min(expires_in_hours, 168)))
    init_dice_rolls(database_path)
    with closing(_connect(database_path)) as connection, connection:
        existing = connection.execute("SELECT * FROM dice_roll_requests WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _request_record(existing), False
        cursor = connection.execute(
            """
            INSERT INTO dice_roll_requests(
              request_id,session_id,campaign_id,character_id,requested_by,roll_type,label,formula,
              visibility,source,source_id,scene_id,action_id,target_value,target_hidden,reason,status,created_at,expires_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',?,?)
            """,
            (
                request_id, session_id, campaign_id, character_id, requested_by, spec.roll_type,
                spec.label, parse_formula(spec.formula).formula, visibility, spec.source, spec.source_id,
                scene_id, action_id, target, int(bool(target_hidden)), str(reason or "").strip()[:500] or None,
                now.isoformat(), expires.isoformat(),
            ),
        )
        row = connection.execute("SELECT * FROM dice_roll_requests WHERE id=?", (cursor.lastrowid,)).fetchone()
    if row is None:
        raise RuntimeError("A solicitação não pôde ser armazenada")
    return _request_record(row), True


def list_roll_requests(database_path: Path, *, character_id: str | None = None, include_completed: bool = False) -> list[dict[str, Any]]:
    init_dice_rolls(database_path)
    clauses: list[str] = []
    params: list[Any] = []
    if character_id:
        clauses.append("character_id=?")
        params.append(character_id)
    if not include_completed:
        clauses.append("status='pending'")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(f"SELECT * FROM dice_roll_requests {where} ORDER BY id DESC LIMIT 100", params).fetchall()
    return [_request_record(row) for row in rows]


def complete_roll_request(
    database_path: Path,
    *,
    request_id: int,
    completion_request_id: str,
    actor_id: str,
    actor_role: str,
    rng: Rng | None = None,
) -> tuple[dict[str, Any], bool]:
    init_dice_rolls(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT * FROM dice_roll_requests WHERE id=?", (request_id,)).fetchone()
        if row is None:
            raise ValueError("Solicitação de rolagem não encontrada")
        request = _request_record(row)
        if request["status"] == "completed":
            if request.get("completion_request_id") == completion_request_id and request.get("roll_event_id"):
                existing = get_roll(database_path, int(request["roll_event_id"]))
                if existing:
                    return existing, False
            raise ValueError("Esta solicitação já foi concluída")
        if request["status"] == "processing":
            if request.get("completion_request_id") == completion_request_id:
                existing = connection.execute("SELECT * FROM dice_roll_events WHERE request_id=?", (completion_request_id,)).fetchone()
                if existing:
                    event = _roll_record(existing)
                    connection.execute(
                        "UPDATE dice_roll_requests SET status='completed',completed_at=?,completed_by=?,roll_event_id=? WHERE id=?",
                        (_now(), actor_id, event["id"], request_id),
                    )
                    return event, False
            raise ValueError("Esta solicitação já está sendo processada")
        if request["status"] != "pending":
            raise ValueError("Esta solicitação não está disponível")
        if datetime.fromisoformat(request["expires_at"]) <= datetime.now(timezone.utc):
            connection.execute("UPDATE dice_roll_requests SET status='expired' WHERE id=?", (request_id,))
            raise ValueError("Esta solicitação expirou")
        if actor_role != "gm" and actor_id != request["character_id"]:
            raise PermissionError("Esta solicitação pertence a outro personagem")
        if actor_role != "gm" and request["visibility"] == "gm":
            raise PermissionError("Esta solicitação é reservada ao Mestre")
        connection.execute(
            "UPDATE dice_roll_requests SET status='processing',completion_request_id=? WHERE id=? AND status='pending'",
            (completion_request_id, request_id),
        )
    try:
        event, created = create_roll(
            database_path,
            request_id=completion_request_id,
            campaign_id=request["campaign_id"],
            character_id=request["character_id"],
            actor_id=actor_id,
            actor_role=actor_role,
            roll_type=request["roll_type"],
            label=request["label"],
            formula=request["formula"],
            visibility=request["visibility"],
            session_id=request.get("session_id"),
            target_value=request.get("target_value"),
            target_hidden=bool(request.get("target_hidden")),
            source="roll_request",
            source_id=str(request_id),
            scene_id=request.get("scene_id"),
            action_id=request.get("action_id"),
            reason=request.get("reason"),
            rng=rng,
            target_hidden_authorized=True,
        )
    except Exception:
        with closing(_connect(database_path)) as connection, connection:
            connection.execute(
                "UPDATE dice_roll_requests SET status='pending',completion_request_id=NULL WHERE id=? AND status='processing' AND completion_request_id=?",
                (request_id, completion_request_id),
            )
        raise
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        current = connection.execute("SELECT status,completion_request_id,roll_event_id FROM dice_roll_requests WHERE id=?", (request_id,)).fetchone()
        if current is None:
            raise RuntimeError("Solicitação desapareceu durante a conclusão")
        if current["status"] == "completed":
            if current["completion_request_id"] == completion_request_id:
                return event, False
            raise ValueError("Esta solicitação já foi concluída")
        connection.execute(
            """
            UPDATE dice_roll_requests SET status='completed',completed_at=?,completed_by=?,
              completion_request_id=?,roll_event_id=? WHERE id=? AND status='processing' AND completion_request_id=?
            """,
            (_now(), actor_id, completion_request_id, event["id"], request_id, completion_request_id),
        )
    return event, created
