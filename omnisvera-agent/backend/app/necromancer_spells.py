"""Necromante: regras da campanha aprovadas em 13/10.

Uso diário primeiro; extras consomem slot memorizado do primeiro círculo.
Toque drena PV no início dos turnos; medo dura turnos individuais e dá -2 d20.
Efeitos antigos sem target_turn_duration mantêm o relógio de exploração.
"""
import json
import uuid

from .character_play import attribute_modifier
from .combat_effects import change_hp
from .dice_rolls import roll_formula
from .dorn_spells import target as spell_target
from .session_ledger import append_session_ledger_event

SPELLS = {'toque-sombrio': 'Toque Sombrio', 'aterrorizar': 'Aterrorizar'}
FREE_KEY = {'toque-sombrio': 'toque_sombrio', 'aterrorrizar': 'aterrorrizar'}
MEMORIZED_KEY = 'magias_de_1o_circulo'


def caster(db):
    row = db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id='morthak'").fetchone()
    overrides = json.loads(row[0]) if row else {}
    if overrides.get('specialization') != 'necromante':
        raise ValueError('Necromante não confirmado na ficha de Morthak')
    state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
    return overrides, state, int(overrides.get('level') or 3)


def save_difficult(db, victim, attribute):
    """JP: penalidade de -2 no d20 quando aterrorizado, conforme campanha."""
    from .dice_rolls import resolve_character_roll
    terrified = any(json.loads(row[0]).get('difficult_tests')
                    for row in db.execute("SELECT data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=?",
                                          (victim['type'], victim['id'])))
    base = int(victim['attributes'].get(attribute, 10))
    effective = base
    definition = {'name': victim['name'], 'defenses': {**victim['defenses'],
        'saving_throw_bonus':int(victim['defenses'].get('saving_throw_bonus') or 0) - (2 if terrified else 0)}}
    spec = resolve_character_roll(definition, [], 'saving_throw', attribute)
    # spec.formula is 1d20 plus the JP bonus (0 here); add the attribute only.
    bonus = attribute_modifier(effective)
    roll = roll_formula(spec.formula)
    total = roll['total'] + bonus
    return dict(total=total, dice=roll['individual_results'], attribute=attribute,
                base_attribute=base, effective_attribute=effective,
                target=spec.target_value, success=total >= spec.target_value,
                difficult=bool(terrified))


def victim_hit_dice(db, victim):
    if victim['type'] == 'character':
        row = db.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id=?",
                         (victim['id'],)).fetchone()
        if not row:
            return None
        return int(json.loads(row[0]).get('level') or 1)
    row = db.execute("SELECT sheet_json FROM session_workspace_tokens WHERE id=?", (victim['id'],)).fetchone()
    if not row:
        return None
    sheet = json.loads(row[0] or '{}')
    for key in ('hit_dice', 'dv'):
        value = sheet.get(key)
        if isinstance(value, bool):
            continue
        try:
            if value is not None:
                import re
                from fractions import Fraction
                match=re.fullmatch(r'\s*(\d+(?:/\d+)?)(?:\s*[+-]\s*\d+)?\s*',str(value))
                if match:
                    amount=float(Fraction(match[1]))
                    if amount>0:return amount
        except (TypeError, ValueError, ZeroDivisionError):
            continue
    return None


def touch_rider_for(db_path, target_type, target_id):
    import sqlite3
    from contextlib import closing
    with closing(sqlite3.connect(str(db_path))) as db:
        return touch_rider(db, spell_target(db, target_type, target_id))


def touch_rider(db, victim):
    """Approved HP damage-over-time; d6 is rolled on entering target turns."""
    return {'dot_hp':True}


def require_visible_target(db, kind, identity, role):
    if kind == 'token' and role != 'gm':
        row = db.execute('SELECT visible_to_players,map_id FROM session_workspace_tokens WHERE id=?', (identity,)).fetchone()
        if not row or not row[0]:
            raise PermissionError('Alvo não disponível para jogadores')
        map_row = db.execute('SELECT visible_to_players FROM session_workspace_maps WHERE id=?', (row[1],)).fetchone()
        if map_row and not map_row[0]:
            raise PermissionError('Mapa do alvo não disponível para jogadores')


def authorized_target(db, kind, identity, role):
    require_visible_target(db, kind, identity, role)
    return spell_target(db, kind, identity)


