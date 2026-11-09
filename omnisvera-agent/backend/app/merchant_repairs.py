"""Approved magical rust repair, composed inside native commerce transactions."""
from copy import deepcopy
import hashlib
import json

from .inventory_conditions import read_condition, save_condition
from .item_registry import digest


def require_no_combat(db):
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effect_clock'").fetchone():
        clock = db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()
        if clock and json.loads(clock[0] or '{}').get('active'):
            raise ValueError('Reparo mágico indisponível durante combate')


def preview(db, character_id, inventory_id):
    require_no_combat(db)
    if type(inventory_id) is not int or inventory_id <= 0:
        raise ValueError('Escolha o item a reparar')
    item = db.execute('SELECT * FROM player_inventory WHERE id=? AND profile_id=?', (inventory_id, character_id)).fetchone()
    if not item:
        raise ValueError('Item não pertence ao inventário selecionado')
    item = dict(item)
    state = read_condition(db, inventory_id)
    if not state or state.get('kind') != 'rust':
        raise ValueError('Item sem corrosão registrada')
    if state.get('destroyed') or item['quantity'] <= 0:
        raise ValueError('Reparo não recria um item destruído')
    if item['quantity'] != 1:
        raise ValueError('Separe uma unidade antes de reparar')
    from .monster_rust import _source, _selection, POLICY
    source = _source(db, item['item_path'])
    source_hash = hashlib.sha256(json.dumps(source, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if state.get('policy') != POLICY or state.get('source_fingerprint') != source_hash:
        raise ValueError('Revise a fonte e os componentes do encantamento antes de reparar')
    selection = _selection(source, state.get('selection'), None)
    original, remaining = state.get('original_bonus'), state.get('bonus_remaining')
    if (not selection or not selection['magical'] or selection['material'] != 'metal'
            or type(original) is not int or type(remaining) is not int
            or original != selection['enchantment_bonus'] or not 0 <= remaining < original
            or state.get('enhancement_rule_ids') != selection['enhancement_rule_ids']):
        raise ValueError('Não há perda de encantamento verificada para restaurar')
    return {'inventory_id': inventory_id, 'name': item['item_title'], 'item_path': item['item_path'],
            'bonus_before': remaining, 'bonus_after': original,
            'fingerprint': digest([item, state, source_hash])}


def available(db, character_id):
    result = []
    if not character_id or not db.execute("SELECT 1 FROM sqlite_master WHERE name='inventory_item_conditions'").fetchone():
        return result
    for row in db.execute('SELECT i.id FROM player_inventory i JOIN inventory_item_conditions c ON c.inventory_id=i.id WHERE i.profile_id=? AND i.quantity=1 ORDER BY i.id', (character_id,)).fetchall():
        try:
            result.append(preview(db, character_id, row['id']))
        except ValueError:
            continue
    return result


def apply(db, character_id, target, now):
    current = preview(db, character_id, target['inventory_id'])
    if current != target:
        raise ValueError('O item mudou; peça novo orçamento de reparo')
    state = deepcopy(read_condition(db, current['inventory_id']))
    state.update(bonus_remaining=current['bonus_after'], repaired_at=now)
    save_condition(db, current['inventory_id'], state, now)
    db.execute('UPDATE player_inventory SET updated_at=? WHERE id=?', (now, current['inventory_id']))
    return {'family': 'rust_repair', **{k: v for k, v in current.items() if k != 'fingerprint'}}
