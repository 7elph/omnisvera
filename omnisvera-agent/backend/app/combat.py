from __future__ import annotations

import json
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from .character_play import available_attack_weapons
from .dice_rolls import parse_formula, resolve_character_roll, resolve_item_damage_formula, roll_formula
from .session_ledger import append_session_ledger_event
from .combat_effects import change_hp, init_effects, effect_snapshot
from .battle_mode import require_battle_turn, commit_battle_action


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


def _participant_effect_state(effects: list[dict], actor_id: str, target_type: str, target_id: str) -> dict[str, dict]:
    """Active effect modifiers on the attacker and the target, by effect id.

    Only these two participants can move the numbers of a pending resolution,
    so only their effects gate confirmation — never a third party's buff.
    """
    participants = {("character", actor_id), (target_type, target_id)}
    return {
        effect["id"]: dict(effect.get("modifiers") or {})
        for effect in effects
        if (effect.get("target_type"), effect.get("target_id")) in participants and effect.get("id")
    }


def _assert_participant_effects_unchanged(current_effects: list[dict], breakdown: dict,
                                          actor_id: str, target_type: str, target_id: str,
                                          current_version: int) -> None:
    before = breakdown.get("effect_ids")
    if not isinstance(before, dict):
        # Records stored before scoped tracking fall back to the global version.
        if breakdown.get("effects_version", 0) != current_version:
            raise CombatExpiredError("Os efeitos mudaram. Resolva o ataque novamente.")
        return
    now = _participant_effect_state(current_effects, actor_id, target_type, target_id)
    if set(now) - set(before):
        raise CombatExpiredError("Um novo efeito entrou no atacante ou no alvo. Resolva o ataque novamente.")
    for effect_id, modifiers in before.items():
        if effect_id not in now:
            raise CombatExpiredError("Um efeito ativo expirou ou foi removido. Resolva o ataque novamente.")
        if now[effect_id] != modifiers:
            raise CombatExpiredError("Um efeito ativo mudou. Resolva o ataque novamente.")


def _resolution_record(row: sqlite3.Row) -> dict[str, Any]:
    record = dict(row)
    record["damage_rolls"] = json.loads(record.pop("damage_rolls_json") or "[]")
    record["breakdown"] = json.loads(record.pop("breakdown_json") or "{}")
    record["confirmed"] = record["status"] == "confirmed"
    return record


def get_attack_resolution(database_path: Path, resolution_id: str) -> dict[str, Any]:
    """Load a stored attack resolution by id (for technique follow-ups)."""
    init_combat(database_path)
    with closing(_connect(database_path)) as connection:
        row = connection.execute(
            "SELECT * FROM combat_attack_resolutions WHERE resolution_id=?", (resolution_id,)
        ).fetchone()
    if row is None:
        raise CombatNotFoundError("Resolução de ataque não encontrada")
    return _resolution_record(row)


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


def monster_attack_definition(token: dict, attack_id: str) -> dict:
    """Separate persisted numeric damage from textual riders, never execute prose."""
    attacks = (token.get("sheet") or {}).get("attacks") or []
    if not attack_id.isdecimal() or int(attack_id) >= len(attacks):
        raise ValueError("Ataque não encontrado na ficha da criatura")
    attack = attacks[int(attack_id)]
    damage = str(attack.get("damage") or "").strip()
    manual_effects = []
    # Catalogue example: 1d8 + Veneno. Reject extra dice/unsupported arithmetic
    # rather than silently dropping it as an effect.
    match = re.fullmatch(r"(\d+\s*[dD]\s*\d+(?:\s*[+-]\s*\d+)?)\s*\+\s*([^\W\d_][^\d+*/=]*)", damage)
    if match:
        damage, effect = match.groups()
        manual_effects.append(effect.strip())
    try:
        damage = parse_formula(damage).formula
        bonus_raw = attack.get("bonus")
        if isinstance(bonus_raw, bool) or not re.fullmatch(r"[+-]?\d+", str(bonus_raw).strip()):
            raise ValueError("Bônus ausente")
        bonus = int(str(bonus_raw).strip())
    except ValueError as error:
        raise ValueError(f"O ataque {attack.get('name') or attack_id} está incompleto na ficha da criatura. O Mestre precisa revisar seu dano e bônus no cadastro; não é necessário digitar uma fórmula durante o ataque.") from error
    return {"name": token["name"], "attacks": [{
        "id": attack_id, "name": attack.get("name") or "Ataque", "damage": damage,
        "attack_bonus": bonus, "base_attack_bonus": bonus,
        "weapon_item_path": f"token:{token['id']}:attack:{attack_id}",
        "manual_effects": manual_effects,
    }]}