def living_touch_target(db, kind, identity, role):
    victim = authorized_target(db, kind, identity, role)
    sheet = {}
    if victim['type'] == 'token':
        row = db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?', (victim['id'],)).fetchone()
        sheet = json.loads(row[0] or '{}') if row else {}
    if (victim['id'] in {'morthak', 'dorn7'} or sheet.get('is_alive') is False
            or sheet.get('is_undead') or sheet.get('construct_traits')
            or sheet.get('summon', {}).get('technique') in {'levantar-esqueleto','animar-mortos'}
            or sheet.get('reanimated_by')):
        raise ValueError('Toque Sombrio exige alvo vivo; mortos-vivos e constructos não são válidos')
    return victim


def grid_distance_m(db, target_type, target_id):
    """Meters between Morthak's pin and the target on a logical grid.

    A configured current grid is authoritative. Legacy maps without a grid
    retain the assisted distance declaration; archived pins cannot supply it.
    """
    from .spatial_grid import distance_cells
    tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {'session_workspace_map_grids','session_workspace_entity_positions','session_workspace_state'}<=tables:return None
    clock=db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()
    encounter=json.loads(clock[0] or '{}') if clock else {}
    current=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
    map_id=encounter.get('map_id') if encounter.get('active') and encounter.get('map_id') else (current[0] if current else None)
    grid=db.execute('SELECT distance_rule,cell_size_m FROM session_workspace_map_grids WHERE map_id=?',(map_id,)).fetchone()
    if not grid:return None
    pins = db.execute("SELECT id, map_id FROM session_workspace_tokens WHERE character_id='morthak' AND map_id=? ORDER BY id",(map_id,)).fetchall()
    if target_type == "token":
        target = db.execute("SELECT id, map_id FROM session_workspace_tokens WHERE id=?", (target_id,)).fetchone()
    else:
        target = db.execute("SELECT id, map_id FROM session_workspace_tokens WHERE character_id=? AND map_id=? ORDER BY id LIMIT 1",
                            (target_id,map_id)).fetchone()
    if target is None or target[1]!=map_id:
        raise ValueError('Posicione o alvo no grid do mapa atual')
    target_id_resolved = target[0]
    mine = next(((p[0], p[1]) for p in pins if p[1] == map_id), None)
    if mine is None:
        raise ValueError('Posicione Morthak no grid do mapa atual')
    rule, cell = grid[0], grid[1]

    def pos(token_id):
        return db.execute("SELECT cell_x,cell_y FROM session_workspace_entity_positions"
                          " WHERE map_id=? AND token_id=?", (map_id, token_id)).fetchone()
    a, b = pos(mine[0]), pos(target_id_resolved)
    if not a or not b:
        raise ValueError('Posições lógicas ausentes no grid do mapa atual')
    return distance_cells(rule, [a[0], a[1]], [b[0], b[1]]) * cell


def touch_cost_key(state, use_memorized):
    free = next((r for r in state.get('resources', []) if r['key'] == FREE_KEY['toque-sombrio']), None)
    if free is None or int(free.get('maximum') or 0) < 1:
        raise ValueError('Recurso diário do Toque Sombrio ausente; confira a progressão ao nível 5')
    if int(free.get('current') or 0) >= 1:
        return {'key': FREE_KEY['toque-sombrio'], 'amount': 1}
    if use_memorized is True:
        return {'key': MEMORIZED_KEY, 'amount': 1}
    raise ValueError('Uso diário esgotado; confirme o consumo de magia memorizada (use_memorized=true)')


def add_effect(db, victim, label, source, now, **extra):
    effect = dict(id='necro:' + uuid.uuid4().hex, target_type=victim['type'], target_id=victim['id'],
                  label=label, source=source, duration='manual', rounds=None,
                  modifiers={}, updated_at=now, **extra)
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',
               (effect['id'], effect['target_type'], effect['target_id'], json.dumps(effect, ensure_ascii=False)))
    return effect


