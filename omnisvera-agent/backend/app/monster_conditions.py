"""On-hit conditions in existing HP/effects/clock transactions and receipts."""
import hashlib
import json
import re
import uuid
from datetime import datetime,timezone
from .damage_profiles import normalized
from .dice_rolls import roll_formula
from .monster_riders import combat_rider_specs

_LABELS={'blinded':'Cegueira','paralyzed':'Paralisia','petrified':'Petrificação','poison_death':'Veneno','poison_damage':'Veneno'}
_DESCRIPTIONS={'blinded':'Não enxerga enquanto durar a cegueira.','paralyzed':'Não pode agir nem se mover enquanto durar a paralisia.',
    'petrified':'Não pode agir nem se mover. Permanece até remoção do efeito.',
    'poison_death':'Veneno ativo. O prazo segue o tempo ficcional; remover o efeito interrompe a contagem.'}


def attack_contract(db,actor_id,attack_index):
    if not str(attack_index).isdecimal():return None
    if not db.execute('SELECT 1 FROM session_workspace_tokens WHERE id=?',(actor_id,)).fetchone():return None
    from .monster_runtime import token_monster
    monster,_=token_monster(db,actor_id)
    if not monster:return None
    riders=[r for r in combat_rider_specs(monster)['on_hit'] if int(attack_index) in r['attack_indices']]
    if not riders:return None
    blob=json.dumps([monster['id'],monster.get('attacks'),monster.get('abilities')],sort_keys=True,ensure_ascii=False)
    return {'monster_id':monster['id'],'revision':hashlib.sha256(blob.encode()).hexdigest(),'riders':riders}


def validate_confirm(db,record):
    saved=record['breakdown'].get('monster_on_hit')
    if saved and attack_contract(db,record['actor_character_id'],record['attack_id'])!=saved:
        raise ValueError('As habilidades da criatura mudaram. Resolva novamente antes de confirmar.')


def _canonical(db,kind,identity):
    if kind=='token':
        row=db.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
        if row and row[0]:return 'character',row[0]
    return kind,identity


def _race(db,kind,identity):
    if kind=='character':
        from .character_play import _step_fields
        row=db.execute('SELECT data_json FROM character_sheets WHERE profile_id=?',(identity,)).fetchone()
        override=db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?',(identity,)).fetchone()
        data=json.loads(override[0] or '{}') if override else {}
        return normalized(data.get('race') or (_step_fields(json.loads(row[0]),'race').get('race') if row else ''))
    from .monster_runtime import token_monster
    from .monster_catalog import get_catalog_monster
    monster,_=token_monster(db,identity)
    original=get_catalog_monster(monster['id']) if monster else None
    name=normalized((original or {}).get('name'))
    return 'elfo' if re.match(r'^elfo(?: |$)',name) else ''


def _immune(db,kind,identity,spec):
    race=_race(db,kind,identity)
    if race in spec.get('immunity_races',[]) or ('elfo' in spec.get('immunity_races',[]) and re.match(r'^elfo(?: |$)',race)):return 'Imunidade racial declarada'
    poison=spec['effect'].startswith('poison') or spec.get('poison',False)
    condition=spec.get('condition') or spec['effect']
    if kind=='character':
        from .construct_rules import is_construct
        if poison and is_construct(db,identity):return 'Corpo Artificial: imunidade a veneno comum'
        if spec.get('natural_disease') and is_construct(db,identity):return 'Corpo Artificial: imunidade a doenças naturais'
        if spec.get('natural_disease') and _race(db,kind,identity)=='vampiro':return 'Imunidades Vampíricas: imunidade a doenças'
        if condition=='petrified' and is_construct(db,identity):return 'Forma Imutável: imunidade à transformação física'
        row=db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?',(identity,)).fetchone()
        stats=json.loads(row[0] or '{}') if row else {}
        if poison and 'poison' in (stats.get('damage_immunities') or []):return 'Imunidade a veneno'
        if condition in (stats.get('condition_immunities') or []):return 'Imunidade declarada na ficha'
        return None
    from .monster_runtime import token_monster,passive_data
    monster,sheet=token_monster(db,identity)
    if poison and 'poison' in (sheet.get('damage_immunities') or []):return 'Imunidade a veneno'
    if poison and any(item.get('type')=='poison' for item in passive_data(db,kind,identity).get('damage_immunities',[])):return 'Imunidade a veneno'
    if condition in (sheet.get('condition_immunities') or []):return 'Imunidade declarada na ficha'
    for ability in (monster or {}).get('abilities') or []:
        text=normalized(ability.get('description'))
        if spec.get('natural_disease') and re.search(r'imune.*doenc|imunidade.*doenc',text):return 'Imunidade declarada a doenças'
        if (poison or spec.get('exposure')=='gas') and re.search(r'nao .*alvo vivo.*(?:venenos|gases)',text):return 'Efeito exige alvo vivo'
        if condition=='petrified' and re.search(r'imune a qualquer tipo de petrificacao',text):return 'Imunidade à petrificação'
        if condition=='paralyzed' and re.search(r'imune.*paralis',text):return 'Imunidade à paralisia'
    return None


