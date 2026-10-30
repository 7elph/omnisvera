"""API scenario siblings must not try joining the fixture's Windows job."""
import os
import subprocess
import sys
from pathlib import Path
from unittest import TestCase, skipUnless
from unittest.mock import Mock, patch

from scripts import run_sheet_test as runner


class ScenarioWorkerContainmentTests(TestCase):
    def test_scenario_gets_its_own_group_without_mutating_fixture_environment(self):
        env = {'OMNISVERA_QA_JOB_NAME': 'fixture-private-group', 'PATH': 'test-path'}
        group = Mock(name='scenario-group')
        group.name = 'scenario-private-group'
        process = Mock()
        process.wait.return_value = 0
        process.poll.return_value = 0
        with patch.object(runner, 'OwnedProcessGroup', return_value=group), \
             patch.object(runner.subprocess, 'Popen', return_value=process) as spawn:
            result = runner.run_scenario_worker(['native-python', 'fixed-script'], cwd=Path('backend'), env=env)
        self.assertEqual(0, result.returncode)
        self.assertEqual('fixture-private-group', env['OMNISVERA_QA_JOB_NAME'])
        self.assertEqual('scenario-private-group', spawn.call_args.kwargs['env']['OMNISVERA_QA_JOB_NAME'])
        self.assertEqual(subprocess.DEVNULL, spawn.call_args.kwargs['stdin'])
        group.track.assert_called_once_with(process)
        group.close.assert_called_once_with()

    def test_failed_group_assignment_stops_only_the_new_scenario_worker(self):
        group = Mock()
        group.name = 'scenario-private-group'
        group.track.side_effect = PermissionError('assignment denied')
        process = Mock()
        with patch.object(runner, 'OwnedProcessGroup', return_value=group), \
             patch.object(runner.subprocess, 'Popen', return_value=process), \
             patch.object(runner, 'stop_owned_server') as stop:
            with self.assertRaises(PermissionError):
                runner.run_scenario_worker(['native-python', 'fixed-script'], cwd=Path('backend'), env={})
        stop.assert_called_once_with(process)
        group.close.assert_called_once_with()

    @skipUnless(os.name == 'nt', 'Windows nested job containment')
    def test_real_scenario_joins_own_group_without_stopping_sibling_fixture(self):
        group = runner.OwnedProcessGroup()
        fixture = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'],
            creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            group.track(fixture)
            env = dict(os.environ, OMNISVERA_QA_JOB_NAME=group.name)
            code = ('from scripts.memory_guard import join_owned_job_from_env;'
                    'join_owned_job_from_env()')
            result = runner.run_scenario_worker([sys.executable, '-c', code],
                cwd=Path(__file__).parent, env=env)
            self.assertEqual(0, result.returncode)
            self.assertIsNone(fixture.poll(), 'Scenario cleanup must preserve sibling fixture')
        finally:
            group.close()
            if fixture.poll() is None:
                runner.stop_owned_server(fixture)
            fixture.wait(timeout=5)
