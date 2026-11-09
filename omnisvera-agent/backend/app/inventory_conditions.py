"""Persistent conditions of native inventory instances, independent of rest/HP.

No catalogue/Vault edits. The one-to-one extension follows player_inventory IDs.
Only reviewed rule IDs lose enhancement; unrelated attribute rules stay intact.
"""
from copy import deepcopy
import json
import hashlib


def init_schema(db):
    db.execute('''CREATE TABLE IF NOT EXISTS inventory_item_conditions (
        inventory_id INTEGER PRIMARY KEY REFERENCES player_inventory(id) ON DELETE CASCADE,
        data_json TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL)''')
    # Legacy connections do not consistently enable SQLite foreign keys.
    db.execute('''CREATE TRIGGER IF NOT EXISTS inventory_condition_cleanup
        AFTER DELETE ON player_inventory BEGIN
        DELETE FROM inventory_item_conditions WHERE inventory_id=OLD.id; END''')


def read_condition(db,inventory_id):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='inventory_item_conditions'").fetchone():
        return None
    row=db.execute('SELECT data_json,version FROM inventory_item_conditions WHERE inventory_id=?',(inventory_id,)).fetchone()
    return {**json.loads(row[0]),'version':int(row[1])} if row else None


def save_condition(db,inventory_id,state,now):
    data={key:value for key,value in state.items() if key!='version'}
    db.execute('''INSERT INTO inventory_item_conditions(inventory_id,data_json,version,updated_at) VALUES(?,?,1,?)
        ON CONFLICT(inventory_id) DO UPDATE SET data_json=excluded.data_json,version=version+1,updated_at=excluded.updated_at''',
        (inventory_id,json.dumps(data,ensure_ascii=False),now))


def project_condition(item):
    from .magic_optics import project as project_optics
    item=project_optics(item)
    condition=item.get('_instance_condition')
    from .magic_weapon_forms import project
    item=project(item,condition)
    if not condition or condition.get('kind')!='rust':return item
    result=deepcopy(item)
    loss=max(0,int(condition.get('original_bonus',0))-int(condition.get('bonus_remaining',0)))
    selected=set(condition.get('enhancement_rule_ids') or [])
    for rule in result.get('effect_rules') or []:
        if rule.get('id') in selected:
            # Store original value in this derived rule to make repeated UI
            # normalization idempotent; never subtract twice on the same dict.
            base=rule.setdefault('_rust_original_value',int(rule.get('value') or 0))
            rule['value']=max(0,base-loss)
    result.setdefault('mechanics',{})['instance_condition']={
        'kind':'rust','enchantment_bonus':condition.get('bonus_remaining',0),
        'destroyed':bool(condition.get('destroyed')),'version':condition.get('version',1)}
    if condition.get('destroyed'):
        result.update(equipped=False,equipment_slot=None)
    return result


def combat_fingerprint(db,actor_id,target_type,target_id):
    """Snapshot relevant native loadouts for resolve/confirm stale protection.

The fingerprint does not contain credentials or notes. An attack preview made
before corrosion/equipment changes must not apply its old attack/AC numbers.
"""
    owners={str(actor_id),str(target_id)}
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='session_workspace_tokens'").fetchone():
        for identity in tuple(owners):
            row=db.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
            if row and row[0]:owners.add(str(row[0]))
    exists=db.execute("SELECT 1 FROM sqlite_master WHERE name='inventory_item_conditions'").fetchone()
    rows=[]
    for owner in sorted(owners):
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='player_inventory'").fetchone():break
        for item in db.execute('SELECT id,profile_id,item_path,quantity,equipped,equipment_slot FROM player_inventory WHERE profile_id=? AND equipped=1 AND quantity>0 ORDER BY id',(owner,)).fetchall():
            condition=read_condition(db,item[0]) if exists else None
            rows.append([*item,condition])
    return hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
