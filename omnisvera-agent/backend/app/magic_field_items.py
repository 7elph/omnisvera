"""Inventory interactions that use private knowledge or persistent physical pairs."""
import hashlib
import json
import unicodedata
import uuid
from contextlib import closing
from datetime import datetime, timezone

from .dice_rolls import roll_formula
from .inventory_conditions import read_condition, save_condition
from .magic_equipment import identity
from .session_ledger import append_session_ledger_event
from .spatial_grid import connect, distance_cells, grid_record

CRYSTAL = 'item-magico-bola-de-cristal'
CRYSTAL_VARIANTS = {CRYSTAL + '-ordeira': False, CRYSTAL + '-caotica': True}
GLASSES = 'item-magico-oculos-da-rapida-leitura'
CUP = 'item-magico-copos-de-mensagem'
BOOK = 'item-magico-livro-das-linguas'
BOOTS = 'item-magico-botas-sem-pegadas'
VESSEL = 'item-magico-vaso-da-agua-ungueal'
NAILS = 'unhas-ungueais'
ITEMS = {CRYSTAL, GLASSES, CUP, BOOK, VESSEL}
OPERATIONS = {
    CRYSTAL: {'set_vision', 'observe'},
    GLASSES: {'set_document', 'read_document'},
    CUP: {'bind', 'listen', 'stop', 'message'},
    BOOK: {'set_languages', 'read_languages'},
    VESSEL: {'drink', 'clip', 'draw_water'},
}
GM_OPERATIONS = {'set_vision', 'set_document', 'set_languages', 'bind'}


def variants(parent):
    return [{**parent, 'id': key, 'source_parent_id': CRYSTAL,
             'name': 'Bola de Cristal ' + ('Caótica' if chaotic else 'Ordeira'),
             'alinhamento': 'caótico' if chaotic else 'ordeiro'}
            for key, chaotic in CRYSTAL_VARIANTS.items()]


def _item(db, access, owner, path):
    if access.mode != 'gm' and access.profile_id != owner:
        raise PermissionError('Item indisponível')
    row = db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=? AND quantity>0',
                     (owner, path)).fetchone()
    if not row:
        raise PermissionError('Item indisponível')
    key = identity(dict(row))
    if key in CRYSTAL_VARIANTS:
        key = CRYSTAL
    if key not in ITEMS:
        raise ValueError('Item sem essa interação')
    return row, key


def _state(db, row):
    return read_condition(db, row['id']) or {}


def _save(db, row, data, now):
    save_condition(db, row['id'], {**_state(db, row), 'field_item': data}, now)


def _cup_pair(db, row, data):
    pair = db.execute('SELECT * FROM player_inventory WHERE id=? AND quantity=1', (data.get('pair'),)).fetchone()
    if (not pair or row['quantity'] != 1 or pair['profile_id'] == row['profile_id']
            or identity(dict(pair)) != CUP):
        return None, {}
    partner = _state(db, pair).get('field_item', {})
    return (pair, partner) if partner.get('pair') == row['id'] else (None, {})


def inspect(path, access, owner, item_path):
    with closing(connect(path)) as db:
        row, key = _item(db, access, owner, item_path)
        data = _state(db, row).get('field_item', {})
        result = {'key': key}
        if key == CRYSTAL:
            observing = _observation(db, owner)
            result.update(subject=data.get('subject'), remaining=_remaining(row),
                          observing=bool(observing), variant_fixed=identity(dict(row)) in CRYSTAL_VARIANTS)
        elif key == GLASSES:
            result.update(title=data.get('title'), pages=data.get('pages'))
        elif key == CUP:
            pair, _ = _cup_pair(db, row, data)
            result.update(paired=pair is not None, listening=bool(pair and data.get('listening')))
            if access.mode == 'gm':
                candidates = db.execute('SELECT * FROM player_inventory WHERE quantity=1 AND profile_id!=?', (owner,))
                result['partners'] = [{'id': x['id'], 'owner': x['profile_id']} for x in candidates if identity(dict(x)) == CUP]
        elif key == BOOK:
            result.update(ready=bool(data.get('languages')))
        elif key == VESSEL:
            result.update(nails=_nail_effect(db, owner) is not None)
        if access.mode == 'gm':
            result['configuration'] = data
        return result


def _remaining(row):
    return max(0, min(3, int(row['charges_current']))) if row['charges_current'] is not None else 3


def _observation(db, owner):
    return db.execute("""SELECT id FROM combat_effects WHERE active=1 AND target_type='character'
        AND target_id=? AND json_extract(data_json,'$.magic_item')=?""", (owner, CRYSTAL)).fetchone()


def _text(value, limit, name, required=True):
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError(f'{name} inválido')
    return value.strip()


