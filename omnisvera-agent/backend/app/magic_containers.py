"""Containers are instance conditions of native inventory, not a second loadout.

Contents are server-created transfer receipts: carried quantity is removed, and
restoration uses grant_item's native condition/charge compatibility checks.
Creature occupancy is delegated to portable_hole. No arbitrary client metadata
or recursive containers. Catalog measurements
may use explicitly approved and labelled provisional family estimates.
"""
import json
import math
import re
import sqlite3
import uuid
from contextlib import closing
from copy import deepcopy

from .dice_rolls import roll_formula
from .inventory_conditions import init_schema,read_condition,save_condition

BAG='item-magico-sacola-magica'
HOLE='item-magico-buraco-portatil'
from .magic_item_rulebook import rules_for
_bag=rules_for(BAG)['parameters'];_hole=rules_for(HOLE)['parameters']
SPECS={BAG+'-ordeira':{'opening_cm':_bag['opening_diameter_cm'],'capacity_kg':_bag['orderly_capacity_kg'],'loss_percent':0},
       BAG+'-caotica':{'opening_cm':_bag['opening_diameter_cm'],'capacity_kg':None,'loss_percent':_bag['chaotic_loss_percent']},
       HOLE:{'opening_cm':100*_hole['diameter_m'],'capacity_kg':None,'loss_percent':0,
             'capacity_m3':math.pi*(_hole['diameter_m']/2)**2*_hole['depth_m'],'depth_cm':100*_hole['depth_m']}}


def append_session_ledger_event(*args,**kwargs):
    from .session_ledger import append_session_ledger_event as append
    return append(*args,**kwargs)


def variants(parent):
    return [{**deepcopy(parent),'id':BAG+'-'+key,'name':'Sacola mágica '+('caótica' if key=='caotica' else 'ordeira'),
        'source_parent_id':BAG} for key in ('ordeira','caotica')]


def compile_item(item):
    key=item.get('id')
    if key not in SPECS and key!=BAG:return None
    spec=SPECS.get(key,{})
    return {'catalog_id':key,'item_type':'container','description':item.get('description',''),
        'damage_formula':None,'effects':[],'effect_rules':[],'usable':False,'thumbnail':item.get('image_path'),
        'mechanics':{'family_schema':1,'family':'magic_equipment','kind':'container','magical':True,
            'magic_container_schema':1,'magic_container_id':key,'requires_variant':key==BAG,
            'equipment_slots':[],'approved_equipment_slots':[],'consume_mode':'none','charges_max':0,
            'recharge':'none','source':item.get('source'),'family_gaps':[],**spec}}


def _authorized(owner,actor,role):
    if role not in {'gm','player'} or role!='gm' and owner!=actor:
        raise PermissionError('Recipiente disponível somente ao portador e ao Mestre')


def _owned(db,owner,path):
    from .item_registry import registry,resolve_item
    index=registry(db);entry=resolve_item(index,path)
    key=(entry or {}).get('mechanics',{}).get('magic_container_id')
    row=db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?',(owner,path)).fetchone()
    if not row or row['quantity']!=1 or key not in SPECS:
        raise ValueError('Escolha uma única unidade de um recipiente com variante definida')
    condition=read_condition(db,row['id']) or {}
    return row,entry,index,condition,SPECS[key]


def _snapshot(condition):
    value=deepcopy(condition.get('magic_container') or {'open':False,'contents':[]})
    if value.get('schema_version',1)!=1:raise ValueError('Versão do recipiente não suportada')
    value['schema_version']=1
    if not isinstance(value.get('contents'),list):raise ValueError('Conteúdo do recipiente inconsistente')
    return value


