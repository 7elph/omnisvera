"""Approved OD1 additions on native effects, grid, turn budget and receipts."""
import json
from .dice_rolls import roll_formula

SPELLS={'reflexos':'Reflexos','teia':'Teia','forca-arcana':'Força Arcana','dissipar-magia':'Dissipar Magia'}
CIRCLES={'reflexos':2,'teia':2,'forca-arcana':2,'dissipar-magia':3}


def _grid_measurement(db,caster,kind,identity):
    from .spatial_grid import distance_cells
    row=db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()
    encounter=json.loads(row[0] or '{}') if row else {}
    current=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
    map_id=encounter.get('map_id') if encounter.get('active') and encounter.get('map_id') else (current[0] if current else None)
    target=db.execute('SELECT id,map_id FROM session_workspace_tokens WHERE '+('id=?' if kind=='token' else 'character_id=?')+' AND map_id=? ORDER BY id LIMIT 1',(identity,map_id)).fetchone()
    if not target:raise ValueError('Posicione o alvo no grid do mapa atual')
    origin=db.execute('SELECT id FROM session_workspace_tokens WHERE character_id=? AND map_id=? ORDER BY id LIMIT 1',(caster,target[1])).fetchone()
    grid=db.execute('SELECT distance_rule,cell_size_m FROM session_workspace_map_grids WHERE map_id=?',(target[1],)).fetchone()
    if not origin or not grid:raise ValueError('Posicione o conjurador e configure o grid do mapa')
    points=[db.execute('SELECT cell_x,cell_y FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',(target[1],i)).fetchone() for i in [origin[0],target[0]]]
    if not all(points):raise ValueError('Posicoes logicas ausentes')
    return distance_cells(grid[0],points[0],points[1])*grid[1],grid[1]


def grid_distance(db,caster,kind,identity):
    if kind=='character' and identity==caster:return 0
    return _grid_measurement(db,caster,kind,identity)[0]


