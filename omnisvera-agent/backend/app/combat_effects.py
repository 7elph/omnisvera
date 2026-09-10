"""Explicit GM adjudication of temporary combat effects; no inferred spell rules."""
from __future__ import annotations

import copy
import json
import re
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .dice_rolls import parse_formula
from .session_ledger import append_session_ledger_event

MODIFIERS = {
    "attack_bonus",
    "damage_bonus",
    "armor_class_bonus",
    "extra_attacks",
    "hp_per_round",
    "strength_bonus",
    "movement_multiplier",
}
DURATIONS = {"rounds", "scene", "rest", "manual", "next_attack"}


def _attribute_modifier(score: int) -> int:
    if score <= 1:
        return -5
    if score <= 3:
        return -4
    if score <= 5:
        return -3
    if score <= 7:
        return -2
    if score <= 9:
        return -1
    if score <= 11:
        return 0
    if score <= 13:
        return 1
    if score <= 15:
        return 2
    if score <= 17:
        return 3
    if score <= 19:
        return 4
    return 5


def init_effects(path: Path) -> None:
    with closing(sqlite3.connect(path, timeout=30)) as db, db:
        db.executescript("""
          CREATE TABLE IF NOT EXISTS combat_effects (
            id TEXT PRIMARY KEY, target_type TEXT NOT NULL, target_id TEXT NOT NULL,
            data_json TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
          CREATE TABLE IF NOT EXISTS combat_effect_clock (
            id INTEGER PRIMARY KEY CHECK(id=1), round INTEGER NOT NULL, version INTEGER NOT NULL);
          INSERT OR IGNORE INTO combat_effect_clock(id,round,version) VALUES(1,1,0);
          CREATE TABLE IF NOT EXISTS combat_effect_commands (
            request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, response_json TEXT NOT NULL);
        """)
        db.execute("BEGIN IMMEDIATE")
        if "encounter_json" not in {row[1] for row in db.execute("PRAGMA table_info(combat_effect_clock)")}:
            db.execute("ALTER TABLE combat_effect_clock ADD COLUMN encounter_json TEXT NOT NULL DEFAULT '{}'")


def effect_snapshot(db: sqlite3.Connection) -> dict:
    clock = db.execute("SELECT round,version FROM combat_effect_clock WHERE id=1").fetchone()
    encounter = json.loads(db.execute("SELECT encounter_json FROM combat_effect_clock WHERE id=1").fetchone()[0])
    return {"round": clock[0], "version": clock[1], "encounter": encounter, "effects": [
        json.loads(row[0]) for row in db.execute("SELECT data_json FROM combat_effects WHERE active=1 ORDER BY id")
    ]}


def readeffects(path: Path) -> dict:
    init_effects(path)
    with closing(sqlite3.connect(path)) as db:
        return effect_snapshot(db)


def expire_rest_effects(db: sqlite3.Connection, character_id: str) -> None:
    cursor = db.execute("UPDATE combat_effects SET active=0 WHERE active=1 AND target_type='character' AND target_id=? AND json_extract(data_json,'$.duration')='rest'", (character_id,))
    if cursor.rowcount:
        db.execute("UPDATE combat_effect_clock SET version=version+1 WHERE id=1")


