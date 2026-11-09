"""Reviewed equipment families, not execution of free-form item descriptions."""
import json
import uuid
from copy import deepcopy
from .magic_equipment import identity

BRACERS='item-magico-braceletes-de-armadura'
COLLAR='item-magico-colar-do-comerciante'
HELM='item-magico-elmo-da-visao-da-verdade'
RING='item-magico-anel-da-conviccao'
MENTAL_KINDS={'fear','charm','illusion','mind_control'}
SPECS={HELM:{'slot':'Cabeça','maximum':0,'source':'Old Dragon 1, p.146','trait':'true_sight'},
       RING:{'slot':'Acessório','maximum':6,'source':'Old Dragon 1, p.141','trait':'mental_ward'}}
SPECS['item-magico-fivela-das-irmas']={'slot':'Acessório','maximum':0,'source':'Old Dragon 1, p.146','trait':'campaign_phase_typed_reduction'}
SPECS['item-magico-medalhao-de-adaptacao']={'slot':'Acessório','maximum':0,'source':'Old Dragon 1, p.147','trait':'breathes_any_environment'}
SPECS['item-magico-botas-sem-pegadas']={'slot':'Pés','maximum':0,'source':'Old Dragon 1, pp.141–148','trait':'no_physical_tracks'}


def variants(parent):
    return [{**deepcopy(parent),'id':BRACERS+'-'+str(n),'name':'Braceletes de armadura +'+str(n),
        'source_parent_id':BRACERS,'preco_po':1000*n,'preco':str(1000*n)+' PO',
        'preco_origem':'campanha_regra_opcional_od1','pricing_source':'Regra opcional OD1 p.147, aprovada pelo Mestre: 1.000 PO por ponto.'}
        for n in range(1,5)]


def compile_item(item):
    key=item.get('id')
    if key==BRACERS:
        return {'catalog_id':key,'item_type':'reference','description':item.get('description',''),
            'damage_formula':None,'effects':[],'effect_rules':[],'usable':False,
            'mechanics':{'family_schema':1,'family':'magic_equipment','kind':'reference',
                'requires_variant':True,'equipment_slots':[],'approved_equipment_slots':[],'family_gaps':[]}}
    if key not in SPECS:return None
    spec=SPECS[key]
    return {'catalog_id':key,'item_type':'accessory','description':item.get('description',''),
        'damage_formula':None,'effects':[],'effect_rules':[],'usable':False,'thumbnail':item.get('image_path'),
        'mechanics':{'family_schema':1,'family':'magic_equipment','kind':'accessory','magical':True,
            'magic_passive_schema':1,'magic_passive_id':key,'passive_trait':spec['trait'],
            'equipment_slots':[spec['slot']],'approved_equipment_slots':[spec['slot']],
            'slot_limit':1,'charges_max':spec['maximum'],'consume_mode':'none','recharge':'none',
            'charge_unit':'gems' if key==RING else None,'source':spec['source'],'family_gaps':[]}}


def equipped(db,owner,key):
    if key not in SPECS or not owner:return None
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='player_inventory'").fetchone():return None
    spec=SPECS[key]
    rows=db.execute('SELECT id,item_path,quantity,charges_current FROM player_inventory WHERE profile_id=? '
        'AND equipped=1 AND quantity>0 AND equipment_slot=? ORDER BY id',(owner,spec['slot'])).fetchall()
    return next(({'id':r[0],'item_path':r[1],'quantity':r[2],'charges_current':r[3]} for r in rows
                 if identity({'item_path':r[1]})==key and (not spec['maximum'] or r[2]==1)),None)


def lifetime_inventory_ids(db,owner=None):
    """Rest must not trust stale recharge metadata for canonical lifetime items."""
    from .magic_absorption import ID as BROOCH
    query='SELECT id,item_path FROM player_inventory'
    rows=db.execute(query+' WHERE profile_id=?',(owner,)).fetchall() if owner else db.execute(query).fetchall()
    return [r[0] for r in rows if identity({'item_path':r[1]}) in {RING,BROOCH}]


def block_mental(db,victim,kind,now):
    if victim.get('type')!='character' or kind not in MENTAL_KINDS:return None
    row=equipped(db,victim['id'],RING)
    if not row:return None
    remaining=6 if row['charges_current'] is None else max(0,min(6,int(row['charges_current'])))
    if remaining<=0:return None
    remaining-=1
    db.execute('UPDATE player_inventory SET charges_current=?,charges_max=6,recharge=?,updated_at=? WHERE id=?',
        (remaining,'none',now,row['id']))
    result={'item_path':row['item_path'],'kind':kind,'remaining':remaining,'maximum':6,'negated':True}
    from .session_ledger import append_session_ledger_event
    append_session_ledger_event(db,source_type='mental_ward',source_id=uuid.uuid4().hex,event_kind='action',
        actor_id='system',actor_name='Anel da convicção',actor_role='system',character_id=victim['id'],
        title=f'Anel da convicção anulou um ataque mental · {remaining}/6 gemas restantes',detail=result,
        visibility='table',created_at=now)
    return result


def illusion_ac_ignored(db,observer,target_type,target_id):
    """Viewer-local optical AC; does not reveal hidden pins or alter their owners."""
    if target_type!='character' or not equipped(db,observer,HELM):return 0
    from .magic_optics import suppressed
    if suppressed(db,target_type,target_id):return 0
    state=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(target_id,)).fetchone()
    from .night_form import current_form
    if state and current_form(json.loads(state[0])):return 0
    rows=db.execute('SELECT item_path FROM player_inventory WHERE profile_id=? AND equipped=1 '
        'AND quantity>0 AND equipment_slot=?',(target_id,'Acessório')).fetchall()
    return 2*sum(identity({'item_path':row[0]})=='item-magico-manto-da-confusao' for row in rows)


def attribute_check_modifier(db,owner,attributes,attribute,*,index=None):
    """Same equipment summary as native sheet rolls, on caller's DB transaction."""
    from .item_registry import registry,resolve_item
    from .character_play import _equipped_effect_summary,_effect_total,attribute_modifier
    from .player_inventory import normalize_inventory_item_mechanics
    index=index or registry(db)
    inventory=[]
    for row in db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND equipped=1 AND quantity>0',(owner,)):
        owned=dict(row);entry=resolve_item(index,owned['item_path'])
        if entry:
            owned.update(effect_rules=entry['effect_rules'],mechanics=entry['mechanics'])
        inventory.append(normalize_inventory_item_mechanics(owned))
    summary=_equipped_effect_summary(inventory)
    base=next((value for key,value in attributes.items() if key.lower() in {attribute,'carisma' if attribute=='charisma' else attribute}),10)
    score=int(base)+_effect_total(summary,'attribute_bonus',attribute)
    return (attribute_modifier(score) or 0)+_effect_total(summary,'skill_bonus',attribute)
