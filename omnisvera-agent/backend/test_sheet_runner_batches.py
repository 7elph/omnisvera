"""Bounded UI batches and partial evidence must not become certification."""
import json
import io
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

from scripts.agent_test_jobs import TestJobs, capabilities
from scripts.run_sheet_test import run_visual_checks
from test_agent_test_tools import FakeProcess


class BatchJobTests(TestCase):
    def setUp(self):
        runtime=patch('scripts.agent_test_jobs.backend_runner_python',return_value=Path('fixed-native-test-python'))
        runtime.start();self.addCleanup(runtime.stop)
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name) / 'jobs'
        self.process = FakeProcess()
        self.commands = []
        self.now = [0.0]
        self.jobs = TestJobs(self.root, spawn=self.spawn, stop=self.stop,
                             watch=False, clock=lambda: self.now[0])
        self.addCleanup(self.jobs.close)

    def spawn(self, command, **kwargs):
        self.commands.append(command)
        return self.process

    def stop(self, process):
        process.returncode = -1

    def start(self, **kwargs):
        return self.jobs.start(request_id='batch-test-request-01',
                               actors=['vezemir', 'morthak', 'raziel', 'dorn7'], **kwargs)

    def report(self, run, *, valid=True):
        folder = self.root / run['run_id'] / 'evidence'
        folder.mkdir()
        value = {'kind': 'sheet_test_evidence', 'schema_version': 1,
                 'scenario_counts': {'PASS': 1 if valid else 99},
                 'scenarios': [{'scenario_id': 'observed', 'status': 'PASS'}],
                 'characters': {}, 'certification': {'ready': True},
                 'all_actions_certified': True}
        (folder / 'sheet-test-report.json').write_text(json.dumps(value), encoding='utf-8')

    def test_combat_batch_is_allowlisted_and_part_of_idempotent_intent(self):
        self.assertIn('combat', capabilities()['ui_suites'])
        first = self.start(ui=True, ui_suite='combat')
        self.assertEqual('combat', first['ui_suite'])
        self.assertIn('--ui-suite', self.commands[0])
        self.assertEqual(first['run_id'], self.start(ui=True, ui_suite='combat')['run_id'])
        with self.assertRaisesRegex(ValueError, 'different'):
            self.start(ui=True)

    def test_arbitrary_suite_or_suite_without_ui_never_spawns(self):
        for options in ({'ui': True, 'ui_suite': '../arbitrary.py'},
                        {'ui': False, 'ui_suite': 'combat'}):
            with self.assertRaises(ValueError):
                self.start(**options)
        self.assertEqual([], self.commands)

    def test_vampiric_batch_uses_native_job_identity_and_requires_four_actors(self):
        self.assertIn('vampiric',capabilities()['ui_suites'])
        first=self.start(ui=True,ui_suite='vampiric')
        self.assertEqual(first['run_id'],self.start(ui=True,ui_suite='vampiric')['run_id'])
        self.assertEqual('vampiric',self.commands[0][-1])
        with self.assertRaises(ValueError):
            self.jobs.start(request_id='vampiric-bad-actors',actors=['raziel'],ui=True,ui_suite='vampiric')
        with self.assertRaises(ValueError):
            self.start(ui=False,ui_suite='vampiric')
        self.assertEqual(1,len(self.commands))

    def test_necromancy_batch_requires_all_actors_ui_and_keeps_identity(self):
        self.assertIn('necromancy',capabilities()['ui_suites'])
        first=self.start(ui=True,ui_suite='necromancy')
        self.assertEqual(first['run_id'],self.start(ui=True,ui_suite='necromancy')['run_id'])
        self.assertEqual('necromancy',self.commands[0][-1])
        for options in ({'actors':['morthak'],'ui':True},
                        {'actors':['vezemir','morthak','raziel','dorn7'],'ui':False}):
            with self.assertRaises(ValueError):
                self.jobs.start(request_id='necro-invalid-options',ui_suite='necromancy',**options)
        self.assertEqual(1,len(self.commands))

    def test_rest_batch_requires_ui_four_actors_and_preserves_idempotent_intent(self):
        self.assertIn('rest', capabilities()['ui_suites'])
        first = self.start(ui=True, ui_suite='rest')
        self.assertEqual(first['run_id'], self.start(ui=True, ui_suite='rest')['run_id'])
        self.assertEqual('rest', self.commands[0][-1])
        for actors, ui in ((['raziel'], True), (['vezemir', 'morthak', 'raziel', 'dorn7'], False)):
            with self.assertRaises(ValueError):
                self.jobs.start(request_id='rest-invalid-options', actors=actors, ui=ui, ui_suite='rest')
        with self.assertRaisesRegex(ValueError, 'different'):
            self.start(ui=True, ui_suite='necromancy')
        self.assertEqual(1, len(self.commands))

    def test_passive_and_summon_batches_require_four_actors_and_native_identity(self):
        for suite in ('passives', 'summon_turns', 'inventory_summons'):
            with self.subTest(suite=suite):
                self.assertIn(suite, capabilities()['ui_suites'])
                request = 'focused-' + suite
                options = dict(request_id=request, actors=['vezemir', 'morthak', 'raziel', 'dorn7'],
                               ui=True, ui_suite=suite)
                first = self.jobs.start(**options)
                self.assertEqual(first['run_id'], self.jobs.start(**options)['run_id'])
                self.assertEqual(suite, self.commands[-1][-1])
                for actors, ui in ((['raziel'], True), (options['actors'], False)):
                    with self.assertRaises(ValueError):
                        self.jobs.start(request_id=request+'-invalid', actors=actors, ui=ui, ui_suite=suite)
                # End only the fake job before trying the next suite.
                self.process.returncode = 0
                self.jobs.status(first['run_id'])
                self.process = FakeProcess()

    def test_timeout_keeps_valid_partial_report_but_never_certifies(self):
        run = self.start(ui=True)
        self.report(run)
        self.now[0] = 1201
        result = self.jobs.status(run['run_id'])
        self.assertEqual(('ERROR', 'INCONCLUSIVE'), (result['state'], result['verdict']))
        self.assertEqual({'PASS': 1}, result['partial_report']['scenario_counts'])
        self.assertFalse(result['partial_report']['certification']['ready'])
        self.assertFalse(result['certification_ready'])
        self.assertNotIn('report', result)

    def test_invalid_partial_counts_are_not_exposed(self):
        run = self.start(ui=True)
        self.report(run, valid=False)
        self.now[0] = 1201
        result = self.jobs.status(run['run_id'])
        self.assertNotIn('partial_report', result)

    def test_api_failure_is_not_hidden_by_ui_skipped_after_failure(self):
        run = self.start(ui=True)
        self.report(run)
        file = self.root/run['run_id']/'evidence/sheet-test-report.json'
        report = json.loads(file.read_text(encoding='utf-8'))
        report.update(scenario_counts={'FAIL':1}, scenarios=[{'scenario_id':'actual-failure','status':'FAIL'}],
                      ui_smoke={'status':'INCONCLUSIVE','reason':'API failed; UI not run'})
        file.write_text(json.dumps(report), encoding='utf-8')
        self.process.returncode = 1
        result = self.jobs.status(run['run_id'])
        self.assertEqual(('COMPLETED','FAIL'), (result['state'],result['verdict']))
        self.assertEqual(1, result['report']['scenario_counts']['FAIL'])

    def test_running_progress_identifies_current_script_and_completed_checks(self):
        run = self.start(ui=True)
        folder = self.root / run['run_id'] / 'evidence'
        folder.mkdir()
        (folder / 'progress.json').write_text(json.dumps({
            'phase': 'ui', 'current': 'three-sheet-actions-smoke.cjs',
            'completed': 1, 'total': 2, 'elapsed_seconds': 12.5}), encoding='utf-8')
        result = self.jobs.status(run['run_id'])
        self.assertEqual('three-sheet-actions-smoke.cjs', result['progress']['current'])
        self.assertEqual(1, result['progress']['completed'])


