"""Reviewed campaign darts, over native ammunition, conditions and turn receipts.

Caio Mouriz, Expansão de Itens, T02-02, CC-BY-SA 4.0 supplies names/packs.
JP, consequences and victim-round duration were approved on 2026-11-01.
No free-form text is executed and no base weapon damage is invented.
"""
import json
import uuid
from copy import deepcopy
from .dice_rolls import roll_formula

RULE = 'campaign:special-darts:2026-11-01:v1'
_KINDS = {
    'alucinante': ('Dardo Alucinante', 'JPS', 'd20_penalty'),
    'cegante': ('Dardo Cegante', 'JPC', 'blinded'),
    'de-assobio': ('Dardo de Assobio', None, 'whistle'),
    'de-sono': ('Dardo de Sono', 'JPC', 'asleep'),
    'ensandecido': ('Dardo Ensandecido', 'JPS', 'd20_penalty'),
    'envenenado': ('Dardo Envenenado', 'JPC', 'poison_damage'),
    'fluorescente': ('Dardo Fluorescente', None, 'fluorescent'),
    'paralisante': ('Dardo Paralisante', 'JPC', 'paralyzed'),
}
SPECS = {'arma-distancia-dardo-' + key + '-x10': {
    'id': 'dart:' + key, 'name': name, 'save': save, 'effect': effect,
    'duration_formula': None if effect == 'whistle' else '1d4',
    'duration_unit': 'victim_rounds', 'campaign_rule': RULE,
    'poison': save is not None,
} for key, (name, save, effect) in _KINDS.items()}


def spec_for(path):
    return deepcopy(SPECS.get(str(path).removeprefix('compendium:')))


def confirm_hit(db, record, now):
    ammo = record['breakdown'].get('ammunition') or {}
    spec = ammo.get('effect')
    if not spec:
        return []
    from .item_defense import intercepted_strikes
    blocked = intercepted_strikes(record)
    hits = [s for index, s in enumerate(record['breakdown']['strikes'])
            if s['result'] == 'hit' and index not in blocked]
    if not hits:
        return []
    from .dorn_spells import target, save
    from .monster_conditions import _immune
    victim = target(db, record['target_type'], record['target_id'])
    results = []
    for _ in hits:
        result = {'name': spec['name'], 'effect': spec['effect'], 'campaign_rule': RULE}
        immune = _immune(db, victim['type'], victim['id'], spec) if spec['save'] else None
        if immune:
            results.append({**result, 'immune': immune})
            continue
        if spec['save']:
            saving = save(db, victim, 'wisdom' if spec['save'] == 'JPS' else 'constitution')
            result.update(save=saving, resisted=saving['success'])
            if saving['success']:
                results.append(result)
                continue
        if spec['effect'] == 'whistle':
            results.append({**result, 'signal': 'Assobio emitido; percepção e alcance do som sob controle do Mestre.'})
            continue
        rolled = roll_formula('1d4')
        turns = int(rolled['total'])
        previous = db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.dart_kind')=?",
            (victim['type'], victim['id'], spec['id'])).fetchone()
        old = json.loads(previous[1]) if previous else {}
        effect = {
            'id': previous[0] if previous else 'item-dart:' + uuid.uuid4().hex,
            'target_type': victim['type'], 'target_id': victim['id'],
            'label': spec['name'], 'source': spec['name'], 'duration': 'manual', 'rounds': None,
            'modifiers': {}, 'item_special': 'dart', 'dart_kind': spec['id'],
            'turns_remaining': max(turns, int(old.get('turns_remaining', 0))),
            'campaign_rule': RULE, 'source_duration_unit': 'victim_rounds',
            'monster_condition': spec['effect'], 'updated_at': now,
            'blocks_actions': spec['effect'] in {'asleep', 'paralyzed'},
            'immobilized': spec['effect'] in {'asleep', 'paralyzed'},
            **{k: old[k] for k in ('last_tick', 'last_finished') if k in old},
        }
        if spec['effect'] == 'd20_penalty':
            effect.update(difficult_tests=True, d20_penalty=-2,
                          condition_description='−2 nos testes de d20; não escolhe ações pela vítima.')
        elif spec['effect'] in {'asleep', 'paralyzed'}:
            effect['condition_description'] = 'Não pode agir nem se mover enquanto durar o efeito.'
        elif spec['effect'] == 'poison_damage':
            effect['condition_description'] = '1d4 de veneno no início de cada rodada da vítima.'
        elif spec['effect'] == 'fluorescent':
            effect['condition_description'] = 'Sinalização fluorescente; não altera visão, fog ou iluminação.'
        db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1) ON CONFLICT(id) DO UPDATE SET data_json=excluded.data_json,active=1',
            (effect['id'], victim['type'], victim['id'], json.dumps(effect, ensure_ascii=False)))
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        results.append({**result, 'effect_id': effect['id'], 'duration_roll': rolled,
                        'turns_remaining': effect['turns_remaining'], 'duration_unit': 'victim_rounds'})
    return results


def _key(participant, encounter):
    return [encounter.get('started_at'), encounter.get('turn_sequence'), participant['target_type'], participant['target_id']]


def _effects(db, participant):
    if not participant:
        return []
    from .monster_conditions import _canonical
    kind, identity = _canonical(db, participant['target_type'], participant['target_id'])
    return [(row[0], json.loads(row[1])) for row in db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.item_special')='dart'", (kind, identity)).fetchall()]


def turn_start(db, participant, encounter, now, request_id):
    from .combat_effects import change_hp
    from .session_ledger import append_session_ledger_event
    from .monster_runtime import public_token
    from .vezemir_skills import survives
    dead = False
    for identity, effect in _effects(db, participant):
        if effect['monster_condition'] != 'poison_damage' or effect.get('last_tick') == _key(participant, encounter):
            continue
        rolled = roll_formula('1d4')
        hp = change_hp(db, effect['target_type'], effect['target_id'], -int(rolled['total']), now,
                       damage_type='poison', damage_context={'kind': 'effect', 'magical': False})
        dead = hp['hp_after'] <= 0 and not (effect['target_type'] == 'character' and survives(db, effect['target_id'], hp['hp_after']))
        effect.update(last_tick=_key(participant, encounter), updated_at=now)
        db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?',
                   (json.dumps(effect, ensure_ascii=False), int(not dead), identity))
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        visible = effect['target_type'] == 'character' or public_token(db, effect['target_id'])
        append_session_ledger_event(db, source_type='item_dart',
            source_id=request_id + ':dart:' + identity + ':' + str(encounter.get('turn_sequence')),
            event_kind='action', actor_id='master', actor_name='Mestre', actor_role='gm',
            character_id=effect['target_id'] if effect['target_type'] == 'character' else None,
            title=effect['label'] + f": {hp['damage_taken']} de dano",
            detail={'roll': rolled, 'hp': hp, 'campaign_rule': RULE},
            visibility='table' if visible else 'gm', created_at=now)
    return dead


def finish_turn(db, participant, encounter, now):
    for identity, effect in _effects(db, participant):
        key = _key(participant, encounter)
        if effect.get('last_finished') == key:
            continue
        effect.update(turns_remaining=int(effect['turns_remaining']) - 1, last_finished=key, updated_at=now)
        db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?',
                   (json.dumps(effect, ensure_ascii=False), int(effect['turns_remaining'] > 0), identity))
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')


def end_combat(db):
    db.execute("UPDATE combat_effects SET active=0 WHERE json_extract(data_json,'$.item_special')='dart'")
