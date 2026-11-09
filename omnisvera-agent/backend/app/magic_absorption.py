"""OD1 p.145 Broche-escudo; exact native identity and lifetime capacity."""
import uuid
from .magic_equipment import identity

ID='item-magico-broche-escudo'
CAPACITY=101
SOURCE='Old Dragon 1 — Livro Básico Aprimorado, p.145'
CATALOG_ENTRY={'id':ID,'category':'item-magico','name':'Broche-escudo',
    'description':'Broche em forma de dragão: absorve até 101 pontos de dano de Mísseis Mágicos e se desintegra ao esgotar essa capacidade.',
    'source':SOURCE,'source_entry':'item-magico-botas-elficas','source_recovery':'Descrição agrupada na importação original; item separado após conferência no livro.',
    'alinhamento':'ordeiro','peso':'','preco':'','preco_po':None,'preco_origem':'não informado','negociavel':True}


def compile_item(item):
    if item.get('id')!=ID:return None
    return {'catalog_id':ID,'item_type':'accessory','description':item.get('description') or '',
        'effects':[],'effect_rules':[],'damage_formula':None,'usable':False,'thumbnail':item.get('image_path'),
        'mechanics':{'family_schema':1,'family':'magic_equipment','kind':'accessory','magical':True,
            'magic_absorption_schema':1,'magic_absorption_id':ID,'equipment_slots':['Acessório'],
            'approved_equipment_slots':['Acessório'],'slot_limit':1,'charges_max':CAPACITY,
            'consume_mode':'none','recharge':'none','charge_unit':'absorbed_damage','family_gaps':[],
            'source':SOURCE}}


def absorb(db,target_type,target_id,damage,context,now):
    """Called inside the native damage transaction, never while resolving a preview.

    Only canonical Mísseis Mágicos events qualify. Arbitrary names/prose and
    other magical damage do not. One individual, equipped brooch handles a hit.
    """
    if target_type!='character' or damage<=0 or not context or context.get('kind')!='spell' or context.get('spell_id')!='misseis-magicos':return None
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='player_inventory'").fetchone():return None
    rows=db.execute('SELECT id,item_path,charges_current FROM player_inventory WHERE profile_id=? '
                    'AND quantity=1 AND equipped=1 AND equipment_slot=? ORDER BY id',
                    (target_id,'Acessório')).fetchall()
    for row in rows:
        if identity({'item_path':row[1]})!=ID:continue
        capacity=CAPACITY if row[2] is None else max(0,min(CAPACITY,int(row[2])))
        unavoidable=max(0,min(damage,int(context.get('unavoidable_damage') or 0)))
        absorbed=min(capacity,damage-unavoidable)
        if absorbed<=0:continue
        remaining=capacity-absorbed;destroyed=remaining==0
        db.execute('UPDATE player_inventory SET charges_current=?,charges_max=?,recharge=?,updated_at=?,'
                   'quantity=CASE WHEN ? THEN 0 ELSE quantity END,equipped=CASE WHEN ? THEN 0 ELSE equipped END,'
                   'equipment_slot=CASE WHEN ? THEN NULL ELSE equipment_slot END WHERE id=?',
                   (remaining,CAPACITY,'none',now,destroyed,destroyed,destroyed,row[0]))
        result={'item_path':row[1],'absorbed':absorbed,'remaining':remaining,'maximum':CAPACITY,'destroyed':destroyed}
        from .session_ledger import append_session_ledger_event
        append_session_ledger_event(db,source_type='magic_item_absorption',source_id=uuid.uuid4().hex,
            event_kind='action',actor_id='system',actor_name='Broche-escudo',actor_role='system',character_id=target_id,
            title=f'Broche-escudo absorveu {absorbed} de dano · '+('desintegrou-se' if destroyed else f'{remaining}/101 restantes'),
            detail=result,visibility='table',created_at=now)
        return result
    return None
