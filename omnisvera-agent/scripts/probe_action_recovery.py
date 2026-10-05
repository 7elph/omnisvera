"""Audit copied party values and rehearse missiles/recovery on a temporary DB only."""
import gc
import json
import os
from pathlib import Path
import sqlite3
import sys
from contextlib import closing
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def main():
    with TemporaryDirectory(prefix='companion-action-probe-') as temporary:
        database = Path(temporary) / 'test.sqlite3'
        with sqlite3.connect((ROOT / 'backend/data/omnisvera_companion.sqlite3').as_uri() + '?mode=ro', uri=True) as source:
            with sqlite3.connect(database) as destination:
                source.backup(destination)
        source.close(); destination.close()
        config = json.loads((ROOT / 'backend/data/access_tokens.json').read_text(encoding='utf-8-sig'))
        profiles = {key: {**value, 'token': 'test-' + key} for key, value in config['player_profiles'].items() if not value.get('gm_controlled')}
        os.environ.update(OMNISVERA_DB_PATH=str(database), OMNISVERA_VAULT_PATH=str(ROOT.parent),
            OMNISVERA_MASTER_TOKEN='probe-master', OMNISVERA_ACCESS_TOKEN='probe-master',
            OMNISVERA_PLAYER_PROFILES_JSON=json.dumps(profiles), OMNISVERA_REBUILD_ON_STARTUP='false', OMNISVERA_TRAINING_CAPTURE_MODE='off')
        sys.path.insert(0, str(ROOT / 'backend'))
        from app.main import app, settings
        from fastapi.testclient import TestClient
        from app.session_workspace import save_workspace_token, update_workspace_table_mode
        assert settings.database_path.resolve() == database.resolve()
        master = {'X-Omnisvera-Token': 'probe-master'}
        player = {'X-Omnisvera-Token': 'test-morthak'}
        with TestClient(app, raise_server_exceptions=True) as client:
            for profile in ('vezemir', 'raziel', 'morthak'):
                response = client.get(f'/characters/{profile}', headers=master)
                assert response.status_code == 200, response.text
                view = response.json(); definition = view['definition']
                print(json.dumps({'character': profile, 'level': definition['level'], 'hp': [view['state'].get('current_hp'),view['state'].get('maximum_hp')],
                    'attributes': definition.get('attributes'), 'attacks': definition['attacks'],
                    'resources': view['state'].get('resources')}, ensure_ascii=False))
            # Test-only target and resource reset, never live campaign writes.
            update_workspace_table_mode(database, 'digital')
            token = save_workspace_token(database, token_type='monster', name='Alvo descartável', latitude=50, longitude=50,
                current_hp=100, maximum_hp=100, visible_to_players=True, sheet={'armor_class':99})
            with closing(sqlite3.connect(database)) as db, db:
                state = json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
                resource = next(r for r in state['resources'] if r['key']=='misseis_magicos')
                resource['current']=3
                db.execute("UPDATE character_states SET state_json=?,version=version+1 WHERE profile_id='morthak'", (json.dumps(state),))
            body={'request_id':'missiles-copy-probe-001','attack_id':'misseis-magicos','target_type':'token','target_id':token['id'],'roll_mode':'digital'}
            response=client.post('/characters/morthak/attacks/resolve',json=body,headers=player)
            assert response.status_code==200, response.text
            result=response.json()
            assert result['breakdown']['automatic_hit'] and result['d20']==0 and result['damage_formula']=='1d4+2', result
            pending=client.get('/combat/attacks/pending',headers=player).json()
            assert any(r['resolution_id']==result['resolution_id'] for r in pending), pending
            assert client.get('/combat/attacks/pending',headers={'X-Omnisvera-Token':'test-raziel'}).json()==[]
            with TestClient(app) as reconnected:
                for _ in range(2):
                    confirmed=reconnected.post('/combat/attacks/'+result['resolution_id']+'/confirm',headers=player)
                    assert confirmed.status_code==200, confirmed.text
            with closing(sqlite3.connect(database)) as db:
                after=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
                assert next(r['current'] for r in after['resources'] if r['key']=='misseis_magicos')==2
                hp=db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(token['id'],)).fetchone()[0]
                assert hp==100-result['damage_total']
            print('MAGIC_MISSILES / RECOVERY / RECONNECT / EXACTLY_ONCE / OWNER_PRIVACY = PASS')
        gc.collect()
        print('TEMPORARY_DATABASE_ONLY = PASS')


if __name__=='__main__':
    main()
