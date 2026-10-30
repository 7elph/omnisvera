"""Approved campaign skills on native HP, effects, grid and turn transactions."""
import json
import uuid
from .dice_rolls import roll_formula
from .session_ledger import append_session_ledger_event


def native_buff_contract(skill, level=1, definition_revision=None):
    """Revision guard without reading/reconciling a legacy playable sheet."""
    if skill not in {'forca-arcana', 'velocidade'}:
        raise ValueError('Buff de Vezemir desconhecido')
    from .action_library import native_action_contract
    from .action_components import require_definition_revision
    contract = native_action_contract('technique:vezemir:' + skill, level)
    require_definition_revision({'definition_revision': definition_revision}, contract)
    return contract


def native_buff_payload(skill, definition, definition_revision=None):
    """Configure existing self-buffs; the native apply command still owns RNG/cost.

    This deliberately preserves their current turn gate (not a newly invented
    main-action cost), effective-strength source and one-use-per-rest resources.
    """
    contract = native_buff_contract(skill, definition.get('level') or 1, definition_revision)
    resolution = contract['resolution']
    lifetime, cost = resolution['lifetime'], contract['costs'][0]
    payload = {'target_type': 'character', 'target_id': 'vezemir', 'duration': contract['duration'],
               'rounds': 1, '_rounds_formula': f"{lifetime['dice']}+{lifetime['add']}",
               'resource': {'character_id': 'vezemir', 'key': cost['key'], 'cost': cost['amount']}}
    if skill == 'forca-arcana':
        strength = int((definition.get('attributes') or {}).get('strength') or 10)
        bonus = max(resolution['minimum_bonus'], strength // resolution['strength_divisor'])
        payload.update(label=f'Força Arcana (For {strength}→{strength + bonus})',
                       source='Força Arcana (Vezemir)', modifiers={'strength_bonus': bonus})
    else:
        payload.update(label='Velocidade', source='Velocidade (Vezemir)', modifiers=resolution['modifiers'])
    return payload


def active_frenzy(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():return None
    row=db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type='character' AND target_id='vezemir' AND json_extract(data_json,'$.skill')='frenesi'").fetchone()
    return json.loads(row[1]) if row else None


def survives(db,actor_id,hp):
    if actor_id!='vezemir' or hp is None or not -10<int(hp)<=0:return False
    effect=active_frenzy(db)
    return bool(effect and effect.get('defy_death'))


def add_effect(db,kind,identity,label,now,**extra):
    effect=dict(id='skill:'+uuid.uuid4().hex,target_type=kind,target_id=identity,label=label,source=label,
                duration='manual',rounds=None,modifiers={},updated_at=now)
    effect.update(extra)
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],kind,identity,json.dumps(effect,ensure_ascii=False)))
    return effect


def _sync_pin_lifeline(db,enabled,now):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='session_workspace_tokens'").fetchone():return
    for identity,raw in db.execute("SELECT id,sheet_json FROM session_workspace_tokens WHERE character_id='vezemir'").fetchall():
        sheet=json.loads(raw or '{}')
        if bool(sheet.get('frenesi_survival'))==bool(enabled):continue
        sheet['frenesi_survival']=bool(enabled)
        db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?',(json.dumps(sheet),now,identity))


def start_frenzy(db,state,now,automatic=False):
    if active_frenzy(db):raise ValueError('Frenesi já está ativo')
    flags=state.setdefault('daily_skill_flags',{})
    if automatic:
        if flags.get('frenesi_auto_used'):raise ValueError('Frenesi automático já usado neste descanso diário')
        flags['frenesi_auto_used']=True
    else:
        resource=next((r for r in state.get('resources',[]) if r['key']=='frenesi'),None)
        if not resource or resource['current']<1:raise ValueError('Sem uso diário de Frenesi')
        resource['current']-=1
    survival=not flags.get('frenesi_lifeline_used')
    duration=int(roll_formula('1d4')['total'])+1
    effect=add_effect(db,'character','vezemir','Frenesi',now,skill='frenesi',duration='rounds',rounds=duration,
                      modifiers={'strength_bonus':2},defy_death=survival,automatic=automatic)
    _sync_pin_lifeline(db,survival,now)
    return effect


