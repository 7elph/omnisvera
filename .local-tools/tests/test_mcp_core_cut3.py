from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
from contextlib import closing
from pathlib import Path


LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

import mcp_server  # noqa: E402
from omnisvera_mcp.adapters import CompanionAdapter  # noqa: E402
from omnisvera_mcp.core import CallContext, RegisteredTool, ToolRegistry  # noqa: E402
from omnisvera_mcp.memory import MemoryStore, SQLiteAuditSink  # noqa: E402


class FakeResponse:
    def __init__(self, value, status=200):
        self.value = value
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.value).encode("utf-8")


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "memory.db"
        self.store = MemoryStore(self.path)

    def tearDown(self):
        self.temporary.cleanup()

    def test_schema_preserves_core_tables_and_versioned_domain_tables(self):
        identifier = self.store.add_memory(
            namespace="sage", item_type="decision", title="Boundary", content="Use API",
            sources=[{"source_type": "adr", "source_ref": "ADR-001", "relation": "supports"}],
        )
        memory = self.store.get_memory(identifier)
        with closing(sqlite3.connect(self.path)) as connection:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )}
        # The Experience/signal/prediction migrations extend, not replace, Cut 3.
        self.assertEqual(tables, {"memory_items", "memory_sources", "project_states", "audit_events",
                                 "predictions", "prediction_resolutions", "signal_observations",
                                 "scheduler_runs", "predictor_experiences", "experience_update_events"})
        self.assertEqual(memory["sources"][0]["source_ref"], "ADR-001")

    def test_equal_project_state_is_deduplicated(self):
        first = self.store.record_project_state("companion", {"online": False}, source="api", confidence=.4, freshness="unavailable")
        second = self.store.record_project_state("companion", {"online": False}, source="api", confidence=.4, freshness="unavailable")
        self.assertEqual(first, second)
        self.assertEqual(self.store.stats()["counts"]["project_states"], 1)

    def test_audit_stores_fingerprint_not_raw_arguments_or_output(self):
        registry = ToolRegistry(audit=SQLiteAuditSink(self.store))
        registry.register(RegisteredTool("probe", lambda _c, _a: "private-output", "read", "system://probe", frozenset()))
        registry.invoke("probe", CallContext.trusted_local_stdio(), {"token": "super-secret"})
        raw = self.path.read_bytes()
        self.assertNotIn(b"super-secret", raw)
        self.assertNotIn(b"private-output", raw)
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute("SELECT actor,client,result,length(arguments_hash) FROM audit_events").fetchone()
        self.assertEqual(row, ("sage", "codex", "success", 64))


class CompanionAdapterTests(unittest.TestCase):
    def test_authenticated_reads_use_only_get_and_real_endpoints(self):
        requests = []

        def opener(request, timeout):
            requests.append((request, timeout))
            if request.full_url.endswith("/gm/sessions"):
                return FakeResponse([{"id": 1, "status": "active"}])
            if request.full_url.endswith("/scenes/active"):
                return FakeResponse({"id": 9, "title": "Ruína"})
            return FakeResponse({"backend": "ok"})

        adapter = CompanionAdapter(Path.cwd(), base_url="http://companion.test", token="test-token", opener=opener)
        self.assertEqual(adapter.get_health().status, "healthy")
        self.assertEqual(adapter.get_dashboard().value["active_scene"]["id"], 9)
        self.assertEqual([request.get_method() for request, _ in requests], ["GET", "GET", "GET"])
        self.assertTrue(all(request.get_header("X-omnisvera-token") == "test-token" for request, _ in requests))
        self.assertEqual([request.full_url.removeprefix("http://companion.test") for request, _ in requests], ["/health", "/gm/sessions", "/scenes/active"])

    def test_offline_is_typed_degradation(self):
        def offline(_request, timeout):
            raise urllib.error.URLError("offline")

        observation = CompanionAdapter(Path.cwd(), token="x", opener=offline).get_app_state()
        self.assertEqual(observation.status, "offline")
        self.assertEqual(observation.freshness, "unavailable")
        self.assertIsNone(observation.value)


class IntegrationTests(unittest.TestCase):
    def test_system_health_keeps_core_healthy_when_companion_is_offline(self):
        result = json.loads(mcp_server.system_health())
        self.assertEqual(result["mcp_core"]["status"], "healthy")
        self.assertIn(result["companion"]["status"], {"healthy", "offline", "degraded", "unavailable"})
        self.assertIn("freshness", result["semantic_index"])

    def test_resources_are_useful_and_readable(self):
        resources = asyncio.run(mcp_server.mcp.list_resources())
        self.assertEqual(
            {str(resource.uri) for resource in resources},
            {"system://health", "omnisvera://handoff", "projects://companion/current"},
        )
        result = asyncio.run(mcp_server.mcp.read_resource("system://health"))
        text = result[0].content
        self.assertEqual(json.loads(text)["mcp_core"]["status"], "healthy")

    def test_dynamic_handoff_has_source_time_freshness_and_limitations(self):
        result = mcp_server.get_handoff()
        for marker in ("Generated:", "Source:", "Observed at:", "Confidence:", "Freshness:", "Limitations:"):
            self.assertIn(marker, result)
        self.assertNotEqual(result, (LOCAL_TOOLS.parent / "Workflow" / "ASSISTANT_HANDOFF.md").read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
