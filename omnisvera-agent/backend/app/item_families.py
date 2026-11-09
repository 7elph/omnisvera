"""Catalog-to-native adapters. Numeric source fields only; no prose execution.

OD1 Aprimorada pp.54-55,58: base weapon and armor tables checked locally.
Expansion rows retain their existing attribution and explicit limitations.
"""
from copy import deepcopy
import re

BODY={'Armadura acolchoada':(1,0,None),'Armadura de couro':(2,0,6),
      'Armadura de couro batido':(3,0,6),'Armadura de placas':(6,2,3),
      'Armadura completa':(8,3,1),'Cota de malha':(4,1,2)}
SHIELDS={'Broquel':1,'Escudo de madeira':1,'Escudo de aço':2,'Escudo torre':0}
USE_KINDS={'heal_hp','restore_resource','temporary_hp','add_condition'}
AMMO={'arma-distancia-dardo-x20':('bolt',20),'arma-distancia-dardo-x20-2':('bolt',20),
      'arma-distancia-dardo-zarabatana-x20':('dart',20),
      'arma-distancia-dardo-x20-expansao':('dart',20),
      'arma-distancia-flecha-x20':('arrow',20),'arma-distancia-flecha-x20-2':('arrow',20),
      'arma-distancia-flecha-improvisada':('arrow',1)}
LAUNCHERS={'arma-distancia-arco-curto':'arrow','arma-distancia-arco-longo':'arrow',
           'arma-distancia-zarabatana':'dart',
           'arma-distancia-besta-de-mao':'bolt','arma-distancia-besta':'bolt'}
from .item_darts import SPECS as DART_SPECS
AMMO.update({identity: ('dart', 10) for identity in DART_SPECS})

def rule(identity,kind,value,target=''):
    return {'id':identity,'trigger':'while_equipped','kind':kind,'value':value,
            'target':target,'stacking':'stack','condition':'','label':'Equipamento · tabela de origem'}

def descriptor(item):
    from .item_dimensions import enrich, METADATA_FIELDS
    result = _descriptor(item)
    prepared = enrich({**item, 'mechanics': {**(item.get('mechanics') or {}), **(result.get('mechanics') or {})}})
    physical = {key: value for key, value in (prepared.get('mechanics') or {}).items() if key in METADATA_FIELDS}
    if physical:
        result['mechanics'] = {**(result.get('mechanics') or {}), **physical}
    return result


