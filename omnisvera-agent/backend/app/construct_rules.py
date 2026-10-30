"""Approved Constructo rules. Semantic categories never imply immunity to all magic."""
import json

IMMUNE = {'physical_transformation': 'Forma Imutável', 'natural_disease': 'Corpo Artificial', 'common_poison': 'Corpo Artificial'}

def is_construct(db, character_id):
    row = db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?', (character_id,)).fetchone()
    return bool(row and json.loads(row[0]).get('construct_traits'))

def validate_effect(db, character_id, category):
    if is_construct(db, character_id) and category in IMMUNE:
        raise ValueError(f'{IMMUNE[category]}: DORN-7 é imune a este efeito')

def validate_healing(db, character_id, category):
    if is_construct(db, character_id) and category == 'conventional_magical_healing':
        raise ValueError('Corpo Artificial: DORN-7 não responde a cura mágica convencional')

def repair(path, *, actor_id, actor_role, request_id, rng=None):
    from contextlib import closing
    import sqlite3
    from .combat_effects import init_effects, change_hp
    from .character_play import _now
    from .dice_rolls import roll_formula, init_dice_rolls
    from .session_ledger import append_session_ledger_event, init_session_ledger
    if actor_role != 'gm':
        raise PermissionError('Somente o Mestre controla Dorn')
    if not request_id or len(request_id) > 120:
        raise ValueError('Informe uma chave idempotente para Reparo')
    init_effects(path)
    init_dice_rolls(path)
    init_session_ledger(path)
    fingerprint = json.dumps(['dorn-reparo', actor_id, actor_role])
    with closing(sqlite3.connect(path, timeout=30)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        old = db.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?', (request_id,)).fetchone()
        if old:
            if old[0] != fingerprint:
                raise ValueError('Requisição pertence a outra ação')
            return json.loads(old[1])
        if not is_construct(db, 'dorn7'):
            raise ValueError('Ficha aprovada de Constructo ainda não aplicada')
        from .battle_mode import require_consumable_turn, commit_consumable_turn
        from .combat_effects import effect_snapshot
        snapshot = effect_snapshot(db)
        require_consumable_turn(db, snapshot, 'dorn7')
        kit = db.execute("SELECT item_path,quantity FROM player_inventory WHERE profile_id='dorn7' AND item_title='Kit de Reparo' AND quantity>0 ORDER BY item_path LIMIT 1").fetchone()
        if not kit:
            raise ValueError('Reparo exige possuir Kit de Reparo')
        rolled = int(roll_formula('1d4', rng)['total'])
        now = _now()
        db.execute("UPDATE player_inventory SET quantity=quantity-1,updated_at=? WHERE profile_id='dorn7' AND item_path=?",(now,kit[0]))
        result = {'heal_roll': rolled, 'kits_remaining':kit[1]-1, **change_hp(db, 'character', 'dorn7', rolled, now)}
        commit_consumable_turn(db, snapshot)
        append_session_ledger_event(db, source_type='construct_repair', source_id=request_id, event_kind='action',
            actor_id=actor_id, actor_name='DORN-7', actor_role=actor_role, character_id='dorn7',
            title=f"DORN-7 reparado: {result['hp_after'] - result['hp_before']} PV", detail=result, created_at=now)
        db.execute('INSERT INTO combat_effect_commands VALUES(?,?,?)', (request_id, fingerprint, json.dumps(result)))
        return result
