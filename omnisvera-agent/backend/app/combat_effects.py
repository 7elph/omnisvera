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

from .dice_rolls import parse_formula, roll_formula
from .session_ledger import append_session_ledger_event
from .battle_mode import stage_battle, restore_exploration

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
    effects=[
        json.loads(row[0]) for row in db.execute("SELECT data_json FROM combat_effects WHERE active=1 ORDER BY id")
    ]
    if any(effect.get('hemomancy_kind') for effect in effects):
        # Keep map-bound riders persisted, but never apply their bonuses on a
        # different map. Legacy effects retain their existing projection.
        selected = db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
        active_map = encounter.get('map_id') if encounter.get('active') else selected[0] if selected else 'default'
        effects = [effect for effect in effects if not effect.get('hemomancy_kind') or effect.get('map_id') == active_map]
    from .dorn_spell_pack import expand_web_effects
    return {"round":clock[0],"version":clock[1],"encounter":encounter,"effects":expand_web_effects(db,effects)}


def readeffects(path: Path) -> dict:
    # Polling must not acquire a writer reservation or re-run migrations.
    # BEGIN gives clock, encounter and effects one coherent read snapshot.
    try:
        with closing(sqlite3.connect(path, timeout=30)) as db:
            db.execute("BEGIN")
            return effect_snapshot(db)
    except sqlite3.OperationalError as error:
        if not any(message in str(error) for message in (
            "no such table: combat_effect_clock", "no such table: combat_effects",
            "no such column: encounter_json",
        )):
            raise
    init_effects(path)  # Only a new/legacy schema needs initialization.
    with closing(sqlite3.connect(path, timeout=30)) as db:
        db.execute("BEGIN")
        return effect_snapshot(db)


def expire_rest_effects(db: sqlite3.Connection, character_id: str, *, complete: bool = False) -> None:
    # A GM full rest ends every temporary status, not just rest-bound buffs.
    # Equipment/passive bonuses remain derived from the equipped inventory.
    duration_filter = "" if complete else " AND json_extract(data_json,'$.duration')='rest'"
    cursor = db.execute("UPDATE combat_effects SET active=0 WHERE active=1 AND target_type='character' AND target_id=?" + duration_filter, (character_id,))
    if complete and character_id == 'raziel':
        from .hemomancy import end_combat as end_hemomancy
        if end_hemomancy(db) and not cursor.rowcount:
            db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    if cursor.rowcount:
        if complete and character_id == 'morthak' and db.execute("SELECT 1 FROM sqlite_master WHERE name='session_workspace_tokens'").fetchone():
            from .morthak_high_spells import cleanup
            cleanup(db, datetime.now(timezone.utc).isoformat())
        db.execute("UPDATE combat_effect_clock SET version=version+1 WHERE id=1")


def expire_session_effects(db: sqlite3.Connection, session_id: int, now: str, *, current_session: bool = False) -> None:
    """Close temporary effects in the session-status transaction, never a GET.

    Manual transformations and rest-bound effects survive. An old session must
    not clear a newer session's global effects, including unscoped legacy rows.
    """
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {'combat_effects', 'combat_effect_clock'} <= tables:
        return
    if db.execute("SELECT 1 FROM game_sessions WHERE status='active' AND id<>?", (session_id,)).fetchone():
        return
    snapshot = effect_snapshot(db)
    encounter = snapshot['encounter']
    if encounter.get('game_session_id') not in (None, session_id) and (encounter.get('active') or not current_session):
        return
    changes = []
    for effect in snapshot['effects']:
        if effect.get('monster_condition'):
            continue  # Bodily conditions follow their clock/cure, not session closure.
        if effect.get('duration') in {'rounds', 'scene', 'next_attack', 'fictional_time'} or effect.get('protocol') == 'guard' or effect.get('immobilized') or effect.get('reward')=='vines' or effect.get('necro_spell') in {'clonagem','aterrorrizar'} or effect.get('dot_hp') or effect.get('skill')=='provocacao':
            db.execute('UPDATE combat_effects SET active=0 WHERE id=?', (effect['id'],))
            changes.append({'expired': effect['id']})
    if encounter.get('active'):
        if encounter.get('battle_mode'):
            restore_exploration(db, encounter, now)
        encounter['active'] = False
        db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))
        changes.append({'encounter': encounter})
    if not changes:
        return
    from .morthak_high_spells import cleanup
    cleanup(db,now)
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    if 'session_ledger' in tables:
        append_session_ledger_event(db, source_type='combat_effect', source_id=f'session-end:{session_id}:{uuid.uuid4().hex}',
            event_kind='state', actor_id='master', actor_name='Mestre', actor_role='gm', character_id=None,
            title='Efeitos temporários encerrados com a sessão', visibility='gm', created_at=now,
            game_session_id=session_id, detail={'action': 'session_end', 'changes': changes})


