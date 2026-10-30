"""Small native spell-effect adapters: canonical area targets and victim-turn identity.

No new effect store or clock. Source spells still own rules, costs and receipts.
"""
import hashlib
import json
import math


def victim_turn_key(encounter, participant, request_id):
    if encounter and encounter.get('started_at') is not None and encounter.get('turn_sequence') is not None:
        return [encounter['started_at'],encounter['turn_sequence'],participant['target_type'],participant['target_id']]
    return ['legacy-hook',request_id,participant['target_type'],participant['target_id']]


def _magic(effect):
    return effect.get('magic_type')=='arcane' and type(effect.get('spell_circle')) is int and effect['spell_circle']>0 and type(effect.get('caster_level')) is int and effect['caster_level']>0


def _map(db,snapshot):
    encounter=snapshot.get('encounter') or {}
    if encounter.get('active'):return encounter.get('map_id')
    row=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
    return row[0] if row else None


def effect_distance(db,snapshot,effect):
    from .dorn_spell_pack import grid_distance
    area=effect.get('web_area')
    if not area:return grid_distance(db,'dorn7',effect['target_type'],effect['target_id'])
    map_id=_map(db,snapshot)
    if area.get('map_id')!=map_id:raise ValueError('Área fora do mapa atual e do alcance de Dissipar Magia')
    grid=db.execute('SELECT distance_rule,cell_size_m,cols,rows FROM session_workspace_map_grids WHERE map_id=?',(map_id,)).fetchone()
    origin=db.execute("SELECT p.cell_x,p.cell_y FROM session_workspace_entity_positions p JOIN session_workspace_tokens t ON t.id=p.token_id AND t.map_id=p.map_id WHERE t.character_id='dorn7' AND t.map_id=? ORDER BY t.id LIMIT 1",(map_id,)).fetchone()
    if not grid or not origin:raise ValueError('Posicione Dorn no grid para dissipar a área')
    scale=grid[1]
    lo=[max(0,math.floor(area[k]/scale)) for k in ('x_m','y_m')]
    hi=[min(limit-1,math.ceil((area[k]+area[size])/scale)-1) for k,size,limit in [('x_m','width_m',grid[2]),('y_m','height_m',grid[3])]]
    if any(a>b for a,b in zip(lo,hi)):raise ValueError('Área fora do grid e do alcance de Dissipar Magia')
    closest=[max(a,min(b,p)) for p,a,b in zip(origin,lo,hi)]
    from .spatial_grid import distance_cells
    return distance_cells(grid[0],origin,closest)*scale


def dispel_preview(db,snapshot,target_token_id):
    from .dorn_spells import target
    pin=db.execute('SELECT map_id FROM session_workspace_tokens WHERE id=?',(target_token_id,)).fetchone()
    if not pin or pin[0]!=_map(db,snapshot):raise ValueError('Escolha um alvo no mapa atual')
    victim=target(db,'token',target_token_id)
    from .action_library import native_action_contract
    row=db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='dorn7'").fetchone()
    level=int(json.loads(row[0]).get('level') or 3) if row else 3
    contract=native_action_contract('technique:dorn7:dissipar-magia',level)
    allowed={};parents={e['id']:e for e in snapshot['effects'] if not e.get('environmental')}
    for effect in snapshot['effects']:
        if (effect['target_type'],effect['target_id'])!=(victim['type'],victim['id']):continue
        if effect.get('web_area'):continue  # The carrier is not the rectangle's location.
        parent=parents.get(effect.get('web_parent_id') or effect['id'])
        if not parent or not _magic(parent):continue
        distance=effect_distance(db,snapshot,parent)
        if distance>contract['range']['meters']:continue
        allowed[parent['id']]={'id':parent['id'],'label':parent['label'],'kind':'area' if parent.get('web_area') else 'entity',
                               'distance_m':distance,'spell_circle':parent['spell_circle'],'caster_level':parent['caster_level']}
    positions=db.execute('SELECT p.token_id,p.cell_x,p.cell_y,p.footprint_w,p.footprint_h,p.version FROM session_workspace_entity_positions p JOIN session_workspace_tokens t ON t.id=p.token_id AND t.map_id=p.map_id WHERE p.map_id=? AND (t.id=? OR t.character_id=?) ORDER BY t.id',(pin[0],target_token_id,'dorn7')).fetchall()
    rows=sorted(allowed.values(),key=lambda e:(e['label'],e['id']))
    fingerprint=hashlib.sha256(json.dumps([target_token_id,pin[0],rows,[list(p) for p in positions]],sort_keys=True).encode()).hexdigest()
    return {'target_token_id':target_token_id,'target_name':victim['name'],'map_id':pin[0],'effects':rows,'fingerprint':fingerprint,'version':snapshot['version'],'definition_revision':contract['revision']}


def resolve_dispel_effect(db,snapshot,payload):
    effect_id=payload.get('effect_id')
    chosen=next((e for e in snapshot['effects'] if e['id']==effect_id),None)
    canonical_id=(chosen or {}).get('web_parent_id') or effect_id
    row=db.execute('SELECT data_json FROM combat_effects WHERE id=? AND active=1',(canonical_id,)).fetchone()
    if not row:raise ValueError('Selecione um efeito magico ativo')
    effect=json.loads(row[0])
    if not _magic(effect):raise ValueError('Dissipação exige magia arcana com círculo e nível de origem cadastrados')
    if payload.get('target_token_id'):
        preview=dispel_preview(db,snapshot,payload['target_token_id'])
        if not any(e['id']==canonical_id for e in preview['effects']):raise ValueError('Este efeito não pertence ao alvo selecionado ou está fora do alcance')
        if payload.get('target_fingerprint') is not None and preview['fingerprint']!=payload['target_fingerprint']:
            raise ValueError('Posição ou efeitos mudaram; selecione o alvo novamente')
    return effect