def bone_dagger_definition(definition: dict) -> dict:
    """Campaign basic attack: Session 6, 01:34:47–01:34:53, 1d4 without damage bonus.

    Keep the character's reviewed ranged hit bonus, not a guessed modifier.
    Torch/burning is a separate GM adjudication, never bundled into this attack.
    """
    ability = next((a for a in definition.get('session_abilities', []) if a.get('id') == 'adaga-de-osso'), None)
    ranged = next((a for a in definition.get('attacks', []) if a.get('id') == 'ranged'), None)
    if definition.get('id') != 'morthak' or not ability or ability.get('blocked'):
        raise ValueError('Adaga de Osso indisponível nesta ficha')
    if not ranged or type(ranged.get('attack_bonus')) is not int:
        raise ValueError('Confira o bônus de acerto à distância de Morthak antes de atacar')
    return {**definition, 'attacks': [{**ranged, 'id': 'adaga-de-osso', 'name': 'Adaga de Osso',
        'damage': '1d4', 'weapon_item_path': 'technique:adaga-de-osso', 'attack_count': 1}]}


def magic_missile_definition(definition: dict, resources: list[dict]) -> dict:
    """Reviewed OD1 Aprimorado p.112, single-projectile levels only.

    Preserve the campaign's existing per-spell resource instead of inventing
    or refilling daily slots. Range/line of sight and magical defenses remain
    Master adjudications, explicitly displayed before confirmation.
    """
    level = definition.get("level")
    if definition.get("id") not in {"morthak", "dorn7"} or type(level) is not int or not 1 <= level <= 3:
        raise ValueError("Mísseis automáticos conferidos apenas para Morthak e Dorn nos níveis 1–3")
    ability = next((a for a in definition.get("session_abilities", []) if a.get("id") == "misseis-magicos"), None)
    if not ability or ability.get("blocked"):
        raise ValueError("Magia indisponível nesta ficha")
    key = str((ability.get("uses") or {}).get("resource_key") or "").replace("-", "_")
    resource = next((r for r in resources if r.get("key") == key), None)
    if not resource:
        raise ValueError("Contador de Mísseis Mágicos não configurado")
    return {**definition, "active_effects": [], "attacks": [{
        "id": "misseis-magicos", "name": "Mísseis Mágicos", "damage": f"1d4+{level}",
        "attack_bonus": 0, "weapon_item_path": "spell:misseis-magicos", "automatic_hit": True,
        "resource_cost": {"key": key, "amount": 1},
        "manual_effects": [f"Conferir linha de visão, alcance de {10 + 3 * level} m e defesas mágicas antes de aplicar. Escudo arcano pode impedir este dano."],
    }]}


