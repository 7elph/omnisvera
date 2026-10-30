"""Native confirmed grid contacts: statless Sphere and reviewed equipment corrosion."""
import hashlib
import json
from .dice_rolls import roll_formula

KINDS={'esfera-da-aniquilacao':'disintegration','monstro-ferrugem':'rust'}


def identity(sheet):
    source=sheet.get('source')
    return source.get('monster_id') if isinstance(source,dict) else None


def is_statless(db,kind,identity_):
    if kind!='token':return False
    raw=db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(identity_,)).fetchone()
    return bool(raw and identity(json.loads(raw[0] or '{}'))=='esfera-da-aniquilacao')


def binding(monster_id):
    return KINDS.get(monster_id)


def _pin(db,pin_id):
    cursor=db.execute('SELECT * FROM session_workspace_tokens WHERE id=?',(pin_id,));raw=cursor.fetchone()
    if not raw:raise ValueError('Pin não encontrado')
    return dict(zip([c[0] for c in cursor.description],raw))


def preview(db,snapshot,token_id,target_pin_id,*,target_ac=None):
    actor=_pin(db,token_id);target=_pin(db,target_pin_id)
    from .monster_runtime import token_monster
    monster,_=token_monster(db,token_id)
    kind=KINDS.get((monster or {}).get('id'))
    if not kind:raise ValueError('Contato especial não configurado nesta criatura')
    if token_id==target_pin_id or target['token_type']=='location':raise ValueError('Escolha outra criatura')
    if is_statless(db,'token',target_pin_id):raise ValueError('Perigo de cenário não possui PV para este contato')
    if actor['map_id']!=target['map_id']:raise ValueError('Contato exige o mesmo mapa')
    grid=db.execute('SELECT distance_rule,cell_size_m FROM session_workspace_map_grids WHERE map_id=?',(actor['map_id'],)).fetchone()
    positions=[db.execute('SELECT cell_x,cell_y,footprint_w,footprint_h,version FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',(actor['map_id'],pin)).fetchone() for pin in (token_id,target_pin_id)]
    if not grid or not all(positions):raise ValueError('Posicione os dois pins no grid antes do contato')
    from .spatial_grid import distance_cells
    a,b=positions
    dx=max(a[0]-b[0]-b[2]+1,b[0]-a[0]-a[2]+1,0)
    dy=max(a[1]-b[1]-b[3]+1,b[1]-a[1]-a[3]+1,0)
    if distance_cells(grid[0],[0,0],[dx,dy])>1:raise ValueError('Contato exige adjacência no grid')
    from .dorn_spells import target as victim_target
    victim=victim_target(db,'token',target_pin_id)
    encounter=snapshot.get('encounter') or {}
    if encounter.get('active') and encounter.get('map_id')!=actor['map_id']:raise ValueError('Pin fora do mapa de combate')
    if kind=='rust':
        from .battle_mode import require_battle_turn
        require_battle_turn(db,snapshot,token_id,victim['type'],victim['id'])
        from .dorn_protocols import protects_ally
        if victim['type']=='character' and any(protects_ally(db,effect,victim['id']) for effect in snapshot['effects']):
            raise ValueError('Guarda protege este aliado. Selecione Dorn no grid e confirme o equipamento dele e o alcance antes do contato.')
        if type(target_ac) is not int or target_ac<=0:raise ValueError('Alvo sem CA configurada')
    state=None
    if victim['type']=='character':
        state=db.execute('SELECT state_json,version FROM character_states WHERE profile_id=?',(victim['id'],)).fetchone()
    items=[]
    if kind=='rust':
        from .monster_rust import preview as item_preview
        owner=victim['id']
        for row in db.execute('SELECT id FROM player_inventory WHERE profile_id=? AND equipped=1 AND quantity>0 ORDER BY id',(owner,)):
            try:items.append(item_preview(db,victim['type'],victim['id'],row[0]))
            except ValueError:continue
    blob=[monster,actor,target,positions,state,items,target_ac]
    fingerprint=hashlib.sha256(json.dumps(blob,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'kind':kind,'token_id':token_id,'target_pin_id':target_pin_id,'target_type':victim['type'],'target_id':victim['id'],
            'target_name':victim['name'],'fingerprint':fingerprint,'map_id':actor['map_id'],
            'inventory':items,'version':snapshot['version'],'target_ac':target_ac}


def command(db,snapshot,payload,now,request_id):
    current=preview(db,snapshot,str(payload.get('token_id') or ''),str(payload.get('target_pin_id') or ''),target_ac=payload.get('_server_target_ac'))
    if current['fingerprint']!=payload.get('fingerprint'):raise ValueError('Posição, ficha ou equipamento mudou. Selecione o alvo novamente.')
    kind,identity_=current['target_type'],current['target_id']
    from .battle_mode import commit_battle_action
    result={'kind':current['kind'],'target_name':current['target_name']}
    if current['kind']=='disintegration':
        from .combat_effects import change_hp
        if kind=='character':
            raw=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(identity_,)).fetchone()
            state=json.loads(raw[0]);from .night_form import end
            end(state);state['temporary_hp']=0
            hp=int(state['current_hp']);db.execute('UPDATE character_states SET state_json=? WHERE profile_id=?',(json.dumps(state),identity_))
        else:hp=int(_pin(db,identity_)['current_hp'])
        result['hp']=change_hp(db,kind,identity_,-hp-10,now,ignore_temporary_hp=True)
        pins=db.execute('SELECT id,sheet_json FROM session_workspace_tokens WHERE '+('character_id=?' if kind=='character' else 'id=?'),(identity_,)).fetchall()
        for pin,raw in pins:
            sheet=json.loads(raw or '{}');sheet.update(disintegrated=True,reanimation_allowed=False,combat_retired=True)
            sheet.pop('corpse',None)
            db.execute('UPDATE session_workspace_tokens SET sheet_json=?,visible_to_players=0,updated_at=? WHERE id=?',(json.dumps(sheet),now,pin))
    else:
        from .monster_rust import preview as item_preview,contact
        selection=payload.get('selection');inventory_id=payload.get('inventory_id')
        # Validate selected equipment BEFORE dice or budget mutation, even on a miss.
        equipment=item_preview(db,kind,identity_,inventory_id,selection)
        if equipment['needs_metadata']:raise ValueError('Confirme material e encantamento do item')
        from .monster_runtime import token_monster
        monster,_=token_monster(db,current['token_id'])
        from .combat_effects import apply_definition_effects
        bonus=int(monster['attacks'][0]['bonus'])
        definition=apply_definition_effects({'attacks':[{'id':'0','attack_bonus':bonus}], 'defenses':{}},[e for e in snapshot['effects'] if e['target_type']=='token' and e['target_id']==current['token_id']])
        bonus=definition['attacks'][0]['attack_bonus']
        from .spatial_grid import diagonal_bonus
        bonus+=diagonal_bonus(db,current['token_id'],kind,identity_)['bonus']
        if any(effect.get('condition')=='magical_darkness' or effect.get('monster_condition')=='blinded'
               for effect in snapshot['effects'] if effect['target_type']==kind and effect['target_id']==identity_):
            bonus+=5
        roll=roll_formula('1d20');die=int(roll['total']);hit=die==20 or (die!=1 and die+bonus>=current['target_ac'])
        result.update(attack_roll=roll,attack_bonus=bonus,hit=hit,target_ac=current['target_ac'])
        if hit:
            from .dorn_spell_pack import redirect_hits
            _,reflection=redirect_hits(db,kind,identity_,[{'result':'hit','damage_total':0}],now)
            if reflection:result['reflection_result']=reflection
            if not any(entry.get('intercepted') for entry in reflection.get('rolls',[])):
                result['corrosion']=contact(db,kind,identity_,inventory_id,selection,expected_fingerprint=equipment['fingerprint'],now=now)
        commit_battle_action(db,snapshot)
    from .session_ledger import append_session_ledger_event
    from .monster_runtime import public_token
    title=('Desintegração' if current['kind']=='disintegration' else 'Ferrugem')+' · '+current['target_name']
    if current['kind']=='rust':
        title+=f" · d20 {result['attack_roll']['total']} {result['attack_bonus']:+d} · "
        corrosion=result.get('corrosion') or {}
        title+=('errou' if not result['hit'] else 'Reflexos interceptou' if not corrosion else 'item destruído' if corrosion.get('destroyed') else 'resistiu' if corrosion.get('resisted') else 'item não metálico' if corrosion.get('unaffected') else f"encantamento +{corrosion.get('bonus_before')} → +{corrosion.get('bonus_after')}")
    append_session_ledger_event(db,source_type='monster_contact',source_id=request_id,event_kind='action',actor_id=current['token_id'],actor_name='Mestre',actor_role='gm',
        character_id=identity_ if kind=='character' else None,title=title,detail=result,
        visibility='table' if public_token(db,current['token_id']) and (kind=='character' or public_token(db,identity_)) else 'gm',created_at=now)
    return result
