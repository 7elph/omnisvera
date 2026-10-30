"""In-process HTTP against TEMP SQLite; no operational service or token."""
from contextlib import closing
from dataclasses import replace
import sqlite3
from unittest import TestCase
from unittest.mock import patch
from fastapi import Header, HTTPException
from fastapi.testclient import TestClient
from app import main
from app.access import AccessContext
import test_spell_engine as baseline

class GenericSpellRetryApiTests(TestCase):
    setUp=baseline.SpellEngineTests.setUp
    hp=baseline.SpellEngineTests.hp

    def client(self):
        def master(x_test_role: str | None=Header(default=None)):
            if x_test_role!='gm':raise HTTPException(status_code=403,detail='Mestre necessário')
            return AccessContext(mode='gm')
        previous=main.app.dependency_overrides.get(main.require_master)
        main.app.dependency_overrides[main.require_master]=master
        def restore():
            if previous is None:main.app.dependency_overrides.pop(main.require_master,None)
            else:main.app.dependency_overrides[main.require_master]=previous
        self.addCleanup(restore)
        settings=patch.object(main,'settings',replace(main.settings,database_path=self.db))
        settings.start();self.addCleanup(settings.stop)
        client=TestClient(main.app);self.addCleanup(client.close)
        return client

    def test_http_replay_keeps_result_and_single_damage(self):
        client=self.client();body=dict(request_id='http-spell-retry',caster_type='token',caster_id='gob1',
            targets=[dict(type='character',id='vezemir')],roll_mode='physical',d20=[1])
        with patch('app.spell_engine.roll_formula',return_value={'total':4}) as rng:
            a=client.post('/gm/compendium/spells/arcana-bola-de-fogo/cast',json=body,headers={'X-Test-Role':'gm'})
            b=client.post('/gm/compendium/spells/arcana-bola-de-fogo/cast',json=body,headers={'X-Test-Role':'gm'})
        self.assertEqual(200,a.status_code,a.text);self.assertEqual(a.json(),b.json());self.assertEqual(26,self.hp());self.assertEqual(1,rng.call_count)

    def test_http_usable_replay_and_cross_route_collision(self):
        client=self.client();body=dict(request_id='http-usable-retry',ability_name='Baforada de teste',
            targets=[dict(type='character',id='vezemir')],roll_mode='physical',d20=[1])
        with patch('app.spell_engine.roll_formula',return_value={'total':4}):
            a=client.post('/gm/workspace/tokens/gob1/actions/execute',json=body,headers={'X-Test-Role':'gm'})
            b=client.post('/gm/workspace/tokens/gob1/actions/execute',json=body,headers={'X-Test-Role':'gm'})
        self.assertEqual(200,a.status_code,a.text);self.assertEqual(a.json(),b.json());self.assertEqual(26,self.hp())
        body.pop('ability_name');body.update(caster_type='token',caster_id='gob1')
        clash=client.post('/gm/compendium/spells/arcana-bola-de-fogo/cast',json=body,headers={'X-Test-Role':'gm'})
        self.assertEqual(400,clash.status_code);self.assertEqual(26,self.hp())

    def test_unauthorized_or_malformed_request_does_not_damage(self):
        client=self.client();body=dict(request_id='valid-id',caster_type='token',caster_id='gob1',targets=[dict(type='character',id='vezemir')])
        denied=client.post('/gm/compendium/spells/arcana-bola-de-fogo/cast',json=body)
        self.assertEqual(403,denied.status_code)
        body['request_id']='bad key'
        invalid=client.post('/gm/compendium/spells/arcana-bola-de-fogo/cast',json=body,headers={'X-Test-Role':'gm'})
        self.assertEqual(422,invalid.status_code);self.assertEqual(30,self.hp())
