"""Approved level-five weapons, composed inside native combat transactions.

No separate turn, damage command, inventory, receipt or realtime transport.
Metadata is server-owned; clients select an action id, never dice or costs.
"""
import copy
import json
import sqlite3
import uuid
from contextlib import closing

from .dice_rolls import roll_formula

REVISION = 'raziel-five-weapons-v4'
LEGACY_IDS = {'lamina-de-sangue','arma-de-sangue','garras-predatorias','investida-predatoria','sangue-defensivo'}
_WEAPONS = [
    dict(weapon='arco',name='Arco de Sangue',damage='1d8',damage_type='piercing',range_m=9,invocation_cost=1,
         skill=dict(id='tiro-do-coracao',name='Tiro do Coração',cost=1,description='+2 no acerto contra alvo marcado por Raziel.'),
         passive=dict(id='mira-predatoria',name='Mira Predatória',description='19–20 naturais que acertem rolam duas vezes somente os dados base.')),
    dict(weapon='foice',name='Foice de Sangue',damage='1d8',damage_type='slashing',range_m=None,invocation_cost=1,
         skill=dict(id='ceifa-rubra',name='Ceifa Rubra',cost=1,description='Acerto com dano aplica 1d4 de sangramento por dois turnos do alvo; não acumula.'),
         passive=dict(id='carrasco',name='Carrasco',description='+1d6 contra alvo previamente com até 25% dos PV. Desmembramento é finalização ao matar.')),
    dict(weapon='marreta',name='Marreta de Sangue',damage='1d10',damage_type='bludgeoning',range_m=None,invocation_cost=1,
         skill=dict(id='ruptura-ossea',name='Ruptura Óssea',cost=1,description='Ignora até 2 de redução de dano físico, nunca imunidades.'),
         passive=dict(id='trauma-profundo',name='Trauma Profundo',description='Acerto com dano deixa Exposto: +2 no próximo ataque de Lança de Sangue contra esse alvo; também ativa +1d6 da lança.')),
    dict(weapon='escudo',name='Escudo de Sangue',damage=None,damage_type=None,range_m=0,invocation_cost=1,
         skill=dict(id='bastiao-carmesim',name='Bastião Carmesim',cost=0,description='Custo total 1: +2 CA por uma rodada; não consome o ataque.'),
         passive=dict(id='revanche-rubra',name='Revanche Rubra',description='Se os +2 CA evitarem um acerto, prepara +1d6 para o próximo ataque hemomântico; uma carga, sem ataque gratuito.')),
    dict(weapon='lanca',name='Lança de Sangue',damage='1d8',damage_type='piercing',range_m=3,invocation_cost=1,
         skill=dict(id='estocada-transfixante',name='Estocada Transfixante',cost=1,bonus_damage='1d4',description='+1d4 de dano perfurante no ataque a até 3 m.'),
         passive=dict(id='ferroada-arterial',name='Ferroada Arterial',description='+1d6 por Exposto e +1d6 por Sangramento; as duas condições somam +2d6.')),
]


def weapons():
    return copy.deepcopy(_WEAPONS)

def blood_cost(spec,skill,held):
    return 1 if skill or spec['weapon']=='escudo' or not held else 0


def action(technique):
    skill = technique.endswith('-habilidade')
    key = technique.removeprefix('hemomancia-').removesuffix('-habilidade')
    spec = next((w for w in _WEAPONS if w['weapon']==key),None)
    if spec is None or technique not in {f'hemomancia-{key}',f'hemomancia-{key}-habilidade'}:
        raise ValueError('Arma hemomântica desconhecida')
    return copy.deepcopy(spec),skill


ACTION_IDS = {f'hemomancia-{w["weapon"]}{suffix}' for w in _WEAPONS for suffix in ('','-habilidade')}


def pack():
    return dict(revision=REVISION,weapons=weapons())


def _effects(db):
    return [json.loads(r[0]) for r in db.execute('SELECT data_json FROM combat_effects WHERE active=1')]


def _put(db,kind,label,now,*,target_type='character',target_id='raziel',map_id=None,**extra):
    # Caller owns BEGIN IMMEDIATE and command receipt. Refresh, never stack.
    db.execute("UPDATE combat_effects SET active=0 WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.hemomancy_kind')=?",(target_type,target_id,kind))
    effect=dict(id='hemomancy:'+uuid.uuid4().hex,target_type=target_type,target_id=target_id,
                label=label,source='Hemomancia (Raziel)',duration='scene',rounds=None,
                modifiers={},hemomancy_kind=kind,map_id=map_id,updated_at=now)
    effect.update(extra)
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],target_type,target_id,json.dumps(effect,ensure_ascii=False)))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return effect


