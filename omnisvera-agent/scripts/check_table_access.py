"""Read-only access check; never prints credentials or private narrative."""
import json
import time
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
tokens = json.loads((root / 'backend/data/access_tokens.json').read_text(encoding='utf-8-sig'))
with httpx.Client(base_url='https://desktop-p30ui0j.taildecf09.ts.net', timeout=25, trust_env=False) as client:
    print('PUBLIC_PAGE', client.get('/').status_code)
    print('ANONYMOUS_CHARACTERS', client.get('/characters').status_code)
    for name in ('morthak', 'vezemir', 'raziel'):
        headers = {'X-Omnisvera-Token': tokens['player_profiles'][name]['token']}
        start = time.monotonic()
        response = client.get('/characters', headers=headers)
        print(name, response.status_code, round(time.monotonic()-start, 2),
              [(x['id'], x['access_level']) for x in response.json()] if response.status_code == 200 else 'failed')
    response = client.get('/gm/sessions', headers={'X-Omnisvera-Token': tokens['master_token']})
    response.raise_for_status()
    for session in response.json():
        narrative = session.get('narrative')
        print('session', session['id'], session['status'], 'narrative_fields', sorted(narrative) if isinstance(narrative, dict) else type(narrative).__name__)
    response = client.get('/scenes/active', headers={'X-Omnisvera-Token': tokens['master_token']})
    scene = response.json()
    print('ACTIVE_SCENE', {key: scene.get(key) for key in ('id', 'title', 'status', 'session_id')} if isinstance(scene, dict) else None)