def _descriptor(item):
    from .magic_appearance import compile_item as compile_appearance
    appearance=compile_appearance(item)
    if appearance is not None:return appearance
    from .magic_containers import compile_item as compile_container
    container=compile_container(item)
    if container is not None:return container
    from .magic_weapon_forms import compile_item as compile_forms
    forms=compile_forms(item)
    if forms is not None:return forms
    from .equipment_checks import compile_item as compile_check
    check=compile_check(item)
    if check:return check
    from .magic_passives import compile_item as compile_passive
    passive=compile_passive(item)
    if passive is not None:return passive
    from .magic_absorption import compile_item as compile_absorption
    absorption=compile_absorption(item)
    if absorption is not None:return absorption
    from .magic_item_uses import compile_item as compile_activation
    activation=compile_activation(item)
    if activation is not None:return activation
    from .magic_equipment import compile_item
    magic=compile_item(item)
    if magic is not None:return magic
    category=item.get('category','');name=item['name'];text=item.get('description','')
    mechanics=deepcopy(item.get('mechanics') or {});rules=deepcopy(item.get('effect_rules') or [])
    result={'catalog_id':item['id'],'item_type':category,'description':text,'damage_formula':None,
            'effects':list(item.get('effects') or []),'effect_rules':rules,'mechanics':mechanics,
            'usable':bool(item.get('usable')),'thumbnail':item.get('image_path')}
    if item.get('native_item_path'):return {**item,**result}
    if mechanics.get('family_schema')==1:
        result.update(item_type=mechanics['kind'],damage_formula=None if mechanics['family']=='ammunition' else mechanics.get('damage_formula'))
        return result
    family=None;gaps=[]
    if category in {'arma-corpo','arma-distancia'}:
        family='weapon';damage=re.sub(r'\s+','',str(item.get('dano') or '')).lower()
        formula=damage if re.fullmatch(r'\d{1,2}d\d{1,4}(?:[+-]\d+)?',damage) else None
        # Expansão de Itens, Madu: the prose explicitly specifies 1d8.
        if item['id']=='arma-corpo-madu':formula='1d8'
        if item['id']=='arma-corpo-bagh-naja':
            formula='1d6'
            mechanics['campaign_rule']='Bagh Naja provisória (01/11/2026): 1d6 base, sem ataque extra; tabela original 1d6/1d4 preservada'
        thrown=re.search(r'Arremesso\s*(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)',text,re.I)
        reach=re.search(r'Alcance\s+(\d+(?:[.,]\d+)?)',text,re.I)
        critical=re.search(r'(?:(1[89])\s*[-–/]\s*20\s*)?[xX](\d)\b',text)
        modes=['melee'] if category=='arma-corpo' else ['ranged']
        if thrown:modes.append('ranged')
        slots=[{'melee':'Corpo a corpo','ranged':'À distância'}[mode] for mode in modes]
        mechanics.update(kind='weapon',damage_formula=formula,attack_modes=modes,
                         approved_equipment_slots=slots,equipment_slots=slots,
                         critical_threshold=int(critical[1]) if critical and critical[1] else 20,
                         critical_multiplier=int(critical[2]) if critical else 2)
        if item['id'] in {'kit-explorador-rede','arma-corpo-garrote'}:
            mechanics.update(special_attack='net' if item['id']=='kit-explorador-rede' else 'garrote',effect_only=True)
        if reach:mechanics['melee_reach_m']=float(reach[1].replace(',','.'))
        if thrown:mechanics.update(range_m=float(thrown[2].replace(',','.')),short_range_m=float(thrown[1].replace(',','.')))
        if category=='arma-distancia':
            distance=(re.search(r'\bAlcance\s+(?:Arremesso\s*)?(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)',text,re.I)
                      or re.search(r'^\s*(?:[–—-]\s*)?(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)',text))
            if distance:mechanics.update(range_m=float(distance[2].replace(',','.')),short_range_m=float(distance[1].replace(',','.')))
            if not formula:gaps.append('ammunition')
        if not formula and 'ammunition' not in gaps and item['id'] not in {'kit-explorador-rede','arma-corpo-garrote'}:gaps.append('special_effect')
        # Preserve combined damage types without choosing one silently.
        types=[v for k,v in [('Co.','slashing'),('Im.','bludgeoning'),('Pe.','piercing')] if k in text]
        if len(types)==1:mechanics['damage_type']=types[0]
        elif types:
            mechanics['damage_types']=types;gaps.append('damage_type_choice')
        if item['id']=='arma-corpo-madu':rules.append(rule('catalog:'+item['id']+':defense','armor_class_bonus',1))
        if 'Especial' in text and item['id'] not in {'arma-corpo-madu','kit-explorador-rede','arma-corpo-garrote'} and 'special_effect' not in gaps:gaps.append('special_effect')
        result.update(item_type='weapon',damage_formula=formula)
        if item['id'] in AMMO:
            kind,pack=AMMO[item['id']];family='ammunition'
            mechanics.update(kind='ammunition',ammunition_kind=kind,pack_size=pack,charges_max=pack,equipment_slots=[],approved_equipment_slots=[],consume_mode='charges')
            result.update(item_type='ammunition',damage_formula=None)
            gaps = []
            if item['id'] in DART_SPECS:
                mechanics['ammunition_effect'] = deepcopy(DART_SPECS[item['id']])
        if item['id'] in LAUNCHERS:
            mechanics['requires_ammunition']=LAUNCHERS[item['id']]
            mechanics['reload_movement']=item['id'].startswith('arma-distancia-besta')
    armor=BODY.get(name);shield=SHIELDS.get(name)
    if category=='protecao' and re.fullmatch(r'\+?\d+',str(item.get('bonus_defesa') or '')):
        bonus=int(item['bonus_defesa']);penalty=re.search(r'Redução\s+-(\d+)\s+metro',text)
        cap=re.search(r'DES máx\s+\+(\d+)',text)
        if name.casefold().startswith('escudo'):shield=bonus
        else:armor=(bonus,int(penalty[1]) if penalty else 0,int(cap[1]) if cap else None)
        if 'ricocheteia' in text and item['id']!='protecao-escudo-de-vibranium':gaps.append('special_effect')
    if armor or shield is not None:
        family='armor' if armor else 'shield';bonus,penalty,cap=armor if armor else (shield,0,None)
        if not armor:
            penalty_match=re.search(r'Redução\s+-(\d+)\s+metro',text)
            penalty=int(penalty_match[1]) if penalty_match else 0
        slots=['Armadura' if armor else 'Mão secundária']
        mechanics.update(kind=family,armor_defense=bonus,equipment_slots=slots,approved_equipment_slots=slots)
        if name=='Escudo torre':mechanics.update(special_defense='tower',block_chance_percent=25)
        if item['id']=='protecao-escudo-de-vibranium':
            mechanics.update(special_attack='vibranium',thrown_damage_formula='1d6',range_m=9,
                             attack_modes=['ranged'],dexterity_cap=3,damage_type='physical',
                             critical_threshold=20,critical_multiplier=2,
                             campaign_rule='Arremesso provisório: 1d6 + FOR, 9 m; retorna ao acertar e cai ao errar')
        if cap is not None:mechanics['dexterity_cap']=cap
        rules.append(rule('catalog:'+item['id']+':armor','armor_class_bonus',bonus))
        if penalty:rules.append(rule('catalog:'+item['id']+':movement','movement_bonus',-penalty))
        if 'Só Samurai' in text:
            for kind in ['attack_bonus','movement_bonus']:
                rules.append({**rule('catalog:'+item['id']+':class:'+kind,kind,-3,'all' if kind=='attack_bonus' else ''),'condition':'family:not_class:samurai'})
        result.update(item_type=family,damage_formula=None)
    if family:mechanics.update(family_schema=1,family=family,family_gaps=gaps,source=item.get('source'),weight=item.get('peso'))
    return result

