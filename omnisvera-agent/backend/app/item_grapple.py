"""Garrote: approved timing on the existing turn clock and logical grid."""
import json
import uuid
from .dice_rolls import roll_formula


def _effects(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='combat_effects'").fetchone():
        return []
    return [json.loads(r[0]) for r in db.execute("SELECT data_json FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.item_special')='garrote'")]


def _emit(db, effect, now, key, title, detail, *, public=None):
    from .session_ledger import append_session_ledger_event
    from .monster_runtime import public_token
    if public is None:public = public_token(db,effect['victim_pin']) and public_token(db,effect['owner_pin'])
    append_session_ledger_event(db,source_type='item_grapple',source_id=key,event_kind='action',
        actor_id=effect['item_owner'],actor_name=effect.get('owner_name',effect['item_owner']),actor_role=effect.get('owner_role','player'),
        character_id=effect['item_owner'],title=title,detail=detail,visibility='table' if public else 'gm',created_at=now)


def _release(db, effect, now, reason):
    db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(effect['id'],))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    _emit(db,effect,now,effect['id']+':release','Garrote encerrado · '+reason,{'effect_id':effect['id'],'reason':reason})


def _context(db, actor, target):
    kind,identity=target['type'],target['id']
    pin=target.get('server_token_id') or (identity if kind=='token' else None)
    token = db.execute('SELECT id,map_id,sheet_json FROM session_workspace_tokens WHERE id=?',(pin,)).fetchone() if pin else None
    if token is None:
        token=db.execute('SELECT t.id,t.map_id,t.sheet_json FROM session_workspace_tokens t JOIN session_workspace_tokens a ON a.map_id=t.map_id WHERE t.character_id=? AND a.character_id=? ORDER BY t.id LIMIT 1',(identity,actor)).fetchone()
    if not token:raise ValueError('Garrote automático exige os dois participantes no grid')
    from .spatial_grid import check_attack_range
    checked=check_attack_range(None,actor_character_id=actor,target_type='token',target_id=token[0],slot='melee',connection=db)
    if not checked.get('checked'):raise ValueError('Garrote automático exige os dois participantes no grid')
    sheet=json.loads(token[2] or '{}');size=str(sheet.get('size') or '').casefold()
    if not size:
        from .monster_runtime import token_monster
        monster,_=token_monster(db,token[0]);size=str((monster or {}).get('size') or '').casefold()
    if kind=='character' and not size:size='m'  # Existing normal character tokens occupy one cell.
    if size not in {'p','m','pequeno','pequena','médio','média','medio','media','small','medium'}:
        raise ValueError('Garrote exige tamanho Pequeno ou Médio cadastrado no alvo')
    owner_pin=db.execute('SELECT id FROM session_workspace_tokens WHERE character_id=? AND map_id=? ORDER BY id LIMIT 1',(actor,token[1])).fetchone()
    return {'map_id':token[1],'victim_pin':token[0],'owner_pin':owner_pin[0]}


def contract(db,actor,target,path):
    from .dorn_spells import target as get_target
    victim=get_target(db,target['type'],target['id'])
    if type(victim['defenses'].get('saving_throw')) is not int:raise ValueError('Cadastre a JP do alvo antes de usar Garrote')
    if any(e['item_owner']==actor for e in _effects(db)):
        raise ValueError('Guarde o garrote ou liberte o alvo antes de iniciar outro aperto')
    return {'kind':'garrote','item_path':path,**_context(db,actor,target)}


def bind(db,record,contract,now):
    effect={'id':'item-garrote:'+uuid.uuid4().hex,'target_type':record['target_type'],'target_id':record['target_id'],
        'label':'Garrotado','source':'Garrote','duration':'manual','rounds':None,'modifiers':{},'blocks_speech':True,
        'item_special':'garrote','item_owner':record['actor_character_id'],'owner_name':record['actor_name'],
        'owner_role':record['requested_by_role'],'damage_context':record['breakdown'].get('damage_profile'),
        'updated_at':now,**{k:v for k,v in contract.items() if k!='kind'},
        'condition_description':'JP de DES antes de 1d4 no início do turno. Sem fala; termina ao guardar, afastar ou incapacitar o portador.'}
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],effect['target_type'],effect['target_id'],json.dumps(effect,ensure_ascii=False)))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return {'effect_id':effect['id'],'label':effect['label']}


