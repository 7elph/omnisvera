"""Explicit, audited recovery of old coin loot stored as inventory.

Never runs at startup. Requires original distribution evidence, exact remaining
quantity and current wallet; does not interpret gems, purses or magic relics.
"""
import json
from contextlib import closing

from .merchant import _connect, _now, _character_state, COIN_FIELDS, purse_copper
from .player_inventory import currency_item_field
from .session_ledger import append_session_ledger_event


def recover_coin_loot(path, *, profile_id, item_path, quantity, expected_purse,
                      restored_purse=None):
    key = f'{profile_id}:{item_path}'
    with closing(_connect(path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        previous = db.execute("SELECT detail_json FROM session_ledger WHERE source_type='currency_recovery' AND source_id=? AND voided_at IS NULL", (key,)).fetchone()
        if previous:
            return {**json.loads(previous[0]), 'replayed': True}
        owned = db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?', (profile_id,item_path)).fetchone()
        if not owned or owned['quantity'] != quantity or quantity <= 0:
            raise ValueError('Quantidade mudou; recuperação cancelada')
        if not item_path.startswith('session-item:'):
            raise ValueError('Recuperação exige o registro original do saque')
        item_id = int(item_path.split(':')[1])
        item = db.execute('SELECT * FROM session_custom_items WHERE id=?', (item_id,)).fetchone()
        field = currency_item_field({'name':item['name'], 'item_type':item['item_type']}) if item else None
        if not field:
            raise ValueError('Item não é uma denominação de moeda conhecida')
        evidence = None
        for row in db.execute("SELECT id,detail_json FROM session_ledger WHERE source_type='loot_distribution' AND voided_at IS NULL"):
            detail = json.loads(row['detail_json'] or '{}')
            ids = [rid for rid,iid in detail.get('created_item_ids',{}).items() if iid==item_id]
            allocated = sum(int(a['quantity']) for a in detail.get('allocations',[]) if a.get('reward_id') in ids and a.get('character_id')==profile_id)
            if ids and allocated == quantity:
                evidence = row['id']
                break
        if evidence is None:
            raise ValueError('Distribuição original não comprovada; recuperação cancelada')
        state = _character_state(db, profile_id)
        before = {k:int(state.get(k) or 0) for k in COIN_FIELDS}
        if before != expected_purse:
            raise ValueError('Saldo mudou; recuperação cancelada')
        base = dict(restored_purse or before)
        if set(base) != set(COIN_FIELDS) or any(type(v)!=int or v<0 for v in base.values()) or purse_copper(base)!=purse_copper(before):
            raise ValueError('Restauração deve preservar o valor integral da bolsa')
        after = {**base, field:base[field]+quantity}
        state.update(after)
        now = _now()
        db.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?', (json.dumps(state,ensure_ascii=False),now,profile_id))
        db.execute('UPDATE player_inventory SET quantity=0,equipped=0,equipment_slot=NULL,updated_at=? WHERE id=?', (now,owned['id']))
        result = dict(item_path=item_path, quantity=quantity, currency_field=field,
                      before=before, after=after, distribution_ledger_id=evidence)
        append_session_ledger_event(db, source_type='currency_recovery',source_id=key,event_kind='treasure',
            actor_id='master',actor_name='Mestre',actor_role='gm',character_id=profile_id,
            title=f'{profile_id}: {quantity}× {item["name"]} do saque transferidos para a bolsa',
            detail=result,visibility='owner',created_at=now)
        return result