def _resolve_weapon_override(
    definition: dict[str, Any],
    inventory: list[dict[str, Any]],
    attack: dict[str, Any],
    attack_id: str,
    weapon_item_path: str | None,
) -> dict[str, Any]:
    """Optional explicit weapon for an attack slot.

    Defaults preserve the legacy auto-pick. An explicit path must be an
    equipped weapon with damage valid for the slot; otherwise it is rejected
    rather than silently falling back.
    """
    if weapon_item_path is None:
        return attack
    wanted = str(weapon_item_path).strip()
    candidates = available_attack_weapons(inventory, attack_id)
    weapon = next((item for item in candidates if str(item.get("item_path") or "") == wanted), None)
    if weapon is None:
        raise ValueError("Arma não disponível para este ataque (equipe-a e confira o dano)")
    attack = dict(attack)
    attack["damage"] = resolve_item_damage_formula(
        {"item_effects": definition.get("item_effects")}, weapon
    )
    attack["weapon_item_path"] = str(weapon.get("item_path") or "")
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
    weapon_item_path: str | None = None,
    controlling_character_id: str | None = None,
    guard_effect_id: str | None = None,
    rng: Rng | None = None,
    now: datetime | None = None,
) -> tuple[dict[str, Any], bool]:
    if requested_by_role != "gm" and requested_by_id != actor_character_id and requested_by_id != controlling_character_id:
        raise PermissionError("Você não pode atacar por este personagem")
    if guard_effect_id and requested_by_role != 'gm':
        raise PermissionError('Somente o Mestre pode confirmar interposição')
    if guard_effect_id and (target.get('type'), target.get('id'), attack_count) != ('character', 'dorn7', 1):
        raise ValueError('Interposição permite somente um ataque dirigido a Dorn')
    request_id = _validate_request_id(request_id)
    attack_id = str(attack_id or "").strip()
    attack = _attack_entry(definition, attack_id)
    attack = _resolve_weapon_override(definition, inventory, attack, attack_id, weapon_item_path)
    automatic_hit = bool(attack.get("automatic_hit"))
    if automatic_hit and roll_mode != "digital":
        raise ValueError("Esta magia automatizada requer modo Digital; no modo Físico use a resolução assistida")
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
            if record['breakdown'].get('guard_effect_id') != guard_effect_id:
                raise ValueError('request_id já utilizado para outra interposição')
            expected = (actor_character_id, requested_by_id, attack_id, target.get("type"), target.get("id"), roll_mode, str(attack.get("weapon_item_path") or ""))
            actual = tuple(record[key] for key in ("actor_character_id", "requested_by_id", "attack_id", "target_type", "target_id", "roll_mode")) + (str((record.get("breakdown") or {}).get("attack", {}).get("weapon_item_path") or ""),)
            old_strikes = record["breakdown"].get("strikes", [{"d20": record["d20"]}])
            if actual != expected or len(old_strikes) != attack_count or (roll_mode == "physical" and [s["d20"] for s in old_strikes] != dice):
                raise ValueError("request_id já utilizado para outra resolução")
            return record, False
        current_snapshot = effect_snapshot(connection)
        guard = next((e for e in current_snapshot['effects'] if e['id'] == guard_effect_id and e.get('protocol') == 'guard'), None)
        if guard_effect_id and not guard:
            raise ValueError('Guarda consumida ou expirada')
        require_battle_turn(connection, current_snapshot, actor_character_id, target.get('type'), target.get('id'), attack_count=attack_count, attack_limit=int(attack.get('attack_count', 1)))
        effects_version = current_snapshot["version"]
        if definition.get("effects_version", effects_version) != effects_version:
            raise ValueError("Os efeitos mudaram durante o cálculo. Tente novamente.")
        resource_cost = None
        if attack.get("resource_cost"):
            row = connection.execute("SELECT state_json,version FROM character_states WHERE profile_id=?", (actor_character_id,)).fetchone()
            if row is None:
                raise ValueError("Estado do conjurador não encontrado")
            cost = attack["resource_cost"]
            resource = next((r for r in json.loads(row["state_json"]).get("resources", []) if r.get("key") == cost["key"]), None)
            if not resource or int(resource.get("current", 0)) < cost["amount"]:
                raise ValueError("Sem usos disponíveis para esta magia")
            resource_cost = {**cost, "state_version": row["version"]}
    if roll_mode == "digital":
        dice = [0] if automatic_hit else [int(roll_formula("1d20", rng)["total"]) for _ in range(attack_count)]
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
        hit = automatic_hit or die + attack_bonus >= int(target_ac)
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
        "guard_effect_id": guard_effect_id,
        "guard_ally_id": guard.get('ally_id') if guard else None,
        "attack_limit": int(attack.get("attack_count", 1)),
        "automatic_hit": automatic_hit,
        "resource_cost": resource_cost,
        "manual_effects": list(attack.get("manual_effects") or []) if result == "hit" else [],
        "strikes": strikes,
        "effects_version": effects_version,
        "effect_ids": _participant_effect_state(current_snapshot["effects"], actor_character_id, target_type, target_id),
        "effects": definition.get("active_effects", []),
        "attack": {
            "base_bonus": int(attack.get("base_attack_bonus") or 0),
            "equipment_bonus": int(attack.get("item_attack_bonus") or 0),
            "total_bonus": attack_bonus,
            "weapon_item_path": str(attack.get("weapon_item_path") or ""),
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
            if record['breakdown'].get('guard_effect_id') != guard_effect_id:
                raise ValueError('request_id já utilizado para outra interposição')
            expected = (actor_character_id, requested_by_id, attack_id, target_type, target_id, roll_mode, str(attack.get("weapon_item_path") or ""))
            actual = tuple(record[key] for key in (
                "actor_character_id", "requested_by_id", "attack_id", "target_type", "target_id", "roll_mode"
            )) + (str((record.get("breakdown") or {}).get("attack", {}).get("weapon_item_path") or ""),)
            old_strikes = record["breakdown"].get("strikes", [{"d20": record["d20"]}])
            if actual != expected or len(old_strikes) != attack_count or (roll_mode == "physical" and [s["d20"] for s in old_strikes] != dice):
                raise ValueError("request_id já utilizado para outra resolução")
            return record, False
        if effect_snapshot(connection)["version"] != effects_version:
            raise ValueError("Os efeitos mudaram durante o cálculo. Tente novamente.")
        if guard_effect_id:
            # Consume atomically with the preview, before any attack is resolved.
            connection.execute('UPDATE combat_effects SET active=0 WHERE id=?', (guard_effect_id,))
            connection.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
            breakdown['effects_version'] += 1
            breakdown['effect_ids'] = _participant_effect_state([e for e in current_snapshot['effects'] if e['id'] != guard_effect_id], actor_character_id, target_type, target_id)
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


def list_pending_attack_resolutions(
    database_path: Path, *, requested_by_id: str, requested_by_role: str,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Recover only still-confirmable previews, never another player's actions."""
    instant = now or _now()
    with closing(_connect(database_path)) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'combat_attack_resolutions', 'combat_effect_clock'}.issubset(tables):
            return []
        rows = connection.execute(
            "SELECT * FROM combat_attack_resolutions WHERE status='pending' "
            "AND (?='gm' OR (requested_by_id=? AND requested_by_role='player')) ORDER BY created_at DESC LIMIT 100",
            (requested_by_role, requested_by_id),
        ).fetchall()
        live_snapshot = effect_snapshot(connection)
        pending = []
        for row in rows:
            record = _resolution_record(row)
            if datetime.fromisoformat(record["expires_at"]) < instant:
                continue
            try:
                _assert_participant_effects_unchanged(
                    live_snapshot["effects"], record["breakdown"],
                    record["actor_character_id"], record["target_type"], record["target_id"],
                    live_snapshot["version"],
                )
            except CombatExpiredError:
                continue
            cost = record["breakdown"].get("resource_cost")
            if cost:
                caster = connection.execute("SELECT version FROM character_states WHERE profile_id=?", (record["actor_character_id"],)).fetchone()
                if caster is None or caster["version"] != cost["state_version"]:
                    continue
            pending.append(record)
        return pending


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
        current_snapshot = effect_snapshot(connection)
        strike_count = len(record['breakdown'].get('strikes') or [record])
        attack_limit = int(record['breakdown'].get('attack_limit') or 1)
        require_battle_turn(connection, current_snapshot, record['actor_character_id'], record['target_type'], record['target_id'], attack_count=strike_count, attack_limit=attack_limit)
        if confirmed_at > datetime.fromisoformat(record["expires_at"]):
            raise CombatExpiredError("A resolução do ataque expirou")
        live_snapshot = effect_snapshot(connection)
        _assert_participant_effects_unchanged(
            live_snapshot["effects"], record["breakdown"],
            record["actor_character_id"], record["target_type"], record["target_id"],
            live_snapshot["version"],
        )
        resource_cost = record["breakdown"].get("resource_cost")
        if resource_cost:
            caster = connection.execute("SELECT state_json,version FROM character_states WHERE profile_id=?", (record["actor_character_id"],)).fetchone()
            if caster is None or caster["version"] != resource_cost["state_version"]:
                raise CombatExpiredError("A ficha ou os recursos mudaram. Confira a magia novamente.")
            caster_state = json.loads(caster["state_json"])
            resource = next((r for r in caster_state.get("resources", []) if r.get("key") == resource_cost["key"]), None)
            if not resource or int(resource.get("current", 0)) < resource_cost["amount"]:
                raise ValueError("Sem usos disponíveis para esta magia")
            resource["current"] -= resource_cost["amount"]
            connection.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?",
                (json.dumps(caster_state, ensure_ascii=False), confirmed_at.isoformat(), record["actor_character_id"]))

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
        dorn_disabled = False
        dorn_profile = record["target_id"] if record["target_type"] == "character" else None
        if dorn_profile is None:
            token_owner = connection.execute(
                "SELECT character_id FROM session_workspace_tokens WHERE id=?", (record["target_id"],)
            ).fetchone()
            dorn_profile = token_owner["character_id"] if token_owner else None
        if dorn_profile == "dorn7" and int(hp_after) == 0:
            # Constructo a 0 PV: desativa e zera a ficha junto (fonte única).
            # Reparo = curar a ficha acima de 0 (limpa o Desativado) + devolver PV ao pin.
            dorn_row = connection.execute(
                "SELECT state_json FROM character_states WHERE profile_id='dorn7'"
            ).fetchone()
            if dorn_row is not None:
                dorn_state = json.loads(dorn_row["state_json"])
                dorn_state["current_hp"] = 0
                if "desativado" not in (dorn_state.get("conditions") or []):
                    dorn_state["conditions"] = list(dorn_state.get("conditions") or []) + ["desativado"]
                connection.execute(
                    "UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id='dorn7'",
                    (json.dumps(dorn_state, ensure_ascii=False), confirmed_at.isoformat()),
                )
                dorn_disabled = True
        commit_battle_action(connection, current_snapshot, attack_count=strike_count, attack_limit=attack_limit)
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
            "dorn_disabled": dorn_disabled,
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
