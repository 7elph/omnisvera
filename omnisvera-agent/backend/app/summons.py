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


def create_summon(path, *, caster, technique, spec, request_id, actor_id, actor_role, corpse_id=None):
    init_effects(path)
    fingerprint = json.dumps([caster, technique, corpse_id, actor_id, actor_role])
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
            corpse = db.execute("SELECT * FROM session_workspace_tokens WHERE id=? AND token_type='monster' AND map_id=? AND visible_to_players=1", (corpse_id, map_id)).fetchone()
            if corpse is None or corpse['current_hp'] != 0:
                raise ValueError('Selecione uma criatura morta e visível neste mapa')
            corpse_sheet = json.loads(corpse['sheet_json'] or '{}')
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
        resource['current'] -= 1
        anchor = corpse or db.execute("SELECT * FROM session_workspace_tokens WHERE token_type='character' AND character_id=? AND map_id=? ORDER BY id LIMIT 1", (caster, map_id)).fetchone()
        latitude, longitude = (anchor['latitude'], min(95, anchor['longitude'] + 5)) if anchor else (50, 50)
        token_id = 'monster:' + uuid.uuid4().hex
        name = f"{corpse['name']} reanimado" if corpse else spec['name']
        sheet = {'marker': spec['marker'], 'role': 'Aliado invocado', 'armor_class': spec['ac'],
            'attacks': [{'name': spec['attack_name'], 'bonus': spec['attack_bonus'], 'damage': spec['damage']}],
            'treasure': '-', 'summon': {'caster': caster, 'technique': technique, 'corpse_id': corpse_id,
                'duration': spec['duration'], 'defaults_note': spec['note']}}
        db.execute("INSERT INTO session_workspace_tokens(id,token_type,map_id,name,image_path,visible_to_players,color,latitude,longitude,current_hp,maximum_hp,conditions_json,sheet_json,created_at,updated_at) VALUES (?,'monster',?,?,?,1,'#7fb069',?,?,?,?, '[]',?,?,?)",
            (token_id, map_id, name, corpse['image_path'] if corpse else None, latitude, longitude, spec['hp'], spec['hp'], json.dumps(sheet, ensure_ascii=False), now.isoformat(), now.isoformat()))
        if corpse:
            corpse_sheet['reanimated_by'] = token_id
            db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?', (json.dumps(corpse_sheet), now.isoformat(), corpse_id))
        db.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?', (json.dumps(state, ensure_ascii=False), now.isoformat(), caster))
        commit_battle_action(db, snapshot)
        if encounter.get('active'):
            members = encounter.get('participants', [])
            index = next((i for i, p in enumerate(members) if p['target_type'] == 'character' and p['target_id'] == caster), None)
            if index is None:
                raise ValueError('O invocador não participa do combate')
            members.insert(index + 1, {'target_type': 'token', 'target_id': token_id, 'token_id': token_id,
                'name': name, 'controller_id': caster, 'initiative': members[index]['initiative']})
            if encounter.get('battle_mode'):
                encounter.setdefault('return_tokens', []).append({'id': token_id, 'map_id': encounter.get('return_map_id', map_id),
                    'latitude': latitude, 'longitude': longitude, 'visible_to_players': 1, 'created': False})
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        result = {'token': _token_record(db.execute('SELECT * FROM session_workspace_tokens WHERE id=?', (token_id,)).fetchone()), 'duration': spec['duration'], 'defaults_note': spec['note']}
        db.execute('INSERT INTO combat_effect_commands(request_id,fingerprint,response_json) VALUES(?,?,?)', (request_id, fingerprint, json.dumps(result)))
        append_session_ledger_event(db, source_type='summon', source_id=request_id, event_kind='action', actor_id=actor_id,
            actor_name=caster, actor_role=actor_role, character_id=caster, title=f'{caster} invocou {name}',
            detail={'token_id': token_id, 'corpse_id': corpse_id, 'technique': technique}, created_at=now.isoformat())
        return result
