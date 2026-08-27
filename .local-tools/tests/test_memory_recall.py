from __future__ import annotations

import asyncio
import copy
import json
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

from mcp.server.fastmcp import FastMCP
from omnisvera_mcp.bridge import register_remote_bridge_tools, remote_bridge_context
from omnisvera_mcp.core import AuthorizationDenied, CallContext
from omnisvera_mcp.memory.bootstrap import MEMORY_SEED_V0_1, apply_bootstrap
from omnisvera_mcp.server import register_foundation_tools


class MemoryRecallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.mcp = FastMCP("recall-test")
        self.bindings, self.registry, _ = register_foundation_tools(
            self.mcp, Path(self.temporary.name),
        )
        self.store = self.registry.services["memory"]
        apply_bootstrap(self.store)
        self.remote = FastMCP("recall-remote-test")
        self.bridge = register_remote_bridge_tools(self.remote, self.registry)

    def seed(self, item_id, *, title="", content="", item_type="decision",
             updated_at="2026-08-27T00:00:00+00:00"):
        item = copy.deepcopy(MEMORY_SEED_V0_1[0])
        item.update(id=item_id, title=title, content=content, type=item_type,
                    updated_at=updated_at)
        self.store.apply_seed([item])

    def ids(self, query, **options):
        return [item["id"] for item in self.store.search_memories(query, **options)]

    def audit_rows(self):
        with closing(self.store._connect()) as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM audit_events")]

    def test_portuguese_question_and_accent_case_normalization(self):
        self.assertEqual(self.ids("Quais restrições existem para o CÂNON?"), ["C-001"])
        self.assertEqual(self.ids("mudancas REVERSÍVEIS"), ["H-001"])
        self.assertEqual(self.ids("tunel"), ["D-002"])

    def test_exact_id_and_exact_title_rank_first(self):
        self.seed("Z-001", title="Bridge", content="D-002")
        self.assertEqual(self.ids("d-002")[0], "D-002")
        self.assertEqual(self.ids("Bridge")[0], "Z-001")

    def test_coverage_then_title_hits_then_id_are_deterministic(self):
        self.seed("R-C", title="Alpha beta", content="")
        self.seed("R-B", title="Alpha", content="beta gamma")
        self.seed("R-A", title="Alpha", content="beta gamma")
        self.seed("R-D", title="Alpha beta gamma extra", content="")
        self.assertEqual(self.ids("alpha beta gamma"), ["R-D", "R-A", "R-B", "R-C"])
        self.assertEqual(self.ids("alpha beta gamma gamma"), self.ids("alpha beta gamma"))

    def test_partial_matches_are_allowed_but_substrings_are_not(self):
        self.assertEqual(self.ids("canon unicornio"), ["C-001"])
        self.assertEqual(self.ids("canonico"), [])

    def test_no_match_and_literal_sql_input_do_not_return_everything(self):
        self.assertEqual(self.ids("zzyyxxyy"), [])
        self.assertEqual(self.ids("%_'; SELECT * FROM memory_items; --"), [])
        self.assertEqual(self.ids("canon", item_type="constraint' OR 1=1 --"), [])
        self.assertEqual(self.store.stats()["counts"]["memory_items"], 4)

    def test_filter_and_limit_are_applied_after_ranking(self):
        self.assertEqual(self.ids("MCP", item_type="decision", limit=1), ["D-001"])
        self.assertEqual(self.ids("canon", item_type="decision"), [])
        self.assertEqual(self.ids("canon", item_type=" constraint "), ["C-001"])
        self.assertEqual(self.ids("canon", item_type=" "), ["C-001"])

    def test_search_does_not_pretruncate_collection_at_100(self):
        items = []
        for index in range(105):
            item = copy.deepcopy(MEMORY_SEED_V0_1[0])
            item.update(id=f"B-{index:03}", title="common", content="unrelated")
            items.append(item)
        items[-1]["title"] = "rare-needle"
        self.store.apply_seed(items)
        self.assertEqual(self.ids("rare needle", limit=1), ["B-104"])

    def test_invalid_queries_fail_explicitly(self):
        for query in (None, 15, "", "  ", "?!%", "de e para", "x" * 1001):
            with self.subTest(query=repr(query)[:30]), self.assertRaises(ValueError):
                self.store.search_memories(query)

    def test_invalid_options_fail_for_both_tools(self):
        for options in ({"limit": 0}, {"limit": 101}, {"limit": -1},
                        {"limit": True}, {"limit": 1.5}, {"limit": "2"},
                        {"item_type": 3}, {"item_type": "x" * 101}):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    self.store.search_memories("canon", **options)
                with self.assertRaises(ValueError):
                    self.store.recall_recent(**options)

    def test_recent_orders_by_updated_time_across_offsets_then_id(self):
        # A sorts later lexically but B is actually newer (15:00 UTC).
        self.seed("Z-B", updated_at="2026-09-01T12:00:00-03:00")
        self.seed("Z-A", updated_at="2026-09-01T14:00:00+00:00")
        self.seed("Z-C", updated_at="2026-09-01T15:00:00+00:00")
        recent = self.store.recall_recent(limit=3)
        self.assertEqual([item["id"] for item in recent], ["Z-B", "Z-C", "Z-A"])

    def test_recent_filters_and_returns_full_records(self):
        result = self.store.recall_recent(item_type="decision", limit=1)
        self.assertEqual(result, [self.store.get_memory("D-002")])
        self.assertEqual(self.store.recall_recent(item_type="unknown"), [])

    def test_results_preserve_all_metadata_and_provenance(self):
        found = self.store.search_memories("canon")[0]
        self.assertEqual(found, self.store.get_memory("C-001"))
        for field in ("id", "type", "namespace", "title", "content", "status",
                      "confidence", "owner", "classification", "created_at", "updated_at", "sources"):
            self.assertIn(field, found)
        self.assertEqual(len(found["sources"]), 2)

    def test_storage_reads_do_not_write_any_table(self):
        before = self.store.path.read_bytes()
        self.store.search_memories("canon")
        self.store.recall_recent()
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_new_rows_are_found_without_index_or_process_restart(self):
        self.assertEqual(self.ids("newword"), [])
        self.seed("NEW", title="newword")
        self.assertEqual(self.ids("newword"), ["NEW"])

    def test_registry_denies_before_storage_for_both_tools(self):
        denied = CallContext(actor="guest", client="test", transport="stdio",
                             scopes=frozenset({"companion.read"}), request_id="denied")
        with patch.object(self.store, "search_memories") as search, \
                patch.object(self.store, "recall_recent") as recent:
            for name, args in (("memory.search", {"query": "canon"}), ("memory.recent", {})):
                with self.assertRaises(AuthorizationDenied):
                    self.registry.invoke(name, denied, args)
            search.assert_not_called()
            recent.assert_not_called()
        self.assertEqual([row["result"] for row in self.audit_rows()], ["denied", "denied"])

    def test_identity_arguments_cannot_be_forged(self):
        for name in ("memory.search", "memory.recent"):
            for field in ("actor", "client", "scopes", "transport", "request_id"):
                with self.subTest(name=name, field=field), self.assertRaises(ValueError):
                    self.registry.invoke(name, remote_bridge_context(), {field: "forged"})

    def test_remote_and_stdio_use_same_handler_and_preserve_old_reads(self):
        expected = [self.store.get_memory("C-001")]
        self.assertEqual(json.loads(self.bridge.memory_search("canon")), expected)
        self.assertEqual(json.loads(self.bindings.memory_search("canon")), expected)
        self.assertEqual(self.bridge.memory_recent("decision", 1),
                         self.bindings.memory_recent("decision", 1))
        self.assertEqual(json.loads(self.bindings.memory_get("C-001")), expected[0])
        self.assertEqual(json.loads(self.bindings.memory_list("decision", 20)),
                         self.store.list_memories(item_type="decision"))

    def test_audit_is_sanitized_and_only_expected_table_changes(self):
        before = self.store.stats()["counts"]
        query = "canon PRIVATE_QUERY_123"
        self.bridge.memory_search(query)
        self.bridge.memory_recent()
        after = self.store.stats()["counts"]
        self.assertEqual(after, {**before, "audit_events": before["audit_events"] + 2})
        rows = self.audit_rows()
        for row, name in zip(rows, ("memory.search", "memory.recent")):
            self.assertEqual(row["actor"], "mia")
            self.assertEqual(row["client"], "chatgpt-mia-bridge")
            self.assertEqual(row["transport"], "streamable-http")
            self.assertEqual(row["result"], "success")
            self.assertEqual(row["target"], "memory://items")
            self.assertEqual(len(row["arguments_hash"]), 64)
            self.assertGreaterEqual(row["duration_ms"], 0)
            self.assertEqual(json.loads(row["metadata_json"]), {"tool": name})
        self.assertNotIn("PRIVATE_QUERY_123", json.dumps(rows))
        self.assertNotIn("fonte de verdade", json.dumps(rows))

    def test_validation_errors_are_audited_without_query_content(self):
        with self.assertRaises(ValueError):
            self.bridge.memory_search("SENSITIVE", limit=0)
        self.assertEqual(self.audit_rows()[0]["result"], "error")
        self.assertNotIn("SENSITIVE", json.dumps(self.audit_rows()))

    def test_public_schemas_and_explicit_remote_allowlist(self):
        local = {tool.name: tool.inputSchema for tool in asyncio.run(self.mcp.list_tools())}
        remote = {tool.name: tool for tool in asyncio.run(self.remote.list_tools())}
        self.assertEqual(set(remote), {"system.health", "get_handoff", "get_companion_state",
                                      "memory.get", "memory.list", "memory.search", "memory.recent"})
        for name in ("memory.search", "memory.recent"):
            self.assertEqual(local[name], remote[name].inputSchema)
            properties = local[name]["properties"]
            self.assertEqual(properties["limit"]["default"], 10)
            self.assertEqual(set(properties), {"item_type", "limit"} |
                             ({"query"} if name == "memory.search" else set()))
            self.assertTrue(remote[name].annotations.readOnlyHint)
            self.assertFalse(remote[name].annotations.destructiveHint)
            self.assertEqual(self.registry.get(name).required_scopes, frozenset({"memory.read"}))

    def test_fastmcp_calls_succeed_and_remote_writes_are_not_invocable(self):
        async def call():
            for name, args in (("memory.search", {"query": "canon"}), ("memory.recent", {})):
                result = await self.remote.call_tool(name, args)
                # FastMCP returns content plus optional structured content in this SDK.
                blocks = result[0] if isinstance(result, tuple) else result
                self.assertTrue(json.loads(blocks[0].text))
            for name in ("create_local_proposal", "audit_changed_notes", "memory.add", "memory.delete"):
                with self.assertRaises(Exception):
                    await self.remote.call_tool(name, {})
        asyncio.run(call())


if __name__ == "__main__":
    unittest.main()
