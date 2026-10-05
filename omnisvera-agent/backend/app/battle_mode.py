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
        # Only explicitly selected participants become visible in the public arena.
        db.execute('UPDATE session_workspace_tokens SET map_id=?,latitude=?,longitude=?,visible_to_players=1,updated_at=? WHERE id=?',
                   (arena['id'], 15 + (index % 8) * 10, 25 if participant['target_type'] == 'character' else 75, now, token['id']))
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


def require_battle_turn(db, snapshot, actor_id, target_type=None, target_id=None, *, attack_count=1, attack_limit=1):
    encounter = snapshot.get('encounter') or {}
    if not encounter.get('active') or not encounter.get('battle_mode'):
        return
    participants = encounter['participants']
    current = participants[encounter.get('turn_index', 0)]
    if current['target_id'] != actor_id:
        raise ValueError('Aguarde o turno deste participante')
    if encounter.get('action_committed'):
        raise ValueError('A ação deste turno já foi confirmada. Passe o turno; intervenções são resolvidas pelo Mestre.')
    used = int(encounter.get('attacks_used') or 0)
    limit = min(int(encounter.get('attack_limit') or attack_limit), attack_limit)
    if used + attack_count > limit:
        raise ValueError('Não há ataques suficientes restantes neste turno')
    if target_id is not None:
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
        encounter['attack_limit'] = min(int(encounter.get('attack_limit') or attack_limit), attack_limit)
        encounter['attacks_used'] = int(encounter.get('attacks_used') or 0) + attack_count
        encounter['action_committed'] = encounter['attacks_used'] >= encounter['attack_limit']
        db.execute('UPDATE combat_effect_clock SET encounter_json=? WHERE id=1', (json.dumps(encounter),))