def _log(db, access, owner, request, title, detail, now, event='action'):
    actor = 'master' if access.mode == 'gm' else access.profile_id
    append_session_ledger_event(db, source_type='magic_field_item', source_id=request + ':' + owner,
        event_kind=event, actor_id=actor, actor_name='Mestre' if access.mode == 'gm' else actor,
        actor_role=access.mode, character_id=owner, title=title, detail=detail,
        visibility='owner', created_at=now)


def cup_distance(db, owner, partner):
    from .portable_hole import assert_actor_exterior
    for actor in (owner, partner):
        assert_actor_exterior(db, actor)
    active = db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
    grid = grid_record(db, active[0]) if active else None
    if not grid:
        raise ValueError('Os dois copos precisam estar no mapa ativo com grid')
    points = []
    for actor in (owner, partner):
        rows = db.execute('''SELECT p.cell_x,p.cell_y FROM session_workspace_entity_positions p
            JOIN session_workspace_tokens t ON t.id=p.token_id AND t.map_id=p.map_id
            WHERE p.map_id=? AND t.character_id=?''', (grid['map_id'], actor)).fetchall()
        if len(rows) != 1:
            raise ValueError('Cada portador precisa de um único pin no mapa ativo')
        points.append(rows[0])
    return distance_cells(grid['distance_rule'], *points) * grid['cell_size_m']


def _cups(db, row, data, action, fields, now, access, request):
    pair, partner = _cup_pair(db, row, data)
    if action == 'bind':
        identifier = fields.get('inventory_id')
        if type(identifier) is not int or row['quantity'] != 1:
            raise ValueError('Escolha dois copos individuais')
        candidate = db.execute('SELECT * FROM player_inventory WHERE id=? AND quantity=1', (identifier,)).fetchone()
        if not candidate or candidate['profile_id'] == row['profile_id'] or identity(dict(candidate)) != CUP:
            raise ValueError('O par deve pertencer a outro portador')
        old_pair, _ = _cup_pair(db, candidate, _state(db, candidate).get('field_item', {}))
        if (pair and pair['id'] != identifier) or (old_pair and old_pair['id'] != row['id']):
            raise ValueError('Um dos copos já está vinculado a outro par')
        _save(db, row, {'pair': identifier, 'listening': False}, now)
        _save(db, candidate, {'pair': row['id'], 'listening': False}, now)
        return {'message': 'Copos vinculados'}
    if not pair:
        raise ValueError('O Mestre precisa vincular o outro copo')
    if action in {'listen', 'stop'}:
        _save(db, row, {**data, 'listening': action == 'listen'}, now)
        return {'message': 'Copo em uso' if action == 'listen' else 'Copo desativado'}
    if not data.get('listening') or not partner.get('listening'):
        raise ValueError('Os dois copos precisam estar em uso')
    if cup_distance(db, row['profile_id'], pair['profile_id']) > 15:
        raise ValueError('O outro copo está fora dos 15 m')
    message = _text(fields.get('text'), 500, 'Mensagem')
    for owner in (row['profile_id'], pair['profile_id']):
        _log(db, access, owner, request, 'Mensagem pelos Copos',
             {'text': message, 'sender': row['profile_id']}, now, 'message')
    return {'message': 'Mensagem entregue'}


def _book(db, row, data, action, fields, now):
    if action == 'set_languages':
        values = fields.get('languages')
        if not isinstance(values, list) or not 2 <= len(values) <= 50:
            raise ValueError('Cadastre de 2 a 50 idiomas da campanha')
        distinct = {}
        for value in values:
            label = _text(value, 70, 'Idioma')
            distinct.setdefault(label.casefold(), label)
        languages = list(distinct.values())
        if len(languages) < 2:
            raise ValueError('Cadastre pelo menos dois idiomas distintos')
        _save(db, row, {'languages': languages}, now)
        return {'message': 'Idiomas cadastrados'}
    owner = row['profile_id']
    record = db.execute('SELECT data_json FROM character_sheets WHERE profile_id=?', (owner,)).fetchone()
    if not record:
        raise ValueError('A ficha não tem idiomas cadastrados')
    sheet = json.loads(record[0])
    languages = sheet.get('languages') or {}
    spoken = (languages.get('spoken_languages') or '').splitlines()
    written = (languages.get('written_languages') or '').splitlines()
    choices = [x for x in data.get('languages', []) if x.casefold() not in
               {old.strip().casefold() for old in spoken + written}]
    if not choices:
        raise ValueError('O livro não tem um idioma novo configurado')
    new = choices[roll_formula(f'1d{len(choices)}')['total'] - 1] if len(choices) > 1 else choices[0]
    languages['spoken_languages'] = new
    languages['written_languages'] = ''
    sheet['languages'] = languages
    db.execute('UPDATE character_sheets SET data_json=?,updated_at=? WHERE profile_id=?',
               (json.dumps(sheet, ensure_ascii=False), now, owner))
    return {'message': f'Agora o leitor conhece apenas {new}', 'language': new}


