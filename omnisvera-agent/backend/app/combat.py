from __future__ import annotations

import json
import re
import secrets
import sqlite3
from contextlib import closing, nullcontext
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
SPECTRAL_DAGGERS_PATH = 'Items/Adagas de Espectro Fantasma.md'


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
    from .monster_actions import build_action_map
    sheet = token.get('sheet') or {}
    origin = sheet.get('source')
    monster_id = origin.get('monster_id') if isinstance(origin, dict) else None
    parsed = build_action_map(token['name'], attacks, sheet.get('abilities') or [], monster_id=monster_id or sheet.get('id'))['attacks'][int(attack_id)]
    if parsed.get('execution_kind') in {'native_contact','passive_grid'}:
        raise ValueError('Use o contato especial ou a passiva no grid; este caso não é um ataque de dano')
    effect_only = bool(parsed.get('effect_only'))
    try:
        damage = '0' if effect_only else parse_formula(damage).formula
        bonus_raw = attack.get("bonus")
        if isinstance(bonus_raw, bool) or not re.fullmatch(r"[+-]?\d+", str(bonus_raw).strip()):
            raise ValueError("Bônus ausente")
        bonus = int(str(bonus_raw).strip())
    except ValueError as error:
        raise ValueError(f"O ataque {attack.get('name') or attack_id} está incompleto na ficha da criatura. O Mestre precisa revisar seu dano e bônus no cadastro; não é necessário digitar uma fórmula durante o ataque.") from error
    from .action_range import _ranged_name_re
    slot=attack.get('slot')
    if slot not in {'melee','ranged','touch'}:
        slot='ranged' if _ranged_name_re().search(str(attack.get('name') or '')) else 'melee'
    from .action_distances import weapon_range
    reach=weapon_range(attack)
    if reach:slot='ranged'
    return {"name": token["name"], "attributes": dict((token.get('sheet') or {}).get('attributes') or {}), "attacks": [{
        "id": attack_id, "name": attack.get("name") or "Ataque", "damage": damage,
        "slot":slot,
        "native_range":{'slot':slot,'max_range_m':reach.get('range_m')},
        "attack_bonus": bonus, "base_attack_bonus": bonus,
        "weapon_item_path": f"token:{token['id']}:attack:{attack_id}",
        "manual_effects": manual_effects,
        "effect_only": effect_only,
        **{key:attack[key] for key in ('damage_type','damage_kind','magical','material','raw','notes') if key in attack},
    }]}


MELEE_ATTACK_IDS = frozenset({"melee", "mordida", "garras-predatorias", "investida-predatoria",
                               "arma-de-sangue", "lamina-de-sangue"})
TOUCH_ATTACK_IDS = frozenset({"toque-sombrio"})
CAMPAIGN_RANGED_METERS = {'adaga-de-osso':9,'lamina-de-sangue':9,'pulseira-de-vinhas':9}