def change_hp(db: sqlite3.Connection, target_type: str, target_id: str, amount: int, now: str, *, ignore_temporary_hp: bool = False, damage_type: str | None = None, regeneration: bool = False, damage_context: dict | None = None) -> dict:
    """Signed HP change, honoring temporary HP for damage and maximum HP for healing."""
    if damage_context and not damage_type:damage_type=damage_context.get('damage_type')
    before_defenses=-amount if amount<0 else 0
    if amount < 0 and (damage_type or damage_context):
        from .monster_runtime import damage_response
        amount = -damage_response(db, target_type, target_id, -amount, damage_type,damage_context)
    after_defenses=max(0,-amount)
    if target_type == "character":
        row = db.execute("SELECT state_json FROM character_states WHERE profile_id=?", (target_id,)).fetchone()
        if row is None:
            raise ValueError("Personagem não encontrado")
        state = json.loads(row[0])
        from .night_form import current_form, change_animal_hp
        if target_id=='raziel' and current_form(state):
            result=change_animal_hp(state,amount)
            db.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?',
                       (json.dumps(state,ensure_ascii=False),now,target_id))
            db.execute('UPDATE session_workspace_tokens SET current_hp=?,updated_at=? WHERE character_id=?',
                       (state['current_hp'],now,target_id))
            return result
        before, maximum = state.get("current_hp"), state.get("maximum_hp")
        temporary = int(state.get("temporary_hp") or 0)
        absorbed = min(temporary, -amount) if amount < 0 and not ignore_temporary_hp else 0
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
    penalty=0
    if target_type=='character' and target_id=='vezemir':
        from .vezemir_skills import hp_result,damage_penalty
        if amount<0:
            penalty=damage_penalty(db);amount-=penalty
        after=hp_result(db,state,int(before)+amount,int(before),int(maximum),now)
    else:
        after = max(0, min(int(maximum), int(before) + amount))
    if target_type == "character":
        state["current_hp"] = after
        if target_id == 'dorn7':
            state['conditions'] = [c for c in state.get('conditions') or [] if str(c).lower() != 'desativado']
            if after == 0:
                state['conditions'].append('desativado')
        db.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?",
                   (json.dumps(state, ensure_ascii=False), now, target_id))
        db.execute("UPDATE session_workspace_tokens SET current_hp=?,updated_at=? WHERE character_id=?", (after, now, target_id))
    else:
        db.execute("UPDATE session_workspace_tokens SET current_hp=?,updated_at=? WHERE id=?", (after, now, target_id))
    from .bat_swarm import sync as sync_swarm
    sync_swarm(db,now)
    from .monster_runtime import track_hp
    track_hp(db,target_type,target_id,int(before),after,damage_type,regeneration,now)
    if after==0:
        from .morthak_high_spells import cleanup
        cleanup(db,now)
    return {"hp_before": before, "hp_after": after, "temporary_hp_absorbed": absorbed, "damage_reduction_penalty":penalty,
            "damage_taken":max(0,int(before)-after),**({'damage_type':damage_type,'damage_before_defenses':before_defenses,'damage_after_defenses':after_defenses} if damage_type or damage_context else {})}


def _current_participant(encounter: dict) -> dict | None:
    participants = encounter.get("participants") or []
    if not participants:
        return None
    index = int(encounter.get("turn_index") or 0) % len(participants)
    return participants[index]


def _expire_missing_target(db: sqlite3.Connection, effect: dict, changes: list[dict]) -> bool:
    # A deleted token must not freeze every subsequent round. Keep the original
    # effect for audit, but stop applying it; never redirect damage to an actor.
    table, column = ("character_states", "profile_id") if effect["target_type"] == "character" else ("session_workspace_tokens", "id")
    if db.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (effect["target_id"],)).fetchone() is not None:
        return False
    db.execute("UPDATE combat_effects SET active=0 WHERE id=?", (effect["id"],))
    changes.append({"expired": effect["id"], "reason": "target_missing", "target_type": effect["target_type"], "target_id": effect["target_id"]})
    return True


