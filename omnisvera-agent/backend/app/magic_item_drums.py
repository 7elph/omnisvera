"""Approved fear instrument: native grid, JP, effects, receipts and movement."""
import hashlib
import json
import uuid
from .magic_item_rulebook import rules_for
from .damage_profiles import normalized

DRUMS='item-magico-tambores-do-panico'
RULES=rules_for(DRUMS)['parameters']


def _effects(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():return []
    return [json.loads(r[0]) for r in db.execute("SELECT data_json FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.magic_item')=?",(DRUMS,))]


def _conditions(db,kind,identity):
    if kind=='character':
        row=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(identity,)).fetchone()
        values=(json.loads(row[0]).get('conditions') or []) if row else []
    else:
        row=db.execute('SELECT conditions_json FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
        values=json.loads(row[0] or '[]') if row else []
    values+= [json.loads(r[0]).get('monster_condition','') for r in db.execute(
        'SELECT data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=?',(kind,identity))]
    return [normalized(str(v)) for v in values]


def _origin(db,effect):
    return db.execute('SELECT p.cell_x,p.cell_y FROM session_workspace_entity_positions p '
        'JOIN session_workspace_tokens t ON t.id=p.token_id AND t.map_id=p.map_id '
        'WHERE p.map_id=? AND p.token_id=? AND t.character_id=?',
        (effect['map_id'],effect['origin_token_id'],effect['target_id'])).fetchone()


def prune(db,now):
    effects=_effects(db);active=set();changed=False
    if not effects:return
    from .spatial_grid import has_schema,grid_record
    for e in effects:
        if not e.get('drum_performance'):continue
        item=db.execute('SELECT quantity FROM player_inventory WHERE id=? AND profile_id=? AND item_path=?',
            (e['inventory_id'],e['target_id'],e['item_path'])).fetchone()
        row=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(e['target_id'],)).fetchone()
        hp=int(json.loads(row[0]).get('current_hp') or 0) if row else 0
        from .night_form import current_form
        from .vezemir_skills import survives
        alive=hp>0 or survives(db,e['target_id'],hp)
        disabled=bool(row and current_form(json.loads(row[0]))) or any(any(c.startswith(k) for k in ['silenced','silenciado','paralyzed','paralisado','petrified','petrificado']) for c in _conditions(db,'character',e['target_id']))
        if item and item[0]==1 and alive and not disabled and has_schema(db) and grid_record(db,e['map_id']) and _origin(db,e):active.add(e['id'])
        else:db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(e['id'],));changed=True
    for e in effects:
        if e.get('drum_fear') and e.get('drum_source') not in active:
            db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(e['id'],));changed=True
    if changed:db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')


def sync(db,now):
    prune(db,now)
    performances=[e for e in _effects(db) if e.get('drum_performance')]
    if not performances:return
    from .spatial_grid import grid_record,distance_cells
    from .dorn_spells import target,save
    from .monster_conditions import _immune
    from .magic_passives import block_mental
    from .monster_runtime import public_token
    from .session_ledger import append_session_ledger_event
    for performance in performances:
        grid=grid_record(db,performance['map_id']);origin=_origin(db,performance)
        if not grid or not origin:continue
        rows=db.execute("SELECT t.id,t.character_id,t.current_hp,p.cell_x,p.cell_y FROM session_workspace_tokens t "
            "JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id "
            "WHERE t.map_id=? AND t.token_type!='location' ORDER BY t.id",(performance['map_id'],)).fetchall()
        for token,character,hp,x,y in rows:
            kind,identity=('character',character) if character else ('token',token)
            if identity==performance['target_id'] or distance_cells(grid['distance_rule'],list(origin),[x,y])*grid['cell_size_m']>RULES['radius_m']+1e-8:continue
            key='drum-check:'+hashlib.sha256(json.dumps([performance['id'],kind,identity]).encode()).hexdigest()
            if db.execute('SELECT 1 FROM combat_effect_commands WHERE request_id=?',(key,)).fetchone():continue
            try:victim=target(db,kind,identity)
            except ValueError:
                if hp is None or hp<=0:continue
                raise
            conditions=_conditions(db,kind,identity)
            immune=(_immune(db,kind,identity,{'effect':'fear','condition':'frightened'})
                    or _immune(db,kind,identity,{'effect':'fear','condition':'fear'}))
            deaf=any(c.startswith(('deaf','surdo','surdez')) for c in conditions)
            result={'target_type':kind,'target_id':identity,'item':DRUMS}
            if immune or deaf:result['immune']=immune or 'Não ouve os tambores'
            else:
                ward=block_mental(db,victim,'fear',now)
                if ward:result.update(mental_ward=ward,resisted=True)
                else:
                    saving=save(db,victim,'wisdom');result.update(saving_throw=saving,resisted=saving['success'])
                    if not saving['success']:
                        fear={'id':'drum-fear:'+uuid.uuid4().hex,'target_type':kind,'target_id':identity,
                            'label':'Pânico · Tambores','source':'Tambores do Pânico','duration':'manual','rounds':None,
                            'condition_description':'Enquanto os tambores tocarem: não ataca/conjura; cada passo deve afastar-se do músico.',
                            'modifiers':{},'magic_item':DRUMS,'drum_fear':True,'drum_source':performance['id'],
                            'map_id':performance['map_id'],'updated_at':now}
                        db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(fear['id'],kind,identity,json.dumps(fear,ensure_ascii=False)))
                        result['effect_id']=fear['id']
            # Internal receipts retain one JP per canonical creature, without
            # exposing hidden listeners in the performer's public effect data.
            db.execute('INSERT INTO combat_effect_commands VALUES(?,?,?)',(key,json.dumps(['drum-check',performance['id'],kind,identity]),json.dumps(result,ensure_ascii=False)))
            visible=public_token(db,performance['origin_token_id']) and public_token(db,token)
            status='imune' if result.get('immune') else 'resistiu' if result.get('resisted') else 'em pânico'
            if result.get('saving_throw'):
                status=f"JPS {result['saving_throw']['total']}/{result['saving_throw']['target']} · {status}"
            append_session_ledger_event(db,source_type='magic_item_fear',source_id=key,event_kind='action',
                actor_id='system',actor_name='Tambores do Pânico',actor_role='system',character_id=identity if kind=='character' else None,
                title=f"Tambores · {victim['name']}: {status}",
                detail=result,visibility='table' if visible else 'gm',created_at=now)
            db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')


