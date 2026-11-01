"""Bounded GM-only suggestions. No dice, writes, inferred enemies or executor."""
import json
import math
import sqlite3
from contextlib import closing
from pathlib import Path

from .battle_mode import require_battle_turn
from .combat import monster_attack_definition
from .combat_effects import effect_snapshot
from .dorn_spells import target
from .spatial_grid import current_participant, distance_cells, grid_record


def propose_actions(path, access, *, token_id, target_token_ids):
    if access.mode!='gm':raise PermissionError('Somente o Mestre consulta propostas de criaturas')
    if not isinstance(target_token_ids,list) or not 1<=len(target_token_ids)<=20 or any(not isinstance(i,str) or not 1<=len(i)<=180 for i in target_token_ids):
        raise ValueError('Escolha entre 1 e 20 pins candidatos')
    # A planning read cannot create schema, spend a resource or advance a turn.
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row;db.execute('BEGIN')
        snapshot=effect_snapshot(db);encounter=snapshot['encounter'] or {}
        actor=db.execute('SELECT * FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()
        if not actor or actor['token_type']!='monster':raise ValueError('Escolha uma criatura existente')
        result={'schema_version':1,'mode':'gm_assisted','token_id':token_id,'combat_version':snapshot['version'],
            'confirmation_required':True,'executed':False,'proposals':[],'blocked':[],
            'limitations':['Somente ataques estruturados sem efeitos adicionais assistidos; magias, baforadas e contatos especiais seguem seus controles nativos.',
                'Os alvos são candidatos escolhidos pelo Mestre; a proposta não define facções nem move a criatura.']}
        def block(reason):result['blocked'].append({'reason':reason})
        participant=current_participant(encounter)
        if not encounter.get('active') or not encounter.get('battle_mode') or not participant or participant['target_type']!='token' or participant['target_id']!=token_id or actor['map_id']!=encounter.get('map_id'):
            block('Propostas exigem o turno atual da criatura no combate com grid');return result
        if actor['current_hp'] is None:block('PV da criatura não cadastrados');return result
        try:require_battle_turn(db,snapshot,token_id)
        except ValueError as error:block(str(error));return result
        grid=grid_record(db,actor['map_id'])
        position=lambda pin:db.execute('SELECT * FROM session_workspace_entity_positions WHERE map_id=? AND token_id=?',(actor['map_id'],pin)).fetchone()
        origin=position(token_id) if grid else None
        if not grid or not origin:block('Grid ou posição da criatura ausentes');return result
        sheet=json.loads(actor['sheet_json'] or '{}')
        token={**dict(actor),'sheet':sheet}
        attacks=sheet.get('attacks') or []
        if len(attacks)>40:block('Lista de ataques excede o limite de revisão');return result
        for index,raw in enumerate(attacks):
            try:
                attack=monster_attack_definition(token,str(index))['attacks'][0]
                if attack.get('manual_effects'):raise ValueError('Efeito adicional exige revisão; não sugerido automaticamente')
                maximum=raw.get('range_m')
                if attack['slot']=='ranged' and (isinstance(maximum,bool) or not isinstance(maximum,(int,float)) or not math.isfinite(maximum) or maximum<=0):
                    raise ValueError('Alcance de distância não cadastrado')
            except (ValueError,TypeError) as error:
                result['blocked'].append({'attack_id':str(index),'reason':str(error)});continue
            for candidate in sorted(set(target_token_ids)):
                row=db.execute('SELECT * FROM session_workspace_tokens WHERE id=? AND map_id=? AND token_type!=?',(candidate,actor['map_id'],'location')).fetchone()
                if not row or candidate==token_id:continue
                kind,identity=('character',row['character_id']) if row['character_id'] else ('token',candidate)
                try:
                    require_battle_turn(db,snapshot,token_id,kind,identity)
                    target(db,kind,identity)
                except ValueError:continue
                destination=position(candidate)
                if not destination:continue
                cells=distance_cells(grid['distance_rule'],[origin['cell_x'],origin['cell_y']],[destination['cell_x'],destination['cell_y']])
                meters=cells*grid['cell_size_m']
                ranged=attack['slot']=='ranged'
                if (not ranged and cells>1) or (ranged and meters>maximum+1e-8):continue
                request={'attack_id':str(index),'target_type':kind,'target_id':identity,
                    **({'range_m':maximum} if ranged else {'range_cells':1})}
                result['proposals'].append({'name':attack['name'],'target_name':row['name'],'distance':{'cells':cells,'meters':meters},
                    'resolve_endpoint':'/gm/combat/tokens/'+token_id+'/attacks/resolve','request':request,
                    'context':{'grid_version':grid['version'],'origin_position_version':origin['version'],'target_position_version':destination['version']}})
        result['proposals'].sort(key=lambda p:(p['distance']['meters'],int(p['request']['attack_id']),p['request']['target_id']))
        if not result['proposals'] and not result['blocked']:block('Nenhum alvo candidato apto no alcance e no combate atual')
        return result
