"""Motor genérico de magias e ações usáveis: JP + dano extraídos do texto.

 Toda magia do grimório vira rolável: JP (JPD/JPC/JPS) e dado de dano vêm da
 ficha; o que o texto não define (área exata, efeitos narrativos) o Mestre
 adjudica — a resposta marca `manual` nesses pontos. Segue o idioma de JP
 já em produção (dorn_spells/morthak: 1d20 + bônus vs JP da vítima).
"""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dice_rolls import resolve_character_roll, roll_formula
from .session_ledger import append_session_ledger_event
from .spell_catalog import get_catalog_spell
from .damage_profiles import infer_damage_type
from .spell_command_receipts import command_receipt, read_receipt, replay_before_resolution, save_receipt

_SAVE_ATTR = {"JPD": "dexterity", "JPC": "constitution", "JPS": "wisdom"}


def _spell_damage(spell):
    """Only dice explicitly tied to injury; counts/durations/buffs are not damage."""
    text = re.sub(r'(?<=[A-Za-zÀ-ú])-\s+(?=[a-zà-ú])', '', spell.get('description') or '')
    if re.search(r'\sR$', spell.get('name','')) and re.search(r'revers|efeito contr[aá]rio', text, re.I):
        return None
    formulas=[]
    for match in re.finditer(r'\d+\s*[dD]\s*\d+(?:\s*[+-]\s*\d+)?',text):
        before=text[max(0,match.start()-180):match.start()]
        after=text[match.end():match.end()+65]
        if re.search(r'(?:m[aá]ximo\s*(?:de)?|por exemplo[^.]*|ou seja[^.]*)\s*$',before,re.I):continue
        if re.match(r'\s*(?:de\s+)?(?:rodadas?|turnos?|dias?|horas?|minutos?|criaturas?|alvos?|dados? de vida|imagens?|pontos? de For[çc]a)\b',after,re.I):continue
        explicit_after=re.match(r'\s*(?:pontos?\s+(?:de\s+)?)?(?:de\s+)?dano\b',after,re.I)
        clause=re.split(r'[.;!?]',before)[-1]
        explicit_before=re.search(r'\bdano\b',clause,re.I) and not re.search(r'n[aã]o[^.]{0,30}\bdano\b',clause,re.I)
        hp_loss=re.match(r'\s*pontos? de vida\b',after,re.I) and re.search(r'perd|sofr|inflig|caus|retira',clause,re.I) and not re.search(r'cura|recuper|restaura',clause,re.I)
        if explicit_after or explicit_before or hp_loss:
            formulas.append(re.sub(r'\s+','',match.group()).lower())
    distinct=list(dict.fromkeys(formulas))
    return distinct[0] if len(distinct)==1 else None


def derive_spell_mechanic(spell: dict[str, Any]) -> dict[str, Any]:
    """Extrai mecânica rolável da ficha. Sem JP/dano no texto → manual."""
    jp_text = f"{spell.get('jogada_protecao') or ''}"
    save_match = re.search(r"\bJP\s*([DCS])\b", jp_text, re.IGNORECASE)
    save = f"JP{save_match.group(1).upper()}" if save_match else None
    if re.search(r"nenhuma", jp_text, re.IGNORECASE):
        save = None
    save_effect = None
    if save:
        save_effect = "halves" if re.search(r"reduz|metade", jp_text, re.IGNORECASE) else "negates"
    damage = _spell_damage(spell)
    from .catalog_spell_contracts import reviewed_heal, reviewed_condition_cure
    healing = reviewed_heal(spell)
    condition_cure = reviewed_condition_cure(spell)
    progression=None
    text=re.sub(r'(?<=[A-Za-zÀ-ú])-\s+(?=[a-zà-ú])','',spell.get('description') or '')
    per_level=re.search(r'\b1d(\d+)\s+(?:pontos?\s+de\s+dano\s+)?por\s+n[íi]vel',text,re.I)
    if per_level and damage==f'1d{per_level.group(1)}':
        cap=re.search(r'm[aá]ximo\s+(?:de\s+)?(\d+)d'+per_level.group(1)+r'\b',text,re.I)
        progression={'die_size':int(per_level.group(1)),'maximum_dice':int(cap.group(1)) if cap else None}
    from .action_distances import metre_formula
    range_formula = metre_formula(spell.get('alcance'))
    return {"save": save, "save_effect": save_effect,"damage_type":infer_damage_type(spell.get('name'),spell.get('description')),
            "damage": None if healing else damage, "healing": healing['formula'] if healing else None,
            "damage_per_level":progression,
            "range_text": (spell.get("alcance") or "").strip() or None,
            "range_m": None if condition_cure or not range_formula else range_formula[0] if not range_formula[1] else None,
            "range_m_per_level": condition_cure['range_m_per_level'] if condition_cure else None,
            "area": (spell.get("area_efeito") or "").strip() or None,
            "duration": (spell.get("duracao") or "").strip() or None}