def prune(db,now,*,moving=None):
    removed=[]
    for effect in _effects(db):
        from .dorn_spells import target
        try:
            target(db,'character',effect['item_owner']);target(db,effect['target_type'],effect['target_id'])
            item=db.execute('SELECT quantity,equipped FROM player_inventory WHERE profile_id=? AND item_path=?',(effect['item_owner'],effect['item_path'])).fetchone()
            if not item or item[0]<1 or not item[1]:raise ValueError('arma guardada')
            from .spatial_grid import distance_cells
            grid=db.execute('SELECT distance_rule FROM session_workspace_map_grids WHERE map_id=?',(effect['map_id'],)).fetchone()
            positions=[]
            for pin in [effect['owner_pin'],effect['victim_pin']]:
                position=db.execute('SELECT p.cell_x,p.cell_y FROM session_workspace_entity_positions p JOIN session_workspace_tokens t ON t.id=p.token_id AND t.map_id=p.map_id WHERE p.map_id=? AND p.token_id=?',(effect['map_id'],pin)).fetchone()
                if not position:raise ValueError('participante saiu do mapa')
                positions.append(list(position))
            if not grid or distance_cells(grid[0],*positions)>1:raise ValueError('participantes se afastaram')
            if moving and moving[0]==effect['map_id'] and moving[1] in {effect['owner_pin'],effect['victim_pin']}:
                slot=0 if moving[1]==effect['owner_pin'] else 1
                if any(distance_cells(grid[0],cell,positions[1-slot])>1 for cell in moving[2]):raise ValueError('participante se afastou durante o percurso')
        except ValueError as error:
            _release(db,effect,now,str(error));removed.append(effect['id'])
    return removed


def assert_can_speak(db,kind,identity):
    if kind=='token':
        row=db.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
        if row and row[0]:kind,identity='character',row[0]
    if any(e['target_type']==kind and e['target_id']==identity for e in _effects(db)):
        raise ValueError('Garrotado: não é possível falar ou executar a parte verbal da magia')


def turn_start(db,participant,encounter,now,request_id):
    if not participant:return False
    prune(db,now)
    for effect in _effects(db):
        if (effect['target_type'],effect['target_id'])!=(participant['target_type'],participant['target_id']):continue
        from .spell_effect_runtime import victim_turn_key
        key=victim_turn_key(encounter,participant,request_id)
        if effect.get('last_target_turn')==key:continue
        from .dorn_spells import target,save
        victim=target(db,effect['target_type'],effect['target_id'])
        effect['last_target_turn']=key
        db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect,ensure_ascii=False),effect['id']))
        try:saving=save(db,victim,'dexterity')
        except ValueError as error:
            _emit(db,effect,now,request_id+':'+effect['id']+':gap','Garrote aguarda JP válida; turno preservado',{'reason':str(error),'effect_id':effect['id']})
            continue
        if saving['success']:
            _release(db,effect,now,'alvo resistiu à JP de DES');continue
        from .combat_effects import change_hp
        from .monster_runtime import public_token
        was_public=public_token(db,effect['victim_pin']) and public_token(db,effect['owner_pin'])
        roll=roll_formula('1d4');hp=change_hp(db,effect['target_type'],effect['target_id'],-int(roll['total']),now,damage_context=effect.get('damage_context'))
        _emit(db,effect,now,request_id+':'+effect['id'],'Garrote · '+victim['name']+f": {hp['damage_taken']} de dano",{'save':saving,'roll':roll,'hp':hp},public=was_public)
        from .vezemir_skills import survives
        if hp['hp_after']<=0 and not (effect['target_type']=='character' and survives(db,effect['target_id'],hp['hp_after'])):return True
    return False
