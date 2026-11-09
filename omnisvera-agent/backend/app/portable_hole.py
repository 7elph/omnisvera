"""Voluntary pocket occupancy references native actors/pins and movement budget.

The condition on the inventory instance is authoritative. Portal pins expose no
inventory contents; containment survives rest and client reloads.
"""
import json
import sqlite3
from contextlib import closing
from .inventory_conditions import read_condition, save_condition
from .character_play import _now


def occupants_by_identity(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='inventory_item_conditions'").fetchone():return {}
    rows=db.execute("SELECT c.inventory_id,j.value FROM inventory_item_conditions c,json_each(c.data_json,'$.magic_container.occupants') j").fetchall()
    return {(o['type'],o['id']):inventory_id for inventory_id,raw in rows for o in [json.loads(raw)]}


def contained(db,kind,identity):
    occupants=occupants_by_identity(db)
    if not occupants:return None
    from .monster_conditions import _canonical
    kind,identity=_canonical(db,kind,identity)
    return occupants.get((kind,identity))


def assert_exterior(db,kind,identity):
    if contained(db,kind,identity) is not None:raise ValueError('Dentro do Buraco Portátil: saia antes de agir no mapa')


def assert_actor_exterior(db,identity):
    assert_exterior(db,'character',identity)
    assert_exterior(db,'token',identity)


def protect_quantity(db,inventory_id,quantity):
    condition=read_condition(db,inventory_id) or {}
    if (condition.get('magic_container') or {}).get('occupants') and quantity!=1:
        raise ValueError('Retire os ocupantes antes de remover ou duplicar o Buraco Portátil')


def protect_pin(db,token_id):
    row=db.execute('SELECT character_id,sheet_json FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()
    if not row:return
    assert_exterior(db,'character' if row[0] else 'token',row[0] or token_id)
    portal=json.loads(row[1] or '{}').get('portable_hole')
    if portal:
        condition=read_condition(db,portal['inventory_id']) or {}
        if (condition.get('magic_container') or {}).get('occupants'):raise ValueError('Retire os ocupantes antes de apagar o portal')


def source(inventory_id):return 'portable-hole:'+str(inventory_id)


def sync_open(db,row,state,now):
    """Opening without a positioned holder preserves legacy item-only storage."""
    from .environment_breathing import begin,stop
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='session_workspace_entity_positions'").fetchone():
        return  # Legacy item storage without a grid remains usable.
    portal=state.get('portal_id') or 'location:portable-hole:'+str(row['id'])
    existing=db.execute('SELECT id FROM session_workspace_tokens WHERE id=?',(portal,)).fetchone()
    if state['open']:
        stop(db,source(row['id']))
        if (not existing or state.get('air_started')) and contained(db,'character',row['profile_id']) is None:
            current=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
            clock=db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()
            encounter=json.loads(clock[0]) if clock else {}
            map_id=encounter.get('map_id') if encounter.get('active') else current[0] if current else None
            pin=db.execute('''SELECT t.*,p.cell_x,p.cell_y FROM session_workspace_tokens t
                JOIN session_workspace_entity_positions p ON t.id=p.token_id AND t.map_id=p.map_id
                WHERE t.character_id=? AND t.map_id=?''',(row['profile_id'],map_id)).fetchone()
            if pin:
                state['portal_id']=portal
                if existing:
                    db.execute('UPDATE session_workspace_tokens SET map_id=?,visible_to_players=?,latitude=?,longitude=?,updated_at=? WHERE id=?',
                        (map_id,pin['visible_to_players'],pin['latitude'],pin['longitude'],now,portal))
                    db.execute('INSERT INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y) VALUES(?,?,?,?) ON CONFLICT(map_id,token_id) DO UPDATE SET cell_x=excluded.cell_x,cell_y=excluded.cell_y,version=version+1',
                        (map_id,portal,pin['cell_x'],pin['cell_y']))
                    state['portal_visible']=bool(pin['visible_to_players']);state['air_started']=False
                    return
                db.execute('''INSERT INTO session_workspace_tokens(id,token_type,map_id,character_id,name,image_path,visible_to_players,color,
                    latitude,longitude,current_hp,maximum_hp,conditions_json,sheet_json,created_at,updated_at)
                    VALUES(?,'location',?,NULL,'Buraco Portátil',NULL,?,'#6486a6',?,?,NULL,NULL,'[]',?,?,?)''',
                    (portal,map_id,pin['visible_to_players'],pin['latitude'],pin['longitude'],json.dumps({'portable_hole':{'inventory_id':row['id']},'marker':'◉'}),now,now))
                db.execute('INSERT INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y) VALUES(?,?,?,?)',
                    (map_id,portal,pin['cell_x'],pin['cell_y']))
                state['portal_visible']=bool(pin['visible_to_players'])
        else:
            db.execute('UPDATE session_workspace_tokens SET visible_to_players=?,updated_at=? WHERE id=?',(int(state.get('portal_visible',False)),now,portal))
    else:
        db.execute('UPDATE session_workspace_tokens SET visible_to_players=0,updated_at=? WHERE id=?',(now,portal))
        # Repeated close cannot replenish the same air supply.
        if not state.get('air_started'):
            for occupant in state.get('occupants',[]):begin(db,occupant['type'],occupant['id'],source(row['id']),60,now)
    state['air_started']=not state['open']


def _read(db,portal_id,actor,role,token_id):
    pin=db.execute('SELECT * FROM session_workspace_tokens WHERE id=?',(portal_id,)).fetchone()
    if not pin:raise ValueError('Buraco Portátil não encontrado')
    portal=json.loads(pin['sheet_json'] or '{}').get('portable_hole')
    if not portal:raise ValueError('Este pin não é um Buraco Portátil')
    row=db.execute('SELECT * FROM player_inventory WHERE id=? AND quantity=1',(portal['inventory_id'],)).fetchone()
    if not row:raise ValueError('Instância do recipiente indisponível')
    condition=read_condition(db,row['id']) or {};state=condition.get('magic_container') or {}
    who=db.execute('SELECT * FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()
    if not who or who['token_type']=='location':raise ValueError('Selecione um personagem ou invocação')
    if role not in {'gm','player'}:raise PermissionError('Acesso inválido')
    summon=json.loads(who['sheet_json'] or '{}').get('summon') or {}
    if role!='gm' and who['character_id']!=actor and summon.get('caster')!=actor:
        raise PermissionError('Só é possível declarar entrada voluntária da própria entidade')
    identity=('character',who['character_id']) if who['character_id'] else ('token',who['id'])
    inside=any((o['type'],o['id'])==identity for o in state.get('occupants',[]))
    if role!='gm' and not inside:
        from .monster_runtime import public_token
        if not public_token(db,portal_id) or not public_token(db,token_id):raise PermissionError('Local indisponível')
    return pin,row,condition,state,who,identity,inside


def portal_view(path,*,portal_id,actor,role,token_id):
    with closing(sqlite3.connect(path)) as db:
        db.row_factory=sqlite3.Row
        pin,row,condition,state,who,identity,inside=_read(db,portal_id,actor,role,token_id)
        version=db.execute('SELECT version FROM combat_effect_clock WHERE id=1').fetchone()[0]
        return {'portal_id':portal_id,'token_id':who['id'],'version':condition.get('version',0),'combat_version':version,
            'open':bool(state.get('open')),'inside':inside,'movement_cost_m':3}


def character_pin(path,portal_id,character_id):
    with closing(sqlite3.connect(path)) as db:
        row=db.execute('''SELECT t.id FROM session_workspace_tokens t JOIN session_workspace_tokens p ON p.id=?
            WHERE t.character_id=? ORDER BY (t.map_id=p.map_id) DESC,t.id LIMIT 1''',(portal_id,character_id)).fetchone()
        if not row:raise ValueError('Personagem sem pin cadastrado')
        return row[0]


def _move_budget(db,snapshot,identity,speed,mode,map_id):
    from .spatial_grid import current_participant,spend_movement
    encounter=snapshot.get('encounter') or {}
    if not encounter.get('active'):return None
    if encounter.get('map_id')!=map_id:raise ValueError('Interação fora do mapa de combate')
    current=current_participant(encounter)
    if not current or identity!=(current['target_type'],current['target_id']):raise ValueError('Aguarde o turno desta entidade')
    if encounter.get('pending_attack'):raise ValueError('Conclua o ataque pendente antes de se deslocar')
    budget=spend_movement(encounter,current,speed,3,mode)
    db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
    return budget


def command(path,*,portal_id,actor,role,request_id,payload,load_movement=None):
    if (set(payload)!={'operation','token_id','expected_version','expected_combat_version'} or
            payload['operation'] not in {'enter','exit','extract'} or not isinstance(payload['token_id'],str) or
            any(type(payload[k]) is not int or payload[k]<0 for k in ('expected_version','expected_combat_version'))):
        raise ValueError('Comando de entrada ou saída inválido')
    if not isinstance(request_id,str) or not 8<=len(request_id)<=120:raise ValueError('Informe uma chave idempotente')
    from .spatial_grid import connect,replay,finish_command,grid_record,distance_cells,visual_position
    from .monster_movement import selected_movement,movement_modes
    fp=json.dumps(['portable_hole',portal_id,actor,role,payload],sort_keys=True)
    # Native character building can initialize modules: keep it outside the writer.
    with closing(connect(path)) as db:
        cached=replay(db,request_id,fp)
        if cached is not None:return cached
        *_,who,identity,inside=_read(db,portal_id,actor,role,payload['token_id'])
        from .summon_profiles import complete_sheet
        raw=load_movement(who['character_id']) if who['character_id'] and load_movement else complete_sheet(json.loads(who['sheet_json'] or '{}')).get('movement')
        clock=db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()
        encounter=json.loads(clock[0]) if clock else {}
        previous=encounter.get('movement') or {}
        from .spatial_grid import turn_key,current_participant
        current=current_participant(encounter)
        used=bool(current and previous.get('turn_key')==turn_key(encounter,current) and previous.get('spent_m'))
        modes=movement_modes(raw) if raw is not None else {}
        mode=previous.get('mode','walk') if used else 'walk' if 'walk' in modes else next(iter(modes),'walk')
        speed=selected_movement(raw,mode) if encounter.get('active') and raw is not None else None
    with closing(connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        cached=replay(db,request_id,fp)
        if cached is not None:return cached
        pin,row,condition,state,who,identity,inside=_read(db,portal_id,actor,role,payload['token_id'])
        from .combat_effects import effect_snapshot
        snapshot=effect_snapshot(db)
        if role!='gm':
            selected=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
            current_map=snapshot['encounter'].get('map_id') if snapshot.get('encounter',{}).get('active') else selected[0] if selected else None
            if pin['map_id']!=current_map:raise ValueError('Use um portal no mapa atual')
        if condition.get('version',0)!=payload['expected_version'] or snapshot['version']!=payload['expected_combat_version']:
            raise ValueError('O recipiente ou turno mudou; atualize antes de confirmar')
        if not state.get('open'):raise ValueError('O Buraco Portátil está fechado')
        from .monster_runtime import public_token
        if role!='gm' and not public_token(db,portal_id):raise PermissionError('Portal indisponível neste mapa')
        if inside!=(payload['operation']!='enter'):raise ValueError('A entidade já está dentro' if inside else 'A entidade está fora')
        extracting=payload['operation']=='extract'
        if extracting and role!='gm':raise PermissionError('Só o Mestre retira ocupantes administrativamente')
        if extracting and snapshot.get('encounter',{}).get('active'):raise ValueError('Retirada administrativa somente fora de combate')
        from .monster_conditions import assert_can_act
        from .battle_mode import require_actor_alive
        if not extracting:
            require_actor_alive(db,identity[1]);assert_can_act(db,identity[1],noncombat=True)
        grid=grid_record(db,pin['map_id'])
        pp=db.execute('SELECT * FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',(pin['map_id'],portal_id)).fetchone()
        pos=db.execute('SELECT * FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',(who['map_id'],who['id'])).fetchone()
        if not grid or not pp or not pos:raise ValueError('Posicione o portal e a entidade no grid')
        now=_now();occupants=state.setdefault('occupants',[])
        from .environment_breathing import stop
        if payload['operation']=='enter':
            if contained(db,*identity) is not None:raise ValueError('A entidade já está em outro recipiente')
            if pin['map_id']!=who['map_id'] or distance_cells(grid['distance_rule'],[pp['cell_x'],pp['cell_y']],[pos['cell_x'],pos['cell_y']])>1:
                raise ValueError('Aproxime-se de uma célula adjacente ao Buraco Portátil')
            from .magic_item_drums import validate_path
            validate_path(db,pin['map_id'],who['id'],[[pos['cell_x'],pos['cell_y']],[pp['cell_x'],pp['cell_y']]])
            if pos['footprint_w']>1 or pos['footprint_h']>1:raise ValueError('Criatura grande: medidas físicas da abertura exigem revisão')
            for raw in snapshot['effects']:
                if (raw.get('target_type'),raw.get('target_id'))==identity and raw.get('immobilized'):raise ValueError('Entidade imobilizada não pode entrar')
            occupants.append({'type':identity[0],'id':identity[1],'name':who['name'],'token_id':who['id']})
        else:
            # Exit to an available adjacent cell. Saved positions on other maps remain.
            fog={}
            if role!='gm':
                fog_rows=db.execute('SELECT layer,enabled,revealed_cells_json,mist_density_json FROM session_workspace_map_fog WHERE map_id=?',(pin['map_id'],)).fetchall()
                if not fog_rows and pin['map_id']=='default':fog_rows=db.execute('SELECT layer,enabled,revealed_cells_json,mist_density_json FROM session_workspace_fog').fetchall()
                fog={r[0]:{'enabled':bool(r[1]),'revealed_cells':json.loads(r[2]),'mist_density':json.loads(r[3])} for r in fog_rows}
            from .session_workspace import _token_is_visible
            def revealed(x,y):
                return role=='gm' or _token_is_visible({'visible_to_players':True,**visual_position(grid,{'cell_x':x,'cell_y':y,'footprint_w':1,'footprint_h':1})},fog)
            occupied=set()
            for p in db.execute('''SELECT p.cell_x,p.cell_y,p.footprint_w,p.footprint_h,t.id,t.character_id,t.token_type FROM session_workspace_entity_positions p
                JOIN session_workspace_tokens t ON t.id=p.token_id AND t.map_id=p.map_id WHERE p.map_id=?''',(pin['map_id'],)):
                if p['token_type']=='location' or contained(db,'character' if p['character_id'] else 'token',p['character_id'] or p['id']) is not None:continue
                occupied.update((x,y) for x in range(p['cell_x'],p['cell_x']+p['footprint_w']) for y in range(p['cell_y'],p['cell_y']+p['footprint_h']))
            cell=next(([pp['cell_x']+dx,pp['cell_y']+dy] for dx,dy in [(0,0),(0,1),(1,0),(0,-1),(-1,0),(1,1),(-1,-1),(-1,1),(1,-1)]
                if 0<=pp['cell_x']+dx<grid['cols'] and 0<=pp['cell_y']+dy<grid['rows'] and (pp['cell_x']+dx,pp['cell_y']+dy) not in occupied and revealed(pp['cell_x']+dx,pp['cell_y']+dy)),None)
            if cell is None:raise ValueError('Não há célula disponível para sair')
            destination_id=who['id']
            if who['map_id']!=pin['map_id']:
                if who['character_id']:
                    saved=db.execute('SELECT id FROM session_workspace_tokens WHERE character_id=? AND map_id=?',(who['character_id'],pin['map_id'])).fetchall()
                    if len(saved)>1:raise ValueError('Há pins duplicados da ficha neste mapa; revise antes de sair')
                    destination_id=saved[0][0] if saved else ('character:'+who['character_id'] if pin['map_id']=='default' else 'character:'+pin['map_id']+':'+who['character_id'])
                    if not saved:
                        db.execute('''INSERT INTO session_workspace_tokens(id,token_type,map_id,character_id,name,image_path,visible_to_players,color,
                            latitude,longitude,current_hp,maximum_hp,conditions_json,sheet_json,created_at,updated_at)
                            SELECT ?,token_type,?,character_id,name,image_path,visible_to_players,color,latitude,longitude,current_hp,maximum_hp,conditions_json,sheet_json,?,?
                            FROM session_workspace_tokens WHERE id=?''',(destination_id,pin['map_id'],now,now,who['id']))
                else:db.execute('UPDATE session_workspace_tokens SET map_id=? WHERE id=?',(pin['map_id'],who['id']))
            point=visual_position(grid,{'cell_x':cell[0],'cell_y':cell[1],'footprint_w':1,'footprint_h':1})
            db.execute('UPDATE session_workspace_entity_positions SET cell_x=?,cell_y=?,version=version+1 WHERE map_id=? AND token_id=?',(*cell,pin['map_id'],destination_id))
            db.execute('UPDATE session_workspace_tokens SET latitude=?,longitude=?,updated_at=? WHERE id=?',(point['latitude'],point['longitude'],now,destination_id))
            occupants[:]=[o for o in occupants if (o['type'],o['id'])!=identity]
            stop(db,source(row['id']),*identity)
        budget=None if extracting else _move_budget(db,snapshot,identity,speed,mode,pin['map_id'])
        save_condition(db,row['id'],{**condition,'magic_container':state},now)
        db.execute('UPDATE player_inventory SET updated_at=? WHERE id=?',(now,row['id']))
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        from .session_ledger import append_session_ledger_event
        ledger=append_session_ledger_event(db,source_type='portable_hole',source_id=request_id,event_kind='action',
            actor_id=actor,actor_name=who['name'],actor_role=role,character_id=who['character_id'],
            title=f"{who['name']} "+('entrou no' if payload['operation']=='enter' else 'saiu do')+' Buraco Portátil',
            detail={'operation':payload['operation'],'token_id':who['id'],'movement':budget},visibility='table' if public_token(db,portal_id) and public_token(db,who['id']) else 'gm',created_at=now)
        return finish_command(db,request_id,fp,{'operation':payload['operation'],'intent':payload,'movement':budget,'ledger_id':ledger})
