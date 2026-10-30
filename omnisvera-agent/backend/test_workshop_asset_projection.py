"""Native image review is projected without rewriting either database."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from app import ai_workshop as workshop
from app.ai_workshop_routes import build_workshop_router


class WorkshopAssetProjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / 'workshop.sqlite3'
        self.campaign = self.root / 'campaign.sqlite3'
        with closing(sqlite3.connect(self.campaign)) as db, db:
            db.execute('CREATE TABLE asset_generation_jobs (id INTEGER PRIMARY KEY, '
                       'entity_type TEXT,entity_id TEXT,status TEXT,image_path TEXT,source_hash TEXT)')

        def master(x_test_role: str | None = Header(default=None)):
            if x_test_role != 'gm':
                raise HTTPException(401, 'Private')
        app = FastAPI()
        app.include_router(build_workshop_router(lambda: self.db, lambda: self.campaign, master))
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.headers = {'X-Test-Role': 'gm'}

    def seed(self, native_status='ignored', *, entity='dragon', source_hash='b'*16,
             native_path='draft:dragon.png', queue='image'):
        payload = {'sources': [{'path': 'private', 'sha256': 'a'*64}],
                   'entity_type': 'compendium_monster', 'entity_id': 'dragon',
                   'source_hash': 'b'*16}
        job = workshop.enqueue_job(self.db, queue=queue, entity_type='compendium_monster',
            entity_id='dragon', revision='v1', purpose='monster_art',
            request_id='fixture-asset-projection-' + queue, payload=payload)['job']
        output = {'asset_job_id': 66, 'image_path': 'draft:dragon.png',
                  'draft': 'PRIVATE GENERATED DRAFT'}
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE ai_workshop_jobs SET status='awaiting_approval',"
                       "external_ref='asset_generation_jobs:66',output_json=? WHERE id=?",
                       (json.dumps(output), job['id']))
        with closing(sqlite3.connect(self.campaign)) as db, db:
            db.execute('INSERT INTO asset_generation_jobs VALUES(66,?,?,?,?,?)',
                       ('compendium_monster', entity, native_status, native_path, source_hash))
        return job['id']

    def detail(self, job_id):
        response = self.client.get(f'/gm/ai-workshop/jobs/{job_id}', headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_ignored_image_leaves_review_count_and_projects_cancelled_read_only(self):
        job_id = self.seed()
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.db, self.campaign)]
        detail = self.detail(job_id)
        overview = self.client.get('/gm/ai-workshop', headers=self.headers).json()
        self.assertEqual(detail['status'], 'cancelled')
        self.assertEqual(detail['asset_review_status'], 'ignored')
        self.assertEqual(overview['counts']['image'].get('awaiting_approval', 0), 0)
        self.assertEqual(overview['counts']['image']['cancelled'], 1)
        self.assertEqual(overview['jobs'][0]['status'], 'cancelled')
        self.assertNotIn('PRIVATE GENERATED DRAFT', json.dumps(overview))
        self.assertEqual(before, [hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.db, self.campaign)])
        self.assertEqual(workshop.get_job(self.db, job_id)['status'], 'awaiting_approval')

    def test_native_approved_same_draft_projects_completed(self):
        drafts = self.root / 'asset_drafts'
        drafts.mkdir()
        content = b'original-image'
        (drafts / 'dragon.png').write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()[:24]
        job_id = self.seed('approved', native_path=f'zz_media/ui/icons/approved/asset_66_{digest}.png')
        detail = self.detail(job_id)
        self.assertEqual(detail['status'], 'completed')
        self.assertEqual(detail['asset_review_status'], 'approved')
        self.assertIn('aprovada', detail['preview']['draft'])

    def test_new_generation_cannot_mark_old_draft_as_completed(self):
        drafts = self.root / 'asset_drafts'
        drafts.mkdir()
        (drafts / 'dragon.png').write_bytes(b'original-image')
        job_id = self.seed('approved', native_path='zz_media/ui/icons/approved/asset_66_' + 'f'*24 + '.png')
        detail = self.detail(job_id)
        self.assertEqual(detail['status'], 'needs_review')
        self.assertEqual(detail['asset_review_status'], 'superseded')
        self.assertNotIn('asset_job_id', detail['preview'])

    def test_pending_same_draft_remains_reviewable(self):
        detail = self.detail(self.seed('awaiting_approval'))
        self.assertEqual(detail['status'], 'awaiting_approval')
        self.assertEqual(detail['asset_review_status'], 'awaiting_approval')

    def test_requeued_native_image_does_not_reuse_old_preview(self):
        detail = self.detail(self.seed('queued'))
        self.assertEqual(detail['status'], 'needs_review')
        self.assertEqual(detail['asset_review_status'], 'superseded')
        self.assertNotIn('asset_job_id', detail['preview'])

    def test_initial_native_queue_remains_external_pending(self):
        job_id = self.seed('queued')
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE ai_workshop_jobs SET status='external_pending',output_json='{}' WHERE id=?", (job_id,))
        detail = self.detail(job_id)
        self.assertEqual(detail['status'], 'external_pending')
        self.assertEqual(detail['asset_review_status'], 'queued')

    def test_conflicting_output_id_cannot_borrow_native_review(self):
        job_id = self.seed()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE ai_workshop_jobs SET external_ref='asset_generation_jobs:67' WHERE id=?", (job_id,))
        detail = self.detail(job_id)
        self.assertEqual(detail['status'], 'needs_review')
        self.assertEqual(detail['asset_review_status'], 'unavailable')

    def test_unverifiable_old_approval_is_not_assumed_current(self):
        job_id = self.seed('approved', native_path='zz_media/ui/icons/approved/asset_66_' + 'f'*24 + '.png')
        self.assertEqual(self.detail(job_id)['status'], 'needs_review')

    def test_native_approved_invalid_path_cannot_complete_workshop(self):
        job_id = self.seed('approved')
        self.assertEqual(self.detail(job_id)['status'], 'needs_review')

    def test_other_entity_or_source_cannot_supply_review(self):
        job_id = self.seed(entity='another-dragon')
        self.assertEqual(self.detail(job_id)['status'], 'needs_review')
        with closing(sqlite3.connect(self.campaign)) as db, db:
            db.execute("UPDATE asset_generation_jobs SET entity_id='dragon',source_hash=?", ('c'*16,))
        self.assertEqual(self.detail(job_id)['status'], 'needs_review')
        self.assertNotIn('asset_job_id', self.detail(job_id)['preview'])

    def test_missing_campaign_is_not_created_and_never_assumed_approved(self):
        job_id = self.seed()
        self.campaign.unlink()
        detail = self.detail(job_id)
        self.assertEqual(detail['status'], 'needs_review')
        self.assertEqual(detail['asset_review_status'], 'unavailable')
        self.assertFalse(self.campaign.exists())

    def test_text_with_asset_reference_is_never_projected_as_image(self):
        job_id = self.seed(queue='text')
        detail = self.detail(job_id)
        self.assertEqual(detail['status'], 'awaiting_approval')
        self.assertNotIn('asset_review_status', detail)

    def test_players_and_anonymous_cannot_inspect_projection(self):
        job_id = self.seed()
        for headers in ({}, {'X-Test-Role': 'player'}):
            for route in ('/gm/ai-workshop', f'/gm/ai-workshop/jobs/{job_id}'):
                self.assertEqual(self.client.get(route, headers=headers).status_code, 401)

    def test_unsafe_draft_path_does_not_read_outside_draft_directory(self):
        job_id = self.seed('approved', native_path='zz_media/ui/icons/approved/asset_66_' + 'f'*24 + '.png')
        with closing(sqlite3.connect(self.db)) as db, db:
            output = {'asset_job_id':66,'image_path':'draft:../outside.png'}
            db.execute('UPDATE ai_workshop_jobs SET output_json=? WHERE id=?', (json.dumps(output),job_id))
        self.assertEqual(self.detail(job_id)['asset_review_status'], 'superseded')


if __name__ == '__main__':
    unittest.main()
