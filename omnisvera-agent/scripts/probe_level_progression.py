"""Rehearse advancement on a temporary SQLite backup, never the campaign DB."""
import json
import gc
import os
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def main():
    with TemporaryDirectory(prefix='companion-level-probe-') as temporary:
        database = Path(temporary) / 'test.sqlite3'
        source = sqlite3.connect((ROOT / 'backend/data/omnisvera_companion.sqlite3').as_uri() + '?mode=ro', uri=True)
        destination = sqlite3.connect(database)
        source.backup(destination)
        source.close()
        destination.close()
        tokens = json.loads((ROOT / 'backend/data/access_tokens.json').read_text(encoding='utf-8-sig'))
        profiles = {key: {**value, 'token': 'test-' + key} for key, value in tokens['player_profiles'].items() if not value.get('gm_controlled')}
        os.environ.update(OMNISVERA_DB_PATH=str(database), OMNISVERA_VAULT_PATH=str(ROOT.parent),
                          OMNISVERA_MASTER_TOKEN='probe-master', OMNISVERA_ACCESS_TOKEN='probe-master',
                          OMNISVERA_PLAYER_PROFILES_JSON=json.dumps(profiles),
                          OMNISVERA_REBUILD_ON_STARTUP='false', OMNISVERA_TRAINING_CAPTURE_MODE='off')
        sys.path.insert(0, str(ROOT / 'backend'))
        from app.main import app, settings
        from fastapi.testclient import TestClient
        assert settings.database_path.resolve() == database.resolve()
        client = TestClient(app)
        headers = {'X-Omnisvera-Token': 'probe-master'}
        for name, target, roll in [('morthak', 2, 3), ('vezemir', 3, 2)]:
            url = f'/gm/characters/{name}/level'
            request = {'target_level': target, 'hp_roll': roll}
            response = client.post(url + '/preview', json=request, headers=headers)
            assert response.status_code == 200, (name, response.status_code, response.text)
            plan = response.json()
            assert plan['status'] == 'ready', plan
            request['fingerprint'] = plan['fingerprint']
            denied = client.post(url + '/confirm', json=request, headers={'X-Omnisvera-Token': 'test-' + name})
            assert denied.status_code in (401, 403)
            response = client.post(url + '/confirm', json=request, headers=headers)
            assert response.status_code == 200, response.text
            assert response.json()['applied'] is True
            replay = client.post(url + '/confirm', json=request, headers=headers)
            assert replay.status_code == 200 and replay.json()['applied'] is False, replay.text
            print(name, 'PREVIEW/CONFIRM/RETRY/PLAYER_DENIED=PASS',
                  [(c['field'], c['before'], c['after']) for c in plan['changes']])
        client.close()
        gc.collect()  # Close cyclic SQLite handles before Windows removes the fixture.
        print('TEMPORARY_DATABASE_ONLY=PASS')


if __name__ == '__main__':
    main()
