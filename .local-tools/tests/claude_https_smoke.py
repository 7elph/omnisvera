"""Explicit, read-only HTTPS acceptance probe. Never follows Claude callback."""
import base64
import hashlib
import json
import re
import secrets
import sqlite3
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.local-tools'))
from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES


def domain_fingerprint():
    path = ROOT / '.assistant-runtime/omnisvera-mcp/memory.db'
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        return {name: hashlib.sha256(repr(db.execute('SELECT * FROM ' + name + ' ORDER BY rowid').fetchall()).encode()).hexdigest()
                for name in ('predictions', 'prediction_resolutions', 'predictor_experiences', 'experience_update_events')}


def main():
    runtime = ROOT / '.assistant-runtime/claude-connector'
    origin = json.loads((runtime / 'config.json').read_text())['issuer']
    password = (runtime / 'login-password.txt').read_text().strip()
    before = domain_fingerprint()
    session = requests.Session()
    def call(method, path, **kwargs):
        return session.request(method, origin + path, timeout=45, **kwargs)
    for method in ('GET','POST'):
        challenge_response=call(method, '/mcp')
        assert challenge_response.status_code==401
        metadata_url=re.search(r'resource_metadata="([^"]+)"',challenge_response.headers['WWW-Authenticate']).group(1)
    resource_metadata=session.get(metadata_url,timeout=45).json()
    assert resource_metadata['resource']==origin+'/mcp'
    issuer=resource_metadata['authorization_servers'][0]
    auth_metadata=session.get(issuer.rstrip('/')+'/.well-known/oauth-authorization-server',timeout=45).json()
    assert auth_metadata['issuer']==issuer
    assert auth_metadata['token_endpoint_auth_methods_supported']==['none']
    assert auth_metadata['code_challenge_methods_supported']==['S256']
    for field in ('authorization_endpoint','token_endpoint','registration_endpoint'):
        assert auth_metadata[field].startswith(origin+'/')
    print('401_METADATA_AUTH_DISCOVERY PASS')
    callback = 'https://claude.ai/api/mcp/auth_callback'
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    r = session.post(auth_metadata['registration_endpoint'],timeout=45, json={'redirect_uris': [callback], 'token_endpoint_auth_method': 'none',
        'grant_types': ['authorization_code', 'refresh_token'], 'response_types': ['code'], 'scope': 'omnisvera.read offline_access'})
    assert r.status_code == 201
    client_id = r.json()['client_id']
    r = session.get(auth_metadata['authorization_endpoint'],timeout=45, params=dict(client_id=client_id, redirect_uri=callback, response_type='code',
        code_challenge=challenge, code_challenge_method='S256', scope='omnisvera.read offline_access', state='smoke', resource=origin+'/mcp'))
    nonce = re.search('name="request" value="([^"]+)"', r.text).group(1)
    r = call('POST', '/login', data={'request': nonce, 'password': password}, headers={'Origin': origin}, allow_redirects=False)
    assert r.status_code == 303
    code = parse_qs(urlparse(r.headers['location']).query)['code'][0]
    r = session.post(auth_metadata['token_endpoint'],timeout=45, data=dict(grant_type='authorization_code', client_id=client_id, code=code,
        redirect_uri=callback, code_verifier=verifier, resource=origin+'/mcp'))
    assert r.status_code == 200
    tokens = r.json()
    headers = {'Authorization': 'Bearer '+tokens['access_token'], 'Accept': 'application/json, text/event-stream'}
    for method, params in [('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name':'https-smoke','version':'1'}}),
                           ('tools/list', {}), ('tools/call', {'name':'system.health','arguments':{}}),
                           ('tools/call', {'name':'system.bootstrap','arguments':{}})]:
        r = call('POST', '/mcp', headers=headers, json={'jsonrpc':'2.0','id':1,'method':method,'params':params})
        assert r.status_code == 200
        data = r.json()
        assert not data.get('error') and not data['result'].get('isError')
        assert not any(s in r.text for s in (password, tokens['access_token'], tokens['refresh_token']))
        if method == 'tools/list':
            names = {t['name'] for t in data['result']['tools']}
            assert names == set(REMOTE_TOOL_NAMES) and 'epistemic.create_prediction' not in names
            print('REMOTE_TOOL_COUNT', len(names))
        print(method, params.get('name',''), 'PASS')
    for field in ('actor', 'client'):
        r = call('POST', '/mcp', headers=headers, json={'jsonrpc':'2.0','id':2,'method':'tools/call',
            'params':{'name':'system.health','arguments':{field:'forged'}}})
        assert r.status_code == 400
    assert before == domain_fingerprint(), 'Operational domain state changed during probe'
    for path in runtime.glob('*.log'):
        contents = path.read_text(errors='replace')
        assert not any(s in contents for s in (password, tokens['access_token'], tokens['refresh_token']))
    print('IDENTITY_INJECTION PASS; DOMAIN_UNCHANGED PASS; SECRET_EXPOSURE NO')


if __name__ == '__main__':
    main()
