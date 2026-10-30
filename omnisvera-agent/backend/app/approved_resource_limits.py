"""Explicit GM-approved limit update; never applied by startup or a read."""
import json
import sqlite3
from contextlib import closing

from .character_play import _now, _write_event
from .session6_rewards import synchronize_resource


def apply_approved_resource_limits(database_path):
    changes = []
    with closing(sqlite3.connect(database_path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        now = _now()
        for profile, key, maximum in (
            ('raziel', 'reserva_de_sangue', 10),
            ('dorn7', 'dorn_misseis_magicos', 3),
        ):
            row = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (profile,)).fetchone()
            if not row:
                raise ValueError(f'Ficha ausente: {profile}')
            state = json.loads(row[0])
            resource = next(r for r in state['resources'] if r['key'] == key)
            before = dict(resource)
            synchronize_resource(resource, maximum)
            row = db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?', (profile,)).fetchone()
            overrides = json.loads(row[0]) if row else {}
            overrides['advancement_resources'] = {**(overrides.get('advancement_resources') or {}), key: maximum}
            for ability in overrides.get('approved_session_abilities') or []:
                if (ability.get('uses') or {}).get('resource_key') == key:
                    ability['uses']['maximum'] = maximum
            db.execute('INSERT INTO character_definition_overrides(profile_id,data_json,updated_at) VALUES(?,?,?) ON CONFLICT(profile_id) DO UPDATE SET data_json=excluded.data_json,updated_at=excluded.updated_at', (profile, json.dumps(overrides, ensure_ascii=False), now))
            if before != resource:
                db.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?', (json.dumps(state, ensure_ascii=False), now, profile))
                _write_event(db, character_id=profile, actor_id='master', actor_role='gm', event_type='approved_resource_limit', field=key, before=before, after=resource, reason='Limites aprovados pelo Mestre: reserva 10, mísseis Dorn 3, pulseira 2.', session_id=None)
                changes.append(profile)
        item = db.execute("SELECT item_path,charges_current,charges_max FROM player_inventory WHERE profile_id='vezemir' AND item_title='Pulseira de Vinhas'").fetchone()
        if not item:
            raise ValueError('Pulseira de Vinhas ausente')
        maximum = int(item[2] or 1)
        charges = {'maximum': maximum, 'current': maximum if item[1] is None else int(item[1])}
        before = dict(charges)
        synchronize_resource(charges, 2)
        db.execute("UPDATE player_inventory SET charges_current=?,charges_max=2,recharge='inn_rest',updated_at=? WHERE profile_id='vezemir' AND item_path=?", (charges['current'], now, item[0]))
        if str(item[0]).startswith('session-item:'):
            identity = int(item[0].split(':')[1])
            row = db.execute('SELECT mechanics_json FROM session_custom_items WHERE id=?', (identity,)).fetchone()
            if row:
                mechanics = json.loads(row[0] or '{}')
                mechanics.update(charges_max=2, recharge='inn_rest')
                db.execute('UPDATE session_custom_items SET mechanics_json=?,updated_at=? WHERE id=?', (json.dumps(mechanics, ensure_ascii=False), now, identity))
        if before != charges:
            _write_event(db, character_id='vezemir', actor_id='master', actor_role='gm', event_type='approved_resource_limit', field=item[0], before=before, after=charges, reason='Pulseira de Vinhas: dois usos por descanso.', session_id=None)
            changes.append('vezemir')
    return changes