def hp_result(db,state,raw,before,maximum,now):
    if not any(r.get('key')=='frenesi' for r in state.get('resources',[])):return max(0,min(maximum,int(raw)))
    flags=state.setdefault('daily_skill_flags',{})
    if raw<maximum/2 and before>0 and not active_frenzy(db) and not flags.get('frenesi_auto_used'):
        effect=start_frenzy(db,state,now,automatic=True)
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        append_session_ledger_event(db,source_type='ability_activation',source_id=effect['id'],event_kind='action',actor_id='vezemir',actor_name='Vezemir',actor_role='player',character_id='vezemir',title=f"Frenesi automático: +2 FOR por {effect['rounds']} rodadas; uso manual preservado",detail={'ability_id':'frenesi','automatic':True,'rounds':effect['rounds']},visibility='table',created_at=now)
    frenzy=active_frenzy(db)
    if frenzy and frenzy.get('defy_death'):
        if raw<=0:
            flags['frenesi_lifeline_used']=True
            frenzy['lifeline_triggered']=True
            db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(frenzy),frenzy['id']))
        if raw>-10:return min(maximum,int(raw))
        frenzy['defy_death']=False
        flags['frenesi_lifeline_exhausted']=True
        db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(frenzy),frenzy['id']))
        _sync_pin_lifeline(db,False,now)
        return -10
    return max(0,min(maximum,int(raw)))


def cleanup_lifeline(db,now):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():return
    effect=active_frenzy(db)
    if effect and effect.get('defy_death'):return
    _sync_pin_lifeline(db,False,now)
    row=db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()
    if row:
        state=json.loads(row[0])
        if int(state.get('current_hp') or 0)<=0:
            db.execute("UPDATE combat_effects SET active=0 WHERE active=1 AND json_extract(data_json,'$.skill')='provocacao'")
        if int(state.get('current_hp') or 0)<0 and not state.get('daily_skill_flags',{}).get('frenesi_lifeline_exhausted'):
            state['current_hp']=0
            db.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id='vezemir'",(json.dumps(state),now))
            db.execute("UPDATE session_workspace_tokens SET current_hp=0 WHERE character_id='vezemir'")


def combat_units(db,caster):
    """Only selected/revealed living units on the native battle grid."""
    from .spatial_grid import distance_cells
    clock=db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()
    encounter=json.loads(clock[0] or '{}') if clock else {}
    if not encounter.get('active') or not encounter.get('battle_mode'):raise ValueError('Esta área automática exige combate ativo com grid')
    map_id=encounter['map_id'];grid=db.execute('SELECT distance_rule,cell_size_m FROM session_workspace_map_grids WHERE map_id=?',(map_id,)).fetchone()
    if not grid:raise ValueError('Configure o grid lógico do mapa')
    origin=db.execute('SELECT p.cell_x,p.cell_y FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id WHERE t.character_id=? AND t.map_id=? LIMIT 1',(caster,map_id)).fetchone()
    if not origin:raise ValueError('Posicione o conjurador no grid')
    identities={p['target_id'] for p in encounter.get('participants',[]) if p['target_type']=='token'}
    units=[]
    for identity,name,hp,raw,x,y in db.execute('SELECT t.id,t.name,t.current_hp,t.sheet_json,p.cell_x,p.cell_y FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id WHERE t.map_id=? AND t.visible_to_players=1 AND t.token_type=\'monster\' AND t.current_hp>0',(map_id,)).fetchall():
        sheet=json.loads(raw or '{}')
        if identity not in identities or sheet.get('summon') or 'aliado' in str(sheet.get('role') or '').casefold():continue
        units.append(dict(type='token',id=identity,name=name,hp=hp,sheet=sheet,x=x,y=y,meters=distance_cells(grid[0],origin,[x,y])*grid[1]))
    return sorted(units,key=lambda u:(u['meters'],u['id']))


def cast(db,snapshot,payload,now,actor_id,role):
    if role!='gm' and actor_id!='vezemir':raise PermissionError('Somente Vezemir ou o Mestre usa esta habilidade')
    from .battle_mode import require_battle_turn,commit_battle_action
    require_battle_turn(db,snapshot,'vezemir')
    state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])
    skill=payload.get('skill')
    if skill=='frenesi':
        result={'spell':'Frenesi','effect':start_frenzy(db,state,now)}
    elif skill=='provocacao':
        resource=next((r for r in state.get('resources',[]) if r['key']=='provocacao'),None)
        if not resource or resource['current']<1:raise ValueError('Sem uso diário de Provocação')
        enemies=combat_units(db,'vezemir')
        if not enemies:raise ValueError('Não há inimigos elegíveis no grid')
        radius=int(roll_formula('1d4')['total'])+len(enemies)
        selected=[u for u in enemies if u['meters']<=radius]
        if not selected:raise ValueError('Nenhum inimigo no raio de Provocação')
        from .dorn_spells import target
        for unit in selected:
            victim=target(db,'token',unit['id'])
            if int(victim['defenses'].get('saving_throw') or 0)<=0:raise ValueError('Configure a JP do inimigo')
        group='provocation:'+uuid.uuid4().hex
        result={'spell':'Provocação','radius_m':radius,'targets':[]}
        for unit in selected:
            old=db.execute("SELECT id FROM combat_effects WHERE active=1 AND target_id=? AND json_extract(data_json,'$.skill')='provocacao'",(unit['id'],)).fetchall()
            for identity, in old:db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(identity,))
            result['targets'].append(add_effect(db,'token',unit['id'],'Provocação',now,skill='provocacao',caster='vezemir',failed=False,group=group))
        resource['current']-=1
    else:raise ValueError('Habilidade desconhecida')
    db.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id='vezemir'",(json.dumps(state),now))
    commit_battle_action(db,snapshot)
    return result


