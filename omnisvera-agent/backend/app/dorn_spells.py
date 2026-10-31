# -*- coding: utf-8 -*-
"""Tomo Arcano pp.56,58-59,82. Runs in the existing effect-command transaction.

Geometry/weight is declared by the GM: there is no inferred grid scale.
Durations use fictional seconds, never wall-clock time.
"""
import json
import uuid
from .dice_rolls import roll_formula, resolve_character_roll
from .combat_effects import change_hp

SPELLS = {'levitacao':'Levitacao', 'escuridao':'Escuridao', 'relampago':'Relampago'}
from .dorn_spell_pack import SPELLS as APPROVED_SPELLS
SPELLS.update(APPROVED_SPELLS)


def upgrade_darkness_restraints(path):
    """One-time, idempotent conversion of the former blindness to approved restraint.

    Never rolls, spends a resource, heals or edits a character sheet.
    """
    import sqlite3
    from contextlib import closing
    from datetime import datetime, timezone
    from .combat_effects import init_effects
    from .session_ledger import append_session_ledger_event
    init_effects(path)
    changed = []
    now = datetime.now(timezone.utc).isoformat()
    with closing(sqlite3.connect(path, timeout=30)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        for identity, raw in db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.spell')='escuridao'").fetchall():
            effect = json.loads(raw)
            if effect.get('immobilized'):
                continue
            try:
                victim = target(db, effect['target_type'], effect['target_id'])
                jp = int(victim['defenses'].get('saving_throw') or 0)
                if jp <= 0:
                    raise ValueError('JP ausente')
            except ValueError:
                db.execute('UPDATE combat_effects SET active=0 WHERE id=?', (identity,))
                changed.append(identity)
                continue
            effect.update(immobilized=True, turns_remaining=3, duration='manual', rounds=None, modifiers={}, saving_throw=jp, saving_throw_bonus=int(victim['defenses'].get('saving_throw_bonus') or 0), target_name=victim['name'], updated_at=now)
            for key in ('condition', 'remaining_seconds', 'infravision_blocked'):
                effect.pop(key, None)
            db.execute('UPDATE combat_effects SET data_json=? WHERE id=?', (json.dumps(effect, ensure_ascii=False), identity))
            changed.append(identity)
        if changed:
            db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
            append_session_ledger_event(db, source_type='darkness_rule_upgrade', source_id='restraint-v1:' + ','.join(changed), event_kind='state', actor_id='master', actor_name='Mestre', actor_role='gm', character_id=None, title='Escuridao atualizada para a imobilizacao aprovada de tres turnos e JP normal', detail={'effects': changed}, visibility='gm', created_at=now)
    return changed


def target(db, kind, identity):
    if kind == 'token':
        row = db.execute("SELECT * FROM session_workspace_tokens WHERE id=? AND token_type!='location'", (identity,)).fetchone()
        if not row:
            raise ValueError('Criatura nao encontrada')
        columns = [r[1] for r in db.execute('PRAGMA table_info(session_workspace_tokens)')]
        record = dict(zip(columns, row))
        sheet = json.loads(record['sheet_json'] or '{}')
        from .monster_contacts import identity as monster_identity
        if monster_identity(sheet)=='esfera-da-aniquilacao':raise ValueError('Perigo de cenário sem PV: use o comando de contato')
        if record.get('character_id'):
            return target(db, 'character', record['character_id'])
        if record.get('current_hp') is None or record['current_hp'] <= 0:
            raise ValueError('Alvo sem PV ou derrotado')
        return {'type': kind, 'id': identity, 'name': record['name'], 'defenses': {'saving_throw': sheet.get('saving_throw'), 'saving_throw_bonus': sheet.get('saving_throw_bonus', 0)}, 'attributes': sheet.get('attributes') or {}}
    if kind != 'character':
        raise ValueError('Tipo de alvo invalido')
    state = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (identity,)).fetchone()
    row = db.execute('SELECT data_json FROM character_sheets WHERE profile_id=?', (identity,)).fetchone()
    if not state or not row:
        raise ValueError('Personagem sem ficha ou incapacitado')
    from .vezemir_skills import survives
    hp=int(json.loads(state[0]).get('current_hp') or 0)
    if hp<=0 and not survives(db,identity,hp):
        raise ValueError('Personagem sem ficha ou incapacitado')
    sheet = json.loads(row[0])
    override = db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?', (identity,)).fetchone()
    overrides = json.loads(override[0]) if override else {}
    return {'type': kind, 'id': identity, 'name': overrides.get('name') or identity,
            'defenses': {'saving_throw': overrides.get('advancement_saving_throw', sheet.get('character_class', {}).get('saving_throw'))},
            'attributes': {**sheet.get('attributes', {}), **overrides.get('attributes', {})}}


