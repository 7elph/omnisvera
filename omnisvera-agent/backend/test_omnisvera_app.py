import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from contextlib import closing

from fastapi.testclient import TestClient
from omnisvera_app import create_app, ReadStore, MemoryStore
from observer_qa import seed


class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'test.db'
        store = MemoryStore(self.path)
        snapshot = store.create_snapshot_memory(domain='world.football', subject='fixture', state={'rating': 1500})
        self.pid = store.create_prediction(domain='world.football', world_id='football', snapshot_memory_id=snapshot,
            claim='Fixture only', probability=.6, horizon='2099-01-01T00:00:00Z', resolution_rule={})
        self.other = store.create_prediction(domain='world.crypto', world_id='crypto', snapshot_memory_id=snapshot,
            claim='Hidden other world', probability=.5, horizon='2099-01-01T00:00:00Z', resolution_rule={})
        self.token = 'test-only-' + 'x'*40
        self.client = TestClient(create_app(self.path, self.token))
        self.addCleanup(self.client.close)
        self.headers = {'X-Omnisvera-App-Token': self.token}

    def test_auth_and_identity(self):
        self.assertEqual(self.client.get('/api/football').status_code,401)
        self.assertEqual(self.client.get('/api/football?actor=admin',headers=self.headers).status_code,400)
        with TestClient(create_app(self.path,self.token,scopes=frozenset())) as client:
            self.assertEqual(client.get('/api/football',headers=self.headers).status_code,403)

    def test_persisted_read_no_mutation(self):
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        for path in ['/api/football','/api/monitor',f'/api/football/predictions/{self.pid}']:
            response=self.client.get(path,headers=self.headers)
            self.assertEqual(response.status_code,200,response.text)
        data=self.client.get('/api/football',headers=self.headers).json()
        self.assertEqual(data['total'],1)
        self.assertIsNone(data['accuracy'])
        self.assertIsNone(data['roi'])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)

    def test_world_boundary_and_no_writes(self):
        self.assertEqual(self.client.get(f'/api/football/predictions/{self.other}',headers=self.headers).status_code,404)
        self.assertEqual(self.client.post('/api/football',headers=self.headers,json={}).status_code,405)
        connection=ReadStore(self.path)._connect()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute('DELETE FROM predictions')
        finally:
            connection.close()

    def test_missing_database_not_created(self):
        missing=Path(self.temp.name)/'missing.db'
        with TestClient(create_app(missing,self.token)) as client:
            self.assertEqual(client.get('/api/football',headers=self.headers).status_code,503)
        self.assertFalse(missing.exists())

    def test_investigation_does_not_invent_match_or_signals(self):
        detail = self.client.get(f'/api/football/predictions/{self.pid}', headers=self.headers).json()
        self.assertIsNone(detail['subject_ref'])
        self.assertEqual(detail['signal_refs'], [])
        self.assertIsNone(detail['resolution'])
        monitor = self.client.get('/api/monitor', headers=self.headers).json()
        self.assertIsNone(monitor['football_last_run'])

    def fixture(self):
        path=Path(self.temp.name)/'populated.db'
        ids=seed(path)
        client=TestClient(create_app(path,self.token))
        self.addCleanup(client.close)
        return path,ids,client

    def test_signal_filters_pagination_and_redaction(self):
        path,_,client=self.fixture()
        result=client.get('/api/football/signals?limit=2',headers=self.headers)
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['total'],4)
        self.assertEqual(len(result.json()['items']),2)
        self.assertNotIn('withheld',result.text)
        self.assertNotIn('authorization',result.text)
        selected=client.get('/api/football/signals',params={'signal_id':'football.match.home_score','entity_ref':'match:qa-0'},headers=self.headers).json()
        self.assertEqual(selected['total'],1)
        self.assertEqual(selected['items'][0]['value'],2)
        timestamp=selected['items'][0]['observed_at']
        exact=client.get('/api/football/signals',params={'since':timestamp,'until':timestamp},headers=self.headers).json()
        self.assertEqual(exact['total'],1)
        empty=client.get('/api/football/signals',params={'signal_id':"' OR 1=1 --"},headers=self.headers).json()
        self.assertEqual(empty['total'],0)

    def test_invalid_period_and_scopes(self):
        for params in ({'since':'bad'},{'since':'2026-01-01T00:00:00'},
                       {'since':'2026-02-01T00:00:00Z','until':'2026-01-01T00:00:00Z'},{'limit':101}):
            self.assertEqual(self.client.get('/api/football/signals',params=params,headers=self.headers).status_code,422)
        for route in ('/api/football/signals','/api/football/experiences?predictor_id=x&predictor_version=y'):
            self.assertEqual(self.client.get(route).status_code,401)
            with TestClient(create_app(self.path,self.token,scopes=frozenset())) as client:
                self.assertEqual(client.get(route,headers=self.headers).status_code,403)
            self.assertEqual(self.client.post(route,headers=self.headers).status_code,405)

    def test_lineage_resolution_and_integrity(self):
        _,ids,client=self.fixture()
        history=client.get('/api/football/experiences?predictor_id=football.qa&predictor_version=fixture',headers=self.headers).json()
        self.assertEqual([x['state_version'] for x in history['items']],[2,1])
        latest=history['items'][0]
        self.assertTrue(latest['integrity_ok'])
        self.assertEqual(latest['previous_experience_id'],ids['first']['experience_id'])
        self.assertEqual(latest['performance']['mean_brier'],.16)
        self.assertEqual(latest['source_outcomes'][0]['prediction_id'],ids['resolved'])
        detail=client.get(f"/api/football/predictions/{ids['open']}",headers=self.headers).json()
        self.assertTrue(detail['experience_reference_intact'])
        self.assertEqual(detail['signal_refs'][0]['signal_id'],'football.match.home_score')
        self.assertIsNone(detail['resolution'])
        resolved=client.get(f"/api/football/predictions/{ids['resolved']}",headers=self.headers).json()
        self.assertEqual(resolved['resolution']['outcome'],1)

    def test_all_read_paths_leave_database_identical_and_no_network(self):
        path,ids,client=self.fixture()
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        with patch('socket.create_connection',side_effect=AssertionError('Unexpected external I/O')):
            for route in ('/api/football','/api/monitor','/api/football/signals',
                          '/api/football/experiences?predictor_id=football.qa&predictor_version=fixture',
                          f"/api/football/predictions/{ids['open']}"):
                response=client.get(route,headers=self.headers)
                self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(before,hashlib.sha256(path.read_bytes()).hexdigest())

    def test_freshness_is_not_invented(self):
        path,_,_=self.fixture()
        with TestClient(create_app(path,self.token,clock=lambda:datetime(2099,1,1,tzinfo=timezone.utc))) as client:
            result=client.get('/api/football/signals',headers=self.headers).json()
        self.assertEqual({x['freshness_at_capture'] for x in result['items']},{'fresh','stale','unknown','error'})
        self.assertTrue(all(x['age_seconds']>86400 for x in result['items']))
        self.assertEqual(result['freshness_rule'],'age-only; no inferred TTL')

    def test_bad_integrity_and_missing_contributor_visible(self):
        path,ids,client=self.fixture()
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("UPDATE predictor_experiences SET learned_state_hash='tampered',source_prediction_ids_json='[999999]' WHERE experience_id=?",(ids['second']['experience_id'],))
        data=client.get('/api/football/experiences?predictor_id=football.qa&predictor_version=fixture',headers=self.headers).json()
        self.assertFalse(data['items'][0]['integrity_ok'])
        self.assertEqual(data['items'][0]['source_predictions'][0]['status'],'unavailable')


if __name__=='__main__':
    unittest.main()
