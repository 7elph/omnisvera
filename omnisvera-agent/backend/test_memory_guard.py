"""Resource automation is local, bounded and never guesses process ownership."""
import json
import io
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import Mock, patch

from scripts import memory_guard as guard


class MemoryGuardTests(TestCase):
    def test_low_and_unknown_memory_never_admit_work(self):
        for value in (None, 0, 1023):
            self.assertFalse(guard.memory_ready({'free_ram_mb': value}, 1024))
        self.assertTrue(guard.memory_ready({'free_ram_mb': 1024}, 1024))

    def test_wait_is_bounded_and_reads_actual_memory_not_state_file(self):
        now = [0]
        def sleep(seconds): now[0] += seconds
        read = Mock(return_value={'free_ram_mb': 50})
        self.assertFalse(guard.wait_for_memory(timeout=10, read=read, sleep=sleep,
                                             clock=lambda: now[0]))
        self.assertEqual(10, now[0])
        self.assertLessEqual(read.call_count, 3)
        read = Mock(side_effect=[{'free_ram_mb': 50}, {'free_ram_mb': 2048}])
        self.assertTrue(guard.wait_for_memory(timeout=10, read=read, sleep=sleep,
                                            clock=lambda: now[0]))

    def test_wait_unknown_fails_closed_and_zero_timeout_does_not_sleep(self):
        sleep = Mock()
        self.assertFalse(guard.wait_for_memory(timeout=0, read=lambda: {}, sleep=sleep))
        sleep.assert_not_called()

    def test_one_instance_per_state_directory_and_release_on_close(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'guard.lock'
            with guard.instance_lock(path) as acquired:
                self.assertTrue(acquired)
                with guard.instance_lock(path) as duplicate:
                    self.assertFalse(duplicate)
            with guard.instance_lock(path) as acquired:
                self.assertTrue(acquired)

    def test_monitor_state_is_bounded_private_and_has_no_prompt(self):
        with TemporaryDirectory() as folder:
            previous = {'free_ram_mb': 500, 'committed_mb': 12000, 'anything_private': 'SECRET'}
            sample = {'free_ram_mb': 300, 'committed_mb': 12200, 'total_ram_mb': 8000}
            state = guard.make_state(sample, previous, [], [], min_free_mb=1024)
            self.assertEqual(-200, state['delta_free_mb'])
            self.assertEqual('waiting_for_memory', state['status'])
            self.assertNotIn('SECRET', json.dumps(state))
            path = Path(folder) / 'state.json'
            guard.write_state(path, state)
            self.assertEqual(state, guard.read_json(path))
            self.assertLess(path.stat().st_size, 16000)


class OrphanSafetyTests(TestCase):
    def setUp(self):
        folder = TemporaryDirectory(); self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.job = self.root / ('test-' + 'a' * 32); self.job.mkdir()
        self.receipts = self.job / 'memory-owners'; self.receipts.mkdir()
        self.record = {'schema_version': 1, 'run_id': self.job.name,
                       'state': 'COMPLETED', 'created_at': 100, 'finished_at': 200}
        self.receipt = {'schema_version': 1, 'source': 'native_sheet_runner',
                        'run_id': self.job.name, 'role': 'fixture', 'pid': 98765,
                        'created_ticks': 555, 'executable': 'C:/runtime/python.exe',
                        'registered_at': 150, 'launcher_pid': 98766, 'launcher_created_ticks': 777}
        self.native = Mock()
        self.native.identity.return_value = None
        self.native.stop_if_matches.return_value = True
        self.save()

    def save(self):
        (self.job / 'job.json').write_text(json.dumps(self.record), encoding='utf-8')
        (self.receipts / 'owned.json').write_text(json.dumps(self.receipt), encoding='utf-8')

    def clean(self):
        return guard.cleanup_finished_tests(self.root, self.native, now=400)

    def test_verified_terminal_orphan_only_is_eligible(self):
        self.assertEqual([98765], self.clean())
        self.native.stop_if_matches.assert_called_once_with(self.receipt)

    def test_live_job_missing_finish_and_grace_period_are_never_touched(self):
        for patch_values in ({'state': 'RUNNING'}, {'finished_at': None}, {'finished_at': 390}):
            with self.subTest(values=patch_values):
                old = dict(self.record); self.record.update(patch_values); self.save()
                self.assertEqual([], self.clean())
                self.record = old
        self.native.stop_if_matches.assert_not_called()


    def test_alive_or_unreadable_launcher_is_not_an_orphan(self):
        self.native.identity.return_value = {'created_ticks': 777}
        self.assertEqual([], self.clean())
        self.native.identity.side_effect = PermissionError('unknown')
        self.assertEqual([], self.clean())
        self.native.stop_if_matches.assert_not_called()

    def test_pid_reuse_does_not_terminate_the_replacement(self):
        self.native.stop_if_matches.return_value = False
        self.assertEqual([], self.clean())

    def test_protected_executables_invalid_role_source_or_run_never_reach_termination(self):
        for values in ({'executable': 'C:/ChatGPT.exe'}, {'executable': 'C:/opencode.exe'},
                       {'role': 'connector'}, {'source': 'other'}, {'run_id': 'test-other'},
                       {'created_ticks': 0}, {'registered_at': 90}):
            with self.subTest(values=values):
                old = dict(self.receipt); self.receipt.update(values); self.save()
                self.assertEqual([], self.clean()); self.receipt = old
        self.native.stop_if_matches.assert_not_called()

    def test_unregistered_processes_are_not_discovered_or_killed(self):
        (self.receipts / 'owned.json').unlink()
        self.assertEqual([], self.clean())
        self.native.identity.assert_not_called()
        self.native.stop_if_matches.assert_not_called()

    def test_registration_needs_native_temp_job_and_running_receipt(self):
        with patch.object(guard, 'test_job_root', return_value=self.root):
            self.assertFalse(guard.register_owned_process(self.job / 'evidence', 98765, 'fixture'))
            self.record['state'] = 'RUNNING'; self.save()
            with patch.object(guard, 'WindowsMetrics', return_value=self.native):
                self.native.identity.side_effect = lambda pid: {
                    'pid': pid, 'created_ticks': 555, 'executable': 'C:/runtime/python.exe'}
                self.assertTrue(guard.register_owned_process(self.job / 'evidence', 98765, 'fixture'))
        self.assertFalse(guard.register_owned_process(self.root / 'unrelated', 98765, 'fixture'))

    def test_oversized_or_broken_receipt_is_ignored(self):
        for text in ('{bad', 'x' * 20000):
            (self.receipts / 'owned.json').write_text(text, encoding='utf-8')
            self.assertEqual([], self.clean())
        self.native.stop_if_matches.assert_not_called()


class RunnerMemoryAdmissionTests(TestCase):
    def test_low_memory_prevents_backup_and_fixture_spawn(self):
        from scripts import run_sheet_test as runner
        with TemporaryDirectory() as folder:
            with patch.object(runner, 'wait_for_memory', return_value=False, create=True), \
                 patch.object(runner, 'backup_readonly') as backup, \
                 patch.object(runner, 'checked_port', return_value=8871), \
                 patch.object(runner.subprocess, 'Popen', side_effect=AssertionError('must not spawn')), \
                 patch('sys.argv', ['run_sheet_test.py', '--output-dir', str(Path(folder)/'evidence')]), \
                 patch('sys.stdout', new_callable=io.StringIO):
                self.assertEqual(2, runner.main())
                backup.assert_not_called()

    def test_ui_rechecks_memory_before_starting_browser_driver(self):
        from scripts import run_sheet_test as runner
        with TemporaryDirectory() as folder:
            with patch.object(runner, 'wait_for_memory', return_value=False, create=True), \
                 patch.object(runner.shutil, 'which', return_value='node'), \
                 patch.object(runner.subprocess, 'Popen', side_effect=AssertionError('must not spawn')):
                result = runner.run_visual_checks(Path(folder), 8871, ['raziel'])
            self.assertEqual('INCONCLUSIVE', result['status'])
            self.assertIn('memory', result['reason'])


@skipUnless(os.name == 'nt', 'native Windows API')
class WindowsGuardTests(TestCase):
    def test_native_metrics_and_same_handle_stop_only_our_disposable_child(self):
        native = guard.WindowsMetrics()
        self.assertIsInstance(native.memory()['free_ram_mb'], int)
        child = subprocess.Popen([getattr(sys, '_base_executable', sys.executable), '-c', 'import time; time.sleep(30)'],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            info = native.identity(child.pid)
            owner = native.identity(os.getpid())
            receipt = dict(schema_version=1, source='native_sheet_runner', role='fixture',
                           **info, launcher_pid=os.getpid(), launcher_created_ticks=owner['created_ticks'])
            self.assertFalse(native.stop_if_matches({**receipt, 'created_ticks': info['created_ticks'] + 1}))
            self.assertFalse(native.stop_if_matches({**receipt, 'executable': 'C:/different/python.exe'}))
            self.assertIsNone(child.poll())
            self.assertTrue(native.stop_if_matches(receipt))
            self.assertEqual(3, child.wait(timeout=3))
        finally:
            if child.poll() is None: child.terminate()
            child.wait(timeout=3)

    def test_second_monitor_exits_instead_of_creating_another_resident_worker(self):
        with TemporaryDirectory() as folder:
            with guard.instance_lock(Path(folder) / 'guard.lock') as acquired:
                self.assertTrue(acquired)
                reply = subprocess.run([getattr(sys, '_base_executable', sys.executable), str(Path(guard.__file__)), '--watch',
                                        '--state-dir', folder], capture_output=True, timeout=5)
                self.assertEqual(0, reply.returncode, reply.stderr)
