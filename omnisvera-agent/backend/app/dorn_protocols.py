"""Approved Dorn verbs, executed inside the existing effect-command transaction."""
import json
from .dice_rolls import resolve_character_roll, roll_formula

PROTOCOLS = [
    {"id": "dorn_guard", "name": "Protocolo de Guarda", "kind": "technique", "group": "Ações / Protocolos", "description": "Uma ação; protege um aliado até o início do próximo turno de Dorn. Uma interposição, confirmada pelo Mestre antes da rolagem, transfere o ataque para Dorn sem bônus."},
    {"id": "dorn_vanguard", "name": "Protocolo de Vanguarda", "kind": "technique", "group": "Ações / Protocolos", "description": "Exploração assistida: Dorn assume a frente. Não detecta armadilhas nem protege automaticamente contra áreas. Até desativar ou encerrar a cena."},
    {"id": "dorn_diagnose", "name": "Diagnóstico da Unidade", "kind": "technique", "group": "Ações / Protocolos", "description": "Uma ação e teste de INT para analisar um mecanismo, constructo ou componente. Informação objetiva determinada pelo Mestre; falha inconclusiva."},
]
for protocol in PROTOCOLS:
    protocol.update(active=True, blocked=False, mechanics_status='structured', source='Protocolos DORN-7 aprovados pelo Mestre')


def command(db, snapshot, action, payload, now):
    approved = db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='dorn7'").fetchone()
    if not approved or not str(json.loads(approved[0]).get('approved_build') or '').startswith('dorn-mage'):
        raise ValueError('Protocolos disponíveis somente na ficha aprovada de Dorn')
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
            raise ValueError('Vanguarda é um protocolo de exploração; encerre o combate')
        if type(payload.get('enabled')) is not bool:
            raise ValueError('Informe ativar ou desativar')
        db.execute("UPDATE combat_effects SET active=0 WHERE id='dorn:vanguard'")
        if not payload['enabled']:
            return {'protocol': 'vanguard', 'active': False}
        effect = dict(id='dorn:vanguard', target_type='character', target_id='dorn7', label='Protocolo de Vanguarda', source='DORN-7 · protocolo aprovado', duration='scene', rounds=None, modifiers={}, protocol='vanguard', updated_at=now)
    else:
        if active:
            if not current or (current.get('target_type'), current.get('target_id')) != ('character', 'dorn7'):
                raise ValueError('Aguarde o turno de Dorn')
            if encounter.get('action_committed') or encounter.get('attacks_used', 0):
                raise ValueError('A ação deste turno já foi usada')
            if db.execute("SELECT 1 FROM combat_attack_resolutions WHERE actor_character_id='dorn7' AND status='pending' AND expires_at>?", (now,)).fetchone():
                raise ValueError('Resolva o ataque pendente antes do protocolo')
        if action == 'dorn_guard':
            if not active:
                raise ValueError('Guarda requer um combate ativo')
            target = payload.get('ally_id')
            if target == 'dorn7' or not any(p.get('target_type') == 'character' and p.get('target_id') == target for p in encounter.get('participants', [])):
                raise ValueError('Escolha um aliado participante, diferente de Dorn')
            ally = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (target,)).fetchone()
            if not ally or int(json.loads(ally[0]).get('current_hp') or 0) <= 0 or payload.get('position_confirmed') is not True:
                raise ValueError('Confirme um aliado vivo e uma posição plausível para interposição')
            if any(e.get('protocol') == 'guard' for e in effects):
                raise ValueError('Guarda já está ativa')
            effect = dict(id='dorn:guard', target_type='character', target_id='dorn7', label='Protocolo de Guarda', source='DORN-7 · protocolo aprovado', duration='manual', rounds=None, modifiers={}, protocol='guard', ally_id=target, until='Início do próximo turno de Dorn', updated_at=now)
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
            result = dict(protocol='diagnose', subject=subject, formula=spec.formula, total=rolled['total'], dice=rolled['individual_results'], difficulty=difficulty, outcome='success' if rolled['total'] >= difficulty else 'inconclusive', information=None, adjudication='Mestre determina a informação objetiva; nenhuma informação narrativa foi revelada automaticamente.')
            effect = None
        else:
            raise ValueError('Protocolo inválido')
        if active:
            encounter.update(action_committed=True, attacks_used=1, attack_limit=1, last_action={'actor': {'target_type':'character', 'target_id':'dorn7'}, 'kind':'protocol', 'label': action, 'at':now})
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))
    if effect:
        db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1) ON CONFLICT(id) DO UPDATE SET data_json=excluded.data_json,active=1', (effect['id'], 'character', 'dorn7', json.dumps(effect, ensure_ascii=False)))
        return {'effect': effect}
    return result
