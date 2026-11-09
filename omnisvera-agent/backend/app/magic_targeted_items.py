"""Reviewed item adapters sharing native grid, HP, effects and inventory receipts."""
import json
import uuid
from .dice_rolls import roll_formula

RAM='item-magico-anel-ariete'
WEB='item-magico-bracelete-do-aracnideo'
REVEAL='item-magico-po-do-aparecimento'
ILLUSION='item-magico-bomba-de-ilusao'
INQUISITOR='item-magico-anel-inquisidor'
SPECS={RAM:{'maximum':3,'slot':'Acessório','consume_mode':'charges','range_m':30},
       WEB:{'maximum':3,'slot':'Acessório','consume_mode':'charges','range_m':9},
       REVEAL:{'maximum':0,'slot':'Acessório','consume_mode':'quantity','range_cells':1}}
SPECS.update({ILLUSION:{'maximum':0,'slot':'Acessório','consume_mode':'quantity','range_cells':1},
              INQUISITOR:{'maximum':0,'slot':'Acessório','consume_mode':'none','range_m':9}})


def range_spec(key):
    spec=SPECS[key]
    return ('touch',None) if spec.get('range_cells') else ('ranged',spec['range_m'])


def checked_options(value):
    if value is None:return {}
    if not isinstance(value,dict) or set(value)-{'target_token_id','charges','map_id','target_cell','expected_grid_version'}:
        raise ValueError('Opções do item inválidas')
    if 'target_token_id' in value and (not isinstance(value['target_token_id'],str) or not 1<=len(value['target_token_id'])<=120):
        raise ValueError('Pin do alvo inválido')
    if 'charges' in value and (type(value['charges']) is not int or not 1<=value['charges']<=3):
        raise ValueError('Use de uma a três cargas')
    cell_keys={'map_id','target_cell','expected_grid_version'}
    if cell_keys.intersection(value):
        if not cell_keys.issubset(value) or 'target_token_id' in value:raise ValueError('Escolha uma célula ou uma criatura, sem misturar alvos')
        if (not isinstance(value['map_id'],str) or not 1<=len(value['map_id'])<=120 or
                type(value['expected_grid_version']) is not int or value['expected_grid_version']<1 or
                not isinstance(value['target_cell'],list) or len(value['target_cell'])!=2 or
                any(type(n) is not int for n in value['target_cell'])):
            raise ValueError('Posição lógica ou versão do grid inválida')
    return value


def compile_item(item):
    key=item.get('id');spec=SPECS.get(key)
    if not spec:return None
    return {'catalog_id':key,'item_type':'accessory','description':item.get('description') or '',
        'damage_formula':None,'effects':[],'usable':True,'thumbnail':item.get('image_path'),
        'effect_rules':[{'id':key+':activate','trigger':'on_use','kind':'magic_activation',
            'value':1,'target':'','duration':'instant','stacking':'non_stack','label':item.get('source') or ''}],
        'mechanics':{'family_schema':1,'family':'magic_activation','kind':'accessory','magical':True,
            'magic_activation_schema':1,'magic_activation_id':key,'activation_mode':'instant',
            'activation_target':'cell' if key==ILLUSION else 'creature','activation_include_self':key in {REVEAL,ILLUSION},
            'activation_variable_charges':key==RAM,'activation_requires_equipped':False,
            'activation_offensive':key in {RAM,WEB},
            'equipment_slots':[spec['slot']],'approved_equipment_slots':[spec['slot']],
            'charges_max':spec['maximum'],'consume_mode':spec['consume_mode'],
            'recharge':'inn_rest' if spec['maximum'] else 'none','family_gaps':[],
            'source':item.get('source_rulebook',{}).get('source') or item.get('source')}}


