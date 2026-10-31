"""Campaign throw contract, using native attacks, turn budget and recoverable loot."""
import json
import uuid

VIBRANIUM_ID = 'protecao-escudo-de-vibranium'


def _identity(db, kind, identity):
    if kind == 'token':
        row = db.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?', (identity,)).fetchone()
        if row and row[0]: return ['character', row[0]]
    return [kind, identity]


def followup(snapshot, actor):
    from .battle_mode import turn_identity
    key = turn_identity(snapshot)
    ticket = ((snapshot.get('encounter') or {}).get('item_followups') or {}).get(actor)
    return ticket if key and ticket and ticket.get('turn') == key else None


def prepare(db, actor, item, target, definition, attack):
    from .combat_effects import effect_snapshot
    from .dice_rolls import resolve_item_damage_formula, parse_formula
    from .spatial_grid import check_attack_range
    checked = check_attack_range(None, actor_character_id=actor, target_type=target['type'],
                                 target_id=target['id'], slot='ranged', max_range_m=9, connection=db)
    if checked.get('checked') and not checked.get('in_range', True):
        raise ValueError('Arremesso de Vibranium: alvo além de 9 m')
    formula = resolve_item_damage_formula({**definition, 'attack_slot': 'ranged'}, item)
    parsed = parse_formula(formula)
    modifier = parsed.modifier + int(attack.get('effect_flat_damage_bonus') or 0)
    damage = f'{parsed.count}d{parsed.sides}' + (f'{modifier:+d}' if modifier else '')
    ticket = followup(effect_snapshot(db), actor)
    other = ticket and ticket['first_target'] != _identity(db, target['type'], target['id'])
    contract = {'kind': 'vibranium', 'item_path': item['item_path'],
                'followup_of': ticket['source'] if other else None,
                'campaign_rule': '1d6 + FOR, 9 m; queda ao errar; retorno ao acertar',
                'protetor': any(str(definition.get(key) or '').strip().casefold()=='protetor' for key in ('specialization','class_name'))}
    totals=(definition.get('item_effects') or {}).get('totals') or {}
    item_bonus=sum(int(totals.get('attack_bonus:'+key,0)) for key in ('all','ranged',item['item_path']))
    effect_bonus=int(attack.get('effect_attack_bonus') or 0)
    base=attack.get('base_attack_bonus')
    if base is None:base=int(attack.get('attack_bonus') or 0)-int(attack.get('item_attack_bonus') or 0)-int(attack.get('mastery_attack_bonus') or 0)-effect_bonus
    original=next((a for a in definition.get('attacks',[]) if a.get('id')=='ranged'),{})
    mastery=int(original.get('mastery_attack_bonus') or 0) if original.get('weapon_item_path')==item['item_path'] else 0
    return {**attack, 'damage': damage, 'attack_bonus':int(base)+item_bonus+effect_bonus+mastery,
            'item_attack_bonus':item_bonus,'mastery_attack_bonus':mastery,
            'item_special': 'vibranium', 'item_special_contract': contract}


def validate(db, record, snapshot):
    spec = record['breakdown'].get('item_special') or {}
    if spec.get('kind') != 'vibranium': return
    row = db.execute('SELECT quantity,equipped FROM player_inventory WHERE profile_id=? AND item_path=?',
                     (record['actor_character_id'], spec['item_path'])).fetchone()
    if not row or row[0] < 1 or not row[1]: raise ValueError('Equipe o escudo antes de arremessar')
    if spec.get('followup_of'):
        ticket = followup(snapshot, record['actor_character_id'])
        if not ticket or ticket['source'] != spec['followup_of'] or ticket['first_target'] == _identity(db, record['target_type'], record['target_id']):
            raise ValueError('Ricochete indisponível: escolha outro alvo no mesmo turno')
    from .spatial_grid import check_attack_range
    check_attack_range(None, actor_character_id=record['actor_character_id'], target_type=record['target_type'],
                       target_id=record['target_id'], slot='ranged', max_range_m=9, connection=db)