def use(db,snapshot,owner,item,inventory,now):
    previous=next((e for e in _effects(db) if e.get('drum_performance') and e['target_id']==owner and e['item_path']==item['item_path']),None)
    if previous:
        db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(previous['id'],));prune(db,now)
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        return [{'kind':'magic_activation','magic_item':DRUMS,'phase':'stop','resolved_value':0,'label':'Tambores pararam; pânico encerrado'}]
    if any(e.get('drum_performance') and e['target_id']==owner for e in _effects(db)):
        raise ValueError('Pare de tocar o outro exemplar dos Tambores antes de começar')
    from .spatial_grid import has_schema,grid_record
    if not has_schema(db):raise ValueError('Tambores exigem posição em um mapa com grid lógico')
    encounter=snapshot.get('encounter') or {}
    selected=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
    map_id=encounter.get('map_id') if encounter.get('active') else selected[0] if selected else 'default'
    if not grid_record(db,map_id):raise ValueError('Tambores exigem mapa com grid lógico')
    origins=db.execute('SELECT t.id FROM session_workspace_tokens t JOIN session_workspace_entity_positions p '
        'ON p.token_id=t.id AND p.map_id=t.map_id WHERE t.map_id=? AND t.character_id=?',(map_id,owner)).fetchall()
    if len(origins)!=1:raise ValueError('Posicione um único pin do músico no grid deste mapa')
    effect={'id':'drums:'+uuid.uuid4().hex,'target_type':'character','target_id':owner,
        'label':'Tambores · tocando','source':'Tambores do Pânico','duration':'manual','rounds':None,'modifiers':{},
        'condition_description':'Aura de 10 m. Pare de tocar antes de atacar ou conjurar.',
        'magic_item':DRUMS,'drum_performance':True,'map_id':map_id,'origin_token_id':origins[0][0],
        'item_path':item['item_path'],'inventory_id':inventory['id'],'updated_at':now}
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],'character',owner,json.dumps(effect,ensure_ascii=False)))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1');sync(db,now)
    return [{'kind':'magic_activation','magic_item':DRUMS,'phase':'start','resolved_value':1,
             'label':'Tambores tocando · raio de 10 m','effect_id':effect['id']}]


def assert_action(db,actor_id,*,movement=False,noncombat=False):
    if movement or noncombat:return
    effects=_effects(db)
    if not effects:return
    from .monster_conditions import _canonical
    kind,identity=_canonical(db,'character' if db.execute('SELECT 1 FROM character_states WHERE profile_id=?',(actor_id,)).fetchone() else 'token',actor_id)
    from .spatial_grid import encounter_record
    encounter,_=encounter_record(db)
    selected=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
    active_map=encounter.get('map_id') if encounter.get('active') else selected[0] if selected else 'default'
    sources={e['id'] for e in effects if e.get('drum_performance')}
    for e in effects:
        if (e['target_type'],e['target_id'])!=(kind,identity):continue
        if e.get('drum_fear') and e.get('drum_source') in sources and e.get('map_id')==active_map:
            raise ValueError('Pânico dos Tambores: afaste-se do músico; não pode atacar ou conjurar')
        if e.get('drum_performance'):raise ValueError('Tambores: pare de tocar antes de atacar ou conjurar')


def validate_path(db,map_id,token_id,cells):
    from .spatial_grid import grid_record,distance_cells
    token=db.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()
    kind,identity=('character',token[0]) if token and token[0] else ('token',token_id)
    active={e['id']:e for e in _effects(db) if e.get('drum_performance')}
    for fear in _effects(db):
        if not fear.get('drum_fear') or (fear['target_type'],fear['target_id'])!=(kind,identity):continue
        source=active.get(fear['drum_source'])
        if not source or source['map_id']!=map_id:continue
        origin=_origin(db,source);grid=grid_record(db,map_id)
        if not origin or not grid:continue
        before=distance_cells(grid['distance_rule'],list(origin),cells[0])
        for cell in cells[1:]:
            after=distance_cells(grid['distance_rule'],list(origin),cell)
            if after<=before:raise ValueError('Pânico dos Tambores: cada passo precisa afastar-se do músico')
            before=after
