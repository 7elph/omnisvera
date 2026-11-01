"""Atomic grants into native player_inventory; never infer rules from prose."""
def resolve_reward(index, reward):
    from .item_registry import key, resolve_item
    identity = reward.get('item_path') or reward.get('catalog_id')
    if identity:
        item = resolve_item(index, str(identity))
        if not item or item['source_kind'] == 'held' or item['catalog_entry_kind'] != 'item' or item.get('trade_group') == 'services':
            raise ValueError('Identidade de recompensa inexistente ou não física')
        if reward.get('item_path') and reward.get('catalog_id'):
            other=resolve_item(index,str(reward['catalog_id']))
            if not other or other['item_path'] != item['item_path']: raise ValueError('Referências de item conflitantes')
        return (None, 'unidentified') if reward.get('requires_identification') else (item, 'explicit')
    if reward.get('requires_identification'): return None, 'unidentified'
    matches = {item['item_path']:item for item in index['entries'].values()
        if item['source_kind'] != 'held' and item['catalog_entry_kind'] == 'item' and item.get('trade_group') != 'services'
        and key(item['name']) == key(reward['name'])}
    if len(matches) == 1: return next(iter(matches.values())), 'matched'
    return None, 'ambiguous' if matches else 'narrative'


def grant_item(db, item, character_id, quantity, now, *, origin, instance=None):
    """Caller owns BEGIN IMMEDIATE and commits grant, receipt and ledger together.

    The native unique(profile_id,item_path) cannot hold incompatible copies.
    Reject that merge rather than create another inventory or discard properties.
    """
    from .inventory_conditions import init_schema, read_condition, save_condition
    instance = instance or {}
    if type(quantity) is not int or quantity < 1: raise ValueError('Quantidade inválida')
    charges = [instance.get('charges_current'), instance.get('charges_max')]
    if any(value is not None and (type(value) is not int or value < 0) for value in charges):
        raise ValueError('Cargas inválidas')
    if (charges[0] is None) != (charges[1] is None) or (charges[0] is not None and charges[0] > charges[1]):
        raise ValueError('Informe as cargas atuais e máximas válidas')
    condition = instance.get('inventory_condition') or None
    recharge = instance.get('recharge')
    row = db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?',
        (character_id, item['item_path'])).fetchone()
    mechanics=item.get('mechanics') or {}
    if charges[1] is not None and mechanics.get('family')=='ammunition' and charges[1]!=mechanics.get('pack_size'):
        raise ValueError('Cargas incompatíveis com o tamanho do pacote de munição')
    # Native stacks represent full remaining copies plus one partially used copy.
    # Two partial copies cannot share this counter without inventing charges.
    if charges[0] is not None and charges[0]<charges[1] and (quantity>1 or (row and row['quantity']>0)):
        raise ValueError('Exemplares parcialmente usados precisam de revisão individual; não podem ser empilhados')
    comparable = lambda value: {k:v for k,v in (value or {}).items() if k != 'version'}
    if row and row['quantity']>0 and mechanics.get('family')=='ammunition':
        # One open pack plus full reserves is already the native ammo model.
        # Replenishing full packs must preserve the open pack's counter.
        pack=mechanics['pack_size']
        fresh=charges[0] is None or charges==[pack,pack]
        same_condition=comparable(read_condition(db,row['id']))==comparable(condition)
        if fresh and same_condition and recharge in (None,'none') and row['recharge'] in (None,'none'):
            if row['charges_max'] not in (None,pack) or (row['charges_current'] is not None and not 0<=row['charges_current']<=pack):
                raise ValueError('Munição existente inconsistente; revise o pacote antes de repor')
            charges=[row['charges_current'],row['charges_max']]
            recharge=row['recharge']
    if row and row['quantity'] > 0 and (row['charges_current'] != charges[0] or row['charges_max'] != charges[1]
            or row['recharge'] != recharge or comparable(read_condition(db,row['id'])) != comparable(condition)):
        raise ValueError('Exemplares com condição/cargas diferentes: escolha outro destinatário ou revise a instância com o Mestre')
    before = row['quantity'] if row else 0
    if row and before > 0:
        db.execute('UPDATE player_inventory SET quantity=quantity+?,updated_at=? WHERE id=?',(quantity,now,row['id']))
    else:
        db.execute('''INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,notes,
            charges_current,charges_max,recharge,updated_at) VALUES(?,?,?,?,0,?,?,?,?,?)
            ON CONFLICT(profile_id,item_path) DO UPDATE SET item_title=excluded.item_title,quantity=excluded.quantity,
            equipped=0,equipment_slot=NULL,notes=excluded.notes,charges_current=excluded.charges_current,
            charges_max=excluded.charges_max,recharge=excluded.recharge,updated_at=excluded.updated_at''',
            (character_id,item['item_path'],item['name'],quantity,origin,*charges,recharge,now))
        inventory_id=db.execute('SELECT id FROM player_inventory WHERE profile_id=? AND item_path=?',
            (character_id,item['item_path'])).fetchone()[0]
        init_schema(db)
        if condition: save_condition(db,inventory_id,condition,now)
        else: db.execute('DELETE FROM inventory_item_conditions WHERE inventory_id=?',(inventory_id,))
    return {'item_path':item['item_path'],'before':before,'after':before+quantity,
        'catalog_id':item['id'],'source_kind':item['source_kind'],'item_revision':item['revision'],
        'charges_current':charges[0],'charges_max':charges[1],'recharge':recharge,'inventory_condition':condition}
