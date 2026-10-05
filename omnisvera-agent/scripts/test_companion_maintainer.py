import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('maintainer', Path(__file__).with_name('companion_maintainer.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MaintainerTests(unittest.TestCase):
    def test_inspect_repeatable_no_product_changes_or_secret_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'backend').mkdir()
            (root / 'backend/example.py').write_text('# TODO token=PRIVATE_CANARY\nx=1\n')
            (root / 'backend/.env').write_text('PRIVATE_CANARY')
            before = m.fingerprint(root)
            def fake_git(root, *args):
                return 'dirty' if args[0] == 'status' else 'fixture'
            with patch.object(m, 'git', side_effect=fake_git), patch.object(m, 'run_check', side_effect=AssertionError('inspect ran checks')):
                first = m.inspect(root)
                second = m.inspect(root)
            self.assertEqual(before, m.fingerprint(root))
            self.assertEqual(first['source_fingerprint'], second['source_fingerprint'])
            self.assertEqual(second['manual_cycle_gate'], 'BLOCKED_DIRTY')
            self.assertEqual(second['marker_count'], 1)
            self.assertNotIn('PRIVATE_CANARY', json.dumps(second))
            self.assertTrue(all(x == 'INCONCLUSIVE' for x in second['tests'].values()))

    def test_missing_executable_is_inconclusive(self):
        self.assertEqual(m.run_check(['missing-companion-executable-xyz'], m.ROOT)['status'], 'INCONCLUSIVE')

    def test_missing_python_dependency_not_pass(self):
        result = m.run_check([m.sys.executable, '-c', 'import nonexistent_companion_dependency_xyz'], m.ROOT)
        self.assertEqual(result['status'], 'INCONCLUSIVE')

    def test_failed_check_is_fail_and_raw_output_not_retained(self):
        result = m.run_check([m.sys.executable, '-c', 'print("PRIVATE_CANARY"); raise SystemExit(1)'], m.ROOT)
        self.assertEqual(result['status'], 'FAIL')
        self.assertNotIn('PRIVATE_CANARY', json.dumps(result))

    def test_history_validation(self):
        report = dict(cycle_id='test-001', problem='overflow', evidence='reproduced in test', classification='GREEN',
                      hypothesis='bound width', files_changed=['frontend/src/example.css'],
                      tests_before={'frontend': 'FAIL'}, tests_after={'frontend': 'PASS'}, result='PASS', commit=None)
        self.assertEqual(m.validate_history(report), report)
        for update in ({'classification':'RED'}, {'commit':'abc'}, {'cycle_id':'../escape'},
                       {'tests_after':{'frontend':'INCONCLUSIVE'}}, {'evidence':'token=PRIVATE_CANARY'}):
            with self.assertRaises(ValueError):
                m.validate_history(dict(report, **update))

    def test_contract_and_commands(self):
        text = (m.ROOT / '.autonomy/OPENCODE_MAINTAINER_PROMPT.md').read_text(encoding='utf-8')
        for word in ('GREEN', 'YELLOW', 'RED', 'INCONCLUSIVE', 'NO_CHANGE'):
            self.assertIn(word, text)
        with tempfile.TemporaryDirectory() as build:
            commands = m.commands(m.ROOT, Path(build))
            self.assertIn(build, commands['build'][0])
            self.assertIn('--noEmit', commands['typescript'][0])
            self.assertNotIn('opencode', json.dumps({k:v[0] for k,v in commands.items()}))


if __name__ == '__main__':
    unittest.main()