def touch_turn(db,participant,now,request_id,*,encounter=None):
    if not participant:return False
    rows=db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.dot_hp')=1",(participant['target_type'],participant['target_id'])).fetchall()
    for identity,raw in rows:
        effect=json.loads(raw)
        from .spell_effect_runtime import victim_turn_key
        key=victim_turn_key(encounter,participant,request_id)
        if effect.get('last_target_turn')==key:continue
        try:spell_target(db,participant['target_type'],participant['target_id'])
        except ValueError:
            db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(identity,));return False
        rolled=int(roll_formula('1d6')['total']);result=None
        effect['last_target_turn']=key
        db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),identity))
        if rolled<=3:result=change_hp(db,participant['target_type'],participant['target_id'],-1,now)
        from .monster_runtime import public_token
        visible=participant['target_type']=='character' or public_token(db,participant['target_id'])
        append_session_ledger_event(db,source_type='touch_dot',source_id=request_id+':'+identity,event_kind='roll',actor_id='morthak',actor_name='Morthak',actor_role='player',character_id='morthak',title=f"Toque Sombrio — {participant['name']}: d6 {rolled}; "+('perdeu 1 PV' if result else 'sem perda de PV'),detail={'ability_id':'toque-sombrio','d6':rolled,**(result or {})},visibility='table' if visible else 'gm',created_at=now)
        from .vezemir_skills import survives
        dead=result and result['hp_after']<=0 and not (participant['target_type']=='character' and survives(db,participant['target_id'],result['hp_after']))
        if dead:
            db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(identity,));return True
    return False


def finish_target_turn(db,participant):
    if not participant:return
    for identity,raw in db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.target_turn_duration')=1",(participant['target_type'],participant['target_id'])).fetchall():
        effect=json.loads(raw);effect['turns_remaining']=max(0,int(effect['turns_remaining'])-1)
        db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?',(json.dumps(effect),int(effect['turns_remaining']>0),identity))


