"""Approved Raziel rules; no passive regeneration or automatic blood recovery."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from .battle_mode import require_battle_turn, commit_battle_action
from .combat_effects import init_effects, effect_snapshot, change_hp
from .dice_rolls import roll_formula
from .session_ledger import append_session_ledger_event


def bite_definition(definition):
    melee = next((a for a in definition.get('attacks', []) if a['id'] == 'melee'), None)
    if not melee or melee.get('attack_bonus') is None:
        raise ValueError('Bônus corpo a corpo não configurado para Raziel')
    # The 1d4 contract is approved now; future racial scaling is not enabled.
    attack = {'id': 'mordida', 'name': 'Mordida', 'attack_bonus': int(melee['attack_bonus']) - int(melee.get('item_attack_bonus') or 0),
        'damage': '1d4', 'weapon_item_path': 'technique:mordida', 'life_drain': True}
    return {**definition, 'attacks': [attack]}


def regenerate(path, *, actor_id, actor_role, request_id, rng=None):
    init_effects(path)
    now = datetime.now(timezone.utc).isoformat()
    fingerprint = json.dumps(['regeneracao-vampirica', 'raziel', actor_id, actor_role])
    with closing(sqlite3.connect(path, timeout=30)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN IMMEDIATE')
        old = db.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?', (request_id,)).fetchone()
        if old:
            if old['fingerprint'] != fingerprint:
                raise ValueError('Requisição já utilizada para outra ação')
            return json.loads(old['response_json'])
        snapshot = effect_snapshot(db)
        require_battle_turn(db, snapshot, 'raziel')
        if int((snapshot.get('encounter') or {}).get('attacks_used') or 0):
            raise ValueError('Regeneração exige uma ação completa disponível')
        row = db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()
        if not row:
            raise ValueError('Ficha de Raziel indisponível')
        state = json.loads(row['state_json'])
        if int(state.get('current_hp') or 0) <= 0:
            raise ValueError('Regeneração não pode levantar Raziel de 0 PV')
        if state['current_hp'] >= state['maximum_hp']:
            raise ValueError('Raziel já está com os PV máximos')
        resource = next((r for r in state.get('resources', []) if r['key'] == 'reserva_de_sangue'), None)
        if not resource or resource.get('current', 0) < 1:
            raise ValueError('Reserva de Sangue insuficiente')
        roll = int(roll_formula('1d4', rng)['total'])
        resource['current'] -= 1
        db.execute("UPDATE character_states SET state_json=? WHERE profile_id='raziel'", (json.dumps(state),))
        hp = change_hp(db, 'character', 'raziel', roll, now)
        commit_battle_action(db, snapshot)
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        result = {'heal_roll': roll, 'healed': hp['hp_after'] - hp['hp_before'],
            'hp_before': hp['hp_before'], 'hp_after': hp['hp_after'], 'blood_remaining': resource['current']}
        append_session_ledger_event(db, source_type='vampire_power', source_id=request_id, event_kind='action',
            actor_id=actor_id, actor_name='Raziel', actor_role=actor_role, character_id='raziel',
            title=f"Raziel regenerou {result['healed']} PV usando 1 sangue", detail=result, created_at=now)
        db.execute('INSERT INTO combat_effect_commands(request_id,fingerprint,response_json) VALUES(?,?,?)',
            (request_id, fingerprint, json.dumps(result)))
        return result
