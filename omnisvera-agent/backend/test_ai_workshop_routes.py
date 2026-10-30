import hashlib
from contextlib import closing
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from app import ai_workshop as workshop
from app.ai_workshop_routes import build_workshop_router, workshop_database_path


class WorkshopRoutesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'private.sqlite3'
        self.campaign = Path(self.tmp.name) / 'campaign.sqlite3'

        def master(x_test_role: str | None = Header(default=None)):
            if x_test_role != 'gm':
                raise HTTPException(401, 'Private')

        app = FastAPI()
        app.include_router(build_workshop_router(lambda: self.db, lambda: self.campaign, master))
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.headers = {'X-Test-Role': 'gm'}

    def seed(self):
        return workshop.enqueue_job(self.db, queue='text', entity_type='session', entity_id='7',
            revision='v1', purpose='npc_lore', request_id='workshop-routes-fixture',
            payload={'sources': [{'path': 'private/transcript.txt', 'text': 'PRIVATE TRANSCRIPT',
                                  'sha256': 'a' * 64}]})['job']['id']

    def test_player_and_anonymous_cannot_read_summary_or_result(self):
        for headers in ({}, {'X-Test-Role': 'player'}):
            for path in ('/gm/ai-workshop', '/gm/ai-workshop/jobs/1'):
                self.assertEqual(self.client.get(path, headers=headers).status_code, 401)
        self.assertFalse(self.db.exists())

    def test_missing_database_is_not_created_by_inspection(self):
        response = self.client.get('/gm/ai-workshop', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['initialized'])
        self.assertFalse(self.db.exists())
        self.assertFalse(self.campaign.exists())

    def test_summary_is_read_only_and_does_not_include_source_payload(self):
        self.seed()
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        response = self.client.get('/gm/ai-workshop', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['counts']['text']['queued'], 1)
        self.assertEqual(data['worker']['state'], 'stopped')
        self.assertNotIn('PRIVATE TRANSCRIPT', response.text)
        self.assertNotIn('payload_json', response.text)
        self.assertNotIn('db', data)
        self.assertEqual(before, hashlib.sha256(self.db.read_bytes()).hexdigest())

    def test_result_preview_is_readable_without_exposing_input(self):
        job_id = self.seed()
        import sqlite3
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute('UPDATE ai_workshop_jobs SET status=?,output_json=? WHERE id=?',
                ('awaiting_approval', json.dumps({'draft': 'O anão oferece reparos.',
                    'facts': ['Loja em Nimalis'], 'suggestions': ['Uma encomenda desaparecida'],
                    'questions': ['Quem contratou?'], 'provider': 'fixture', 'model': 'test'}), job_id))
        response = self.client.get(f'/gm/ai-workshop/jobs/{job_id}', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['preview']['draft'], 'O anão oferece reparos.')
        self.assertNotIn('PRIVATE TRANSCRIPT', response.text)
        self.assertNotIn('payload_json', response.text)

    def test_missing_result_and_mutations_are_rejected(self):
        self.seed()
        self.assertEqual(self.client.get('/gm/ai-workshop/jobs/9999', headers=self.headers).status_code, 404)
        self.assertEqual(self.client.post('/gm/ai-workshop', headers=self.headers).status_code, 405)

    def test_review_requires_master_and_rejects_stale_hash(self):
        import sqlite3
        from app import scene_play
        job_id = self.seed()
        scene_play.init_scene_play(self.campaign)
        scene, _ = scene_play.create_scene(self.campaign, request_id='fixture-scene-review',
            campaign_id='omnisvera', title='Privada', location_name='Fixture', created_by='master')
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute('UPDATE ai_workshop_jobs SET status=?,output_json=? WHERE id=?',
                ('awaiting_approval', json.dumps({'draft': 'Segredo da fixture'}), job_id))
        detail = self.client.get(f'/gm/ai-workshop/jobs/{job_id}', headers=self.headers).json()
        body = dict(decision='import', scene_id=scene['id'], expected_revision='v1',
            expected_output_hash='0'*64, request_id='fixture-review-once')
        path = f'/gm/ai-workshop/jobs/{job_id}/review'
        for headers in ({}, {'X-Test-Role': 'player'}):
            self.assertEqual(self.client.post(path, json=body, headers=headers).status_code, 401)
        self.assertEqual(self.client.post(path, json=body, headers=self.headers).status_code, 409)
        body['expected_output_hash'] = detail['output_hash']
        first = self.client.post(path, json=body, headers=self.headers)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json(), self.client.post(path, json=body, headers=self.headers).json())

    def test_default_runtime_path_and_explicit_override(self):
        from unittest.mock import patch
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(workshop_database_path(), Path(__file__).resolve().parents[1] / '.autonomy/runtime/ai-workshop.sqlite3')
        with patch.dict('os.environ', {'OMNISVERA_AI_WORKSHOP_DB': str(self.db)}):
            self.assertEqual(workshop_database_path(), self.db.resolve())


if __name__ == '__main__':
    unittest.main()