def command(db,snapshot,payload,now):
    from .dorn_spells import target,add_effect,roll_formula as roll
    from .battle_mode import require_battle_turn,commit_battle_action
    spell=payload['spell_id'];row=db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='dorn7'").fetchone()
    overrides=json.loads(row[0]) if row else {}
    if not str(overrides.get('approved_build') or '').startswith('dorn-mage'):raise ValueError('Ficha aprovada de Dorn necessaria')
    caster=target(db,'character','dorn7');level=int(overrides.get('level') or 3)
    from .action_library import native_action_contract
    from .action_components import require_definition_revision, roll_native_component
    contract = native_action_contract('technique:dorn7:' + spell, level)
    require_definition_revision(payload, contract)
    require_battle_turn(db,snapshot,'dorn7')
    if (snapshot.get('encounter') or {}).get('active') and int((snapshot.get('encounter') or {}).get('attacks_used') or 0):raise ValueError('Conjuracao exige uma acao completa disponivel')
    state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
    key=contract['costs'][0]['key']
    cost=contract['costs'][0]['amount']
    resources=state.setdefault('resources',[])
    resource=next((r for r in resources if r['key']==key),None)
    if resource is None:
        resource={'key':key,'label':SPELLS.get(spell,spell),'current':1,'maximum':1}
        resources.append(resource)
        db.execute("UPDATE character_states SET state_json=?,version=version+1 WHERE profile_id='dorn7'",(json.dumps(state,ensure_ascii=False),))
    if not resource or resource['current']<cost:raise ValueError('Sem preparacao disponivel')
    metadata={'magic_type':'arcane','spell_circle':CIRCLES[spell],'caster_level':level}
    results=[]
    if spell=='reflexos':
        if any(e.get('spell')=='reflexos' for e in snapshot['effects']):raise ValueError('Reflexos ja esta ativo')
        count=roll_native_component(contract['resolution']['images'],roll)
        seconds=roll_native_component(contract['resolution']['lifetime'],roll)
        effect=add_effect(db,caster,spell,seconds,now,images_remaining=count,intercept_chance_percent=contract['resolution']['intercept_chance_percent'],**metadata)
        results=[{'target':caster['name'],'effect':effect}]
    elif spell=='forca-arcana':
        selected=payload.get('targets') or []
        if len(selected)!=1:raise ValueError('Selecione um receptor da Forca Arcana')
        victim=target(db,selected[0]['type'],selected[0]['id'])
        if victim['type']=='character' and victim['id']=='dorn7':
            distance,cell=0,None
        else:
            distance,cell=_grid_measurement(db,'dorn7',selected[0]['type'],selected[0]['id'])
        if victim['type']=='character' and victim['id']=='morthak':raise ValueError('Forca Arcana exige alvo vivo; Dorn e excecao aprovada')
        if victim['type']=='token':
            raw=db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(victim['id'],)).fetchone()[0]
            sheet=json.loads(raw or '{}')
            if sheet.get('is_undead') or sheet.get('construct_traits') or sheet.get('summon',{}).get('technique') in {'levantar-esqueleto','animar-mortos'}:raise ValueError('Forca Arcana exige alvo vivo')
        if distance>0:
            if distance>cell*contract['range']['cells']:raise ValueError('Forca Arcana exige alvo adjacente')
        original=int(victim['attributes'].get('strength') or 0)
        if original<1:raise ValueError('Forca original ausente ou invalida')
        if any(e.get('spell')==spell and e['target_type']==victim['type'] and e['target_id']==victim['id'] for e in snapshot['effects']):raise ValueError('Forca Arcana ja esta ativa neste receptor')
        effect=add_effect(db,victim,spell,roll_native_component(contract['resolution']['lifetime'],roll),now,original_strength=original,**metadata)
        effect['modifiers']={'strength_bonus':original//contract['resolution']['strength_divisor']}
        db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),effect['id']))
        results=[{'target':victim['name'],'effect':effect}]
    elif spell=='dissipar-magia':
        from .spell_effect_runtime import resolve_dispel_effect,effect_distance
        effect=resolve_dispel_effect(db,snapshot,payload)
        circle,source_level=effect['spell_circle'],effect['caster_level']
        distance=effect_distance(db,snapshot,effect)
        if distance>contract['range']['meters']:raise ValueError('Efeito fora do alcance de Dissipar Magia')
        check=contract['resolution']['check']
        total=roll_native_component(check,roll);die=total-check['add']
        difficulty=contract['resolution']['difficulty']['base']+circle+source_level;success=total>=difficulty
        if success:db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(effect['id'],))
        results=[{'target':effect['label'],'d20':die,'total':total,'difficulty':difficulty,'success':success}]
        from .session_ledger import append_session_ledger_event
        from .monster_runtime import public_token
        import uuid
        public=public_token(db,payload['target_token_id']) if payload.get('target_token_id') else effect['target_type']=='character'
        append_session_ledger_event(db,source_type='spell_resolution',source_id='dispel:'+uuid.uuid4().hex,event_kind='roll',
            actor_id='dorn7',actor_name='Unidade DORN-7',actor_role='gm',character_id='dorn7',
            title=f"Dissipar Magia · {effect['label']}: d20 {die} + {check['add']} = {total} contra {difficulty} · "+('dissipada' if success else 'resistiu'),
            detail={'ability_id':'dissipar-magia','d20':die,'total':total,'difficulty':difficulty,'success':success,'effect_id':effect['id']},
            visibility='table' if public else 'gm',created_at=now)

    else:
        results=cast_web(db,snapshot,payload,now,level,metadata,contract)
    from .action_components import spend_native_resource
    remaining=spend_native_resource(db,'dorn7',key,cost,now)
    commit_battle_action(db,snapshot)
    return {'spell':SPELLS[spell],'results':results,'resource_remaining':remaining,
            **({'action_contract':{'ref':contract['ref'],'revision':contract['revision'],'level':level}} if contract else {})}


def redirect_hits(db,kind,identity,strikes,now,area=False):
    amount=sum(int(s.get('damage_total') or 0) for s in strikes)
    if area:
        return amount,{}
    row=db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.spell')='reflexos'",(kind,identity)).fetchone()
    if not row:
        return amount,{}
    effect=json.loads(row[1])
    remaining=int(effect.get('images_remaining') or 0)
    redirected=[]
    for index,strike in enumerate(strikes):
        if remaining<1:
            continue
        if strike.get('result')!='hit':
            continue
        # natural20 of player marked unavoidable ignores reflexos
        if strike.get('unavoidable'):
            continue
        # Reflexos: 90% interception (1d10 <= 9)
        die_roll=roll_formula('1d10')
        die=int(die_roll.get('total') or 0)
        intercepted = die*10 <= int(effect.get('intercept_chance_percent',90))  # persisted cast contract; legacy campaign default
        if intercepted:
            remaining-=1
            amount -= int(strike.get('damage_total') or 0)
        redirected.append({'strike':index,'die':die,'intercepted':intercepted})
    effect['images_remaining']=remaining
    effect['updated_at']=now
    db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?',(json.dumps(effect),int(remaining>0),effect['id']))
    if redirected:
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return amount,{'images_remaining':remaining,'rolls':redirected,'effect_id':effect['id']}


