# -*- coding: utf-8 -*-
"""Approved Dorn verbs, executed inside the existing effect-command transaction."""
import json
from .dice_rolls import resolve_character_roll, roll_formula


PROTOCOLS = [
    {"id": "dorn_guard", "name": "Protocolo de Guarda", "kind": "technique", "group": "Acoes / Protocolos", "description": "Protege aliados a até 9 m até o próximo turno; Dorn recebe metade do dano redirecionado. Recarga 5–6 em 1d6."},
    {"id": "dorn_vanguard", "name": "Protocolo de Vanguarda", "kind": "technique", "group": "Acoes / Protocolos", "description": "Dorn assume a frente da formacao ate desativar ou encerrar a cena."},
    {"id": "dorn_diagnose", "name": "Diagnostico da Unidade", "kind": "technique", "group": "Acoes / Protocolos", "description": "Uma acao e teste de INT para analisar um mecanismo, constructo ou componente. Informacao objetiva determinada pelo Mestre; falha inconclusiva."},
]
for protocol in PROTOCOLS:
    protocol.update(active=True, blocked=False, mechanics_status='structured', source='Protocolos DORN-7 aprovados pelo Mestre')


def _ensure_resource(db, profile_id, key, label, maximum=1):
    row = db.execute("SELECT state_json FROM character_states WHERE profile_id=?", (profile_id,)).fetchone()
    if not row:
        return
    state = json.loads(row[0])
    resources = state.setdefault('resources', [])
    if next((r for r in resources if r.get('key') == key), None) is None:
        resources.append({'key': key, 'label': label, 'current': maximum, 'maximum': maximum})
        db.execute("UPDATE character_states SET state_json=?,version=version+1 WHERE profile_id=?", (json.dumps(state, ensure_ascii=False), profile_id))


def protects_ally(db, effect, ally_id):
    if not effect:
        return False
    if effect.get('protocol') != 'guard':
        return False
    if ally_id == 'dorn7':
        return False
    dorn=db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()
    if not dorn or int(json.loads(dorn[0]).get('current_hp') or 0)<=0:return False
    if not effect.get('area_guard'):return effect.get('ally_id')==ally_id
    ally = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (ally_id,)).fetchone()
    if ally:
        try:
            ally_state = json.loads(ally[0])
            if int(ally_state.get('current_hp') or 0) <= 0:
                return False
        except Exception:
            return False
    else:
        return False
    encounter_row = db.execute("SELECT encounter_json FROM combat_effect_clock WHERE id=1").fetchone()
    encounter = json.loads(encounter_row[0] or '{}') if encounter_row and encounter_row[0] else {}
    participants = encounter.get('participants') or []
    if not any(p.get('target_type') == 'character' and p.get('target_id') == ally_id for p in participants):
        return False
    if not encounter.get('active'):return False
    from .spatial_grid import distance_cells
    points=[]
    for identity in ('dorn7',ally_id):
        row=db.execute('SELECT p.cell_x,p.cell_y,g.cell_size_m,g.distance_rule FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id JOIN session_workspace_map_grids g ON g.map_id=t.map_id WHERE t.character_id=? AND t.map_id=? ORDER BY t.id LIMIT 1',(identity,encounter.get('map_id'))).fetchone()
        if not row:return False
        points.append(row)
    return distance_cells(points[0][3],points[0][:2],points[1][:2])*points[0][2]<=9+1e-9