def attack_slot_and_max(attack_id: str, slot: str | None, level: int | None = None):
    """Slot ('melee'|'touch'|'ranged') and approved max range for target listing
    and validation. Unknown maxima stay None: Mestre adjudica."""
    resolved = slot or ("touch" if attack_id in TOUCH_ATTACK_IDS
                        else "ranged" if attack_id in {"ranged", "adaga-de-osso", "misseis-magicos"}
                        else "melee")
    maximum = 10 + 3 * level if attack_id == "misseis-magicos" and isinstance(level, int) else CAMPAIGN_RANGED_METERS.get(attack_id) if resolved=='ranged' else None
    return resolved, maximum


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
    """Campaign missile activation, with the existing daily counter.

    Preserve the campaign's existing per-spell resource instead of inventing
    or refilling daily slots. Range/line of sight and magical defenses remain
    Master adjudications, explicitly displayed before confirmation.
    """
    level = definition.get("level")
    if definition.get("id") not in {"morthak", "dorn7"} or type(level) is not int or not 1 <= level <= 15:
        raise ValueError("Nível de Morthak/Dorn fora da progressão conferida (1–15)")
    ability = next((a for a in definition.get("session_abilities", []) if a.get("id") == "misseis-magicos"), None)
    if not ability or ability.get("blocked"):
        raise ValueError("Magia indisponível nesta ficha")
    key = str((ability.get("uses") or {}).get("resource_key") or "").replace("-", "_")
    resource = next((r for r in resources if r.get("key") == key), None)
    if not resource:
        raise ValueError("Contador de Mísseis Mágicos não configurado")
    return {**definition, "active_effects": [], "attacks": [{
        "id": "misseis-magicos", "name": "Mísseis Mágicos", "damage": f"1d4+{min(level,5)}",
        "attack_bonus": 0, "weapon_item_path": "spell:misseis-magicos", "automatic_hit": True,
        "resource_cost": {"key": key, "amount": 1}, "max_range_m": 10 + 3 * level,
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
    attack["damage"] = '0' if (weapon.get('mechanics') or {}).get('special_attack') in {'net','garrote','dart'} else resolve_item_damage_formula(
        {"item_effects": definition.get("item_effects"), "attributes": definition.get("attributes"), 'attack_slot': attack_id}, weapon
    )
    attack["weapon_item_path"] = str(weapon.get("item_path") or "")
    return attack


def _require_blood_target(connection, target_type, target_id):
    owner = target_id if target_type == 'character' else None
    sheet = {}
    if target_type == 'token':
        token = connection.execute('SELECT character_id,sheet_json FROM session_workspace_tokens WHERE id=?', (target_id,)).fetchone()
        if token:
            owner = token['character_id']
            sheet = json.loads(token['sheet_json'] or '{}')
    necromantic = (sheet.get('summon') or {}).get('technique') in {'levantar-esqueleto', 'animar-mortos'}
    if owner in {'morthak', 'dorn7'} or sheet.get('has_blood') is False or necromantic or sheet.get('reanimated_by'):
        raise ValueError('Mordida exige um alvo com sangue; esqueletos e constructos não fornecem cura')


def _assert_preview_turn(record, snapshot):
    from .battle_mode import turn_identity
    saved, current = record['breakdown'].get('combat_turn'), turn_identity(snapshot)
    if saved is not None:
        if saved != current:
            raise CombatExpiredError('Esta prévia pertence a outro turno')
    elif current is not None:
        encounter = snapshot['encounter']
        if current[-1] != record['actor_character_id'] or record['created_at'] < encounter.get('turn_started_at', ''):
            raise CombatExpiredError('Esta prévia anterior não pertence ao turno atual')


def resolve_attack(database_path: Path, **kwargs) -> tuple[dict[str, Any], bool]:
    # Dice, preview reservation and receipt share one lock: concurrent tabs
    # cannot generate multiple previews before either has reserved the turn.
    init_combat(database_path)
    init_effects(database_path)
    if any((item.get('mechanics') or {}).get('special_attack')=='vibranium' for item in kwargs.get('inventory',[])):
        from .loot import init_loot
        init_loot(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute('BEGIN IMMEDIATE')
        return _resolve_attack(database_path, connection=connection, **kwargs)

def replay_attack_request(database_path,*,request_id,character_id,actor_id,intent):
    with closing(_connect(database_path)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_attack_resolutions'").fetchone():return None
        row=db.execute('SELECT * FROM combat_attack_resolutions WHERE request_id=?',(request_id,)).fetchone()
    if row is None:return None
    record=_resolution_record(row);stored=record['breakdown'].get('request_intent')
    if stored is None:return None
    if record['actor_character_id']!=character_id or record['requested_by_id']!=actor_id:raise PermissionError('Resolução pertence a outro acesso')
    if stored!=intent:raise ValueError('request_id já utilizado com outro ataque')
    return record


def _resolve_attack(
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
    ammunition_item_path: str | None = None,
    damage_type: str | None = None,
    tower_protected_side: bool | None = None,
    blood_boost: int = 0,
    controlling_character_id: str | None = None,
    request_intent: dict | None = None,
    guard_effect_id: str | None = None,
    rng: Rng | None = None,
    now: datetime | None = None,
    connection: sqlite3.Connection,
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
    if ammunition_item_path is not None:
        from copy import deepcopy
        from .item_families import project_ammunition
        inventory = deepcopy(inventory)
        selected_weapon = weapon_item_path or attack.get('weapon_item_path')
        weapon = next((i for i in inventory if i.get('item_path') == selected_weapon), {})
        if attack_id != 'ranged' or not (weapon.get('mechanics') or {}).get('requires_ammunition'):
            raise ValueError('Este ataque não utiliza munição selecionável')
        project_ammunition(inventory, {selected_weapon: ammunition_item_path})
        weapon_item_path = selected_weapon
    attack = _resolve_weapon_override(definition, inventory, attack, attack_id, weapon_item_path)
    from .item_specials import select_damage_type
    attack = select_damage_type(attack, inventory, damage_type)
    from .item_specials import prepare_attack, validate_net
    attack = prepare_attack(connection, attack, inventory, target, blood_boost=blood_boost, actor_id=actor_character_id, definition=definition)
    if attack.get('item_special')=='vibranium' and attack_count!=1:raise ValueError('Arremesse uma vez por confirmação para escolher os alvos do ricochete')
    if type(blood_boost) is not int or not 0<=blood_boost<=999:raise ValueError('Reforço de sangue inválido')
    if blood_boost:
        if actor_character_id!='raziel' or attack_id not in {'melee','ranged'} or attack_count!=1:
            raise ValueError('Reforço de sangue exige um ataque de arma equipada de Raziel')
        if not any(i.get('item_path')==attack.get('weapon_item_path') for i in available_attack_weapons(inventory,attack_id)):
            raise ValueError('Equipe uma arma válida antes de reforçá-la')
        attack={**attack,'blood_boost':blood_boost,'resource_cost':{'key':'reserva_de_sangue','amount':blood_boost}}
    from .night_form import require_humanoid
    require_humanoid(connection,actor_character_id)
    spectral_drain = actor_character_id == 'raziel' and attack_id in {'melee', 'ranged'} and any(
        str(item.get('item_path') or '').replace('\\', '/') == SPECTRAL_DAGGERS_PATH
        and item.get('item_path') == attack.get('weapon_item_path')
        for item in available_attack_weapons(inventory, attack_id)
    )
    automatic_hit = bool(attack.get("automatic_hit"))
    from .item_families import ammunition_contract,consume_ammunition
    ammunition=ammunition_contract(inventory,attack.get('weapon_item_path'),attack_count,definition.get('movement'),ammunition_item_path)
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
    with nullcontext(connection):
        row = connection.execute("SELECT * FROM combat_attack_resolutions WHERE request_id=?", (request_id,)).fetchone()
        if row:
            record = _resolution_record(row)
            if record['breakdown'].get('guard_effect_id') != guard_effect_id:
                raise ValueError('request_id já utilizado para outra interposição')
            if record['breakdown'].get('declared_tower_side') != tower_protected_side:
                raise ValueError('request_id já utilizado para outro lado do escudo')
            if record['breakdown'].get('selected_damage_type') != damage_type:
                raise ValueError('request_id já utilizado para outro tipo de dano')
            if (record['breakdown'].get('ammunition') or {}).get('item_path') != (ammunition or {}).get('item_path'):
                raise ValueError('request_id já utilizado para outra munição')
            expected = (actor_character_id, requested_by_id, attack_id, target.get("type"), target.get("id"), roll_mode, str(attack.get("weapon_item_path") or ""))
            actual = tuple(record[key] for key in ("actor_character_id", "requested_by_id", "attack_id", "target_type", "target_id", "roll_mode")) + (str((record.get("breakdown") or {}).get("attack", {}).get("weapon_item_path") or ""),)
            old_strikes = record["breakdown"].get("strikes", [{"d20": record["d20"]}])
            if actual != expected or len(old_strikes) != attack_count or int((record['breakdown'].get('attack') or {}).get('blood_boost') or 0)!=blood_boost or (roll_mode == "physical" and [s["d20"] for s in old_strikes] != dice):
                raise ValueError("request_id já utilizado para outra resolução")
            return record, False
        from .item_defense import has_tower
        target_tower=has_tower(connection,target['type'],target['id'])
        if target_tower and type(tower_protected_side) is not bool:
            raise ValueError('TOWER_SIDE_REQUIRED: declare se o ataque vem do lado protegido do escudo torre')
        if attack_id in {'toque-sombrio','misseis-magicos'} or attack.get('damage_kind')=='spell':
            from .item_grapple import assert_can_speak
            assert_can_speak(connection,'character' if connection.execute('SELECT 1 FROM character_states WHERE profile_id=?',(actor_character_id,)).fetchone() else 'token',actor_character_id)
        current_snapshot = effect_snapshot(connection)
        if attack.get('item_special') == 'net':
            validate_net(connection, actor_character_id, attack['weapon_item_path'])
        from .battle_mode import turn_identity, require_actor_alive
        combat_turn = turn_identity(current_snapshot)
        pending_id = (current_snapshot.get('encounter') or {}).get('pending_attack')
        if combat_turn is not None and not pending_id:
            legacy = connection.execute("SELECT * FROM combat_attack_resolutions WHERE actor_character_id=? AND status='pending' AND created_at>=? ORDER BY created_at LIMIT 1",
                (actor_character_id, current_snapshot['encounter'].get('turn_started_at', ''))).fetchone()
            if legacy and _resolution_record(legacy)['breakdown'].get('combat_turn') is None:
                legacy_record = _resolution_record(legacy)
                legacy_record['breakdown']['combat_turn'] = combat_turn
                pending_id = legacy_record['resolution_id']
                current_snapshot['encounter']['pending_attack'] = pending_id
                connection.execute('UPDATE combat_attack_resolutions SET breakdown_json=? WHERE resolution_id=?', (json.dumps(legacy_record['breakdown']), pending_id))
                connection.execute('UPDATE combat_effect_clock SET encounter_json=?,version=version+1 WHERE id=1', (json.dumps(current_snapshot['encounter']),))
        if combat_turn is not None and pending_id:
            pending = connection.execute('SELECT * FROM combat_attack_resolutions WHERE resolution_id=?', (pending_id,)).fetchone()
            if pending:
                record = _resolution_record(pending)
                same = (record['actor_character_id'] == actor_character_id and record['requested_by_id'] == requested_by_id
                    and record['attack_id'] == attack_id and record['target_type'] == target.get('type')
                    and record['target_id'] == target.get('id') and record['roll_mode'] == roll_mode
                    and record['breakdown'].get('guard_effect_id') == guard_effect_id
                    and str(record['breakdown'].get('attack', {}).get('weapon_item_path') or '') == str(attack.get('weapon_item_path') or '')
                    and (record['breakdown'].get('ammunition') or {}).get('item_path') == (ammunition or {}).get('item_path')
                    and int(record['breakdown'].get('attack',{}).get('blood_boost') or 0)==blood_boost
                    and len(record['breakdown'].get('strikes') or [record]) == attack_count)
                if same:
                    return record, False
            raise ValueError('Existe ataque pendente; confirme a prévia ou passe o turno')
        require_actor_alive(connection, actor_character_id)
        if attack_id == 'toque-sombrio':
            from .necromancer_spells import caster, living_touch_target, touch_cost_key
            _, caster_state, _ = caster(connection)
            living_touch_target(connection, target.get('type'), target.get('id'), requested_by_role)
            attack = {**attack, 'resource_cost': touch_cost_key(caster_state, bool(attack.get('use_memorized')))}
        guard = next((e for e in current_snapshot['effects'] if e['id'] == guard_effect_id and e.get('protocol') == 'guard'), None)
        guarded_id = target.get('id') if target.get('type') == 'character' else None
        if target.get('type') == 'token':
            guarded_pin = connection.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?', (target.get('id'),)).fetchone()
            guarded_id = guarded_pin[0] if guarded_pin else None
        if guard_effect_id and not guard:
            raise ValueError('Guarda consumida ou expirada')
        guard_ally_id=(guard.get('ally_id') or target.get('guard_ally_id')) if guard else None
        if guard and guard.get('area_guard'):
            from .dorn_protocols import protects_ally
            if not protects_ally(connection,guard,guard_ally_id):raise ValueError('Aliado fora da área de Guarda')
        if attack.get('life_drain'):
            _require_blood_target(connection, target.get('type'), target.get('id'))
            own = connection.execute('SELECT state_json FROM character_states WHERE profile_id=?', (actor_character_id,)).fetchone()
            if not own or int(json.loads(own['state_json']).get('current_hp') or 0) <= 0:
                raise ValueError('Raziel não pode morder a 0 PV')
            target_owner = connection.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?', (target.get('id'),)).fetchone() if target.get('type') == 'token' else None
            if target.get('id') == actor_character_id or (target_owner and target_owner['character_id'] == actor_character_id):
                raise ValueError('Raziel não pode morder a si mesmo')
        # Interception changes who receives the hit, not the attacker's intended
        # target (e.g. a provoked enemy must still declare the protected ally).
        require_battle_turn(connection, current_snapshot, actor_character_id,
            'character' if guard else target.get('type'), guard_ally_id if guard else target.get('id'),
            attack_count=attack_count, attack_limit=int(attack.get('attack_count', 1)),
            auxiliary=bool((attack.get('item_special_contract') or {}).get('followup_of')))
        consume_ammunition(connection,actor_character_id,ammunition,_now().isoformat())
        from .item_families import reload_movement
        reload_movement(current_snapshot,ammunition)
        if guarded_id and not guard_effect_id and any(e.get('protocol') == 'guard' and e.get('ally_id') == guarded_id for e in current_snapshot['effects']):
            dorn_state = connection.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()
            if dorn_state and int(json.loads(dorn_state[0]).get('current_hp') or 0) > 0:
                raise ValueError('Guarda: este ataque deve ser redirecionado automaticamente para Dorn')
        effects_version = current_snapshot["version"]
        if definition.get("effects_version", effects_version) != effects_version:
            raise ValueError("Os efeitos mudaram durante o cálculo. Tente novamente.")
        if attack.get("item_special")=="vibranium":definition={**definition,"attacks":[attack]}
        if attack.get('hemomancy'):
            from .hemomancy import prepare
            attack = prepare(connection, database_path, current_snapshot, attack, target, requested_by_role)
            definition = {**definition, 'attacks': [attack]}
        resource_cost = None
        if attack.get("resource_cost"):
            row = connection.execute("SELECT state_json,version FROM character_states WHERE profile_id=?", (actor_character_id,)).fetchone()
            if row is None:
                raise ValueError("Estado do conjurador não encontrado")
            cost = attack["resource_cost"]
            resource = next((r for r in json.loads(row["state_json"]).get("resources", []) if r.get("key") == cost["key"]), None)
            if not resource or int(resource.get("current", 0)) < cost["amount"]:
                raise ValueError("Sem usos disponíveis para esta magia")
            resource_cost = {**cost, "state_version": row["version"], 'resource_current': int(resource['current'])}
    native_range=None
    if attack.get('native_range'):
        from .spatial_grid import check_attack_range
        spec=attack['native_range']
        intended_type,intended_id=('character',guard_ally_id) if guard else (target['type'],target['id'])
        native_range={**spec,'target_type':intended_type,'target_id':intended_id,
            **check_attack_range(database_path,actor_character_id=actor_character_id,
                target_type=intended_type,target_id=intended_id,slot=spec['slot'],
                max_range_m=spec['max_range_m'],connection=connection,include_context=True)}
    from .item_range import range_context
    item_range = None if automatic_hit else range_context(connection,database_path,actor_character_id,attack,inventory,target)
    if roll_mode == "digital":
        dice = [0] if automatic_hit else [int(roll_formula("1d20", rng)["total"]) for _ in range(attack_count)]
        d20 = dice[0]
    attack_spec = resolve_character_roll(definition, inventory, "attack", attack_id)
    attack_bonus = parse_formula(attack_spec.formula).modifier
    if item_range:attack_bonus+=item_range['bonus']
    from .raziel_pipeline import attack_context
    raziel_context=attack_context(connection,actor_character_id)
    from .spatial_grid import diagonal_bonus
    tactical=diagonal_bonus(connection,actor_character_id,target.get('type'),target.get('id'))
    if not automatic_hit:attack_bonus+=tactical['bonus']
    # Tomo Arcano p.53: attacks against a blinded creature are very easy (+5).
    if not automatic_hit and any((e.get('condition')=='magical_darkness' or e.get('monster_condition')=='blinded') for e in current_snapshot['effects'] if e.get('target_type')==target.get('type') and e.get('target_id')==target.get('id')):
        attack_bonus += 5
    effect_only = bool(attack.get('effect_only')) and (attack.get('item_special') in {'net','garrote','dart'} or not connection.execute('SELECT 1 FROM character_states WHERE profile_id=?', (actor_character_id,)).fetchone())
    damage_formula = '0' if effect_only else parse_formula(str(attack["damage"])).formula
    damage_modifier = 0 if effect_only else parse_formula(damage_formula).modifier

    target_type = str(target.get("type") or "")
    target_id = str(target.get("id") or "").strip()
    target_name = str(target.get("name") or "Alvo").strip() or "Alvo"
    if target_type not in {"character", "token"} or not target_id:
        raise ValueError("Alvo inválido")
    target_ac = target.get('touch_armor_class') if attack.get('item_special') == 'net' else target.get("armor_class")
    from .magic_passives import illusion_ac_ignored
    ignored_illusion_ac=illusion_ac_ignored(connection,actor_character_id,target_type,target_id) if attack.get('item_special')!='net' else 0
    if ignored_illusion_ac and target_ac is not None:target_ac=int(target_ac)-ignored_illusion_ac
    current_hp = target.get("current_hp")
    if isinstance(target_ac, bool) or target_ac is None or int(target_ac) <= 0:
        raise ValueError("O alvo não possui CA válida")
    if isinstance(current_hp, bool) or current_hp is None:
        raise ValueError("O alvo não possui HP configurado")
    from .vezemir_skills import survives
    if int(current_hp) <= 0 and not survives(connection,target_id,int(current_hp)):
        raise ValueError("O alvo já está sem HP")

    if raziel_context:
        attack_bonus=(attack_bonus+(2 if raziel_context.get('conditional_id') else 0))*raziel_context['multiplier']
        if item_range:
            item_range={**item_range,'base_bonus':item_range['bonus'],'bonus':item_range['bonus']*raziel_context['multiplier']}
    attack_total = d20 + attack_bonus
    result = "hit" if attack_total >= int(target_ac) else "miss"
    strikes = []
    for die in dice:
        # Old Dragon SRD: natural 1 misses and natural 20 hits regardless of bonuses.
        hit = automatic_hit or (die != 1 and (die == 20 or die + attack_bonus >= int(target_ac)))
        damage = roll_formula(damage_formula, rng) if hit and not effect_only else {
            "individual_results": [], "modifier": damage_modifier, "total": 0,
        }
        strikes.append({"d20": die, "attack_total": die + attack_bonus, "result": "hit" if hit else "miss",
                        "damage_total": max(0, int(damage["total"])), "damage_rolls": damage["individual_results"]})
        from .critical_rules import augment_strike
        player_attack=bool(connection.execute('SELECT 1 FROM character_states WHERE profile_id=?',(actor_character_id,)).fetchone())
        augment_strike(strikes[-1],attack,inventory,rng,player_attack=player_attack and not automatic_hit and not effect_only)
        if attack.get('hemomancy'):
            from .hemomancy import roll_passives
            roll_passives(attack, strikes[-1], rng)
        if hit and blood_boost:
            boost=roll_formula(f'{blood_boost}d4',rng)
            strikes[-1]['damage_total']+=int(boost['total']);strikes[-1]['damage_rolls']+=boost['individual_results']
        from .raziel_pipeline import roll_attack as pipeline_roll
        if not effect_only:pipeline_roll(strikes[-1],raziel_context,rng)
        if player_attack and die==20 and not automatic_hit:strikes[-1]['unavoidable']=True
    result = "hit" if any(s["result"] == "hit" for s in strikes) else "miss"
    damage_roll = {"individual_results": [die for s in strikes for die in s["damage_rolls"]],
                   "modifier": damage_modifier, "total": sum(s["damage_total"] for s in strikes)}
    hemomancy = attack.get('hemomancy')
    if isinstance(hemomancy, dict) and result == 'hit':
        # Base dice, conditional dice and flat modifiers stay separately
        # auditable. Critical dice never duplicate a flat modifier.
        if any(strike.get('critical') for strike in strikes):
            damage_formula += '+' + hemomancy['base_damage']
        if hemomancy.get('skill_damage'):
            damage_formula += '+' + hemomancy['skill_damage']
        if hemomancy['passive_d6']:
            damage_formula += f"+{hemomancy['passive_d6']}d6"
        if hemomancy['bonus']:
            damage_formula += f"+{hemomancy['bonus']}"
            damage_roll['modifier'] += hemomancy['bonus']
    if blood_boost:damage_formula+=f'+{blood_boost}d4 (reforço de sangue)'
    equipment = [
        {
            "item_path": str(item.get("item_path") or ""),
            "item_title": str(item.get("item_title") or "Item"),
            "role": str(item.get("role") or "support"),
        }
        for item in attack.get("equipment") or []
    ]
    strength_rider = {}
    if attack_id == 'toque-sombrio' and result == 'hit':
        from .necromancer_spells import living_touch_target, touch_rider
        strength_rider = touch_rider(connection, living_touch_target(connection, target_type, target_id, requested_by_role))
        explanation = 'Ao confirmar o acerto, ativa Toque Sombrio: no início do turno do alvo, 1–3 em 1d6 causa −1 PV. Sem perda de FOR.'
        attack = {**attack, 'manual_effects': [*(attack.get('manual_effects') or []), explanation]}
    from .damage_profiles import attack_profile
    from .monster_conditions import attack_contract
    monster_contract=attack_contract(connection,actor_character_id,attack_id)
    if monster_contract:
        automated={r['name'].casefold() for r in monster_contract['riders']}
        attack={**attack,'manual_effects':[name for name in attack.get('manual_effects',[]) if name.casefold() not in automated]}
    from .inventory_conditions import combat_fingerprint
    breakdown = {
        'request_intent':request_intent,
        'selected_damage_type':damage_type,
        'declared_tower_side':tower_protected_side,
        'tower_shield':{'protected_side':tower_protected_side} if target_tower else None,
        'item_special': {'kind':'net', 'item_path':attack['weapon_item_path'], 'dexterity_ac_bonus':target.get('dexterity_ac_bonus') or 0} if attack.get('item_special') == 'net' else attack.get('item_special_contract'),
        'ammunition':ammunition,
        'item_range':item_range,
        'inventory_condition_fingerprint':combat_fingerprint(connection,actor_character_id,target_type,target_id),
        'damage_profile':attack_profile(attack,inventory),
        **({'illusion_ac_ignored':ignored_illusion_ac} if ignored_illusion_ac else {}),
        **({'monster_on_hit':monster_contract} if monster_contract else {}),
        'combat_turn': combat_turn,
        "guard_effect_id": guard_effect_id,
        "guard_ally_id": guard_ally_id,
        "area_guard": bool(guard and guard.get('area_guard')),
        "life_drain": bool(attack.get('life_drain')) or spectral_drain,
        "strength_drain": strength_rider,
        "attack_limit": int(attack.get("attack_count", 1)),
        "automatic_hit": automatic_hit,
        "resource_cost": resource_cost,
        "manual_effects": list(attack.get("manual_effects") or []) if result == "hit" else [],
        "strikes": strikes,
        "effects_version": effects_version,
        "tactical_state": tactical,
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
    if native_range is not None:breakdown['native_range']=native_range
    if isinstance(attack.get('hemomancy'), dict):
        breakdown['hemomancy'] = attack['hemomancy']
    if raziel_context:breakdown['raziel_pipeline']=raziel_context
    from .hemomancy import incoming_shield
    shield_trigger = incoming_shield(current_snapshot, target, strikes)
    if shield_trigger:
        breakdown['hemomancy_shield'] = shield_trigger
    if tactical['bonus'] and not automatic_hit:
        breakdown['attack'].update(tactical_bonus=tactical['bonus'],tactical_reason=tactical['reason'])
    if attack.get("effect_attack_bonus"):
        breakdown["attack"]["effect_bonus"] = int(attack["effect_attack_bonus"])
    resolution_id = f"attack:{secrets.token_hex(16)}"
    with nullcontext(connection):
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
        if guard_effect_id and not (guard and guard.get('area_guard')):
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
        if combat_turn is not None:
            encounter = current_snapshot['encounter']
            encounter['pending_attack'] = resolution_id
            connection.execute('UPDATE combat_effect_clock SET encounter_json=?,version=version+1 WHERE id=1', (json.dumps(encounter),))
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
            try:
                _assert_preview_turn(record, live_snapshot)
                from .item_range import validate_confirm as validate_pending_range
                validate_pending_range(connection,database_path,record)
            except (CombatExpiredError,ValueError):
                continue
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
                caster = connection.execute("SELECT state_json,version FROM character_states WHERE profile_id=?", (record["actor_character_id"],)).fetchone()
                resource = next((r for r in json.loads(caster[0]).get('resources', []) if r.get('key') == cost['key']), None) if caster else None
                if resource is None or int(resource.get('current') or 0) < cost['amount']:
                    continue
                if record['breakdown'].get('combat_turn') is None:
                    if caster['version'] != cost['state_version']:
                        continue
                elif int(resource['current']) != cost.get('resource_current', int(resource['current'])):
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
        native_range=record['breakdown'].get('native_range')
        if native_range:
            from .spatial_grid import check_attack_range
            try:
                checked=check_attack_range(database_path,actor_character_id=record['actor_character_id'],
                    target_type=native_range['target_type'],target_id=native_range['target_id'],
                    slot=native_range['slot'],max_range_m=native_range['max_range_m'],connection=connection,include_context=True)
                if any(checked.get(key)!=native_range.get(key) for key in ('checked','cells','meters','context')):
                    raise ValueError('A distância mudou desde a rolagem; resolva novamente')
            except ValueError as error:raise CombatExpiredError(str(error)) from error
        from .item_range import validate_confirm as validate_item_range
        try:validate_item_range(connection,database_path,record)
        except ValueError as error:raise CombatExpiredError(str(error)) from error
        current_snapshot = effect_snapshot(connection)
        _assert_preview_turn(record, current_snapshot)
        strike_count = len(record['breakdown'].get('strikes') or [record])
        attack_limit = int(record['breakdown'].get('attack_limit') or 1)
        from .night_form import require_humanoid
        require_humanoid(connection,record['actor_character_id'])
        require_battle_turn(connection, current_snapshot, record['actor_character_id'],
            'character' if record['breakdown'].get('guard_ally_id') else record['target_type'],
            record['breakdown'].get('guard_ally_id') or record['target_id'],
            attack_count=strike_count, attack_limit=attack_limit, resolution_id=resolution_id,
            auxiliary=bool((record['breakdown'].get('item_special') or {}).get('followup_of')))
        if record['breakdown'].get('tactical_state') is not None:
            from .spatial_grid import diagonal_bonus
            if diagonal_bonus(connection,record['actor_character_id'],record['target_type'],record['target_id'])!=record['breakdown']['tactical_state']:
                raise CombatExpiredError('A posição ou o bônus diagonal mudou. Resolva o ataque novamente.')
        if record['attack_id'] == 'mordida':
            _require_blood_target(connection, record['target_type'], record['target_id'])
        if confirmed_at > datetime.fromisoformat(record["expires_at"]):
            raise CombatExpiredError("A resolução do ataque expirou")
        live_snapshot = effect_snapshot(connection)
        if record['breakdown'].get('area_guard'):
            from .dorn_protocols import protects_ally
            live_guard=next((e for e in live_snapshot['effects'] if e['id']==record['breakdown']['guard_effect_id']),None)
            if not protects_ally(connection,live_guard,record['breakdown']['guard_ally_id']):
                raise CombatExpiredError('A área de Guarda mudou; resolva novamente')
        _assert_participant_effects_unchanged(
            live_snapshot["effects"], record["breakdown"],
            record["actor_character_id"], record["target_type"], record["target_id"],
            live_snapshot["version"],
        )
        from .hemomancy import validate_confirm
        validate_confirm(connection, current_snapshot, record)
        from .inventory_conditions import combat_fingerprint
        saved_inventory=record['breakdown'].get('inventory_condition_fingerprint')
        if saved_inventory and saved_inventory!=combat_fingerprint(connection,record['actor_character_id'],record['target_type'],record['target_id']):
            raise ValueError('Equipamento mudou desde a rolagem. Resolva novamente antes de confirmar.')
        from .monster_conditions import validate_confirm as validate_monster_conditions
        validate_monster_conditions(connection,record)
        resource_cost = record["breakdown"].get("resource_cost")
        if resource_cost:
            caster = connection.execute("SELECT state_json,version FROM character_states WHERE profile_id=?", (record["actor_character_id"],)).fetchone()
            if caster is None:
                raise CombatExpiredError("A ficha do conjurador não está disponível")
            caster_state = json.loads(caster["state_json"])
            resource = next((r for r in caster_state.get("resources", []) if r.get("key") == resource_cost["key"]), None)
            if record['breakdown'].get('combat_turn') is None:
                if caster['version'] != resource_cost['state_version']:
                    raise CombatExpiredError('A ficha ou os recursos mudaram. Confira a magia novamente.')
            elif resource and int(resource['current']) != resource_cost.get('resource_current', int(resource['current'])):
                raise CombatExpiredError('Os usos desta magia mudaram durante a prévia; passe o turno ou peça adjudicação ao Mestre')
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
            from .vezemir_skills import survives
            if int(hp_before) <= 0 and not survives(connection,record['target_id'],hp_before):
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
        from .dorn_spell_pack import redirect_hits
        from .item_families import consume_ammunition
        from .item_families import reload_movement
        reload_movement(current_snapshot,record['breakdown'].get('ammunition'),apply=True)
        consume_ammunition(connection,record['actor_character_id'],record['breakdown'].get('ammunition'),confirmed_at.isoformat(),apply=True)
        # Legacy initiative also uses the native movement budget; its attack
        # commit intentionally does not write the battle-mode action counters.
        if (record['breakdown'].get('ammunition') or {}).get('reload_movement') and current_snapshot.get('encounter',{}).get('active'):
            connection.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(current_snapshot['encounter']),))
        from .item_specials import validate_confirmation
        validate_confirmation(connection,record)
        actual_damage,reflection=redirect_hits(connection,record['target_type'],record['target_id'],record['breakdown'].get('strikes') or [record],confirmed_at.isoformat(),observer_id=record['actor_character_id'])
        if reflection:
            record['breakdown']['reflection_result']=reflection;record['damage_total']=actual_damage
            connection.execute('UPDATE combat_attack_resolutions SET damage_total=?,breakdown_json=? WHERE resolution_id=?',(actual_damage,json.dumps(record['breakdown']),resolution_id))
        from .item_defense import apply_tower
        tower_result=apply_tower(record)
        if tower_result:record['breakdown']['item_defense_result']=tower_result
        from .hemomancy import damage_after_mitigation, confirmed as confirm_hemomancy
        if record['breakdown'].get('hemomancy'):
            strikes=record['breakdown'].get('strikes') or []
            unavoidable=sum(s['damage_total'] for s in strikes if s.get('unavoidable'))
            record['damage_total'] = unavoidable+damage_after_mitigation(connection, record, max(0,int(record['damage_total'])-unavoidable))
        if record['breakdown'].get('area_guard'):
            before=int(record['damage_total'])
            unavoidable=min(before,sum(s['damage_total'] for s in record['breakdown'].get('strikes',[]) if s.get('unavoidable')))
            record['damage_total']=unavoidable+(before-unavoidable)//2
            record['breakdown']['guard_damage']={'before':before,'after':record['damage_total']}
            connection.execute('UPDATE combat_attack_resolutions SET damage_total=?,breakdown_json=? WHERE resolution_id=?',
                (record['damage_total'],json.dumps(record['breakdown']),resolution_id))
        profile=record['breakdown'].get('damage_profile')
        context={**profile,'unavoidable_damage':sum(s['damage_total'] for s in record['breakdown'].get('strikes',[]) if s.get('unavoidable'))} if profile else None
        hp_change = change_hp(connection, record["target_type"], record["target_id"], -int(record["damage_total"]), confirmed_at.isoformat(),damage_context=context)
        rapina_received=max(0,int(hp_change.get('damage_after_defenses',record['damage_total']))
            +int(hp_change.get('damage_reduction_penalty') or 0))
        if hp_change.get('magic_item_absorption'):
            absorption=hp_change['magic_item_absorption']
            record['breakdown']['magic_item_absorption']=absorption
            record['damage_total']=max(0,int(record['damage_total'])-absorption['absorbed'])
            connection.execute('UPDATE combat_attack_resolutions SET damage_total=?,breakdown_json=? WHERE resolution_id=?',
                (record['damage_total'],json.dumps(record['breakdown'],ensure_ascii=False),resolution_id))
        from .monster_rust import reverse_contact
        from .item_specials import confirm_hit as confirm_item_hit
        special_result = confirm_item_hit(connection, record, confirmed_at.isoformat())
        if special_result:
            record['breakdown']['item_special_result'] = special_result
        from .item_darts import confirm_hit as confirm_dart_hit
        dart_results = confirm_dart_hit(connection, record, confirmed_at.isoformat())
        if dart_results:
            record['breakdown']['item_dart_results'] = dart_results
            connection.execute('UPDATE combat_attack_resolutions SET breakdown_json=? WHERE resolution_id=?',
                (json.dumps(record['breakdown'],ensure_ascii=False),resolution_id))
        rust_results=reverse_contact(connection,record,confirmed_at.isoformat())
        if rust_results:record['breakdown']['rust_contact_results']=rust_results
        if rust_results:
            connection.execute('UPDATE combat_attack_resolutions SET breakdown_json=? WHERE resolution_id=?',(json.dumps(record['breakdown'],ensure_ascii=False),resolution_id))
        if record['breakdown'].get('monster_on_hit'):
            from .monster_conditions import apply_on_hit
            riders=apply_on_hit(connection,record,confirmed_at.isoformat())
            record['breakdown']['monster_rider_results']=riders
            for rider in riders:
                if rider.get('hp'):
                    hp_change['hp_after']=rider['hp']['hp_after']
                    hp_change['damage_taken']=max(0,hp_change['hp_before']-hp_change['hp_after'])
                    record['damage_total']+=rider['hp'].get('damage_before_defenses',rider.get('damage_dealt',0))
        if profile:
            record['breakdown']['damage_defenses']={key:hp_change[key] for key in ('damage_type','damage_before_defenses','damage_after_defenses') if key in hp_change}
            connection.execute('UPDATE combat_attack_resolutions SET damage_total=?,breakdown_json=? WHERE resolution_id=?',(record['damage_total'],json.dumps(record['breakdown'],ensure_ascii=False),resolution_id))
        from .raziel_pipeline import confirmed as pipeline_confirm
        pipeline_confirm(connection,record,hp_change,confirmed_at.isoformat())
        if record['breakdown'].get('hemomancy') or record['breakdown'].get('hemomancy_shield'):
            confirm_hemomancy(connection, current_snapshot, record, hp_change, confirmed_at.isoformat())
            connection.execute('UPDATE combat_attack_resolutions SET damage_total=?,breakdown_json=? WHERE resolution_id=?',
                (record['damage_total'], json.dumps(record['breakdown'], ensure_ascii=False), resolution_id))
        hp_after = hp_change["hp_after"]
        if hp_change.get('damage_reduction_penalty'):
            record['damage_total']+=hp_change['damage_reduction_penalty']
            record['breakdown']['damage_reduction_penalty']=hp_change['damage_reduction_penalty']
            connection.execute('UPDATE combat_attack_resolutions SET damage_total=?,breakdown_json=? WHERE resolution_id=?',(record['damage_total'],json.dumps(record['breakdown']),resolution_id))
        if hp_after==0:
            from .vezemir_skills import kill_reward
            kill_reward(connection,record['actor_character_id'],record['target_type'],record['target_id'],confirmed_at.isoformat())
        if record['breakdown'].get('life_drain'):
            spectral = record['attack_id'] in {'melee', 'ranged'} and str(
                (record['breakdown'].get('attack') or {}).get('weapon_item_path') or ''
            ).replace('\\', '/') == SPECTRAL_DAGGERS_PATH
            if record['actor_character_id'] != 'raziel' or not (record['attack_id'] == 'mordida' or spectral):
                raise ValueError('Drenagem não autorizada para este ataque')
            own = connection.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()
            if not own or int(json.loads(own['state_json']).get('current_hp') or 0) <= 0:
                raise ValueError('Raziel não pode drenar vida a 0 PV')
            drained = hp_change.get('damage_taken',max(0, int(hp_before) - int(hp_after)))
            healed = change_hp(connection, 'character', 'raziel', drained, confirmed_at.isoformat())
            record['breakdown']['drain_result'] = {**healed, 'drained': drained,
                'healed': int(healed['hp_after']) - int(healed['hp_before'])}
            connection.execute('UPDATE combat_attack_resolutions SET breakdown_json=? WHERE resolution_id=?',
                (json.dumps(record['breakdown'], ensure_ascii=False), resolution_id))
        if (record['breakdown'].get('strength_drain') or {}).get('dot_hp') and hp_after>0:
            from .necromancer_spells import add_effect
            victim={'type':record['target_type'],'id':record['target_id']}
            existing=connection.execute("SELECT 1 FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.dot_hp')=1",(record['target_type'],record['target_id'])).fetchone()
            if not existing:
                origin=connection.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='morthak'").fetchone()
                add_effect(connection,victim,'Toque Sombrio','Morthak · Toque Sombrio',confirmed_at.isoformat(),necro_spell='toque-sombrio',dot_hp=True,magic_type='arcane',spell_circle=1,caster_level=int(json.loads(origin[0]).get('level') or 5) if origin else 5)
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
        from .magic_item_combat import reflect_rapina
        rapina=reflect_rapina(connection,record,rapina_received,confirmed_at.isoformat())
        if rapina:
            record['breakdown']['rapina_reflection']=rapina
            connection.execute('UPDATE combat_attack_resolutions SET breakdown_json=? WHERE resolution_id=?',
                (json.dumps(record['breakdown'],ensure_ascii=False),resolution_id))
        fumble=sum(s.get('fumble_damage',0) for s in record['breakdown'].get('strikes',[]))
        if fumble:
            record['breakdown']['fumble_result']=change_hp(connection,'character',record['actor_character_id'],-fumble,confirmed_at.isoformat(),damage_context={**(profile or {}),'kind':'effect'})
            record['breakdown']['fumble_result']['damage']=fumble
            connection.execute('UPDATE combat_attack_resolutions SET breakdown_json=? WHERE resolution_id=?',(json.dumps(record['breakdown']),resolution_id))
        from .monster_runtime import record_confirmed_attacks
        from .magic_field_items import NAILS, confirm_nails
        if record['attack_id'] == NAILS:
            record['breakdown']['ungual_nails'] = confirm_nails(connection, record, confirmed_at.isoformat())
            connection.execute('UPDATE combat_attack_resolutions SET breakdown_json=? WHERE resolution_id=?',
                (json.dumps(record['breakdown'], ensure_ascii=False), resolution_id))
        record_confirmed_attacks(connection,record,confirmed_at.isoformat())
        from .item_throwing import confirmed as confirm_throw
        throwing = confirm_throw(connection, record, current_snapshot, confirmed_at.isoformat())
        if throwing:
            record['breakdown']['item_special_result'] = throwing
            connection.execute('UPDATE combat_attack_resolutions SET breakdown_json=? WHERE resolution_id=?',(json.dumps(record['breakdown']),resolution_id))
        bonus_throw = bool((record['breakdown'].get('item_special') or {}).get('followup_of'))
        commit_battle_action(connection, current_snapshot, attack_count=0 if bonus_throw else strike_count, attack_limit=attack_limit)
        from .battle_mode import retire_defeated
        retire_defeated(connection, confirmed_at.isoformat())
        from .dorn_spells import confirmed_ranged
        confirmed_ranged(connection, record['actor_character_id'], record, current_snapshot['round'])
        consumed = [e["id"] for e in record["breakdown"].get("effects", []) if e["duration"] == "next_attack"]
        for effect_id in consumed:
            connection.execute("UPDATE combat_effects SET active=0 WHERE id=?", (effect_id,))
        if consumed:
            connection.execute("UPDATE combat_effect_clock SET version=version+1 WHERE id=1")
        detail = {
            "turn_sequence": (current_snapshot.get("encounter") or {}).get("turn_sequence"),
            "turn_started_at": (current_snapshot.get("encounter") or {}).get("turn_started_at"),
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
        detail['breakdown']=dict(detail['breakdown'])
        detail['breakdown'].pop('monster_on_hit',None)  # Raw source contract is technical, not table narrative.
        detail['breakdown'].pop('item_special',None)
        caster_visibility=connection.execute('SELECT visible_to_players FROM session_workspace_tokens WHERE id=?',(record['actor_character_id'],)).fetchone()
        from .monster_runtime import public_token
        private_actor=caster_visibility is not None and not public_token(connection,record['actor_character_id'])
        private_target=record['target_type']=='token' and not public_token(connection,record['target_id'])
        ledger_id = append_session_ledger_event(
            connection,
            source_type="combat_action",
            source_id=record["resolution_id"],
            event_kind="action",
            actor_id=record["requested_by_id"],
            actor_name=record["actor_name"],
            actor_role=record["requested_by_role"],
            character_id=record["actor_character_id"],
            title=f"{record['actor_name']} atacou {record['target_name']} com {record['attack_name']}" + (' · '+record['breakdown']['item_special_result']['label'] if record['breakdown'].get('item_special_result') else '') + (' · escudo torre bloqueou' if any(r.get('blocked') for r in (record['breakdown'].get('item_defense_result') or {}).get('rolls',[])) else '') + (f" · Rapina devolveu {rapina['damage']} de dano" if rapina else ''),
            detail=detail,
            visibility="gm" if private_actor or private_target else "table",
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