def ammunition_choices(inventory, weapon):
    kind = (weapon.get('mechanics') or {}).get('requires_ammunition')
    if not kind:
        return []
    return sorted([i for i in inventory if (i.get('mechanics') or {}).get('ammunition_kind') == kind
        and i.get('quantity', 0) > 0 and ((i['quantity'] - 1) * i['mechanics']['pack_size']
        + (i.get('charges_current') if i.get('charges_current') is not None else i['mechanics']['pack_size'])) > 0],
        key=lambda i: (bool(i['mechanics'].get('ammunition_effect')), 'improvisada' in i['item_path'], i['item_path']))


def project_ammunition(inventory, selections=None):
    """One inventory, packs as quantity and remaining projectiles as charges."""
    for item in inventory:
        m=item.get('mechanics') or {}
        if m.get('family')=='ammunition':
            item['charges_max']=m['pack_size']
            if item.get('charges_current') is None:item['charges_current']=m['pack_size']
    for item in inventory:
        m=item.get('mechanics') or {};kind=m.get('requires_ammunition')
        if not kind:continue
        candidates=ammunition_choices(inventory, item)
        selected=(selections or {}).get(item.get('item_path'))
        ammo=next((i for i in candidates if i['item_path']==selected),None) if selected else next(iter(candidates),None)
        if selected and not ammo:raise ValueError('Munição indisponível ou incompatível com a arma equipada')
        for key in ('ammunition_path','ammunition_pack_size','ammunition_effect'):
            m.pop(key, None)
        if m.get('special_attack')=='dart':m.pop('special_attack')
        item['damage_formula']=(ammo['mechanics'].get('damage_formula')) if ammo else None
        m['damage_formula']=item['damage_formula']
        if ammo:
            m['ammunition_path']=ammo['item_path'];m['ammunition_pack_size']=ammo['mechanics']['pack_size'];m['damage_type']='piercing'
            if ammo['mechanics'].get('ammunition_effect'):
                m['special_attack']='dart'
                m['ammunition_effect']=deepcopy(ammo['mechanics']['ammunition_effect'])
            m['family_gaps']=[g for g in m.get('family_gaps',[]) if g!='ammunition']
    return inventory

def ammunition_contract(inventory,weapon_path,count,movement=None,selected_path=None):
    item=next((i for i in inventory if i.get('item_path')==weapon_path),{})
    m=item.get('mechanics') or {}
    if not m.get('requires_ammunition'):return None
    choices=ammunition_choices(inventory,item)
    if selected_path is None and len(choices)>1 and any(i['mechanics'].get('ammunition_effect') for i in choices):
        raise ValueError('Escolha a munição na confirmação do alvo')
    if not m.get('ammunition_path'):raise ValueError('Sem munição compatível para esta arma')
    contract={'item_path':m['ammunition_path'],'pack_size':m['ammunition_pack_size'],'amount':count}
    if m.get('ammunition_effect'):contract['effect']=deepcopy(m['ammunition_effect'])
    if m.get('reload_movement'):
        if count!=1:raise ValueError('A besta precisa recarregar entre disparos; escolha um único ataque')
        from .spatial_grid import movement_m
        contract['reload_movement']=True
        try:contract['reload_budget_m']=movement_m(movement)
        except ValueError:contract['reload_budget_m']=None
    return contract