def command(db, snapshot, action, payload, now):
    approved = db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='dorn7'").fetchone()
    if not approved or not str(json.loads(approved[0]).get('approved_build') or '').startswith('dorn-mage'):
        raise ValueError('Protocolos disponiveis somente na ficha aprovada de Dorn')
    row = db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()
    if not row or int(json.loads(row[0]).get('current_hp') or 0) <= 0:
        raise ValueError('Dorn precisa estar operacional')
    encounter = snapshot.get('encounter') or {}
    active = encounter.get('active')
    members = encounter.get('participants') or []
    current = members[int(encounter.get('turn_index') or 0) % len(members)] if active and members else None
    effects = [e for e in snapshot['effects'] if e.get('protocol') in {'guard', 'vanguard'} and e['target_id'] == 'dorn7']
    if action == 'dorn_vanguard':
        if active and payload.get('enabled') is not False:
            raise ValueError('Vanguarda e um protocolo de exploracao; encerre o combate')
        if type(payload.get('enabled')) is not bool:
            raise ValueError('Informe ativar ou desativar')
        db.execute("UPDATE combat_effects SET active=0 WHERE id='dorn:vanguard'")
        if not payload['enabled']:
            return {'protocol': 'vanguard', 'active': False}
        effect = dict(id='dorn:vanguard', target_type='character', target_id='dorn7', label='Protocolo de Vanguarda', source='DORN-7 · protocolo aprovado', duration='scene', rounds=None, modifiers={}, protocol='vanguard', updated_at=now)
    else:
        if active:
            from .battle_mode import require_battle_turn
            require_battle_turn(db, snapshot, 'dorn7')
            if not current or (current.get('target_type'), current.get('target_id')) != ('character', 'dorn7'):
                raise ValueError('Aguarde o turno de Dorn')
            if encounter.get('action_committed') or encounter.get('attacks_used', 0):
                raise ValueError('A acao deste turno ja foi usada')
        if action == 'dorn_guard':
            if not active:
                raise ValueError('Guarda requer um combate ativo')
            legacy_target=payload.get('ally_id')
            if legacy_target is None:
                if not db.execute("SELECT 1 FROM sqlite_master WHERE name='session_workspace_entity_positions'").fetchone():raise ValueError('Guarda de área exige o grid do combate')
                if not db.execute("SELECT 1 FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id JOIN session_workspace_map_grids g ON g.map_id=t.map_id WHERE t.character_id='dorn7' AND t.map_id=?",(encounter.get('map_id'),)).fetchone():raise ValueError('Posicione Dorn no grid do combate')
            if legacy_target is not None:
                if legacy_target=='dorn7' or not any(p.get('target_type')=='character' and p.get('target_id')==legacy_target for p in members):
                    raise ValueError('Escolha um aliado participante, diferente de Dorn')
                ally=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(legacy_target,)).fetchone()
                if not ally or int(json.loads(ally[0]).get('current_hp') or 0)<=0 or payload.get('position_confirmed') is not True:
                    raise ValueError('Confirme um aliado vivo e uma posição plausível para interposição')
                if payload.get('grid_selection'):
                    from .spatial_grid import check_attack_range
                    checked=check_attack_range(None,connection=db,actor_character_id='dorn7',target_type='character',target_id=legacy_target,slot='touch')
                    if not checked['checked']:raise ValueError('Posicione o aliado no grid')
            if any(e.get('protocol') == 'guard' for e in effects):
                raise ValueError('Guarda ja esta ativa')
            _ensure_resource(db, 'dorn7', 'dorn_guard', 'Protocolo de Guarda', 1)
            state_row = db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()
            state = json.loads(state_row[0]) if state_row else {}
            resources = state.get('resources') or []
            guard_res = next((r for r in resources if r.get('key') == 'dorn_guard'), None)
            if not guard_res or int(guard_res.get('current') or 0) < 1:
                raise ValueError('Sem preparacao disponivel')
            guard_res['current'] = int(guard_res.get('current') or 0) - 1
            db.execute("UPDATE character_states SET state_json=?,version=version+1 WHERE profile_id='dorn7'", (json.dumps(state, ensure_ascii=False),))
            effect = dict(id='dorn:guard', target_type='character', target_id='dorn7', label='Protocolo de Guarda', source='DORN-7 · protocolo aprovado', duration='manual', rounds=None, modifiers={}, protocol='guard', area_guard=True, radius_m=9, until='Inicio do proximo turno de Dorn', updated_at=now)
            if legacy_target is not None:
                effect.pop('area_guard');effect.pop('radius_m');effect['ally_id']=legacy_target
        elif action == 'dorn_diagnose':
            subject = str(payload.get('subject') or '').strip()
            if not subject or len(subject) > 160:
                raise ValueError('Informe o mecanismo ou componente analisado')
            definition = payload.get('_definition') or {}
            spec = resolve_character_roll(definition, [], 'attribute', 'intelligence')
            difficulty = payload.get('difficulty')
            if type(difficulty) is not int or not 1 <= difficulty <= 99:
                raise ValueError('O Mestre deve definir a dificuldade de 1 a 99')
            rolled = roll_formula(spec.formula)
            result = dict(protocol='diagnose', subject=subject, formula=spec.formula, total=rolled['total'], dice=rolled['individual_results'], difficulty=difficulty, outcome='success' if rolled['total'] >= difficulty else 'inconclusive', information=None, adjudication='Mestre determina a informacao objetiva; nenhuma informacao narrativa foi revelada automaticamente.')
            effect = None
        else:
            raise ValueError('Protocolo invalido')
        if active:
            encounter.update(action_committed=True, attacks_used=1, attack_limit=1, last_action={'actor': {'target_type':'character', 'target_id':'dorn7'}, 'kind':'protocol', 'label': action, 'at':now})
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))
    if effect:
        db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1) ON CONFLICT(id) DO UPDATE SET data_json=excluded.data_json,active=1', (effect['id'], 'character', 'dorn7', json.dumps(effect, ensure_ascii=False)))
        return {'effect': effect}
    return result