def scaled_spell_mechanic(spell, level):
    """Resolve only explicit per-level damage/range; geometry and durations stay separate."""
    mechanic=derive_spell_mechanic(spell)
    if mechanic.get('range_m_per_level'):
        if type(level) is not int or not 1 <= level <= 100:
            raise ValueError('Defina o nível de conjurador para calcular o alcance desta magia.')
        mechanic['range_m'] = mechanic['range_m_per_level'] * level
        return mechanic
    from .action_distances import metre_formula, resolved_metres
    expression=metre_formula(spell.get('alcance'))
    if expression:mechanic['range_m']=resolved_metres(spell.get('alcance'),level)
    explicit_spell = spell.get('id') in {'arcana-dardos-misticos', 'divina-dardo-de-brasa', 'arcana-toque-chocante'}
    if not mechanic['damage_per_level'] and not explicit_spell:return mechanic
    if type(level) is not int or not 1<=level<=100:raise ValueError('Defina o nível de conjurador; não é derivado dos DV nem presumido como 1')
    if mechanic['damage_per_level']:
        spec=mechanic['damage_per_level'];count=min(level,spec['maximum_dice']) if spec['maximum_dice'] else level
        mechanic['damage']=f"{count}d{spec['die_size']}"
    # Reviewed literal spell rules; no general inference from examples or dice counts.
    if spell.get('id') == 'arcana-toque-chocante':
        mechanic['damage'] = f'1d8+{level}'
    elif spell.get('id') in {'arcana-dardos-misticos', 'divina-dardo-de-brasa'}:
        count = min(5, (level + 1) // 2) if spell['id'] == 'arcana-dardos-misticos' else 1 + (level - 1) // 3
        bonus = count if spell['id'] == 'arcana-dardos-misticos' else count * min(level, 5)
        mechanic.update(damage=f'{count}d4+{bonus}', projectiles=count,
                        projectile_allocation='all_to_one_target')
    return mechanic


def _caster_level(connection,kind,identity,tradition):
    if kind=='character':
        row=connection.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?',(identity,)).fetchone()
        value=json.loads(row[0]).get('level') if row else None
        if type(value) is int and value>0:return value
        row=connection.execute('SELECT data_json FROM character_sheets WHERE profile_id=?',(identity,)).fetchone()
        value=(json.loads(row[0]).get('character_class') or {}).get('level') if row else None
        return value if type(value) is int and value>0 else None
    row=connection.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
    sheet=json.loads(row[0] or '{}') if row else {}
    value=sheet.get('spellcaster_level')
    if type(value) is int and value>0:return value
    from .monster_actions import build_action_map
    actions=build_action_map('',[],sheet.get('abilities') or [])
    levels={e['spellcasting']['caster_level'] for e in actions['spellcasting'] if e.get('spellcasting',{}).get('tradition')==tradition and e['spellcasting'].get('caster_level')}
    return next(iter(levels)) if len(levels)==1 else None


def _victim(db: sqlite3.Connection, kind: str, identity: str) -> dict[str, Any]:
    from .dorn_spells import target
    return target(db, kind, identity)


def _caster_name(db: sqlite3.Connection, kind: str, identity: str) -> str:
    if kind == "token":
        row = db.execute("SELECT name FROM session_workspace_tokens WHERE id=?", (identity,)).fetchone()
        if not row:
            raise ValueError("Conjurador não encontrado")
        return str(row[0])
    return str(_victim(db, "character", identity)["name"])


def _roll_save(victim: dict[str, Any], save: str, roll_mode: str, d20: int | None) -> dict[str, Any]:
    from .character_play import attribute_modifier
    from .dice_rolls import parse_formula
    attribute = _SAVE_ATTR[save]
    original = int((victim.get("attributes") or {}).get(attribute, 10))
    attr_bonus = int(attribute_modifier(original) or 0)
    definition = {"name": victim["name"],
                  "defenses": {**victim["defenses"], "saving_throw_bonus": int(victim["defenses"].get("saving_throw_bonus") or 0)}}
    spec = resolve_character_roll(definition, [], "saving_throw", attribute)
    form_bonus = parse_formula(spec.formula).modifier
    if roll_mode == "physical":
        if d20 is None or not 1 <= int(d20) <= 20:
            raise ValueError("Informe o d20 físico (1-20)")
        rolled = int(d20)
    elif roll_mode == "digital":
        rolled = int(roll_formula("1d20")["total"])
    else:
        raise ValueError("Modo de rolagem inválido")
    total = rolled + form_bonus + attr_bonus
    return {"d20": rolled, "save_bonus": form_bonus + attr_bonus, "total": total,
            "target": spec.target_value, "success": total >= spec.target_value}


def _apply_damage(db: sqlite3.Connection, kind: str, identity: str, damage: int,damage_profile=None) -> dict[str, int]:
    from .combat_effects import change_hp
    result = change_hp(db, kind, identity, -max(0, damage), _now_iso(),damage_context=damage_profile)
    return {**result, "before": result["hp_before"], "after": result["hp_after"]}


def _resolve_targets(database_path: Path, *, label: str, source: str, save: str | None, save_effect: str | None,
                     damage_dice: str | None, caster_name: str, caster_id: str, caster_token_id: str | None,
                     targets: list[dict[str, str]], roll_mode: str, d20: int | list[int] | None,
                     range_spec: dict[str, Any] | None = None,damage_profile=None,shared_damage=False,
                     receipt=None, healing_dice: str | None = None, condition_cure: dict | None = None,npc_spell_id: str | None = None) -> dict[str, Any]:
    from .config import get_settings
    from .combat_effects import effect_snapshot, init_effects
    from .battle_mode import commit_battle_action, require_battle_target, require_battle_turn
    from .action_range import enforce_action_range
    database_path = Path(database_path or get_settings().database_path)
    if not targets:
        raise ValueError("Informe ao menos um alvo")
    if roll_mode not in ("digital", "physical"):
        raise ValueError("Modo de rolagem inválido")
    if roll_mode == "physical" and (save or not (healing_dice or condition_cure)):
        dice = [int(value) for value in (d20 if isinstance(d20, list) else [d20])]
        if len(dice) != len(targets) or any(not 1 <= value <= 20 for value in dice):
            raise ValueError("Informe um d20 físico (1-20) por alvo")
    results = []
    init_effects(database_path)
    with closing(sqlite3.connect(str(database_path), timeout=30)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.row_factory = sqlite3.Row
        cached = read_receipt(connection, receipt)
        if cached is not None:
            return cached
        from .npc_spell_resources import require_use,consume
        npc_budget=require_use(connection,caster_token_id,npc_spell_id) if npc_spell_id and caster_token_id==caster_id else None
        victims = [_victim(connection, item["type"], item["id"]) for item in targets]
        identities = [(victim["type"], victim["id"]) for victim in victims]
        if len(set(identities)) != len(identities):
            raise ValueError("O mesmo alvo não pode ser atingido duas vezes na mesma seleção")
        if healing_dice:
            from .catalog_spell_contracts import require_healing_target
            for victim in victims:
                require_healing_target(connection, victim)
        snapshot = {}
        encounter = {}
        in_battle = False
        has_clock = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name='combat_effect_clock'").fetchone()
        if has_clock:
            snapshot = effect_snapshot(connection)
            encounter = snapshot.get("encounter") or {}
            in_battle = bool(encounter.get("active") and encounter.get("battle_mode"))
        if in_battle:
            require_battle_turn(connection, snapshot, caster_id)
            for item in targets:
                require_battle_target(connection, snapshot, item["type"], item["id"])
        from .magic_item_drums import assert_action
        assert_action(connection,caster_id)
        shared_roll=None
        for position, item in enumerate(targets):
            if range_spec is not None and caster_token_id is not None:
                outcome_range = enforce_action_range(database_path, attacker_token_id=caster_token_id,
                                                     target_type=item["type"], target_id=item["id"],
                                                     mode=range_spec["mode"], range_m=range_spec.get("range_m"),
                                                     range_cells=range_spec.get("range_cells"))
            else:
                outcome_range = {"checked": False}
            victim = victims[position]
            outcome: dict[str, Any] = {"target": victim["name"], "target_type": item["type"], "target_id": item["id"],
                                       "range": outcome_range}
            if save:
                physical = dice[position] if roll_mode == "physical" else None
                check = _roll_save(victim, save, roll_mode, physical)
                outcome["save"] = check
                resisted = bool(check["success"])
            else:
                resisted = False
            dealt = 0
            if healing_dice or condition_cure:
                if not outcome_range.get('checked'):
                    from .session_context import table_exists
                    if table_exists(connection, 'session_workspace_map_grids'):
                        grid = connection.execute('SELECT 1 FROM session_workspace_map_grids g '
                            'JOIN session_workspace_tokens t ON t.map_id=g.map_id WHERE t.id=?',
                            (caster_token_id,)).fetchone()
                        if caster_token_id is None and table_exists(connection, 'session_workspace_state'):
                            current = connection.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
                            map_id = encounter.get('map_id') if in_battle else (current[0] if current else None)
                            grid = connection.execute('SELECT 1 FROM session_workspace_map_grids WHERE map_id=?', (map_id,)).fetchone()
                        if grid:
                            raise ValueError('Posicione conjurador e alvo no grid para validar o alcance.')
            if condition_cure:
                from .catalog_spell_contracts import remove_reviewed_condition
                outcome.update(remove_reviewed_condition(connection, victim, condition_cure, _now_iso()))
            elif healing_dice:
                healing_roll = roll_formula(healing_dice)
                rolled = int(healing_roll['total'])
                from .combat_effects import change_hp
                changed = change_hp(connection, victim['type'], victim['id'], max(0, rolled), _now_iso())
                outcome.update(healing_rolled=rolled, healing_roll=healing_roll, healing_applied=changed['hp_after'] - changed['hp_before'],
                    damage_dealt=0, hp={**changed, 'before':changed['hp_before'], 'after':changed['hp_after']})
            elif damage_dice:
                if not shared_damage or shared_roll is None:shared_roll=int(roll_formula(damage_dice)["total"])
                rolled=shared_roll
                if save and resisted:
                    dealt = rolled // 2 if save_effect == "halves" else 0
                else:
                    dealt = 0 if (save and save_effect == "negates" and resisted) else rolled
                outcome["damage_rolled"] = rolled
                outcome["damage_dealt"] = dealt
                outcome["hp"] = _apply_damage(connection, victim["type"], victim["id"], dealt,damage_profile)
                outcome['damage_dealt']=outcome['hp']['damage_taken']
            else:
                outcome["damage_dealt"] = 0
            outcome["resisted"] = resisted
            outcome["manual"] = True if condition_cure else (not outcome_range.get('checked')) if healing_dice else (
                damage_dice is None or (save is None and "efeito" in label.lower()))
            results.append(outcome)
        from .monster_runtime import public_token
        private = (caster_token_id is not None and not public_token(connection, caster_token_id)) or any(
            victim['type'] == 'token' and not public_token(connection, victim['id']) for victim in victims)
        append_session_ledger_event(connection, source_type=source, source_id=f"{caster_name}:{_now_slug()}",
                                    event_kind="action", actor_id="master", actor_name="Mestre", actor_role="gm",
                                    character_id=None, title=f"{caster_name} usou {label}",
                                    detail={"label": label, "results": results,**({'caster_resource':npc_budget} if npc_budget else {})}, visibility="gm" if private else "table", created_at=_now_iso())
        if in_battle:
            commit_battle_action(connection, snapshot)
        if npc_budget:consume(connection,caster_token_id,npc_budget,_now_iso())
        from .battle_mode import retire_defeated
        retire_defeated(connection, _now_iso())
        result = {"label": label, "caster": caster_name, "mechanic": {"save": save, "save_effect": save_effect, "damage": damage_dice, 'healing':healing_dice, 'damage_type':(damage_profile or {}).get('damage_type')},
                  "results": results,
                  "manual_note": ("Cura de PV aplicada. Sem posições de grid, o alcance por toque é assistido. Custos/repertório continuam assistidos."
                    if healing_dice else "Efeitos narrativos (área, duração, condições) ficam com o Mestre; aqui rolaram JP e dano.")
                    if any(outcome.get("manual") for outcome in results) else None}
        if condition_cure:
            result['mechanic'].update(condition_cure=condition_cure['condition'], range_m=(range_spec or {}).get('range_m'))
            result['manual_note'] = 'Paralisia individual identificada removida, sem alterar PV. Custos/repertório, barreiras, lentidão e imobilizações de área continuam assistidos. Sem grid, o alcance também é assistido; versão em grupo não executada.'
        if npc_budget:result['caster_resource']=npc_budget
        save_receipt(connection, receipt, result)
        return result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_slug() -> str:
    import uuid
    return uuid.uuid4().hex[:8]


def cast_spell(database_path: Path, *, spell_id: str, caster_type: str, caster_id: str,
               targets: list[dict[str, str]], roll_mode: str = "digital", d20: int | list[int] | None = None,
               damage_override: str | None = None, save_override: str | None = None,
               range_m: float | None = None, range_cells: int | None = None,
               request_id: str | None = None) -> dict[str, Any]:
    from .config import get_settings
    database_path = Path(database_path or get_settings().database_path)
    receipt = command_receipt(request_id, 'cast_spell', dict(spell_id=spell_id, caster_type=caster_type,
        caster_id=caster_id, targets=targets, roll_mode=roll_mode, d20=d20,
        damage_override=damage_override, save_override=save_override, range_m=range_m, range_cells=range_cells))
    cached = replay_before_resolution(database_path, receipt)
    if cached is not None:
        return cached
    spell = get_catalog_spell(spell_id)
    if spell is None:
        raise ValueError("Magia não encontrada no grimório")
    if not str(spell.get('description') or '').strip():
        raise ValueError('Magia sem descrição suficiente na fonte; execução assistida necessária.')
    from .catalog_spell_contracts import reviewed_heal, reviewed_condition_cure
    healing = reviewed_heal(spell, strict=True)
    condition_cure = reviewed_condition_cure(spell, strict=True)
    if healing:
        if len(targets) != 1:
            raise ValueError('Esta cura por toque exige exatamente um alvo.')
        if damage_override is not None or save_override is not None or range_m is not None or range_cells not in (None, 1):
            raise ValueError('Cura revisada usa sua fórmula normal e alcance por toque, sem sobrescritas.')
    if condition_cure:
        if len(targets) != 1:
            raise ValueError('Remover Paralisia automatizado exige um alvo único; a regra em grupo é assistida.')
        if any(value is not None for value in (damage_override,save_override,range_m,range_cells)):
            raise ValueError('Remoção revisada usa o alcance e efeito da fonte, sem sobrescritas.')
    if caster_type not in ("character", "token"):
        raise ValueError("Conjurador inválido")
    mechanic = derive_spell_mechanic(spell)
    save = save_override if save_override is not None else mechanic["save"]
    if save is not None and save not in _SAVE_ATTR:
        raise ValueError("JP inválida (use JPD, JPC, JPS ou nula)")
    damage = damage_override if damage_override is not None else mechanic["damage"]
    if damage is not None and not re.fullmatch(r"\d+\s*[dD]\s*\d+(?:\s*[+-]\s*\d+)?", damage.strip()):
        raise ValueError("Dado de dano inválido")
    from .config import get_settings
    database_path = Path(database_path or get_settings().database_path)
    with closing(sqlite3.connect(str(database_path), timeout=30)) as connection:
        connection.row_factory = sqlite3.Row
        from .item_grapple import assert_can_speak
        assert_can_speak(connection,caster_type,caster_id)
        caster_name = _caster_name(connection, caster_type, caster_id)
        caster_token_id = caster_id if caster_type == "token" else _character_token(connection, caster_id)
        level=_caster_level(connection,caster_type,caster_id,spell.get('tradition'))
    if condition_cure and (type(level) is not int or not 1 <= level <= 100):
        raise ValueError('Defina o nível de conjurador para calcular o alcance de Remover Paralisia.')
    from .action_distances import metre_formula
    formula=metre_formula(spell.get('alcance'))
    if level is not None or formula and formula[1] or (damage_override is None and (mechanic['damage_per_level'] or spell_id in {'arcana-dardos-misticos', 'divina-dardo-de-brasa', 'arcana-toque-chocante'})):
        mechanic=scaled_spell_mechanic(spell,level)
        if damage_override is None:damage=mechanic['damage']
    elif range_m is None and range_cells is None:
        mechanic=scaled_spell_mechanic(spell,None)
    if mechanic.get('projectiles') and len(targets) != 1:
        raise ValueError('Este modo concentra todos os dardos em um alvo; distribuição entre alvos ainda não configurada')
    if condition_cure:
        range_spec = {'mode':'ranged', 'range_m':condition_cure['range_m_per_level'] * level}
        save = None
        damage = None
    elif healing:
        range_spec = {'mode':'touch','range_cells':1}
    elif mechanic.get('range_m') is not None:
        if range_m is not None and range_m>mechanic['range_m']:
            raise ValueError('O alcance não pode exceder o máximo calculado da magia')
        range_spec = {'mode':'ranged','range_m':mechanic['range_m']}
    elif range_m is not None or range_cells is not None:
        range_spec: dict[str, Any] | None = {"mode": "ranged" if range_cells != 1 else "melee",
                                             "range_m": range_m, "range_cells": range_cells}
    elif (mechanic.get("range_text") or "").strip().lower().startswith("toque"):
        range_spec = {"mode": "touch", "range_cells": 1}
    elif mechanic.get("range_m"):
        range_spec = {"mode": "ranged", "range_m": mechanic["range_m"]}
    else:
        range_spec = None
    return _resolve_targets(database_path, label=spell["name"], source="spell_cast", save=save,
                            save_effect=mechanic["save_effect"], damage_dice=damage, caster_name=caster_name,
                            caster_id=caster_id, caster_token_id=caster_token_id,
                            targets=targets, roll_mode=roll_mode, d20=d20, range_spec=range_spec,
                            shared_damage=bool(re.search(r'jogar\s+o\s+dano\s+uma\s+vez',spell.get('description',''),re.I)),
                            damage_profile={'kind':'spell','magical':True,'damage_type':mechanic.get('damage_type')}, receipt=receipt,
                            healing_dice=healing['formula'] if healing else None, condition_cure=condition_cure,npc_spell_id=spell_id if caster_type=='token' else None)


def _character_token(connection: sqlite3.Connection, character_id: str) -> str | None:
    row = connection.execute("SELECT id FROM session_workspace_tokens WHERE character_id=? ORDER BY id LIMIT 1",
                             (character_id,)).fetchone()
    return str(row["id"]) if row else None


def execute_token_action(database_path: Path, *, token_id: str, ability_name: str,
                         targets: list[dict[str, str]], roll_mode: str = "digital",
                         d20: int | list[int] | None = None, damage_override: str | None = None,
                         range_m: float | None = None, range_cells: int | None = None,
                         request_id: str | None = None) -> dict[str, Any]:
    from .config import get_settings
    from .monster_actions import build_action_map
    database_path = Path(database_path or get_settings().database_path)
    receipt = command_receipt(request_id, 'execute_token_action', dict(token_id=token_id,
        ability_name=ability_name, targets=targets, roll_mode=roll_mode, d20=d20,
        damage_override=damage_override, range_m=range_m, range_cells=range_cells))
    cached = replay_before_resolution(database_path, receipt)
    if cached is not None:
        return cached
    # Catalog breaths must use the native command/receipt and authoritative area.
    # This legacy single-target endpoint cannot bypass their limits or passives.
    from .monster_runtime import token_monster
    from .monster_action_specs import monster_action_specs
    with closing(sqlite3.connect(str(database_path),timeout=30)) as native_db:
        monster,_=token_monster(native_db,token_id)
    if monster and any(s['name'].casefold()==ability_name.casefold() for s in monster_action_specs(monster)):
        raise ValueError('Use a baforada nativa pelo grid; o endpoint antigo não aplica seus limites')
    if monster:
        from .monster_exposures import exposure_specs
        if any(s['name'].casefold()==ability_name.casefold() for s in exposure_specs(monster)):
            raise ValueError('Use a exposição nativa pelo grid para confirmar contato visual ou área de gás')
        from .monster_riders import combat_rider_specs
        if any(s['name'].casefold()==ability_name.casefold() for s in combat_rider_specs(monster)['on_hit']):
            raise ValueError('Esta passiva é aplicada automaticamente ao acertar o ataque, sem ativação separada')
    with closing(sqlite3.connect(str(database_path), timeout=30)) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT name, sheet_json FROM session_workspace_tokens WHERE id=? AND token_type='monster'", (token_id,)).fetchone()
        if row is None:
            raise ValueError("Criatura não encontrada")
        sheet = json.loads(row["sheet_json"] or "{}")
        action_map = build_action_map(row["name"], sheet.get("attacks") or [], sheet.get("abilities") or [])
    ability = next((entry for entry in action_map["active_abilities"] + action_map["spellcasting"]
                    if entry["name"].casefold() == (ability_name or "").strip().casefold()), None)
    if ability is None:
        raise ValueError("Ação usável não encontrada (só usáveis e conjurações executam; passivas não)")
    if sheet.get('spell_repertoire') is not None and ability.get('kind')=='spellcasting':
        raise ValueError('Use a magia específica do repertório; a conjuração genérica não aplica seus limites')
    save = ability.get("save")
    damage = damage_override if damage_override is not None else ability.get("reference_dice")
    if damage is not None and not re.fullmatch(r"\d+\s*[dD]\s*\d+(?:\s*[+-]\s*\d+)?", str(damage).strip()):
        raise ValueError("Dado de dano inválido")
    description = (ability.get("description") or "")
    save_effect = "halves" if re.search(r"reduz|metade", description, re.IGNORECASE) else "negates"
    with closing(sqlite3.connect(str(database_path), timeout=30)) as connection:
        connection.row_factory = sqlite3.Row
        caster_name = _caster_name(connection, "token", token_id)
    if range_m is not None or range_cells is not None:
        range_spec = {"mode": "ranged" if range_cells != 1 else "melee",
                      "range_m": range_m, "range_cells": range_cells}
    elif ability.get("range_m"):
        range_spec = {"mode": "ranged", "range_m": ability["range_m"]}
    else:
        range_spec = None
    return _resolve_targets(database_path, label=f"{row['name']} · {ability['name']}", source="monster_action",
                            save=save, save_effect=save_effect, damage_dice=damage, caster_name=caster_name,
                            caster_id=token_id, caster_token_id=token_id,
                            targets=targets, roll_mode=roll_mode, d20=d20, range_spec=range_spec,
                            damage_profile={'kind':'effect','damage_type':infer_damage_type(ability['name'],description)}, receipt=receipt)
