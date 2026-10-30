"""Item use in the existing inventory, turn clock and ledger, atomically."""
import json
import sqlite3
from contextlib import closing
from .battle_mode import require_consumable_turn, commit_consumable_turn
from .character_play import _now, _write_event
from .combat_effects import init_effects, effect_snapshot, change_hp
from .construct_rules import validate_healing
from .dice_rolls import roll_formula
from .session_ledger import append_session_ledger_event

def replay_inventory_use(path,*,character_id,actor_id,actor_role,request_id,item_path):
    if not request_id:return None
    with closing(sqlite3.connect(path)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effect_commands'").fetchone():return None
        row=db.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?',(request_id,)).fetchone()
    if not row:return None
    expected=json.dumps(['use_item',character_id,actor_id,actor_role,item_path])
    if row[0]!=expected:raise ValueError('Requisição pertence a outra ação')
    return json.loads(row[1])


def use_inventory_item(path, *, character_id, actor_id, actor_role, request_id, item, session_id=None):
    if actor_role != 'gm' and actor_id != character_id:
        raise PermissionError('Você não pode usar o inventário deste personagem')
    if not request_id or len(request_id) > 120:
        raise ValueError('Informe uma chave idempotente para o consumível')
    item_path = str(item.get('item_path') or '')
    fingerprint = json.dumps(['use_item', character_id, actor_id, actor_role, item_path])
    init_effects(path)
    with closing(sqlite3.connect(path, timeout=30)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN IMMEDIATE')
        receipt = db.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?', (request_id,)).fetchone()
        if receipt:
            if receipt['fingerprint'] != fingerprint:
                raise ValueError('Requisição pertence a outra ação')
            return json.loads(receipt['response_json'])
        snapshot = effect_snapshot(db)
        require_consumable_turn(db, snapshot, character_id)
        inventory = db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?', (character_id, item_path)).fetchone()
        from .hp_potions import ITEM_PATH as HP_POTION_PATH, consumption_source
        if item_path == HP_POTION_PATH:
            inventory = consumption_source(db, character_id)
        if not inventory or inventory['quantity'] <= 0:
            raise ValueError('Item utilizável não encontrado no inventário')
        consumed_path = inventory['item_path']
        rules = [r for r in item.get('effect_rules') or [] if r.get('trigger') == 'on_use']
        if not item.get('usable') or not rules:
            raise ValueError('Este item não possui efeito configurado para uso')
        mechanics = item.get('mechanics') or {}
        consume_mode = mechanics.get('consume_mode') or 'quantity'
        if consume_mode not in {'quantity', 'charges', 'none'}:
            raise ValueError('Modo de consumo inválido')
        maximum = int(inventory['charges_max'] or mechanics.get('charges_max') or 0)
        charges = int(inventory['charges_current'] if inventory['charges_current'] is not None else maximum)
        if consume_mode == 'charges' and (maximum <= 0 or charges <= 0):
            raise ValueError('Este item está sem cargas')
        state_row = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (character_id,)).fetchone()
        if not state_row:
            raise ValueError('Ficha indisponível')
        before = json.loads(state_row[0])
        resources = {r['key'] for r in before.get('resources') or []}
        resolved = []
        for rule in rules:
            kind, target = rule.get('kind'), str(rule.get('target') or '').strip()
            if kind not in {'heal_hp', 'restore_resource', 'temporary_hp', 'add_condition'}:
                raise ValueError('Regra de uso incompatível')
            if kind == 'restore_resource' and target not in resources:
                raise ValueError('Recurso do efeito não encontrado')
            if kind == 'add_condition' and not target:
                raise ValueError('Informe a condição aplicada pelo item')
            if kind == 'heal_hp':
                validate_healing(db, character_id, rule.get('effect_category'))
            value = int(roll_formula(rule['formula'])['total']) if rule.get('formula') else int(rule.get('value') or 0)
            if kind != 'add_condition' and value <= 0:
                raise ValueError('O valor do efeito de uso deve ser positivo')
            resolved.append({**rule, 'resolved_value': value})
        now = _now()
        for rule in resolved:
            value, kind = rule['resolved_value'], rule['kind']
            if kind == 'heal_hp':
                change_hp(db, 'character', character_id, value, now)
                continue
            state = json.loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (character_id,)).fetchone()[0])
            if kind == 'restore_resource':
                resource = next(r for r in state['resources'] if r['key'] == rule['target'])
                resource['current'] = min(int(resource['maximum']), int(resource['current']) + value)
            elif kind == 'temporary_hp':
                state['temporary_hp'] = max(int(state.get('temporary_hp') or 0), value)
            else:
                duration = {'round': '1 rodada', 'scene': 'até o fim da cena', 'rest': 'até descansar'}.get(rule.get('duration'))
                condition = (f"{rule['target']} ({duration})" if duration else str(rule['target']))[:80]
                state['conditions'] = list(dict.fromkeys([*(state.get('conditions') or []), condition]))
            db.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?', (json.dumps(state, ensure_ascii=False), now, character_id))
        if consume_mode == 'quantity':
            db.execute('UPDATE player_inventory SET quantity=quantity-1,updated_at=? WHERE profile_id=? AND item_path=?', (now, character_id, consumed_path))
        elif consume_mode == 'charges':
            # Legacy holders display catalogue charge metadata without stored
            # columns. Persist its recharge cycle with the first consumption,
            # otherwise Master's rest cannot find the exhausted item.
            recharge=inventory['recharge'] or mechanics.get('recharge') or 'none'
            db.execute('UPDATE player_inventory SET charges_current=?,charges_max=?,recharge=?,updated_at=? WHERE profile_id=? AND item_path=?', (charges-1, maximum, recharge, now, character_id, item_path))
        commit_consumable_turn(db, snapshot)
        after = json.loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (character_id,)).fetchone()[0])
        # Character history and shared narrative remain native; no elevated player role.
        event_id = _write_event(db, character_id=character_id, actor_id=actor_id, actor_role=actor_role,
            event_type='use_item', field='consumable', before={'state': before, 'inventory': dict(inventory)},
            after={'state': after, 'item_path': item_path, 'consumed_item_path': consumed_path, 'consume_mode': consume_mode},
            reason=f"Usou {item['name']}", session_id=session_id)
        result = {'event_id': event_id, 'rules': resolved}
        append_session_ledger_event(db, source_type='item_use', source_id=request_id, event_kind='action',
            actor_id=actor_id, actor_name=character_id, actor_role=actor_role, character_id=character_id,
            title=f"{character_id} usou {item['name']}", detail={'item_path': item_path, 'item_name': item['name'],
                'rules': resolved, 'consumed_item_path': consumed_path, 'hp_before': before.get('current_hp'), 'hp_after': after.get('current_hp'),
                'turn_sequence': (snapshot.get('encounter') or {}).get('turn_sequence')}, visibility='table', created_at=now)
        db.execute('INSERT INTO combat_effect_commands VALUES(?,?,?)', (request_id, fingerprint, json.dumps(result)))
        return result