class FakeVisualProcess:
    returncode = 0
    pid = 123456

    def __init__(self):
        self.stdin = io.StringIO()

    def communicate(self, timeout=None):
        return json.dumps({'status': 'PASS', 'action_coverage': []}), ''


class VisualBatchTests(TestCase):
    def setUp(self):
        contained = patch('scripts.run_sheet_test.OwnedProcessGroup')
        self.groups = contained.start(); self.addCleanup(contained.stop)
        available = patch('scripts.run_sheet_test.wait_for_memory', return_value=True)
        available.start(); self.addCleanup(available.stop)
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.output = Path(folder.name)
        self.calls = []

    def spawn(self, command, **kwargs):
        self.calls.append((command, kwargs))
        return FakeVisualProcess()

    def run_batch(self, suite='combat'):
        with patch('scripts.run_sheet_test.shutil.which', return_value='node'), \
             patch('scripts.run_sheet_test.subprocess.Popen', side_effect=self.spawn), \
             patch('app.approved_spell_pack.apply_approved_spell_pack'):
            return run_visual_checks(self.output, 8871,
                ['vezemir', 'morthak', 'raziel', 'dorn7'], ui_suite=suite)

    def test_combat_batch_runs_both_fixed_halves_without_unrelated_map_shop_suite(self):
        result = self.run_batch()
        scripts = [Path(call[0][-1]).name for call in self.calls]
        self.assertEqual(['sheet-combat-readiness-smoke.cjs', 'three-sheet-actions-smoke.cjs',
                          'three-sheet-actions-second-smoke.cjs'], scripts)
        self.assertEqual(len(scripts), len(set(scripts)))
        self.assertEqual('1', self.calls[-1][1]['env']['OMNISVERA_QA_EXTENDED_ACTIONS'])
        self.assertEqual('first', self.calls[-1][1]['env']['OMNISVERA_QA_THREE_SHEET_BATCH'])
        wrapper = Path(__file__).resolve().parents[1]/'frontend'/'tests'/'three-sheet-actions-second-smoke.cjs'
        self.assertIn("OMNISVERA_QA_THREE_SHEET_BATCH='second'", wrapper.read_text(encoding='utf-8'))
        self.assertEqual('PASS', result['status'])
        self.assertEqual('combat', result['suite'])
        checkpoint = json.loads((self.output / 'progress.json').read_text(encoding='utf-8'))
        self.assertEqual(3, checkpoint['completed'])
        self.assertTrue(all('duration_seconds' in check for check in result['checks']))

    def test_full_batch_preserves_all_twelve_existing_smokes(self):
        result = self.run_batch('full')
        self.assertEqual(12, len(self.calls))
        self.assertEqual('PASS', result['status'])
        self.assertEqual(12, self.groups.return_value.close.call_count)

    def test_oct24_uses_two_fixed_scripts_and_only_checked_fixture_maintenance(self):
        with patch('app.approved_resource_limits.apply_approved_resource_limits') as maintain:
            result=self.run_batch('oct24')
        maintain.assert_called_once_with(self.output/'simulation.sqlite3')
        self.assertEqual(['table-balance-oct24-smoke.cjs','monster-exposure-poison-smoke.cjs'],[Path(call[0][-1]).name for call in self.calls])
        self.assertEqual('PASS',result['status'])

    def test_friday_batch_is_fixed_and_sequential_without_expanding_full(self):
        result=self.run_batch('friday')
        self.assertEqual(['scene-preparation-smoke.cjs','thoradin-wallet-smoke.cjs',
            'three-sheet-actions-smoke.cjs','three-sheet-actions-second-smoke.cjs',
            'hemomancy-passives-smoke.cjs','summon-turns-smoke.cjs','four-sheet-rest-smoke.cjs'],
            [Path(call[0][-1]).name for call in self.calls])
        self.assertEqual('PASS',result['status'])

    def test_failed_containment_stops_only_created_child_and_never_opens_the_gate(self):
        process = FakeVisualProcess()
        self.groups.return_value.track.side_effect = OSError('fixture assign denied')
        with patch.object(self, 'spawn', return_value=process), \
             patch('scripts.run_sheet_test.stop_owned_server') as stop:
            result = self.run_batch('passives')
        self.assertEqual('INCONCLUSIVE', result['status'])
        stop.assert_called_once_with(process)
        self.groups.return_value.close.assert_called_once()
        self.assertIsNone(process.stdin)

    def test_lightning_batch_runs_readiness_and_native_multitarget_flow(self):
        result=self.run_batch('lightning')
        self.assertEqual(['sheet-combat-readiness-smoke.cjs','range-multitarget-smoke.cjs'],
                         [Path(call[0][-1]).name for call in self.calls])
        self.assertEqual('PASS',result['status'])

    def test_hemomancy_batch_is_explicit_and_does_not_expand_other_batches(self):
        result=self.run_batch('hemomancy')
        self.assertEqual(['hemomancy-weapons-smoke.cjs','hemomancy-weapons-second-smoke.cjs'],[Path(call[0][-1]).name for call in self.calls])
        self.assertEqual('first',self.calls[0][1]['env']['OMNISVERA_QA_HEMOMANCY_BATCH'])
        self.assertEqual('PASS',result['status'])

    def test_vampiric_batch_runs_only_two_fixed_halves(self):
        with patch.dict('os.environ',{'OMNISVERA_QA_VAMPIRIC_BATCH':'untrusted-filter'}):
            result=self.run_batch('vampiric')
        self.assertEqual(['raziel-vampiric-smoke.cjs','raziel-vampiric-second-smoke.cjs'],
                         [Path(call[0][-1]).name for call in self.calls])
        self.assertEqual('first',self.calls[0][1]['env']['OMNISVERA_QA_VAMPIRIC_BATCH'])
        self.assertEqual('PASS',result['status'])
        self.assertTrue(result['grid_actions'])

    def test_necromancy_batch_is_three_fixed_scripts_without_expanding_full(self):
        with patch.dict('os.environ',{'OMNISVERA_QA_NECROMANCY_BATCH':'arbitrary'}):
            result=self.run_batch('necromancy')
        self.assertEqual(['morthak-necromancy-smoke.cjs','morthak-summons-smoke.cjs',
                          'morthak-high-spells-smoke.cjs'],[Path(call[0][-1]).name for call in self.calls])
        self.assertEqual('first',self.calls[0][1]['env']['OMNISVERA_QA_NECROMANCY_BATCH'])
        self.assertEqual('PASS',result['status'])

    def test_rest_batch_runs_only_two_fixed_smokes_without_expanding_full(self):
        result = self.run_batch('rest')
        self.assertEqual(['map-toolbar-rest-smoke.cjs', 'four-sheet-rest-smoke.cjs'],
                         [Path(call[0][-1]).name for call in self.calls])
        self.assertEqual('PASS', result['status'])
        self.assertEqual('rest', result['suite'])
        self.assertTrue(all(call[1]['env']['OMNISVERA_SHEET_QA_ACTORS'] == 'vezemir,morthak,raziel,dorn7'
                            for call in self.calls))

    def test_passive_and_summon_batches_use_only_fixed_scripts(self):
        for suite, scripts in (
            ('passives', ['hemomancy-passives-smoke.cjs']),
            ('summon_turns', ['summon-turns-smoke.cjs']),
        ):
            with self.subTest(suite=suite):
                self.calls.clear()
                result = self.run_batch(suite)
                self.assertEqual(scripts, [Path(call[0][-1]).name for call in self.calls])
                self.assertEqual('PASS', result['status'])
                self.assertEqual(suite, result['suite'])
                self.assertTrue(result['grid_actions'])

    def test_pretty_passive_receipt_survives_the_native_checkpoint(self):
        coverage = [{'actor': 'raziel', 'key': 'passive:mira-predatoria',
                     'verified_checks': ['ui']}]
        process = FakeVisualProcess()
        process.communicate = lambda timeout=None: (
            'RUN mira\n' + json.dumps({'status': 'PASS', 'action_coverage': coverage}, indent=2), '')
        with patch.object(self, 'spawn', return_value=process):
            result = self.run_batch('passives')
        self.assertEqual('PASS', result['status'])
        self.assertEqual(coverage, result['checks'][0]['action_coverage'])
        saved = json.loads((self.output/'ui-progress.json').read_text(encoding='utf-8'))
        self.assertEqual(coverage, saved['checks'][0]['action_coverage'])

    def test_explicit_uncertainty_stops_batch_without_false_game_failure(self):
        process = FakeVisualProcess()
        process.returncode = 2
        process.communicate = lambda timeout=None: (
            json.dumps({'status': 'INCONCLUSIVE', 'reason': 'Missing fixture component'}, indent=2), '')
        with patch.object(self, 'spawn', return_value=process) as launch:
            result = self.run_batch('necromancy')
        self.assertEqual(1, launch.call_count)
        self.assertEqual('INCONCLUSIVE', result['status'])
        self.assertEqual('Missing fixture component', result['checks'][0]['reason'])
        self.assertNotIn('action_coverage', result['checks'][0])

    def test_declared_failure_stops_even_if_script_accidentally_exits_zero(self):
        process = FakeVisualProcess()
        process.communicate = lambda timeout=None: ('{"status":"FAIL"}', '')
        with patch.object(self, 'spawn', return_value=process) as launch:
            result = self.run_batch('combat')
        self.assertEqual(1, launch.call_count)
        self.assertEqual('FAIL', result['status'])

    def test_visual_fixture_copies_only_referenced_media_and_reports_gaps(self):
        (self.output/'simulation.sqlite3').touch()
        gaps={'copied':['zz_media/map.png'],'missing':['zz_media/missing.png'],'skipped':[],'bytes':20}
        with patch('scripts.fixture_media.copy_fixture_media', return_value=gaps) as copy:
            result=self.run_batch('lightning')
        self.assertEqual(gaps,result['media_fixture'])
        self.assertEqual(self.output/'simulation.vault',copy.call_args.args[2])

    def test_api_exit_code_has_priority_over_inconclusive_ui(self):
        from scripts.run_sheet_test import runner_exit_code
        self.assertEqual(1, runner_exit_code(1, {'status':'INCONCLUSIVE'}))
        self.assertEqual(2, runner_exit_code(0, {'status':'INCONCLUSIVE'}))
        self.assertEqual(1, runner_exit_code(0, {'status':'FAIL'}))
        self.assertEqual(0, runner_exit_code(0, {'status':'PASS'}))

    def test_visual_timeout_records_current_script_and_stops_only_owned_process(self):
        process = FakeVisualProcess()
        process.communicate = lambda timeout=None: (_ for _ in ()).throw(
            subprocess.TimeoutExpired('node', timeout, output='partial'))
        with patch('scripts.run_sheet_test.shutil.which', return_value='node'), \
             patch('scripts.run_sheet_test.subprocess.Popen', return_value=process), \
             patch('scripts.run_sheet_test.stop_owned_server') as stop, \
             patch('app.approved_spell_pack.apply_approved_spell_pack'):
            result = run_visual_checks(self.output, 8871,
                ['vezemir', 'morthak', 'raziel', 'dorn7'], ui_suite='combat')
        stop.assert_called_once_with(process)
        self.assertEqual('INCONCLUSIVE', result['status'])
        self.assertEqual('sheet-combat-readiness-smoke.cjs', result['checks'][0]['script'])
        self.assertEqual('INCONCLUSIVE', result['checks'][0]['status'])


class BatchMCPContractTests(IsolatedAsyncioTestCase):
    async def test_mcp_exposes_safe_batch_and_partial_evidence(self):
        from scripts.companion_test_mcp import create_server
        server = create_server()
        start = next(tool for tool in await server.list_tools() if tool.name == 'companion_test_start')
        self.assertEqual(['full', 'combat', 'lightning', 'hemomancy', 'vampiric', 'necromancy', 'rest', 'passives', 'summon_turns', 'friday', 'oct24', 'monster_defaults', 'active_spells', 'catalog', 'inventory_summons', 'sprite_studio', 'item_families'], start.inputSchema['properties']['ui_suite']['enum'])
        from scripts.companion_test_mcp import TestRunResponse
        self.assertIn('partial_report', TestRunResponse.model_fields)
        self.assertIn('progress', TestRunResponse.model_fields)