def inspect(path,*,owner,actor,role,item_path):
    _authorized(owner,actor,role)
    if not isinstance(item_path,str) or not 1<=len(item_path)<=1000:raise ValueError('Recipiente inválido')
    with closing(sqlite3.connect(path)) as db:
        db.row_factory=sqlite3.Row
        row,entry,index,condition,spec=_owned(db,owner,item_path)
        state=_snapshot(condition)
        contents=[{k:e.get(k) for k in ('id','item_path','name','quantity','unit_weight_kg',
                                       'charges_current','charges_max')} for e in state['contents']]
        occupants=state.get('occupants',[])
        if role!='gm':
            from .monster_runtime import public_token
            occupants=[o for o in occupants if (o['type']=='character' and o['id']==actor) or public_token(db,o['token_id'])]
        return {'item_path':item_path,'version':condition.get('version',0),'open':bool(state['open']),
            'contents':contents,'weight_kg':round(sum(e['quantity']*e['unit_weight_kg'] for e in contents),6),
            'volume_m3':sum(e['quantity']*e['unit_volume_m3'] for e in state['contents']) if 'capacity_m3' in spec else None,
            **spec,'creature_occupants_supported':entry['mechanics']['magic_container_id']==HOLE,
            'portal_id':state.get('portal_id'),'occupants':occupants,'nested_containers_supported':False}


def _measure(entry):
    m=entry.get('mechanics') or {}
    weight=m.get('weight_kg')
    if weight is None:
        raw=m.get('weight')
        match=re.fullmatch(r'\s*(\d+(?:[.,]\d+)?)\s*(kg|g)\s*',str(raw or ''),re.I)
        if match:weight=float(match[1].replace(',','.'))/(1000 if match[2].lower()=='g' else 1)
    diameter=m.get('container_entry_cm')
    if isinstance(weight,bool) or not isinstance(weight,(float,int)) or not math.isfinite(weight) or weight<0:
        raise ValueError('Peso do item não cadastrado; não será presumido como zero')
    if isinstance(diameter,bool) or not isinstance(diameter,(float,int)) or not math.isfinite(diameter) or diameter<=0:
        raise ValueError('Dimensões de entrada do item não cadastradas; não será presumido que cabe')
    return float(weight),float(diameter)


