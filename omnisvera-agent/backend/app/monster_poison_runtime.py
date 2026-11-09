"""Complex poisons in native combat_effects and fictional-time transactions.

Base sheets/attributes are never rewritten. No second clock or turn system.
"""
import json
import math
import uuid
from .dice_rolls import roll_formula

LABELS={'strength':'Força','dexterity':'Destreza','constitution':'Constituição',
        'intelligence':'Inteligência','wisdom':'Sabedoria','charisma':'Carisma'}
KINDS={'poison_attribute','poison_attribute_periodic','delayed_condition','delayed_attribute','disease_attribute'}


def project_attributes(attributes,effects):
    result=dict(attributes or {})
    for key in LABELS:
        if result.get(key) is None:continue
        relevant=[e for e in effects if e.get('poison_runtime') and e.get('attribute')==key]
        multiplier=min([1]+[float(e.get('attribute_multiplier',1)) for e in relevant])
        loss=sum(int(e.get('attribute_loss',0)) for e in relevant)
        result[key]=max(0,math.floor(float(result[key])*multiplier)-loss)
        ceilings=[int(e['attribute_max']) for e in relevant if e.get('attribute_max') is not None]
        if ceilings:result[key]=min(result[key],min(ceilings))
    return result


def current_attributes(db,kind,identity):
    if kind=='character':
        from .character_play import _step_fields
        raw=db.execute('SELECT data_json FROM character_sheets WHERE profile_id=?',(identity,)).fetchone()
        overrides=db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?',(identity,)).fetchone()
        data=json.loads(raw[0]) if raw else {}
        attributes=dict(data.get('attributes') or _step_fields(data,'attributes'))
        attributes.update(json.loads(overrides[0] or '{}').get('attributes') or {} if overrides else {})
    else:
        raw=db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
        attributes=dict(json.loads(raw[0] or '{}').get('attributes') or {}) if raw else {}
    from .character_play import _number
    attributes={k:int(_number(v)) for k,v in attributes.items() if _number(v) is not None}
    if kind=='character' and db.execute("SELECT 1 FROM sqlite_master WHERE name='player_inventory'").fetchone():
        from .magic_equipment import attribute_bonuses
        inventory=[dict(zip(('item_path','quantity','equipped'),row)) for row in db.execute(
            'SELECT item_path,quantity,equipped FROM player_inventory WHERE profile_id=?',(identity,))]
        for key,bonus in attribute_bonuses(inventory).items():
            if key in attributes:attributes[key]+=bonus
    effects=[]
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():
        effects=[json.loads(r[0]) for r in db.execute('SELECT data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=?',(kind,identity))]
    if attributes.get('strength') is not None:
        attributes['strength']=int(attributes['strength'])+sum(int(e.get('modifiers',{}).get('strength_bonus',0)) for e in effects)
    return project_attributes(attributes,effects)


def _roll_seconds(formula,unit):
    if unit not in {'rounds','turns','days'}:raise ValueError('Unidade de duração do efeito não declarada')
    roll=roll_formula(formula);value=int(roll['total'])*{'rounds':10,'turns':600,'days':86400}[unit]
    if not 0<value<=604800:raise ValueError('Duração de veneno fora do limite')
    return value,roll


def _save(db,effect,active=True):
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET data_json=excluded.data_json,active=excluded.active',
        (effect['id'],effect['target_type'],effect['target_id'],json.dumps(effect,ensure_ascii=False),int(active)))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')


def _describe(effect):
    phase=effect['poison_phase'];spec=effect['poison_spec']
    effect.update(blocks_actions=False,immobilized=False,monster_condition='poison_pending' if phase=='latent' else 'poison_attribute')
    if spec['effect']=='disease_attribute':
        effect.update(label=spec['name'],monster_condition='diseased',
                      condition_description=f"{LABELS[effect['attribute']]} limitada a {spec['attribute_max']} enquanto durar a doença. A ficha base e os PV máximos permanecem preservados.")
    elif spec['effect']=='delayed_condition':
        label={'asleep':'Sono','paralyzed':'Paralisia'}[spec['condition']]
        effect['label']=f'Veneno · {label} pendente' if phase=='latent' else label
        effect['condition_description']='Veneno com início adiado; ainda pode agir.' if phase=='latent' else label+': não pode agir nem se mover até o efeito terminar.'
        if phase=='active':effect.update(monster_condition=spec['condition'],blocks_actions=True,immobilized=True)
    else:
        label=LABELS[effect['attribute']]
        effect['label']='Veneno · '+label
        if phase=='latent':effect['condition_description']=f'Veneno pendente: reduzirá {label} à metade após o atraso.'
        elif spec['effect']=='delayed_attribute':effect['condition_description']=f'{label} temporariamente reduzida à metade; frações seguem o piso inteiro do motor.'
        else:effect['condition_description']=f"Perda acumulada de {label}: {effect.get('attribute_loss',0)}. "+('Perda periódica encerrada.' if phase=='drained' else 'A ficha base permanece preservada.')


