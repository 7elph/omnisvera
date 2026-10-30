"""Alcance tático das ações: anel no grid, validação no anel e aproximação.

 O anel abre com alcance declarado (magia: alcance da ficha; usável:
 range_m do mapa; ataque corpo a corpo: 1 célula). Desconhecido (arcos de
 monstros sem alcance no livro, magias sem alcance parseável) não inventa:
 o Mestre declara os metros uma vez (range_override_m) e o pipeline segue.
"""
from __future__ import annotations

import json
import math
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from .spatial_grid import distance_cells

_RANGED_NAME_RE = None


def _ranged_name_re():
    global _RANGED_NAME_RE
    if _RANGED_NAME_RE is None:
        import re
        _RANGED_NAME_RE = re.compile(r"arco|besta|funda|zarabatana|dardo|arremess|disparo|\btiro\b", re.IGNORECASE)
    return _RANGED_NAME_RE


def declared_range(database_path: Path, ref: str) -> dict[str, Any]:
    """Alcance declarado da ação, sem inventar: {mode, range_m?, range_cells?, unknown}."""
    from .action_library import describe_action,parse_action_ref
    library,head,section,key=parse_action_ref(ref)
    if library=='token' and section=='attack':
        from .monster_runtime import token_monster
        from .monster_contacts import binding
        with closing(sqlite3.connect(str(database_path))) as connection:monster,_=token_monster(connection,head)
        kind=binding((monster or {}).get('id'))
        if kind:return {'mode':'touch','range_cells':1,'label':'Contato no grid','native_contact':{'token_id':head,'kind':kind}}
    if library=='token' and section=='ability':
        from .monster_runtime import token_monster,breath_contract
        with closing(sqlite3.connect(str(database_path))) as connection:
            monster,_=token_monster(connection,head)
        if monster:
            try:
                contract=breath_contract(monster,key)
                if contract['execution_status']=='native':
                    return {'mode':'ranged','range_m':contract['geometry'].get('depth_m') or contract['geometry'].get('radius_m'),
                            'label':'Contato visual' if contract.get('requires_eye_contact') else 'Baforada · área nativa',
                            'native_breath':{'token_id':head,'ability_name':key,'reflection_allowed':contract.get('reflection_allowed',False)}}
            except ValueError:pass
    described = describe_action(database_path, ref)
    if described.get('contract'):
        resolved = described['contract']['range']
        if resolved['mode'] == 'touch':
            return {'mode': 'touch', 'range_cells': resolved['cells'],
                    'label': f"{resolved['cells']} célula (regra aprovada)"}
        if resolved['mode'] == 'self':
            return {'mode': 'self', 'range_m': 0, 'label': 'Próprio conjurador'}
        return {'mode':resolved['mode'], 'range_m':resolved['meters'], 'label':f"{resolved['meters']} m (regra aprovada)"}
    if described["kind"] == "spell":
        from .spell_catalog import get_catalog_spell
        from .spell_engine import derive_spell_mechanic
        spell_id = ref.split(":", 1)[1]
        spell = get_catalog_spell(spell_id)
        mechanic = derive_spell_mechanic(spell or {})
        alcance = (mechanic.get("range_text") or "")
        if alcance.strip().lower().startswith("toque"):
            return {"mode": "touch", "range_cells": 1, "label": alcance}
        if mechanic.get("range_m"):
            return {"mode": "ranged", "range_m": mechanic["range_m"], "label": alcance}
        return {"mode": "unknown", "label": alcance or "alcance a confirmar com o Mestre"}
    if described["kind"] in ("usable", "passive"):
        range_m = _usable_range_m(database_path, ref)
        if range_m:
            return {"mode": "ranged", "range_m": range_m, "label": f"{range_m} m (ficha)"}
        if described["kind"] == "passive":
            return {"mode": "passive", "label": "sempre ligada"}
        return {"mode": "unknown", "label": "alcance a confirmar com o Mestre"}
    if described["kind"] == "attack":
        name = described["name"]
        if _ranged_name_re().search(name or ""):
            return {"mode": "unknown", "label": "arma de distância sem alcance no livro — Mestre declara"}
        return {"mode": "melee", "range_cells": 1, "label": "corpo a corpo (adjacência)"}
    if described["kind"] == "technique":
        return {"mode": "unknown", "label": "alcance na ficha da técnica"}
    return {"mode": "unknown", "label": "?"}


