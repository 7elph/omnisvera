"""Native visual receipts preserve uncertainty without hiding failed tests."""
import json
from unittest import TestCase

from scripts import run_sheet_test as runner


class VisualResultReceiptTests(TestCase):
    def test_pretty_terminal_receipt_keeps_action_coverage(self):
        coverage = [{'actor': 'raziel', 'key': 'passive:mira-predatoria',
                     'verified_checks': ['ui']}]
        stdout = 'RUN mira\n' + json.dumps(
            {'status': 'PASS', 'action_coverage': coverage}, indent=2)
        result = runner.visual_process_result(stdout, '', 0)
        self.assertEqual('PASS', result['status'])
        self.assertEqual(coverage, result['action_coverage'])

    def test_single_line_receipts_remain_compatible(self):
        result = runner.visual_process_result(
            '{"status":"PASS","action_coverage":[]}', '', 0)
        self.assertEqual({'status': 'PASS', 'action_coverage': []}, result)

    def test_explicit_missing_component_is_inconclusive_not_game_failure(self):
        result = runner.visual_process_result(
            'RUN clones\n' + json.dumps({'status': 'INCONCLUSIVE',
                                        'reason': 'Fixture crystal missing'}, indent=2),
            'Inconclusive: Fixture crystal missing', 2)
        self.assertEqual('INCONCLUSIVE', result['status'])
        self.assertEqual('Fixture crystal missing', result['reason'])
        self.assertNotIn('action_coverage', result)

    def test_nonzero_exit_cannot_publish_pass_or_coverage(self):
        for code in (1, 2, -1):
            with self.subTest(code=code):
                result = runner.visual_process_result(
                    '{"status":"PASS","action_coverage":[{"actor":"raziel"}]}',
                    '', code)
                self.assertEqual('FAIL', result['status'])
                self.assertNotIn('action_coverage', result)

    def test_explicit_failure_overrides_zero_exit_and_missing_module_text(self):
        for code in (0, 1):
            with self.subTest(code=code):
                result = runner.visual_process_result(
                    '{"status":"FAIL"}', 'Cannot find module in assertion', code)
                self.assertEqual('FAIL', result['status'])

    def test_exit_two_alone_does_not_relabel_an_assertion_as_inconclusive(self):
        result = runner.visual_process_result('', 'AssertionError: no damage', 2)
        self.assertEqual('FAIL', result['status'])

    def test_only_terminal_json_is_eligible_for_action_coverage(self):
        result = runner.visual_process_result(
            '{"status":"PASS","action_coverage":[{"actor":"raziel"}]}\nRUN other case',
            '', 0)
        self.assertEqual('PASS', result['status'])
        self.assertNotIn('action_coverage', result)

    def test_known_dependency_absence_is_still_inconclusive(self):
        for stderr in ('Cannot find module playwright', "Executable doesn't exist"):
            with self.subTest(stderr=stderr):
                self.assertEqual('INCONCLUSIVE',
                    runner.visual_process_result('', stderr, 1)['status'])

    def test_explicit_inconclusive_cannot_hide_unexpected_exit(self):
        result = runner.visual_process_result(
            '{"status":"INCONCLUSIVE","reason":"partial"}', 'AssertionError', 1)
        self.assertEqual('FAIL', result['status'])

    def test_layout_only_zero_exit_without_receipt_preserves_legacy_success(self):
        self.assertEqual({'status': 'PASS'},
                         runner.visual_process_result('layout completed', '', 0))

    def test_unrecognized_json_shape_cannot_supply_coverage_or_crash_reader(self):
        for status in (['PASS'], {'value': 'PASS'}, None, True):
            with self.subTest(status=status):
                result = runner.visual_process_result(json.dumps({
                    'status': status, 'action_coverage': [{'actor': 'raziel'}]}), '', 1)
                self.assertEqual({'status': 'FAIL'}, result)
