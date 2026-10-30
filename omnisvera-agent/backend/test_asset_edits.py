import hashlib
import sqlite3
from contextlib import closing
from unittest.mock import patch
import unittest
from PIL import Image
from app import asset_api, asset_generation
import test_asset_approval


class ImageEditTests(unittest.TestCase):
    setUp = test_asset_approval.ApprovalTests.setUp
    tearDown = test_asset_approval.ApprovalTests.tearDown

    def source(self):
        path = self.root / 'zz_media/original.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (32, 48), 'red').save(path)
        self.original = path.read_bytes()
        return path

    def payload(self):
        return {'image_path': 'zz_media/original.png', 'instruction': 'Remove only the weapon', 'request_id': 'edit-test-001'}

    def test_explicit_mode_records_actual_route_and_replay_cannot_change_mode(self):
        self.source()
        provider = self.provider()
        provider.last_run = {'mode': 'test', 'requested_model': 'flux-2-klein-4b', 'used_provider': 'cloudflare', 'fallback_used': False}
        with patch.object(asset_api, 'get_provider', return_value=provider) as factory:
            response = self.client.post('/gm/assets/adjust', json={**self.payload(), 'generation_mode': 'test'}, headers=self.headers)
            self.assertEqual(response.status_code, 200, response.text)
            factory.assert_called_once_with(mode='test')
            import json
            self.assertEqual(json.loads(response.json()['context_json'])['generation'], provider.last_run)
            replay = self.client.post('/gm/assets/adjust', json=self.payload(), headers=self.headers)
            self.assertEqual(replay.status_code, 409)
            self.assertEqual(provider.calls, 1)

    def test_unknown_mode_rejected_without_generation(self):
        with patch.object(asset_api, 'get_provider') as factory:
            response = self.client.post('/gm/assets/adjust', json={**self.payload(), 'generation_mode': 'paid'}, headers=self.headers)
            self.assertEqual(response.status_code, 422)
            factory.assert_not_called()

    def provider(self, fail=False):
        class Provider:
            calls = 0
            def generate(inner, prompt, output, references):
                inner.calls += 1
                self.assertIn('Remove only the weapon', prompt)
                self.assertEqual(references[0].read_bytes(), self.original)
                if fail: raise RuntimeError('secret provider error')
                Image.new('RGB', (32, 48), 'blue').save(output)
        return Provider()

    def test_new_version_original_unchanged_replay_and_approval(self):
        source = self.source()
        provider = self.provider()
        with patch.object(asset_api, 'get_provider', return_value=provider):
            first = self.client.post('/gm/assets/adjust', json=self.payload(), headers=self.headers)
            self.assertEqual(first.status_code, 200, first.text)
            job = first.json()
            self.assertEqual(job['status'], 'awaiting_approval')
            self.assertEqual(self.client.post('/gm/assets/adjust', json=self.payload(), headers=self.headers).json()['id'], job['id'])
            self.assertEqual(provider.calls, 1)
            changed = {**self.payload(), 'instruction': 'Different edit'}
            self.assertEqual(self.client.post('/gm/assets/adjust', json=changed, headers=self.headers).status_code, 409)
        self.assertEqual(source.read_bytes(), self.original)
        before = self.client.get(f"/gm/assets/{job['id']}/base-preview", headers=self.headers)
        self.assertEqual(before.content, self.original)
        self.assertEqual(self.client.get(f"/gm/assets/{job['id']}/base-preview").status_code, 403)
        self.assertEqual(self.client.get(f"/gm/assets/{job['id']}/preview", headers=self.headers).status_code, 200)
        approved = self.client.post(f"/gm/assets/{job['id']}/approve", json={'image_path':job['image_path']}, headers=self.headers)
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(source.read_bytes(), self.original)

    def test_invalid_paths_blank_and_player_never_generate(self):
        self.source()
        with patch.object(asset_api, 'get_provider') as provider:
            self.assertEqual(self.client.post('/gm/assets/adjust', json=self.payload()).status_code, 403)
            self.assertEqual(self.client.post('/gm/assets/adjust', json={**self.payload(), 'instruction':'  '}, headers=self.headers).status_code, 422)
            for path in ('zz_media/../../private.png', 'https://example.com/image.png', 'draft:../../outside.png'):
                self.assertEqual(self.client.post('/gm/assets/adjust', json={**self.payload(), 'image_path':path}, headers=self.headers).status_code, 409)
            provider.return_value.generate.assert_not_called()

    def test_failed_edit_preserves_parent_and_original_and_sanitizes_error(self):
        source = self.source()
        asset_generation.update_job_status(self.job['id'], 'approved', image_path='zz_media/original.png')
        parent = asset_generation.get_job(self.job['id'])
        with patch.object(asset_api, 'get_provider', return_value=self.provider(fail=True)):
            response = self.client.post('/gm/assets/adjust', json={**self.payload(),'parent_job_id':self.job['id']}, headers=self.headers)
        self.assertEqual(response.json()['status'], 'failed')
        self.assertNotIn('secret', response.text)
        self.assertEqual(asset_generation.get_job(self.job['id']), parent)
        self.assertEqual(source.read_bytes(), self.original)

    def test_stale_parent_and_parallel_generation_blocked(self):
        self.source()
        with patch.object(asset_api, 'get_provider') as provider:
            response = self.client.post('/gm/assets/adjust', json={**self.payload(),'parent_job_id':self.job['id']}, headers=self.headers)
            self.assertEqual(response.status_code, 409)
            with asset_api._generation_lock:
                self.assertEqual(self.client.post('/gm/assets/adjust', json=self.payload(), headers=self.headers).status_code, 409)
            provider.return_value.generate.assert_not_called()

    def test_safe_provider_diagnostic_is_persisted_without_changing_source(self):
        from app.cloudflare_provider import ImageProviderError
        source = self.source()
        with patch.object(asset_api, 'get_provider') as provider:
            provider.return_value.generate.side_effect = ImageProviderError('Workers AI não respondeu dentro do tempo limite.')
            response = self.client.post('/gm/assets/adjust', json=self.payload(), headers=self.headers)
        self.assertEqual(response.json()['status'], 'failed')
        self.assertIn('tempo limite', response.json()['error'])
        self.assertEqual(source.read_bytes(), self.original)

    def test_item_library_edit_stays_in_item_category(self):
        self.source()
        with patch.object(asset_api, 'get_provider', return_value=self.provider()):
            response = self.client.post('/gm/assets/adjust', json={**self.payload(), 'category':'items'}, headers=self.headers)
        job = response.json()
        self.assertEqual(job['asset_type'], 'item_art')
        self.assertEqual(self.client.post(f"/gm/assets/{job['id']}/approve", json={'image_path':job['image_path']}, headers=self.headers).status_code, 200)
        with closing(sqlite3.connect(self.db)) as conn:
            self.assertEqual(conn.execute('SELECT category FROM session_workspace_icons').fetchone()[0], 'items')