def selected(db,snapshot,owner,key,options,role):
    """Resolve canonical targets from current persisted cells, never client positions."""
    spec=SPECS[key]
    current=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
    encounter=snapshot.get('encounter') or {}
    map_id=encounter.get('map_id') if encounter.get('active') else current[0] if current else None
    origins=db.execute('SELECT id FROM session_workspace_tokens WHERE character_id=? AND map_id=?',(owner,map_id)).fetchall()
    if len(origins)!=1:raise ValueError('Posicione um único pin do portador no mapa atual')
    token_id=options.get('target_token_id') or (origins[0][0] if key in {REVEAL,ILLUSION} else '')
    row=db.execute('SELECT * FROM session_workspace_tokens WHERE id=? AND map_id=?',(token_id,map_id)).fetchone()
    if not row:raise ValueError('Escolha um alvo no mapa atual')
    row=dict(row)
    from .portable_hole import assert_exterior
    assert_exterior(db,'character',owner)
    assert_exterior(db,'token',row['id'])
    door=json.loads(row['sheet_json'] or '{}').get('door')
    if row['token_type']=='location' and (key!=RAM or not door):raise ValueError('Escolha uma criatura ou uma porta cadastrada para o Aríete')
    if door and door.get('open'):raise ValueError('A porta já está aberta')
    if role!='gm':
        from .monster_runtime import public_token
        if not public_token(db,row['id']):raise PermissionError('Alvo não revelado')
    from .spatial_grid import grid_record,distance_cells
    grid=grid_record(db,map_id)
    if not grid:raise ValueError('Configure o grid lógico antes de usar o item')
    points=[db.execute('SELECT cell_x,cell_y FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',(map_id,t)).fetchone() for t in (origins[0][0],token_id)]
    if not all(points):raise ValueError('Posições lógicas ausentes')
    cells=distance_cells(grid['distance_rule'],points[0],points[1])
    if cells>spec.get('range_cells',float('inf')) or cells*grid['cell_size_m']>spec.get('range_m',float('inf')):
        raise ValueError('Alvo fora do alcance do item')
    from .dorn_spells import target
    victim=None if row['token_type']=='location' else target(db,'character',row['character_id']) if row['character_id'] else target(db,'token',row['id'])
    return row,victim,grid,points[1]


def selected_empty_cell(db,snapshot,owner,options,role):
    """Empty adjacent cells use persisted positions, bounds, fog and grid version."""
    from .spatial_grid import grid_record,distance_cells,visual_position,validate_cell
    from .session_workspace import _token_is_visible
    from .monster_runtime import public_token
    encounter=snapshot.get('encounter') or {}
    current=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
    map_id=encounter.get('map_id') if encounter.get('active') else current[0] if current else None
    if options['map_id']!=map_id:raise ValueError('O mapa mudou; selecione novamente a célula')
    origins=db.execute('SELECT id FROM session_workspace_tokens WHERE character_id=? AND map_id=?',(owner,map_id)).fetchall()
    if len(origins)!=1:raise ValueError('Posicione um único pin do portador no mapa atual')
    if role!='gm' and not public_token(db,origins[0][0]):raise PermissionError('Pin do portador indisponível')
    grid=grid_record(db,map_id)
    if not grid or grid['version']!=options['expected_grid_version']:raise ValueError('O grid mudou; selecione novamente a célula')
    cell=options['target_cell'];validate_cell(grid,cell,1,1)
    origin=db.execute('SELECT cell_x,cell_y FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',(map_id,origins[0][0])).fetchone()
    if not origin or distance_cells(grid['distance_rule'],origin,cell)!=1:raise ValueError('Escolha uma célula vazia adjacente')
    rows=db.execute('SELECT layer,enabled,revealed_cells_json,mist_density_json FROM session_workspace_map_fog WHERE map_id=?',(map_id,)).fetchall()
    if not rows and map_id=='default':rows=db.execute('SELECT layer,enabled,revealed_cells_json,mist_density_json FROM session_workspace_fog').fetchall()
    fog={row[0]:{'enabled':row[1],'revealed_cells':json.loads(row[2]),'mist_density':json.loads(row[3])} for row in rows}
    point=visual_position(grid,{'cell_x':cell[0],'cell_y':cell[1],'footprint_w':1,'footprint_h':1})
    map_row=db.execute('SELECT visible_to_players FROM session_workspace_maps WHERE id=?',(map_id,)).fetchone()
    public=bool(map_row and map_row[0]) and _token_is_visible(point,fog)
    if role!='gm' and not public:raise PermissionError('Célula não revelada neste mapa')
    for row in db.execute('''SELECT p.cell_x,p.cell_y,p.footprint_w,p.footprint_h,t.character_id,t.current_hp
        FROM session_workspace_entity_positions p JOIN session_workspace_tokens t ON p.token_id=t.id
        WHERE p.map_id=? AND t.map_id=p.map_id AND t.token_type!='location' ''',(map_id,)).fetchall():
        hp=row[5]
        if row[4]:
            state=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(row[4],)).fetchone()
            if state:hp=json.loads(state[0]).get('current_hp',hp)
        if hp is not None and hp<=0:continue
        if row[0]<=cell[0]<row[0]+row[2] and row[1]<=cell[1]<row[1]+row[3]:
            raise ValueError('Célula indisponível; escolha outra célula vazia')
    return grid,cell,public