def _store(db,kind,identity,spec,actor_id,seconds,now):
    previous=db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.rider_id')=? AND json_extract(data_json,'$.source_token_id')=?",(kind,identity,spec['id'],actor_id)).fetchone()
    if previous and seconds is not None:
        old=json.loads(previous[1]).get('remaining_seconds',seconds)
        seconds=min(seconds,old) if spec['effect']=='poison_death' else max(seconds,old)
    effect={'id':previous[0] if previous else 'condition:'+uuid.uuid4().hex,'target_type':kind,'target_id':identity,
        'label':_LABELS[spec['effect']],'source':'Condição de combate','duration':'fictional_time' if seconds is not None else 'manual',
        'rounds':None,'modifiers':{},'monster_condition':spec['effect'],'rider_id':spec['id'],'source_token_id':actor_id,
        'source_duration_unit':spec['duration_unit'],'condition_description':_DESCRIPTIONS[spec['effect']],
        'blocks_actions':spec['effect'] in {'paralyzed','petrified'},'immobilized':spec['effect'] in {'paralyzed','petrified'},'updated_at':now}
    if seconds is not None:effect['remaining_seconds']=seconds
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1) ON CONFLICT(id) DO UPDATE SET data_json=excluded.data_json,active=1',
        (effect['id'],kind,identity,json.dumps(effect,ensure_ascii=False)))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return effect


def apply_spec(db,victim,spec,actor_id,now):
    """One native immunity/JP/effect pipeline for confirmed hits or exposures."""
    from .dorn_spells import save
    from .combat_effects import change_hp
    kind,identity=victim['type'],victim['id']
    immune=_immune(db,kind,identity,spec)
    if immune:return {'name':spec['name'],'effect':spec['effect'],'immune':immune}
    chance_result={}
    if spec['effect']=='disease_attribute':
        active=db.execute("SELECT 1 FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.monster_condition')='diseased' AND json_extract(data_json,'$.label')=?",(kind,identity,spec['name'])).fetchone()
        if active:return {'name':spec['name'],'effect':spec['effect'],'manual':True,
                          'manual_reason':'Reinfecção da mesma doença não tem regra de acúmulo/duração definida; efeito existente preservado.'}
        chance=roll_formula(spec['chance_formula'])
        triggered=int(chance['total'])<=int(spec['chance_success_max'])
        chance_result={'chance_roll':chance,'triggered':triggered}
        if not triggered:return {'name':spec['name'],'effect':spec['effect'],**chance_result}
    saving=save(db,victim,{'JPC':'constitution','JPD':'dexterity','JPS':'wisdom'}[spec['save']])
    result={'name':spec['name'],'effect':spec['effect'],'save':saving,'resisted':saving['success'],**chance_result}
    if spec['effect']=='parasite':
        if not saving['success']:
            from .monster_parasites import apply
            result.update(apply(db,victim,actor_id,now))
        return result
    if spec['effect'] in {'poison_attribute','poison_attribute_periodic','delayed_condition','delayed_attribute','disease_attribute'}:
        if not saving['success']:
            from .monster_poison_runtime import apply_poison
            result.update(apply_poison(db,victim,spec,actor_id,now))
        return result
    if spec['effect']=='poison_damage':
        rolled=roll_formula(spec['damage_formula']);amount=int(rolled['total'])
        if saving['success']:amount=amount//2 if spec['save_effect']=='halves' else 0
        hp=change_hp(db,kind,identity,-amount,now,damage_type='poison',damage_context={'kind':'effect','magical':False})
        result.update(damage_roll=rolled,damage_dealt=hp['damage_taken'],hp=hp)
    elif not saving['success']:
        duration=roll_formula(spec['duration_formula']) if spec['duration_formula'] else None
        seconds=max(0,int(duration['total']))*(600 if spec['duration_unit']=='turns' else 10) if duration else None
        if seconds is None or seconds>0:
            effect=_store(db,kind,identity,spec,actor_id,seconds,now)
            result.update(effect_id=effect['id'],duration_roll=duration,remaining_seconds=effect.get('remaining_seconds'),duration_unit=spec['duration_unit'])
    return result


