"""Tower shield: declared protected side, source 25%, native confirmed strikes."""
import json
from .dice_rolls import roll_formula

TOWER_ID='kit-basico-escudo-torre-20-kg-30-po'


def has_tower(db,kind,identity):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='player_inventory'").fetchone():return False
    if kind=='token':
        row=db.execute('SELECT character_id,sheet_json FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
        if not row:return False
        if row[0]:identity=row[0]
        else:
            return any(i.get('equipped') and int(i.get('quantity',1) or 0)>0 and (i.get('mechanics') or {}).get('special_defense')=='tower' for i in (json.loads(row[1] or '{}').get('inventory') or []))
    item=db.execute('SELECT id FROM player_inventory WHERE profile_id=? AND quantity>0 AND equipped=1 AND item_path=?',(identity,'compendium:'+TOWER_ID)).fetchone()
    if not item:return False
    from .inventory_conditions import read_condition
    return not bool((read_condition(db,item[0]) or {}).get('destroyed'))


def intercepted_strikes(record):
    reflected={r['strike'] for r in record['breakdown'].get('reflection_result',{}).get('rolls',[]) if r.get('intercepted')}
    blocked={r['strike'] for r in record['breakdown'].get('item_defense_result',{}).get('rolls',[]) if r.get('blocked')}
    return reflected|blocked


def requires_declaration(db,kind,identity):
    if has_tower(db,kind,identity):return True
    if kind=='token':
        row=db.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
        identity=row[0] if row else None
    if not identity or identity=='dorn7' or not has_tower(db,'character','dorn7'):return False
    from .dorn_protocols import protects_ally
    for row in db.execute("SELECT data_json FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.protocol')='guard'"):
        guard=json.loads(row[0])
        if (guard.get('area_guard') and protects_ally(db,guard,identity)) or guard.get('ally_id')==identity:return True
    return False


def apply_tower(record):
    contract=record['breakdown'].get('tower_shield')
    if not contract:return None
    result={'protected_side':contract['protected_side'],'blocked_damage':0,'rolls':[]}
    if not contract['protected_side']:return result
    reflected=intercepted_strikes(record)
    for index,strike in enumerate(record['breakdown']['strikes']):
        if strike['result']!='hit' or strike.get('unavoidable') or index in reflected:continue
        rolled=roll_formula('1d4');blocked=int(rolled['total'])==1
        result['rolls'].append({'strike':index,'die':int(rolled['total']),'blocked':blocked})
        if blocked:
            amount=int(strike['damage_total']);result['blocked_damage']+=amount
            strike.update(damage_before_tower=amount,damage_total=0,blocked_by_tower=True)
            record['damage_total']=max(0,record['damage_total']-amount)
    return result
