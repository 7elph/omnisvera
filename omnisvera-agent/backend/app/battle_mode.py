"""Transactional map staging for the opt-in battle interface. No sheet copies."""
import json
import uuid
import sqlite3


def row(db, sql, args=()):
    cursor = db.cursor()
    cursor.row_factory = sqlite3.Row
    return cursor.execute(sql, args).fetchone()


def stage_battle(db, encounter, now, *, participants=None):
    arena = row(db, "SELECT * FROM session_workspace_maps WHERE id=?", (encounter['map_id'],))
    if arena is None or not arena['visible_to_players']:
        raise ValueError('Escolha um mapa de combate disponível para jogadores')
    if row(db, "SELECT name FROM sqlite_master WHERE type='table' AND name='deleted_workspace_maps'") and row(db, 'SELECT id FROM deleted_workspace_maps WHERE id=?', (arena['id'],)):
        raise ValueError('Este mapa foi removido da biblioteca')
    previous = row(db, 'SELECT map_id FROM session_workspace_state WHERE id=1')
    if previous is None:
        raise ValueError('Abra primeiro um mapa de exploração na Mesa')
    if participants is None:
        encounter['return_map_id'] = previous['map_id']
        encounter['return_tokens'] = []
    for index, participant in enumerate(encounter['participants'] if participants is None else participants):
        if participant['target_type'] == 'character':
            token = row(db, "SELECT * FROM session_workspace_tokens WHERE character_id=? AND token_type='character' ORDER BY (map_id=?) DESC,(map_id=?) DESC,id LIMIT 1", (participant['target_id'], arena['id'], previous['map_id']))
        else:
            token = row(db, 'SELECT * FROM session_workspace_tokens WHERE id=?', (participant['target_id'],))
        created = token is None
        if created:
            if participant['target_type'] != 'character':
                raise ValueError('Participante não encontrado no mapa')
            token_id = 'battle:' + uuid.uuid4().hex
            db.execute("INSERT INTO session_workspace_tokens(id,token_type,character_id,name,created_at,updated_at) VALUES (?,'character',?,?,?,?)",
                       (token_id, participant['target_id'], participant.get('name', participant['target_id']), now, now))
            token = row(db, 'SELECT * FROM session_workspace_tokens WHERE id=?', (token_id,))
        encounter['return_tokens'].append({key: token[key] for key in ('id', 'map_id', 'latitude', 'longitude', 'visible_to_players')} | {'created': created})
        participant['token_id'] = token['id']
        sheet = json.loads(token['sheet_json'] or '{}')
        if sheet.pop('combat_retired', None):
            db.execute('UPDATE session_workspace_tokens SET sheet_json=? WHERE id=?', (json.dumps(sheet), token['id']))
        # Only explicitly selected participants become visible in the public arena.
        # Preserve the GM's placement. Only brand-new, unpositioned PC pins
        # receive a default formation; initiative must not move existing pins.
        latitude = 15 + (index % 8) * 10 if created else token['latitude']
        longitude = (25 if participant['target_type'] == 'character' else 75) if created else token['longitude']
        db.execute('UPDATE session_workspace_tokens SET map_id=?,latitude=?,longitude=?,visible_to_players=1,updated_at=? WHERE id=?',
                   (arena['id'], latitude, longitude, now, token['id']))
    switch_map(db, arena['id'], now)


def switch_map(db, map_id, now):
    selected = row(db, 'SELECT * FROM session_workspace_maps WHERE id=?', (map_id,))
    if selected:
        db.execute('UPDATE session_workspace_state SET map_id=?,map_title=?,map_image_path=?,view_zoom=1,view_scroll_left=0,view_scroll_top=0,updated_at=? WHERE id=1',
                   (selected['id'], selected['title'], selected['image_path'], now))


def restore_exploration(db, encounter, now):
    for token in encounter.get('return_tokens', []):
        if token['created']:
            db.execute('DELETE FROM session_workspace_tokens WHERE id=?', (token['id'],))
        else:
            db.execute('UPDATE session_workspace_tokens SET map_id=?,latitude=?,longitude=?,visible_to_players=?,updated_at=? WHERE id=?',
                       (token['map_id'], token['latitude'], token['longitude'], token['visible_to_players'], now, token['id']))
    switch_map(db, encounter.get('return_map_id'), now)


