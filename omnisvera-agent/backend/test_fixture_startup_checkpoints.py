"""Private startup checkpoints diagnose launch failures without exposing host state."""
import io
import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts import cf01_probe, run_sheet_test
from scripts.agent_test_jobs import TestJobs
from test_agent_test_tools import FakeProcess


class StartupCheckpointTests(TestCase):
    def setUp(self):
        contained = patch.object(run_sheet_test, 'OwnedProcessGroup')
        contained.start(); self.addCleanup(contained.stop)
        available = patch.object(run_sheet_test, 'wait_for_memory', return_value=True)
        available.start(); self.addCleanup(available.stop)

    def test_api_scenarios_do_not_inherit_the_host_input(self):
        with TemporaryDirectory() as directory:
            output=Path(directory)/'evidence'
            with patch.object(run_sheet_test, 'backup_readonly'), \
                 patch.object(run_sheet_test, 'checked_port', return_value=8871), \
                 patch.object(run_sheet_test.subprocess, 'Popen',
                     side_effect=[FakeProcess(), RuntimeError('capture-api-only')]) as launch, \
                 patch.object(run_sheet_test, 'stop_owned_server'), \
                 patch('httpx.Client') as client, \
                 patch('sys.argv', ['run_sheet_test.py','--output-dir',str(output)]), \
                 patch('sys.stdout', new_callable=io.StringIO):
                health=client.return_value.__enter__.return_value.get.return_value
                health.status_code=200
                health.json.return_value={'access_mode':'gm','database_path':str(output/'simulation.sqlite3')}
                with self.assertRaisesRegex(RuntimeError, 'capture-api-only'):
                    run_sheet_test.main()
            self.assertEqual(2,launch.call_count)
            self.assertIn('all_actions_simulation.py',str(launch.call_args.args[0]))
            self.assertEqual(subprocess.DEVNULL,launch.call_args.kwargs.get('stdin'),
                             'API scenarios are noninteractive, not MCP protocol readers')

    def test_fixture_server_does_not_inherit_the_mcp_transport_input(self):
        with TemporaryDirectory() as directory:
            output=Path(directory)/'evidence'
            with patch.object(run_sheet_test, 'backup_readonly'), \
                 patch.object(run_sheet_test, 'checked_port', return_value=8871), \
                 patch.object(run_sheet_test.subprocess, 'Popen', side_effect=RuntimeError('capture-only-no-child')) as launch, \
                 patch('sys.argv', ['run_sheet_test.py','--output-dir',str(output)]), \
                 patch('sys.stdout', new_callable=io.StringIO):
                with self.assertRaisesRegex(RuntimeError, 'capture-only-no-child'):
                    run_sheet_test.main()
            self.assertEqual(1, launch.call_count)
            self.assertEqual(subprocess.DEVNULL, launch.call_args.kwargs.get('stdin'),
                             'The fixture must not inherit MCP stdin from a long-lived host')
            self.assertIn('cf01_probe.py', str(launch.call_args.args[0]))

    def test_checkpoint_is_allowlisted_runtime_metadata_not_environment_or_arguments(self):
        stream=io.StringIO()
        process=FakeProcess()
        with patch.dict(os.environ, {'OMNISVERA_MASTER_TOKEN':'DO_NOT_LOG_TOKEN',
                                    'OPENCODE_SERVER_PASSWORD':'DO_NOT_LOG_PASSWORD'}):
            cf01_probe.startup_checkpoint('fixture_spawned', process=process, stream=stream)
        text=stream.getvalue()
        self.assertTrue(text.startswith('FIXTURE_STARTUP='))
        record=json.loads(text.split('=',1)[1])
        self.assertEqual('fixture_spawned', record['stage'])
        self.assertEqual(process.pid, record['child_pid'])
        self.assertIsNone(record['child_exit_code'])
        self.assertEqual({'stage','pid','parent_pid','executable','python_version',
                          'child_pid','child_exit_code'}, set(record))
        self.assertNotIn('DO_NOT_LOG', text)

    def test_unknown_stage_cannot_inject_arbitrary_log_content(self):
        stream=io.StringIO()
        with self.assertRaises(ValueError):
            cf01_probe.startup_checkpoint('secret=user-input', stream=stream)
        self.assertEqual('',stream.getvalue())

    def test_logging_flushes_immediately_and_keeps_dead_child_exit_code(self):
        class Stream(io.StringIO):
            flushed=False
            def flush(self):self.flushed=True
        stream=Stream();process=FakeProcess();process.returncode=7
        cf01_probe.startup_checkpoint('fixture_health_timeout', process=process, stream=stream)
        self.assertTrue(stream.flushed)
        self.assertEqual(7,json.loads(stream.getvalue().split('=',1)[1])['child_exit_code'])

    def test_mcp_launch_logs_to_existing_private_file_not_transport_stdout(self):
        with TemporaryDirectory() as directory:
            process=FakeProcess();captured=[]
            def spawn(command,**kwargs):
                captured.append((command,kwargs));return process
            with patch('sys.stdout',new_callable=io.StringIO) as transport, \
                 patch('scripts.agent_test_jobs.backend_runner_python',return_value=Path('fixed-native-test-python')):
                manager=TestJobs(Path(directory)/'jobs',spawn=spawn,
                    stop=lambda child:setattr(child,'returncode',-1),watch=False)
                try:
                    run=manager.start(request_id='startup-checkpoint-test',actors=['raziel'])
                    content=(manager.root/run['run_id']/'runner.private.log').read_text(encoding='utf-8')
                finally:manager.close()
            self.assertEqual('',transport.getvalue())
            records=[json.loads(line.split('=',1)[1]) for line in content.splitlines()]
            self.assertEqual(['runner_spawn_requested','runner_spawned'],[r['stage'] for r in records])
            self.assertEqual(process.pid,records[-1]['child_pid'])
            self.assertNotIn('env',records[-1])
            self.assertEqual(1,len(captured))