def change_hp(db: sqlite3.Connection, target_type: str, target_id: str, amount: int, now: str) -> dict:
    """Signed HP change, honoring temporary HP for damage and maximum HP for healing."""
    if target_type == "character":
        row = db.execute("SELECT state_json FROM character_states WHERE profile_id=?", (target_id,)).fetchone()
        if row is None:
            raise ValueError("Personagem não encontrado")
        state = json.loads(row[0])
        before, maximum = state.get("current_hp"), state.get("maximum_hp")
        temporary = int(state.get("temporary_hp") or 0)
        absorbed = min(temporary, -amount) if amount < 0 else 0
        state["temporary_hp"] = temporary - absorbed
        amount += absorbed
    else:
        row = db.execute("SELECT current_hp,maximum_hp FROM session_workspace_tokens WHERE id=? AND token_type!='location'", (target_id,)).fetchone()
        if row is None:
            raise ValueError("Criatura não encontrada")
        before, maximum = row
        absorbed = 0
    if before is None or maximum is None:
        raise ValueError("Alvo sem HP configurado")
    after = max(0, min(int(maximum), int(before) + amount))
    if target_type == "character":
        state["current_hp"] = after
        db.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?",
                   (json.dumps(state, ensure_ascii=False), now, target_id))
        db.execute("UPDATE session_workspace_tokens SET current_hp=?,updated_at=? WHERE character_id=?", (after, now, target_id))
    else:
        db.execute("UPDATE session_workspace_tokens SET current_hp=?,updated_at=? WHERE id=?", (after, now, target_id))
    return {"hp_before": before, "hp_after": after, "temporary_hp_absorbed": absorbed}


def _current_participant(encounter: dict) -> dict | None:
    participants = encounter.get("participants") or []
    if not participants:
        return None
    index = int(encounter.get("turn_index") or 0) % len(participants)
    return participants[index]


def _tick_round_effects(db: sqlite3.Connection, snapshot: dict, changes: list[dict], now: str) -> None:
    for effect in snapshot["effects"]:
        expire = False
        amount = effect["modifiers"].get("hp_per_round", 0)
        if amount:
            changes.append({"id": effect["id"], **change_hp(db, effect["target_type"], effect["target_id"], amount, now)})
        if effect["duration"] == "rounds":
            effect["rounds"] -= 1
            expire = effect["rounds"] <= 0
            db.execute("UPDATE combat_effects SET data_json=? WHERE id=?", (json.dumps(effect), effect["id"]))
        if expire:
            db.execute("UPDATE combat_effects SET active=0 WHERE id=?", (effect["id"],))
            changes.append({"expired": effect["id"]})