def require_actor_alive(db, actor_id):
    state = row(db, 'SELECT state_json FROM character_states WHERE profile_id=?', (actor_id,))
    if state:
        hp = json.loads(state['state_json']).get('current_hp')
    else:
        token = row(db, 'SELECT current_hp FROM session_workspace_tokens WHERE id=?', (actor_id,))
        hp = token['current_hp'] if token else None
    if hp is not None and int(hp) <= 0:
        from .vezemir_skills import survives
        if survives(db,actor_id,hp):return
        raise ValueError('Participante a 0 PV não pode executar ações de combate')


def turn_identity(snapshot):
    encounter = snapshot.get('encounter') or {}
    if not encounter.get('active') or not encounter.get('battle_mode') or not encounter.get('participants'):
        return None
    current = encounter['participants'][encounter.get('turn_index', 0)]
    return [encounter.get('started_at'), encounter.get('turn_sequence'), current['target_type'], current['target_id']]


def require_consumable_turn(db, snapshot, actor_id):
    from .monster_conditions import assert_can_act
    assert_can_act(db,actor_id)
    encounter = snapshot.get('encounter') or {}
    if turn_identity(snapshot) is None:
        return
    require_actor_alive(db, actor_id)
    if encounter['participants'][encounter.get('turn_index', 0)]['target_id'] != actor_id:
        raise ValueError('Aguarde o turno deste participante')
    if encounter.get('consumable_used'):
        raise ValueError('Apenas um consumível por turno; o ataque continua independente')


def commit_consumable_turn(db, snapshot):
    if turn_identity(snapshot) is not None:
        snapshot['encounter']['consumable_used'] = True
        db.execute('UPDATE combat_effect_clock SET encounter_json=?,version=version+1 WHERE id=1', (json.dumps(snapshot['encounter']),))


def require_battle_turn(db, snapshot, actor_id, target_type=None, target_id=None, *, attack_count=1, attack_limit=1, resolution_id=None, auxiliary=False):
    require_actor_alive(db, actor_id)
    from .monster_conditions import assert_can_act
    assert_can_act(db,actor_id)
    encounter = snapshot.get('encounter') or {}
    if not encounter.get('active') or not encounter.get('battle_mode'):
        return
    participants = encounter['participants']
    if not participants:
        raise ValueError('Não há participantes aptos; encerre o combate')
    current = participants[encounter.get('turn_index', 0)]
    if current['target_id'] != actor_id:
        raise ValueError('Aguarde o turno deste participante')
    if encounter.get('pending_attack') and encounter['pending_attack'] != resolution_id:
        raise ValueError('Existe um ataque pendente. Retome a prévia ou passe o turno; fechar a janela não permite rerrolar.')
    if encounter.get('action_committed') and not auxiliary:
        raise ValueError('A ação deste turno já foi confirmada. Passe o turno; intervenções são resolvidas pelo Mestre.')
    used = int(encounter.get('attacks_used') or 0)
    limit = min(int(encounter.get('attack_limit') or attack_limit), attack_limit)
    if not auxiliary and used + attack_count > limit:
        raise ValueError('Não há ataques suficientes restantes neste turno')
    require_battle_target(db, snapshot, target_type, target_id)
    if target_type and target_id:
        from .vezemir_skills import target_allowed
        if not target_allowed(db,actor_id,target_type,target_id):
            raise ValueError('Provocação: neste turno esta criatura só pode atacar Vezemir')


def require_battle_target(db, snapshot, target_type, target_id):
    encounter = snapshot.get('encounter') or {}
    if encounter.get('active') and encounter.get('battle_mode') and target_id is not None:
        participants = encounter.get('participants') or []
        identities = {(p['target_type'], p['target_id']) for p in participants}
        if target_type == 'token':
            token = row(db, 'SELECT character_id,map_id,token_type FROM session_workspace_tokens WHERE id=?', (target_id,))
            if token is None or token['map_id'] != encounter['map_id']:
                raise ValueError('Alvo fora do mapa de combate')
            if token['token_type'] == 'character' and token['character_id']:
                target_type, target_id = 'character', token['character_id']
        if (target_type, target_id) not in identities:
            raise ValueError('O alvo não participa deste combate')