def _map_id(db,snapshot):
    encounter=snapshot.get('encounter') or {}
    active=encounter.get('map_id') if encounter.get('active') else None
    if not active:
        row=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
        active=row[0] if row else 'default'
    return active


def _origin(db,snapshot):
    active=_map_id(db,snapshot)
    pin=db.execute("SELECT t.id,t.map_id FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id WHERE t.character_id='raziel' AND t.map_id=? ORDER BY t.id LIMIT 1",(active,)).fetchone()
    if not pin:raise ValueError('Posicione Raziel no grid do mapa ativo')
    return pin[0],pin[1]


def _hp(db,kind,identity):
    if kind=='character':
        row=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(identity,)).fetchone()
        if not row:raise ValueError('Alvo não encontrado')
        state=json.loads(row[0]);return int(state['current_hp']),int(state['maximum_hp'])
    row=db.execute('SELECT current_hp,maximum_hp FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
    if not row or row[0] is None or row[1] is None:raise ValueError('Alvo sem PV')
    return int(row[0]),int(row[1])


def _range(db,snapshot,spec,target,role):
    from .spatial_grid import grid_record, distance_cells
    origin,map_id=_origin(db,snapshot)
    if target['type']=='character':
        row=db.execute('SELECT id,visible_to_players FROM session_workspace_tokens WHERE character_id=? AND map_id=? ORDER BY id LIMIT 1',(target['id'],map_id)).fetchone()
    else:
        row=db.execute('SELECT id,visible_to_players FROM session_workspace_tokens WHERE id=? AND map_id=?',(target['id'],map_id)).fetchone()
    if not row or (role!='gm' and not row[1]):raise ValueError('Alvo não disponível no mapa')
    if row[0]==origin:raise ValueError('Não ataque a si mesmo')
    grid=grid_record(db,map_id)
    if not grid:raise ValueError('Configure o grid do mapa ativo')
    points=[]
    for token in (origin,row[0]):
        position=db.execute('SELECT cell_x,cell_y FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',(map_id,token)).fetchone()
        if not position:raise ValueError('Posicione o alvo no mesmo grid de Raziel')
        points.append(list(position))
    cells=distance_cells(grid['distance_rule'],*points)
    if (spec['range_m'] is None and cells>1) or (spec['range_m'] is not None and cells*grid['cell_size_m']>spec['range_m']+1e-8):
        raise ValueError('Fora de alcance da arma hemomântica')
    return map_id


def prepare(db,path,snapshot,attack,target,role):
    if db.execute('SELECT 1 FROM combat_effect_commands WHERE request_id=?',(attack['command_request_id'],)).fetchone():
        raise ValueError('request_id já usado para outra ação')
    spec,skill=action(attack['id'])
    if spec['weapon']=='escudo':raise ValueError('Escudo não é um ataque')
    map_id=_range(db,snapshot,spec,target,role)
    effects=_effects(db)
    held=next((e for e in effects if e.get('hemomancy_kind')=='weapon' and e['target_id']=='raziel' and e.get('map_id')==map_id),None)
    invocation=0 if held and held.get('weapon')==spec['weapon'] else spec['invocation_cost']
    cost=blood_cost(spec,skill,bool(held and held.get('weapon')==spec['weapon']))
    exposed=next((e for e in effects if e.get('hemomancy_kind')=='exposed' and (e['target_type'],e['target_id'],e.get('map_id'))==(target['type'],target['id'],map_id)),None)
    bleeding=any(e.get('hemomancy_kind')=='bleed' and (e['target_type'],e['target_id'],e.get('map_id'))==(target['type'],target['id'],map_id) for e in effects)
    charge=next((e for e in effects if e.get('hemomancy_kind')=='revenge' and e.get('map_id')==map_id),None)
    marked=any(e.get('source')=='Marca Rubra (Lâminas de Sangue)' and e['target_type']==target['type'] and e['target_id']==target['id'] and e.get('map_id',map_id)==map_id for e in effects)
    hp,maximum=_hp(db,target['type'],target['id'])
    attack=copy.deepcopy(attack)
    if spec['weapon']=='arco' and skill and marked:attack['attack_bonus']+=2
    attack['hemomancy']=dict(revision=REVISION,weapon=spec['weapon'],skill=skill,map_id=map_id,
        base_damage=spec['damage'],skill_damage=spec['skill'].get('bonus_damage') if skill else None,
        skill_name=spec['skill']['name'] if skill else None,
        request_target=attack.get('request_target'),
        invocation=invocation,previous_weapon_id=held['id'] if held else None,
        exposed_id=exposed['id'] if exposed else None,charge_id=charge['id'] if charge else None,
        target_hp=hp,target_maximum=maximum,bonus=2 if exposed and spec['weapon']=='lanca' else 0,marked=marked,bleeding=bleeding,
        passive_d6=int(bool(charge))+int(spec['weapon']=='lanca')*(int(bool(exposed))+int(bleeding))+int(spec['weapon']=='foice' and hp*4<=maximum),
        damage_type=spec['damage_type'],ignore_reduction=2 if spec['weapon']=='marreta' and skill else 0)
    if cost:attack['resource_cost']=dict(key='reserva_de_sangue',amount=cost)
    return attack


def roll_passives(attack,strike,rng):
    meta=attack.get('hemomancy')
    if not meta or strike['result']!='hit':return
    extras=[]
    if meta['weapon']=='arco' and strike['d20']>=19:
        base=next(w['damage'] for w in _WEAPONS if w['weapon']=='arco')
        extras.append(('Mira Predatória',roll_formula(base,rng)))
        strike['critical']=True
    if meta.get('skill_damage'):
        extras.append((meta['skill_name'],roll_formula(meta['skill_damage'],rng)))
    if meta['passive_d6']:extras.append(('Passivas hemomânticas',roll_formula(f"{meta['passive_d6']}d6",rng)))
    for label,result in extras:
        strike['damage_total']+=int(result['total']);strike['damage_rolls']+=result['individual_results']
        strike.setdefault('hemomancy_rolls',[]).append(dict(label=label,**result))
    strike['damage_total']+=meta['bonus']


def validate_confirm(db,snapshot,record):
    meta=record['breakdown'].get('hemomancy')
    if not meta:return
    if meta['revision']!=REVISION:raise ValueError('Definição de Hemomancia mudou; refaça a prévia')
    spec,_=action(record['attack_id'])
    map_id=_range(db,snapshot,spec,{'type':record['target_type'],'id':record['target_id']},record['requested_by_role'])
    if map_id!=meta['map_id']:raise ValueError('O mapa mudou; refaça a prévia')
    if _hp(db,record['target_type'],record['target_id'])!=(meta['target_hp'],meta['target_maximum']):raise ValueError('Os PV do alvo mudaram; refaça a prévia')


def damage_after_mitigation(db,record,damage):
    meta=record['breakdown'].get('hemomancy')
    if not meta:return damage
    if record['target_type']=='token':
        raw=db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(record['target_id'],)).fetchone()
    else:
        raw=db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?',(record['target_id'],)).fetchone()
    stats=json.loads(raw[0] or '{}') if raw else {}
    reduction=stats.get('damage_reduction',0)
    if type(reduction) is not int or not 0<=reduction<=999:raise ValueError('Redução de dano cadastrada inválida')
    immunities=stats.get('damage_immunities') or []
    if not isinstance(immunities,list):raise ValueError('Imunidades cadastradas inválidas')
    immune=meta['damage_type'] in immunities or 'physical' in immunities
    reduction=max(0,reduction-meta['ignore_reduction'])
    record['breakdown']['hemomancy_mitigation']=dict(reduction=reduction,immune=immune)
    return 0 if immune else max(0,damage-reduction)


