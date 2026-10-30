"""Approved Oct24 composition; uses native effects, turns, resources and receipts."""
import json,sqlite3
from .dice_rolls import roll_formula

def effects(db):
    return [json.loads(r[0]) for r in db.execute("SELECT data_json FROM combat_effects WHERE active=1 AND target_id='raziel'")]

def _save(db,effect):
    db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect,ensure_ascii=False),effect['id']))

def _progress(db,map_id,now):
    from .hemomancy import _put
    return next((e for e in effects(db) if e.get('hemomancy_kind')=='pipeline' and e.get('map_id')==map_id),None) or _put(db,'pipeline','Sequências de Hemomancia',now,map_id=map_id,flags={})

def progress(db,map_id,now,**flags):
    from .hemomancy import _put
    effect=_progress(db,map_id,now);effect['flags'].update(flags)
    if effect['flags'].get('rupture_complete') and effect['flags'].get('mark_complete') and not effect['flags'].get('convergence_unlocked'):
        effect['flags']['convergence_unlocked']=True
        _put(db,'convergence','Convergência Rubra',now,map_id=map_id)
    _save(db,effect)

def command(db,snapshot,now,payload):
    from .night_form import require_humanoid
    from .battle_mode import require_battle_turn
    from .action_components import spend_native_resource
    from .hemomancy import _put,_map_id
    require_humanoid(db,'raziel');require_battle_turn(db,snapshot,'raziel',auxiliary=True)
    skill=payload.get('skill');map_id=_map_id(db,snapshot)
    if skill=='reforco':
        mode=payload.get('mode')
        if mode not in ('x1','x2','x3'):raise ValueError('Escolha x1, x2 ou x3')
        multiplier=int(mode[1:]);active=next((e for e in effects(db) if e.get('hemomancy_kind')=='boost'),None)
        if multiplier==1:
            if active:db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(active['id'],))
            return {'spell':'Reforço x1','multiplier':1}
        if active:raise ValueError('Reforço já ativo; aguarde acabar ou volte a x1 (sem reembolso)')
        remaining=spend_native_resource(db,'raziel','reserva_de_sangue',multiplier,now)
        encounter=snapshot.get('encounter') or {}
        effect=_put(db,'boost',f'Reforço x{multiplier}',now,map_id=map_id,duration='manual',multiplier=multiplier,turns_remaining=2,
            has_started=bool(encounter.get('active')),last_sequence=encounter.get('turn_sequence'))
        return {'spell':f'Reforço x{multiplier}','effect':effect,'blood_remaining':remaining}
    if skill!='velocidade':raise ValueError('Poder de Raziel desconhecido')
    if any(e.get('skill')=='raziel_speed' for e in effects(db)):raise ValueError('Velocidade já ativa')
    row=db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone();state=json.loads(row[0])
    resource=next((r for r in state.get('resources',[]) if r['key']=='velocidade'),None)
    if resource is None:
        state.setdefault('resources',[]).append(dict(key='velocidade',label='Velocidade',current=1,maximum=1,recharge='inn_rest'))
        db.execute("UPDATE character_states SET state_json=?,version=version+1 WHERE profile_id='raziel'",(json.dumps(state),))
    spend_native_resource(db,'raziel','velocidade',1,now)
    row=db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='raziel'").fetchone()
    level=int(json.loads(row[0]).get('level') or 5) if row else 5
    effect=_put(db,'speed','Velocidade',now,map_id=map_id,skill='raziel_speed',duration='rounds',rounds=int(roll_formula('1d4')['total'])+level,
        modifiers={'extra_attacks':1,'movement_multiplier':2,'armor_class_bonus':2})
    return {'spell':'Velocidade','effect':effect}

def attack_context(db,actor_id):
    if actor_id!='raziel':return {}
    active=effects(db)
    boost=next((e for e in active if e.get('hemomancy_kind')=='boost'),{})
    conditional=next((e for e in active if e.get('hemomancy_kind')=='convergence'),{})
    return {'multiplier':int(boost.get('multiplier') or 1),'boost_id':boost.get('id'),'conditional_id':conditional.get('id')}

def roll_attack(strike,context,rng):
    if not context:return
    if context.get('conditional_id') and strike['result']=='hit':
        extra=roll_formula('1d6',rng);strike['damage_total']+=extra['total'];strike['damage_rolls']+=extra['individual_results']
        strike['pipeline_bonus_roll']=extra
    multiplier=context.get('multiplier',1)
    strike['unmultiplied_damage']=strike['damage_total']
    strike['damage_total']*=multiplier
    if strike.get('fumble_damage'):strike['fumble_damage']*=multiplier
    if multiplier!=1:strike['damage_multiplier']=multiplier

def confirmed(db,record,hp_change,now):
    if record['actor_character_id']!='raziel':return
    context=record['breakdown'].get('raziel_pipeline') or {}
    if context.get('conditional_id'):db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(context['conditional_id'],))
    meta=record['breakdown'].get('hemomancy') or {}
    if not meta or not hp_change.get('damage_taken'):return
    flags={}
    if meta['weapon']=='marreta':flags['exposed_applied']=True
    if meta['weapon']=='foice' and meta['skill']:flags['bleed_applied']=True
    effect=next((e for e in effects(db) if e.get('hemomancy_kind')=='pipeline' and e.get('map_id')==meta['map_id']),{'flags':{}})
    if meta['weapon']=='lanca' and meta.get('exposed_id') and meta.get('bleeding') and effect['flags'].get('exposed_applied') and effect['flags'].get('bleed_applied'):
        flags['rupture_complete']=True
    if meta['weapon']=='arco' and meta['skill'] and meta.get('marked'):flags['bow_ready']=True
    if flags:progress(db,meta['map_id'],now,**flags)

