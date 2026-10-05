"""Explicit one-time GM-approved replacement, never run during startup/reads."""
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

from .character_play import _now, _write_event

SPEC = json.loads((Path(__file__).parent / 'data/dorn7_mage2.json').read_text(encoding='utf-8'))


def apply_dorn_mage(database_path):
    with closing(sqlite3.connect(database_path)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN IMMEDIATE')
        row = db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='dorn7'").fetchone()
        overrides = json.loads(row[0]) if row else {}
        if overrides.get('approved_build') == SPEC['version']:
            return {'applied': False, 'reason': 'already_applied'}
        sheetrow = db.execute("SELECT * FROM character_sheets WHERE profile_id='dorn7'").fetchone()
        staterow = db.execute("SELECT * FROM character_states WHERE profile_id='dorn7'").fetchone()
        if not sheetrow or not staterow:
            raise ValueError('Dorn precisa ter a ficha de jogador existente; não criar perfil substituto.')
        state = json.loads(staterow['state_json'])
        # Refuse changed/ambiguous data, rather than discarding ongoing play.
        if state.get('current_hp') != 20 or state.get('maximum_hp') != 20 or state.get('resources'):
            raise ValueError('Estado de Dorn mudou: revisar PV/recursos antes de substituir por 13/13.')
        if db.execute("SELECT 1 FROM player_inventory WHERE profile_id='dorn7'").fetchone():
            raise ValueError('Inventário existente: conciliar sem duplicar itens antes de aplicar.')
        clock = db.execute('SELECT encounter_json FROM combat_effect_clock LIMIT 1').fetchone()
        encounter = json.loads(clock[0] or '{}') if clock else {}
        pins = [r[0] for r in db.execute("SELECT id FROM session_workspace_tokens WHERE character_id='dorn7'")]
        ids = {'dorn7', *pins}
        if encounter.get('active') and any(p.get('target_id') in ids for p in encounter.get('participants', [])):
            raise ValueError('Dorn participa do combate ativo; não modificar a ficha agora.')
        for r in db.execute('SELECT target_id FROM combat_effects WHERE active=1'):
            if r[0] in ids:
                raise ValueError('Dorn possui efeito ativo; resolver antes da troca.')
        now = _now()
        for r in db.execute("SELECT actor_character_id,target_id FROM combat_attack_resolutions WHERE status='pending' AND expires_at>?", (now,)):
            if r[0] in ids or r[1] in ids:
                raise ValueError('Há ataque pendente envolvendo Dorn.')
        before = {'sheet': dict(sheetrow), 'overrides': overrides, 'state': dict(staterow)}
        data = json.loads(sheetrow['data_json'])
        data.update(deepcopy(SPEC['sheet']))
        # Only replace mechanics covered by the approval; private annotations survive.
        for key in ('level_pending', 'advancement_attack_delta', 'advancement_base_attack',
                    'advancement_saving_throw', 'advancement_resources', 'natural_attacks',
                    'approved_session_abilities', 'level_advancement', 'advancement_history', 'attack_count'):
            overrides.pop(key, None)
        overrides.update(approved_build=SPEC['version'], level=2, maximum_hp=13,
                         armor_class=11, movement='9 m', race='Constructo Arcano', class_name='Mago',
                         attributes=data['attributes'], experience=2500,
                         approved_session_abilities=[dict(a, source=SPEC['source']) for a in SPEC['abilities']])
        state.update(current_hp=13, maximum_hp=13, resources=[{
            'key': a['uses']['resource_key'], 'label': a['uses']['label'],
            'current': 1, 'maximum': 1, 'recharge': 'inn_rest'
        } for a in SPEC['abilities']])
        state['session_notes'] = (state.get('session_notes') or '') + '\nFicha substituída por Constructo Arcano / Mago2 em 03/10/2026. Mecânica anterior arquivada no evento de reconciliação.'
        item_paths = []
        for item in SPEC['items']:
            mechanics = {'equipment_slots': ['arma corpo a corpo'] if item.get('damage') else [],
                         'damage_formula': item.get('damage', ''), 'consume_mode': 'none', 'slot_limit': 1}
            cursor = db.execute('INSERT INTO session_custom_items(name,item_type,description,effects_json,effect_rules_json,mechanics_json,usable,image_path,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (item['name'], item['type'], item['description'], '[]', '[]', json.dumps(mechanics), 0, None, now, now))
            path = f'session-item:{cursor.lastrowid}'
            item_paths.append(path)
            equipped = bool(item.get('equipped'))
            db.execute('INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,equipment_slot,notes,updated_at) VALUES(?,?,?,?,?,?,?,?)',
                ('dorn7', path, item['name'], 1, int(equipped), 'arma corpo a corpo' if equipped else None, SPEC['version'], now))
        db.execute("UPDATE character_sheets SET data_json=?,updated_at=? WHERE profile_id='dorn7'", (json.dumps(data, ensure_ascii=False), now))
        db.execute("INSERT INTO character_definition_overrides(profile_id,data_json,updated_at) VALUES('dorn7',?,?) ON CONFLICT(profile_id) DO UPDATE SET data_json=excluded.data_json,updated_at=excluded.updated_at", (json.dumps(overrides, ensure_ascii=False), now))
        db.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id='dorn7'", (json.dumps(state, ensure_ascii=False), now))
        event = _write_event(db, character_id='dorn7', actor_id='master', actor_role='gm',
            event_type='approved_build_reconciliation', field='approved_build', before=before,
            after={'sheet': data, 'overrides': overrides, 'state': state, 'item_paths': item_paths},
            reason=SPEC['source'], session_id=None)
        return {'applied': True, 'event_id': event, 'version': SPEC['version'], 'items': item_paths}
