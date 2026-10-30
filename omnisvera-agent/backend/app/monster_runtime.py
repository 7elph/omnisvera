"""Monster rules inside native combat transactions, budgets and receipts.

No second clock, HP store or socket. Source-incomplete abilities stay assisted.
Area membership uses token centres in the map's metres, on its 2-D plane.
"""
from __future__ import annotations
import hashlib
import json
import math
import re

from .monster_action_specs import monster_action_specs
from .dice_rolls import roll_formula


def public_token(db, token_id):
    """Reuse map/fog visibility within the current command transaction."""
    from .session_workspace import _token_is_visible
    row=db.execute('SELECT map_id,latitude,longitude,visible_to_players FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()
    if not row or not row[3]:return False
    map_id=row[0] or 'default'
    map_row=db.execute('SELECT visible_to_players FROM session_workspace_maps WHERE id=?',(map_id,)).fetchone()
    if map_row and not map_row[0]:return False
    if db.execute('SELECT 1 FROM deleted_workspace_maps WHERE id=?',(map_id,)).fetchone():return False
    clock=db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()
    battle=json.loads(clock[0] or '{}') if clock else {}
    if battle.get('active') and battle.get('battle_mode') and battle.get('map_id')==map_id:
        if any((p.get('token_id') or p.get('target_id'))==token_id for p in [*battle.get('participants',[]),*battle.get('defeated',[])]):return True
    rows=db.execute('SELECT layer,enabled,revealed_cells_json,mist_density_json FROM session_workspace_map_fog WHERE map_id=?',(map_id,)).fetchall()
    if not rows and map_id=='default':rows=db.execute('SELECT layer,enabled,revealed_cells_json,mist_density_json FROM session_workspace_fog').fetchall()
    fog={r[0]:{'enabled':bool(r[1]),'revealed_cells':json.loads(r[2] or '[]'),'mist_density':json.loads(r[3] or '{}')} for r in rows}
    return _token_is_visible({'visible_to_players':True,'latitude':row[1] or 0,'longitude':row[2] or 0},fog)


def token_monster(db, token_id):
    from .monster_catalog import get_catalog_monster
    from .monster_actions import _split_token_ability
    row = db.execute("SELECT name,sheet_json,token_type FROM session_workspace_tokens WHERE id=?", (token_id,)).fetchone()
    if not row:
        raise ValueError('Criatura não encontrada')
    sheet = json.loads(row[1] or '{}')
    if row[2]!='monster':return None,sheet
    origin = sheet.get('source')
    source = get_catalog_monster(origin.get('monster_id', '')) if isinstance(origin, dict) else None
    if not source:
        return None, sheet
    monster = {**source, **{k:sheet[k] for k in ('hit_dice','attacks','movement') if k in sheet}, 'name':row[0]}
    if 'abilities' in sheet:
        monster['abilities'] = [a if isinstance(a,dict) else dict(zip(('name','description'), _split_token_ability(str(a)))) for a in sheet['abilities']]
    return monster, sheet


def breath_contract(monster, name):
    from .monster_exposures import exposure_specs
    exposure=next((s for s in exposure_specs(monster) if s['name'].casefold()==name.casefold()),None)
    if exposure and exposure['execution_status']=='native':return exposure
    spec = next((s for s in monster_action_specs(monster) if s['name'].casefold() == name.casefold()), None)
    if not spec:
        if exposure:return exposure
        raise ValueError('Baforada não encontrada')
    gaps = list(spec['reasons'])
    # An explicit absence of acid's lingering damage needs no extra effect.
    text=spec['description_full'].casefold()
    if re.search(r'não causa o dano regressivo',text) and not re.search(r'chance|cego|petrific|ghoul|concentrando|extra',text):
        gaps=[gap for gap in gaps if gap!='condicoes_ou_efeitos_adicionais']
    geometry = spec['geometry']
    required = {'cone':('width_m','depth_m'), 'line':('depth_m',), 'cloud':('width_m','depth_m','height_m'), 'radius':('radius_m',)}
    if geometry['shape'] not in required or any(not geometry.get(k) for k in required.get(geometry['shape'], ())):
        gaps.append('Área da baforada incompleta')
    if spec['uses'].get('recharge') not in ('day','combat','at_will'):
        gaps.append('Recarga depende de contador ainda não vinculado')
    text = spec['description_full'].casefold()
    damage_type = next((kind for kind,pattern in [('fire',r'fogo'),('cold',r'gelo|frio'),('acid',r'ácido'),('lightning',r'el[ée]tric'),('poison',r'venenoso'),('necrotic',r'necr[óo]tic')] if re.search(pattern,text)), None)
    canonical = json.dumps([monster.get('id'),name,spec],sort_keys=True,ensure_ascii=False)
    return {**spec, 'damage_type':damage_type, 'gaps':list(dict.fromkeys(gaps)),
            'revision':hashlib.sha256(canonical.encode()).hexdigest(),
            'execution_status':'assisted' if gaps else 'native'}


def action_contracts(db,token_id):
    from .monster_exposures import exposure_specs
    monster,sheet=token_monster(db,token_id)
    if not monster:return {}
    names=dict.fromkeys(s['name'] for s in [*monster_action_specs(monster),*exposure_specs(monster)])
    contracts={name:breath_contract(monster,name) for name in names}
    progress=(sheet.get('monster_runtime') or {}).get('attack_recharge') or {}
    for spec in contracts.values():
        threshold=spec['uses'].get('every_n_attacks')
        if threshold:
            spec['attacks_until_ready']=max(0,threshold-int(progress.get(spec['id'],0)))
            spec['ready']=spec['attacks_until_ready']==0
    return contracts


def record_confirmed_attacks(db,record,now):
    if not str(record['attack_id']).isdecimal():return
    actor_id=record['actor_character_id']
    if not db.execute('SELECT 1 FROM session_workspace_tokens WHERE id=?',(actor_id,)).fetchone():return
    contracts=action_contracts(db,actor_id)
    rechargeable=[s for s in contracts.values() if s['uses'].get('every_n_attacks')]
    if not rechargeable:return
    _,sheet=token_monster(db,actor_id);runtime=sheet.setdefault('monster_runtime',{})
    progress=runtime.setdefault('attack_recharge',{})
    for spec in rechargeable:
        threshold=spec['uses']['every_n_attacks']
        progress[spec['id']]=min(threshold,int(progress.get(spec['id'],0))+len(record['breakdown'].get('strikes') or [record]))
    db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?',(json.dumps(sheet,ensure_ascii=False),now,actor_id))


def _units(db, snapshot, token_id, aim_token_id):
    encounter = snapshot.get('encounter') or {}
    if not encounter.get('active') or not encounter.get('battle_mode'):
        raise ValueError('Baforada automática exige combate ativo com grid')
    map_id = encounter['map_id']
    grid = db.execute('SELECT cell_size_m FROM session_workspace_map_grids WHERE map_id=?',(map_id,)).fetchone()
    if not grid:
        raise ValueError('Grid lógico ausente')
    rows = db.execute('SELECT t.id,t.character_id,t.name,t.visible_to_players,p.cell_x,p.cell_y,p.footprint_w,p.footprint_h,t.updated_at,t.current_hp FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id WHERE t.map_id=? AND t.token_type!=?',(map_id,'location')).fetchall()
    participants = {(p['target_type'],p['target_id']) for p in encounter.get('participants') or []}
    units = {}
    for row in rows:
        pin, char, name, visible, x,y,w,h,stamp,hp = tuple(row)
        kind, identity = ('character',char) if char else ('token',pin)
        if (kind,identity) not in participants:
            continue
        units[pin] = dict(pin=pin,type=kind,id=identity,name=name,visible=bool(visible),x=(x+w/2)*grid[0],y=(y+h/2)*grid[0],state_stamp=[stamp,hp])
    if token_id not in units or aim_token_id not in units:
        raise ValueError('Origem e direção devem estar no mapa e no combate atual')
    return units[token_id],units[aim_token_id],list(units.values()),map_id


def _inside(origin, aim, target, geometry):
    if geometry['shape']=='radius':return math.hypot(target['x']-origin['x'],target['y']-origin['y'])<=geometry['radius_m']+1e-8
    vx,vy=aim['x']-origin['x'],aim['y']-origin['y']; length=math.hypot(vx,vy)
    if length<=0:
        raise ValueError('Escolha uma direção diferente da origem')
    dx,dy=target['x']-origin['x'],target['y']-origin['y']
    forward=(dx*vx+dy*vy)/length; side=abs(dx*vy-dy*vx)/length
    shape=geometry['shape']; depth=geometry.get('depth_m') or 0
    if shape=='radius':return math.hypot(dx,dy)<=geometry['radius_m']+1e-8
    if forward<=0 or forward>depth+1e-8:return False
    if shape=='cone':return side<=geometry['width_m']/2*forward/depth+1e-8
    if shape=='cloud':return side<=geometry['width_m']/2+1e-8
    # Zero-width line: centres on the selected ray; no arbitrary cell-width.
    return side<=1e-8


def preview(db,snapshot,token_id,name,aim_token_id):
    monster,sheet=token_monster(db,token_id)
    if not monster:raise ValueError('Sem fonte do bestiário para automatizar esta baforada')
    contract=breath_contract(monster,name)
    if contract['execution_status']!='native':raise ValueError('Baforada assistida: '+'; '.join(contract['gaps']))
    origin,aim,units,map_id=_units(db,snapshot,token_id,aim_token_id)
    if token_id==aim_token_id and not contract.get('reflection_allowed'):raise ValueError('Esta ação não pode atingir a própria origem')
    if not _inside(origin,aim,aim,contract['geometry']):raise ValueError('Direção fora do alcance')
    selected=[];seen=set()
    from .dorn_spells import target
    for unit in sorted(units,key=lambda u:u['pin']):
        if contract.get('targeting_mode')=='single':
            if unit['pin']!=aim_token_id:continue
        elif unit['pin']==token_id:continue
        if not _inside(origin,aim,unit,contract['geometry']):continue
        key=(unit['type'],unit['id'])
        if key in seen:continue
        try:target(db,*key)
        except ValueError:continue  # Corpses are not targets, and cannot roll JP.
        selected.append(unit);seen.add(key)
    if not selected:raise ValueError('Nenhuma criatura viva nessa área')
    stamp=[map_id,origin['pin'],aim['pin'],contract['revision'],sorted((u['pin'],u['type'],u['id'],u['x'],u['y'],u['state_stamp']) for u in units)]
    contract={**contract,'area_fingerprint':hashlib.sha256(json.dumps(stamp,sort_keys=True).encode()).hexdigest()}
    grid=db.execute('SELECT cols,rows,cell_size_m FROM session_workspace_map_grids WHERE map_id=?',(map_id,)).fetchone()
    contract['area_cells']=[[x,y] for x in range(grid[0]) for y in range(grid[1]) if _inside(origin,aim,{'x':(x+.5)*grid[2],'y':(y+.5)*grid[2]},contract['geometry'])] if grid[0]*grid[1]<=40000 and contract.get('targeting_mode')!='single' else []
    return contract,selected,map_id


def command(db,snapshot,payload,now,request_id):
    allowed={'token_id','ability_name','aim_token_id','definition_revision','area_fingerprint','eye_contact_confirmed'}
    if set(payload)-allowed:raise ValueError('Parâmetros da baforada não podem sobrescrever regras')
    token_id=str(payload.get('token_id') or '');name=str(payload.get('ability_name') or '')
    from .battle_mode import require_battle_turn,commit_battle_action
    monster,_=token_monster(db,token_id)
    if not monster:raise ValueError('Criatura sem fonte válida no catálogo')
    initial=breath_contract(monster,name)
    gaze=initial.get('requires_eye_contact',False)
    if gaze:
        if payload.get('eye_contact_confirmed') is not True:raise ValueError('Confirme o contato visual direto ou refletido')
        from .battle_mode import require_actor_alive
        from .monster_conditions import assert_can_act
        require_actor_alive(db,token_id);assert_can_act(db,token_id)
    else:
        if 'eye_contact_confirmed' in payload:raise ValueError('Contato visual não pertence a esta ação')
        require_battle_turn(db,snapshot,token_id)
    spec,units,map_id=preview(db,snapshot,token_id,name,str(payload.get('aim_token_id') or ''))
    if payload.get('definition_revision')!=spec['revision']:raise ValueError('Definição mudou. Atualize a criatura')
    if payload.get('area_fingerprint')!=spec['area_fingerprint']:raise ValueError('Posições mudaram. Confirme a área novamente')
    if not gaze:
        for unit in units:require_battle_turn(db,snapshot,token_id,unit['type'],unit['id'])
    monster,sheet=token_monster(db,token_id)
    runtime=sheet.setdefault('monster_runtime',{});usage=runtime.setdefault('usage',{})
    key=spec['id'];period=spec['uses']['recharge'];scope=(snapshot['encounter'].get('started_at') if period=='combat' else 'day')
    spent=usage.get(key,{})
    used=int(spent.get('spent') or 0) if spent.get('scope')==scope else 0
    maximum=spec['uses']['maximum']
    threshold=spec['uses'].get('every_n_attacks')
    if threshold:
        progress=int((runtime.get('attack_recharge') or {}).get(key,0))
        if progress<threshold:raise ValueError(f'Gás indisponível: exige {threshold} ataques confirmados; faltam {threshold-progress}')
        used=0
    if maximum is not None and used>=maximum:raise ValueError('Sem usos de baforada até o próximo descanso')
    # One damage roll is shared by the entire area; every creature has its JP.
    roll=roll_formula(spec['damage_formula']) if spec.get('damage_formula') else None
    total=max(0,int(roll['total']))*spec.get('damage_multiplier',1) if roll else 0
    from .dorn_spells import target,save
    from .combat_effects import change_hp
    outcomes=[]
    for unit in units:
        victim=target(db,unit['type'],unit['id'])
        if spec.get('condition'):
            from .monster_conditions import apply_spec
            resolved=apply_spec(db,victim,spec['condition'],token_id,now)
            outcomes.append(dict(target=unit['name'],target_type=unit['type'],target_id=unit['id'],pin_id=unit['pin'],visible=unit['visible'],
                save=resolved.get('save'),resisted=resolved.get('resisted',False),manual=False,damage_rolled=0,damage_dealt=0,condition=resolved))
            continue
        if spec.get('activation')=='gas':
            from .monster_conditions import _immune
            immunity=_immune(db,unit['type'],unit['id'],{'effect':'poison_damage','exposure':'gas'})
            if immunity:
                outcomes.append(dict(target=unit['name'],target_type=unit['type'],target_id=unit['id'],pin_id=unit['pin'],visible=unit['visible'],save=None,resisted=False,manual=False,damage_rolled=total,damage_dealt=0,immune=immunity))
                continue
        check=save(db,victim,{'JPD':'dexterity','JPC':'constitution','JPS':'wisdom'}[spec['save']])
        damage=total//2 if check['success'] and spec['save_effect']=='halves' else 0 if check['success'] else total
        hp=change_hp(db,unit['type'],unit['id'],-damage,now,damage_type=spec['damage_type'],damage_context={'kind':'effect','magical':False} if spec.get('activation')=='gas' else None)
        outcomes.append(dict(target=unit['name'],target_type=unit['type'],target_id=unit['id'],pin_id=unit['pin'],visible=unit['visible'],save=check,resisted=bool(check['success']),manual=False,damage_rolled=total,damage_dealt=hp.get('damage_taken',damage),hp={**hp,'before':hp['hp_before'],'after':hp['hp_after']}))
    # Re-read latest sheet: damage reactions may have updated a target's state.
    _,sheet=token_monster(db,token_id);runtime=sheet.setdefault('monster_runtime',{});usage=runtime.setdefault('usage',{})
    if threshold:runtime.setdefault('attack_recharge',{})[key]=0
    else:usage[key]={'scope':scope,'spent':used+1}
    db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?',(json.dumps(sheet,ensure_ascii=False),now,token_id))
    if not gaze:commit_battle_action(db,snapshot)
    from .session_ledger import append_session_ledger_event
    public=[{k:v for k,v in result.items() if k!='visible'} for result in outcomes if public_token(db,result['pin_id'])]
    caster_visible=public_token(db,token_id)
    if public:append_session_ledger_event(db,source_type='monster_breath',source_id=request_id,event_kind='action',actor_id='master',actor_name='Mestre',actor_role='gm',character_id=None,
        title=f"{monster['name']} usou {name}",detail={'label':name,'roll':roll,'results':public},visibility='table' if caster_visible else 'gm',created_at=now)
    return dict(label=name,damage_roll=roll,damage_total=total,results=outcomes,map_id=map_id,uses_remaining=maximum-used-1 if maximum is not None else None)


def full_rest(db,now):
    """Only the GM's explicit party-rest flag calls this, inside its receipt."""
    for token_id,raw in db.execute("SELECT id,sheet_json FROM session_workspace_tokens WHERE token_type='monster'").fetchall():
        sheet=json.loads(raw or '{}');runtime=sheet.get('monster_runtime')
        if runtime and runtime.get('usage'):
            runtime['usage']={}
            db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?',(json.dumps(sheet,ensure_ascii=False),now,token_id))


def passive_data(db,target_type,target_id):
    if target_type!='token':return {}
    monster,sheet=token_monster(db,target_id)
    if not monster:return {}
    from .monster_passives import passive_specs
    return passive_specs(monster)


def damage_response(db,kind,identity,amount,damage_type,context=None):
    context=context or {}
    unavoidable=context.get('unavoidable_damage',0)
    unavoidable=max(0,min(amount,unavoidable)) if type(unavoidable) is int else 0
    amount-=unavoidable
    spec=passive_data(db,kind,identity)
    monster=None;sheet={}
    if kind=='token' and db is not None:monster,sheet=token_monster(db,identity)
    elif kind=='character' and db is not None:
        row=db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?',(identity,)).fetchone()
        sheet=json.loads(row[0] or '{}') if row else {}
        if damage_type=='poison' and context.get('magical') is False:
            from .construct_rules import is_construct
            if is_construct(db,identity):return unavoidable
    immunities=spec.get('damage_immunities') or []
    local=sheet.get('damage_immunities') or []
    if not isinstance(local,list):raise ValueError('Imunidades de dano cadastradas inválidas')
    if any((entry.get('type') if isinstance(entry,dict) else entry)==damage_type for entry in immunities) or damage_type in local or (damage_type in {'slashing','piercing','bludgeoning'} and 'physical' in local):return unavoidable
    from .damage_profiles import weapon_defense
    amount=math.floor(amount*weapon_defense(monster,context))
    for key in ('damage_resistances','damage_vulnerabilities'):
        mapping=spec.get(key) or {}
        factor=mapping.get(damage_type) if isinstance(mapping,dict) else next((item.get('factor') for item in mapping if isinstance(item,dict) and item.get('type')==damage_type),None)
        if isinstance(factor,(int,float)) and not isinstance(factor,bool) and 0<=factor<=10:amount=math.floor(amount*factor)
    return max(0,amount)+unavoidable


def track_hp(db,kind,identity,before,after,damage_type,regeneration,now):
    if kind!='token':return
    monster,sheet=token_monster(db,identity)
    if not monster:return
    spec=passive_data(db,kind,identity).get('regeneration') or {}
    if not spec:return
    runtime=sheet.setdefault('monster_runtime',{});blocked=int(runtime.get('nonregenerable_damage') or 0)
    if after<before and damage_type in spec.get('blocked_by',[]):blocked+=before-after
    if after>before and not regeneration:blocked=max(0,blocked-(after-before))
    runtime['nonregenerable_damage']=blocked
    db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?',(json.dumps(sheet,ensure_ascii=False),now,identity))


def turn_start(db,participant,encounter,round_number,now,request_id):
    if not participant or participant['target_type']!='token':return
    identity=participant['target_id'];spec=passive_data(db,'token',identity).get('regeneration') or {}
    if not spec:return
    monster,sheet=token_monster(db,identity);runtime=sheet.setdefault('monster_runtime',{})
    key=[encounter.get('started_at'),round_number]
    if runtime.get('regeneration_tick')==key:return
    row=db.execute('SELECT current_hp,maximum_hp FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
    if not row or not row[0] or row[0]<=0:return
    amount=min(int(spec['amount']),max(0,row[1]-row[0]-int(runtime.get('nonregenerable_damage') or 0)))
    runtime['regeneration_tick']=key
    db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?',(json.dumps(sheet,ensure_ascii=False),identity))
    if amount:
        from .combat_effects import change_hp
        hp=change_hp(db,'token',identity,amount,now,regeneration=True)
        from .session_ledger import append_session_ledger_event
        visible=public_token(db,identity)
        append_session_ledger_event(db,source_type='monster_regeneration',source_id=request_id+':'+identity,event_kind='action',actor_id='master',actor_name='Mestre',actor_role='gm',character_id=None,
            title=f"{monster['name']} regenerou {amount} PV",detail=hp,visibility='table' if visible else 'gm',created_at=now)