def _nail_effect(db, owner):
    return db.execute("""SELECT id FROM combat_effects WHERE active=1 AND target_type='character'
        AND target_id=? AND json_extract(data_json,'$.ungual_nails')=1""", (owner,)).fetchone()


def _vessel(db, owner, action, now):
    from .battle_mode import require_actor_alive, require_consumable_turn, commit_consumable_turn
    from .combat_effects import effect_snapshot
    from .night_form import require_humanoid
    if action == 'draw_water':
        return {'message': 'O vaso enche com 1 litro de água', 'liters': 1}
    require_actor_alive(db, owner)
    require_humanoid(db, owner)
    effect = _nail_effect(db, owner)
    if action == 'clip':
        if not effect:
            raise ValueError('Não há unhas crescidas para aparar')
        db.execute('UPDATE combat_effects SET active=0 WHERE id=?', (effect[0],))
    else:
        if effect:
            raise ValueError('As unhas já cresceram')
        snapshot = effect_snapshot(db)
        require_consumable_turn(db, snapshot, owner)
        identifier = 'ungual:' + uuid.uuid4().hex
        data = {'id': identifier, 'target_type': 'character', 'target_id': owner,
                'label': 'Unhas crescidas', 'source': 'Vaso da Água Ungueal',
                'duration': 'manual', 'rounds': None, 'modifiers': {}, 'magic_item': VESSEL,
                'ungual_nails': True, 'updated_at': now}
        db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)', (identifier, 'character', owner, json.dumps(data)))
        commit_consumable_turn(db, snapshot)
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return {'message': 'Unhas aparadas' if action == 'clip' else 'Unhas crescidas · ataque de 1d4'}


def project_nails(definition, effects):
    if not any(effect.get('ungual_nails') for effect in effects):
        return definition
    melee = next((entry for entry in definition.get('attacks', []) if entry.get('id') == 'melee'), {})
    bonus = (melee.get('base_attack_bonus') or 0) + (melee.get('effect_attack_bonus') or 0)
    attack = {'id': NAILS, 'name': 'Unhas ungueais', 'damage': '1d4', 'weapon_item_path': 'natural:' + NAILS,
              'range': 'Adjacente', 'attack_count': 1, 'attack_bonus': bonus, 'base_attack_bonus': bonus,
              'native_range': {'slot': 'melee', 'max_range_m': None}, 'slot': 'melee'}
    return {**definition, 'attacks': [*definition.get('attacks', []), attack]}


def confirm_nails(db, record, now):
    owner = record['actor_character_id']
    if not _nail_effect(db, owner):
        raise ValueError('As unhas já foram aparadas; resolva outro ataque')
    roll = roll_formula('1d4')
    if roll['total'] != 1:
        return {'roll': roll, 'broke': False}
    from .combat_effects import change_hp
    hp = change_hp(db, 'character', owner, -1, now, damage_type='physical',
                   damage_context={'kind': 'effect', 'damage_type': 'physical'})
    return {'roll': roll, 'broke': True, 'self_damage': 1, 'hp': hp}


def _require_mage(db, owner):
    row = db.execute('SELECT data_json FROM character_sheets WHERE profile_id=?', (owner,)).fetchone()
    data = json.loads(row[0]) if row else {}
    override = db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?', (owner,)).fetchone()
    class_name = (json.loads(override[0]).get('class_name') if override else None) or (data.get('character_class') or {}).get('class_name') or ''
    name = unicodedata.normalize('NFKD', class_name).encode('ascii', 'ignore').decode().casefold()
    if 'mago' not in name and 'necromante' not in name:
        raise ValueError('A Bola de Cristal exige um mago')