def save(db, victim, attribute):
    from .character_play import attribute_modifier
    blinded = any(json.loads(row[0]).get('condition') == 'magical_darkness' for row in db.execute('SELECT data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=?', (victim['type'], victim['id'])))
    from .combat_effects import effect_snapshot
    effects = [e for e in effect_snapshot(db)['effects'] if e['target_type'] == victim['type'] and e['target_id'] == victim['id']]
    penalty = (-2 if any(e.get('necro_spell') == 'aterrorrizar' or e.get('d20_penalty') for e in effects) else 0) + (-2 if attribute == 'dexterity' and any(e.get('environmental') for e in effects) else 0)
    from .item_specials import test_penalty
    penalty += test_penalty(effects)
    definition = {'name': victim['name'], 'defenses': {**victim['defenses'], 'saving_throw_bonus': int(victim['defenses'].get('saving_throw_bonus') or 0) + penalty + (-5 if blinded else 0)}}
    spec = resolve_character_roll(definition, [], 'saving_throw', attribute)
    from .monster_poison_runtime import current_attributes
    current=current_attributes(db,victim['type'],victim['id'])
    original = int(current.get(attribute, 10))
    if attribute=='strength' and attribute not in current:
        original+=sum(int(e.get('modifiers',{}).get('strength_bonus') or 0) for e in effects)
    bonus = attribute_modifier(original)
    roll = roll_formula(spec.formula)
    total = roll['total'] + bonus
    return dict(total=total, dice=roll['individual_results'], attribute_bonus=bonus, target=spec.target_value, success=total >= spec.target_value)


def add_effect(db, victim, spell, seconds, now, **extra):
    row = db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='dorn7'").fetchone()
    extra = {'magic_type': 'arcane', 'spell_circle': 3 if spell == 'relampago' else 2, 'caster_level': int(json.loads(row[0]).get('level') or 3) if row else 3, **extra}
    effect = dict(id='spell:' + uuid.uuid4().hex, target_type=victim['type'], target_id=victim['id'],
                  label=SPELLS[spell], source='DORN-7 · Tomo Arcano', duration='fictional_time', rounds=None,
                  remaining_seconds=seconds, modifiers={}, spell=spell, updated_at=now, **extra)
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)', (effect['id'], effect['target_type'], effect['target_id'], json.dumps(effect, ensure_ascii=False)))
    return effect


def elapse(db, snapshot, seconds, changes, now=None):
    from .monster_poison_runtime import advance_native_clock
    from datetime import datetime,timezone
    # Legacy once-per-command round bookkeeping must not be repeated/lost when
    # the same native advance is segmented at a poison's onset or expiration.
    if seconds>=10:
        for effect in snapshot['effects']:
            if effect.get('spell')!='levitacao':continue
            effect.pop('moved_turn_sequence',None)
            if effect.get('ranged_attack_round')==snapshot['round']:
                effect['levitation_ranged_penalty']=max(-5,int(effect.get('levitation_ranged_penalty',-1))-1)
                effect.pop('ranged_attack_round',None)
    advance_native_clock(db,snapshot,seconds,changes,now or datetime.now(timezone.utc).isoformat(),_elapse_plain)


def _elapse_plain(db, snapshot, seconds, changes, now=None):
    for effect in snapshot['effects']:
        if effect.get('duration') != 'fictional_time':
            continue
        effect['remaining_seconds'] = max(0, effect['remaining_seconds'] - seconds)
        db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?', (json.dumps(effect), int(effect['remaining_seconds'] > 0), effect['id']))
        if not effect['remaining_seconds']:
            from .monster_conditions import expire
            expire(db,effect,now)
            changes.append({'expired': effect['id']})


