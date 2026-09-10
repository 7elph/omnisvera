import base64
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlparse,parse_qs

sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from starlette.testclient import TestClient
from claude_connector import build_connector
from claude_oauth import CALLBACK
from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES
from omnisvera_mcp.core.registry import ToolRegistry,RegisteredTool


class Collector:
    def __init__(self): self.events=[]
    def record(self,event): self.events.append(event)


class ClaudeConnectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.audit=Collector(); self.registry=ToolRegistry(audit=self.audit)
        for name in REMOTE_TOOL_NAMES:
            scopes={"epistemic.write"} if name=="epistemic.commit_candidate" else {"world.read"}
            self.registry.register(RegisteredTool(name,lambda ctx,args:json.dumps({"ok":True}),"read","test://read",frozenset(scopes)))
        app,_,self.provider,_=build_connector(self.registry,"https://connector.example",Path(self.tmp.name)/"oauth.db","test-password")
        self.http=self.enterContext(TestClient(app,base_url="https://connector.example"))

    def begin(self):
        r=self.http.post('/register',json={"redirect_uris":[CALLBACK],"token_endpoint_auth_method":"none",
            "grant_types":["authorization_code","refresh_token"],"response_types":["code"],"scope":"omnisvera.read offline_access"})
        self.assertEqual(r.status_code,201,r.text)
        self.client_id=r.json()['client_id']; self.verifier='x'*64
        challenge=base64.urlsafe_b64encode(hashlib.sha256(self.verifier.encode()).digest()).decode().rstrip('=')
        r=self.http.get('/authorize',params=dict(client_id=self.client_id,redirect_uri=CALLBACK,response_type="code",
            code_challenge=challenge,code_challenge_method="S256",scope="omnisvera.read offline_access",
            state="test-state",resource="https://connector.example/mcp"))
        self.assertEqual(r.status_code,200,r.text)
        self.nonce=re.search('name="request" value="([^"]+)"',r.text).group(1)

    def authorize(self,crypto=False):
        self.begin()
        r=self.http.post('/login',data={"request":self.nonce,"password":"test-password", "crypto_consent":"yes" if crypto else "no"},
                         headers={"Origin":"https://connector.example"},follow_redirects=False)
        self.assertEqual(r.status_code,303,r.text)
        params=parse_qs(urlparse(r.headers['location']).query)
        self.assertEqual(params['state'],['test-state']); self.code=params['code'][0]
        self.token_args=dict(grant_type="authorization_code",client_id=self.client_id,code=self.code,
                             redirect_uri=CALLBACK,code_verifier=self.verifier,resource="https://connector.example/mcp")
        r=self.http.post('/token',data=self.token_args)
        self.assertEqual(r.status_code,200,r.text)
        self.tokens=r.json()
        return {"Authorization":"Bearer "+self.tokens['access_token'],"Accept":"application/json, text/event-stream"}

    def test_oauth_discovery_read_and_audit(self):
        self.assertEqual(self.http.post('/mcp',json={}).status_code,401)
        meta=self.http.get('/.well-known/oauth-authorization-server').json()
        self.assertIn('S256',meta['code_challenge_methods_supported'])
        self.assertEqual(meta['token_endpoint_auth_methods_supported'],['none'])
        h=self.authorize()
        r=self.http.post('/mcp',headers=h,json={"jsonrpc":"2.0","id":1,"method":"tools/list"})
        self.assertEqual(r.status_code,200,r.text)
        names={t['name'] for t in r.json()['result']['tools']}
        self.assertEqual(names,set(REMOTE_TOOL_NAMES)); self.assertNotIn('epistemic.create_prediction',names)
        r=self.http.post('/mcp',headers=h,json={"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"system.health","arguments":{}}})
        self.assertFalse(r.json()['result'].get('isError'))
        event=self.audit.events[-1]
        self.assertEqual((event['actor'],event['client'],event['transport']),('claude.observer','claude','streamable-http'))
        self.assertEqual(event['metadata']['caller_class'],'external-ai')
        self.assertNotIn(self.tokens['access_token'],json.dumps(self.audit.events))

    def test_identity_and_write_denied(self):
        h=self.authorize()
        for field in ['actor','client','scopes']:
            r=self.http.post('/mcp',headers=h,json={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"system.health","arguments":{field:"crypto.btc.direction"}}})
            self.assertEqual(r.status_code,400)
        r=self.http.post('/mcp',headers=h,json={"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"epistemic.commit_candidate","arguments":{"candidate":{"predictor_id":"crypto.btc.direction"}}}})
        self.assertTrue(r.json()['result']['isError'])
        self.assertEqual(self.audit.events[-1]['result'],'denied')

    def test_refresh_rotation_and_code_replay(self):
        h=self.authorize()
        self.assertEqual(self.http.post('/token',data=self.token_args).status_code,400)
        args=dict(grant_type="refresh_token",client_id=self.client_id,refresh_token=self.tokens['refresh_token'])
        r=self.http.post('/token',data=args)
        self.assertEqual(r.status_code,200,r.text)
        self.assertNotEqual(r.json()['refresh_token'],self.tokens['refresh_token'])
        self.assertEqual(self.http.post('/token',data=args).status_code,400)
        self.assertEqual(self.http.post('/mcp',headers=h,json={}).status_code,401)

    def test_token_resource_and_pkce_rejected(self):
        self.authorize()
        args=dict(grant_type='refresh_token',client_id=self.client_id,
                  refresh_token=self.tokens['refresh_token'],resource='https://other.example/mcp')
        self.assertEqual(self.http.post('/token',data=args).status_code,400)
        args['resource']='https://connector.example/mcp'
        self.assertEqual(self.http.post('/token',data=args).status_code,200)
        self.begin()
        r=self.http.post('/login',data={'request':self.nonce,'password':'test-password'},
            headers={'Origin':'https://connector.example'},follow_redirects=False)
        code=parse_qs(urlparse(r.headers['location']).query)['code'][0]
        args=dict(grant_type='authorization_code',client_id=self.client_id,code=code,
                  redirect_uri=CALLBACK,code_verifier='wrong'*13,resource='https://connector.example/mcp')
        self.assertEqual(self.http.post('/token',data=args).status_code,400)

    def test_bad_login_and_redirect(self):
        self.assertEqual(self.http.post('/register',json={"redirect_uris":["https://evil.example/callback"],"token_endpoint_auth_method":"none"}).status_code,400)
        self.begin()
        self.assertEqual(self.http.post('/login',data={"request":self.nonce,"password":"test-password"},headers={"Origin":"https://evil.example"}).status_code,403)
        self.assertEqual(self.http.post('/login',data={"request":self.nonce,"password":"wrong"},headers={"Origin":"https://connector.example"}).status_code,403)

    def test_login_origin_allowed(self):
        self.begin()
        page=self.http.get('/login',params={'request':self.nonce})
        self.assertEqual(page.headers['referrer-policy'],'same-origin')
        self.assertIn("form-action 'self' " + CALLBACK + ";",page.headers['content-security-policy'])
        for origin in ('null','https://evil.example'):
            rejected=self.http.post('/login',data={'request':self.nonce,'password':'test-password'},
                                    headers={'Origin':origin},follow_redirects=False)
            self.assertEqual(rejected.status_code,403)
            self.assertEqual(rejected.json()['error'],'invalid_origin')
        r = self.http.post('/login', data={"request": self.nonce, "password": "test-password"},
                           headers={"Origin": "https://connector.example"}, follow_redirects=False)
        self.assertEqual(r.status_code, 303)
        self.begin()
        r = self.http.post('/login', data={"request": self.nonce, "password": "test-password"},
                           headers={"Origin": "https://claude.ai"}, follow_redirects=False)
        self.assertEqual(r.status_code, 303)
        self.begin()
        r = self.http.post('/login', data={"request": self.nonce, "password": "test-password"},
                           headers={"Origin": "https://evil.example"}, follow_redirects=False)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json().get("error"), "invalid_origin")

    def test_actual_predictor_binding_in_temporary_database(self):
        from datetime import datetime, timedelta, timezone
        from test_crypto_btc_poc import CryptoPoCTest
        from omnisvera_mcp.core.context import CallContext
        from omnisvera_mcp import epistemic
        fixture=CryptoPoCTest()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.candidate['horizon']=(datetime.now(timezone.utc)+timedelta(hours=1)).replace(second=0,microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
        for actor in ('claude.observer','football.elo'):
            context=CallContext(actor=actor,client='claude',transport='streamable-http',
                                scopes=fixture.ctx.scopes,request_id='fixture-only')
            with self.assertRaisesRegex(ValueError,'not authorized'):
                epistemic.commit_candidate(fixture.store,context,{'candidate':fixture.candidate})
        # Explicitly authorized server-owned fixture principal, never production.
        result=json.loads(epistemic.commit_candidate(fixture.store,fixture.ctx,{'candidate':fixture.candidate}))
        self.assertEqual(result['status'],'created')

    def test_crypto_session_scoped_write_and_refresh(self):
        from datetime import datetime,timedelta,timezone
        from test_crypto_btc_poc import CryptoPoCTest
        from omnisvera_mcp import epistemic
        fixture=CryptoPoCTest(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.candidate['horizon']=(datetime.now(timezone.utc)+timedelta(hours=1)).replace(second=0,microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.registry._tools['epistemic.commit_candidate']=RegisteredTool('epistemic.commit_candidate',
            lambda ctx,args:epistemic.commit_candidate(fixture.store,ctx,args),'write','epistemic://predictions',frozenset({'epistemic.write'}))
        self.registry._tools['epistemic.snapshot_from_model']=RegisteredTool('epistemic.snapshot_from_model',
            lambda ctx,args:self.fail('Broad write escaped transport scope'),'write','epistemic://snapshots',frozenset({'epistemic.write'}))
        def invoke(h,name,args):
            return self.http.post('/mcp',headers=h,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}})
        observer=self.authorize()
        self.assertFalse(invoke(observer,'system.health',{}).json()['result'].get('isError'))
        self.assertTrue(invoke(observer,'epistemic.commit_candidate',{'candidate':fixture.candidate}).json()['result']['isError'])
        crypto=self.authorize(crypto=True)
        first=invoke(crypto,'epistemic.commit_candidate',{'candidate':fixture.candidate}).json()['result']
        self.assertFalse(first.get('isError'),first)
        created=json.loads(first['content'][0]['text'])
        replay=invoke(crypto,'epistemic.commit_candidate',{'candidate':fixture.candidate}).json()['result']
        replay=json.loads(replay['content'][0]['text'])
        self.assertEqual(replay['status'],'already_committed')
        self.assertEqual(replay['prediction_id'],created['prediction_id'])
        pred=fixture.store.get_prediction(created['prediction_id'])
        self.assertEqual(pred['candidate_hash'],created['candidate_hash'])
        self.assertEqual(self.audit.events[-1]['actor'],'crypto.btc.direction')
        self.assertEqual(self.audit.events[-1]['client'],'claude')
        self.assertEqual(self.audit.events[-1]['transport'],'streamable-http')
        self.assertEqual(self.audit.events[-1]['metadata']['caller_class'],'external-ai')
        football={k:v for k,v in fixture.candidate.items() if not k.startswith('experience_')}
        football['predictor_id']='football.elo'
        self.assertTrue(json.loads(epistemic.validate_candidate(fixture.store,fixture.ctx,{'candidate':football}))['valid'])
        denied=invoke(crypto,'epistemic.commit_candidate',{'candidate':football}).json()['result']
        self.assertTrue(denied['isError']); self.assertIn('not authorized',str(denied))
        self.assertTrue(invoke(crypto,'epistemic.snapshot_from_model',{'model':{}}).json()['result']['isError'])
        self.assertEqual(invoke(crypto,'system.health',{'actor':'football.elo'}).status_code,400)
        refresh=self.http.post('/token',data={'grant_type':'refresh_token','client_id':self.client_id,'refresh_token':self.tokens['refresh_token']})
        self.assertEqual(refresh.status_code,200)
        refreshed={**crypto,'Authorization':'Bearer '+refresh.json()['access_token']}
        self.assertFalse(invoke(refreshed,'system.health',{}).json()['result'].get('isError'))
        self.assertEqual(self.audit.events[-1]['actor'],'crypto.btc.direction')
        self.assertTrue(invoke(observer,'epistemic.commit_candidate',{'candidate':fixture.candidate}).json()['result']['isError'])

    def test_snapshot_scoped_crypto_world_only(self):
        # A/B/C + H/I/J scoped snapshot minimal surface
        from datetime import datetime, timedelta, timezone
        from test_crypto_btc_poc import CryptoPoCTest
        from omnisvera_mcp import epistemic
        fixture = CryptoPoCTest(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        # Real snapshot path would need world.model; mock registry snapshot to avoid DB writes
        # but keep policy check: only crypto world_id should pass through ClaudeRegistry
        self.registry._tools['epistemic.snapshot_from_model'] = RegisteredTool(
            'epistemic.snapshot_from_model',
            lambda ctx, args: json.dumps({"snapshot_id": "snap-test", "world_id": args.get("model", {}).get("world_id")}),
            'write', 'epistemic://snapshots', frozenset({'epistemic.write'}))
        self.registry._tools['world.capture_signals'] = RegisteredTool(
            'world.capture_signals',
            lambda ctx, args: json.dumps({"captured": 1}),
            'write', 'world://signals/capture', frozenset({'world.write'}))
        self.registry._tools['epistemic.resolve_due_predictions'] = RegisteredTool(
            'epistemic.resolve_due_predictions',
            lambda ctx, args: json.dumps({"resolved": 1}),
            'write', 'epistemic://predictions', frozenset({'epistemic.write'}))
        # also ensure commit still works via real handler for later
        self.registry._tools['epistemic.commit_candidate'] = RegisteredTool(
            'epistemic.commit_candidate',
            lambda ctx, args: epistemic.commit_candidate(fixture.store, ctx, args),
            'write', 'epistemic://predictions', frozenset({'epistemic.write'}))
        def invoke(h, name, args):
            return self.http.post('/mcp', headers=h, json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}})
        observer = self.authorize()
        crypto = self.authorize(crypto=True)
        # A) observer -> snapshot crypto BLOCK
        self.assertTrue(invoke(observer, 'epistemic.snapshot_from_model', {'model': {'world_id': 'crypto', 'state': {}}}).json()['result']['isError'])
        # B) crypto -> snapshot crypto PASS
        ok = invoke(crypto, 'epistemic.snapshot_from_model', {'model': {'world_id': 'crypto', 'state': {'price': 100}}}).json()['result']
        self.assertFalse(ok.get('isError'), ok)
        self.assertIn('snap-test', ok['content'][0]['text'])
        self.assertEqual(self.audit.events[-1]['actor'], 'crypto.btc.direction')
        # C) crypto -> snapshot football BLOCK
        self.assertTrue(invoke(crypto, 'epistemic.snapshot_from_model', {'model': {'world_id': 'football', 'state': {}}}).json()['result']['isError'])
        # empty model also BLOCK
        self.assertTrue(invoke(crypto, 'epistemic.snapshot_from_model', {'model': {}}).json()['result']['isError'])
        # H) resolve_due BLOCK
        self.assertTrue(invoke(crypto, 'epistemic.resolve_due_predictions', {}).json()['result']['isError'])
        self.assertTrue(invoke(observer, 'epistemic.resolve_due_predictions', {}).json()['result']['isError'])
        # I) capture_signals BLOCK
        self.assertTrue(invoke(crypto, 'world.capture_signals', {'world_id': 'crypto', 'signals': []}).json()['result']['isError'])
        self.assertTrue(invoke(observer, 'world.capture_signals', {'world_id': 'crypto', 'signals': []}).json()['result']['isError'])
        # J) create_prediction absent remotely
        listed = self.http.post('/mcp', headers=crypto, json={'jsonrpc':'2.0','id':1,'method':'tools/list'}).json()['result']['tools']
        names = {t['name'] for t in listed}
        self.assertNotIn('epistemic.create_prediction', names)
        # direct call should be unknown tool / error
        r = invoke(crypto, 'epistemic.create_prediction', {})
        self.assertTrue(r.json().get('error') or r.json()['result'].get('isError'))
        # K) minimal crypto canonicalization still works via validate
        fixture.candidate['horizon'] = (datetime.now(timezone.utc)+timedelta(hours=1)).replace(second=0,microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
        minimal = {k: fixture.candidate[k] for k in ('world_id','domain','claim','probability','horizon','model_snapshot_id','predictor_id','predictor_version','experience_id','experience_state_version','experience_state_hash')}
        minimal['resolution_rule'] = {"type":"price_direction","coin_id":"bitcoin","quote":"usd","comparison":"horizon_price_gt_reference","resolver_id":"crypto.btc.direction.v1"}
        valid = json.loads(epistemic.validate_candidate(fixture.store, fixture.ctx, {"candidate": minimal}))
        self.assertTrue(valid['valid'], valid)
        # validate mutates candidate to canonicalized form server-side
        self.assertEqual(minimal['resolution_rule']['source'], 'https://api.exchange.coinbase.com/products/BTC-USD/candles')
        self.assertEqual(minimal['resolution_rule']['price_basis'], 'closed_1m_candle')
        self.assertIn('reference_price', minimal['resolution_rule'])
        self.assertIn('reference_observed_at', minimal['resolution_rule'])
        # commit minimal canonicalized via transport should also PASS for crypto
        committed = invoke(crypto, 'epistemic.commit_candidate', {'candidate': minimal}).json()['result']
        self.assertFalse(committed.get('isError'), committed)


if __name__=='__main__': unittest.main()