def apply(db,snapshot,owner,key,item,inventory,remaining,now,options,role):
    options=checked_options(options)
    if key in {RAM,WEB}:
        from .monster_conditions import assert_can_act
        from .night_form import require_humanoid
        require_humanoid(db,owner)
        assert_can_act(db,owner)
    if key!=RAM and 'charges' in options:raise ValueError('Este item não permite escolher cargas')
    if 'target_cell' in options and key!=ILLUSION:raise ValueError('Este item exige uma criatura como alvo')
    cost=options.get('charges',1) if key==RAM else 1
    if SPECS[key]['maximum'] and remaining<cost:raise ValueError('Cargas insuficientes')
    from .monster_runtime import public_token
    if key==ILLUSION and 'target_cell' in options:
        grid,pos,public=selected_empty_cell(db,snapshot,owner,options,role)
        pin=victim=None
    else:
        pin,victim,grid,pos=selected(db,snapshot,owner,key,options,role)
        public=public_token(db,pin['id'])
    result={'kind':'magic_activation','magic_item':key,'resolved_value':1,'charges_spent':cost,
            'visibility':'table' if public else 'gm'}
    if key==INQUISITOR:
        if victim['type']=='character':
            raw=db.execute('SELECT data_json FROM character_sheets WHERE profile_id=?',(victim['id'],)).fetchone()
            sheet=json.loads(raw[0]);override=db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?',(victim['id'],)).fetchone()
            if override:sheet.update(json.loads(override[0]))
        else:sheet=json.loads(pin['sheet_json'] or '{}')
        source=None
        if victim['type']=='token':
            from .monster_runtime import token_monster
            source,_=token_monster(db,pin['id'])
        from .magic_capability import resolve
        capability=resolve(sheet,monster=source);capable=capability['value']
        label='possui capacidade mágica' if capable is True else 'sem capacidade mágica' if capable is False else 'capacidade mágica não cadastrada'
        from .session_ledger import append_session_ledger_event
        append_session_ledger_event(db,source_type='magic_detection_notice',source_id=uuid.uuid4().hex,event_kind='action',
            actor_id=owner,actor_name=owner,actor_role=role,character_id=victim['id'] if victim['type']=='character' else None,
            title=f'{owner} usou Anel Inquisidor para identificar sua capacidade mágica',detail={'target_type':victim['type'],'target_id':victim['id']},
            visibility='owner' if victim['type']=='character' else 'gm',created_at=now)
        return [{**result,'label':f"Anel Inquisidor · {pin['name']}: {label}",'magic_capability':capable,'capability_source':capability['source']}]
    if key==ILLUSION:
        rolled=roll_formula('1d4');rounds=int(rolled['total'])
        if not 1<=rounds<=4:raise ValueError('Duração de ilusão inválida')
        effect={'id':'magic-item:'+uuid.uuid4().hex,'target_type':'character','target_id':owner,
            'label':'Ilusão visual','source':item.get('name') or inventory['item_title'],'duration':'fictional_time',
            'rounds':None,'remaining_seconds':10*rounds,'source_duration_unit':'rounds','modifiers':{},
            'magic_item':key,'item_path':item['item_path'],'optical_kind':'illusion',
            'visual_area':{'map_id':grid['map_id'],'cell':list(pos),'x_m':pos[0]*grid['cell_size_m'],'y_m':pos[1]*grid['cell_size_m'],
                'width_m':grid['cell_size_m'],'height_m':grid['cell_size_m']},'updated_at':now}
        db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],'character',owner,json.dumps(effect,ensure_ascii=False)))
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        return [{**result,'label':f'Ilusão visual · {rounds} rodadas','effect_id':effect['id'],'roll':rolled}]
    if key==RAM:
        if pin['token_type']=='location':
            from .map_doors import ram
            return [{**result,**ram(db,pin,cost,roll_formula('1d20'),now,owner=owner,role=role)}]
        roll=roll_formula(str(cost)+'d6');damage=int(roll['total'])
        from .combat_effects import change_hp
        hp=change_hp(db,victim['type'],victim['id'],-damage,now,damage_type='physical',
            damage_context={'kind':'effect','magical':True,'damage_type':'physical'})
        return [{**result,'label':f"Aríete · {pin['name']}: {damage} de dano",'roll':roll,'hp':hp,'damage':damage}]
    if key==REVEAL:
        removed=[]
        for row in db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND ((target_type=? AND target_id=?) OR json_type(data_json,'$.visual_area')='object')",(victim['type'],victim['id'])).fetchall():
            e=json.loads(row[1])
            area=e.get('visual_area')
            if area:
                inside=(list(pos)==area['cell']) if area.get('cell') is not None else (
                    area['x_m']<=pos[0]*grid['cell_size_m']<area['x_m']+area['width_m'] and
                    area['y_m']<=pos[1]*grid['cell_size_m']<area['y_m']+area['height_m'])
                if area['map_id']!=grid['map_id'] or not inside:continue
            if e.get('optical_kind') in {'invisibility','confusion','camouflage','illusion'} or e.get('spell') in {'invisibilidade','ilusao','confusao'}:
                db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(row[0],));removed.append(row[0])
        from .magic_optics import apply as suppress_optics
        suppress_optics(db,victim,now)
        if removed:db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        return [{**result,'label':f"Pó do aparecimento · {pin['name']}: {len(removed)} efeitos removidos; óptica suprimida até descansar",'removed_effects':removed,'optical_suppression':True}]
    # Same environmental web representation/clock/rendering as the existing spell.
    effect={'id':'magic-item:'+uuid.uuid4().hex,'target_type':'character','target_id':owner,
        'label':'Teia','source':item.get('name') or inventory['item_title'],'duration':'fictional_time',
        'rounds':None,'remaining_seconds':7200,'modifiers':{},'magic_item':key,
        'item_path':item['item_path'],'magic_type':'arcane','spell':'teia','spell_circle':2,
        'caster_level':6,'web_area':{'map_id':grid['map_id'],'x_m':pos[0]*grid['cell_size_m'],
            'y_m':pos[1]*grid['cell_size_m'],'width_m':3,'height_m':3,'vertical_m':6},'updated_at':now}
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],'character',owner,json.dumps(effect,ensure_ascii=False)))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return [{**result,'label':'Teia · área 3 × 3 m por duas horas','effect_id':effect['id']}]