def effect_command(path: Path, *, actor_id: str, actor_role: str, request_id: str,
                   expected_version: int, action: str, payload: dict,
                   allow_player: bool = False) -> dict:
    if actor_role != "gm" and not (allow_player and actor_role == "player"):
        raise PermissionError("Somente o mestre controla efeitos e rodadas")
    if not 8 <= len(request_id) <= 120:
        raise ValueError("request_id inválido")
    fingerprint = json.dumps([actor_id, action, payload, expected_version], sort_keys=True)
    init_effects(path)
    with closing(sqlite3.connect(path, timeout=30)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute("SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?", (request_id,)).fetchone()
        if previous:
            if previous[0] != fingerprint:
                raise ValueError("request_id já utilizado com outro conteúdo")
            return json.loads(previous[1])
        snapshot = effect_snapshot(db)
        if snapshot["version"] != expected_version:
            raise ValueError("Estado dos efeitos mudou. Atualize antes de continuar.")
        now = datetime.now(timezone.utc).isoformat()
        changes = []
        if action in {"start", "initiative", "next_turn", "end"}:
            encounter = snapshot.get("encounter") or {}
            if action == "start" and encounter.get("active"):
                raise ValueError("Já existe um combate ativo. Encerre-o ou ajuste a iniciativa.")
            if action != "start" and not encounter.get("active"):
                raise ValueError("Nenhum combate ativo")
            if action == "end":
                encounter["active"] = False
            elif action == "next_turn":
                participants = encounter.get("participants") or []
                if not participants:
                    raise ValueError("O combate não possui participantes")
                current = _current_participant(encounter)
                requested_actor = payload.get("actor")
                if actor_role == "player":
                    if not isinstance(requested_actor, dict) or current is None or (
                        requested_actor.get("target_type"), requested_actor.get("target_id")
                    ) != (current.get("target_type"), current.get("target_id")):
                        raise PermissionError("Somente o participante atual pode encerrar este turno")
                previous_index = int(encounter.get("turn_index") or 0) % len(participants)
                next_index = (previous_index + 1) % len(participants)
                if next_index == 0:
                    _tick_round_effects(db, snapshot, changes, now)
                    db.execute("UPDATE combat_effect_clock SET round=round+1 WHERE id=1")
                encounter["turn_index"] = next_index
                encounter["turn_sequence"] = int(encounter.get("turn_sequence") or 0) + 1
                encounter["action_committed"] = False
                encounter["turn_started_at"] = now
                encounter["last_transition_by"] = actor_id
            else:
                participants = payload.get("participants") or []
                if not 1 <= len(participants) <= 100:
                    raise ValueError("Escolha os participantes do combate")
                seen = set()
                for participant in participants:
                    key = (participant.get("target_type"), participant.get("target_id"))
                    if key[0] not in {"character", "token"} or not key[1] or key in seen or type(participant.get("initiative")) is not int or not -99 <= participant["initiative"] <= 999:
                        raise ValueError("Participante ou iniciativa inválidos")
                    seen.add(key)
                context: dict[str, int] = {}
                if action == "start":
                    for field in ("game_session_id", "scene_id"):
                        value = payload.get(field)
                        if value is not None:
                            if type(value) is not int or value <= 0:
                                raise ValueError("Contexto de combate inválido")
                            context[field] = value
                else:
                    for field in ("game_session_id", "scene_id"):
                        if encounter.get(field) is not None:
                            context[field] = int(encounter[field])
                ordered = sorted(participants, key=lambda p: -p["initiative"])
                previous = _current_participant(encounter) if action == "initiative" else None
                turn_index = next(
                    (
                        index for index, participant in enumerate(ordered)
                        if previous
                        and (participant["target_type"], participant["target_id"])
                        == (previous.get("target_type"), previous.get("target_id"))
                    ),
                    0,
                )
                encounter = {
                    "active": True,
                    "map_id": str(payload.get("map_id") or encounter.get("map_id") or "default"),
                    "title": str(payload.get("title") or encounter.get("title") or "Combate")[:120],
                    "participants": ordered,
                    "turn_index": turn_index,
                    "turn_sequence": int(encounter.get("turn_sequence") or 0) + 1,
                    "action_committed": False,
                    "turn_started_at": now,
                    **context,
                }
                if action == "start":
                    db.execute("UPDATE combat_effect_clock SET round=1 WHERE id=1")
            db.execute("UPDATE combat_effect_clock SET encounter_json=? WHERE id=1", (json.dumps(encounter),))
            changes.append({"encounter": encounter})
        elif action == "apply":
            target_type, target_id = payload.get("target_type"), payload.get("target_id")
            if target_type not in {"character", "token"} or not target_id:
                raise ValueError("Alvo inválido")
            # Read/validate existence without changing HP or producing state events.
            table, column = ("character_states", "profile_id") if target_type == "character" else ("session_workspace_tokens", "id")
            if not db.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (target_id,)).fetchone():
                raise ValueError("Alvo não encontrado")
            label, source = str(payload.get("label") or "").strip(), str(payload.get("source") or "").strip()
            if not label or len(label) > 120 or not source or len(source) > 240:
                raise ValueError("Informe nome e origem do efeito")
            duration = payload.get("duration")
            rounds = payload.get("rounds")
            if duration not in DURATIONS or (duration == "rounds" and (type(rounds) is not int or not 1 <= rounds <= 999)):
                raise ValueError("Duração inválida")
            modifiers = payload.get("modifiers") or {}
            if not isinstance(modifiers, dict) or set(modifiers) - MODIFIERS or any(type(v) is not int or not -999 <= v <= 999 for v in modifiers.values()):
                raise ValueError("Modificador inválido")
            if not 0 <= modifiers.get("extra_attacks", 0) <= 9:
                raise ValueError("Ataques adicionais devem ficar entre 0 e 9")
            if modifiers.get("movement_multiplier", 0) not in {0, 1, 2, 3, 4}:
                raise ValueError("Multiplicador de movimento inválido")
            damage_bonus_formula = str(payload.get("damage_bonus_formula") or "").strip() or None
            if damage_bonus_formula is not None:
                damage_bonus_formula = parse_formula(damage_bonus_formula).formula
            combat_actor = payload.get("combat_actor")
            if combat_actor is not None:
                encounter = snapshot.get("encounter") or {}
                current = _current_participant(encounter)
                if not encounter.get("active") or current is None:
                    raise ValueError("Nenhum turno de combate ativo")
                actor_key = (combat_actor.get("target_type"), combat_actor.get("target_id")) if isinstance(combat_actor, dict) else (None, None)
                if actor_key != (current.get("target_type"), current.get("target_id")):
                    raise PermissionError("Esta ação não pertence ao participante do turno atual")
                if encounter.get("action_committed"):
                    raise ValueError("A ação principal deste turno já foi usada")
            resource = payload.get("resource")
            resource_change = None
            if resource is not None:
                if not isinstance(resource, dict) or resource.get("character_id") != actor_id:
                    raise ValueError("Recurso de habilidade inválido")
                resource_key = str(resource.get("key") or "").strip()
                resource_cost = resource.get("cost")
                if not resource_key or type(resource_cost) is not int or not 1 <= resource_cost <= 999:
                    raise ValueError("Custo de habilidade inválido")
                state_row = db.execute("SELECT state_json FROM character_states WHERE profile_id=?", (actor_id,)).fetchone()
                if state_row is None:
                    raise ValueError("Estado do personagem não encontrado")
                character_state = json.loads(state_row[0])
                resources = list(character_state.get("resources") or [])
                resource_index = next((index for index, item in enumerate(resources) if item.get("key") == resource_key), -1)
                if resource_index < 0 or int(resources[resource_index].get("current") or 0) < resource_cost:
                    raise ValueError("Recurso insuficiente para esta habilidade")
                before_resource = dict(resources[resource_index])
                resources[resource_index] = {**before_resource, "current": int(before_resource.get("current") or 0) - resource_cost}
                character_state["resources"] = resources
                db.execute(
                    "UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?",
                    (json.dumps(character_state, ensure_ascii=False), now, actor_id),
                )
                resource_change = {"before": before_resource, "after": resources[resource_index]}
            effect_id = payload.get("id") or f"effect:{uuid.uuid4().hex}"
            existing = next((e for e in snapshot["effects"] if e["id"] == effect_id), None)
            if payload.get("id") and (not existing or (existing["target_type"], existing["target_id"]) != (target_type, target_id)):
                raise ValueError("Efeito para edição não encontrado neste alvo")
            # Same source/name refreshes instead of silently stacking with itself.
            existing = existing or next((e for e in snapshot["effects"] if (e["target_type"], e["target_id"], e["label"], e["source"]) == (target_type, target_id, label, source)), None)
            if existing:
                effect_id = existing["id"]
            effect = dict(id=effect_id, target_type=target_type, target_id=target_id, label=label, source=source,
                          duration=duration, rounds=rounds if duration == "rounds" else None,
                          modifiers=modifiers, damage_bonus_formula=damage_bonus_formula, updated_at=now)
            db.execute("INSERT INTO combat_effects VALUES(?,?,?,?,1) ON CONFLICT(id) DO UPDATE SET data_json=excluded.data_json,active=1",
                       (effect_id, target_type, target_id, json.dumps(effect, ensure_ascii=False)))
            changes.append({"effect": effect, "previous": existing})
            if resource_change:
                changes.append({"resource": resource_change})
            if combat_actor is not None:
                encounter = snapshot.get("encounter") or {}
                encounter["action_committed"] = True
                encounter["last_action"] = {
                    "actor": combat_actor,
                    "label": label,
                    "kind": "ability",
                    "at": now,
                }
                db.execute("UPDATE combat_effect_clock SET encounter_json=? WHERE id=1", (json.dumps(encounter),))
        elif action in {"remove", "round", "scene", "rest"}:
            if action == "remove" and not any(e["id"] == payload.get("id") for e in snapshot["effects"]):
                raise ValueError("Efeito não encontrado")
            for effect in snapshot["effects"]:
                expire = (action == "remove" and effect["id"] == payload.get("id")) or (action == "scene" and effect["duration"] == "scene")
                expire = expire or (action == "rest" and effect["duration"] == "rest" and effect["target_type"] == payload.get("target_type") and effect["target_id"] == payload.get("target_id"))
                if action == "round":
                    amount = effect["modifiers"].get("hp_per_round", 0)
                    if amount:
                        changes.append({"id": effect["id"], **change_hp(db, effect["target_type"], effect["target_id"], amount, now)})
                    if effect["duration"] == "rounds":
                        effect["rounds"] -= 1
                        expire = effect["rounds"] <= 0
                        db.execute("UPDATE combat_effects SET data_json=? WHERE id=?", (json.dumps(effect), effect["id"]))
                if expire:
                    db.execute("UPDATE combat_effects SET active=0 WHERE id=?", (effect["id"],))
                    changes.append({"expired": effect["id"]})
            if action == "round":
                db.execute("UPDATE combat_effect_clock SET round=round+1 WHERE id=1")
        else:
            raise ValueError("Ação de efeito inválida")
        db.execute("UPDATE combat_effect_clock SET version=version+1 WHERE id=1")
        result = effect_snapshot(db)
        append_session_ledger_event(db, source_type="combat_effect", source_id=request_id, event_kind="state",
                                   actor_id=actor_id, actor_name="Mestre", actor_role="gm", character_id=None, title=f"Efeitos: {action}",
                                   detail={"action": action, "changes": changes, "round": result["round"]}, visibility="gm", created_at=now,
                                   game_session_id=(result.get("encounter") or {}).get("game_session_id"))
        db.execute("INSERT INTO combat_effect_commands VALUES(?,?,?)", (request_id, fingerprint, json.dumps(result)))
        return result