def _tick_round_effects(db: sqlite3.Connection, snapshot: dict, changes: list[dict], now: str) -> None:
    from .dorn_spells import elapse
    elapse(db, snapshot, 10, changes,now)
    for effect in snapshot["effects"]:
        if _expire_missing_target(db, effect, changes):
            continue
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


def replay_technique_effect(path: Path, *, actor_id: str, request_id: str,
                            source: str, target_id: str) -> dict | None:
    """Recover a fixed, server-defined buff before recomputing derived stats."""
    with closing(sqlite3.connect(path, timeout=30)) as db:
        previous = db.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?', (request_id,)).fetchone()
    if previous is None:
        return None
    saved = json.loads(previous[0])
    payload = saved[2] if len(saved) == 4 and isinstance(saved[2], dict) else {}
    if (saved[:2] != [actor_id, 'apply'] or payload.get('source') != source
            or payload.get('target_type') != 'character' or payload.get('target_id') != target_id):
        raise ValueError('request_id já utilizado com outro conteúdo')
    return json.loads(previous[1])


def effect_command(path: Path, *, actor_id: str, actor_role: str, request_id: str,
                   expected_version: int, action: str, payload: dict,
                   allow_player: bool = False) -> dict:
    if actor_role != "gm" and not (allow_player and actor_role == "player"):
        raise PermissionError("Somente o mestre controla efeitos e rodadas")
    if action.startswith('dorn_') and actor_role != 'gm':
        raise PermissionError('Somente o Mestre controla os protocolos de Dorn')
    if action in {'monster_breath','monster_contact'} and actor_role != 'gm':
        raise PermissionError('Somente o Mestre controla baforadas do bestiário')
    if not 8 <= len(request_id) <= 120:
        raise ValueError("request_id inválido")
    # A version is a precondition for a NEW command, not its identity. A retry
    # after a lost reply must recover its receipt even after the clock advances.
    # Server-derived diagnostic sheet metadata changes after the command. It
    # is execution context, not user intent; retain legacy receipts as well.
    intent = {key: value for key, value in payload.items() if key != '_definition'} if action == 'dorn_diagnose' else {k:v for k,v in payload.items() if not k.startswith('_server_')} if action=='monster_contact' else payload
    fingerprint = json.dumps([actor_id, action, intent, None], sort_keys=True)
    init_effects(path)
    with closing(sqlite3.connect(path, timeout=30)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute("SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?", (request_id,)).fetchone()
        if previous:
            saved = json.loads(previous[0])
            saved_intent = {key: value for key, value in saved[2].items() if key != '_definition'} if len(saved) == 4 and action == 'dorn_diagnose' and isinstance(saved[2], dict) else saved[2] if len(saved) == 4 else None
            if action=='monster_contact' and isinstance(saved_intent,dict):saved_intent={k:v for k,v in saved_intent.items() if not k.startswith('_server_')}
            if len(saved) != 4 or saved[:2] != [actor_id, action] or saved_intent != intent:
                raise ValueError("request_id já utilizado com outro conteúdo")
            return json.loads(previous[1])
        snapshot = effect_snapshot(db)
        if snapshot["version"] != expected_version:
            raise ValueError("Estado dos efeitos mudou. Atualize antes de continuar.")
        now = datetime.now(timezone.utc).isoformat()
        changes = []
        protocol_result = None
        if action == 'monster_contact':
            from .monster_contacts import command
            protocol_result=command(db,snapshot,payload,now,request_id)
            changes.append(protocol_result)
        elif action == 'parasite_remove':
            from .monster_parasites import remove
            protocol_result=remove(db,snapshot,actor_id,actor_role,payload,now,request_id)
            changes.append(protocol_result)
        elif action == 'monster_breath':
            from .monster_runtime import command as monster_command
            protocol_result=monster_command(db,snapshot,payload,now,request_id)
            changes.append(protocol_result)
        elif action == 'raziel_skill':
            if actor_role!='gm' and actor_id!='raziel':raise PermissionError('Somente Raziel ou o Mestre usa este poder')
            from .raziel_pipeline import command as raziel_command
            protocol_result=raziel_command(db,snapshot,now,payload)
            changes.append(protocol_result)
        elif action == 'hemomancy_mark':
            if actor_role != 'gm' and actor_id != 'raziel':
                raise PermissionError('Somente Raziel ou o Mestre usa Marca Rubra')
            from .hemomancy import mark_command
            protocol_result = mark_command(db, snapshot, now, payload, request_id, actor_role)
            changes.append(protocol_result)
        elif action == 'hemomancy_shield':
            if actor_role != 'gm' and actor_id != 'raziel':
                raise PermissionError('Somente Raziel ou o Mestre usa este escudo')
            from .hemomancy import shield_command
            protocol_result = shield_command(db, snapshot, now, payload, request_id)
            changes.append(protocol_result)
        elif action == 'vezemir_skill':
            from .vezemir_skills import cast
            protocol_result=cast(db,snapshot,payload,now,actor_id,actor_role)
            changes.append(protocol_result)
        elif action == 'vine_cast':
            from .session6_rewards import cast_vines
            changes.append(cast_vines(db, snapshot, payload, now, actor_id, actor_role))
        elif action in {'dorn_spell_cast','dorn_spell_time','dorn_spell_end','dorn_levitate_move','dorn_levitate_stabilize'}:
            from .dorn_spells import command
            protocol_result = command(db, snapshot, action, payload, now)
            changes.append(protocol_result)
        elif action in {"dorn_guard", "dorn_vanguard", "dorn_diagnose"}:
            from .dorn_protocols import command
            protocol_result = command(db, snapshot, action, payload, now)
            changes.append(protocol_result)
        elif action in {"necro_spell_cast", "necro_spell_end", "necro_spell_time"}:
            if actor_role != "gm" and actor_id != "morthak":
                raise PermissionError("Somente Morthak (ou o Mestre) conjura estas magias")
            from .necromancer_spells import command
            protocol_result = command(db, snapshot, action, payload, now, actor_id, actor_role)
            changes.append(protocol_result)
        elif action in {"start", "initiative", "next_turn", "end"}:
            encounter = snapshot.get("encounter") or {}
            if action == "start" and encounter.get("active"):
                raise ValueError("Já existe um combate ativo. Encerre-o ou ajuste a iniciativa.")
            if action != "start" and not encounter.get("active"):
                raise ValueError("Nenhum combate ativo")
            if action == "end":
                if encounter.get('battle_mode'):
                    restore_exploration(db, encounter, now)
                encounter["active"] = False
            elif action == "next_turn":
                participants = encounter.get("participants") or []
                if not participants:
                    raise ValueError("O combate não possui participantes")
                current = _current_participant(encounter)
                requested_actor = payload.get("actor")
                from .necromancer_spells import finish_target_turn
                finish_target_turn(db,current)
                if actor_role == "player":
                    owns_turn = current is not None and current.get("target_type") == "character" and current.get("target_id") == actor_id
                    if current and current.get('target_type') == 'token':
                        token = db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?', (current['target_id'],)).fetchone()
                        owns_turn = token is not None and json.loads(token[0] or '{}').get('summon', {}).get('caster') == actor_id
                    if not owns_turn:
                        raise PermissionError("Somente o participante atual pode encerrar este turno")
                    requested_key = (requested_actor.get('target_type'), requested_actor.get('target_id')) if isinstance(requested_actor, dict) else (None, None)
                    if current is None or requested_key not in {(current.get('target_type'), current.get('target_id')), ('character', actor_id)}:
                        raise PermissionError("Somente o participante atual pode encerrar este turno")
                previous_index = int(encounter.get("turn_index") or 0) % len(participants)
                next_index = (previous_index + 1) % len(participants)
                if next_index == 0:
                    _tick_round_effects(db, snapshot, changes, now)
                    db.execute("UPDATE combat_effect_clock SET round=round+1 WHERE id=1")
                encounter["turn_index"] = next_index
                encounter["turn_sequence"] = int(encounter.get("turn_sequence") or 0) + 1
                encounter["action_committed"] = False
                encounter["attacks_used"] = 0
                encounter.pop('pending_attack', None)
                encounter.pop('consumable_used', None)
                encounter.pop("attack_limit", None)
                encounter["turn_started_at"] = now
                encounter["last_transition_by"] = actor_id
            else:
                participants = payload.get("participants") or []
                from .monster_contacts import is_statless
                if any(is_statless(db,p.get("target_type"),p.get("target_id")) for p in participants):
                    raise ValueError("A Esfera é um perigo de cenário e não entra na iniciativa normal")
                if action == 'initiative' and encounter.get('battle_mode'):
                    if payload.get('map_id') and payload['map_id'] != encounter.get('map_id'):
                        raise ValueError('Encerre o combate antes de trocar a arena')
                    previous_members = {(p['target_type'], p['target_id']) for p in encounter.get('participants', [])}
                    new_members = {(p.get('target_type'), p.get('target_id')) for p in participants}
                    if not previous_members.issubset(new_members):
                        raise ValueError('Encerre o combate antes de remover participantes da arena')
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
                # Controlled summons follow their caster, including after initiative edits.
                summon_groups = {}
                caster_ids = {p['target_id'] for p in ordered if p['target_type'] == 'character'}
                for participant in ordered:
                    if participant['target_type'] != 'token':
                        continue
                    row = db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?', (participant['target_id'],)).fetchone()
                    caster = ((json.loads(row[0] or '{}').get('summon') or {}).get('caster')) if row else None
                    if caster in caster_ids:
                        summon_groups.setdefault(caster, []).append(participant)
                summon_ids = {p['target_id'] for group in summon_groups.values() for p in group}
                ordered = [item for participant in ordered if not (participant['target_type'] == 'token' and participant['target_id'] in summon_ids)
                    for item in [participant, *(summon_groups.get(participant['target_id'], []) if participant['target_type'] == 'character' else [])]]
                if action == 'initiative':
                    old_participants = {(p['target_type'], p['target_id']): p for p in encounter.get('participants', [])}
                    for participant in ordered:
                        old = old_participants.get((participant['target_type'], participant['target_id']), {})
                        for field in ('token_id', 'controller_id'):
                            if field in old:
                                participant[field] = old[field]
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
                    **({key: encounter[key] for key in ('battle_mode', 'return_map_id', 'return_tokens') if key in encounter} if action == 'initiative' else {}),
                    "active": True,
                    "started_at": encounter.get('started_at', now) if action == 'initiative' else now,
                    "map_id": str(payload.get("map_id") or encounter.get("map_id") or "default"),
                    "title": str(payload.get("title") or encounter.get("title") or "Combate")[:120],
                    "participants": ordered,
                    "turn_index": turn_index,
                    "turn_sequence": int(encounter.get("turn_sequence") or 0) + (0 if action == 'initiative' else 1),
                    "action_committed": encounter.get('action_committed', False) if action == 'initiative' else False,
                    **({key: encounter[key] for key in ('attacks_used', 'attack_limit', 'movement', 'pending_attack', 'consumable_used') if key in encounter} if action == 'initiative' else {}),
                    "turn_started_at": now,
                    **context,
                }
                if action == "start":
                    if payload.get('battle_mode'):
                        encounter['battle_mode'] = True
                        stage_battle(db, encounter, now)
                    db.execute("UPDATE combat_effect_clock SET round=1 WHERE id=1")
                elif encounter.get('battle_mode'):
                    additions = [p for p in ordered if (p['target_type'], p['target_id']) not in previous_members]
                    if additions:
                        stage_battle(db, encounter, now, participants=additions)
            if action in {'start', 'next_turn'}:
                from .monster_runtime import turn_start as monster_turn
                current_round=db.execute('SELECT round FROM combat_effect_clock WHERE id=1').fetchone()[0]
                monster_turn(db,_current_participant(encounter),encounter,current_round,now,request_id)
                from .raziel_pipeline import turn_start as raziel_turn
                from .dorn_recharge import turn_start as dorn_turn
                if action=='start':dorn_turn(db,{'target_type':'character','target_id':'dorn7'},encounter,now,request_id,starting=True)
                raziel_turn(db,_current_participant(encounter),encounter,now,request_id)
                if not (action=='start' and (_current_participant(encounter) or {}).get('target_id')=='dorn7'):
                    dorn_turn(db,_current_participant(encounter),encounter,now,request_id)
                from .session6_rewards import vine_turn
                from .vezemir_skills import target_turn
                from .necromancer_spells import touch_turn
                from .hemomancy import turn_start as hemomancy_turn
                target_turn(db,_current_participant(encounter),now,request_id)
                from .monster_parasites import turn_start as parasite_turn
                while parasite_turn(db,_current_participant(encounter),encounter,now,request_id) or hemomancy_turn(db,_current_participant(encounter),encounter,now,request_id+':'+str(encounter.get('turn_sequence',0))) or touch_turn(db,_current_participant(encounter),now,request_id+':'+str(encounter.get('turn_sequence',0)),encounter=encounter) or vine_turn(db, _current_participant(encounter), now, request_id, encounter):
                    from .necromancer_spells import finish_target_turn
                    finish_target_turn(db,_current_participant(encounter))
                    members = encounter['participants']
                    encounter['turn_index'] = (encounter['turn_index'] + 1) % len(members)
                    encounter['turn_sequence'] = int(encounter.get('turn_sequence') or 0) + 1
                    if encounter['turn_index'] == 0:
                        _tick_round_effects(db, snapshot, changes, now)
                        db.execute('UPDATE combat_effect_clock SET round=round+1 WHERE id=1')
                    target_turn(db,_current_participant(encounter),now,request_id+':'+str(encounter.get('turn_sequence',0)))
                    monster_turn(db,_current_participant(encounter),encounter,db.execute('SELECT round FROM combat_effect_clock WHERE id=1').fetchone()[0],now,request_id)
                    raziel_turn(db,_current_participant(encounter),encounter,now,request_id)
                    dorn_turn(db,_current_participant(encounter),encounter,now,request_id)
            if action == 'end':
                from .hemomancy import end_combat as end_hemomancy
                end_hemomancy(db)
                db.execute("UPDATE combat_effects SET active=0 WHERE json_extract(data_json,'$.necro_spell')='clonagem'")
                db.execute("UPDATE combat_effects SET active=0 WHERE json_extract(data_json,'$.skill')='provocacao' OR json_extract(data_json,'$.dot_hp')=1 OR json_extract(data_json,'$.necro_spell')='aterrorrizar'")
                db.execute("UPDATE combat_effects SET active=0 WHERE json_extract(data_json,'$.monster_condition') IS NULL AND (json_extract(data_json,'$.reward')='vines' OR json_extract(data_json,'$.immobilized')=1)")
                for effect in snapshot['effects']:
                    if effect.get('duration') == 'rounds':
                        db.execute('UPDATE combat_effects SET active=0 WHERE id=?', (effect['id'],))
                        changes.append({'expired': effect['id']})
            if action in {'start','next_turn'}:
                from .morthak_high_spells import clone_turn
                clone_turn(db,encounter,now)
            db.execute("UPDATE combat_effect_clock SET encounter_json=? WHERE id=1", (json.dumps(encounter),))
            # Guard lasts until Dorn becomes current again, not until a global round tick.
            new_current = _current_participant(encounter)
            if action in {'start', 'end'} or (action == 'next_turn' and new_current and new_current.get('target_type') == 'character' and new_current.get('target_id') == 'dorn7'):
                for effect in snapshot['effects']:
                    if effect.get('protocol') == 'guard':
                        db.execute('UPDATE combat_effects SET active=0 WHERE id=?', (effect['id'],))
                        changes.append({'expired': effect['id']})
            changes.append({"encounter": encounter})
        elif action == "apply":
            target_type, target_id = payload.get("target_type"), payload.get("target_id")
            if target_type == 'character':
                from .construct_rules import validate_effect, validate_healing
                validate_effect(db, target_id, payload.get('effect_category'))
                if (payload.get('modifiers') or {}).get('hp_per_round', 0) > 0:
                    validate_healing(db, target_id, payload.get('effect_category'))
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
                from .battle_mode import require_battle_turn
                require_battle_turn(db, snapshot, combat_actor.get('target_id'))
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
                if not isinstance(resource, dict) or not resource.get('character_id') or (actor_role != 'gm' and resource.get("character_id") != actor_id):
                    raise ValueError("Recurso de habilidade inválido")
                resource_character_id = str(resource['character_id'])
                from .battle_mode import require_battle_turn
                require_battle_turn(db, snapshot, resource_character_id)
                resource_key = str(resource.get("key") or "").strip()
                resource_cost = resource.get("cost")
                if not resource_key or type(resource_cost) is not int or not 1 <= resource_cost <= 999:
                    raise ValueError("Custo de habilidade inválido")
                state_row = db.execute("SELECT state_json FROM character_states WHERE profile_id=?", (resource_character_id,)).fetchone()
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
                    (json.dumps(character_state, ensure_ascii=False), now, resource_character_id),
                )
                resource_change = {"before": before_resource, "after": resources[resource_index]}
            if payload.get('_rounds_formula'):
                if duration != 'rounds':
                    raise ValueError('Rolagem de duração exige efeito por rodadas')
                rounds = int(roll_formula(str(payload['_rounds_formula']))['total'])
                if not 1 <= rounds <= 999:
                    raise ValueError('Duração inválida')
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
            if action == 'round':
                from .dorn_spells import elapse
                elapse(db, snapshot, 10, changes,now)
            if action == "remove" and not any(e["id"] == payload.get("id") for e in snapshot["effects"]):
                raise ValueError("Efeito não encontrado")
            for effect in snapshot["effects"]:
                if action == "round" and _expire_missing_target(db, effect, changes):
                    continue
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
        from .vezemir_skills import cleanup_lifeline
        cleanup_lifeline(db,now)
        from .morthak_high_spells import cleanup
        cleanup(db,now)
        from .battle_mode import retire_defeated
        retired = retire_defeated(db, now)
        if retired:
            changes.append({'defeated': retired})
        from .bat_swarm import sync as sync_swarm
        sync_swarm(db,now)
        result = effect_snapshot(db)
        public_character = None
        public_label = None
        if action == 'raziel_skill':
            public_character,public_label='raziel',(protocol_result or {}).get('spell')
        elif action == 'vine_cast':
            public_character, public_label = 'vezemir', 'Pulseira de Vinhas'
        elif action == 'hemomancy_shield':
            public_character, public_label = 'raziel', 'Bastião Carmesim'
        elif action == 'hemomancy_mark':
            public_character, public_label = 'raziel', 'Marca Rubra'
        elif action == 'dorn_spell_cast':
            public_character, public_label = 'dorn7', (protocol_result or {}).get('spell')
        elif action == 'necro_spell_cast':
            public_character, public_label = 'morthak', (protocol_result or {}).get('spell')
        elif action == 'vezemir_skill':
            public_character, public_label = 'vezemir', (protocol_result or {}).get('spell')
        elif action == 'dorn_guard' or (action == 'dorn_vanguard' and payload.get('enabled') is True):
            public_character, public_label = 'dorn7', 'Protocolo de Guarda' if action == 'dorn_guard' else 'Protocolo de Vanguarda'
        elif action == 'apply' and actor_role == 'player':
            public_character = (payload.get('resource') or {}).get('character_id') or (payload.get('combat_actor') or {}).get('target_id')
            public_label = payload.get('label') if public_character else None
        if public_character and public_label:
            append_session_ledger_event(db, source_type='ability_activation', source_id=request_id, event_kind='action',
                actor_id=actor_id, actor_name=str(public_character), actor_role=actor_role, character_id=str(public_character),
                title=f'Usou {public_label}', detail={'ability_name': public_label},
                visibility='table', created_at=now, game_session_id=(result.get('encounter') or {}).get('game_session_id'))
        if protocol_result is not None:
            result['protocol_result'] = protocol_result
        append_session_ledger_event(db, source_type="combat_effect", source_id=request_id, event_kind="state",
                                   actor_id=actor_id, actor_name="Mestre", actor_role="gm", character_id=None, title=f"Efeitos: {action}",
                                   detail={"action": action, "changes": changes, "round": result["round"]}, visibility="gm", created_at=now,
                                   game_session_id=(result.get("encounter") or {}).get("game_session_id"))
        db.execute("INSERT INTO combat_effect_commands VALUES(?,?,?)", (request_id, fingerprint, json.dumps(result)))
        return result


