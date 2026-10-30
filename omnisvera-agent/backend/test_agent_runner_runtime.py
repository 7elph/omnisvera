"""Observer MCP SDK and native app rehearsals use separate fixed runtimes."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts import agent_test_jobs
from test_agent_test_tools import FakeProcess


class NativeRunnerRuntimeTests(TestCase):
    def test_fixed_backend_venv_selection_is_platform_specific_without_path_lookup(self):
        with TemporaryDirectory() as directory:
            backend=Path(directory)/'backend'
            for platform,relative in [('win32','Scripts/python.exe'),('linux','bin/python')]:
                expected=backend/'.venv'/relative
                expected.parent.mkdir(parents=True,exist_ok=True);expected.touch()
                with patch.object(agent_test_jobs,'BACKEND',backend), \
                     patch.object(agent_test_jobs.sys,'platform',platform), \
                     patch('shutil.which',side_effect=AssertionError('No PATH fallback')):
                    self.assertEqual(expected,agent_test_jobs.backend_runner_python())

    def test_mcp_command_uses_native_interpreter_not_observer_executable(self):
        with TemporaryDirectory() as directory:
            native=Path(directory)/'backend/.venv/Scripts/python.exe'
            captured=[];process=FakeProcess()
            def spawn(command,**kwargs):captured.append(command);return process
            with patch.object(agent_test_jobs,'backend_runner_python',return_value=native), \
                 patch.object(agent_test_jobs.sys,'executable','observer-sdk-python'):
                jobs=agent_test_jobs.TestJobs(Path(directory)/'jobs',spawn=spawn,
                    stop=lambda child:setattr(child,'returncode',-1),watch=False)
                try:
                    jobs.start(request_id='native-runtime-choice-01',actors=['raziel'])
                finally:jobs.close()
            self.assertEqual(str(native),captured[0][0])
            self.assertNotIn('observer-sdk-python',captured[0])

    def test_missing_native_runtime_is_durable_inconclusive_and_never_spawns(self):
        with TemporaryDirectory() as directory:
            captured=[]
            def spawn(*args,**kwargs):captured.append(args);return FakeProcess()
            jobs=agent_test_jobs.TestJobs(Path(directory)/'jobs',
                spawn=spawn,stop=lambda child:setattr(child,'returncode',-1),watch=False)
            try:
                with patch.object(agent_test_jobs,'BACKEND',Path(directory)/'missing-backend'):
                    first=jobs.start(request_id='native-runtime-missing-01',actors=['raziel'])
                    second=jobs.start(request_id='native-runtime-missing-01',actors=['raziel'])
                self.assertEqual([],captured)
                self.assertEqual(('ERROR','INCONCLUSIVE'),(first['state'],first['verdict']))
                self.assertIn('RUNTIME_UNAVAILABLE',first['error'])
                self.assertIsInstance(first['finished_at'],float)
                self.assertEqual(first['run_id'],second['run_id'])
                saved=json.loads((jobs.root/first['run_id']/'job.json').read_text(encoding='utf-8'))
                self.assertEqual('ERROR',saved['state'])
            finally:jobs.close()