def incoming_shield(snapshot,target,strikes):
    if (target.get('type'),target.get('id'))!=('character','raziel'):return None
    shield=next((e for e in snapshot['effects'] if e.get('hemomancy_kind')=='shield'),None)
    if shield and any(s['result']=='miss' and s['d20'] not in (1,20) and s['attack_total']>=int(target['armor_class'])-2 for s in strikes):return shield['id']
    return None


def confirmed(db,snapshot,record,hp_change,now):
    meta=record['breakdown'].get('hemomancy')
    if record['breakdown'].get('hemomancy_shield'):
        shield=next((e for e in snapshot['effects'] if e['id']==record['breakdown']['hemomancy_shield']),None)
        if shield and not any(e.get('hemomancy_kind')=='revenge' for e in _effects(db)):
            _put(db,'revenge','Revanche Rubra',now,map_id=shield.get('map_id'))
    if not meta:return
    _put(db,'weapon',next(w['name'] for w in _WEAPONS if w['weapon']==meta['weapon']),now,map_id=meta['map_id'],weapon=meta['weapon'])
    for identity in (meta['exposed_id'] if meta['weapon']=='lanca' else None,meta['charge_id']):
        if identity:db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(identity,))
    if not hp_change.get('damage_taken'):return
    kind,identity=record['target_type'],record['target_id']
    if meta['weapon']=='marreta' and hp_change['hp_after']>0:
        _put(db,'exposed','Exposto — Trauma Profundo',now,target_type=kind,target_id=identity,map_id=meta['map_id'])
    if meta['weapon']=='foice' and meta['skill'] and hp_change['hp_after']>0:
        from .combat import _require_blood_target
        try:_require_blood_target(db,kind,identity)
        except ValueError:return
        _put(db,'bleed','Sangramento — Ceifa Rubra',now,target_type=kind,target_id=identity,map_id=meta['map_id'],remaining_turns=2)
    if meta['weapon']=='foice' and hp_change['hp_after']==0:
        finisher='Carrasco — finalização da criatura derrotada com desmembramento.'
        record['breakdown']['hemomancy_finisher']=finisher
        record['breakdown'].setdefault('manual_effects',[]).append(finisher)


