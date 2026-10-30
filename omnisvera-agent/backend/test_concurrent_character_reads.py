from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import TestCase
from unittest.mock import patch

from app.concurrent_reads import ConcurrentReads
from app import main


class ConcurrentCharacterReadsTests(TestCase):
    def test_existing_item_reads_do_not_reinitialize_or_rewrite_workspace(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from app import session_workspace
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / 'read.sqlite3'
            self.assertIsNone(session_workspace.get_session_item(database, 99))
            with patch.object(session_workspace, 'init_session_workspace', side_effect=AssertionError('read rewrote workspace')):
                self.assertIsNone(session_workspace.get_session_item(database, 99))
                self.assertIsNone(session_workspace.get_session_item_by_path(database, 'session-item:99'))

    def test_presentation_cache_expires_and_default_reads_remain_fresh(self):
        reads = ConcurrentReads()
        calls = []
        def load():
            calls.append(1)
            return len(calls)
        with patch('app.concurrent_reads.monotonic', return_value=10):
            self.assertEqual(reads.run('art', load, ttl=3), 1)
            self.assertEqual(reads.run('art', load, ttl=3), 1)
            self.assertEqual(reads.run('state', load), 2)
            self.assertEqual(reads.run('state', load), 3)
        with patch('app.concurrent_reads.monotonic', return_value=14):
            self.assertEqual(reads.run('art', load, ttl=3), 4)

    def test_action_catalog_returns_copies_and_scopes_cache_by_profile(self):
        with patch.object(main, '_action_catalog_reads', ConcurrentReads()), patch.object(
            main, '_load_session_action_catalog', return_value=[{'id': 'spell', 'name': 'Original'}]
        ) as load:
            first = main._session_action_catalog('raziel')
            first[0]['name'] = 'Changed'
            self.assertEqual(main._session_action_catalog('raziel')[0]['name'], 'Original')
            main._session_action_catalog('morthak')
            self.assertEqual(load.call_count, 2)

    def test_overlapping_reads_share_work_but_next_read_is_fresh(self):
        reads = ConcurrentReads()
        entered, release = Event(), Event()
        calls = []

        def load():
            calls.append(1)
            entered.set()
            self.assertTrue(release.wait(3))
            return len(calls)

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(reads.run, 'db', load)
            self.assertTrue(entered.wait(3))
            follower = reads._pending['db']
            follower_entered = Event()
            original_result = follower.result

            def wait_for_shared_result():
                follower_entered.set()
                return original_result()

            with patch.object(follower, 'result', side_effect=wait_for_shared_result):
                second = pool.submit(reads.run, 'db', load)
                self.assertTrue(follower_entered.wait(3))
                release.set()
                self.assertEqual(first.result(), second.result())
        self.assertEqual(reads.run('db', load), 2)
        self.assertEqual(reads._pending, {})

    def test_failed_read_does_not_poison_next_request(self):
        reads = ConcurrentReads()
        with self.assertRaises(ValueError):
            reads.run('db', lambda: (_ for _ in ()).throw(ValueError('offline')))
        self.assertEqual(reads.run('db', lambda: 'recovered'), 'recovered')

    def test_shared_summaries_are_copied_before_access_filtering(self):
        records = [{'id': 'raziel', 'resources': [{'key': 'blood', 'current': 7}]}]
        with patch.object(main._character_summary_reads, 'run', return_value=records):
            public = main.playable_characters(main.AccessContext(mode='player', profile_id='morthak'))
            owner = main.playable_characters(main.AccessContext(mode='player', profile_id='raziel'))
        self.assertEqual(public[0]['resources'], [])
        self.assertEqual(owner[0]['resources'][0]['current'], 7)
        self.assertNotIn('access_level', records[0])