def cast_web(db,snapshot,payload,now,level,metadata,contract=None):
    from .dorn_spells import target,add_effect
    if contract is None:
        from .action_library import native_action_contract
        contract=native_action_contract('technique:dorn7:teia',level)
    selected=payload.get('targets') or []
    if len(selected)!=1 or selected[0]['type']!='token':raise ValueError('Escolha um pin para marcar a celula inicial da area de Teia')
    anchor=db.execute('SELECT map_id FROM session_workspace_tokens WHERE id=?',(selected[0]['id'],)).fetchone()
    if not anchor:raise ValueError('Pin de area nao encontrado')
    if grid_distance(db,'dorn7','token',selected[0]['id'])>contract['range']['meters']:raise ValueError('Area fora do alcance de Teia')
    pos=db.execute('SELECT cell_x,cell_y FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',(anchor[0],selected[0]['id'])).fetchone()
    grid=db.execute('SELECT cell_size_m FROM session_workspace_map_grids WHERE map_id=?',(anchor[0],)).fetchone()
    if not pos or not grid:raise ValueError('Area precisa de grid logico')
    effect=add_effect(db,target(db,'character','dorn7'),'teia',contract['resolution']['lifetime_seconds'],now,web_area={'map_id':anchor[0],'x_m':pos[0]*grid[0],'y_m':pos[1]*grid[0],**contract['resolution']['dimensions']},**metadata)
    return [{'target':'Area 3 x 3 m; altura 6 m','effect':effect}]


def in_web(area,map_id,x,y,w,h,scale):
    return map_id==area['map_id'] and x*scale<area['x_m']+area['width_m'] and (x+w)*scale>area['x_m'] and y*scale<area['y_m']+area['height_m'] and (y+h)*scale>area['y_m']


def expand_web_effects(db,effects):
    areas=[e for e in effects if e.get('web_area')]
    if not areas:return effects
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='session_workspace_state'").fetchone():
        current=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
        if current:
            areas=[e for e in areas if e['web_area']['map_id']==current[0]]
    result=list(effects);seen=set()
    has_states=bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='character_states'").fetchone())
    for area in areas:
        records=db.execute("SELECT t.id,t.character_id,p.cell_x,p.cell_y,p.footprint_w,p.footprint_h,g.cell_size_m FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id JOIN session_workspace_map_grids g ON g.map_id=t.map_id WHERE t.map_id=? AND t.token_type!='location' AND (t.character_id IS NOT NULL OR t.current_hp>0)",(area['web_area']['map_id'],)).fetchall()
        for identity,character,x,y,w,h,scale in records:
            if character and has_states:
                state=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(character,)).fetchone()
                if not state or int(json.loads(state[0]).get('current_hp') or 0)<=0:continue
            kind,target=('character',character) if character else ('token',identity)
            if (kind,target) in seen or not in_web(area['web_area'],area['web_area']['map_id'],x,y,w,h,scale):continue
            seen.add((kind,target))
            result.append({**area,'id':area['id']+':occupant:'+target,'target_type':kind,'target_id':target,'label':'Teia','duration':'derived','rounds':None,'environmental':True,'web_parent_id':area['id'],'modifiers':{'armor_class_bonus':-2},'web_area':None})
    return result


def web_step_multiplier(db,map_id,cell):
    grid=db.execute('SELECT cell_size_m FROM session_workspace_map_grids WHERE map_id=?',(map_id,)).fetchone()
    for raw, in db.execute("SELECT data_json FROM combat_effects WHERE active=1 AND json_type(data_json,'$.web_area')='object'"):
        area=json.loads(raw)['web_area']
        if grid and in_web(area,map_id,cell[0],cell[1],1,1,grid[0]):return 3
    return 1
