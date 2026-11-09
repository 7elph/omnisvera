"""Explicit door properties on existing location pins; no inferred walls/LOS."""
import json
import uuid
from contextlib import closing
from .spatial_grid import connect, grid_record, visual_position, replay, finish_command
from .character_play import _now, attribute_modifier
from .session_ledger import append_session_ledger_event


def configure(path, *, token_id, actor, role, request_id, payload):
    if role!='gm':raise PermissionError('Somente o Mestre configura portas')
    if (set(payload)!={'difficulty','open'} or type(payload['difficulty']) is not int or
            not 1<=payload['difficulty']<=99 or type(payload['open']) is not bool):
        raise ValueError('Informe dificuldade de 1 a 99 e estado da porta')
    if not isinstance(request_id,str) or not 8<=len(request_id)<=120:raise ValueError('Informe uma chave idempotente')
    fp=json.dumps(['door',token_id,actor,role,payload],sort_keys=True)
    with closing(connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        previous=replay(db,request_id,fp)
        if previous is not None:return previous
        row=db.execute('SELECT * FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()
        if not row or row['token_type']!='location':raise ValueError('Escolha um pin de local')
        sheet=json.loads(row['sheet_json'] or '{}')
        if sheet.get('portable_hole'):raise ValueError('Este local já representa um recipiente')
        grid=grid_record(db,row['map_id'])
        if not grid:raise ValueError('Configure o grid lógico deste mapa')
        # Explicit conversion once, then the cell remains authoritative.
        pos=db.execute('SELECT * FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',(row['map_id'],token_id)).fetchone()
        if not pos:
            x=max(0,min(grid['cols']-1,int((row['longitude']-grid['origin_x'])/(100-grid['origin_x'])*grid['cols'])))
            y=max(0,min(grid['rows']-1,int((row['latitude']-grid['origin_y'])/(100-grid['origin_y'])*grid['rows'])))
            db.execute('INSERT INTO session_workspace_entity_positions(map_id,token_id,cell_x,cell_y) VALUES(?,?,?,?)',(row['map_id'],token_id,x,y))
            point=visual_position(grid,dict(cell_x=x,cell_y=y,footprint_w=1,footprint_h=1))
            db.execute('UPDATE session_workspace_tokens SET latitude=?,longitude=? WHERE id=?',(point['latitude'],point['longitude'],token_id))
        now=_now()
        sheet['door']={**payload,'version':int(sheet.get('door',{}).get('version',0))+1,
            'campaign_rule':'1d20 + modificador de FOR; DC 12 provisória para porta comum.'}
        db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?',(json.dumps(sheet,ensure_ascii=False),now,token_id))
        ledger=append_session_ledger_event(db,source_type='map_door',source_id=request_id,event_kind='state',
            actor_id=actor,actor_name='Mestre',actor_role=role,character_id=None,title=f"Porta configurada · {row['name']}",
            detail={'token_id':token_id,**sheet['door']},visibility='gm',created_at=now)
        return finish_command(db,request_id,fp,{'token_id':token_id,'door':sheet['door'],'ledger_id':ledger})


def ram(db, pin, charges, roll, now, *, owner, role):
    door=json.loads(pin['sheet_json'] or '{}').get('door')
    if not door or door.get('open'):raise ValueError('Escolha uma porta cadastrada e fechada')
    strength={1:14,2:17,3:24}[charges]
    modifier=attribute_modifier(strength) or 0
    natural=int(roll['total'])
    if not 1<=natural<=20:raise ValueError('Rolagem de arrombamento inválida')
    total=natural+modifier
    success=total>=door['difficulty']
    if success:
        door={**door,'open':True,'version':door.get('version',0)+1}
        db.execute("UPDATE session_workspace_tokens SET sheet_json=json_set(sheet_json,'$.door',json(?)),updated_at=? WHERE id=?",
            (json.dumps(door),now,pin['id']))
    public={'door_check':True,'target_token_id':pin['id'],'strength':strength,'modifier':modifier,
        'total':total,'success':success,'roll':roll,'campaign_rule':True,
        'label':f"Aríete · {pin['name']}: {total} · "+('abriu' if success else 'resistiu')}
    append_session_ledger_event(db,source_type='door_force_check',source_id=uuid.uuid4().hex,event_kind='action',
        actor_id='master' if role=='gm' else owner,actor_name='Mestre' if role=='gm' else owner,actor_role=role,
        character_id=owner,title=f"Aríete · {pin['name']}: {total} contra {door['difficulty']}",
        detail={**public,'difficulty':door['difficulty']},visibility='gm',created_at=now)
    return public
