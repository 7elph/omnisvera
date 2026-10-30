"""Real HTTP combat rehearsal. Fixed loopback fixture tokens; temporary DB only."""
import argparse
import json
import sqlite3
import tempfile
import uuid
from contextlib import closing
from pathlib import Path
import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    database = parser.parse_args().database.resolve()
    if Path(tempfile.gettempdir()).resolve() not in database.parents or not database.is_file():
        raise ValueError('Only an existing temporary rehearsal database is allowed')
    prefix = 'integrity-http-' + uuid.uuid4().hex
    clients = {role: httpx.Client(base_url='http://127.0.0.1:8871', headers={'X-Omnisvera-Token':'cf01-local-' + role}, timeout=30, trust_env=False)
        for role in ('gm', 'vezemir', 'raziel', 'morthak')}
    gm = clients['gm']
    def read(route, role='gm'):
        response = clients[role].get(route); response.raise_for_status(); return response.json()
    def post(route, payload, role='gm', status=200):
        response = clients[role].post(route, json=payload)
        assert response.status_code == status, (route, response.status_code, response.text)
        return response.json()
    def command(action, role='gm', **payload):
        return post('/combat/next-turn' if action=='next_turn' else '/gm/combat/effects',
            {'request_id': prefix + uuid.uuid4().hex, 'expected_version':read('/combat/effects')['version'], 'action':action, 'payload':payload}, role)
    def confirm(record, role):
        route = '/combat/attacks/' + record['resolution_id'] + '/confirm'
        first = post(route, {}, role); replay = post(route, {}, role)
        assert first == replay
        return first
    def attack(actor, request_id, role, target, attack_id='melee'):
        return post('/characters/' + actor + '/attacks/resolve', {'request_id':request_id, 'attack_id':attack_id,
            'target_type':'token','target_id':target,'roll_mode':'physical','d20':15}, role)
    try:
        assert read('/health')['access_mode'] == 'gm'
        if read('/combat/effects').get('encounter', {}).get('active'): command('end')
        workspace = read('/workspace'); map_id = workspace['map']['id']
        response = gm.patch('/gm/workspace/table-mode', json={'table_mode':'physical'})
        response.raise_for_status()
        # Only this verified disposable copy is modified to make all scenarios available.
        with closing(sqlite3.connect(database)) as db, db:
            db.execute("UPDATE session_workspace_tokens SET current_hp=0 WHERE json_extract(sheet_json,'$.summon.caster')='morthak' AND json_extract(sheet_json,'$.summon.technique')='levantar-esqueleto'")
            for actor in ('vezemir','raziel','morthak','dorn7'):
                row = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (actor,)).fetchone()
                state = json.loads(row[0]); state['current_hp'] = max(1, int(state['maximum_hp']) - 5)
                for resource in state.get('resources', []): resource['current'] = resource['maximum']
                db.execute('UPDATE character_states SET state_json=?,version=version+1 WHERE profile_id=?', (json.dumps(state), actor))
            db.execute("UPDATE player_inventory SET quantity=3 WHERE profile_id='vezemir' AND item_path='session-item:11'")
        enemy = post('/gm/workspace/tokens', {'token_type':'monster','map_id':map_id,'name':prefix,'latitude':50,'longitude':75,
            'visible_to_players':True,'current_hp':200,'maximum_hp':200,'sheet':{'armor_class':10,'saving_throw':20,'has_blood':True,'attacks':[{'name':'Teste','bonus':1,'damage':'1d4'}]}})
        command('start', title=prefix, map_id=map_id, battle_mode=True, participants=[
            *[{'target_type':'character','target_id':actor,'name':actor,'initiative':20-index} for index, actor in enumerate(('vezemir','raziel','morthak','dorn7'))],
            {'target_type':'token','target_id':enemy['id'],'name':'Alvo de teste','initiative':1}])
        for technique in ('forca-arcana', 'velocidade'):
            payload = {'request_id': prefix + technique}
            activated = post('/characters/vezemir/techniques/' + technique, payload, 'vezemir')
            assert activated == post('/characters/vezemir/techniques/' + technique, payload, 'vezemir')
            assert activated['duration_rounds'] > 0
        use = {'action':'use_item','payload':{'item_path':'session-item:11'},'request_id':prefix+'potion'}
        first = post('/characters/vezemir/actions', use, 'vezemir')
        replay = post('/characters/vezemir/actions', use, 'vezemir')
        quantities = lambda character: next(i['quantity'] for i in character['inventory'] if i['item_path']=='session-item:11')
        assert quantities(first) == quantities(replay) == 2
        post('/characters/vezemir/actions', {**use,'request_id':prefix+'potion-extra'}, 'vezemir', status=400)
        preview = attack('vezemir', prefix+'attack', 'vezemir', enemy['id'])
        other = attack('vezemir', prefix+'reroll', 'vezemir', enemy['id'])
        assert preview['resolution_id'] == other['resolution_id'] and preview['d20'] == other['d20']
        assert read('/combat/attacks/pending', 'vezemir')[0]['resolution_id'] == preview['resolution_id']
        confirm(preview, 'vezemir'); command('next_turn', 'vezemir')
        bite = post('/characters/raziel/techniques/mordida', {'request_id':prefix+'bite','target_type':'token','target_id':enemy['id'],'roll_mode':'physical','d20':15}, 'raziel')
        bitten = confirm(bite, 'raziel')
        assert bitten['breakdown']['drain_result']['healed'] > 0
        command('next_turn', 'raziel')
        summon_payload = {'request_id':prefix+'summon','map_id':map_id}
        summon = post('/characters/morthak/techniques/levantar-esqueleto', summon_payload, 'morthak')
        assert summon == post('/characters/morthak/techniques/levantar-esqueleto', summon_payload, 'morthak')
        post('/characters/morthak/techniques/levantar-esqueleto', {**summon_payload,'request_id':prefix+'summon-extra'}, 'morthak', status=400)
        command('next_turn', 'morthak')
        controlled = post('/gm/combat/tokens/' + summon['token']['id'] + '/attacks/resolve', {'request_id':prefix+'skeleton-attack',
            'attack_id':'0','target_type':'token','target_id':enemy['id'],'roll_mode':'physical','d20':15}, 'morthak')
        confirm(controlled, 'morthak'); command('next_turn', 'morthak')
        gm.patch('/gm/workspace/table-mode', json={'table_mode':'digital'}).raise_for_status()
        magic = post('/characters/dorn7/attacks/resolve', {'request_id':prefix+'dorn-missiles','attack_id':'misseis-magicos',
            'target_type':'token','target_id':enemy['id'],'roll_mode':'digital'}, 'gm')
        confirm(magic, 'gm')
        assert read('/combat/effects')['encounter']['action_committed']
        command('end')
        for actor in ('vezemir','raziel','morthak'):
            assert read('/characters/' + actor, actor)['access_level'] == 'owner'
        # Reconnect with a new HTTP client; neither damage nor the summon disappears.
        with httpx.Client(base_url='http://127.0.0.1:8871', headers={'X-Omnisvera-Token':'cf01-local-gm'}, trust_env=False) as reconnected:
            assert reconnected.get('/characters/dorn7').json()['state']['resources'][0]['current'] == 2
        with closing(sqlite3.connect(database)) as db:
            assert db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?', (enemy['id'],)).fetchone()[0] < 200
            assert db.execute('SELECT count(*) FROM session_workspace_tokens WHERE id=?', (summon['token']['id'],)).fetchone()[0] == 1
        print('PASS: native HTTP; strength and velocity recover original duration; potion once plus attack; preview cannot reroll; confirmation replay; bite heals; one skeleton; controlled summon attack; Dorn missiles; owner access; persistence after reconnect.')
    finally:
        combat = read('/combat/effects')
        if combat.get('encounter', {}).get('active') and combat['encounter'].get('title') == prefix: command('end')
        for client in clients.values(): client.close()


if __name__ == '__main__': main()