def apply_poison(db,victim,spec,actor_id,now):
    kind,identity=victim['type'],victim['id'];attribute=spec.get('attribute')
    attrs=current_attributes(db,kind,identity)
    if attribute and (attribute not in attrs or attrs[attribute] is None):
        return {'manual':True,'manual_reason':'Configure '+LABELS[attribute]+' do alvo para aplicar o efeito; nenhum atributo foi presumido.'}
    row=db.execute("SELECT data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.rider_id')=? AND json_extract(data_json,'$.source_token_id')=?",(kind,identity,spec['id'],actor_id)).fetchone()
    old=json.loads(row[0]) if row else None
    effect=old or {'id':'condition:'+uuid.uuid4().hex,'target_type':kind,'target_id':identity,'source':'Condição de combate',
        'duration':'manual','rounds':None,'modifiers':{},'poison_runtime':True,'poison_spec':spec,
        'rider_id':spec['id'],'source_token_id':actor_id,'attribute':attribute,'attribute_loss':0}
    result={};family=spec['effect']
    if family=='disease_attribute':
        duration,duration_roll=_roll_seconds(spec['duration_formula'],spec['duration_unit'])
        effect.update(poison_phase='active',remaining_seconds=duration,source_duration_unit=spec['duration_unit'],
                      attribute_max=int(spec['attribute_max']))
        result.update(attribute=attribute,attribute_before=int(attrs[attribute]),
                      attribute_after=min(int(attrs[attribute]),int(spec['attribute_max'])),
                      duration_seconds=duration,duration_roll=duration_roll)
    elif family=='poison_attribute':
        rolled=roll_formula(spec['amount_formula']);before=int(attrs[attribute]);loss=min(max(0,before-int(spec.get('floor',0))),max(0,int(rolled['total'])))
        effect.update(attribute_loss=int(effect.get('attribute_loss',0))+loss,poison_phase='drained',source_duration_unit='permanent')
        result.update(attribute=attribute,attribute_before=before,attribute_after=before-loss,attribute_roll=rolled)
    elif family=='poison_attribute_periodic':
        effect.setdefault('tick_remaining_seconds',int(spec['interval_seconds']))
        effect.setdefault('remaining_seconds',effect['tick_remaining_seconds'])
        effect.setdefault('poison_phase','draining');effect['source_duration_unit']='turns'
        result.update(attribute=attribute,next_tick_seconds=effect.get('tick_remaining_seconds'))
    else:
        delay,delay_roll=_roll_seconds(spec['delay_formula'],spec['delay_unit'])
        duration,duration_roll=_roll_seconds(spec['duration_formula'],spec['duration_unit'])
        if not old:effect.update(poison_phase='latent',remaining_seconds=delay,duration_remaining_seconds=duration)
        elif effect['poison_phase']=='latent':
            effect['remaining_seconds']=min(int(effect['remaining_seconds']),delay)
            effect['duration_remaining_seconds']=max(int(effect['duration_remaining_seconds']),duration)
        else:effect['remaining_seconds']=max(int(effect['remaining_seconds']),duration)
        effect['source_duration_unit']=spec['delay_unit'] if effect['poison_phase']=='latent' else spec['duration_unit']
        result.update(delay_roll=delay_roll,duration_roll=duration_roll,delay_seconds=delay,duration_seconds=duration)
    effect['updated_at']=now;_describe(effect);_save(db,effect)
    return {**result,'effect_id':effect['id'],'phase':effect['poison_phase'],'remaining_seconds':effect.get('remaining_seconds'),'duration_unit':effect['source_duration_unit']}