def after_shield(db,map_id,now):
    from .hemomancy import _put
    effect=next((e for e in effects(db) if e.get('hemomancy_kind')=='pipeline' and e.get('map_id')==map_id),None)
    if effect and effect['flags'].get('bow_ready'):
        _put(db,'revenge','Revanche Rubra',now,map_id=map_id)
        progress(db,map_id,now,bow_ready=False,mark_complete=True)

def turn_start(db,participant,encounter,now,request_id):
    if not participant or (participant['target_type'],participant['target_id'])!=('character','raziel'):return
    for effect in effects(db):
        if effect.get('hemomancy_kind')!='boost':continue
        sequence=encounter.get('turn_sequence')
        if effect.get('has_started') and effect.get('last_sequence')!=sequence:effect['turns_remaining']-=1
        effect.update(has_started=True,last_sequence=sequence)
        db.execute('UPDATE combat_effects SET active=?,data_json=? WHERE id=?',(int(effect['turns_remaining']>0),json.dumps(effect),effect['id']))

def cross_mark(db,snapshot,now,payload,request_id,role):
    from .hemomancy import _range,_map_id,_put,_hp
    from .night_form import require_humanoid
    from .battle_mode import require_battle_turn
    from .action_components import spend_native_resource
    from .combat import _require_blood_target
    from .session_workspace import _token_is_visible
    require_humanoid(db,'raziel');require_battle_turn(db,snapshot,'raziel',auxiliary=True)
    if (snapshot.get('encounter') or {}).get('action_committed'):raise ValueError('A ação do turno já foi confirmada; passe o turno')
    kind,identity=payload.get('target_type'),payload.get('target_id');map_id=_map_id(db,snapshot)
    if kind not in ('character','token') or not identity:raise ValueError('Selecione o centro da Marca Rubra no grid')
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='session_workspace_entity_positions'").fetchone():raise ValueError('Marca Rubra exige o grid do mapa')
    _require_blood_target(db,kind,identity)
    if _hp(db,kind,identity)[0]<=0:raise ValueError('Selecione um inimigo vivo para o centro da Marca Rubra')
    factory=db.row_factory
    try:
        db.row_factory=sqlite3.Row
        _range(db,snapshot,{'range_m':9},{'type':kind,'id':identity},role)
    finally:db.row_factory=factory
    center=db.execute('SELECT p.cell_x,p.cell_y FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id WHERE t.map_id=? AND '+('t.id=?' if kind=='token' else 't.character_id=?')+' ORDER BY t.id LIMIT 1',(map_id,identity)).fetchone()
    if not center:raise ValueError('Centro da Marca Rubra fora do grid')
    cells=[[center[0]+dx,center[1]+dy] for dx,dy in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]]
    bounds=db.execute('SELECT cols,rows FROM session_workspace_map_grids WHERE map_id=?',(map_id,)).fetchone()
    cells=[c for c in cells if 0<=c[0]<bounds[0] and 0<=c[1]<bounds[1]]
    fog={}
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='session_workspace_map_fog'").fetchone():
        for row in db.execute('SELECT * FROM session_workspace_map_fog WHERE map_id=?',(map_id,)):
            # Native helper consumes the saved native fog records, not inferred visibility.
            names=[c[1] for c in db.execute('PRAGMA table_info(session_workspace_map_fog)')];value=dict(zip(names,row))
            value['revealed_cells']=json.loads(value.get('revealed_cells_json') or '[]')
            value['mist_density']=json.loads(value.get('mist_density_json') or '{}')
            if 'layer' in value:fog[value['layer']]=value
    targets=[]
    for row in db.execute('SELECT t.id,t.character_id,t.token_type,t.visible_to_players,t.latitude,t.longitude,t.sheet_json,p.cell_x,p.cell_y FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id WHERE t.map_id=?',(map_id,)).fetchall():
        token,char,token_type,visible,lat,lon,raw,x,y=row;sheet=json.loads(raw or '{}')
        if [x,y] not in cells or token_type!='monster' or char or sheet.get('summon') or 'aliado' in str(sheet.get('role','')).lower():continue
        if role!='gm' and not _token_is_visible({'visible_to_players':bool(visible),'token_type':token_type,'latitude':lat,'longitude':lon},fog):continue
        try:
            _require_blood_target(db,'token',token)
            if _hp(db,'token',token)[0]<=0:continue
        except ValueError:continue
        targets.append(token)
    if identity not in targets:raise ValueError('Centro da Marca Rubra indisponível: escolha um inimigo vivo com sangue e visível')
    if not targets:raise ValueError('Nenhum inimigo vivo com sangue na cruz de Marca Rubra')
    remaining=spend_native_resource(db,'raziel','reserva_de_sangue',1,now)
    selected=[_put(db,'mark','Marca Rubra',now,target_type='token',target_id=token,map_id=map_id,source='Marca Rubra (Lâminas de Sangue)') for token in targets]
    progress(db,map_id,now,mark_applied=True)
    return {'effects':selected,'effect':selected[0],'blood_remaining':remaining,'area_cells':cells,'center':list(center),'spell':'Marca Rubra'}
