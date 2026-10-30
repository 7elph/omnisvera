"""Morcego: live, individual flying pins covering a target on the native grid.

No saving throw, fixed timer or guaranteed dispersal is supplied by the source.
Call ``sync`` only inside an existing mutation transaction, never from a GET.
The horizontal grid cannot model altitude: overlap of declared flying bats is
the explicit, reversible spatial interpretation used here.
"""
from __future__ import annotations

import hashlib
import json

from .monster_movement import movement_modes


def _tables(db):
    return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _map_id(db, tables):
    if 'combat_effect_clock' in tables:
        raw = db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()
        encounter = json.loads(raw[0] or '{}') if raw else {}
        if encounter.get('active') and encounter.get('map_id'):
            return encounter['map_id']
    if 'session_workspace_state' in tables:
        row = db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
        if row:
            return row[0]
    return None


def _covers(a, b):
    return (a['cell_x'] < b['cell_x'] + b['footprint_w']
            and b['cell_x'] < a['cell_x'] + a['footprint_w']
            and a['cell_y'] < b['cell_y'] + b['footprint_h']
            and b['cell_y'] < a['cell_y'] + a['footprint_h'])


def _units(db, map_id, tables):
    fields = ('id', 'token_type', 'character_id', 'sheet_json', 'current_hp',
              'cell_x', 'cell_y', 'footprint_w', 'footprint_h')
    rows = db.execute('''SELECT t.id,t.token_type,t.character_id,t.sheet_json,t.current_hp,
        p.cell_x,p.cell_y,p.footprint_w,p.footprint_h
        FROM session_workspace_tokens t JOIN session_workspace_entity_positions p
        ON p.token_id=t.id AND p.map_id=t.map_id
        JOIN session_workspace_map_grids g ON g.map_id=p.map_id
        WHERE t.map_id=? AND t.token_type!='location' ORDER BY t.id''', (map_id,))
    units = []
    for raw in rows:
        unit = dict(zip(fields, raw))
        try:
            unit['sheet'] = json.loads(unit.pop('sheet_json') or '{}')
        except (ValueError, TypeError):
            continue
        sheet = unit['sheet']
        if not isinstance(sheet, dict):
            continue
        summon = sheet.get('summon')
        if isinstance(summon, dict) and summon.get('dismissed'):
            continue
        hp = unit['current_hp']
        if unit['character_id'] and 'character_states' in tables:
            state = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (unit['character_id'],)).fetchone()
            if state:
                hp = json.loads(state[0] or '{}').get('current_hp')
        # Unknown HP is no proof that a unit is a live swarm participant.
        if not isinstance(hp, (int, float)) or isinstance(hp, bool):
            continue
        if hp <= 0:
            from .vezemir_skills import survives
            if not unit['character_id'] or not survives(db, unit['character_id'], hp):
                continue
        units.append(unit)
    return units


def _flying_bat(unit):
    sheet = unit['sheet']
    source = sheet.get('source')
    if (unit['token_type'] != 'monster' or unit['character_id']
            or not isinstance(source, dict) or source.get('monster_id') != 'morcego'):
        return False
    try:
        modes = movement_modes(sheet.get('movement'))
    except (ValueError, TypeError):
        return False
    chosen = sheet.get('movement_mode')
    return modes.get('fly', 0) > 0 and (chosen == 'fly' or (chosen is None and set(modes) == {'fly'}))


def sync(db, now):
    """Reconcile conditional effects in the caller's native write transaction.

    Returns a compact mutation list. Repeated reconciliation of the same
    positions neither writes effects nor advances the combat version.
    No schema creation, transaction commit, rolls or gameplay state mutation
    outside the effects/clock tables occurs here.
    """
    tables = _tables(db)
    required = {'session_workspace_tokens', 'session_workspace_map_grids',
                'session_workspace_entity_positions', 'combat_effects', 'combat_effect_clock'}
    if not required <= tables:
        return []
    active_map = _map_id(db, tables)
    units = _units(db, active_map, tables) if active_map else []
    bats = [unit for unit in units if _flying_bat(unit)]
    expected = {}
    for unit in units:
        if _flying_bat(unit):
            continue
        covering = sum(_covers(bat, unit) for bat in bats)
        if covering < 10:
            continue
        kind, identity = ('character', unit['character_id']) if unit['character_id'] else ('token', unit['id'])
        identity_key = json.dumps([active_map, kind, identity], separators=(',', ':'))
        effect_id = 'bat-swarm:' + hashlib.sha256(identity_key.encode()).hexdigest()[:24]
        expected[effect_id] = {'id': effect_id, 'target_type': kind, 'target_id': identity,
            'label': 'Confusão · enxame', 'source': 'Morcego · confusão do enxame',
            'duration': 'manual', 'rounds': None, 'modifiers': {}, 'difficult_tests': True,
            'd20_penalty': True, 'monster_condition': 'swarm_confusion', 'bat_swarm': True,
            'map_id': active_map, 'swarm_count': 10,
            'condition_description': '−2 nas ações, exceto se debater e tentar afastar os morcegos. '
                'Termina quando menos de dez morcegos vivos em voo cobrem o alvo no grid.',
            'spatial_interpretation': 'flying_pin_footprint_overlap', 'updated_at': now}
    previous = {}
    for row in db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.bat_swarm')=1"):
        previous[row[0]] = json.loads(row[1])
    changes = []
    for identity, old in previous.items():
        if identity not in expected:
            db.execute('UPDATE combat_effects SET active=0 WHERE id=?', (identity,))
            changes.append({'expired': identity, 'reason': 'swarm_no_longer_covers_target'})
    for identity, effect in expected.items():
        old = previous.get(identity)
        if old and {k: v for k, v in old.items() if k != 'updated_at'} == {k: v for k, v in effect.items() if k != 'updated_at'}:
            continue
        db.execute('''INSERT INTO combat_effects VALUES(?,?,?,?,1)
            ON CONFLICT(id) DO UPDATE SET data_json=excluded.data_json,active=1''',
            (identity, effect['target_type'], effect['target_id'], json.dumps(effect, ensure_ascii=False)))
        changes.append({'applied': identity, 'target_type': effect['target_type'],
                        'target_id': effect['target_id'], 'condition': 'swarm_confusion'})
    if changes:
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return changes
