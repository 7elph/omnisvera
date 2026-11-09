"""Atomic controlled summons in the current map and encounter."""
import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from .battle_mode import require_battle_turn, commit_battle_action
from .combat_effects import effect_snapshot, init_effects
from .session_ledger import append_session_ledger_event
from .session_workspace import _token_record


def dismiss_summon(path, *, caster, token_id, request_id, actor_id, actor_role):
    """Owner-authorized dismissal, not a kill or a daily-use refund."""
    init_effects(path)
    fingerprint=json.dumps(['dismiss',caster,token_id,actor_id,actor_role])
    now=datetime.now(timezone.utc).isoformat()
    with closing(sqlite3.connect(path,timeout=30)) as db, db:
        db.row_factory=sqlite3.Row;db.execute('BEGIN IMMEDIATE')
        if actor_role!='gm' and actor_id!=caster:raise PermissionError('Você não controla esta invocação')
        old=db.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?',(request_id,)).fetchone()
        if old:
            if old['fingerprint']!=fingerprint:raise ValueError('Esta requisição já foi usada para outra ação')
            return json.loads(old['response_json'])
        token=db.execute('SELECT * FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()
        sheet=json.loads(token['sheet_json'] or '{}') if token else {}
        if not token or sheet.get('summon',{}).get('caster')!=caster:
            raise PermissionError('Você não controla esta invocação')
        if sheet['summon'].get('technique')=='clonagem':raise ValueError('Encerre a concentração para dispensar os clones')
        sheet['summon']['dismissed']=True;sheet['combat_retired']=True;sheet.pop('corpse',None)
        db.execute('UPDATE session_workspace_tokens SET current_hp=0,sheet_json=?,updated_at=? WHERE id=?',(json.dumps(sheet),now,token_id))
        db.execute("UPDATE combat_effects SET active=0 WHERE target_type='token' AND target_id=?",(token_id,))
        from .battle_mode import retire_defeated
        retire_defeated(db,now)
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        result={'dismissed':token_id,'resource_refunded':False}
        db.execute('INSERT INTO combat_effect_commands VALUES(?,?,?)',(request_id,fingerprint,json.dumps(result)))
        append_session_ledger_event(db,source_type='summon_dismissal',source_id=request_id,event_kind='action',actor_id=actor_id,
            actor_name=caster,actor_role=actor_role,character_id=caster,title=f"{caster} dispensou {token['name']}",detail=result,created_at=now)
        return result


def create_summon(path, *, caster, technique, spec, request_id, actor_id, actor_role, corpse_id=None, reuse_existing=False, replace_token_id=None):
    if actor_role != 'gm' and actor_id != caster:
        raise PermissionError('Você não controla esta invocação')
    if replace_token_id and technique != 'levantar-esqueleto':
        raise ValueError('A substituição se aplica somente ao esqueleto invocado')
    from .character_play import attach_spell_images
    artwork_id = 'levantar-um-esqueleto' if technique == 'levantar-esqueleto' else technique
    artwork = attach_spell_images([{'id': artwork_id, 'kind': 'spell'}])[0].get('image_path')
    init_effects(path)
    fingerprint = json.dumps([caster, technique, corpse_id, actor_id, actor_role])
    if reuse_existing:
        fingerprint += ':reuse'
    if replace_token_id:
        fingerprint += ':replace:' + replace_token_id
    now = datetime.now(timezone.utc)
    with closing(sqlite3.connect(path, timeout=30)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN IMMEDIATE')
        old = db.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?', (request_id,)).fetchone()
        if old:
            if old['fingerprint'] != fingerprint:
                raise ValueError('Esta requisição já foi usada para outra ação')
            return json.loads(old['response_json'])
        snapshot = effect_snapshot(db)
        replacement = None
        if technique == 'levantar-esqueleto':
            active = []
            for token in db.execute('SELECT * FROM session_workspace_tokens WHERE current_hp>0'):
                sheet = json.loads(token['sheet_json'] or '{}')
                summon = sheet.get('summon') or {}
                if summon.get('caster') == caster and summon.get('technique') == technique and not (sheet.get('combat_retired') or summon.get('dismissed')):
                    active.append(token)
            if len(active) > 1:
                raise ValueError('Há mais de um esqueleto ativo; dispense as invocações excedentes antes de invocar')
            if replace_token_id:
                if not active or active[0]['id'] != replace_token_id:
                    raise ValueError('A invocação mudou. Atualize antes de confirmar a substituição')
                replacement = active[0]
            elif active:
                token = active[0]
                if reuse_existing:
                    encounter = snapshot.get('encounter') or {}
                    workspace = db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
                    current_map = encounter.get('map_id') if encounter.get('active') and encounter.get('battle_mode') else workspace['map_id'] if workspace else None
                    summon = json.loads(token['sheet_json'] or '{}')['summon']
                    result = {'existing': True, 'existing_token_id': token['id'], 'duration': summon.get('duration'),
                              'needs_replacement': not token['visible_to_players'] or token['map_id'] != current_map}
                    # The owner can replace their unit, without receiving any
                    # hidden map coordinates/sheet from a player's request.
                    if token['visible_to_players']:
                        result['token'] = _token_record(token)
                    db.execute('INSERT INTO combat_effect_commands(request_id,fingerprint,response_json) VALUES(?,?,?)',(request_id,fingerprint,json.dumps(result)))
                    return result  # Inspection/cancellation spends nothing.
                raise ValueError('Apenas um esqueleto ativo por invocador; a invocação existente ainda está viva')
        require_battle_turn(db, snapshot, caster)
        if int((snapshot.get('encounter') or {}).get('attacks_used') or 0):
            raise ValueError('A invocação exige uma ação completa ainda disponível')
        encounter = snapshot.get('encounter') or {}
        workspace = db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
        if workspace is None:
            raise ValueError('Abra um mapa antes de invocar')
        map_id = encounter.get('map_id') if encounter.get('active') and encounter.get('battle_mode') else workspace['map_id']
        corpse = None
        if technique == 'animar-mortos':
            corpse = db.execute("SELECT * FROM session_workspace_tokens WHERE id=? AND token_type!='location' AND map_id=? AND visible_to_players=1", (corpse_id, map_id)).fetchone()
            if corpse is None or corpse['current_hp'] != 0:
                raise ValueError('Selecione uma criatura morta e visível neste mapa')
            corpse_sheet = _token_record(corpse)['sheet']
            if corpse['character_id']:
                body_state=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(corpse['character_id'],)).fetchone()
                if body_state and int(json.loads(body_state[0]).get('current_hp') or 0)>0:
                    raise ValueError('O personagem ainda está vivo')
            if corpse_sheet.get('summon') or corpse_sheet.get('reanimated_by'):
                raise ValueError('Este cadáver já foi utilizado ou pertence a uma invocação')
            if not corpse_sheet.get('reanimation_allowed'):
                raise ValueError('O Mestre precisa autorizar este cadáver para reanimação')
        state_row = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (caster,)).fetchone()
        if state_row is None:
            raise ValueError('Ficha do invocador indisponível')
        state = json.loads(state_row['state_json'])
        resource = next((r for r in state.get('resources', []) if r['key'] == spec['resource_key']), None)
        if not resource or resource.get('current', 0) < 1:
            raise ValueError('Sem usos disponíveis para esta invocação')
        if replacement:
            sheet = json.loads(replacement['sheet_json'] or '{}')
            sheet['summon']['dismissed'] = True
            sheet['combat_retired'] = True
            sheet.pop('corpse', None)
            db.execute('UPDATE session_workspace_tokens SET current_hp=0,sheet_json=?,updated_at=? WHERE id=?', (json.dumps(sheet), now.isoformat(), replace_token_id))
            db.execute("UPDATE combat_effects SET active=0 WHERE target_type='token' AND target_id=?", (replace_token_id,))
            from .battle_mode import retire_defeated
            retire_defeated(db, now.isoformat())
            snapshot = effect_snapshot(db)
            encounter = snapshot.get('encounter') or {}
        resource['current'] -= 1
        anchor = corpse or db.execute("SELECT * FROM session_workspace_tokens WHERE token_type='character' AND character_id=? AND map_id=? ORDER BY id LIMIT 1", (caster, map_id)).fetchone()
        latitude, longitude = (anchor['latitude'], min(95, anchor['longitude'] + 5)) if anchor else (50, 50)
        token_id = 'monster:' + uuid.uuid4().hex
        name = f"{corpse['name']} reanimado" if corpse else spec['name']
        sheet = {'has_blood': False, 'marker': spec['marker'], 'role': 'Aliado invocado', 'armor_class': spec['ac'],
            'attacks': [{'name': spec['attack_name'], 'bonus': spec['attack_bonus'], 'damage': spec['damage']}],
            'treasure': '-', 'summon': {'caster': caster, 'technique': technique, 'corpse_id': corpse_id,
                'duration': spec['duration'], 'defaults_note': spec['note']}}
        from .summon_profiles import complete_sheet
        sheet=complete_sheet(sheet)
        from .spatial_grid import grid_record,visual_position,has_schema
        grid=grid_record(db,map_id) if has_schema(db) else None
        origin=db.execute('SELECT * FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',
            (map_id,anchor['id'])).fetchone() if grid and anchor else None
        destination=None
        if origin:
            # Reuse clone placement's live footprints and this map's distance
            # rule/scale. Choose before INSERT so the new pin cannot block itself.
            from .morthak_high_spells import available_cells
            start=(origin['cell_x'],origin['cell_y'])
            cells,_=available_cells(db,map_id,start,grid['cell_size_m'])
            cells=[cell for cell in cells if cell!=start]
            if not cells:raise ValueError('Não há célula adjacente livre para esta invocação')
            preferred=(start[0]+1 if start[0]+1<grid['cols'] else max(0,start[0]-1),start[1])
            x,y=preferred if preferred in cells else cells[0]
            destination={**dict(origin),'token_id':token_id,'cell_x':x,'cell_y':y}
        db.execute("INSERT INTO session_workspace_tokens(id,token_type,map_id,name,image_path,visible_to_players,color,latitude,longitude,current_hp,maximum_hp,conditions_json,sheet_json,created_at,updated_at) VALUES (?,'monster',?,?,?,1,'#7fb069',?,?,?,?, '[]',?,?,?)",
            (token_id, map_id, name, artwork, latitude, longitude, spec['hp'], spec['hp'], json.dumps(sheet, ensure_ascii=False), now.isoformat(), now.isoformat()))
        if corpse:
            corpse_sheet['reanimated_by'] = token_id
            db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?', (json.dumps(corpse_sheet), now.isoformat(), corpse_id))
        if destination:
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=?,cell_y=?,version=version+1 WHERE map_id=? AND token_id=?',(destination['cell_x'],destination['cell_y'],map_id,token_id))
            visual=visual_position(grid,destination);latitude,longitude=visual['latitude'],visual['longitude']
            db.execute('UPDATE session_workspace_tokens SET latitude=?,longitude=? WHERE id=?',(latitude,longitude,token_id))
        db.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?', (json.dumps(state, ensure_ascii=False), now.isoformat(), caster))
        commit_battle_action(db, snapshot)
        if encounter.get('active'):
            members = encounter.get('participants', [])
            current = members[encounter.get('turn_index', 0)] if members else None
            if corpse:
                members = [p for p in members if not (p['target_type'] == 'token' and p['target_id'] == corpse_id)]
                encounter['participants'] = members
            index = next((i for i, p in enumerate(members) if p['target_type'] == 'character' and p['target_id'] == caster), None)
            if index is None:
                raise ValueError('O invocador não participa do combate')
            members.insert(index + 1, {'target_type': 'token', 'target_id': token_id, 'token_id': token_id,
                'name': name, 'controller_id': caster, 'initiative': members[index]['initiative']})
            if current:
                encounter['turn_index'] = next(i for i, p in enumerate(members)
                    if (p['target_type'], p['target_id']) == (current['target_type'], current['target_id']))
            if encounter.get('battle_mode'):
                encounter.setdefault('return_tokens', []).append({'id': token_id, 'map_id': encounter.get('return_map_id', map_id),
                    'latitude': latitude, 'longitude': longitude, 'visible_to_players': 1, 'created': False})
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        result = {'token': _token_record(db.execute('SELECT * FROM session_workspace_tokens WHERE id=?', (token_id,)).fetchone()), 'duration': spec['duration'], 'defaults_note': spec['note']}
        if replacement:
            result['replaced_token_id'] = replace_token_id
        db.execute('INSERT INTO combat_effect_commands(request_id,fingerprint,response_json) VALUES(?,?,?)', (request_id, fingerprint, json.dumps(result)))
        append_session_ledger_event(db, source_type='summon', source_id=request_id, event_kind='action', actor_id=actor_id,
            actor_name=caster, actor_role=actor_role, character_id=caster, title=f'{caster} invocou {name}',
            detail={'token_id': token_id, 'corpse_id': corpse_id, 'technique': technique, 'replaced_token_id': replace_token_id}, created_at=now.isoformat())
        return result
