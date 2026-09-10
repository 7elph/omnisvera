from __future__ import annotations

import asyncio
import inspect
import json
import sys
import unittest
from pathlib import Path


LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

import mcp_http_server  # noqa: E402
import mcp_server  # noqa: E402
from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES, remote_bridge_context  # noqa: E402

WRITE_TOOL_NAMES = {
    "world.capture_signals",
    "epistemic.commit_candidate",
    "epistemic.create_snapshot",
    "epistemic.snapshot_from_model",
    "epistemic.create_prediction",
    "epistemic.resolve_prediction",
}


class BridgeContractTests(unittest.TestCase):
    def test_remote_discovery_is_exactly_the_bounded_allowlist(self) -> None:
        tools = asyncio.run(mcp_http_server.mcp.list_tools())
        self.assertEqual(tuple(tool.name for tool in tools), REMOTE_TOOL_NAMES)
        for tool in tools:
            self.assertEqual(tool.annotations.readOnlyHint, tool.name not in WRITE_TOOL_NAMES)
            self.assertEqual(tool.annotations.idempotentHint, tool.name not in WRITE_TOOL_NAMES)
        self.assertTrue(all(tool.annotations.destructiveHint is False for tool in tools))

    def test_effectful_local_tools_are_not_registered_remotely(self) -> None:
        tools = asyncio.run(mcp_http_server.mcp.list_tools())
        names = {tool.name for tool in tools}
        self.assertNotIn("create_local_proposal", names)
        self.assertNotIn("audit_changed_notes", names)
        self.assertNotIn("semantic_search", names)
        self.assertNotIn("memory.add", names)
        self.assertNotIn("memory.update", names)
        self.assertNotIn("memory.delete", names)

    def test_remote_context_is_internal_and_distinct_in_audit(self) -> None:
        context = remote_bridge_context()
        self.assertEqual(context.actor, "mia")
        self.assertEqual(context.client, "chatgpt-mia-bridge")
        self.assertEqual(context.transport, "streamable-http")
        schemas = repr([
            tool.inputSchema for tool in asyncio.run(mcp_http_server.mcp.list_tools())
        ])
        for forbidden in ("actor", "client", "transport", "scopes", "request_id"):
            self.assertNotIn(forbidden, schemas)

    def test_remote_bindings_have_no_client_identity_arguments(self) -> None:
        self.assertEqual(str(inspect.signature(mcp_http_server.BRIDGE_BINDINGS.system_health)), "() -> 'str'")
        self.assertEqual(str(inspect.signature(mcp_http_server.BRIDGE_BINDINGS.get_handoff)), "() -> 'str'")
        self.assertEqual(str(inspect.signature(mcp_http_server.BRIDGE_BINDINGS.get_companion_state)), "() -> 'str'")
        self.assertEqual(str(inspect.signature(mcp_http_server.BRIDGE_BINDINGS.memory_get)), "(memory_id: 'str') -> 'str'")
        self.assertEqual(str(inspect.signature(mcp_http_server.BRIDGE_BINDINGS.memory_list)), "(item_type: 'str | None' = None, limit: 'int' = 20) -> 'str'")

    def test_remote_calls_reuse_core_registry_and_typed_companion_result(self) -> None:
        health = json.loads(mcp_http_server.BRIDGE_BINDINGS.system_health())
        companion = json.loads(mcp_http_server.BRIDGE_BINDINGS.get_companion_state())
        self.assertEqual(health["mcp_core"]["status"], "healthy")
        self.assertIn(companion["status"], {"healthy", "offline", "degraded", "unavailable"})
        self.assertEqual(
            mcp_server.CORE_REGISTRY.get("get_companion_state").resource,
            "projects://companion/current",
        )

    def test_remote_memory_read_returns_persisted_content_and_sources(self) -> None:
        memories = json.loads(mcp_http_server.BRIDGE_BINDINGS.memory_list(None, 20))

        self.assertIsInstance(memories, list)
        self.assertEqual(mcp_server.CORE_REGISTRY.get("memory.get").resource, "memory://items")
        self.assertEqual(mcp_server.CORE_REGISTRY.get("memory.list").resource, "memory://items")
        self.assertIn("memory.read", remote_bridge_context().scopes)
        self.assertIn("memory.write", remote_bridge_context().scopes)


if __name__ == "__main__":
    unittest.main()
