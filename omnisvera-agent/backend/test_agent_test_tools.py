"""AI transport is isolated, idempotent, bounded and does not execute arbitrary code."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest import IsolatedAsyncioTestCase, skipUnless
from unittest.mock import patch
import importlib.util
from scripts.agent_test_jobs import TestJobs


class FakeProcess:
    pid = 123456
    def __init__(self): self.returncode = None
    def poll(self): return self.returncode
    def wait(self, timeout=None): return self.returncode


class AgentTestJobsTests(TestCase):
    def setUp(self):
        runtime=patch('scripts.agent_test_jobs.backend_runner_python',return_value=Path('fixed-native-test-python'))
        runtime.start();self.addCleanup(runtime.stop)
        folder=TemporaryDirectory();self.addCleanup(folder.cleanup);self.root=Path(folder.name)/'jobs'
        self.process=FakeProcess();self.spawns=[];self.stops=[]
        self.jobs=TestJobs(self.root,spawn=self.spawn,stop=self.stop,watch=False)
        self.addCleanup(self.jobs.close)
    def spawn(self, command, **kwargs):
        self.spawns.append((command,kwargs));return self.process
    def stop(self, process):
        self.stops.append(process);process.returncode=-1
    def start(self, **extra):
        return self.jobs.start(request_id='agent-test-0001',actors=['raziel'],**extra)
    def finish(self, run, *, fails=0, exit_code=0):
        output=self.root/run['run_id']/'evidence';output.mkdir()
        report={'schema_version':1,'kind':'sheet_test_evidence','scenario_counts':{'PASS':1,'FAIL':fails},
                'characters':{},'scenarios':[{'status':'PASS','scenario_id':'one'}]+[
                    {'status':'FAIL','scenario_id':'failed-'+str(i)} for i in range(fails)],'all_actions_certified':False}
        (output/'sheet-test-report.json').write_text(json.dumps(report),encoding='utf-8')
        self.process.returncode=exit_code
    def test_retry_returns_same_run_and_changed_input_conflicts(self):
        first=self.start();second=self.start()
        self.assertEqual(first['run_id'],second['run_id']);self.assertEqual(1,len(self.spawns))
        with self.assertRaisesRegex(ValueError,'different'):self.jobs.start(request_id='agent-test-0001',actors=['morthak'])
    def test_busy_rejects_another_job_without_duplicating_process(self):
        self.start()
        with self.assertRaisesRegex(RuntimeError,'BUSY'):self.jobs.start(request_id='another-test-01',actors=['morthak'])
        self.assertEqual(1,len(self.spawns))
    def test_fixed_command_has_no_live_token_or_caller_source_path(self):
        self.start()
        command,kwargs=self.spawns[0]
        self.assertIn('--output-dir',command);self.assertNotIn('--source-db',command)
        self.assertNotIn('--keep-server',command);self.assertNotIn('shell',kwargs)
        self.assertNotIn('access_tokens',str(command))

    def test_ui_is_explicit_idempotent_input_and_fixed_script_flag(self):
        run=self.start(ui=True)
        self.assertTrue(run['ui'])
        self.assertIn('--ui',self.spawns[0][0])
        self.assertEqual(run['run_id'],self.start(ui=True)['run_id'])
        with self.assertRaisesRegex(ValueError,'different'):self.start()

    def test_missing_requested_ui_evidence_is_not_a_pass(self):
        run=self.start(ui=True);self.finish(run)
        self.assertEqual('ERROR',self.jobs.status(run['run_id'])['state'])

    def test_memory_gate_failure_is_reported_as_resource_unavailable_not_harness_error(self):
        run=self.start(ui=True)
        folder=self.root/run['run_id']
        (folder/'evidence').mkdir()
        (folder/'evidence/progress.json').write_text(json.dumps({'phase':'waiting_memory','current':'minimum_1024_mb'}),encoding='utf-8')
        (folder/'runner.private.log').write_text('MEMORY_UNAVAILABLE: rehearsal not started; no source database or service changed\n',encoding='utf-8')
        self.process.returncode=2
        result=self.jobs.status(run['run_id'])
        self.assertEqual('INCONCLUSIVE',result['verdict'])
        self.assertIn('MEMORY_UNAVAILABLE',result['error'])
        self.assertFalse(result['certification_ready'])

    def test_exit_two_without_memory_evidence_remains_a_harness_error(self):
        run=self.start(ui=True);self.process.returncode=2
        self.assertIn('HARNESS_ERROR',self.jobs.status(run['run_id'])['error'])

    def test_existing_report_cannot_be_hidden_by_a_stale_memory_marker(self):
        run=self.start(ui=True);self.finish(run,fails=1,exit_code=2)
        folder=self.root/run['run_id']
        (folder/'evidence/progress.json').write_text(json.dumps({'phase':'waiting_memory'}),encoding='utf-8')
        (folder/'runner.private.log').write_text('MEMORY_UNAVAILABLE: rehearsal not started; stale marker\n',encoding='utf-8')
        self.assertIn('HARNESS_ERROR',self.jobs.status(run['run_id'])['error'])

    def test_ui_failure_is_not_hidden_by_green_api_scenarios(self):
        run=self.start(ui=True);self.finish(run,exit_code=1)
        file=self.root/run['run_id']/'evidence'/'sheet-test-report.json'
        report=json.loads(file.read_text(encoding='utf-8'));report['ui_smoke']={'status':'FAIL'}
        file.write_text(json.dumps(report),encoding='utf-8')
        result=self.jobs.status(run['run_id'])
        self.assertEqual('COMPLETED',result['state']);self.assertEqual('FAIL',result['verdict'])
    def test_completed_with_failures_is_a_result_not_infrastructure_error(self):
        run=self.start();self.finish(run,fails=1,exit_code=1)
        status=self.jobs.status(run['run_id'])
        self.assertEqual('COMPLETED',status['state']);self.assertEqual('FAIL',status['verdict'])
        self.assertEqual(1,status['report']['scenario_counts']['FAIL'])
    def test_missing_report_is_error_not_pass(self):
        run=self.start();self.process.returncode=0
        status=self.jobs.status(run['run_id'])
        self.assertEqual('ERROR',status['state']);self.assertEqual('INCONCLUSIVE',status['verdict'])
    def test_traversal_invalid_actor_and_empty_list_rejected_before_launch(self):
        for actors in ([],['unknown']):
            with self.assertRaises(ValueError):self.jobs.start(request_id='invalid-input-1',actors=actors)
        with self.assertRaises(ValueError):self.jobs.status('../access_tokens.json')
        self.assertEqual([],self.spawns)
    def test_disconnect_cancels_only_process_owned_by_this_server(self):
        run=self.start();self.jobs.close()
        self.assertEqual([self.process],self.stops)
        saved=json.loads((self.root/run['run_id']/'job.json').read_text(encoding='utf-8'))
        self.assertEqual('CANCELLED',saved['state'])
    def test_two_server_instances_cannot_claim_same_job_directory(self):
        with self.assertRaisesRegex(RuntimeError,'BUSY'):
            TestJobs(self.root,watch=False)

    def test_finished_receipt_survives_server_restart_without_reexecution(self):
        run=self.start();self.finish(run);self.jobs.status(run['run_id']);self.jobs.close()
        next_server=TestJobs(self.root,spawn=self.spawn,stop=self.stop,watch=False)
        self.addCleanup(next_server.close)
        recovered=next_server.start(request_id='agent-test-0001',actors=['raziel'])
        self.assertEqual(run['run_id'],recovered['run_id']);self.assertEqual('COMPLETED',recovered['state'])
        self.assertEqual(1,len(self.spawns))

    def test_timeout_stops_only_owned_process_and_is_inconclusive(self):
        now=[0.0];self.jobs._clock=lambda:now[0]
        run=self.start();now[0]=1201.0
        status=self.jobs.status(run['run_id'])
        self.assertEqual('ERROR',status['state']);self.assertEqual('INCONCLUSIVE',status['verdict'])
        self.assertEqual([self.process],self.stops)

    def test_report_exit_code_mismatch_cannot_be_declared_pass(self):
        run=self.start();self.finish(run,fails=1,exit_code=0)
        self.assertEqual('ERROR',self.jobs.status(run['run_id'])['state'])

    def test_empty_scenarios_and_code_as_input_are_not_supported(self):
        for scenarios in ([],[''],['line\nbreak']):
            with self.assertRaises(ValueError):self.start(scenarios=scenarios)
        with self.assertRaises(TypeError):self.start(source_db='operational.sqlite3')
        self.assertEqual([],self.spawns)

    def test_report_counts_must_match_actual_scenarios(self):
        run=self.start();self.finish(run)
        file=self.root/run['run_id']/'evidence'/'sheet-test-report.json'
        report=json.loads(file.read_text(encoding='utf-8'));report['scenario_counts']={'PASS':99}
        file.write_text(json.dumps(report),encoding='utf-8')
        self.assertEqual('ERROR',self.jobs.status(run['run_id'])['state'])

    def test_transport_pass_is_separate_from_sheet_certification(self):
        run=self.start();self.finish(run)
        result=self.jobs.status(run['run_id'])
        self.assertEqual('PASS',result['verdict'])
        self.assertFalse(result['certification_ready'])


@skipUnless(importlib.util.find_spec('mcp'), 'MCP observer dependency unavailable')
class AgentMCPContractTests(IsolatedAsyncioTestCase):
    async def test_tools_have_input_and_structured_output_schemas(self):
        from scripts.companion_test_mcp import create_server
        server=create_server()
        tools=await server.list_tools()
        self.assertEqual({'companion_test_capabilities','companion_test_start','companion_test_status'},{t.name for t in tools})
        for tool in tools:
            self.assertIsNotNone(tool.outputSchema,tool.name)
        start=next(t for t in tools if t.name=='companion_test_start')
        self.assertEqual(1,start.inputSchema['properties']['actors']['minItems'])
        self.assertNotIn('source_db',start.inputSchema['properties'])
        self.assertEqual(['RUNNING','COMPLETED','ERROR','CANCELLED','INTERRUPTED'],start.outputSchema['properties']['state']['enum'])