def apply_on_hit(db,record,now):
    contract=record['breakdown'].get('monster_on_hit')
    if not contract:return []
    strikes=record['breakdown'].get('strikes') or [record]
    redirected={r['strike'] for r in record['breakdown'].get('reflection_result',{}).get('rolls',[]) if r.get('intercepted')}
    hits=[s for i,s in enumerate(strikes) if s.get('result')=='hit' and i not in redirected]
    from .dorn_spells import target
    try:victim=target(db,record['target_type'],record['target_id'])
    except ValueError:return []
    kind,identity=victim['type'],victim['id'];results=[]
    for strike in hits:
        for spec in contract['riders']:
            try:victim=target(db,kind,identity)
            except ValueError:return results
            results.append(apply_spec(db,victim,spec,record['actor_character_id'],now))
    return results


def assert_can_act(db,actor_id):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():return
    row=db.execute('SELECT 1 FROM character_states WHERE profile_id=?',(actor_id,)).fetchone()
    kind,identity=_canonical(db,'character' if row else 'token',actor_id)
    for raw in db.execute('SELECT data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=?',(kind,identity)):
        effect=json.loads(raw[0])
        if effect.get('monster_condition') and effect.get('blocks_actions'):
            raise ValueError(str(effect['label'])+': participante não pode agir nem se mover')


def expire(db,effect,now=None):
    if effect.get('monster_condition')!='poison_death':return
    from .combat_effects import change_hp
    from .dorn_spells import target
    from .session_ledger import append_session_ledger_event
    try:victim=target(db,effect['target_type'],effect['target_id'])
    except ValueError:return
    kind,identity=victim['type'],victim['id']
    row=db.execute('SELECT '+('state_json FROM character_states WHERE profile_id=?' if kind=='character' else 'current_hp FROM session_workspace_tokens WHERE id=?'),(identity,)).fetchone()
    current=int(json.loads(row[0])['current_hp']) if kind=='character' else int(row[0])
    when=now or datetime.now(timezone.utc).isoformat()
    # Same native instant-death convention as Magia da Morte, including Frenesi.
    result=change_hp(db,kind,identity,-current-(10 if kind=='character' and identity=='vezemir' else 0),when,ignore_temporary_hp=True)
    from .monster_runtime import public_token
    visible=kind=='character' or public_token(db,identity)
    append_session_ledger_event(db,source_type='monster_condition_expiry',source_id=effect['id'],event_kind='action',actor_id='master',actor_name='Mestre',actor_role='gm',character_id=identity if kind=='character' else None,
        title=f"Veneno: prazo esgotado para {victim['name']}",detail=result,visibility='table' if visible else 'gm',created_at=when)


def public_effect(effect):
    return {key:value for key,value in effect.items() if key in {'id','target_type','target_id','label','source','duration','rounds','modifiers','monster_condition','source_duration_unit','condition_description','blocks_actions','immobilized','remaining_seconds','updated_at','attribute','attribute_loss','attribute_multiplier','poison_phase','turns_remaining','campaign_rule'}}
