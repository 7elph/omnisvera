"""Permanent presentation history, keyed to a transferred physical belt identity.

No changes to race, class, attributes, portraits or Vault. Equip transitions and
native character command receipts prevent retries from counting as another use.
"""
import json
import uuid

ID='item-magico-cinto-da-mudanca-de-sexo'


def compile_item(item):
    if item.get('id')!=ID:return None
    return {'catalog_id':ID,'item_type':'accessory','description':item.get('description',''),
        'damage_formula':None,'effects':[],'effect_rules':[],'usable':False,'thumbnail':item.get('image_path'),
        'mechanics':{'family_schema':1,'family':'magic_equipment','kind':'accessory','magical':True,
            'magic_appearance_schema':1,'magic_appearance_id':ID,'equipment_slots':['Cinto'],
            'approved_equipment_slots':['Cinto'],'slot_limit':1,'charges_max':0,'consume_mode':'none',
            'recharge':'none','family_gaps':[],'source':item.get('source')}}


def equipped_transition(db,owner,before,after,request_id,now):
    from .magic_equipment import identity
    if identity(after)!=ID or (before or {}).get('equipped') or not after.get('equipped'):return
    if after.get('quantity')!=1:raise ValueError('Individualize o cinto antes de equipá-lo')
    if not request_id:raise ValueError('Equipar o cinto exige uma chave idempotente')
    from .inventory_conditions import read_condition,save_condition
    row=db.execute('SELECT id FROM player_inventory WHERE profile_id=? AND item_path=?',(owner,after['item_path'])).fetchone()
    condition=read_condition(db,row[0]) or {}
    uid=condition.get('appearance_belt_uid')
    if not uid:
        uid=uuid.uuid4().hex;condition['appearance_belt_uid']=uid;save_condition(db,row[0],condition,now)
    row=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(owner,)).fetchone()
    state=json.loads(row[0]);history=state.setdefault('appearance_belts',{})
    count=history.get(uid,0)
    if type(count) is not int or not 0<=count<=2:raise ValueError('Histórico do cinto inconsistente')
    if count>=2:return
    count+=1;history[uid]=count
    state['appearance']={'source_id':ID,'phase':'changed' if count==1 else 'mixed','activation_count':count,
        'permanent':True,'label':'Alteração física permanente' if count==1 else 'Características físicas mistas permanentes'}
    db.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?',
        (json.dumps(state,ensure_ascii=False),now,owner))
