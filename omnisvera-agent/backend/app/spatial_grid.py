"""Logical extension of the existing workspace maps/pins; no canvas or turn engine.

Origins are percentages of the image surface. Cells, not percentages, are the
combat authority. Chebyshev is explicitly provisional and configurable per map.
"""
import json
import math
import re
import sqlite3
from contextlib import closing, nullcontext
from datetime import datetime, timezone
from pathlib import Path

from .session_ledger import append_session_ledger_event


def connect(path):
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db


def init_spatial(path: Path):
    with closing(connect(path)) as db:
        if db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name IN ('session_workspace_map_grids','session_workspace_entity_positions','session_workspace_spatial_commands','trg_spatial_new_pin','trg_spatial_transfer_pin','trg_spatial_delete_pin')").fetchone()[0] == 6:
            return  # Runtime commands must not repeat schema writes/migrations.
    with closing(connect(path)) as db, db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS session_workspace_map_grids(
          map_id TEXT PRIMARY KEY REFERENCES session_workspace_maps(id),
          grid_type TEXT NOT NULL CHECK(grid_type='square'), cols INTEGER NOT NULL, rows INTEGER NOT NULL,
          cell_size_m REAL NOT NULL, origin_x REAL NOT NULL, origin_y REAL NOT NULL,
          distance_rule TEXT NOT NULL, provisional INTEGER NOT NULL DEFAULT 1,
          version INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS session_workspace_entity_positions(
          map_id TEXT NOT NULL REFERENCES session_workspace_map_grids(map_id),
          token_id TEXT NOT NULL REFERENCES session_workspace_tokens(id),
          cell_x INTEGER NOT NULL, cell_y INTEGER NOT NULL,
          footprint_w INTEGER NOT NULL DEFAULT 1, footprint_h INTEGER NOT NULL DEFAULT 1,
          version INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(map_id,token_id));
        CREATE TABLE IF NOT EXISTS session_workspace_spatial_commands(
          request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, response_json TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS trg_spatial_new_pin AFTER INSERT ON session_workspace_tokens
        WHEN NEW.token_type!='location' BEGIN
          INSERT OR IGNORE INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y)
          SELECT NEW.map_id,NEW.id,
            MAX(0,MIN(cols-1,CAST((NEW.longitude-origin_x)/(100-origin_x)*cols AS INTEGER))),
            MAX(0,MIN(rows-1,CAST((NEW.latitude-origin_y)/(100-origin_y)*rows AS INTEGER)))
          FROM session_workspace_map_grids WHERE map_id=NEW.map_id;
        END;
        CREATE TRIGGER IF NOT EXISTS trg_spatial_transfer_pin AFTER UPDATE OF map_id ON session_workspace_tokens
        WHEN NEW.token_type!='location' BEGIN
          INSERT OR IGNORE INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y)
          SELECT NEW.map_id,NEW.id,
            MAX(0,MIN(cols-1,CAST((NEW.longitude-origin_x)/(100-origin_x)*cols AS INTEGER))),
            MAX(0,MIN(rows-1,CAST((NEW.latitude-origin_y)/(100-origin_y)*rows AS INTEGER)))
          FROM session_workspace_map_grids WHERE map_id=NEW.map_id;
        END;
        CREATE TRIGGER IF NOT EXISTS trg_spatial_delete_pin AFTER DELETE ON session_workspace_tokens BEGIN
          DELETE FROM session_workspace_entity_positions WHERE token_id=OLD.id;
        END;
        ''')


def has_schema(db):
    return db.execute("SELECT 1 FROM sqlite_master WHERE name='session_workspace_map_grids'").fetchone() is not None


def grid_record(db, map_id):
    row = db.execute('SELECT * FROM session_workspace_map_grids WHERE map_id=?', (map_id,)).fetchone() if has_schema(db) else None
    return dict(row) if row else None


def visual_position(grid, position):
    return dict(longitude=grid['origin_x'] + (position['cell_x'] + position['footprint_w']/2) * (100-grid['origin_x'])/grid['cols'],
                latitude=grid['origin_y'] + (position['cell_y'] + position['footprint_h']/2) * (100-grid['origin_y'])/grid['rows'])


def enrich_snapshot(path, snapshot):
    """Read-only projection after the existing visibility/privacy filtering."""
    if not snapshot.get('map'):
        return snapshot
    with closing(connect(path)) as db:
        grid = grid_record(db, snapshot['map']['id'])
        if not grid:
            return snapshot
        snapshot['map']['grid'] = grid
        for token in snapshot['tokens']:
            position = db.execute('SELECT * FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?', (grid['map_id'], token['id'])).fetchone()
            if position:
                token['grid_position'] = dict(position)
                token.update(visual_position(grid, position))
        bonus_context={}
        for token in snapshot['tokens']:
            identity=token.get('character_id') or token['id']
            token['tactical_attack_bonus']=diagonal_bonus(db,identity,context=bonus_context)['bonus']
    return snapshot


def diagonal_bonus(db, actor_id, target_type=None, target_id=None, *, context=None):
    """Approved campaign rule: diagonal allies OR opposite-diagonal flank, max +2.

    Only living participants, one-cell footprints and authoritative positions.
    No persistent buff: movement/death removes the computed bonus immediately.
    """
    empty={'bonus':0,'reason':None,'positions':[]}
    if context is not None and 'units' in context:return _diagonal_from_units(context['units'],actor_id,target_type,target_id)
    encounter,_=encounter_record(db)
    if not encounter.get('active') or not encounter.get('battle_mode') or not has_schema(db):
        if context is not None:context['units']=[]
        return empty
    map_id=encounter.get('map_id');members=encounter.get('participants') or []
    ids={p.get('token_id') or (p['target_id'] if p['target_type']=='token' else None) for p in members}
    characters={p['target_id'] for p in members if p['target_type']=='character'}
    rows=db.execute('SELECT t.*,p.cell_x,p.cell_y,p.footprint_w,p.footprint_h,p.version AS position_version FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id WHERE t.map_id=? AND t.visible_to_players=1',(map_id,)).fetchall()
    units=[]
    for raw in rows:
        unit=dict(raw);sheet=json.loads(unit['sheet_json'] or '{}')
        if unit['id'] not in ids and unit.get('character_id') not in characters:continue
        hp=unit.get('current_hp')
        if unit.get('character_id'):
            state=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(unit['character_id'],)).fetchone()
            if state:hp=json.loads(state[0]).get('current_hp')
        from .vezemir_skills import survives
        if (hp is not None and hp<=0 and not survives(db,unit.get('character_id'),hp)) or unit['footprint_w']!=1 or unit['footprint_h']!=1:continue
        unit['party']=bool(unit.get('character_id') or sheet.get('summon') or 'aliado' in str(sheet.get('role') or '').casefold())
        units.append(unit)
    if context is not None:context['units']=units
    return _diagonal_from_units(units,actor_id,target_type,target_id)


def _diagonal_from_units(units,actor_id,target_type,target_id):
    empty={'bonus':0,'reason':None,'positions':[]}
    actor=next((u for u in units if (u.get('character_id') or u['id'])==actor_id),None)
    if not actor or not actor['party']:return empty
    others=[u for u in units if u['id']!=actor['id'] and u['party']]
    stamp=lambda u:[u['id'],u['cell_x'],u['cell_y'],u['position_version']]
    for ally in others:
        if abs(actor['cell_x']-ally['cell_x'])==1 and abs(actor['cell_y']-ally['cell_y'])==1:
            return {'bonus':2,'reason':'Aliados em diagonal','positions':[stamp(actor),stamp(ally)]}
    enemies=[u for u in units if not u['party'] and (target_id is None or (u['id']==target_id if target_type=='token' else u.get('character_id')==target_id))]
    for enemy in enemies:
        dx=actor['cell_x']-enemy['cell_x'];dy=actor['cell_y']-enemy['cell_y']
        if abs(dx)!=1 or abs(dy)!=1:continue
        for ally in others:
            if ally['cell_x']-enemy['cell_x']==-dx and ally['cell_y']-enemy['cell_y']==-dy:
                return {'bonus':2,'reason':'Flanqueamento diagonal','positions':[stamp(actor),stamp(ally),stamp(enemy)]}
    return empty


def encounter_record(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effect_clock'").fetchone():
        return {}, 0
    row = db.execute('SELECT encounter_json,version FROM combat_effect_clock WHERE id=1').fetchone()
    return (json.loads(row[0]), row[1]) if row else ({}, 0)


def visible_map(db, map_id, role):
    row = db.execute('SELECT * FROM session_workspace_maps WHERE id=? AND id NOT IN (SELECT id FROM deleted_workspace_maps)', (map_id,)).fetchone()
    if not row or (role != 'gm' and not row['visible_to_players']):
        raise PermissionError('Mapa indisponível')
    return row


def seed_positions(db, grid):
    for token in db.execute("SELECT * FROM session_workspace_tokens WHERE map_id=? AND token_type!='location'", (grid['map_id'],)).fetchall():
        x = max(0, min(grid['cols']-1, math.floor((token['longitude']-grid['origin_x'])/(100-grid['origin_x'])*grid['cols'])))
        y = max(0, min(grid['rows']-1, math.floor((token['latitude']-grid['origin_y'])/(100-grid['origin_y'])*grid['rows'])))
        db.execute('INSERT OR IGNORE INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y) VALUES(?,?,?,?)', (grid['map_id'], token['id'], x, y))


def distance_cells(rule, a, b):
    dx, dy = abs(a[0]-b[0]), abs(a[1]-b[1])
    return max(dx, dy) if rule == 'chebyshev' else dx+dy


def validate_cell(grid, cell, w=1, h=1):
    if not isinstance(cell, (list, tuple)) or len(cell) != 2 or any(type(v) is not int for v in cell):
        raise ValueError('Informe células inteiras [x,y]')
    if not 0 <= cell[0] <= grid['cols']-w or not 0 <= cell[1] <= grid['rows']-h:
        raise ValueError('Posição fora do grid')


def replay(db, request_id, fingerprint):
    if not isinstance(request_id, str) or not 8 <= len(request_id) <= 120:
        raise ValueError('request_id inválido')
    row = db.execute('SELECT * FROM session_workspace_spatial_commands WHERE request_id=?', (request_id,)).fetchone()
    if row:
        if row['fingerprint'] != fingerprint:
            raise ValueError('request_id já utilizado com outro comando')
        return json.loads(row['response_json'])


def finish_command(db, request_id, fingerprint, result):
    db.execute('INSERT INTO session_workspace_spatial_commands VALUES(?,?,?)', (request_id, fingerprint, json.dumps(result)))
    return result


def configure_grid(path, *, actor_id, role, request_id, map_id, config, expected_version=0):
    if role != 'gm':
        raise PermissionError('Somente o Mestre configura o grid')
    init_spatial(path)
    fp = json.dumps([actor_id, role, 'configure_grid', map_id, config, expected_version], sort_keys=True)
    with closing(connect(path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        visible_map(db, map_id, role)
        previous = replay(db, request_id, fp)
        if previous is not None:
            return previous
        old = grid_record(db, map_id)
        if expected_version != (old['version'] if old else 0):
            raise ValueError('O grid mudou; atualize antes de configurar')
        encounter, _ = encounter_record(db)
        if encounter.get('active') and encounter.get('map_id') == map_id:
            raise ValueError('Encerre o combate antes de alterar a escala ou o grid')
        if set(config) - {'grid_type','cols','rows','cell_size_m','origin_x','origin_y','distance_rule','provisional'}:
            raise ValueError('Campo de grid inválido')
        grid = dict(map_id=map_id, grid_type=config.get('grid_type', 'square'), cols=config.get('cols'), rows=config.get('rows'),
            cell_size_m=config.get('cell_size_m'), origin_x=config.get('origin_x', 0), origin_y=config.get('origin_y', 0),
            distance_rule=config.get('distance_rule', 'chebyshev'), provisional=1, version=(old['version'] if old else 0)+1)
        if grid['grid_type'] != 'square' or grid['distance_rule'] not in {'chebyshev','manhattan'}:
            raise ValueError('Grid ou regra de distância inválidos')
        if any(type(grid[k]) is not int or not 1 <= grid[k] <= 200 for k in ('cols','rows')):
            raise ValueError('Colunas/linhas devem ficar entre 1 e 200')
        for k, low, high in [('cell_size_m', .01, 10000), ('origin_x', 0, 99), ('origin_y', 0, 99)]:
            if type(grid[k]) not in (int,float) or not math.isfinite(grid[k]) or not low <= grid[k] <= high:
                raise ValueError('Escala/origem inválida')
        if old:
            for pos in db.execute('SELECT * FROM session_workspace_entity_positions WHERE map_id=?', (map_id,)):
                validate_cell(grid, [pos['cell_x'],pos['cell_y']], pos['footprint_w'], pos['footprint_h'])
        db.execute('''INSERT INTO session_workspace_map_grids VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(map_id) DO UPDATE SET
            cols=excluded.cols,rows=excluded.rows,cell_size_m=excluded.cell_size_m,origin_x=excluded.origin_x,origin_y=excluded.origin_y,
            distance_rule=excluded.distance_rule,version=excluded.version''', tuple(grid.values()))
        seed_positions(db, grid)
        if old:
            for position in db.execute('SELECT * FROM session_workspace_entity_positions WHERE map_id=?',(map_id,)).fetchall():
                visual = visual_position(grid, position)
                db.execute('UPDATE session_workspace_tokens SET latitude=?,longitude=? WHERE id=? AND map_id=?',
                    (visual['latitude'],visual['longitude'],position['token_id'],map_id))
        from .bat_swarm import sync as sync_bat_swarm
        sync_bat_swarm(db, datetime.now(timezone.utc).isoformat())
        ledger_id = append_session_ledger_event(db, source_type='spatial_grid', source_id=request_id, event_kind='state',
            actor_id=actor_id,actor_name='Mestre',actor_role='gm',character_id=None,title='Grid lógico configurado',
            detail={'map_id':map_id,'grid':grid},visibility='gm',created_at=datetime.now(timezone.utc).isoformat())
        return finish_command(db, request_id, fp, {'grid':grid, 'ledger_id':ledger_id})


def movement_m(value):
    from .monster_movement import selected_movement
    return selected_movement(value)


def turn_key(encounter, participant):
    return [encounter.get('started_at'), encounter.get('turn_sequence'), participant.get('target_type'),participant.get('target_id')]


def current_participant(encounter):
    members = encounter.get('participants') or []
    return members[int(encounter.get('turn_index') or 0) % len(members)] if encounter.get('active') and members else None


def move_entity(path, *, actor_id, role, request_id, map_id, token_id, mode, cells,
                expected_position_version, expected_grid_version, expected_combat_version=None, load_movement=None, movement_mode=None):
    """One transaction for path, turn budget, pin projection, audit and retry receipt."""
    init_spatial(path)
    intent = [actor_id,role,map_id,token_id,mode,cells,expected_position_version,expected_grid_version,expected_combat_version]
    if movement_mode is not None:intent.append(movement_mode)
    fp = json.dumps(intent, sort_keys=True)
    # Native character loading may initialize other modules. Do it BEFORE the
    # writer transaction and bind its effect snapshot to the checked version.
    speed = None
    with closing(connect(path)) as db:
        _, before_version = encounter_record(db)
        visible_map(db, map_id, role)
        token = db.execute('SELECT * FROM session_workspace_tokens WHERE id=?', (token_id,)).fetchone()
        cached = replay(db, request_id, fp)
        if cached is not None:
            return cached
        if token and mode == 'COMBAT_MOVE':
            sheet = json.loads(token['sheet_json'] or '{}')
            if role != 'gm' and token['character_id'] != actor_id and sheet.get('summon',{}).get('caster') != actor_id:
                raise PermissionError('O jogador só move sua entidade ou invocação')
            from .monster_movement import selected_movement, movement_modes
            raw_movement=load_movement(token['character_id']) if token['character_id'] and load_movement else sheet.get('movement')
            selected_mode=movement_mode or sheet.get('movement_mode')
            speed=selected_movement(raw_movement,selected_mode)
            if selected_mode is None:
                modes=movement_modes(raw_movement)
                selected_mode='walk' if 'walk' in modes else next(iter(modes))
    with closing(connect(path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        map_record = visible_map(db, map_id, role)
        cached = replay(db, request_id, fp)
        if cached is not None:
            return cached
        token = db.execute('SELECT * FROM session_workspace_tokens WHERE id=? AND map_id=?', (token_id,map_id)).fetchone()
        if not token or token['token_type'] == 'location':
            raise ValueError('Entidade combatente não está neste mapa')
        if role != 'gm':
            from .session_workspace import _token_is_visible
            # Read fog directly: no nested initialization/writer connection.
            fog = {}
            for row in db.execute('SELECT layer,enabled,revealed_cells_json,mist_density_json FROM session_workspace_map_fog WHERE map_id=?', (map_id,)):
                fog[row[0]] = dict(enabled=row[1],revealed_cells=json.loads(row[2]),mist_density=json.loads(row[3]))
            if not _token_is_visible(dict(token),fog):
                raise PermissionError('Entidade indisponível')
        grid = grid_record(db, map_id)
        if not grid or grid['version'] != expected_grid_version:
            raise ValueError('Grid ausente ou desatualizado')
        pos = db.execute('SELECT * FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?', (map_id,token_id)).fetchone()
        if not pos or pos['version'] != expected_position_version:
            raise ValueError('A posição mudou; atualize antes de mover')
        if not isinstance(cells, list) or not 1 <= len(cells) <= 401:
            raise ValueError('Caminho inválido ou longo demais')
        for cell in cells:
            validate_cell(grid, cell, pos['footprint_w'], pos['footprint_h'])
        if cells[0] != [pos['cell_x'],pos['cell_y']]:
            raise ValueError('O início do caminho não corresponde à posição atual')
        encounter, version = encounter_record(db)
        if mode == 'GM_REPOSITION':
            if role != 'gm':
                raise PermissionError('Somente o Mestre reposiciona fora do combate')
            if encounter.get('active'):
                raise ValueError('Reposicionamento administrativo somente fora do combate')
            cost = 0
            budget = None
        elif mode == 'COMBAT_MOVE':
            from .monster_conditions import assert_can_act
            assert_can_act(db,token['character_id'] or token_id)
            current = current_participant(encounter)
            identity = ('character',token['character_id']) if token['character_id'] else ('token',token_id)
            if not current or encounter.get('map_id') != map_id or identity != (current.get('target_type'),current.get('target_id')):
                raise ValueError('Aguarde o turno desta entidade no mapa de combate')
            if version != expected_combat_version or version != before_version:
                raise ValueError('O turno ou os efeitos mudaram; atualize antes de mover')
            summon = json.loads(token['sheet_json'] or '{}').get('summon', {})
            if role != 'gm' and not (token['character_id'] == actor_id or summon.get('caster') == actor_id):
                raise PermissionError('O jogador só move sua entidade ou invocação')
            if token['character_id']:
                state = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (token['character_id'],)).fetchone()
                hp = json.loads(state[0]).get('current_hp') if state else None
            else:
                hp = token['current_hp']
            from .vezemir_skills import survives
            if hp is not None and hp <= 0 and not survives(db,token['character_id'],hp):
                raise ValueError('Entidade incapacitada não pode se mover')
            for row in db.execute('SELECT data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=?', identity):
                effect = json.loads(row[0])
                if effect.get('reward') == 'vines' or effect.get('immobilized'):
                    raise ValueError('Alvo imobilizado: '+str(effect.get('label') or 'Pulseira de Vinhas'))
            cost_cells = 0
            for a,b in zip(cells,cells[1:]):
                dx,dy = abs(a[0]-b[0]),abs(a[1]-b[1])
                if max(dx,dy) != 1:
                    raise ValueError('Passos devem ser adjacentes; não é permitido teleportar')
                from .dorn_spell_pack import web_step_multiplier
                cost_cells += distance_cells(grid['distance_rule'],a,b)*web_step_multiplier(db,map_id,b)
            cost = cost_cells * grid['cell_size_m']
            key = turn_key(encounter,current)
            spent = (encounter.get('movement') or {}).get('spent_m',0) if (encounter.get('movement') or {}).get('turn_key') == key else 0
            previous_mode=(encounter.get('movement') or {}).get('mode','walk')
            if spent and previous_mode!=selected_mode:
                raise ValueError('Não é possível trocar o modo de movimento depois de se deslocar neste turno')
            if speed is None or spent + cost > speed + 1e-8:
                raise ValueError('Movimento acima do limite disponível neste turno')
            budget = dict(turn_key=key,budget_m=speed,spent_m=round(spent+cost,6),mode=selected_mode)
            encounter['movement'] = budget
            db.execute('UPDATE combat_effect_clock SET encounter_json=?,version=version+1 WHERE id=1', (json.dumps(encounter),))
            version += 1
        else:
            raise ValueError('Use COMBAT_MOVE ou GM_REPOSITION')
        result_pos = {**dict(pos), 'cell_x':cells[-1][0], 'cell_y':cells[-1][1], 'version':pos['version']+1}
        db.execute('UPDATE session_workspace_entity_positions SET cell_x=?,cell_y=?,version=version+1 WHERE map_id=? AND token_id=?', (*cells[-1],map_id,token_id))
        projected = visual_position(grid,result_pos)
        now = datetime.now(timezone.utc).isoformat()
        db.execute('UPDATE session_workspace_tokens SET latitude=?,longitude=?,updated_at=? WHERE id=?', (projected['latitude'],projected['longitude'],now,token_id))
        from .bat_swarm import sync as sync_bat_swarm
        sync_bat_swarm(db, now)
        from .item_grapple import prune as prune_item_grapple
        prune_item_grapple(db,now,moving=(map_id,token_id,cells))
        # Conditional effects can advance the same authoritative clock.
        # Return that version, including in the cached idempotent receipt.
        _, version = encounter_record(db)
        from .session_workspace import _token_is_visible
        fog = {}
        for row in db.execute('SELECT layer,enabled,revealed_cells_json,mist_density_json FROM session_workspace_map_fog WHERE map_id=?', (map_id,)):
            fog[row[0]] = dict(enabled=row[1],revealed_cells=json.loads(row[2]),mist_density=json.loads(row[3]))
        # Hidden paths/positions never enter the public ledger.
        public = bool(map_record['visible_to_players']) and bool(token['visible_to_players']) and all(
            _token_is_visible({**dict(token), **visual_position(grid,{**dict(pos),'cell_x':c[0],'cell_y':c[1]})},fog) for c in cells)
        ledger_id = append_session_ledger_event(db, source_type='spatial_move', source_id=request_id,event_kind='action',actor_id=actor_id,
            actor_name='Mestre' if role=='gm' else actor_id,actor_role=role,character_id=token['character_id'],
            title=f"{token['name']} {'se deslocou' if mode=='COMBAT_MOVE' else 'foi reposicionado'} · {cost:g} m",
            detail=dict(mode=mode,map_id=map_id,token_id=token_id,path=cells,position=result_pos,cells=cost/grid['cell_size_m'],meters=cost,movement=budget),
            visibility='table' if public else 'gm',created_at=now)
        return finish_command(db, request_id,fp,dict(position=result_pos,movement=budget,combat_version=version,ledger_id=ledger_id,**projected))


def check_attack_range(path, *, actor_character_id, target_type, target_id, slot, max_range_m=None, connection=None):
    """Grid-aware range gate for attacks and combat techniques.

    When attacker and target share a map with a logical grid and both have
    positions, melee/touch require adjacency (1 cell) and ranged requires
    ``max_range_m`` when defined. Anything else passes silently: without a
    grid the Mestre adjudica (assisted), never invented.
    """
    with (nullcontext(connection) if connection is not None else closing(connect(path))) as db:
        cursor = db.cursor()
        cursor.row_factory = sqlite3.Row
        if target_type == "token":
            target = cursor.execute("SELECT * FROM session_workspace_tokens WHERE id=?", (target_id,)).fetchone()
        else:
            target = cursor.execute("SELECT * FROM session_workspace_tokens WHERE character_id=? ORDER BY id LIMIT 1",
                                (target_id,)).fetchone()
        if target is None:
            return {"checked": False}
        actors = cursor.execute("SELECT * FROM session_workspace_tokens WHERE character_id=?",
                            (actor_character_id,)).fetchall()
        partner = next((a for a in actors if a["map_id"] == target["map_id"]), None)
        if partner is None:
            return {"checked": False}
        grid = grid_record(cursor, target["map_id"])
        if not grid:
            return {"checked": False}
        pos = lambda token_id: cursor.execute("SELECT cell_x,cell_y FROM session_workspace_entity_positions"
                                          " WHERE map_id=? AND token_id=?",
                                          (target["map_id"], token_id)).fetchone()
        a, b = pos(partner["id"]), pos(target["id"])
        if not a or not b:
            return {"checked": False}
        cells = distance_cells(grid["distance_rule"], [a["cell_x"], a["cell_y"]], [b["cell_x"], b["cell_y"]])
        meters = cells * grid["cell_size_m"]
        if slot in {"melee", "touch"} and cells > 1:
            raise ValueError(f"Fora de alcance corpo a corpo ({cells} células)")
        if slot == "ranged" and max_range_m is not None and meters > max_range_m + 1e-8:
            raise ValueError(f"Fora de alcance ({meters:g} m, máximo {max_range_m:g} m)")
        return {"checked": True, "cells": cells, "meters": meters}


def targets_in_range(path, *, actor_character_id, attacker_token_id=None, map_id=None,
                      slot="melee", max_range_m=None, role="gm"):
    """List tokens on the same grid with distance and validity for an attack.

    Without a grid or positions, returns gridded False so the UI keeps the
    manual target picker (assisted). Never invents positions.
    """
    from .session_workspace import get_workspace_snapshot
    snapshot = get_workspace_snapshot(path, map_id=map_id or "default", is_gm=(role == "gm"))
    grid = (snapshot.get("map") or {}).get("grid")
    if not grid:
        return {"gridded": False, "slot": slot, "max_range_m": max_range_m, "targets": []}
    by_id = {t["id"]: t for t in snapshot.get("tokens", [])}
    attacker = by_id.get(attacker_token_id or "")
    if attacker is None:
        owned = [t for t in snapshot.get("tokens", []) if t.get("character_id") == actor_character_id]
        attacker = owned[0] if owned else None
    if attacker is None or not attacker.get("grid_position"):
        return {"gridded": False, "slot": slot, "max_range_m": max_range_m, "targets": []}
    origin = attacker["grid_position"]
    targets = []
    for token in snapshot.get("tokens", []):
        if token["id"] == attacker["id"] or token.get("token_type") == "location":
            continue
        pos = token.get("grid_position")
        if not pos:
            continue
        cells = distance_cells(grid["distance_rule"], [origin["cell_x"], origin["cell_y"]],
                               [pos["cell_x"], pos["cell_y"]])
        meters = cells * grid["cell_size_m"]
        if slot in {"melee", "touch"}:
            valid, reason = cells <= 1, "" if cells <= 1 else f"{cells} células (adjacência exigida)"
        elif max_range_m is not None:
            valid = meters <= max_range_m + 1e-8
            reason = "" if valid else f"{meters:g} m (máximo {max_range_m:g} m)"
        else:
            valid, reason = True, "alcance a confirmar com o Mestre"
        targets.append({"type": "token", "id": token["id"], "name": token.get("name"),
                        "cells": cells, "meters": meters, "valid": valid, "reason": reason,
                        "current_hp": token.get("current_hp"), "maximum_hp": token.get("maximum_hp")})
    targets.sort(key=lambda t: (t["cells"], t["name"] or ""))
    return {"gridded": True, "slot": slot, "max_range_m": max_range_m,
            "origin": {"token_id": attacker["id"], "cell_x": origin["cell_x"], "cell_y": origin["cell_y"]},
            "cell_size_m": grid["cell_size_m"], "targets": targets}


def distance_between(path, map_id, token_a, token_b, role='gm'):
    from .session_workspace import get_workspace_snapshot
    snapshot = get_workspace_snapshot(path, map_id=map_id, is_gm=role=='gm')
    if not snapshot.get('map') or snapshot['map']['id'] != map_id:
        raise PermissionError('Mapa indisponível')
    tokens = {t['id']:t for t in snapshot['tokens']}
    if token_a not in tokens or token_b not in tokens:
        raise PermissionError('Entidade indisponível')
    grid = snapshot['map'].get('grid')
    a,b = tokens[token_a].get('grid_position'),tokens[token_b].get('grid_position')
    if not grid or not a or not b:
        raise ValueError('Entidade sem posição lógica')
    cells = distance_cells(grid['distance_rule'],[a['cell_x'],a['cell_y']],[b['cell_x'],b['cell_y']])
    return dict(cells=cells,meters=cells*grid['cell_size_m'],rule=grid['distance_rule'],provisional=bool(grid['provisional']))


def reject_legacy_move(path, token_id):
    with closing(connect(path)) as db:
        token = db.execute('SELECT token_type,map_id FROM session_workspace_tokens WHERE id=?', (token_id,)).fetchone()
        encounter,_ = encounter_record(db)
        if token and token['token_type'] != 'location' and (grid_record(db,token['map_id']) or encounter.get('active')):
            raise ValueError('Use o comando de movimento por células; coordenadas visuais não movem combatentes')


def seed_session7_grids(path):
    """Only registered Session 7 maps; no imagery, zones, fog or old maps edited."""
    from .session7_content import MAPS
    init_spatial(path)
    with closing(connect(path)) as db:
        maps = [dict(row) for row in db.execute('SELECT id,title FROM session_workspace_maps')]
    results = []
    for item in maps:
        if item['title'] not in {value[0] for value in MAPS.values()}:
            continue
        with closing(connect(path)) as db:
            if grid_record(db,item['id']):
                continue
            encounter,_ = encounter_record(db)
            if encounter.get('active') and encounter.get('map_id') == item['id']:
                continue  # Never recalibrate an active battle on application startup.
        configure_grid(path,actor_id='master',role='gm',request_id='grid-s7-'+item['id'],map_id=item['id'],
            config=dict(cols=32,rows=24,cell_size_m=1.5),expected_version=0)
        results.append(item['id'])
    return results
