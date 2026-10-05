"""Session 6 real-HTTP arena rehearsal, exclusively against cf01 temporary fixture.

Usage: python session6_rehearsal.py <OS-temp database> <port>
Seeds only one summon resource in the disposable DB. Never use operational tokens.
"""
from contextlib import closing
import json
import sqlite3
import sys
import uuid
import httpx
from cf01_probe import TOKENS, checked_database


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    database = checked_database(sys.argv[1])
    if not database.is_file():
        raise SystemExit('Prepare a disposable fixture first')
    prefix = 's6-' + uuid.uuid4().hex
    clients = {role: httpx.Client(base_url=f'http://127.0.0.1:{int(sys.argv[2])}',
        headers={'X-Omnisvera-Token': TOKENS[role]}, trust_env=False, timeout=30)
        for role in ('gm', 'morthak', 'vezemir', 'raziel')}
    gm, mage, fighter = (clients[r] for r in ('gm', 'morthak', 'vezemir'))
    def require(response):
        response.raise_for_status()
        return response.json()
    def state(): return require(gm.get('/combat/effects'))
    def command(action, payload=None):
        return require(gm.post('/gm/combat/effects', json={'request_id': prefix + uuid.uuid4().hex,
            'expected_version': state()['version'], 'action': action, 'payload': payload or {}}))
    def turn(client):
        body = {'request_id': prefix + uuid.uuid4().hex, 'expected_version': state()['version'], 'action': 'next_turn'}
        reply = require(client.post('/combat/next-turn', json=body))
        assert require(client.post('/combat/next-turn', json=body)) == reply
    def attack(client, endpoint, attack_id, target_id):
        body = {'request_id': prefix + uuid.uuid4().hex, 'attack_id': attack_id,
            'target_type': 'token', 'target_id': target_id, 'roll_mode': 'physical', 'd20': 20}
        result = require(client.post(endpoint, json=body))
        confirm = '/combat/attacks/' + result['resolution_id'] + '/confirm'
        done = require(client.post(confirm))
        assert require(client.post(confirm)) == done
        return done
    try:
        # Authenticate with fixture-only credential before making any mutation.
        assert require(gm.get('/health'))['access_mode'] == 'gm'
        if state().get('encounter', {}).get('active'): command('end')
        original = require(gm.get('/workspace'))['map']['id']
        maps = require(gm.get('/workspace/maps'))
        arena = next(m['id'] for m in maps if m['visible_to_players'] and m['id'] != original)
        with closing(sqlite3.connect(database)) as db, db:
            row = db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()
            value = json.loads(row[0])
            next(r for r in value['resources'] if r['key'] == 'levantar_um_esqueleto')['current'] = 1
            db.execute("UPDATE character_states SET state_json=?,version=version+1 WHERE profile_id='morthak'", (json.dumps(value),))
        require(gm.patch('/gm/workspace/table-mode', json={'table_mode': 'physical'}))
        require(gm.patch('/gm/characters/vezemir/definition', json={'fields': {'attack_count': 2}, 'reason': 'Fixture descartável de multiataque'}))
        enemies = [require(gm.post('/gm/workspace/tokens', json={'token_type': 'monster', 'name': f'Alvo Sessão6 {i}',
            'map_id': original, 'visible_to_players': True, 'latitude': 40, 'longitude': 50+i*10,
            'current_hp': 100, 'maximum_hp': 100, 'sheet': {'armor_class': 1, 'attacks': [{'name': 'Golpe', 'bonus': 20, 'damage': '1d4'}]}})) for i in range(2)]
        command('start', {'title': 'Ensaio descartável Sessão6', 'map_id': arena, 'battle_mode': True, 'participants': [
            {'target_type': 'character', 'target_id': 'morthak', 'initiative': 30},
            {'target_type': 'character', 'target_id': 'vezemir', 'initiative': 20},
            *[{'target_type': 'token', 'target_id': e['id'], 'initiative': 10-i} for i, e in enumerate(enemies)]]})
        attack(mage, '/characters/morthak/attacks/resolve', 'adaga-de-osso', enemies[0]['id'])
        turn(mage)
        for enemy in enemies: attack(fighter, '/characters/vezemir/attacks/resolve', 'melee', enemy['id'])
        denied = fighter.post('/characters/vezemir/attacks/resolve', json={'request_id': prefix + 'third', 'attack_id': 'melee', 'target_type': 'token', 'target_id': enemies[0]['id'], 'roll_mode': 'physical', 'd20': 20})
        assert denied.status_code == 400, denied.text
        turn(fighter); command('next_turn'); command('next_turn')
        body = {'request_id': prefix + 'summon'}
        token = require(mage.post('/characters/morthak/techniques/levantar-um-esqueleto', json=body))['token']
        assert require(mage.post('/characters/morthak/techniques/levantar-um-esqueleto', json=body))['token']['id'] == token['id']
        assert token['map_id'] == arena and token['character_id'] is None and token['current_hp'] == 10
        assert token['id'] in {t['id'] for t in require(mage.get('/workspace'))['tokens']}
        turn(mage)
        endpoint = f"/gm/combat/tokens/{token['id']}/attacks/resolve"
        denied = clients['raziel'].post(endpoint, json={'request_id': prefix + 'forged', 'attack_id': '0', 'target_type': 'token', 'target_id': enemies[0]['id'], 'roll_mode': 'physical', 'd20': 20})
        assert denied.status_code == 403
        attack(mage, endpoint, '0', enemies[0]['id']); turn(mage); turn(fighter)
        caster_hp = require(mage.get('/characters/morthak'))['state']['current_hp']
        damage = attack(gm, f"/gm/combat/tokens/{enemies[0]['id']}/attacks/resolve", '0', token['id'])
        assert damage['hp_before'] == 10 and damage['hp_after'] == 10-damage['damage_total']
        assert require(mage.get('/characters/morthak'))['state']['current_hp'] == caster_hp
        command('end')
        restored = require(mage.get('/workspace'))
        assert restored['map']['id'] == original
        assert next(t for t in restored['tokens'] if t['id'] == token['id'])['current_hp'] == damage['hp_after']
        print(json.dumps({'status': 'PASS', 'bone_dagger': 'PASS', 'split_targets': 'PASS',
            'third_attack_denied': 'PASS', 'owned_summon_turn': 'PASS', 'other_player_denied': 'PASS',
            'summon_hp_independent': 'PASS', 'exactly_once_retry': 'PASS', 'restore_exploration': 'PASS',
            'transport': 'real loopback HTTP', 'live_mobile_table': 'NOT_TESTED'}, indent=2))
    finally:
        for client in clients.values(): client.close()


if __name__ == '__main__': main()
