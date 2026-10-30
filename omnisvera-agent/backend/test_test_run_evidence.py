from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app import test_run_evidence as evidence


RUN_ID = "test-" + "a" * 32


class TestRunEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.job = {"schema_version": 1, "run_id": RUN_ID, "state": "COMPLETED", "verdict": "PASS",
                    "exit_code": 0, "actors": ["raziel"], "ui": True, "ui_suite": "full"}
        self.report = {"schema_version": 1, "kind": "sheet_test_evidence", "scenario_counts": {"PASS": 1},
                       "scenarios": [{"actor": "raziel", "status": "PASS", "error": "PRIVATE_PATH_OR_NOTES"}],
                       "characters": {"raziel": {"entries": [], "counts": {}}},
                       "ui_smoke": {"status": "PASS", "reason": "PRIVATE_UI_LOG"},
                       "certification": {"ready": True}, "private_snapshot": "SECRET_CONTENT"}
        self.write()

    def write(self) -> None:
        folder = self.root / RUN_ID
        (folder / "evidence").mkdir(parents=True, exist_ok=True)
        (folder / "job.json").write_text(json.dumps(self.job), encoding="utf-8")
        (folder / "evidence/sheet-test-report.json").write_text(json.dumps(self.report), encoding="utf-8")

    def read(self):
        return evidence.read_test_run_evidence(RUN_ID, root=self.root)

    def test_existing_terminal_evidence_is_allowlisted_and_does_not_certify_proposal(self) -> None:
        result = self.read()
        self.assertEqual(set(result), {"run_id", "state", "verdict", "scenario_counts", "actors", "ui_suite",
                                       "ui_status", "certification_ready", "scope", "report_sha256"})
        self.assertEqual(result["scenario_counts"], {"PASS": 1})
        self.assertEqual(result["actors"], ["raziel"])
        self.assertIs(result["certification_ready"], False)
        self.assertEqual(result["scope"], "existing_code_only_not_proposal_execution")
        raw = (self.root / RUN_ID / "evidence/sheet-test-report.json").read_bytes()
        self.assertEqual(result["report_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertNotIn("PRIVATE", json.dumps(result))
        self.assertNotIn("SECRET", json.dumps(result))

    def test_run_id_and_root_boundaries_reject_paths(self) -> None:
        for run_id in ("../secret", RUN_ID + "/..", "test-" + "A" * 32, "https://example.invalid/run"):
            with self.subTest(run_id=run_id), self.assertRaises(ValueError):
                evidence.read_test_run_evidence(run_id, root=self.root)
        with self.assertRaises(ValueError):
            evidence.read_test_run_evidence(RUN_ID, root=Path(__file__).parent)
        with self.assertRaises(FileNotFoundError):
            evidence.read_test_run_evidence("test-" + "b" * 32, root=self.root)

    def test_terminal_verdict_exit_and_report_schema_must_agree(self) -> None:
        original_job = deepcopy(self.job)
        for field, value in (("state", "RUNNING"), ("state", "ERROR"), ("verdict", "INCONCLUSIVE"),
                             ("verdict", "FAIL"), ("exit_code", 1), ("exit_code", True), ("run_id", "other")):
            with self.subTest(field=field, value=value):
                self.job = {**original_job, field: value}
                self.write()
                with self.assertRaises(ValueError):
                    self.read()
        self.job = original_job
        for field, value in (("kind", "other"), ("schema_version", 2), ("characters", {})):
            saved = deepcopy(self.report)
            self.report[field] = value
            self.write()
            with self.assertRaises(ValueError):
                self.read()
            self.report = saved

    def test_counter_actor_and_integer_counts_validation(self) -> None:
        for counts in ({"PASS": 2}, {"PASS": True}, {"PASS": -1}, {"UNKNOWN": 1}):
            self.report["scenario_counts"] = counts
            self.write()
            with self.assertRaises(ValueError):
                self.read()
        self.report["scenario_counts"] = {"PASS": 1}
        self.report["scenarios"][0]["actor"] = "private-character"
        self.write()
        with self.assertRaises(ValueError):
            self.read()

    def test_failed_completed_run_is_valid_evidence_not_a_proposal_approval(self) -> None:
        self.job.update(verdict="FAIL", exit_code=1)
        self.report["scenario_counts"] = {"FAIL": 1}
        self.report["scenarios"][0]["status"] = "FAIL"
        self.report["ui_smoke"]["status"] = "INCONCLUSIVE"
        self.write()
        result = self.read()
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIs(result["certification_ready"], False)

    def test_symlink_component_and_file_size_limit_are_rejected(self) -> None:
        original = Path.is_symlink
        unsafe = self.root / RUN_ID / "evidence"
        with patch.object(Path, "is_symlink", autospec=True,
                          side_effect=lambda path: path == unsafe or original(path)):
            with self.assertRaises(ValueError):
                self.read()
        with patch.object(evidence, "MAX_REPORT_BYTES", 10):
            with self.assertRaises(ValueError):
                self.read()

    def test_nan_and_duplicate_json_fields_are_rejected(self) -> None:
        path = self.root / RUN_ID / "evidence/sheet-test-report.json"
        for raw in ('{"schema_version": 1, "x": NaN}', '{"x": 1, "x": 2}'):
            path.write_text(raw, encoding="utf-8")
            with self.assertRaises(ValueError):
                self.read()

    def test_character_coverage_counts_and_ui_suite_must_match(self) -> None:
        self.report["characters"]["raziel"]["counts"] = {"PASS": 1}
        self.write()
        with self.assertRaises(ValueError):
            self.read()
        self.report["characters"]["raziel"]["counts"] = {}
        self.report["ui_smoke"]["suite"] = "combat"
        self.write()
        with self.assertRaises(ValueError):
            self.read()

    def test_hemomancy_suite_is_accepted_without_certifying_all_actions(self):
        self.job['ui_suite']='hemomancy'
        self.job['actors']=['raziel','morthak','vezemir','dorn7']
        self.report['characters']={actor:{'entries':[],'counts':{}} for actor in self.job['actors']}
        self.report['ui_smoke']['suite']='hemomancy'
        self.write()
        result=self.read()
        self.assertEqual('hemomancy',result['ui_suite'])
        self.assertFalse(result['certification_ready'])

    def test_vampiric_suite_is_accepted_but_never_certifies_all_actions(self):
        self.job['ui_suite']='vampiric'
        self.job['actors']=['raziel','morthak','vezemir','dorn7']
        self.report['characters']={actor:{'entries':[],'counts':{}} for actor in self.job['actors']}
        self.report['ui_smoke']['suite']='vampiric'
        self.write()
        result=self.read()
        self.assertEqual('vampiric',result['ui_suite'])
        self.assertFalse(result['certification_ready'])

    def test_rest_suite_is_accepted_without_certifying_all_actions(self):
        self.job['ui_suite'] = 'rest'
        self.job['actors'] = ['raziel', 'morthak', 'vezemir', 'dorn7']
        self.report['characters'] = {actor: {'entries': [], 'counts': {}} for actor in self.job['actors']}
        self.report['ui_smoke']['suite'] = 'rest'
        self.write()
        result = self.read()
        self.assertEqual('rest', result['ui_suite'])
        self.assertFalse(result['certification_ready'])

    def test_friday_suite_accepts_only_consistent_terminal_visual_evidence(self):
        self.job['ui_suite'] = 'friday'
        self.job['actors'] = ['raziel', 'morthak', 'vezemir', 'dorn7']
        self.report['characters'] = {actor: {'entries': [], 'counts': {}} for actor in self.job['actors']}
        self.report['ui_smoke']['suite'] = 'friday'
        self.write()
        result = self.read()
        self.assertEqual('friday', result['ui_suite'])
        self.assertFalse(result['certification_ready'])
        self.assertNotIn('SECRET', json.dumps(result))
        for status, suite in [('INCONCLUSIVE', 'friday'), ('PASS', 'rest')]:
            self.report['ui_smoke'].update(status=status, suite=suite)
            self.write()
            with self.assertRaises(ValueError):
                self.read()
        self.report['ui_smoke'].update(status='PASS', suite='unknown')
        self.job['ui_suite'] = 'unknown'
        self.write()
        with self.assertRaises(ValueError):
            self.read()

    def test_passive_and_summon_evidence_never_certifies_entire_sheet(self):
        for suite in ('passives', 'summon_turns'):
            with self.subTest(suite=suite):
                self.job['ui_suite'] = suite
                self.job['actors'] = ['raziel', 'morthak', 'vezemir', 'dorn7']
                self.report['characters'] = {actor: {'entries': [], 'counts': {}} for actor in self.job['actors']}
                self.report['ui_smoke']['suite'] = suite
                self.write()
                result = self.read()
                self.assertEqual(suite, result['ui_suite'])
                self.assertFalse(result['certification_ready'])

    def test_necromancy_suite_does_not_certify_proposals_or_all_actions(self):
        self.job['ui_suite']='necromancy'
        self.job['actors']=['raziel','morthak','vezemir','dorn7']
        self.report['characters']={actor:{'entries':[],'counts':{}} for actor in self.job['actors']}
        self.report['ui_smoke']['suite']='necromancy'
        self.write()
        result=self.read()
        self.assertEqual('necromancy',result['ui_suite'])
        self.assertFalse(result['certification_ready'])


if __name__ == "__main__":
    unittest.main()
