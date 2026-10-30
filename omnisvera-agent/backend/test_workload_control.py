"""One heavy workload at a time; owned test trees cannot outlive their controller."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import Mock, patch

from scripts import memory_guard as guard


class WorkloadControlTests(TestCase):
    def test_nested_call_reuses_slot_but_other_thread_is_blocked(self):
        from concurrent.futures import ThreadPoolExecutor
        with TemporaryDirectory() as folder, patch.object(guard, 'state_directory', return_value=Path(folder)):
            with guard.workload_slot() as first:
                self.assertTrue(first)
                with guard.workload_slot() as nested:
                    self.assertTrue(nested)
                def competitor():
                    with guard.workload_slot() as acquired:
                        return acquired
                with ThreadPoolExecutor(max_workers=1) as pool:
                    self.assertFalse(pool.submit(competitor).result(timeout=3))
            with guard.workload_slot() as released:
                self.assertTrue(released)

    def test_exception_releases_slot(self):
        with TemporaryDirectory() as folder, patch.object(guard, 'state_directory', return_value=Path(folder)):
            with self.assertRaisesRegex(ValueError, 'fixture'):
                with guard.workload_slot():
                    raise ValueError('fixture')
            with guard.workload_slot() as acquired:
                self.assertTrue(acquired)

    def test_slot_blocks_another_process_and_releases_without_resident_worker(self):
        with TemporaryDirectory() as folder, patch.object(guard, 'state_directory', return_value=Path(folder)):
            code = ("from pathlib import Path;from scripts.memory_guard import instance_lock;"
                    "import sys;\nwith instance_lock(Path(sys.argv[1])) as acquired: print(int(acquired))")
            command = [sys.executable, '-c', code, str(Path(folder)/'workload.lock')]
            def attempt():
                return subprocess.run(command, cwd=Path(__file__).parent, capture_output=True,
                                      text=True, timeout=5, check=True).stdout.strip()
            with guard.workload_slot():
                self.assertEqual('0', attempt())
            self.assertEqual('1', attempt())

    def test_busy_workshop_does_not_claim_or_call_an_adapter(self):
        from app import ai_workshop
        from contextlib import contextmanager
        @contextmanager
        def busy():
            yield False
        adapter = Mock()
        with patch.object(guard, 'workload_slot', busy), patch.object(ai_workshop, 'claim_next_job') as claim:
            result = ai_workshop.tick(Path('unused.sqlite3'), {'text': adapter}, min_free_ram_mb=0)
        self.assertEqual('resource_busy', result['reason'])
        claim.assert_not_called(); adapter.assert_not_called()

    def test_busy_rehearsal_does_not_backup_or_spawn(self):
        from scripts import run_sheet_test as runner
        from contextlib import contextmanager
        @contextmanager
        def busy():
            yield False
        with patch.object(runner, 'workload_slot', busy, create=True), \
             patch.object(runner, 'backup_readonly') as backup, \
             patch.object(runner.subprocess, 'Popen') as spawn:
            self.assertEqual(2, runner.main())
        backup.assert_not_called(); spawn.assert_not_called()


@skipUnless(os.name == 'nt', 'Windows job containment')
class WindowsOwnedTreeTests(TestCase):
    def test_real_venv_worker_joins_named_group_before_work(self):
        import json
        with TemporaryDirectory() as folder:
            marker = Path(folder)/'worker.json'
            code = ("from scripts.memory_guard import join_owned_job_from_env;"
                    "join_owned_job_from_env();import json,os,time;from pathlib import Path;"
                    "Path(__import__('sys').argv[1]).write_text(json.dumps({'pid':os.getpid()}));time.sleep(60)")
            group = guard.OwnedProcessGroup()
            env = {k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP'}}
            env['OMNISVERA_QA_JOB_NAME'] = group.name
            worker = subprocess.Popen([sys.executable, '-c', code, str(marker)], env=env,
                cwd=Path(__file__).parent, creationflags=subprocess.CREATE_NO_WINDOW)
            identity = None
            native = guard.WindowsMetrics()
            try:
                group.track(worker)
                import time
                deadline = time.monotonic()+5
                while not marker.exists() and time.monotonic()<deadline:
                    time.sleep(.05)
                self.assertTrue(marker.exists())
                identity = native.identity(json.loads(marker.read_text())['pid'])
                self.assertIsNotNone(identity)
                group.close();worker.wait(timeout=3)
                deadline = time.monotonic()+3
                while native.identity(identity['pid']) and time.monotonic()<deadline:time.sleep(.05)
                self.assertIsNone(native.identity(identity['pid']))
            finally:
                group.close()
                if worker.poll() is None:worker.kill()
                worker.wait(timeout=3)

    def test_node_cannot_enter_main_without_parent_gate(self):
        import shutil
        node = shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        preload = Path(__file__).parents[1]/'frontend/tests/owned-ui-preload.cjs'
        result = subprocess.run([node, '--require', str(preload), '-e', "console.log('ENTERED')"],
                                input='', capture_output=True, text=True, timeout=5)
        self.assertEqual(2, result.returncode)
        self.assertNotIn('ENTERED', result.stdout)
        group = guard.OwnedProcessGroup()
        child = subprocess.Popen([node, '--require', str(preload), '-e', "console.log('ENTERED')"],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            group.track(child)
            out, _ = child.communicate(input='1', timeout=5)
            self.assertEqual(0, child.returncode)
            self.assertEqual('ENTERED', out.strip())
        finally:
            group.close()
            if child.poll() is None:child.kill()
            child.wait(timeout=3)

    def test_close_terminates_only_the_worker_and_its_disposable_descendant(self):
        import json
        with TemporaryDirectory() as folder:
            marker = Path(folder)/'child.json'
            code = ("import subprocess,sys,time,json;from pathlib import Path;"
                    "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
                    "Path(sys.argv[1]).write_text(json.dumps({'pid':child.pid}));time.sleep(60)")
            # The child waits for a private gate before spawning, proving it is
            # assigned before this disposable descendant exists.
            gated = "import sys;sys.stdin.buffer.read(1);" + code
            worker = subprocess.Popen([sys._base_executable, '-c', gated, str(marker)],
                                      stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            native = guard.WindowsMetrics()
            child_identity = None
            group = guard.OwnedProcessGroup()
            try:
                group.track(worker)
                worker.stdin.write(b'1'); worker.stdin.close()
                import time
                deadline = time.monotonic()+5
                while not marker.exists() and time.monotonic()<deadline:
                    time.sleep(.05)
                self.assertTrue(marker.exists())
                child_identity = native.identity(json.loads(marker.read_text())['pid'])
                self.assertIsNotNone(child_identity)
                group.close()
                worker.wait(timeout=3)
                deadline = time.monotonic()+3
                while native.identity(child_identity['pid']) and time.monotonic()<deadline:
                    time.sleep(.05)
                self.assertIsNone(native.identity(child_identity['pid']))
                self.assertIsNotNone(native.identity(os.getpid()), 'controller must remain alive')
            finally:
                group.close()
                if worker.poll() is None: worker.kill()
                worker.wait(timeout=3)
                if child_identity and native.identity(child_identity['pid']):
                    receipt = dict(schema_version=1, source='native_sheet_runner', role='ui',
                        **child_identity, launcher_pid=os.getpid(),
                        launcher_created_ticks=native.identity(os.getpid())['created_ticks'])
                    native.stop_if_matches(receipt)
