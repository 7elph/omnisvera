import sqlite3
from contextlib import closing
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from app import asset_api, asset_generation
from app.asset_approval import approve_job
from app.config import get_settings
from app.access import AccessContext
from test_asset_generation import _setup_db


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / 'db.sqlite'
        _setup_db(self.db)
        self.settings = replace(get_settings(), database_path=self.db, vault_path=self.root)
        self.patches = [patch.object(asset_generation, 'get_settings', return_value=self.settings), patch.object(asset_api, 'get_settings', return_value=self.settings)]
        for p in self.patches: p.start()
        self.job = next(j for j in asset_generation.queue_missing_assets(self.db) if j['asset_type'] == 'potion_hp')
        app = FastAPI()
        def master(x_omnisvera_token: str = Header(default='')):
            if x_omnisvera_token != 'gm': raise HTTPException(403)
            return AccessContext(mode='gm')
        asset_api.init_asset_api(app, master)
        self.client = TestClient(app)
        self.headers = {'X-Omnisvera-Token': 'gm'}

    def tearDown(self):
        self.client.close()
        for p in self.patches: p.stop()
        self.tmp.cleanup()

    def generate(self, size=(32, 32)):
        class Provider:
            def generate(self, prompt, path):
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.new('RGB', size, 'blue').save(path)
        with patch.object(asset_api, 'get_provider', return_value=Provider()):
            return self.client.post(f"/gm/assets/{self.job['id']}/regenerate", headers=self.headers)

    def test_generate_preview_approve_idempotent_catalogue(self):
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        job = response.json()
        self.assertEqual(job['status'], 'awaiting_approval')
        self.assertFalse((self.root / 'zz_media').exists())
        url = f"/gm/assets/{job['id']}/preview"
        self.assertEqual(self.client.get(url, headers=self.headers).status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 403)
        url = f"/gm/assets/{job['id']}/approve"
        payload = {'image_path': job['image_path']}
        self.assertEqual(self.client.post(url, json=payload).status_code, 403)
        first = self.client.post(url, json=payload, headers=self.headers)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()['status'], 'approved')
        self.assertEqual(self.client.post(url, json=payload, headers=self.headers).json(), first.json())
        with closing(sqlite3.connect(self.db)) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM session_workspace_icons').fetchone()[0], 1)
        published = self.root / first.json()['image_path']
        before = published.read_bytes()
        self.generate()
        self.assertEqual(published.read_bytes(), before)

    def test_placeholder_rejected(self):
        self.assertEqual(self.generate((1, 1)).status_code, 502)
        self.assertEqual(asset_generation.get_job(self.job['id'])['status'], 'failed')

    def test_stale_approval_rejected(self):
        old = self.generate().json()
        self.generate()
        with self.assertRaises(ValueError): approve_job(self.settings, self.job['id'], old['image_path'])

    def test_failure_returned_and_retry_clears_error(self):
        with patch.object(asset_api, 'get_provider', side_effect=RuntimeError('provider unavailable')):
            self.assertEqual(self.client.post(f"/gm/assets/{self.job['id']}/regenerate", headers=self.headers).status_code, 502)
        self.assertIsNone(self.generate().json()['error'])

    def test_concurrent_generation_blocked(self):
        with asset_api._generation_lock:
            response = self.client.post(f"/gm/assets/{self.job['id']}/regenerate", headers=self.headers)
        self.assertEqual(response.status_code, 409)