def mark_command(db,snapshot,now,payload,request_id,role):
    """Native receipt owns the approved cross, validation and single charge."""
    from .raziel_pipeline import cross_mark
    if db.execute('SELECT 1 FROM combat_attack_resolutions WHERE request_id=?',(request_id,)).fetchone():
        raise ValueError('request_id já usado para outra ação')
    previous_factory=db.row_factory
    db.row_factory=sqlite3.Row
    try:
        return cross_mark(db,snapshot,now,payload,request_id,role)
    finally:
        db.row_factory=previous_factory


def shield_command(db,snapshot,now,payload,request_id):
    if db.execute('SELECT 1 FROM combat_attack_resolutions WHERE request_id=?',(request_id,)).fetchone():
        raise ValueError('request_id já usado para outra ação')
    if payload.get('definition_revision') not in (None,REVISION):raise ValueError('Definição de Hemomancia mudou; atualize a ficha')
    from .night_form import require_humanoid
    from .battle_mode import require_actor_alive,require_battle_turn
    from .action_components import spend_native_resource
    from .raziel_action_contracts import BLOOD_DEFENSE_SOURCE
    require_humanoid(db,'raziel');require_actor_alive(db,'raziel');require_battle_turn(db,snapshot,'raziel',auxiliary=True)
    if any(e.get('source')==BLOOD_DEFENSE_SOURCE for e in snapshot['effects']):raise ValueError('Escudo de sangue já ativo')
    map_id=_map_id(db,snapshot)
    remaining=spend_native_resource(db,'raziel','reserva_de_sangue',1,now)
    effect=_put(db,'shield','Sangue Defensivo — escudo (Raziel)',now,map_id=map_id,
                source=BLOOD_DEFENSE_SOURCE,duration='rounds',rounds=1,modifiers={'armor_class_bonus':2})
    from .raziel_pipeline import after_shield
    after_shield(db,map_id,now)
    return dict(effect=effect,blood_remaining=remaining)


def turn_start(db,participant,encounter,now,request_id):
    if not participant:return False
    from .combat_effects import change_hp
    from .session_ledger import append_session_ledger_event
    died=False
    for effect in _effects(db):
        if effect.get('hemomancy_kind')!='bleed' or (effect['target_type'],effect['target_id'])!=(participant['target_type'],participant['target_id']) or effect.get('map_id')!=encounter.get('map_id'):continue
        hp,_=_hp(db,effect['target_type'],effect['target_id'])
        if hp<=0:
            db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(effect['id'],));continue
        rolled=roll_formula('1d4');result=change_hp(db,effect['target_type'],effect['target_id'],-int(rolled['total']),now)
        effect['remaining_turns']-=1
        db.execute('UPDATE combat_effects SET active=?,data_json=? WHERE id=?',(int(effect['remaining_turns']>0 and result['hp_after']>0),json.dumps(effect,ensure_ascii=False),effect['id']))
        append_session_ledger_event(db,source_type='hemomancy_bleed',source_id=request_id+':'+effect['id'],event_kind='roll',actor_id='raziel',actor_name='Raziel',actor_role='player',character_id='raziel',title=f"Ceifa Rubra — {participant.get('name','alvo')}: 1d4 = {rolled['total']} · PV {result['hp_before']} → {result['hp_after']}",detail={'formula':'1d4','dice':'1d4','results':rolled['individual_results'],'modifier':0,'subtotal':rolled['total'],'total':rolled['total'],**result},visibility='table',created_at=now)
        died=died or result['hp_after']==0
    return died