def confirmed_ranged(db, actor_id, attack, round_number):
    if attack.get('attack_id') != 'ranged':
        return
    for row in db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type='character' AND target_id=?", (actor_id,)).fetchall():
        effect = json.loads(row[1])
        if effect.get('spell') == 'levitacao':
            effect['ranged_attack_round'] = round_number
            db.execute('UPDATE combat_effects SET data_json=? WHERE id=?', (json.dumps(effect), row[0]))


def command(db,snapshot,action,payload,now):
    if action=='dorn_levitate_stabilize':
        row=db.execute('SELECT data_json FROM combat_effects WHERE id=? AND active=1',(payload.get('effect_id'),)).fetchone()
        if not row or json.loads(row[0]).get('spell')!='levitacao':
            raise ValueError('Levitacao nao esta ativa')
        effect=json.loads(row[0])
        encounter=snapshot.get('encounter') or {}
        if encounter.get('active'):
            from .battle_mode import require_battle_turn
            require_battle_turn(db, snapshot, effect['target_id'])
            members=encounter.get('participants') or []
            current=members[int(encounter.get('turn_index') or 0)%len(members)] if members else {}
            if (current.get('target_type'),current.get('target_id'))!=(effect['target_type'],effect['target_id']):
                raise ValueError('Aguarde o turno do receptor')
            if encounter.get('action_committed') or encounter.get('attacks_used'):
                raise ValueError('Estabilizar exige a rodada sem atacar')
            encounter.update(action_committed=True,attacks_used=1,attack_limit=1)
            db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
        effect['levitation_ranged_penalty']=-1
        effect.pop('ranged_attack_round',None)
        db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),effect['id']))
        return {'effect':effect}
    if action=='dorn_spell_time':
        seconds=payload.get('seconds')
        if type(seconds) is not int or not 1<=seconds<=86400:
            raise ValueError('Informe de 1 a 86400 segundos de tempo ficcional')
        changes=[]
        elapse(db,snapshot,seconds,changes,now)
        return {'elapsed_seconds':seconds,'changes':changes}
    if action=='dorn_spell_end':
        row=db.execute('SELECT data_json FROM combat_effects WHERE id=? AND active=1',(payload.get('effect_id'),)).fetchone()
        if not row or json.loads(row[0]).get('spell') not in SPELLS:
            raise ValueError('Efeito de magia nao encontrado')
        db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(payload['effect_id'],))
        return {'ended':payload['effect_id']}
    if action=='dorn_levitate_move':
        row=db.execute('SELECT data_json FROM combat_effects WHERE id=? AND active=1',(payload.get('effect_id'),)).fetchone()
        if not row or json.loads(row[0]).get('spell')!='levitacao':
            raise ValueError('Levitacao nao esta ativa')
        effect=json.loads(row[0])
        delta=payload.get('vertical_meters')
        if isinstance(delta,bool) or not isinstance(delta,(int,float)) or not -2<=delta<=2:
            raise ValueError('Levitacao permite subir/descer ate 2 m por rodada')
        encounter=snapshot.get('encounter') or {}
        sequence=snapshot['round']
        if encounter.get('active'):
            members=encounter.get('participants') or []
            current=members[int(encounter.get('turn_index') or 0)%len(members)] if members else {}
            if (current.get('target_type'),current.get('target_id'))!=('character','dorn7'):
                raise ValueError('Dorn move o receptor no proprio turno')
        if effect.get('moved_turn_sequence')==sequence:
            raise ValueError('Movimento vertical ja usado nesta rodada; avance tempo/rodada para continuar')
        effect['altitude_meters']=max(0,effect.get('altitude_meters',0)+delta)
        effect['moved_turn_sequence']=sequence
        db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),effect['id']))
        return {'effect':effect}
    spell=payload.get('spell_id')
    if spell not in SPELLS:
        raise ValueError('Magia nao suportada')
    if spell in APPROVED_SPELLS:
        from .dorn_spell_pack import command as approved_command
        return approved_command(db,snapshot,payload,now)
    row=db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='dorn7'").fetchone()
    overrides=json.loads(row[0]) if row else {}
    if not str(overrides.get('approved_build') or '').startswith('dorn-mage'):
        raise ValueError('Ficha aprovada de Dorn necessaria')
    caster=target(db,'character','dorn7')
    level=int(overrides.get('level') or 3)
    contract = None
    if spell == 'relampago':
        from .action_library import native_action_contract
        from .action_components import require_definition_revision
        contract = native_action_contract('technique:dorn7:relampago', level)
        require_definition_revision(payload, contract)
    encounter=snapshot.get('encounter') or {}
    if encounter.get('active'):
        from .battle_mode import require_battle_turn
        require_battle_turn(db, snapshot, 'dorn7')
        members=encounter.get('participants') or []
        current=members[int(encounter.get('turn_index') or 0)%len(members)] if members else {}
        if (current.get('target_type'),current.get('target_id'))!=('character','dorn7'):
            raise ValueError('Aguarde o turno de Dorn')
        if encounter.get('action_committed') or encounter.get('attacks_used'):
            raise ValueError('A acao deste turno ja foi usada')
    grid_lightning=spell=='relampago' and payload.get('grid_selection') is True
    if not grid_lightning and payload.get('position_confirmed') is not True:
        raise ValueError('Mestre deve confirmar alcance, area, peso e posicao plausivel')
    selected=payload.get('targets') or []
    if not isinstance(selected,list) or not 1<=len(selected)<=30:
        raise ValueError('Selecione de 1 a 30 alvos')
    victims=[target(db,str(t.get('type')),str(t.get('id'))) for t in selected]
    if len({(t['type'],t['id']) for t in victims})!=len(victims):
        raise ValueError('Alvo repetido, inclusive pin do mesmo personagem')
    if contract and len(victims)>contract['targeting']['max_targets']:
        raise ValueError(f"Relampago aceita ate {contract['targeting']['max_targets']} alvos")
    if grid_lightning:
        from .spatial_grid import check_attack_range
        map_ids=set()
        workspace_map = db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
        current_map = encounter.get('map_id') if encounter.get('active') else (workspace_map[0] if workspace_map else 'default')
        if payload.get('map_id') is not None and payload['map_id'] != current_map:
            raise ValueError('O mapa mudou. Selecione os alvos novamente.')
        for victim, selection in zip(victims,selected):
            if selection.get('type')!='token':
                raise ValueError('Selecione pins no mapa para Relampago')
            pin=db.execute('SELECT map_id,current_hp FROM session_workspace_tokens WHERE id=?',(selection['id'],)).fetchone()
            if not pin or (victim['type']=='token' and int(pin[1] or 0)<=0):
                raise ValueError('Alvo sem PV ou indisponivel')
            map_ids.add(pin[0])
            if payload.get('map_id') is not None and pin[0] != current_map:
                raise ValueError('Alvos fora do mapa selecionado')
            checked=check_attack_range(None,connection=db,actor_character_id='dorn7',target_type='token',target_id=selection['id'],slot='ranged',max_range_m=contract['range']['meters'])
            if not checked['checked']:
                raise ValueError('Relampago exige posicoes no grid')
        if len(map_ids)!=1:
            raise ValueError('Selecione alvos no mesmo mapa')
        if encounter.get('active') and next(iter(map_ids))!=encounter.get('map_id'):
            raise ValueError('Alvos fora do mapa do combate')
    state=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()[0])
    cost = contract['costs'][0]['amount'] if contract else 1
    key=contract['costs'][0]['key'] if contract else 'dorn_'+spell
    resource=next((r for r in state.get('resources',[]) if r['key']==key),None)
    if not resource or resource['current']<cost:
        raise ValueError('Sem preparacao disponivel')
    results=[]
    damage_roll = None
    if spell=='levitacao':
        if len(victims)!=1:
            raise ValueError('Levitacao aceita um unico receptor')
        weight=payload.get('weight_kg')
        distance=payload.get('distance_meters')
        if isinstance(weight,bool) or not isinstance(weight,(int,float)) or not 0<weight<=50*level:
            raise ValueError(f'Peso maximo: {50*level} kg')
        if isinstance(distance,bool) or not isinstance(distance,(int,float)) or not 0<=distance<=20*level:
            raise ValueError(f'Alcance maximo: {20*level} m')
        victim=victims[0]
        saving=save(db,victim,'constitution') if payload.get('unwilling') else None
        effect=None if saving and saving['success'] else add_effect(db,victim,spell,600*level,now,altitude_meters=0,vertical_meters_per_round=2,weight_kg=weight,levitation_ranged_penalty=-1)
        results.append({'target':victim['name'],'saving_throw':saving,'effect':effect})
    elif spell=='escuridao':
        mode=payload.get('mode','area')
        if mode!='area':
            raise ValueError('Tomo: Escuridao e area de 4,5 m, nao versao nos olhos do LB1')
        distance=payload.get('distance_meters')
        if isinstance(distance,bool) or not isinstance(distance,(int,float)) or not 0<=distance<=10*level:
            raise ValueError(f'Alcance maximo: {10*level} m')
        group='darkness:'+uuid.uuid4().hex
        for victim in victims:
            from .session6_rewards import add_restraint
            effect=add_restraint(db,victim['type'],victim['id'],now,label='Escuridao',
                saving_throw=victim['defenses'].get('saving_throw'),saving_throw_bonus=victim['defenses'].get('saving_throw_bonus',0),target_name=victim['name'],
                spell='escuridao',radius_meters=4.5,area_group=group)
            results.append({'target':victim['name'],'effect':effect})
    else:
        damage_roll=roll_formula(contract['resolution']['damage']['formula']) if contract else roll_formula('3d6')
        total_damage=int(damage_roll['total'])
        if 1 <= len(victims) <= 3:
            n = len(victims)
            base = total_damage // n
            rem = total_damage % n
            shares = []
            for i in range(n):
                shares.append(base + (1 if i < rem else 0))
            for idx,(victim, declaration) in enumerate(zip(victims,selected)):
                contacts=1
                saves=[save(db,victim,contract['resolution']['save']['attribute']) for _ in range(contacts)]
                saving={**saves[-1],'success':all(s['success'] for s in saves)}
                share = shares[idx]
                amount = share // 2 if saving['success'] else share
                hp=change_hp(db,victim['type'],victim['id'],-amount,now,damage_type='lightning',damage_context={'kind':'spell','magical':True})
                results.append({'target':victim['name'],'saving_throw':saving,'contact_saves':saves,'damage':hp['damage_taken'],'damage_before_defenses':amount,**hp})
        else:
            for victim, declaration in zip(victims,selected):
                contacts=1
                if type(contacts) is not int or not 1<=contacts<=10:
                    raise ValueError('Informe de 1 a 10 contatos do raio por criatura')
                saves=[save(db,victim,contract['resolution']['save']['attribute']) for _ in range(contacts)]
                saving={**saves[-1],'success':all(s['success'] for s in saves)}
                amount=damage_roll['total']//2 if saving['success'] else damage_roll['total']
                hp=change_hp(db,victim['type'],victim['id'],-amount,now,damage_type='lightning',damage_context={'kind':'spell','magical':True})
                results.append({'target':victim['name'],'saving_throw':saving,'contact_saves':saves,'damage':hp['damage_taken'],'damage_before_defenses':amount,**hp})
    from .action_components import spend_native_resource
    remaining=spend_native_resource(db,'dorn7',key,cost,now)
    if encounter.get('active'):
        encounter.update(action_committed=True,attacks_used=1,attack_limit=1,last_action={'actor':{'target_type':'character','target_id':'dorn7'},'kind':'spell','label':SPELLS[spell],'at':now})
        db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1',(json.dumps(encounter),))
    if spell == 'relampago' and damage_roll is None and contract:
        damage_roll = roll_formula(contract['resolution']['damage']['formula'])
    ret = {'spell':SPELLS[spell],'results':results,'resource_remaining':remaining}
    if contract and spell == 'relampago':
        ret['damage_roll'] = damage_roll
        ret['action_contract'] = {'ref':contract['ref'],'revision':contract['revision'],'level':level}
    return ret
