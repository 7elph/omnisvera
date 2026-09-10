from __future__ import annotations

import json
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from .dice_rolls import parse_formula, resolve_character_roll, roll_formula
from .session_ledger import append_session_ledger_event
from .combat_effects import change_hp, init_effects, effect_snapshot


RollMode = Literal["digital", "physical"]
Rng = Callable[[int, int], int]
RESOLUTION_TTL_MINUTES = 15


class CombatNotFoundError(ValueError):
    pass


class CombatExpiredError(ValueError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_combat(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS combat_attack_resolutions (
              resolution_id TEXT PRIMARY KEY,
              request_id TEXT NOT NULL UNIQUE,
              campaign_id TEXT NOT NULL,
              actor_character_id TEXT NOT NULL,
              actor_name TEXT NOT NULL,
              requested_by_id TEXT NOT NULL,
              requested_by_role TEXT NOT NULL,
              attack_id TEXT NOT NULL,
              attack_name TEXT NOT NULL,
              target_type TEXT NOT NULL CHECK (target_type IN ('character','token')),
              target_id TEXT NOT NULL,
              target_name TEXT NOT NULL,
              roll_mode TEXT NOT NULL CHECK (roll_mode IN ('digital','physical')),
              d20 INTEGER NOT NULL,
              attack_bonus INTEGER NOT NULL,
              attack_total INTEGER NOT NULL,
              target_ac INTEGER NOT NULL,
              result TEXT NOT NULL CHECK (result IN ('hit','miss')),
              damage_formula TEXT NOT NULL,
              damage_rolls_json TEXT NOT NULL,
              damage_modifier INTEGER NOT NULL,
              damage_total INTEGER NOT NULL,
              breakdown_json TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','confirmed')),
              created_at TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              confirmed_at TEXT,
              hp_before INTEGER,
              hp_after INTEGER,
              ledger_id INTEGER
            );
            CREATE INDEX IF NOT EXISTS idx_combat_attack_status
              ON combat_attack_resolutions(status, expires_at);
            """
        )


def _resolution_record(row: sqlite3.Row) -> dict[str, Any]:
    record = dict(row)
    record["damage_rolls"] = json.loads(record.pop("damage_rolls_json") or "[]")
    record["breakdown"] = json.loads(record.pop("breakdown_json") or "{}")
    record["confirmed"] = record["status"] == "confirmed"
    return record


def _validate_request_id(request_id: str) -> str:
    clean = str(request_id or "").strip()
    if not 8 <= len(clean) <= 120 or not re.fullmatch(r"[A-Za-z0-9._:-]+", clean):
        raise ValueError("request_id inválido")
    return clean


def _attack_entry(definition: dict[str, Any], attack_id: str) -> dict[str, Any]:
    attack = next(
        (entry for entry in definition.get("attacks") or [] if str(entry.get("id") or "") == attack_id),
        None,
    )
    if attack is None:
        raise CombatNotFoundError("Ataque não encontrado")
    if not attack.get("damage") or not attack.get("weapon_item_path"):
        raise ValueError("Equipe uma arma válida para realizar este ataque")
    return attack


def resolve_attack(
    database_path: Path,
    *,
    request_id: str,
    actor_character_id: str,
    actor_name: str,
    requested_by_id: str,
    requested_by_role: Literal["gm", "player"],
    definition: dict[str, Any],
    inventory: list[dict[str, Any]],
    attack_id: str,
    target: dict[str, Any],
    roll_mode: RollMode,
    physical_d20: int | None = None,
    attack_count: int = 1,
    physical_d20s: list[int] | None = None,
    rng: Rng | None = None,
    now: datetime | None = None,
) -> tuple[dict[str, Any], bool]:
    if requested_by_role != "gm" and requested_by_id != actor_character_id:
        raise PermissionError("Você não pode atacar por este personagem")
    request_id = _validate_request_id(request_id)
    attack_id = str(attack_id or "").strip()
    attack = _attack_entry(definition, attack_id)
    if type(attack_count) is not int or not 1 <= attack_count <= min(10, int(attack.get("attack_count", 1))):
        raise ValueError("Quantidade de ataques não permitida pela ficha")
    if roll_mode not in {"digital", "physical"}:
        raise ValueError("Modo de rolagem inválido")
    if roll_mode == "physical":
        dice = physical_d20s if physical_d20s is not None else [physical_d20]
        if physical_d20s is not None and physical_d20 is not None:
            raise ValueError("Informe d20 ou d20s, não ambos")
        if len(dice) != attack_count or any(type(value) is not int or not 1 <= value <= 20 for value in dice):
            raise ValueError("O resultado físico do d20 deve ficar entre 1 e 20")
        d20 = dice[0]
    else:
        if physical_d20 is not None or physical_d20s is not None:
            raise ValueError("Não informe d20 físico em uma rolagem digital")
        dice = []
    # Valid replays return stored dice, including after target death. Never reroll a request.
    init_combat(database_path)
    init_effects(database_path)
    with closing(_connect(database_path)) as connection:
        row = connection.execute("SELECT * FROM combat_attack_resolutions WHERE request_id=?", (request_id,)).fetchone()
        if row:
            record = _resolution_record(row)
            expected = (actor_character_id, requested_by_id, attack_id, target.get("type"), target.get("id"), roll_mode)
            actual = tuple(record[key] for key in ("actor_character_id", "requested_by_id", "attack_id", "target_type", "target_id", "roll_mode"))
            old_strikes = record["breakdown"].get("strikes", [{"d20": record["d20"]}])
            if actual != expected or len(old_strikes) != attack_count or (roll_mode == "physical" and [s["d20"] for s in old_strikes] != dice):
                raise ValueError("request_id já utilizado para outra resolução")
            return record, False
        effects_version = effect_snapshot(connection)["version"]
        if definition.get("effects_version", effects_version) != effects_version:
            raise ValueError("Os efeitos mudaram durante o cálculo. Tente novamente.")
    if roll_mode == "digital":
        dice = [int(roll_formula("1d20", rng)["total"]) for _ in range(attack_count)]
        d20 = dice[0]
    attack_spec = resolve_character_roll(definition, inventory, "attack", attack_id)
    attack_bonus = parse_formula(attack_spec.formula).modifier
    damage_formula = parse_formula(str(attack["damage"])).formula

    target_type = str(target.get("type") or "")
    target_id = str(target.get("id") or "").strip()
    target_name = str(target.get("name") or "Alvo").strip() or "Alvo"
    if target_type not in {"character", "token"} or not target_id:
        raise ValueError("Alvo inválido")
    target_ac = target.get("armor_class")
    current_hp = target.get("current_hp")
    if isinstance(target_ac, bool) or target_ac is None or int(target_ac) <= 0:
        raise ValueError("O alvo não possui CA válida")
    if isinstance(current_hp, bool) or current_hp is None:
        raise ValueError("O alvo não possui HP configurado")
    if int(current_hp) <= 0:
        raise ValueError("O alvo já está sem HP")

    attack_total = d20 + attack_bonus
    result = "hit" if attack_total >= int(target_ac) else "miss"
    strikes = []
    for die in dice:
        hit = die + attack_bonus >= int(target_ac)
        damage = roll_formula(damage_formula, rng) if hit else {
            "individual_results": [], "modifier": parse_formula(damage_formula).modifier, "total": 0,
        }
        strikes.append({"d20": die, "attack_total": die + attack_bonus, "result": "hit" if hit else "miss",
                        "damage_total": max(0, int(damage["total"])), "damage_rolls": damage["individual_results"]})
    result = "hit" if any(s["result"] == "hit" for s in strikes) else "miss"
    damage_roll = {"individual_results": [die for s in strikes for die in s["damage_rolls"]],
                   "modifier": parse_formula(damage_formula).modifier, "total": sum(s["damage_total"] for s in strikes)}
    equipment = [
        {
            "item_path": str(item.get("item_path") or ""),
            "item_title": str(item.get("item_title") or "Item"),
            "role": str(item.get("role") or "support"),
        }
        for item in attack.get("equipment") or []
    ]
    breakdown = {
        "strikes": strikes,
        "effects_version": effects_version,
        "effects": definition.get("active_effects", []),
        "attack": {
            "base_bonus": int(attack.get("base_attack_bonus") or 0),
            "equipment_bonus": int(attack.get("item_attack_bonus") or 0),
            "total_bonus": attack_bonus,
        },
        "damage": {
            "weapon_formula": next(
                (str(item.get("damage_formula")) for item in inventory if item.get("item_path") == attack.get("weapon_item_path")),
                damage_formula,
            ),
            "effective_formula": damage_formula,
            "rolls": list(damage_roll["individual_results"]),
            "modifier": int(damage_roll["modifier"]),
        },
        "equipment": equipment,
    }
    created = now or _now()
    if attack.get("effect_attack_bonus"):
        breakdown["attack"]["effect_bonus"] = int(attack["effect_attack_bonus"])
    resolution_id = f"attack:{secrets.token_hex(16)}"
    init_combat(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute(
            "SELECT * FROM combat_attack_resolutions WHERE request_id=?", (request_id,)
        ).fetchone()
        if existing:
            record = _resolution_record(existing)
            expected = (actor_character_id, requested_by_id, attack_id, target_type, target_id, roll_mode)
            actual = tuple(record[key] for key in (
                "actor_character_id", "requested_by_id", "attack_id", "target_type", "target_id", "roll_mode"
            ))
            old_strikes = record["breakdown"].get("strikes", [{"d20": record["d20"]}])
            if actual != expected or len(old_strikes) != attack_count or (roll_mode == "physical" and [s["d20"] for s in old_strikes] != dice):
                raise ValueError("request_id já utilizado para outra resolução")
            return record, False
        if effect_snapshot(connection)["version"] != effects_version:
            raise ValueError("Os efeitos mudaram durante o cálculo. Tente novamente.")
        connection.execute(
            """
            INSERT INTO combat_attack_resolutions(
              resolution_id,request_id,campaign_id,actor_character_id,actor_name,
              requested_by_id,requested_by_role,attack_id,attack_name,target_type,target_id,target_name,
              roll_mode,d20,attack_bonus,attack_total,target_ac,result,damage_formula,
              damage_rolls_json,damage_modifier,damage_total,breakdown_json,status,created_at,expires_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',?,?)
            """,
            (
                resolution_id, request_id, "omnisvera", actor_character_id, actor_name,
                requested_by_id, requested_by_role, attack_id, str(attack.get("name") or "Ataque"),
                target_type, target_id, target_name, roll_mode, d20, attack_bonus, attack_total,
                int(target_ac), result, damage_formula, json.dumps(damage_roll["individual_results"]),
                int(damage_roll["modifier"]), int(damage_roll["total"]),
                json.dumps(breakdown, ensure_ascii=False), created.isoformat(),
                (created + timedelta(minutes=RESOLUTION_TTL_MINUTES)).isoformat(),
            ),
        )
        row = connection.execute(
            "SELECT * FROM combat_attack_resolutions WHERE resolution_id=?", (resolution_id,)
        ).fetchone()
    if row is None:
        raise RuntimeError("A resolução do ataque não pôde ser armazenada")
    return _resolution_record(row), True


def confirm_attack_resolution(
    database_path: Path,
    *,
    resolution_id: str,
    requested_by_id: str,
    requested_by_role: Literal["gm", "player"],
    now: datetime | None = None,
) -> tuple[dict[str, Any], bool]:
    init_combat(database_path)
    init_effects(database_path)
    confirmed_at = now or _now()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM combat_attack_resolutions WHERE resolution_id=?", (resolution_id,)
        ).fetchone()
        if row is None:
            raise CombatNotFoundError("Resolução de ataque não encontrada")
        record = _resolution_record(row)
        if requested_by_role != "gm" and requested_by_id != record["requested_by_id"]:
            raise PermissionError("Você não pode confirmar esta resolução")
        if record["status"] == "confirmed":
            return record, False
        if confirmed_at > datetime.fromisoformat(record["expires_at"]):
            raise CombatExpiredError("A resolução do ataque expirou")
        if record["breakdown"].get("effects_version", 0) != effect_snapshot(connection)["version"]:
            raise CombatExpiredError("Os efeitos mudaram. Resolva o ataque novamente.")

        if record["target_type"] == "character":
            target_row = connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id=?", (record["target_id"],)
            ).fetchone()
            if target_row is None:
                raise CombatNotFoundError("Estado do personagem alvo não encontrado")
            target_state = json.loads(target_row["state_json"])
            hp_before = target_state.get("current_hp")
            if hp_before is None:
                raise ValueError("O alvo não possui HP configurado")
            if int(hp_before) <= 0:
                raise ValueError("O alvo já está sem HP")
        else:
            target_row = connection.execute(
                "SELECT current_hp FROM session_workspace_tokens WHERE id=?", (record["target_id"],)
            ).fetchone()
            if target_row is None:
                raise CombatNotFoundError("Token alvo não encontrado")
            hp_before = target_row["current_hp"]
            if hp_before is None:
                raise ValueError("O alvo não possui HP configurado")
            if int(hp_before) <= 0:
                raise ValueError("O alvo já está sem HP")
        hp_change = change_hp(connection, record["target_type"], record["target_id"], -int(record["damage_total"]), confirmed_at.isoformat())
        hp_after = hp_change["hp_after"]
        consumed = [e["id"] for e in record["breakdown"].get("effects", []) if e["duration"] == "next_attack"]
        for effect_id in consumed:
            connection.execute("UPDATE combat_effects SET active=0 WHERE id=?", (effect_id,))
        if consumed:
            connection.execute("UPDATE combat_effect_clock SET version=version+1 WHERE id=1")
        detail = {
            "temporary_hp_absorbed": hp_change["temporary_hp_absorbed"],
            "consumed_effects": consumed,
            "combat_action_id": record["resolution_id"],
            "actor_id": record["actor_character_id"],
            "actor_name": record["actor_name"],
            "attack_id": record["attack_id"],
            "attack_name": record["attack_name"],
            "target_type": record["target_type"],
            "target_id": record["target_id"],
            "target_name": record["target_name"],
            "roll_mode": record["roll_mode"],
            "d20": record["d20"],
            "attack_bonus": record["attack_bonus"],
            "attack_total": record["attack_total"],
            "target_ac": record["target_ac"],
            "result": record["result"],
            "damage_formula": record["damage_formula"],
            "damage_rolls": record["damage_rolls"],
            "damage_modifier": record["damage_modifier"],
            "damage_total": record["damage_total"],
            "breakdown": record["breakdown"],
            "hp_before": int(hp_before),
            "hp_after": hp_after,
        }
        ledger_id = append_session_ledger_event(
            connection,
            source_type="combat_action",
            source_id=record["resolution_id"],
            event_kind="action",
            actor_id=record["requested_by_id"],
            actor_name=record["actor_name"],
            actor_role=record["requested_by_role"],
            character_id=record["actor_character_id"],
            title=f"{record['actor_name']} atacou {record['target_name']} com {record['attack_name']}",
            detail=detail,
            visibility="table",
            created_at=confirmed_at.isoformat(),
        )
        connection.execute(
            """
            UPDATE combat_attack_resolutions
            SET status='confirmed',confirmed_at=?,hp_before=?,hp_after=?,ledger_id=?
            WHERE resolution_id=? AND status='pending'
            """,
            (confirmed_at.isoformat(), int(hp_before), hp_after, ledger_id, resolution_id),
        )
        updated = connection.execute(
            "SELECT * FROM combat_attack_resolutions WHERE resolution_id=?", (resolution_id,)
        ).fetchone()
    if updated is None:
        raise RuntimeError("A confirmação do ataque não pôde ser armazenada")
    return _resolution_record(updated), True