def reload_movement(snapshot,contract,*,apply=False):
    if not contract or not contract.get('reload_movement'):return
    encounter=snapshot.get('encounter') or {}
    if not encounter.get('active'):return
    if not contract.get('reload_budget_m'):raise ValueError('Deslocamento indefinido para a recarga; confira a ficha')
    from .spatial_grid import turn_key,current_participant
    participant=current_participant(encounter)
    if participant is None:raise ValueError('Turno indisponível para recarga')
    key=turn_key(encounter,participant);budget=encounter.get('movement') or {}
    if budget.get('turn_key')==key and budget.get('spent_m',0)>0:
        raise ValueError('A recarga exige todo o deslocamento; o personagem já se moveu neste turno')
    if apply:encounter['movement']={'turn_key':key,'budget_m':contract['reload_budget_m'],'spent_m':contract['reload_budget_m'],'mode':'walk'}

def consume_ammunition(db,owner,contract,now,*,apply=False):
    if contract is None:return
    row=db.execute('SELECT id,quantity,charges_current FROM player_inventory WHERE profile_id=? AND item_path=?',(owner,contract['item_path'])).fetchone()
    if not row:raise ValueError('Munição indisponível; atualize a ficha')
    pack=contract['pack_size'];quantity=int(row[1]);charges=pack if row[2] is None else int(row[2]);amount=contract['amount']
    if not 0<=charges<=pack or amount<1:raise ValueError('Munição inconsistente; nada foi aplicado')
    if quantity<=0 or (quantity-1)*pack+charges<amount:raise ValueError('Munição insuficiente; nada foi aplicado')
    remaining=(quantity-1)*pack+charges-amount
    if apply:
        new_quantity=(remaining+pack-1)//pack;new_charges=remaining%pack or (pack if remaining else 0)
        db.execute('UPDATE player_inventory SET quantity=?,charges_current=?,charges_max=?,updated_at=? WHERE id=?',(new_quantity,new_charges,pack,now,row[0]))

def weapon_range(attack_id,inventory,weapon_path=None):
    from .character_play import available_attack_weapons
    candidates=available_attack_weapons(inventory,attack_id)
    weapon=next((i for i in candidates if i['item_path']==weapon_path),None) if weapon_path else next(iter(candidates),None)
    m=(weapon or {}).get('mechanics') or {}
    limit=m.get('melee_reach_m') if attack_id=='melee' else m.get('range_m')
    # 'ranged' here selects metric distance validation, not the attack's damage/attribute.
    return ('ranged',limit) if limit else (attack_id,None)

def armor_anchor(character):
    defense=character['definition']['defenses'];base=defense.get('base_armor_class');effective=defense.get('armor_class')
    if base is None or effective is None:raise ValueError('Defina a CA da ficha antes de equipar uma proteção')
    from .character_play import attribute_modifier
    dex=attribute_modifier(character['definition'].get('base_attributes',character['definition']['attributes']).get('dexterity',10)) or 0
    modifier=int(defense.get('armor_modifier') or 0);source=defense.get('armor_modifier_source') or {}
    applied=int(source.get('applied_value',0 if source.get('included_in_sheet') else modifier))
    return {'neutral':base-(modifier-applied),'reference':base,'dexterity_modifier':dex}

def anchored_defense(anchor,base,modifier,attributes,inventory):
    from .character_play import attribute_modifier
    dex=attribute_modifier(attributes.get('dexterity',10)) or 0
    caps=[i['mechanics']['dexterity_cap'] for i in inventory if i.get('equipped') and i.get('quantity',0)>0 and 'dexterity_cap' in (i.get('mechanics') or {})]
    effective_dex=min(dex,min(caps)) if caps else dex
    return int(anchor['neutral'])+(int(base)-int(anchor['reference']))+modifier+effective_dex-int(anchor['dexterity_modifier'])
