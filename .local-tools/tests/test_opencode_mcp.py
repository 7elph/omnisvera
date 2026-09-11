from __future__ import annotations

import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOCAL_TOOLS))

import mcp_opencode_server as facade
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES

WRITE_TOOL_NAMES = {
    "world.capture_signals",
    "epistemic.commit_candidate",
    "epistemic.create_snapshot",
    "epistemic.snapshot_from_model",
    "epistemic.create_prediction",
    "epistemic.resolve_prediction",
    "epistemic.resolve_due_predictions",
}


class OpenCodeMcpTests(unittest.TestCase):
    def test_allowlist_and_identity_are_internal(self):
        tools = asyncio.run(facade.mcp.list_tools())
        self.assertCountEqual([tool.name for tool in tools], REMOTE_TOOL_NAMES)
        for tool in tools:
            self.assertEqual(tool.annotations.readOnlyHint, tool.name not in WRITE_TOOL_NAMES)
            self.assertFalse(tool.annotations.destructiveHint)
            for forbidden in ("actor", "client", "scopes", "transport"):
                self.assertNotIn(forbidden, tool.inputSchema.get("properties", {}))

    def test_context_is_distinct_and_read_only(self):
        context = facade.opencode_context()
        self.assertEqual((context.actor, context.client, context.transport), ("sage", "opencode", "stdio"))
        self.assertNotIn("*", context.scopes)
        self.assertNotIn("vault.propose", context.scopes)
        self.assertNotIn("vault.audit", context.scopes)
        self.assertNotEqual(context.request_id, facade.opencode_context().request_id)

    def test_calls_reuse_registry_with_opencode_identity(self):
        with patch.object(facade.local_core.CORE_REGISTRY, "invoke", return_value="[]") as invoke:
            self.assertEqual(facade.BRIDGE_BINDINGS.memory_list("decision", 5), "[]")
        name, context, arguments = invoke.call_args.args
        self.assertEqual(name, "memory.list")
        self.assertEqual(context.client, "opencode")
        self.assertEqual(arguments, {"item_type": "decision", "limit": 5})

    def test_cold_start_discovery_read_and_write_denial(self):
        async def probe():
            params = StdioServerParameters(
                command=sys.executable,
                args=[str(LOCAL_TOOLS / "mcp_opencode_server.py")],
                cwd=str(LOCAL_TOOLS.parent),
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    discovered = await session.list_tools()
                    self.assertCountEqual([tool.name for tool in discovered.tools], REMOTE_TOOL_NAMES)
                    result = await session.call_tool("memory.list", {"limit": 5})
                    self.assertFalse(result.isError)
                    self.assertIsInstance(json.loads(result.content[0].text), list)
                    forbidden = await session.call_tool("create_local_proposal", {"task": "not allowed", "source_files": []})
                    self.assertTrue(forbidden.isError)
                    denied_write = await session.call_tool(
                        "world.capture_signals", {"world_id": "companion.session", "signals": []}
                    )
                    self.assertTrue(denied_write.isError)
        asyncio.run(asyncio.wait_for(probe(), timeout=40))


if __name__ == "__main__":
    unittest.main()