def target_allowed(db,actor,target_type,target_id):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():return True
    effects=[json.loads(row[0]) for row in db.execute("SELECT data_json FROM combat_effects WHERE active=1 AND target_id=? AND json_extract(data_json,'$.skill')='provocacao'",(actor,))]
    if not any(e.get('failed') for e in effects):return True
    if target_type=='character':return target_id=='vezemir'
    row=db.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?',(target_id,)).fetchone()
    return bool(row and row[0]=='vezemir')


def target_turn(db,participant,now,request_id):
    if not participant:return
    from .dorn_spells import target
    for identity,raw in db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.skill')='provocacao'",(participant['target_type'],participant['target_id'])).fetchall():
        effect=json.loads(raw)
        if effect.get('failed') and int(effect.get('guaranteed_turns') or 0)>0:
            effect['guaranteed_turns']-=1
            db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),identity))
            append_session_ledger_event(db,source_type='provocation_save',source_id=request_id+':'+identity,event_kind='state',actor_id=participant['target_id'],actor_name=participant['name'],actor_role='gm',character_id='vezemir',title=f"{participant['name']} — Provocação: turno obrigatório contra Vezemir; sem nova JP",detail={'guaranteed_turn':True},visibility='table',created_at=now)
            continue
        try:victim=target(db,participant['target_type'],participant['target_id'])
        except ValueError:
            db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(identity,));continue
        rolled=int(roll_formula('1d20')['total']);bonus=int(victim['defenses'].get('saving_throw_bonus') or 0)-2;jp=int(victim['defenses']['saving_throw'])
        if db.execute("SELECT 1 FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.necro_spell')='aterrorrizar'",(participant['target_type'],participant['target_id'])).fetchone():bonus-=2
        success=rolled+bonus>=jp;effect['failed']=not success
        effect['guaranteed_turns']=0 if success else 1
        db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?',(json.dumps(effect),int(not success),identity))
        append_session_ledger_event(db,source_type='provocation_save',source_id=request_id+':'+identity,event_kind='roll',actor_id=participant['target_id'],actor_name=participant['name'],actor_role='gm',character_id='vezemir',title=f"{participant['name']} — JP contra Provocação: {rolled}+{bonus} / {jp}; "+('resistiu' if success else 'só pode atacar Vezemir'),detail={'d20':rolled,'bonus':bonus,'saving_throw':jp,'success':success},visibility='table',created_at=now)


def damage_penalty(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():return 0
    return db.execute("SELECT COUNT(*) FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.skill')='provocacao' AND json_extract(data_json,'$.failed')=1 AND target_id IN (SELECT id FROM session_workspace_tokens WHERE current_hp>0)").fetchone()[0]


def kill_reward(db,actor,kind,identity,now):
    if actor!='vezemir' or not active_frenzy(db):return
    if not db.execute("SELECT 1 FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.skill')='provocacao' AND json_extract(data_json,'$.failed')=1",(kind,identity)).fetchone():return
    row=db.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone();state=json.loads(row[0])
    resource=next((r for r in state.get('resources',[]) if r['key']=='provocacao'),None)
    if resource and resource['current']<resource['maximum']:
        resource['current']=resource['maximum']
        db.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id='vezemir'",(json.dumps(state),now))
        append_session_ledger_event(db,source_type='provocation_refund',source_id='refund:'+identity,event_kind='action',actor_id='vezemir',actor_name='Vezemir',actor_role='player',character_id='vezemir',title='Frenesi: inimigo provocado derrotado; uso de Provocação recuperado',detail={'ability_id':'provocacao'},visibility='table',created_at=now)