def apply_definition_effects(definition: dict, effects: list[dict]) -> dict:
    result = copy.deepcopy(definition)
    totals = {key: sum(e["modifiers"].get(key, 0) for e in effects) for key in MODIFIERS}
    difficult = any(e.get('difficult_tests') for e in effects)
    if difficult:
        totals['attack_bonus'] -= 2
    darkness_count=sum(e.get('condition')=='magical_darkness' for e in effects)
    if darkness_count>1:
        totals['attack_bonus']+=5*(darkness_count-1)  # blindness is not cumulative
    result["active_effects"] = effects
    # Strength flows into melee the Old Dragon way: the raised score moves the
    # attribute modifier, which carries both the attack roll and the damage.
    original_attributes=dict(result.get('attributes') or {})
    projected_attributes=dict(original_attributes)
    if projected_attributes.get('strength') is not None:
        projected_attributes['strength']=int(projected_attributes['strength'])+totals['strength_bonus']
    from .monster_poison_runtime import project_attributes
    projected_attributes=project_attributes(projected_attributes,effects)
    def modifier_delta(key):
        try:return _attribute_modifier(int(projected_attributes[key]))-_attribute_modifier(int(original_attributes[key]))
        except (TypeError,ValueError,KeyError):return 0
    strength_delta=modifier_delta('strength');dexterity_delta=modifier_delta('dexterity')
    for attack in result.get("attacks") or []:
        melee_delta = strength_delta if attack.get("id") == "melee" or attack.get('slot') in {'melee','touch'} else 0
        ranged_delta = dexterity_delta if attack.get('id')=='ranged' or attack.get('slot')=='ranged' else 0
        levitation_delta = min([0]+[int(e.get('levitation_ranged_penalty',-1)) for e in effects if e.get('spell')=='levitacao']) if attack.get('id')=='ranged' else 0
        attack["attack_bonus"] = int(attack.get("attack_bonus") or 0) + totals["attack_bonus"] + melee_delta + ranged_delta + levitation_delta
        attack["effect_attack_bonus"] = totals["attack_bonus"] + melee_delta + ranged_delta + levitation_delta
        attack["attack_count"] = max(1, min(10, int(attack.get("attack_count", 1)) + totals["extra_attacks"]))
        damage_delta = totals["damage_bonus"] + melee_delta
        attack['effect_damage_bonus'] = damage_delta
        if attack.get("damage") and damage_delta and not attack.get("effect_only"):
            parsed = parse_formula(attack["damage"])
            # Preserve all dice; only change the flat modifier.
            base = parsed.formula.split("+")[0].split("-")[0]
            modifier = parsed.modifier + damage_delta
            attack["damage"] = f"{base}{modifier:+d}" if modifier else base
        attack["extra_damage_formulas"] = [
            effect["damage_bonus_formula"] for effect in effects if effect.get("damage_bonus_formula")
        ]
    defenses = result.get("defenses") or {}
    if any(e.get('environmental') for e in effects):
        conditional=defenses.setdefault('conditional_saving_throw_bonuses',{})
        conditional['dexterity']=int(conditional.get('dexterity') or 0)-2
    if difficult:
        defenses['saving_throw_bonus'] = int(defenses.get('saving_throw_bonus') or 0) - 2
    if any(e.get('condition')=='magical_darkness' for e in effects):
        defenses['saving_throw_bonus']=int(defenses.get('saving_throw_bonus') or 0)-5
        result['vision_blocked']=True
    if defenses.get("armor_class") is not None:
        defenses["armor_class"] += totals["armor_class_bonus"]
    if projected_attributes!=original_attributes:
        result['base_attributes']=result.get('base_attributes') or original_attributes
        result['attributes']=projected_attributes
        for key,value in projected_attributes.items():
            if value is not None:result.setdefault('attribute_modifiers',{})[key]=_attribute_modifier(int(value))
    # Efeito legado: atributo -2. Aterrorizar aprovado: modificador d20 -2.
    difficult_sources = [e["id"] for e in effects if e.get("difficult_tests")]
    if difficult_sources:
        base_attributes = result.get("base_attributes") or result.get("attributes") or {}
        modifiers = result.setdefault("attribute_modifiers", {})
        adjusted = []
        for key in ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"):
            try:
                if base_attributes.get(key) is None:
                    continue
                if any(e.get('necro_spell')=='aterrorrizar' or e.get('d20_penalty') for e in effects):
                    modifiers[key] = int(modifiers.get(key,_attribute_modifier(int(base_attributes[key]))))-2
                else:modifiers[key] = _attribute_modifier(int(base_attributes[key]) - 2)
                adjusted.append(key)
            except (TypeError, ValueError):
                continue
        result["difficult_tests"] = {"attributes": adjusted, "sources": difficult_sources}
        if any(e.get('necro_spell')=='aterrorrizar' or e.get('d20_penalty') for e in effects):
            item_effects=result.get('item_effects') or {}
            if item_effects.get('skill_modifiers'):
                item_effects['skill_modifiers']={k:int(v)-2 for k,v in item_effects['skill_modifiers'].items()}
            if defenses.get('initiative') is not None: defenses['initiative']-=2
    movement_multiplier = max([1] + [int(effect.get("modifiers", {}).get("movement_multiplier") or 1) for effect in effects])
    if movement_multiplier > 1 and result.get("movement"):
        match = re.search(r"\d+(?:[.,]\d+)?", str(result["movement"]))
        if match:
            value = float(match.group(0).replace(",", ".")) * movement_multiplier
            shown = str(int(value)) if value.is_integer() else str(value).replace(".", ",")
            result["movement"] = f"{shown} m · Velocidade ×{movement_multiplier}"
    return result