def command(db, snapshot, action, payload, now, actor_id, actor_role):
    if actor_role != 'gm' and actor_id != 'morthak':
        raise PermissionError('Somente Morthak (ou o Mestre) conjura estas magias')
    if action == 'necro_spell_time':
        if actor_role != 'gm':
            raise PermissionError('Somente o Mestre avança o tempo de exploração')
        turns = payload.get('turns')
        if type(turns) is not int or not 1 <= turns <= 100:
            raise ValueError('Informe de 1 a 100 turnos de exploração')
        changes=[]
        for effect in snapshot['effects']:
            if effect.get('necro_spell') != 'aterrorrizar' or effect.get('target_turn_duration'): continue
            effect['turns_remaining'] = max(0,int(effect['turns_remaining']) - turns)
            db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?',
                (json.dumps(effect), int(effect['turns_remaining'] > 0), effect['id']))
            changes.append({'effect_id':effect['id'],'turns_remaining':effect['turns_remaining']})
        return {'elapsed_turns':turns,'changes':changes}
    if action == 'necro_spell_end':
        row = db.execute('SELECT data_json FROM combat_effects WHERE id=? AND active=1',
                         (payload.get('effect_id'),)).fetchone()
        if not row or not json.loads(row[0]).get('necro_spell'):
            raise ValueError('Efeito de Necromante não encontrado')
        db.execute('UPDATE combat_effects SET active=0 WHERE id=?', (payload['effect_id'],))
        return {'ended': payload['effect_id']}
    if action != 'necro_spell_cast':
        raise ValueError('Ação de Necromante desconhecida')
    spell = payload.get('spell_id')
    from .morthak_high_spells import SPELLS as HIGH_SPELLS,command as high_command
    if spell in HIGH_SPELLS:return high_command(db,snapshot,payload,now)
    if spell not in SPELLS:
        raise ValueError('Magia não suportada')
    overrides, state, level = caster(db)
    from .battle_mode import require_actor_alive
    require_actor_alive(db, 'morthak')
    encounter = snapshot.get('encounter') or {}
    if encounter.get('active'):
        from .battle_mode import require_battle_turn
        require_battle_turn(db, snapshot, 'morthak')
        members = encounter.get('participants') or []
        current = members[int(encounter.get('turn_index') or 0) % len(members)] if members else {}
        if (current.get('target_type'), current.get('target_id')) != ('character', 'morthak'):
            raise ValueError('Aguarde o turno de Morthak')
        if encounter.get('action_committed') or encounter.get('attacks_used'):
            raise ValueError('A ação deste turno já foi usada')
    if spell == 'toque-sombrio':
        raise ValueError('Toque Sombrio usa o fluxo de ataque (toque, 1d4); chame pela técnica, não por conjuração direta')
    # Aterrorizar: raio 9m + 3m/nível; 1d6 turnos individuais + nível.
    reach = 9 + 3 * level
    selected = payload.get('targets') or []
    if not selected:
        from .vezemir_skills import combat_units
        selected=[{'type':'token','id':u['id']} for u in combat_units(db,'morthak') if u['meters']<=reach]
    if not isinstance(selected, list) or not 1 <= len(selected) <= 30:
        raise ValueError('Selecione de 1 a 30 alvos')
    selected=[dict(declaration) for declaration in selected]
    manual_confirmation = payload.get('position_confirmed') is True
    staged = []
    for declaration in selected:
        victim = authorized_target(db, str(declaration.get('type')), str(declaration.get('id')), actor_role)
        distance = grid_distance_m(db, str(declaration.get('type')), str(declaration.get('id')))
        auto = distance is not None
        if not auto:distance = declaration.get('distance_meters')
        if isinstance(distance, bool) or not isinstance(distance, (int, float)) or not 0 <= distance <= reach:
            raise ValueError(f'Alcance máximo: {reach} m por alvo declarado')
        declaration['distance_meters'] = distance
        declaration['distance_auto'] = auto
        staged.append((victim, declaration))
    if not manual_confirmation and not all(d.get('distance_auto') for _, d in staged):
        raise ValueError('Mestre deve confirmar alcance, área e posição plausível')
    victims = []
    for victim, declaration in staged:
        declared_dv = declaration.get('dv')
        persisted_dv = victim_hit_dice(db, victim)
        if persisted_dv is not None:
            dv = persisted_dv
        elif declared_dv is None:
            dv = None
        elif isinstance(declared_dv, bool) or not isinstance(declared_dv, int) or not 1 <= declared_dv <= 99:
            raise ValueError('DV declarado inválido (1-99)')
        else:
            if actor_role != 'gm':
                raise ValueError('DV ausente na ficha; peça ao Mestre para configurar o alvo')
            dv = declared_dv
        if dv is None:
            raise ValueError('DV ausente na ficha; peça ao Mestre para configurar o alvo')
        if dv is not None and dv < 2:
            from .dice_rolls import resolve_character_roll
            resolve_character_roll({'defenses':victim['defenses']}, [], 'saving_throw', 'wisdom')
        victims.append((victim, dv))
    if len({(victim['type'],victim['id']) for victim, _ in victims}) != len(victims):
        raise ValueError('Alvo repetido, inclusive pin do mesmo personagem')
    turns = int(roll_formula('1d6')['total']) + level
    key = FREE_KEY['aterrorrizar']
    resource = next((r for r in state.get('resources', []) if r['key'] == key), None)
    if resource is None or int(resource.get('maximum') or 0) < 1:
        raise ValueError('Recurso diário de Aterrorizar ausente; confira a progressão ao nível 5')
    if int(resource.get('current') or 0) >= 1:
        resource['current'] -= 1
        cost_source = 'daily'
    elif payload.get('use_memorized') is True:
        slot = next((r for r in state.get('resources', []) if r['key'] == MEMORIZED_KEY), None)
        if slot is None or int(slot.get('current') or 0) < 1:
            raise ValueError('Sem magia memorizada de 1º círculo para o uso adicional')
        slot['current'] -= 1
        cost_source = 'memorized'
    else:
        raise ValueError('Uso diário esgotado; confirme o consumo de magia memorizada (use_memorized=true)')
    results = []
    for victim, dv in victims:
        if dv is None:
            results.append({'target': victim['name'], 'skipped': 'DV desconhecido; Mestre adjudica manualmente'})
            continue
        if dv >= 2:
            results.append({'target': victim['name'], 'skipped': f'DV {dv} imune (alvos: menos de 2 DV)'})
            continue
        saving = save_difficult(db, victim, 'wisdom')
        if saving['success']:
            results.append({'target': victim['name'], 'saving_throw': saving, 'effect': None})
            continue
        effect = add_effect(db, victim, 'Aterrorizado', 'Morthak · Aterrorizar', now,
                            necro_spell='aterrorrizar', difficult_tests=True,
                            magic_type='arcane',spell_circle=1,caster_level=level,
                            turns_remaining=turns, turns_total=turns,
                            target_turn_duration=True,until=f'{turns} turnos individuais do alvo')
        results.append({'target': victim['name'], 'saving_throw': saving, 'effect': effect})
    db.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=\'morthak\'',
               (json.dumps(state, ensure_ascii=False), now))
    if encounter.get('active'):
        encounter.update(action_committed=True, attacks_used=1, attack_limit=1,
                         last_action={'actor': {'target_type': 'character', 'target_id': 'morthak'},
                                      'kind': 'spell', 'label': SPELLS[spell], 'at': now})
        db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))
    return {'spell': SPELLS[spell], 'cost_source': cost_source, 'results': results,
            'position': 'grid' if all(d.get('distance_auto') for d in selected) else 'manual',
            'duration_turns': turns, 'resource_remaining': resource['current']}
