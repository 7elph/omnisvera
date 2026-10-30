"""Automation admission and real-asset bridge, using disposable fixtures only."""
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from app import ai_workshop as w


class WorkshopExecutionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.db=self.root/'workshop.sqlite3';self.campaign=self.root/'campaign.sqlite3'
        w.init_workshop(self.db);self.now=datetime(2026,10,26,12,tzinfo=timezone.utc)

    def enqueue(self,identity):
        return w.enqueue_job(self.db,queue='text',entity_type='session',entity_id=identity,
            revision='v1',purpose='fixture',request_id='fixture-'+identity,now=self.now)['job']

    def test_daily_budget_counts_claimed_attempts_and_resets_at_utc_midnight(self):
        w.configure_provider(self.db,queue='text',provider='fixture',configured_limit=1,now=self.now)
        self.enqueue('one');self.enqueue('two')
        first=w.claim_next_job(self.db,queue='text',worker_id='fixture',now=self.now)['job']
        self.assertIsNotNone(first)
        blocked=w.claim_next_job(self.db,queue='text',worker_id='fixture',now=self.now+timedelta(seconds=1))
        self.assertIsNone(blocked['job']);self.assertEqual(blocked['reason'],'provider_daily_budget')
        next_day=w.claim_next_job(self.db,queue='text',worker_id='fixture',now=self.now+timedelta(days=1))
        self.assertIsNotNone(next_day['job'])

    def test_explicit_zero_budget_disables_the_queue(self):
        w.configure_provider(self.db,queue='text',provider='fixture',configured_limit=0,now=self.now)
        self.enqueue('zero')
        result=w.claim_next_job(self.db,queue='text',worker_id='fixture',now=self.now)
        self.assertIsNone(result['job']);self.assertEqual(result['reason'],'provider_daily_budget')

    def test_live_worker_lock_cannot_be_stolen_just_because_it_is_old(self):
        lock = self.root/'worker.lock'
        with patch.object(w, '_pid_alive', return_value=True):
            lock.write_text(json.dumps({'pid': 123, 'created_at': '2020-01-01T00:00:00+00:00'}))
            with self.assertRaises(w.CheckoutLockBusy): w.acquire_checkout_lock(lock, 'second')

    def test_manual_asset_generation_waits_for_existing_heavy_work(self):
        from contextlib import contextmanager
        from fastapi import HTTPException
        from app.asset_api import _admitted_generation
        @contextmanager
        def busy(): yield False
        with patch('scripts.memory_guard.workload_slot', busy), patch('app.asset_api._generate_job') as generate:
            with self.assertRaises(HTTPException) as caught: _admitted_generation(None, 1, 'official')
            self.assertEqual(caught.exception.status_code,409)
            generate.assert_not_called()

    def image_job(self):
        return {'id':1,'entity_type':'compendium_monster','entity_id':'gorgon','revision':'v1',
            'payload_json':{'sources':[{'path':'fixture','sha256':'a'*64}],
            'entity_type':'compendium_monster','entity_id':'gorgon','asset_type':'monster_art',
            'style_version':'omnisvera.monster.v1','source_hash':'b'*16}}

    def test_real_image_bridge_returns_a_private_draft_and_retry_never_generates_again(self):
        from app.workshop_execution import ImageGenerationAdapter
        from app.asset_generation import init_asset_generation
        init_asset_generation(self.campaign)
        settings=SimpleNamespace(database_path=self.campaign,vault_path=self.root/'vault')
        def generate(settings,identity,mode):
            with closing(sqlite3.connect(self.campaign)) as db,db:
                db.execute("UPDATE asset_generation_jobs SET status='awaiting_approval',image_path='draft:fixture.png' WHERE id=?",(identity,))
            return {'id':identity,'status':'awaiting_approval','image_path':'draft:fixture.png'}
        with patch('app.workshop_execution.generate_draft',side_effect=generate) as external:
            adapter=ImageGenerationAdapter(settings)
            first=adapter(self.image_job());second=adapter(self.image_job())
        external.assert_called_once();self.assertEqual(first['status'],'awaiting_approval')
        self.assertEqual(first['output']['asset_job_id'],second['output']['asset_job_id'])
        self.assertEqual(first['output']['image_path'],'draft:fixture.png')
        with closing(sqlite3.connect(self.campaign)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM asset_generation_jobs').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT status FROM asset_generation_jobs').fetchone()[0],'awaiting_approval')

    def test_in_progress_image_is_ambiguous_and_never_retried_as_another_generation(self):
        from app.workshop_execution import ImageGenerationAdapter
        from app.ai_workshop_adapters import ImageAssetAdapter,WorkshopAdapterError
        from app.asset_generation import init_asset_generation
        init_asset_generation(self.campaign);ImageAssetAdapter(self.campaign)(self.image_job())
        with closing(sqlite3.connect(self.campaign)) as db,db:db.execute("UPDATE asset_generation_jobs SET status='generating'")
        with patch('app.workshop_execution.generate_draft') as external:
            with self.assertRaises(WorkshopAdapterError) as error:
                ImageGenerationAdapter(SimpleNamespace(database_path=self.campaign))(self.image_job())
        self.assertEqual(error.exception.kind,'timeout_ambiguous');external.assert_not_called()

    def test_config_defaults_do_not_turn_on_external_providers(self):
        from app.workshop_execution import configuration
        with patch.dict('os.environ',{'AI_WORKSHOP_CONFIG_FILE':str(self.root/'missing.json')}):
            result=configuration()
        self.assertFalse(result['enabled']);self.assertFalse(result['image']);self.assertFalse(result['code'])
        self.assertGreaterEqual(result['min_free_ram_mb'],1024)

    def test_uncertain_transcription_used_as_lore_is_parked_for_review_without_a_retry(self):
        from app.workshop_execution import ContextTextAdapter
        context={'kind':'current_party_snapshot','members':[]}
        response={'status':'awaiting_approval','output':{'draft':'## Sugestões\nCrie a torre de Mortax.\n## Perguntas\nO que significa “Mortax”? Pode ser erro de ASR.'}}
        result=ContextTextAdapter(lambda job:response,context_loader=lambda:context)({'payload_json':{}})
        self.assertEqual(result['status'],'needs_review')
        self.assertIn('uncertain_names_used_as_lore',result['output']['quality_notes'])

    def test_roster_enrichment_never_rewrites_original_job_or_forwards_private_roster_fields(self):
        from app.workshop_execution import ContextTextAdapter
        original={'payload_json':{'facts':['historical source']}}
        context={'kind':'current_party_snapshot','members':[{'id':'raziel','role':'party_member'}]}
        seen=[]
        result=ContextTextAdapter(lambda job:(seen.append(job) or {'status':'awaiting_approval','output':{'draft':'Fato explícito.'}}),context_loader=lambda:context)(original)
        self.assertEqual(original['payload_json']['facts'],['historical source'])
        self.assertEqual(seen[0]['payload_json']['facts'][-1],context)
        self.assertIn('party_context_sha256',result['output'])

    def test_generated_blocks_must_fit_native_scene_elements_without_truncation(self):
        from app.workshop_execution import quality_notes
        self.assertIn('oversized_block',quality_notes('x'*50001))

    def test_repeated_generated_sentences_are_parked_without_modifying_the_output(self):
        from app.workshop_execution import ContextTextAdapter
        text = ('Fonte privada da fixture. Sugestão de preparação, sem execução. ' * 75)
        result = ContextTextAdapter(lambda job: {'status':'awaiting_approval','output':{'draft':text}},context_loader=lambda:{'members':[]})({'payload_json':{}})
        self.assertEqual(result['status'],'needs_review')
        self.assertIn('repeated_content',result['output']['quality_notes'])
        self.assertEqual(result['output']['draft'],text)

    def test_normal_short_refrains_do_not_count_as_repeated_generated_content(self):
        from app.workshop_execution import quality_notes
        text = 'Fatos: Nimalis. Sugestão: loja. Dúvidas: nenhuma. Fatos: guardas. Sugestão: conversa. Dúvidas: entrega.'
        self.assertNotIn('repeated_content',quality_notes(text))