def apply_definition_effects(definition: dict, effects: list[dict]) -> dict:
    result = copy.deepcopy(definition)
    totals = {key: sum(e["modifiers"].get(key, 0) for e in effects) for key in MODIFIERS}
    result["active_effects"] = effects
    for attack in result.get("attacks") or []:
        attack["attack_bonus"] += totals["attack_bonus"]
        attack["effect_attack_bonus"] = totals["attack_bonus"]
        attack["attack_count"] = max(1, min(10, int(attack.get("attack_count", 1)) + totals["extra_attacks"]))
        if attack.get("damage") and totals["damage_bonus"]:
            parsed = parse_formula(attack["damage"])
            # Preserve all dice; only change the flat modifier.
            base = parsed.formula.split("+")[0].split("-")[0]
            modifier = parsed.modifier + totals["damage_bonus"]
            attack["damage"] = f"{base}{modifier:+d}" if modifier else base
        attack["extra_damage_formulas"] = [
            effect["damage_bonus_formula"] for effect in effects if effect.get("damage_bonus_formula")
        ]
    defenses = result.get("defenses") or {}
    if defenses.get("armor_class") is not None:
        defenses["armor_class"] += totals["armor_class_bonus"]
    if totals["strength_bonus"]:
        attributes = result.get("attributes") or {}
        base_attributes = result.get("base_attributes") or attributes
        if attributes.get("strength") is not None:
            attributes["strength"] = int(attributes["strength"]) + totals["strength_bonus"]
            result.setdefault("attribute_modifiers", {})["strength"] = _attribute_modifier(int(attributes["strength"]))
            result["base_attributes"] = base_attributes
    movement_multiplier = max([1] + [int(effect.get("modifiers", {}).get("movement_multiplier") or 1) for effect in effects])
    if movement_multiplier > 1 and result.get("movement"):
        match = re.search(r"\d+(?:[.,]\d+)?", str(result["movement"]))
        if match:
            value = float(match.group(0).replace(",", ".")) * movement_multiplier
            shown = str(int(value)) if value.is_integer() else str(value).replace(".", ",")
            result["movement"] = f"{shown} m · Velocidade ×{movement_multiplier}"
    return result