def end_combat(db):
    return db.execute("UPDATE combat_effects SET active=0 WHERE active=1 AND json_extract(data_json,'$.hemomancy_kind') IS NOT NULL").rowcount


def use_weapon(path,technique,request,actor_id,actor_role,load_character,load_target):
    from .combat import resolve_attack,_resolution_record
    from .combat_effects import effect_command,readeffects
    spec,skill=action(technique)
    allowed={'request_id','definition_revision','target_type','target_id','roll_mode','d20','mode'}
    if set(request.model_dump(exclude_none=True))-allowed:raise ValueError('Parâmetros extras não permitidos para Hemomancia')
    if request.mode not in (None,'basic','skill'):raise ValueError('Modo hemomântico inválido')
    if skill and request.mode=='basic':raise ValueError('Modo não corresponde à habilidade')
    if request.mode=='skill':
        technique=technique.removesuffix('-habilidade')+'-habilidade';skill=True
    request_id=request.request_id or 'hemomancy-'+uuid.uuid4().hex
    if spec['weapon']=='escudo':
        if request.target_type or request.target_id or request.roll_mode or request.d20 is not None:raise ValueError('Escudo é uma ação pessoal, sem ataque')
        return effect_command(path,actor_id=actor_id,actor_role=actor_role,request_id=request_id,
            expected_version=readeffects(path)['version'],action='hemomancy_shield',
            payload={'definition_revision':request.definition_revision},allow_player=True)
    # Recover native receipts before loading mutable sheet, form, target or revision.
    with closing(sqlite3.connect(path)) as db:
        db.row_factory=sqlite3.Row
        row=db.execute('SELECT * FROM combat_attack_resolutions WHERE request_id=?',(request_id,)).fetchone()
        if row:
            record=_resolution_record(row)
            expected=(actor_id,actor_role,technique,request.target_type,request.target_id,request.roll_mode or 'digital')
            saved=record['breakdown']['hemomancy']['request_target']
            actual=(record['requested_by_id'],record['requested_by_role'],record['attack_id'],*saved,record['roll_mode'])
            if actual!=expected or (record['roll_mode']=='physical' and request.d20!=record['d20']) or (record['roll_mode']=='digital' and request.d20 is not None):raise ValueError('request_id já usado para outra ação')
            return record
    if request.definition_revision not in (None,REVISION):raise ValueError('Definição de Hemomancia mudou; atualize a ficha')
    if not request.target_type or not request.target_id:raise ValueError('Selecione o alvo no grid')
    character=load_character()
    slot='ranged' if spec['weapon']=='arco' else 'melee'
    base=next((a for a in character['definition']['attacks'] if a['id']==slot),None)
    if base is None:raise ValueError('Ataque humanoide indisponível; desative a forma animal ou confira o bônus da ficha')
    bonus=int(base.get('base_attack_bonus',base.get('attack_bonus') or 0))+int(base.get('effect_attack_bonus') or 0)
    damage_bonus=int(base.get('effect_damage_bonus') or 0)
    damage=spec['damage']+(f'{damage_bonus:+d}' if damage_bonus else '')
    attack=dict(id=technique,name=spec['skill']['name'] if skill else spec['name'],attack_bonus=bonus,
                attack_count=int(base.get('attack_count') or 1),
                damage=damage,weapon_item_path='hemomancy:'+technique,hemomancy=True,
                request_target=[request.target_type,request.target_id],command_request_id=request_id)
    definition={**character['definition'],'attacks':[attack]}
    result,_=resolve_attack(path,request_id=request_id,actor_character_id='raziel',actor_name=definition['name'],
        requested_by_id=actor_id,requested_by_role=actor_role,definition=definition,inventory=character.get('inventory') or [],
        attack_id=technique,target=load_target(request.target_type,request.target_id),roll_mode=request.roll_mode or 'digital',physical_d20=request.d20)
    return result