def _emit(db,effect,text,detail,now):
    from .session_ledger import append_session_ledger_event
    from .monster_runtime import public_token
    kind,identity=effect['target_type'],effect['target_id']
    visible=kind=='character' or public_token(db,identity)
    append_session_ledger_event(db,source_type='monster_poison_tick',source_id=uuid.uuid4().hex,event_kind='action',
        actor_id='master',actor_name='Mesa',actor_role='gm',character_id=identity if kind=='character' else None,
        title='Veneno — '+text,detail=detail,visibility='table' if visible else 'gm',created_at=now)


def _step_poison(db,effect,seconds,changes,now):
    from .dorn_spells import target
    try:victim=target(db,effect['target_type'],effect['target_id'])
    except ValueError:
        if effect['poison_spec']['effect'] in {'delayed_condition','delayed_attribute','disease_attribute'}:
            _save(db,effect,False);changes.append({'expired':effect['id'],'reason':'target_unavailable'});return
        effect['poison_phase']='drained';effect.pop('tick_remaining_seconds',None);effect.pop('remaining_seconds',None)
        _describe(effect);_save(db,effect);return
    spec=effect['poison_spec'];phase=effect['poison_phase']
    if phase=='latent':
        effect['remaining_seconds']-=seconds
        if effect['remaining_seconds']<=0:
            effect.update(poison_phase='active',remaining_seconds=effect.pop('duration_remaining_seconds'),source_duration_unit=spec['duration_unit'])
            if spec['effect']=='delayed_attribute':effect['attribute_multiplier']=float(spec['multiplier'])
            _describe(effect);_emit(db,effect,victim['name']+' · '+effect['label']+' começou',{'condition':effect['label'],'phase':'active'},now)
    elif phase=='active':
        effect['remaining_seconds']-=seconds
        if effect['remaining_seconds']<=0:
            _save(db,effect,False);changes.append({'expired':effect['id']});return
    elif phase=='draining':
        effect['tick_remaining_seconds']-=seconds;effect['remaining_seconds']=effect['tick_remaining_seconds']
        if effect['tick_remaining_seconds']<=0:
            attribute=effect['attribute'];attrs=current_attributes(db,effect['target_type'],effect['target_id'])
            if attribute not in attrs:
                effect['poison_phase']='drained';effect.pop('tick_remaining_seconds',None);effect.pop('remaining_seconds',None)
                _emit(db,effect,victim['name']+' · atributo ausente, dreno pendente',{'manual':True},now)
            else:
                before=int(attrs[attribute]);floor=int(spec['floor']);rolled=roll_formula(spec['amount_formula'])
                loss=min(max(0,before-floor),max(0,int(rolled['total'])));after=before-loss
                effect['attribute_loss']+=loss
                _emit(db,effect,f"{victim['name']} · {LABELS[attribute]} {before} → {after}",{'attribute':attribute,'before':before,'after':after,'roll':rolled},now)
                if after<=floor:
                    effect['poison_phase']='drained';effect.pop('tick_remaining_seconds',None);effect.pop('remaining_seconds',None)
                    if spec.get('lethal_at_floor') and after<=0:
                        from .monster_conditions import expire
                        expire(db,{**effect,'monster_condition':'poison_death'},now)
                else:effect['tick_remaining_seconds']=int(spec['interval_seconds']);effect['remaining_seconds']=effect['tick_remaining_seconds']
    effect['updated_at']=now;_describe(effect);_save(db,effect)


def advance_native_clock(db,snapshot,seconds,changes,now,plain_elapse):
    """Segment the existing clock at actual deadlines; no per-turn clock added."""
    remaining=seconds
    while remaining>0:
        poisons=[e for e in snapshot['effects'] if e.get('poison_runtime') and e.get('poison_phase') in {'latent','active','draining'}]
        if not poisons:plain_elapse(db,snapshot,remaining,changes,now);break
        deadlines=[int(e['remaining_seconds']) for e in poisons]
        deadlines.extend(int(e['remaining_seconds']) for e in snapshot['effects'] if e.get('duration')=='fictional_time' and e.get('remaining_seconds',0)>0)
        step=min([remaining,*[d for d in deadlines if d>0]])
        plain_elapse(db,snapshot,step,changes,now)
        for effect in poisons:_step_poison(db,effect,step,changes,now)
        remaining-=step
        # Re-read active flags/expiry after each boundary, in the same transaction.
        active={r[0] for r in db.execute('SELECT id FROM combat_effects WHERE active=1')}
        snapshot['effects'][:]=[e for e in snapshot['effects'] if e['id'] in active]