def _drop(db, record, spec, now):
    """A native location pin and loot reward retain the original inventory identity."""
    from .inventory_conditions import read_condition
    owner = record['actor_character_id']
    item = db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?', (owner, spec['item_path'])).fetchone()
    if not item or item['quantity'] < 1: raise ValueError('Escudo indisponível')
    reward = {'id': 'dropped-shield', 'name': item['item_title'] or 'Escudo de Vibranium', 'kind': 'item',
              'quantity': 1, 'item_path': spec['item_path'], 'inventory_condition': read_condition(db, item['id']),
              'charges_current': item['charges_current'], 'charges_max': item['charges_max'],
              'description': 'Queda provisória na célula do alvo. Recuperação pelo espólio nativo; preserva referência e condição.'}
    pin = None
    if record['target_type'] == 'token':
        pin = db.execute('SELECT * FROM session_workspace_tokens WHERE id=?', (record['target_id'],)).fetchone()
    if pin is None:
        pin = db.execute('SELECT * FROM session_workspace_tokens WHERE character_id=? ORDER BY updated_at DESC LIMIT 1', (record['target_id'],)).fetchone()
    loot_id = 'loot:drop:' + uuid.uuid4().hex
    drop_id = 'item-drop:' + uuid.uuid4().hex
    from .monster_runtime import public_token
    visible = bool(pin and public_token(db,pin['id']))
    if pin:
        sheet = json.dumps({'item_drop': {'loot_id': loot_id}}, ensure_ascii=False)
        db.execute('''INSERT INTO session_workspace_tokens(id,map_id,token_type,name,visible_to_players,latitude,longitude,sheet_json,created_at,updated_at)
                      VALUES(?,?,?,?,?,?,?,?,?,?)''',
                   (drop_id, pin['map_id'], 'location', reward['name'] + ' — caído', int(visible), pin['latitude'], pin['longitude'], sheet, now, now))
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='session_workspace_entity_positions'").fetchone():
            position = db.execute('SELECT * FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?', (pin['map_id'], pin['id'])).fetchone()
            if position:
                db.execute('''INSERT INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y,footprint_w,footprint_h)
                              VALUES(?,?,?,?,1,1)''', (pin['map_id'], drop_id, position['cell_x'], position['cell_y']))
    db.execute('''INSERT INTO loot_resolutions(resolution_id,request_id,source_key,source_type,source_id,source_name,treasure_code,treasure_scope,roll_mode,rewards_json,rolls_json,status,created_at,revealed_at)
                  VALUES(?,?,?,'token',?,?,'item-drop','carried','digital',?,'[]',?,?,?)''',
               (loot_id, record['resolution_id'] + ':drop', record['resolution_id'] + ':drop', drop_id,
                reward['name'] + ' caído', json.dumps([reward], ensure_ascii=False), 'revealed' if visible else 'draft', now, now if visible else None))
    db.execute('UPDATE player_inventory SET quantity=quantity-1,equipped=0,updated_at=? WHERE id=?', (now, item['id']))
    return {'loot_resolution_id': loot_id, 'pin_id': drop_id if pin else None}


def confirmed(db, record, snapshot, now):
    spec = record['breakdown'].get('item_special') or {}
    if spec.get('kind') != 'vibranium': return None
    from .item_defense import intercepted_strikes
    from .battle_mode import turn_identity
    blocked = intercepted_strikes(record)
    hit = any(s['result'] == 'hit' and i not in blocked for i, s in enumerate(record['breakdown']['strikes']))
    encounter = snapshot.get('encounter') or {}
    grants = encounter.setdefault('item_followups', {})
    grants.pop(record['actor_character_id'], None)
    result = {'returned': hit, 'followup': False, 'label': 'Escudo retornou' if hit else 'Escudo caiu'}
    if not hit:
        result.update(_drop(db, record, spec, now))
    elif not spec.get('followup_of') and turn_identity(snapshot):
        # Canonical server definition captured on the native preview, never a client flag.
        if spec.get('protetor'):
            grants[record['actor_character_id']] = {'turn': turn_identity(snapshot), 'source': record['resolution_id'],
                'first_target': _identity(db, record['target_type'], record['target_id']), 'item_path': spec['item_path']}
            result['followup'] = True
    if encounter.get('active'):
        db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))
    return result


def restore_reward(db, reward, character_id, quantity, now):
    """Only internally created item drops may restore a canonical owned item."""
    from .inventory_conditions import init_schema, read_condition, save_condition
    path = reward['item_path']
    row = db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?', (character_id, path)).fetchone()
    condition = reward.get('inventory_condition')
    comparable = lambda value: {k: v for k, v in (value or {}).items() if k != 'version'}
    if row and row['quantity'] > 0 and (comparable(read_condition(db, row['id'])) != comparable(condition)
           or row['charges_current'] != reward.get('charges_current') or row['charges_max'] != reward.get('charges_max')):
        raise ValueError('Condição diferente: recupere o escudo em um inventário sem outro exemplar')
    db.execute('''INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,notes,charges_current,charges_max,updated_at)
                  VALUES(?,?,?,?,0,'Recuperado do mapa',?,?,?) ON CONFLICT(profile_id,item_path) DO UPDATE SET quantity=quantity+excluded.quantity,updated_at=excluded.updated_at''',
               (character_id, path, reward['name'], quantity, reward.get('charges_current'), reward.get('charges_max'), now))
    restored = db.execute('SELECT id FROM player_inventory WHERE profile_id=? AND item_path=?', (character_id, path)).fetchone()[0]
    init_schema(db)
    if condition: save_condition(db, restored, condition, now)
    else: db.execute('DELETE FROM inventory_item_conditions WHERE inventory_id=?', (restored,))
    if row and row['quantity'] == 0:
        db.execute('UPDATE player_inventory SET charges_current=?,charges_max=? WHERE id=?', (reward.get('charges_current'), reward.get('charges_max'), restored))
