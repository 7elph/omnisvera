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

from omnisvera_model.colab import CLASSIFICATION, prepare_colab_package  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
