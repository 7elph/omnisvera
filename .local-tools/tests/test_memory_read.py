from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

from omnisvera_mcp.core import CallContext, RegisteredTool, ToolRegistry  # noqa: E402
from omnisvera_mcp.core.policy import AuthorizationDenied  # noqa: E402
from omnisvera_mcp.memory import MemoryStore, SQLiteAuditSink  # noqa: E402
from omnisvera_mcp.memory.bootstrap import apply_bootstrap  # noqa: E402


class MemoryReadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "memory.db"
        self.store = MemoryStore(self.path)
        apply_bootstrap(self.store)

    def tearDown(self):
        self.temporary.cleanup()

    def test_get_returns_content_and_provenance(self):
        item = self.store.get_memory("D-001")

        self.assertEqual(item["id"], "D-001")
        self.assertEqual(item["type"], "decision")
        self.assertIn("6100a10", item["content"])
        self.assertEqual(item["status"], "accepted")
        self.assertEqual(item["confidence"], 1.0)
        self.assertEqual(item["owner"], "omnisvera")
        self.assertEqual(item["classification"], "internal")
        self.assertEqual(len(item["sources"]), 2)

    def test_list_filters_by_type_and_has_full_records(self):
        decisions = self.store.list_memories(item_type="decision", limit=20)

        self.assertEqual({item["id"] for item in decisions}, {"D-001", "D-002"})
        self.assertTrue(all(item["content"] and item["sources"] for item in decisions))

    def test_list_limit_is_bounded(self):
        self.assertEqual(len(self.store.list_memories(limit=1)), 1)
        self.assertEqual(len(self.store.list_memories(limit=0)), 1)

    def test_policy_denies_memory_without_scope(self):
        registry = ToolRegistry()
        registry.register(RegisteredTool(
            "memory.get",
            lambda _context, _arguments: json.dumps(self.store.get_memory("D-001")),
            "read",
            "memory://items",
            frozenset({"memory.read"}),
        ))
        context = CallContext(
            actor="guest",
            client="test",
            transport="test",
            scopes=frozenset({"companion.read"}),
            request_id="memory-denied",
        )

        with self.assertRaises(AuthorizationDenied):
            registry.invoke("memory.get", context, {"memory_id": "D-001"})

    def test_audit_records_identity_and_tool_without_copying_memory_content(self):
        registry = ToolRegistry(audit=SQLiteAuditSink(self.store))
        registry.register(RegisteredTool(
            "memory.get",
            lambda _context, arguments: json.dumps(self.store.get_memory(arguments["memory_id"])),
            "read",
            "memory://items",
            frozenset({"memory.read"}),
        ))
        context = CallContext(
            actor="mia",
            client="test-bridge",
            transport="streamable-http",
            scopes=frozenset({"memory.read"}),
            request_id="memory-audit",
        )

        registry.invoke("memory.get", context, {"memory_id": "D-001"})

        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute(
                "SELECT actor,client,target,result,arguments_hash,metadata_json FROM audit_events"
            ).fetchone()
        self.assertEqual(row[:4], ("mia", "test-bridge", "memory://items", "success"))
        self.assertEqual(len(row[4]), 64)
        self.assertEqual(json.loads(row[5]), {"tool": "memory.get"})
        self.assertNotIn("6100a10", row[5])


if __name__ == "__main__":
    unittest.main()
