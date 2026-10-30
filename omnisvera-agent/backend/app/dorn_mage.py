"""Explicit one-time GM-approved replacement, never run during startup/reads."""
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

from .character_play import _now, _write_event

SPEC = json.loads((Path(__file__).parent / 'data/dorn7_mage3.json').read_text(encoding='utf-8'))


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
        upgrading = str(overrides.get('approved_build') or '').startswith('dorn-mage')
        if not upgrading and (state.get('current_hp') != 20 or state.get('maximum_hp') != 20 or state.get('resources')):
            raise ValueError('Estado de Dorn mudou: revisar PV/recursos antes de aplicar a ficha aprovada.')
        if not upgrading and db.execute("SELECT 1 FROM player_inventory WHERE profile_id='dorn7'").fetchone():
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
        for key, value in SPEC['sheet'].items():
            data[key] = {**data.get(key, {}), **deepcopy(value)}
        # Only replace mechanics covered by the approval; private annotations survive.
        for key in ('level_pending', 'advancement_attack_delta', 'advancement_base_attack',
                    'advancement_saving_throw', 'advancement_resources', 'natural_attacks',
                    'approved_session_abilities', 'level_advancement', 'attack_count'):
            overrides.pop(key, None)
        overrides.update(approved_build=SPEC['version'], name='Unidade DORN-7', level=3, maximum_hp=20,
                         armor_class=11, movement='9 m', race='Constructo Arcano', class_name='Mago',
                         attributes=data['attributes'], prepared_magic_override=True,
                         level_hp_anchor={'level': 3, 'maximum_hp': 20}, construct_traits=True,
                         approved_session_abilities=[dict(a, source=SPEC['source']) for a in SPEC['abilities']])
        spent = {r['key']: int(r['maximum']) - int(r['current']) for r in state.get('resources', [])}
        state.update(current_hp=min(int(state['current_hp']), 20), maximum_hp=20, resources=[{
            'key': a['uses']['resource_key'], 'label': a['uses']['label'],
            'current': max(0, a['uses']['maximum'] - spent.get(a['uses']['resource_key'], 0)), 'maximum': a['uses']['maximum'], 'recharge': 'inn_rest'
        } for a in SPEC['abilities'] if a.get('uses')])
        state['session_notes'] = (state.get('session_notes') or '') + '\nFicha aprovada: Constructo Arcano / Mago3, PV máximos 20. Estado anterior arquivado no evento.'
        item_paths = []
        for item in SPEC['items']:
            mechanics = {'equipment_slots': item.get('equipment_slots') or (['arma corpo a corpo'] if item.get('damage') else []),
                         'approved_equipment_slots': item.get('equipment_slots') or (['Corpo a corpo'] if item.get('damage') else []),
                         'damage_formula': item.get('damage', ''), 'thrown_damage_formula': item.get('thrown_damage'), 'consume_mode': 'none', 'slot_limit': 1}
            names = (item['name'], 'Cajado Rúnico' if item['name'] == 'Malha Rúnica' else item['name'])
            old = db.execute("SELECT * FROM player_inventory WHERE profile_id='dorn7' AND item_title IN (?,?)", names).fetchone()
            shared = old and db.execute("SELECT 1 FROM player_inventory WHERE item_path=? AND profile_id!='dorn7'", (old['item_path'],)).fetchone()
            if old and not shared and str(old['item_path']).startswith('session-item:'):
                path = old['item_path']
                db.execute('UPDATE session_custom_items SET name=?,description=?,mechanics_json=?,updated_at=? WHERE id=?',
                           (item['name'], item['description'], json.dumps(mechanics), now, int(path.split(':')[1])))
                db.execute("UPDATE player_inventory SET item_title=?,updated_at=? WHERE profile_id='dorn7' AND item_path=?", (item['name'], now, path))
            else:
                cursor = db.execute('INSERT INTO session_custom_items(name,item_type,description,effects_json,effect_rules_json,mechanics_json,usable,image_path,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (item['name'], item['type'], item['description'], '[]', '[]', json.dumps(mechanics), 0, None, now, now))
                path = f'session-item:{cursor.lastrowid}'
                if old:
                    db.execute("UPDATE player_inventory SET item_path=?,item_title=?,updated_at=? WHERE profile_id='dorn7' AND item_path=?", (path, item['name'], now, old['item_path']))
            item_paths.append(path)
            equipped = bool(item.get('equipped'))
            if old is None:
                db.execute('INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,equipment_slot,notes,updated_at) VALUES(?,?,?,?,?,?,?,?)',
                    ('dorn7', path, item['name'], int(item.get('quantity',1)), int(equipped), 'arma corpo a corpo' if equipped else None, SPEC['version'], now))
        db.execute("UPDATE character_sheets SET data_json=?,updated_at=? WHERE profile_id='dorn7'", (json.dumps(data, ensure_ascii=False), now))
        db.execute("INSERT INTO character_definition_overrides(profile_id,data_json,updated_at) VALUES('dorn7',?,?) ON CONFLICT(profile_id) DO UPDATE SET data_json=excluded.data_json,updated_at=excluded.updated_at", (json.dumps(overrides, ensure_ascii=False), now))
        db.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id='dorn7'", (json.dumps(state, ensure_ascii=False), now))
        event = _write_event(db, character_id='dorn7', actor_id='master', actor_role='gm',
            event_type='approved_build_reconciliation', field='approved_build', before=before,
            after={'sheet': data, 'overrides': overrides, 'state': state, 'item_paths': item_paths},
            reason=SPEC['source'], session_id=None)
        return {'applied': True, 'event_id': event, 'version': SPEC['version'], 'items': item_paths}
