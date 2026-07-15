from __future__ import annotations

import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from omnisvera_model.behavior_seed import build_seed_rows, install_seed
from omnisvera_model.dataset import find_conflicts, find_duplicates, validate_rows
from omnisvera_model.io import read_jsonl
from omnisvera_model.io import read_json
from omnisvera_model.preflight import validate_training_config


class BehaviorSeedTests(unittest.TestCase):
    def test_seed_contains_exactly_thirty_two_safe_approved_examples(self):
        rows = build_seed_rows()
        self.assertEqual(32, len(rows))
        self.assertFalse(validate_rows(rows))
        self.assertTrue(all(row["review_status"] == "approved" for row in rows))
        self.assertTrue(all(not row["contains_canon"] and not row["contains_secret"] for row in rows))
        self.assertTrue(all(row["access_profile"] == "player" for row in rows))

    def test_seed_covers_all_behavior_targets_without_conflicts(self):
        rows = build_seed_rows()
        categories = Counter(row["category"] for row in rows)
        self.assertEqual(10, len(categories))
        self.assertFalse(find_duplicates(rows)[0])
        self.assertFalse(find_conflicts(rows))

    def test_install_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "seed.jsonl"
            first = install_seed(output)
            second = install_seed(output)
            self.assertEqual(32, first["created"])
            self.assertEqual(32, second["created"])
            self.assertEqual(32, len(read_jsonl(output)))

    def test_experimental_50_config_is_valid_and_conservative(self):
        config = read_json(ROOT / "omnisvera-model" / "config" / "experimental-50.json")
        self.assertFalse(validate_training_config(config))
        self.assertEqual(3, config["epochs"])
        self.assertEqual(0.0001, config["learning_rate"])
        self.assertTrue(config["experimental_only"])


if __name__ == "__main__":
    unittest.main()