def _apply(db, row, key, operation, fields, access, request, now):
    data = _state(db, row).get('field_item', {})
    owner = row['profile_id']
    if key == CUP:
        return _cups(db, row, data, operation, fields, now, access, request)
    if key == VESSEL:
        result = _vessel(db, owner, operation, now)
        _log(db, access, owner, request, result['message'], {}, now)
        return result
    if key == BOOK:
        result = _book(db, row, data, operation, fields, now)
        if operation == 'read_languages':
            _log(db, access, owner, request, 'Leu o Livro das Línguas', result, now)
        return result
    if row['quantity'] != 1:
        raise ValueError('A interação exige um item individual')
    if operation == 'set_vision':
        chaotic = CRYSTAL_VARIANTS.get(identity(dict(row)), fields.get('chaotic') is True)
        _save(db, row, {'subject': _text(fields.get('subject'), 120, 'Alvo'),
            'text': _text(fields.get('text'), 3000, 'Visão'),
            'false_text': _text(fields.get('false_text', ''), 3000, 'Visão falsa', chaotic),
            'chaotic': chaotic}, now)
        return {'message': 'Visão cadastrada'}
    if operation == 'set_document':
        pages = fields.get('pages')
        if type(pages) is not int or not 1 <= pages <= 10000:
            raise ValueError('Número de páginas inválido')
        _save(db, row, {'title': _text(fields.get('title'), 120, 'Título'),
            'text': _text(fields.get('text'), 5000, 'Documento'), 'pages': pages}, now)
        return {'message': 'Documento cadastrado'}
    if operation == 'observe':
        _require_mage(db, owner)
        if not data.get('text'):
            raise ValueError('O Mestre precisa cadastrar uma visão')
        if _observation(db, owner):
            raise ValueError('Já há uma observação ativa neste turno de exploração')
        remaining = _remaining(row) - 1
        if remaining < 0:
            raise ValueError('Sem usos até o descanso')
        false = data['chaotic'] and roll_formula('1d100')['total'] <= 30
        result = {'message': data['false_text'] if false else data['text'], 'remaining': remaining,
                  'duration_exploration_turns': 1}
        db.execute("UPDATE player_inventory SET charges_current=?,charges_max=3,recharge='inn_rest',updated_at=? WHERE id=?",
                   (remaining, now, row['id']))
        identifier = 'crystal:' + uuid.uuid4().hex
        effect = {'id': identifier, 'target_type': 'character', 'target_id': owner,
                  'label': 'Observação arcana', 'source': 'Bola de Cristal',
                  'duration': 'fictional_time', 'remaining_seconds': 600, 'source_duration_unit': 'turns',
                  'rounds': None, 'modifiers': {}, 'magic_item': CRYSTAL, 'updated_at': now}
        db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)', (identifier, 'character', owner, json.dumps(effect)))
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        _log(db, access, owner, request, 'Observou pela Bola de Cristal', {'text': result['message']}, now)
        return result
    if not data.get('pages'):
        raise ValueError('O Mestre precisa cadastrar um documento')
    if data['pages'] > 100:
        raise ValueError('Os Óculos leem até 100 páginas')
    _log(db, access, owner, request, 'Leu com os Óculos da Rápida Leitura', {'text': data['text']}, now)
    return {'message': data['text'], 'pages': data['pages'], 'learned_spell': False}


def execute(path, access, owner, item_path, operation, fields, request):
    if access.mode != 'gm' and access.profile_id != owner:
        raise PermissionError('Item indisponível')
    if operation in GM_OPERATIONS and access.mode != 'gm':
        raise PermissionError('Somente o Mestre configura o item')
    fingerprint = hashlib.sha256(json.dumps(['field_item', access.mode, access.profile_id, owner, item_path,
        operation, fields], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect(path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        previous = db.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?', (request,)).fetchone()
        if previous:
            if previous[0] != fingerprint:
                raise ValueError('Identificador de comando já usado')
            return json.loads(previous[1])
        row, key = _item(db, access, owner, item_path)
        if operation not in OPERATIONS[key]:
            raise ValueError('Interação indisponível para este item')
        result = _apply(db, row, key, operation, fields, access, request, now)
        db.execute('INSERT INTO combat_effect_commands VALUES(?,?,?)', (request, fingerprint, json.dumps(result, ensure_ascii=False)))
        return result


def record_tracks(db, token, map_id, cells, request, now):
    """Evidence is captured at movement time, never reconstructed from current equipment."""
    from .magic_passives import equipped
    owner = token['character_id']
    if owner and equipped(db, owner, BOOTS):
        return
    append_session_ledger_event(db, source_type='physical_tracks', source_id=request,
        event_kind='state', actor_id='system', actor_name='Rastros', actor_role='system',
        character_id=owner, title='Rastros no mapa', visibility='gm', created_at=now,
        detail={'map_id': map_id, 'token_id': token['id'], 'cells': cells})


def tracks(path, access, map_id):
    if access.mode != 'gm':
        raise PermissionError('Somente o Mestre consulta os rastros')
    with closing(connect(path)) as db:
        rows = db.execute("""SELECT detail_json,created_at FROM session_ledger
            WHERE source_type='physical_tracks' AND voided_at IS NULL
            AND json_extract(detail_json,'$.map_id')=? ORDER BY id DESC LIMIT 100""", (map_id,))
        return {'tracks': [{**json.loads(row[0]), 'created_at': row[1]} for row in rows]}