def command(path,*,owner,actor,role,request_id,payload):
    _authorized(owner,actor,role)
    operation=payload.get('operation')
    keys={'item_path','operation','expected_version'}
    if operation=='store':keys|={'source_path','quantity'}
    elif operation=='take':keys|={'entry_id','quantity'}
    elif operation not in {'open','close'}:raise ValueError('Operação de recipiente inválida')
    if set(payload)!=keys or any(not isinstance(payload[k],str) or not 1<=len(payload[k])<=1000
                              for k in ('item_path',*(['source_path'] if operation=='store' else ['entry_id'] if operation=='take' else []))):
        raise ValueError('Parâmetros de recipiente inválidos')
    if type(payload['expected_version']) is not int or payload['expected_version']<0:
        raise ValueError('Versão do recipiente inválida')
    amount=payload.get('quantity',1)
    if type(amount) is not int or not 1<=amount<=99:raise ValueError('Quantidade deve ficar entre 1 e 99')
    if not isinstance(request_id,str) or not 1<=len(request_id)<=120:raise ValueError('Informe uma chave idempotente')
    from .combat_effects import init_effects,effect_snapshot
    from .character_play import _now,_write_event
    from .battle_mode import require_actor_alive,require_battle_turn
    from .night_form import require_humanoid
    from .monster_conditions import assert_can_act
    init_effects(path)
    fingerprint=json.dumps(['magic_container',owner,actor,role,payload],sort_keys=True)
    with closing(sqlite3.connect(path,timeout=30)) as db,db:
        db.row_factory=sqlite3.Row;db.execute('BEGIN IMMEDIATE');init_schema(db)
        receipt=db.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?',(request_id,)).fetchone()
        if receipt:
            if receipt[0]!=fingerprint:raise ValueError('Requisição pertence a outra operação')
            return json.loads(receipt[1])
        row,entry,index,condition,spec=_owned(db,owner,payload['item_path'])
        if condition.get('version',0)!=payload['expected_version']:raise ValueError('O recipiente mudou; atualize seu conteúdo')
        snapshot=effect_snapshot(db)
        administrative_open=(role=='gm' and operation in {'open','close'} and
            entry['mechanics']['magic_container_id']==HOLE and not (snapshot.get('encounter') or {}).get('active'))
        if not administrative_open:
            require_actor_alive(db,owner);require_humanoid(db,owner,'manipular recipientes');assert_can_act(db,owner,noncombat=True)
        if role=='player' and (snapshot.get('encounter') or {}).get('active') and (snapshot['encounter'].get('battle_mode')):
            require_battle_turn(db,snapshot,owner)
        state=_snapshot(condition);now=_now();lost=0;rolls=[]
        before=deepcopy(state)
        if operation in {'open','close'}:
            state['open']=operation=='open'
            if entry['mechanics']['magic_container_id']==HOLE:
                from .portable_hole import sync_open
                sync_open(db,row,state,now)
                db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
            title='Abriu' if state['open'] else 'Fechou'
        else:
            if not state['open']:raise ValueError('Abra o recipiente antes de mover itens')
            from .item_registry import resolve_item
            if operation=='store':
                source=resolve_item(index,payload['source_path'])
                if not source or source.get('catalog_entry_kind')!='item' or source.get('trade_group')=='services':
                    raise ValueError('Escolha um item físico do inventário')
                if source.get('trade_group')=='livestock' or str(source.get('category','')).casefold() in {'hospedagem','servico-magico','propriedades','creature','monster','npc','animal','mount','criatura','monstro'}:
                    raise ValueError('Recipientes não aceitam criaturas, propriedades ou serviços')
                if (source.get('mechanics') or {}).get('magic_container_schema') or payload['source_path']==payload['item_path']:
                    raise ValueError('Não é permitido guardar outro recipiente mágico')
                held=db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?',(owner,payload['source_path'])).fetchone()
                if not held or held['quantity']<amount:raise ValueError('Quantidade indisponível no inventário')
                if held['equipped']:raise ValueError('Guarde o item equipado antes de colocá-lo no recipiente')
                mechanics=source.get('mechanics') or {}
                individual=mechanics.get('magic_appearance_schema') or mechanics.get('magic_activation_schema') or mechanics.get('magic_absorption_schema') or (mechanics.get('magic_passive_schema') and mechanics.get('charges_max'))
                if individual and held['quantity']!=1:raise ValueError('Individualize as cópias mágicas antes de guardá-las')
                if held['quantity']>1 and held['charges_max'] and (mechanics.get('family')!='ammunition' or held['charges_current'] not in (None,held['charges_max'])):
                    raise ValueError('Individualize a pilha com cargas antes de guardá-la; os contadores não serão fundidos')
                original=read_condition(db,held['id'])
                if (held['charges_max'] or original) and amount!=held['quantity']:
                    raise ValueError('Mova a instância inteira para preservar suas cargas e condições')
                if original and original.get('destroyed'):raise ValueError('Item destruído não pode ser guardado')
                from .magic_weapon_forms import project as project_form
                source=project_form(source,original)
                mechanics=source.get('mechanics') or {}
                weight,diameter=_measure(source)
                if diameter>spec['opening_cm']:raise ValueError('O item não passa pela abertura do recipiente')
                volume=None
                if entry['mechanics']['magic_container_id']==HOLE:
                    volume=mechanics.get('storage_volume_m3');length=mechanics.get('container_packed_length_cm')
                    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in (volume,length)):
                        raise ValueError('Volume e comprimento acondicionado não cadastrados para o Buraco Portátil')
                    if length>spec['depth_cm']:raise ValueError('O comprimento acondicionado ultrapassa a profundidade do Buraco Portátil')
                    if sum(e.get('unit_volume_m3',0)*e['quantity'] for e in state['contents'])+volume*amount>spec['capacity_m3']:
                        raise ValueError('O conteúdo ultrapassa o volume do Buraco Portátil')
                total=sum(e['unit_weight_kg']*e['quantity'] for e in state['contents'])
                if spec['capacity_kg'] is not None and total+weight*amount>spec['capacity_kg']:
                    raise ValueError('O conteúdo ultrapassa a capacidade do recipiente')
                if len(state['contents'])>=100:raise ValueError('Divida a organização do recipiente antes de acrescentar outro registro')
                if spec['loss_percent']:
                    for _ in range(amount):
                        roll=roll_formula('1d100');n=roll['total']
                        if type(n) is not int or not 1<=n<=100:raise ValueError('Resultado percentual inválido')
                        rolls.append(roll);lost+=int(n<=spec['loss_percent'])
                if amount-lost:
                    state['contents'].append({'id':uuid.uuid4().hex,'item_path':held['item_path'],
                        'name':held['item_title'],'quantity':amount-lost,'unit_weight_kg':weight,'unit_volume_m3':volume,
                        'physical_metadata':deepcopy(mechanics.get('physical_metadata')),
                        'unit_entry_cm':diameter,'unit_packed_length_cm':mechanics.get('container_packed_length_cm'),
                        'charges_current':held['charges_current'],'charges_max':held['charges_max'],
                        'recharge':held['recharge'],'inventory_condition':deepcopy(original)})
                db.execute('UPDATE player_inventory SET quantity=quantity-?,updated_at=? WHERE id=?',(amount,now,held['id']))
                title='Guardou';item_name=held['item_title']
            else:
                stored=next((e for e in state['contents'] if e['id']==payload['entry_id']),None)
                if not stored or stored['quantity']<amount:raise ValueError('Quantidade indisponível no recipiente')
                source=resolve_item(index,stored['item_path'])
                if not source:raise ValueError('Fonte do item indisponível; o conteúdo foi preservado')
                if (stored.get('charges_max') or stored.get('inventory_condition')) and amount!=stored['quantity']:
                    raise ValueError('Retire a instância inteira para preservar suas cargas e condições')
                from .item_transfer import grant_item
                grant_item(db,source,owner,amount,now,origin='Retirado de recipiente mágico',instance=stored)
                stored['quantity']-=amount
                state['contents']=[e for e in state['contents'] if e['quantity']>0]
                title='Retirou';item_name=stored['name']
        after={**condition,'magic_container':state};save_condition(db,row['id'],after,now)
        db.execute('UPDATE player_inventory SET updated_at=? WHERE id=?',(now,row['id']))
        text=f"{title} {row['item_title']}" if operation in {'open','close'} else f"{title} {amount} × {item_name} · {row['item_title']}"+(f' · {lost} perdido(s)' if lost else '')
        event=_write_event(db,character_id=owner,actor_id=actor,actor_role=role,event_type='container',
            field='inventory',before={'open':before['open'],'entries':len(before['contents'])},
            after={'open':state['open'],'entries':len(state['contents']),'lost':lost},reason=text,session_id=None)
        result={'event_id':event,'lost':lost,'intent':payload,'rolls':rolls}
        append_session_ledger_event(db,source_type='magic_container',source_id=request_id,event_kind='action',
            actor_id=actor,actor_name=owner,actor_role=role,character_id=owner,title=text,
            detail={'item_path':payload['item_path'],'operation':operation,'quantity':amount,'lost':lost,'rolls':rolls},
            visibility='owner',created_at=now)
        db.execute('INSERT INTO combat_effect_commands VALUES(?,?,?)',(request_id,fingerprint,json.dumps(result)))
        return result


def recharge_contents(db,owner,now):
    """Only the GM's full rest, with the same lifetime-item exclusions as carried gear."""
    from .magic_equipment import identity
    from .magic_absorption import ID as BROOCH
    from .magic_passives import RING
    for row in db.execute('SELECT id FROM player_inventory WHERE profile_id=? AND quantity>0',(owner,)).fetchall():
        condition=read_condition(db,row[0]) or {};state=condition.get('magic_container')
        if not state:continue
        changed=False
        for entry in state['contents']:
            if entry.get('recharge')=='inn_rest' and entry.get('charges_max') is not None and identity(entry) not in {BROOCH,RING}:
                entry['charges_current']=entry['charges_max'];changed=True
        if changed:
            save_condition(db,row[0],condition,now)
            db.execute('UPDATE player_inventory SET updated_at=? WHERE id=?',(now,row[0]))