def commit_battle_action(db, snapshot, *, attack_count=1, attack_limit=1):
    encounter = snapshot.get('encounter') or {}
    if encounter.get('active') and encounter.get('battle_mode'):
        encounter.pop('pending_attack', None)
        encounter['attack_limit'] = min(int(encounter.get('attack_limit') or attack_limit), attack_limit)
        encounter['attacks_used'] = int(encounter.get('attacks_used') or 0) + attack_count
        encounter['action_committed'] = encounter['attacks_used'] >= encounter['attack_limit']
        db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))


def retire_defeated(db, now):
    """Remove incapacitated combatants, preserving sheets, loot and saved pins."""
    if not row(db, "SELECT name FROM sqlite_master WHERE name='combat_effect_clock'"):
        return []
    clock = row(db, 'SELECT encounter_json FROM combat_effect_clock WHERE id=1')
    encounter = json.loads(clock['encounter_json'] or '{}') if clock else {}
    members = encounter.get('participants') or []
    if not encounter.get('active') or not members:
        return []
    removed = []
    missing = set()
    for member in members:
        # A dismissed/expired clone has no pin left. It must not retain an
        # invisible turn merely because there is no HP row to inspect.
        if member['target_type'] == 'token' and row(db, 'SELECT id FROM session_workspace_tokens WHERE id=?', (member['target_id'],)) is None:
            removed.append(member)
            missing.add(member['target_id'])
            continue
        # Legacy initiative does not auto-retire ordinary 0 HP participants,
        # but an expired/dismissed pin cannot keep a turn in either interface.
        if not encounter.get('battle_mode'):
            continue
        try:
            require_actor_alive(db, member['target_id'])
        except ValueError:
            removed.append(member)
    if not removed:
        return []
    current_index = int(encounter.get('turn_index') or 0) % len(members)
    current = members[current_index]
    remaining = [p for p in members if p not in removed]
    next_member = next((members[(current_index + offset) % len(members)] for offset in range(len(members)) if members[(current_index + offset) % len(members)] in remaining), None)
    encounter['participants'] = remaining
    encounter['turn_index'] = remaining.index(next_member) if next_member else 0
    encounter.setdefault('defeated', []).extend(removed)
    if current in removed:
        encounter['turn_sequence'] = int(encounter.get('turn_sequence') or 0) + 1
        encounter['turn_started_at'] = now
        encounter['action_committed'] = False
        encounter['attacks_used'] = 0
        for key in ('pending_attack', 'consumable_used', 'attack_limit', 'movement'):
            encounter.pop(key, None)
    for member in removed:
        token_id = member.get('token_id') or (member['target_id'] if member['target_type'] == 'token' else None)
        token = row(db, 'SELECT sheet_json FROM session_workspace_tokens WHERE id=?', (token_id,)) if token_id else None
        if token:
            sheet = json.loads(token['sheet_json'] or '{}')
            sheet['combat_retired'] = True
            db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?', (json.dumps(sheet), now, token_id))
    db.execute('UPDATE combat_effect_clock SET encounter_json=?,version=version+1 WHERE id=1', (json.dumps(encounter),))
    # Losing the last turn in initiative still closes the round. Persist the
    # reduced roster first, so damage-over-time cannot restore retired members.
    if current in removed and next_member and members.index(next_member) < current_index:
        from .combat_effects import effect_snapshot, _tick_round_effects
        changes = []
        _tick_round_effects(db, effect_snapshot(db), changes, now)
        db.execute('UPDATE combat_effect_clock SET round=round+1 WHERE id=1')
        removed.extend(retire_defeated(db, now))
    if row(db, "SELECT name FROM sqlite_master WHERE name='session_ledger'"):
        from .session_ledger import append_session_ledger_event
        append_session_ledger_event(db, source_type='combat_retirement', source_id=uuid.uuid4().hex,
            event_kind='state', actor_id='master', actor_name='Mesa', actor_role='gm', character_id=None,
            title=', '.join(p.get('name') or p['target_id'] for p in removed) + (' fora do combate' if missing else ' fora do combate · 0 PV'),
            detail={'defeated': removed}, visibility='table', created_at=now)
    return removed
