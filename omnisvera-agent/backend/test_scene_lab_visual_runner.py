from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts import run_scene_lab_visual as runner


class SceneLabVisualRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.database = self.root / "simulation.sqlite3"
        self.database.write_bytes(b"already existing copied fixture")
        self.vault = self.database.with_suffix(".vault")
        self.vault.mkdir()
        self.output = self.root / "new-ui-evidence"
        self.frontend = self.root / "frontend"
        (self.frontend / "dist").mkdir(parents=True)
        (self.frontend / "dist/index.html").write_text("fixture build", encoding="utf-8")
        (self.frontend / "tests").mkdir()
        (self.frontend / "tests/scene-lab-smoke.cjs").write_text("// fixture", encoding="utf-8")
        self.modules = self.root / "node_modules"
        (self.modules / "playwright").mkdir(parents=True)
        (self.modules / "playwright/package.json").write_text("{}", encoding="utf-8")
        self.server = Mock(pid=91001)
        self.server.poll.return_value = None
        self.browser = Mock(pid=91002, returncode=0)
        self.browser.poll.return_value = 0
        self.pass_payload = {"status": "PASS", "scope": "isolated_private_scene_lab_ui_only",
                             "visual_acceptance": "pending_human_or_agent_image_review", "checks": ["GM", "player"],
                             "screenshots": [], "proposal_execution": "NOT_IMPLEMENTED_NOT_TESTED"}
        self.browser.communicate.return_value = (json.dumps(self.pass_payload) + "\n", "")
        patches = [patch.object(runner, "FRONTEND", self.frontend), patch.object(runner, "QA_MODULES", self.modules),
                   patch.object(runner.shutil, "which", return_value="node.exe"),
                   patch.object(runner, "checked_port", return_value=8871),
                   patch.object(runner, "_read_health", return_value={"access_mode": "gm", "backend": "ok",
                                "database_path": str(self.database), "vault_path": str(self.vault)}),
                   patch.object(runner.subprocess, "Popen", side_effect=[self.server, self.browser]),
                   patch.object(runner, "stop_owned_server")]
        self.mocks = [item.start() for item in patches]
        for item in patches:
            self.addCleanup(item.stop)
        self.spawn, self.stop = self.mocks[-2:]

    def run_smoke(self, **kwargs):
        return runner.run_scene_lab_visual(self.database, self.output, **kwargs)

    def test_pass_isolated_children_fixed_environment_and_pending_visual_acceptance(self) -> None:
        with patch.dict(os.environ, {"OMNISVERA_MASTER_TOKEN": "OPERATIONAL_SECRET",
                                   "OPENCODE_SERVER_PASSWORD": "PRIVATE_PASSWORD",
                                   "OMNISVERA_VAULT_PATH": "C:/production",
                                   "HTTP_PROXY": "http://private-proxy"}):
            result = self.run_smoke()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["visual_acceptance"], "pending_human_or_agent_image_review")
        self.assertEqual(result["proposal_execution"], "NOT_IMPLEMENTED_NOT_TESTED")
        self.assertEqual(self.spawn.call_count, 2)
        server_args = self.spawn.call_args_list[0].args[0]
        self.assertIn("serve", server_args)
        self.assertNotIn("prepare", server_args)
        self.assertIn(str(self.database), server_args)
        for call in self.spawn.call_args_list:
            env = call.kwargs["env"]
            self.assertEqual(env["OMNISVERA_MASTER_TOKEN"], "cf01-local-gm")
            self.assertEqual(env["OMNISVERA_DB_PATH"], str(self.database))
            self.assertEqual(env["OMNISVERA_VAULT_PATH"], str(self.vault))
            self.assertNotIn("OPENCODE_SERVER_PASSWORD", env)
            self.assertNotIn("HTTP_PROXY", env)
            self.assertNotIn("OPERATIONAL_SECRET", json.dumps(env))
        self.assertEqual(self.spawn.call_args_list[1].kwargs["env"]["OMNISVERA_SHEET_QA_URL"], "http://127.0.0.1:8871")
        self.browser.communicate.assert_called_once_with(timeout=300)
        self.stop.assert_called_once_with(self.server)
        self.assertTrue((self.output / "lab-smoke.private.log").is_file())
        self.assertEqual(json.loads((self.output / "scene-lab-visual-result.json").read_text())["status"], "PASS")

    def test_invalid_database_production_port_existing_output_or_missing_dependencies_never_spawn(self) -> None:
        for port in (8787, 8788, 8872):
            with self.subTest(port=port), self.assertRaises(ValueError):
                self.run_smoke(port=port)
        with self.assertRaises(ValueError):
            runner.run_scene_lab_visual(Path(__file__), self.output)
        self.output.mkdir()
        with self.assertRaises(ValueError):
            self.run_smoke()
        self.output.rmdir()
        self.mocks[2].return_value = None
        with self.assertRaises(ValueError):
            self.run_smoke()
        self.spawn.assert_not_called()
        self.stop.assert_not_called()

    def test_occupied_port_is_not_stopped(self) -> None:
        self.mocks[3].side_effect = ValueError("Occupied fixture port")
        with self.assertRaises(ValueError):
            self.run_smoke()
        self.spawn.assert_not_called()
        self.stop.assert_not_called()

    def test_failed_fixture_child_or_wrong_health_never_runs_browser_and_stops_only_owned_server(self) -> None:
        self.server.poll.return_value = 1
        result = self.run_smoke()
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertEqual(self.spawn.call_count, 1)
        self.stop.assert_called_once_with(self.server)

    def test_health_timeout_and_path_mismatch_cleanup_owned_child(self) -> None:
        with patch.object(runner, "_wait_for_fixture", side_effect=TimeoutError):
            result = self.run_smoke()
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.stop.assert_called_once_with(self.server)
        self.assertEqual(self.spawn.call_count, 1)

    def test_browser_failure_or_timeout_cleans_only_created_processes(self) -> None:
        self.browser.returncode = 1
        self.browser.poll.return_value = 1
        result = self.run_smoke()
        self.assertEqual(result["status"], "FAIL")
        self.stop.assert_called_once_with(self.server)

    def test_browser_timeout_stops_its_owned_tree_and_fixture(self) -> None:
        self.browser.returncode = None
        self.browser.poll.return_value = None
        self.browser.communicate.side_effect = subprocess.TimeoutExpired("fixed smoke", 300)
        result = self.run_smoke()
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertEqual([call.args[0] for call in self.stop.call_args_list], [self.browser, self.server])

    def test_zero_exit_without_explicit_pass_json_is_not_acceptance(self) -> None:
        self.browser.communicate.return_value = ("PASS\n", "")
        result = self.run_smoke()
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertEqual(result["visual_acceptance"], "pending_human_or_agent_image_review")

    def test_health_requires_gm_exact_fixture_paths_and_temporary_vault(self) -> None:
        self.mocks[4].return_value = {"access_mode": "gm", "backend": "ok",
                                     "database_path": str(self.root / "other.sqlite3"), "vault_path": str(self.vault)}
        result = self.run_smoke()
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertEqual(self.spawn.call_count, 1)
        self.stop.assert_called_once_with(self.server)


if __name__ == "__main__":
    unittest.main()
