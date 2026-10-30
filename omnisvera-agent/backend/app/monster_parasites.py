"""Human-approved provisional campaign parasite; native effects, turns and action budget."""
import json
import uuid
from .dice_rolls import roll_formula

RULE = 'flagelo-provisional-v1'
DESCRIPTION = ('Regra provisória da campanha: contato exige JPC; falha causa 1d4 de dano '
               'no início dos próximos 3 turnos da vítima. Não acumula nem renova. '
               'Gastar a ação principal remove o parasita.')


def specs(monster):
    if monster.get('id') != 'flagelo-da-podridao':
        return []
    return [{'id': RULE, 'name': 'Infestação', 'ability_index': -1, 'description': DESCRIPTION,
             'attack_indices': [0], 'effect': 'parasite', 'save': 'JPC', 'save_effect': 'negates',
             'duration_formula': None, 'duration_unit': 'victim_turns', 'campaign_rule': RULE}]


def apply(db, victim, source_id, now):
    kind, identity = victim['type'], victim['id']
    old = db.execute("SELECT id FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.campaign_rule')=?", (kind, identity, RULE)).fetchone()
    if old:
        return {'effect_id': old[0], 'already_infested': True, 'campaign_rule': RULE}
    effect = {'id':'parasite:'+uuid.uuid4().hex, 'target_type':kind, 'target_id':identity,
              'label':'Infestação', 'source':'Regra provisória da campanha', 'duration':'manual',
              'rounds':None, 'turns_remaining':3, 'source_duration_unit':'victim_turns',
              'modifiers':{}, 'monster_condition':'parasite', 'campaign_rule':RULE,
              'condition_description':DESCRIPTION, 'source_token_id':source_id, 'updated_at':now}
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],kind,identity,json.dumps(effect,ensure_ascii=False)))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return {'effect_id':effect['id'], 'campaign_rule':RULE, 'turns_remaining':3}


def _emit(db, kind, identity, name, title, detail, now, source_id):
    from .session_ledger import append_session_ledger_event
    from .monster_runtime import public_token
    visible = kind == 'character' or public_token(db, identity)
    append_session_ledger_event(db,source_type='monster_parasite',source_id=source_id,event_kind='action',
        actor_id=identity,actor_name=name,actor_role='gm',character_id=identity if kind=='character' else None,
        title=title,detail=detail,visibility='table' if visible else 'gm',created_at=now)


def turn_start(db, participant, encounter, now, request_id):
    if not participant:
        return False
    kind, identity = participant['target_type'], participant['target_id']
    row = db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.campaign_rule')=?", (kind, identity, RULE)).fetchone()
    if not row:
        return False
    effect = json.loads(row[1])
    key = [encounter.get('started_at'), encounter.get('turn_sequence'), kind, identity]
    if effect.get('last_tick') == key:
        return False
    from .dorn_spells import target
    try:
        target(db, kind, identity)
    except ValueError:
        db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(row[0],))
        return False
    from .combat_effects import change_hp
    roll = roll_formula('1d4')
    hp = change_hp(db,kind,identity,-int(roll['total']),now)
    effect.update(turns_remaining=int(effect['turns_remaining'])-1,last_tick=key,updated_at=now)
    from .vezemir_skills import survives
    dead = hp['hp_after'] <= 0 and not (kind=='character' and survives(db,identity,hp['hp_after']))
    active = effect['turns_remaining'] > 0 and not dead
    db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?',(json.dumps(effect,ensure_ascii=False),int(active),row[0]))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    _emit(db,kind,identity,participant.get('name') or identity,
          f"Infestação · {participant.get('name') or identity}: {hp['damage_taken']} de dano",{'roll':roll,'hp':hp,'turns_remaining':effect['turns_remaining'],'campaign_rule':RULE},now,request_id+':parasite:'+identity)
    return dead


def remove(db, snapshot, actor_id, actor_role, payload, now, request_id):
    from .dorn_spells import target
    victim = target(db,str(payload.get('target_type') or ''),str(payload.get('target_id') or ''))
    kind, identity = victim['type'], victim['id']
    if actor_role != 'gm':
        controlled = kind=='character' and identity==actor_id
        if kind=='token':
            row=db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
            controlled=bool(row and (json.loads(row[0] or '{}').get('summon') or {}).get('caster')==actor_id)
        if not controlled:
            raise PermissionError('Você só pode remover o parasita da própria ficha ou invocação')
    row = db.execute("SELECT id FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.campaign_rule')=?",(kind,identity,RULE)).fetchone()
    if not row:
        raise ValueError('Este alvo não está infestado')
    from .battle_mode import require_battle_turn, commit_battle_action
    require_battle_turn(db,snapshot,identity)
    db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(row[0],))
    commit_battle_action(db,snapshot)
    result={'removed':row[0],'target_type':kind,'target_id':identity,'campaign_rule':RULE}
    _emit(db,kind,identity,victim['name'],victim['name']+' removeu o parasita usando sua ação',result,now,request_id)
    return result
