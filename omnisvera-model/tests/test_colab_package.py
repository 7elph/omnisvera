from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from omnisvera_model.colab import (  # noqa: E402
    CLASSIFICATION,
    EXPERIMENTAL_CLASSIFICATION,
    prepare_colab_package,
    prepare_experimental_colab_package,
)
from omnisvera_model.io import write_jsonl  # noqa: E402
from omnisvera_model.schema import new_example  # noqa: E402
from omnisvera_model.training import SMOKE_ACK  # noqa: E402


def approved(example_id: str, question: str, answer: str) -> dict:
    return new_example(
        id=example_id,
        source_type="corrected_chat",
        category="grounded_qa",
        access_profile="player",
        instruction=question,
        ideal_response=answer,
        retrieved_context=[
            {
                "path": "Characters/Individual/Example.md",
                "title": "Example",
                "type": "character",
                "visibility": "Jogadores",
            }
        ],
        source_note_ids=["Characters/Individual/Example.md"],
        source_note_hashes=["a" * 64],
        review_status="approved",
        reviewer="Sage",
        quality_score=2,
    )


class ColabPackageTests(unittest.TestCase):
    def test_acknowledgement_is_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "approved.jsonl"
            write_jsonl(source, [approved("one", "Pergunta um?", "Resposta um."), approved("two", "Pergunta dois?", "Resposta dois.")])
            with self.assertRaises(RuntimeError):
                prepare_colab_package(Path(temporary) / "smoke.zip", approved=source)

    def test_package_is_sanitized_and_runner_dry_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "approved.jsonl"
            output = root / "smoke.zip"
            write_jsonl(source, [approved("one", "Pergunta um?", "Resposta um."), approved("two", "Pergunta dois?", "Resposta dois.")])
            report = prepare_colab_package(output, approved=source, acknowledgement=SMOKE_ACK)
            self.assertEqual(2, report["eligible"])
            self.assertFalse(report["training_started"])
            self.assertTrue(report["validation"]["valid"])
            with zipfile.ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn("colab/runner.py", archive.namelist())
                self.assertFalse(any(name.endswith(".md") for name in archive.namelist()))
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(CLASSIFICATION, manifest["classification"])
                self.assertFalse(manifest["production_eligible"])
                archive.extractall(root / "unpacked")
            dry_run = subprocess.run(
                [sys.executable, str(root / "unpacked/colab/runner.py"), "--package-root", str(root / "unpacked"), "--dry-run"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, dry_run.returncode, dry_run.stderr)
            self.assertIn('"training_started": false', dry_run.stdout)

    def test_experimental_package_has_twenty_updates_and_fixed_bootstrap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "approved.jsonl"
            output = root / "experimental.zip"
            rows = [approved(f"case-{index}", f"Pergunta {index}?", f"Resposta {index}.") for index in range(18)]
            write_jsonl(source, rows)
            report = prepare_experimental_colab_package(output, approved=source, acknowledgement=SMOKE_ACK)
            self.assertEqual(EXPERIMENTAL_CLASSIFICATION, report["classification"])
            self.assertEqual(20, report["expected_optimizer_updates"])
            with zipfile.ZipFile(output) as archive:
                manifest = json.loads(archive.read("manifest.json"))
                config = json.loads(archive.read("config/experimental-colab.json"))
                requirements = archive.read("requirements-colab.txt").decode("utf-8")
                runner = archive.read("colab/runner.py").decode("utf-8")
                training = archive.read("omnisvera_model/training.py").decode("utf-8")
                archive.extractall(root / "unpacked")
            self.assertEqual(5, config["epochs"])
            self.assertEqual(4, config["gradient_accumulation_steps"])
            self.assertEqual(16, config["lora_rank"])
            self.assertEqual(32, config["lora_alpha"])
            self.assertFalse(manifest["production_eligible"])
            self.assertNotIn("torchao==", requirements)
            self.assertIn('"uninstall", "-y", "torchao"', runner)
            self.assertIn("enable_input_require_grads", training)
            self.assertIn('gradient_checkpointing_kwargs={"use_reentrant": False}', training)
            self.assertIn("backward_preflight(model", training)
            dry_run = subprocess.run(
                [sys.executable, str(root / "unpacked/colab/runner.py"), "--package-root", str(root / "unpacked"), "--dry-run"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, dry_run.returncode, dry_run.stderr)
            payload = json.loads(dry_run.stdout)
            self.assertEqual(20, payload["optimizer_steps_expected"])
            self.assertFalse(payload["training_started"])


if __name__ == "__main__":
    unittest.main()
