"""Air deadlines on the native fictional clock, never wall-clock resident timers.

Protection here concerns respiration only: no poison/gaze/gas-save immunity.
The caller supplies the deadline; 60 seconds belongs to the portable hole.
"""
import json
import uuid
from functools import lru_cache
from pathlib import Path
from .inventory_conditions import read_condition

MEDAL='item-magico-medalhao-de-adaptacao'


@lru_cache(maxsize=1)
def _reviewed_traits():
    characters=json.loads((Path(__file__).parent/'data/session_abilities.json').read_text(encoding='utf-8'))['characters']
    reviewed={'nao-vida-consciente-vampiro','nao-vida-consciente-esqueleto'}
    return {identity for identity,abilities in characters.items() if any(a.get('id') in reviewed for a in abilities)}


def protection(db,kind,identity):
    from .monster_conditions import _canonical
    kind,identity=_canonical(db,kind,identity)
    if kind=='character':
        from .magic_passives import equipped
        row=equipped(db,identity,MEDAL)
        if row and not (read_condition(db,row['id']) or {}).get('destroyed'):
            return 'Medalhão de Adaptação'
        from .construct_rules import is_construct
        if is_construct(db,identity):return 'Corpo Artificial · não respira'
        # These two reviewed traits explicitly say breathing is unnecessary.
        if identity in _reviewed_traits():return 'Não-Vida Consciente'
    else:
        row=db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
        if not row:return None
        sheet=json.loads(row[0] or '{}')
        if sheet.get('requires_breathing') is False or sheet.get('is_construct') is True or sheet.get('is_undead') is True:
            return 'Natureza cadastrada · não respira'
        summon=sheet.get('summon') or {}
        from .summon_profiles import PROFILES
        if summon.get('caster')=='morthak' and summon.get('technique') in PROFILES:
            return 'Morto-vivo invocado · não respira'
        if (sheet.get('source') or {}).get('monster_id'):
            from .monster_catalog import get_catalog_monster
            from .damage_profiles import normalized
            monster=get_catalog_monster(sheet['source']['monster_id'])
            if normalized((monster or {}).get('category')) in {'morto-vivo','morto vivo','undead','constructo','construct'}:
                return 'Natureza do bestiário · não respira'
    return None


def begin(db,kind,identity,source,seconds,now):
    if type(seconds) is not int or seconds<=0:raise ValueError('Cadastre o prazo de ar em segundos ficcionais')
    from .monster_conditions import _canonical
    kind,identity=_canonical(db,kind,identity)
    stop(db,source,kind,identity)
    effect={'id':'air:'+uuid.uuid4().hex,'target_type':kind,'target_id':identity,
        'label':'Ar limitado','source':'Ambiente sem ar','duration':'fictional_time','rounds':None,
        'remaining_seconds':seconds,'modifiers':{},'air_exposure':True,'air_source':source,'updated_at':now}
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],kind,identity,json.dumps(effect)))


def stop(db,source,kind=None,identity=None):
    query="UPDATE combat_effects SET active=0 WHERE active=1 AND json_extract(data_json,'$.air_source')=?"
    args=[source]
    if kind is not None:query+=' AND target_type=? AND target_id=?';args.extend([kind,identity])
    db.execute(query,args)


def step(db,effect,seconds,now):
    """Handle only air effects; keep empty air active while a protected occupant lives."""
    if not effect.get('air_exposure'):return False
    remaining=max(0,int(effect['remaining_seconds'])-seconds)
    effect['remaining_seconds']=remaining
    if remaining or protection(db,effect['target_type'],effect['target_id']):
        db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),effect['id']))
        return True
    from .dorn_spells import target
    from .combat_effects import change_hp
    from .session_ledger import append_session_ledger_event
    try:victim=target(db,effect['target_type'],effect['target_id'])
    except ValueError:
        db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(effect['id'],));return True
    kind,identity=victim['type'],victim['id']
    row=db.execute('SELECT '+('state_json FROM character_states WHERE profile_id=?' if kind=='character' else 'current_hp FROM session_workspace_tokens WHERE id=?'),(identity,)).fetchone()
    hp=json.loads(row[0]).get('current_hp') if kind=='character' else row[0]
    db.execute('UPDATE combat_effects SET data_json=?,active=0 WHERE id=?',(json.dumps(effect),effect['id']))
    from .vezemir_skills import survives
    if hp is None or (hp<=0 and not (kind=='character' and survives(db,identity,hp))):return True
    result=change_hp(db,kind,identity,-int(hp)-(10 if kind=='character' and identity=='vezemir' else 0),now,ignore_temporary_hp=True)
    append_session_ledger_event(db,source_type='environment_asphyxia',source_id=effect['id'],event_kind='action',
        actor_id='system',actor_name='Ambiente',actor_role='system',character_id=identity if kind=='character' else None,
        title=f"Asfixia · {victim['name']}: ar esgotado",detail=result,visibility='gm',created_at=now)
    return True
