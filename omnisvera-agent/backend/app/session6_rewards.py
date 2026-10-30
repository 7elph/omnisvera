"""Approved Session 6 rewards, equipped bonuses and turn-bound vine saves."""
import json
import random
import uuid

from .battle_mode import require_consumable_turn, commit_consumable_turn, require_battle_target
from .session_ledger import append_session_ledger_event


def equipped_item(db, owner, name):
    row = db.execute('SELECT item_path FROM player_inventory WHERE profile_id=? AND item_title=? AND equipped=1 AND quantity>0', (owner, name)).fetchone()
    return row is not None


def missile_maximum(inventory):
    return 4 if any(item.get('item_title') == 'Página de Grimório' and item.get('equipped') and int(item.get('quantity') or 0) > 0 for item in inventory) else 3


def synchronize_resource(resource, maximum):
    old_maximum = int(resource.get('maximum') or 0)
    if old_maximum == maximum:
        return False
    spent = old_maximum - int(resource.get('current') or 0) + int(resource.get('equipment_spent_overflow') or 0)
    resource.update(maximum=maximum, current=max(0, maximum - spent))
    if spent > maximum or 'equipment_spent_overflow' in resource:
        resource['equipment_spent_overflow'] = max(0, spent - maximum)
    return True


def cast_vines(db, snapshot, payload, now, actor_id, actor_role):
    if actor_role != 'gm' and actor_id != 'vezemir':
        raise PermissionError('A Pulseira de Vinhas pertence a Vezemir')
    if not equipped_item(db, 'vezemir', 'Pulseira de Vinhas'):
        raise ValueError('Equipe a Pulseira de Vinhas antes de usar')
    encounter = snapshot.get('encounter') or {}
    if not encounter.get('active') or not encounter.get('battle_mode'):
        raise ValueError('A Pulseira de Vinhas exige combate ativo')
    kind, target = payload['target_type'], payload['target_id']
    require_consumable_turn(db, snapshot, 'vezemir')
    require_battle_target(db, snapshot, kind, target)
    from .spatial_grid import check_attack_range
    from .combat import CAMPAIGN_RANGED_METERS
    check_attack_range(None, connection=db, actor_character_id='vezemir', target_type=kind,
        target_id=target, slot='ranged', max_range_m=CAMPAIGN_RANGED_METERS['pulseira-de-vinhas'])
    if kind == 'character' and target == 'vezemir':
        raise ValueError('Selecione outro alvo')
    if any(e.get('reward') == 'vines' and e['target_type'] == kind and e['target_id'] == target for e in snapshot['effects']):
        raise ValueError('Este alvo já está preso pelas vinhas')
    item = db.execute("SELECT item_path,charges_current,charges_max FROM player_inventory WHERE profile_id='vezemir' AND item_title='Pulseira de Vinhas' AND equipped=1 AND quantity>0").fetchone()
    maximum = int(item[2] or 2)
    remaining = maximum if item[1] is None else int(item[1])
    if remaining <= 0:
        raise ValueError('Sem usos disponíveis da Pulseira de Vinhas; descanse para recuperar')
    effect = add_restraint(db, kind, target, now, label='Pulseira de Vinhas',
        saving_throw=payload['_saving_throw'], saving_throw_bonus=payload['_saving_throw_bonus'],
        target_name=payload['_target_name'], reward='vines')
    db.execute("UPDATE player_inventory SET charges_current=?,charges_max=?,recharge='inn_rest',updated_at=? WHERE profile_id='vezemir' AND item_path=?", (remaining - 1, maximum, now, item[0]))
    commit_consumable_turn(db, snapshot)
    return effect


def add_restraint(db, kind, target, now, *, label, saving_throw, saving_throw_bonus=0, target_name='', **extra):
    if int(saving_throw or 0)<=0:
        raise ValueError('Configure a JP normal do alvo antes de imobilizar')
    if db.execute("SELECT 1 FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND (json_extract(data_json,'$.immobilized')=1 OR json_extract(data_json,'$.reward')='vines')",(kind,target)).fetchone():
        raise ValueError('Este alvo já está imobilizado')
    effect=dict(id='restraint:'+uuid.uuid4().hex,target_type=kind,target_id=target,
        label=label,source=label,duration='manual',rounds=None,modifiers={},turns_remaining=3,
        immobilized=True,saving_throw=int(saving_throw),saving_throw_bonus=int(saving_throw_bonus),target_name=target_name,updated_at=now,**extra)
    db.execute('INSERT INTO combat_effects(id,target_type,target_id,data_json,active) VALUES(?,?,?,?,1)',(effect['id'],kind,target,json.dumps(effect)))
    return effect


def vine_turn(db, participant, now, request_id, encounter):
    """Resolve once on entering the target's turn; command transaction handles replay."""
    row = db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.monster_condition') IS NULL AND (json_extract(data_json,'$.reward')='vines' OR json_extract(data_json,'$.immobilized')=1)", (participant['target_type'], participant['target_id'])).fetchone()
    if row is None:
        return False
    effect = json.loads(row[1])
    d20 = random.randint(1, 20)
    frightened=db.execute("SELECT 1 FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.necro_spell')='aterrorrizar'",(participant['target_type'],participant['target_id'])).fetchone()
    bonus=int(effect['saving_throw_bonus'])-(2 if frightened else 0)
    success = d20 + bonus >= effect['saving_throw']
    effect['turns_remaining'] -= 1
    active = not success and effect['turns_remaining'] > 0
    db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?', (json.dumps(effect), int(active), row[0]))
    text = f"{participant['name']} — JP contra {effect['label']}: d20 {d20}, bônus {bonus:+d}, JP {effect['saving_throw']}. "
    text += 'Libertou-se e pode agir.' if success else 'Falhou e passou o turno.'
    if not active and not success:
        text += ' A imobilização termina após o terceiro turno.'
    append_session_ledger_event(db, source_type='vines_save', source_id=f'{request_id}:{encounter.get("turn_sequence",0)}', event_kind='roll', actor_id=participant['target_id'], actor_name=participant['name'], actor_role='gm', character_id=participant['target_id'] if participant['target_type']=='character' else None, title=text, detail={'d20': d20, 'success': success}, visibility='public', created_at=now, game_session_id=encounter.get('game_session_id'))
    return not success
