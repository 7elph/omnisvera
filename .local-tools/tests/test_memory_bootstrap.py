from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

from omnisvera_mcp.memory import MemoryConflictError, MemoryStore  # noqa: E402
from omnisvera_mcp.memory.bootstrap import MEMORY_SEED_V0_1, apply_bootstrap  # noqa: E402


class MemoryBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "memory.db"
        self.store = MemoryStore(self.path)

    def tearDown(self):
        self.temporary.cleanup()

    def test_seed_inserts_four_explicit_memories_with_verifiable_sources(self):
        result = apply_bootstrap(self.store)

        self.assertEqual(result, {"inserted": 4, "skipped": 0})
        counts = self.store.stats()["counts"]
        self.assertEqual(counts["memory_items"], 4)
        self.assertEqual(counts["memory_sources"], 8)
        # Bootstrap must not populate any later domain tables either.
        self.assertTrue(all(value == 0 for name, value in counts.items()
                            if name not in {"memory_items", "memory_sources"}))
        for seed in MEMORY_SEED_V0_1:
            item = self.store.get_memory(seed["id"])
            self.assertEqual(item["type"], seed["type"])
            self.assertEqual(item["status"], seed["status"])
            self.assertEqual(item["confidence"], seed["confidence"])
            self.assertEqual(item["owner"], seed["owner"])
            self.assertEqual(item["classification"], seed["classification"])
            self.assertEqual(item["created_at"], seed["created_at"])
            self.assertEqual(item["updated_at"], seed["updated_at"])
            self.assertTrue(all(source["source_ref"].startswith(("commit:", "doc:")) for source in item["sources"]))

    def test_second_execution_is_idempotent(self):
        apply_bootstrap(self.store)
        before = self.store.stats()["counts"]

        result = apply_bootstrap(self.store)

        self.assertEqual(result, {"inserted": 0, "skipped": 4})
        self.assertEqual(self.store.stats()["counts"], before)

    def test_conflicting_id_fails_atomically(self):
        self.store.add_memory(
            item_id="D-002",
            namespace="mia",
            item_type="decision",
            title="Conflicting decision",
            content="Different content",
        )

        with self.assertRaisesRegex(MemoryConflictError, "D-002"):
            apply_bootstrap(self.store)

        self.assertIsNone(self.store.get_memory("D-001"))
        self.assertEqual(self.store.stats()["counts"]["memory_items"], 1)

    def test_seed_does_not_change_project_state_or_audit(self):
        self.store.record_project_state(
            "companion", {"status": "healthy"}, source="companion.api", confidence=1.0, freshness="fresh"
        )
        before = self.store.stats()["counts"]

        apply_bootstrap(self.store)

        after = self.store.stats()["counts"]
        self.assertEqual(after["project_states"], before["project_states"])
        self.assertEqual(after["audit_events"], before["audit_events"])

    def test_duplicate_ids_are_rejected_before_writes(self):
        duplicate = [dict(MEMORY_SEED_V0_1[0]), dict(MEMORY_SEED_V0_1[0])]

        with self.assertRaisesRegex(ValueError, "duplicate IDs"):
            self.store.apply_seed(duplicate)

        with closing(sqlite3.connect(self.path)) as connection:
            count = connection.execute("SELECT COUNT(*) FROM memory_items").fetchone()[0]
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