def _usable_range_m(database_path: Path, ref: str) -> int | None:
    # Reaproveita o range_m já extraído em monster_actions.classify_ability.
    from .action_library import parse_action_ref
    from .monster_catalog import get_catalog_monster
    from .monster_actions import build_action_map
    try:
        library, head, _section, key = parse_action_ref(ref)
    except ValueError:
        return None
    if library not in ("monster", "token") or not key:
        return None
    if library=='token':
        from .monster_runtime import token_monster,breath_contract
        with closing(sqlite3.connect(str(database_path))) as connection:
            monster,_=token_monster(connection,head)
        if monster:
            try:
                contract=breath_contract(monster,key)
                if contract['execution_status']=='native':
                    return contract['geometry'].get('depth_m') or contract['geometry'].get('radius_m')
            except ValueError:pass
    if library == "monster":
        monster = get_catalog_monster(head)
        if monster is None:
            return None
        action_map = build_action_map(
            monster["name"], monster.get("attacks") or [],
            [(ability.get("name") or "", ability.get("description") or "") for ability in monster.get("abilities") or []])
    else:
        with closing(sqlite3.connect(str(database_path), timeout=30)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute("SELECT name, sheet_json FROM session_workspace_tokens WHERE id=?",
                                     (head,)).fetchone()
            if row is None:
                return None
            sheet = json.loads(row["sheet_json"] or "{}")
        action_map = build_action_map(row["name"], sheet.get("attacks") or [], sheet.get("abilities") or [])
    for entry in action_map["active_abilities"] + action_map["spellcasting"]:
        if entry["name"].casefold() == key.casefold():
            return entry.get("range_m")
    return None


def _grid_and_pos(database_path: Path, map_id: str, token_id: str) -> tuple[dict | None, dict | None]:
    with closing(sqlite3.connect(str(database_path), timeout=30)) as connection:
        connection.row_factory = sqlite3.Row
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "session_workspace_map_grids" not in tables or "session_workspace_entity_positions" not in tables:
            return None, None
        grid = connection.execute("SELECT * FROM session_workspace_map_grids WHERE map_id=?", (map_id,)).fetchone()
        pos = connection.execute("SELECT cell_x, cell_y FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?",
                                 (map_id, token_id)).fetchone()
    return (dict(grid) if grid else None, {"cell_x": pos["cell_x"], "cell_y": pos["cell_y"]} if pos else None)


def ring_for_action(database_path: Path, *, ref: str = "", attacker_token_id: str, map_id: str,
                    attacker_character_id: str = "", slot_override: str | None = None,
                    max_override: float | None = None, range_override_m: float | None = None,
                    role: str = 'gm', include_self: bool = False, target_kind: str = 'living') -> dict[str, Any]:
    """Anel de alcance + alvos válidos para abrir no grid.

    refs da biblioteca (spell/monster/token/technique) resolvem o alcance
    declarado; ataques de personagem usam slot/max resolvidos pelo chamador;
    slot_override preenche desconhecidos (técnicas com slot conhecido).
    """
    from .spatial_grid import targets_in_range
    slot = slot_override
    max_m = max_override
    declared: dict[str, Any] = {"mode": "unknown", "label": "alcance a confirmar com o Mestre"}
    if ref and not (slot and max_m is not None):
        declared = declared_range(database_path, ref)
    mode = declared.get("mode", "unknown")
    range_m = range_override_m if range_override_m is not None else declared.get("range_m")
    if range_override_m is not None:
        mode = "ranged"
    if slot in ("melee", "touch"):
        mode = slot
    elif slot == "ranged":
        mode = "ranged"
    from .session_workspace import get_workspace_snapshot
    visible = get_workspace_snapshot(database_path, map_id=map_id, is_gm=role == 'gm')
    attacker = next((t for t in visible.get('tokens', []) if t['id'] == attacker_token_id), None)
    if not attacker_token_id:
        attacker = next((t for t in visible.get('tokens', []) if t.get('character_id') == attacker_character_id), None)
    if attacker is None:
        raise PermissionError('Posicione uma entidade disponível neste mapa antes de usar a ação')
    attacker_token_id = attacker['id']
    grid, pos = _grid_and_pos(database_path, map_id, attacker_token_id)
    if not grid or not pos:
        return {"gridded": False, "declared": declared, "reason": "sem grid ou posição — Mestre adjudica"}
    if mode in ("unknown", "passive"):
        return {"gridded": False, "declared": declared, "reason": declared.get("label")}
    cell_size = float(grid["cell_size_m"])
    if mode in ("melee", "touch"):
        slot, max_m, range_cells = "touch" if mode == "touch" else "melee", None, 1
    else:
        slot, max_m = "ranged", (float(range_m) if range_m is not None else max_m)
        range_cells = max(1, int(math.ceil(max_m / cell_size))) if (max_m is not None and cell_size > 0) else 0
        if mode == 'self':
            range_cells = 0
    listed = targets_in_range(database_path, actor_character_id=attacker_character_id,
                              attacker_token_id=attacker_token_id or None,
                              map_id=map_id, slot=slot, max_range_m=max_m, role=role)
    if not listed.get("gridded"):
        return {"gridded": False, "declared": declared, "reason": "atacante sem posição"}
    if mode == 'self':
        # A zero-radius self effect is not an unbounded ranged action, nor
        # does sharing the origin cell make another entity the caster.
        listed['targets'] = []
    if include_self or (role=='gm' and (declared.get('native_breath') or {}).get('reflection_allowed')):
        listed['targets'].insert(0,{'type':'token','id':attacker['id'],'name':attacker['name'],
            'cells':0,'meters':0,'valid':True,'reason':''})
    by_id={t['id']:t for t in visible.get('tokens',[])}
    # Character HP belongs to the sheet; legacy pins can retain an old HP copy.
    character_hp={}
    with closing(sqlite3.connect(database_path)) as db:
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='character_states'").fetchone():
            character_hp={identity:json.loads(raw or '{}').get('current_hp')
                          for identity,raw in db.execute('SELECT profile_id,state_json FROM character_states')}
    for candidate in listed.get('targets',[]):
        token=by_id[candidate['id']];sheet=token.get('sheet') or {}
        hp=character_hp.get(token.get('character_id'),token.get('current_hp'))
        candidate['current_hp']=hp
        if declared.get('native_breath'):
            ap=attacker.get('grid_position') or {};bp=token.get('grid_position') or {}
            if ap and bp and range_m is not None:
                dx=(ap['cell_x']+ap.get('footprint_w',1)/2)-(bp['cell_x']+bp.get('footprint_w',1)/2)
                dy=(ap['cell_y']+ap.get('footprint_h',1)/2)-(bp['cell_y']+bp.get('footprint_h',1)/2)
                meters=math.hypot(dx,dy)*cell_size
                candidate.update(meters=meters,valid=meters<=range_m+1e-8,reason='' if meters<=range_m+1e-8 else 'Fora de alcance')
        if target_kind=='corpse':
            eligible=hp==0 and not sheet.get('summon') and not sheet.get('reanimated_by') and sheet.get('reanimation_allowed')
            if not eligible:candidate.update(valid=False,reason='Cadáver não autorizado ou já utilizado')
        elif hp is not None and hp<=0:
            candidate.update(valid=False,reason='Alvo sem PV')
    if ref=='technique:dorn7:dissipar-magia':
        from .spell_effect_runtime import dispel_preview
        from .combat_effects import effect_snapshot
        with closing(sqlite3.connect(str(database_path))) as dispel_db:
            dispel_db.execute('BEGIN')
            current_effects=effect_snapshot(dispel_db)
            for candidate in listed.get('targets',[]):
                try:options=dispel_preview(dispel_db,current_effects,candidate['id'])['effects']
                except ValueError:options=[]
                candidate.update(valid=bool(options),reason='' if options else 'Nenhuma magia arcana dissipável no alcance')
                if options:candidate['meters']=min(option['distance_m'] for option in options)
    return {"gridded": True, "declared": declared, **({"native_contact":declared["native_contact"]} if declared.get("native_contact") else {}), "mode": mode, "slot": slot,
            "native_breath":declared.get('native_breath') if role=='gm' else None,
            "range_m": max_m, "range_cells": range_cells, "cell_size_m": cell_size,
            "rule": grid["distance_rule"], "cols": grid["cols"], "rows": grid["rows"],
            "origin": listed.get("origin"), "targets": listed.get("targets", [])}


def enforce_action_range(database_path: Path, *, attacker_token_id: str, target_type: str, target_id: str,
                         mode: str, range_m: float | None = None, range_cells: int | None = None) -> dict[str, Any]:
    """Garante o alvo dentro do anel. Sem grid/posições, não bloqueia (checked False)."""
    with closing(sqlite3.connect(str(database_path), timeout=30)) as connection:
        connection.row_factory = sqlite3.Row
        token = connection.execute("SELECT map_id FROM session_workspace_tokens WHERE id=?", (attacker_token_id,)).fetchone()
        if token is None:
            return {"checked": False}
        map_id = token["map_id"]
        grid, apos = _grid_and_pos(database_path, map_id, attacker_token_id)
        if not grid or not apos:
            return {"checked": False}
        if target_type == "token":
            target_token = target_id
        else:
            row = connection.execute("SELECT id FROM session_workspace_tokens WHERE character_id=? AND map_id=? ORDER BY id LIMIT 1",
                                     (target_id,map_id)).fetchone()
            if row is None:
                return {"checked": False}
            target_token = row["id"]
        _, bpos = _grid_and_pos(database_path, map_id, target_token)
        if not bpos:
            return {"checked": False}
        cells = distance_cells(grid["distance_rule"], [apos["cell_x"], apos["cell_y"]], [bpos["cell_x"], bpos["cell_y"]])
        meters = cells * float(grid["cell_size_m"])
    if mode in ("melee", "touch"):
        if cells > 1:
            raise ValueError(f"Fora de alcance corpo a corpo ({cells} células)")
        return {"checked": True, "cells": cells, "meters": meters}
    limit = range_m if range_m is not None else ((range_cells or 0) * float(grid["cell_size_m"]))
    if limit and meters > limit + 1e-8:
        raise ValueError(f"Fora de alcance ({meters:g} m, máximo {limit:g} m)")
    return {"checked": True, "cells": cells, "meters": meters}


def approach_preview(database_path: Path, *, map_id: str, token_id: str, target_type: str, target_id: str,
                     mode: str, range_m: float | None = None, range_cells: int | None = None) -> dict[str, Any]:
    """Caminho até o alcance: anda pelo caminho mais curto e para na primeira
    célula dentro do anel, limitada ao orçamento restante do turno."""
    from .spatial_grid import grid_record, movement_m, turn_key, current_participant
    from .combat_effects import effect_snapshot
    with closing(sqlite3.connect(str(database_path), timeout=30)) as connection:
        connection.row_factory = sqlite3.Row
        grid = grid_record(connection, map_id)
        if not grid:
            raise ValueError("Mapa sem grid")
        apos = connection.execute("SELECT cell_x, cell_y FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?",
                                  (map_id, token_id)).fetchone()
        token = connection.execute("SELECT * FROM session_workspace_tokens WHERE id=? AND map_id=?", (token_id, map_id)).fetchone()
        if not apos or token is None:
            raise ValueError("Atacante sem posição")
        if target_type == "token":
            target_token = target_id
        else:
            row = connection.execute("SELECT id FROM session_workspace_tokens WHERE character_id=? AND map_id=? ORDER BY id LIMIT 1", (target_id,map_id)).fetchone()
            if row is None:
                raise ValueError("Alvo sem token neste mapa")
            target_token = row["id"]
        bpos = connection.execute("SELECT cell_x, cell_y FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?",
                                  (map_id, target_token)).fetchone()
        if not bpos:
            raise ValueError("Alvo sem posição")
        start = [apos["cell_x"], apos["cell_y"]]
        goal = [bpos["cell_x"], bpos["cell_y"]]
        rule = grid["distance_rule"]
        cell_size = float(grid["cell_size_m"])
        limit_m = None
        if mode in ("melee", "touch"):
            limit_cells = 1
        elif range_m is not None:
            limit_m, limit_cells = float(range_m), None
        elif range_cells is not None:
            limit_cells = int(range_cells)
        else:
            raise ValueError("Alcance desconhecido — Mestre declara os metros")
        snapshot = {}
        has_clock = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name='combat_effect_clock'").fetchone()
        if has_clock:
            snapshot = effect_snapshot(connection)
        encounter = snapshot.get("encounter") or {}
        speed = None
        spent = 0.0
        if encounter.get("active") and encounter.get("battle_mode"):
            sheet = json.loads(token["sheet_json"] or "{}")
            speed = movement_m(sheet.get("movement"))
            key = turn_key(encounter, current_participant(encounter) or {})
            movement = encounter.get("movement") or {}
            spent = float(movement.get("spent_m") or 0) if movement.get("turn_key") == key else 0.0
        remaining = None if speed is None else max(0.0, speed - spent)

        def within(cell: list[int]) -> bool:
            cells = distance_cells(rule, cell, goal)
            if mode in ("melee", "touch"):
                return cells <= 1
            meters = cells * cell_size
            return meters <= (limit_m if limit_m is not None else limit_cells * cell_size) + 1e-8

        if within(start):
            return {"already_in_range": True, "path": [start], "cost_m": 0.0,
                    "remaining_m": remaining, "lands_in_range": True, "cells": distance_cells(rule, start, goal)}
        # passo guloso até o alvo (chebyshev anda na diagonal; manhattan em L)
        path = [start]
        cursor = list(start)
        guard = (grid["cols"] + grid["rows"]) * 2 + 10
        while cursor != goal and len(path) < guard:
            nx = cursor[0] + (1 if goal[0] > cursor[0] else -1 if goal[0] < cursor[0] else 0)
            ny = cursor[1] + (1 if goal[1] > cursor[1] else -1 if goal[1] < cursor[1] else 0)
            if rule == "manhattan" and nx != cursor[0] and ny != cursor[1]:
                ny = cursor[1]
            cursor = [max(0, min(grid["cols"] - 1, nx)), max(0, min(grid["rows"] - 1, ny))]
            if cursor == path[-1]:
                break
            path.append(list(cursor))
        # corta pelo orçamento e para na primeira célula dentro do anel
        affordable: list[list[int]] = [path[0]]
        cost = 0.0
        for step in path[1:]:
            step_cost = distance_cells(rule, affordable[-1], step) * cell_size
            if remaining is not None and cost + step_cost > remaining + 1e-8:
                break
            affordable.append(step)
            cost += step_cost
            if within(step):
                break
        return {"already_in_range": False, "path": affordable, "cost_m": round(cost, 2),
                "remaining_m": remaining, "lands_in_range": within(affordable[-1]),
                "cells": distance_cells(rule, start, goal), "meters": round(distance_cells(rule, start, goal) * cell_size, 2)}
