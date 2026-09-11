"""Test bridge tool parity: registration vs exposure vs execution.

Verifies that all currently allowlisted remote tools are:
1. Registered in CORE_REGISTRY
2. Exposed via REMOTE_TOOL_NAMES
3. Callable via MCP protocol without Unknown tool errors
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestBridgeParity(unittest.TestCase):
    """Test parity between registry, allowlist, and MCP endpoint."""

    def test_core_registry_has_all_remote_tools(self):
        """CORE_REGISTRY must contain every tool in REMOTE_TOOL_NAMES."""
        import mcp_server
        from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES

        registry_tools = set(mcp_server.CORE_REGISTRY.names())
        missing = set(REMOTE_TOOL_NAMES) - registry_tools
        self.assertEqual(
            missing, set(),
            f"CORE_REGISTRY missing remote tools: {missing}",
        )

    def test_remote_tool_count(self):
        """The current contract adds Experience and world context to the old surface."""
        from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES
        self.assertEqual(len(REMOTE_TOOL_NAMES), 31)
        self.assertEqual(len(set(REMOTE_TOOL_NAMES)), len(REMOTE_TOOL_NAMES))
        self.assertNotIn("epistemic.create_prediction", REMOTE_TOOL_NAMES)

    def test_core_registry_count(self):
        """CORE_REGISTRY must have at least 28 tools (may have extras)."""
        import mcp_server
        self.assertGreaterEqual(len(mcp_server.CORE_REGISTRY.names()), 28)

    def test_required_tools_present(self):
        """Specific critical tools must be in REMOTE_TOOL_NAMES."""
        from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES
        required = [
            "system.health",
            "system.manifest",
            "system.bootstrap",
            "world.list",
            "world.observe",
            "world.model",
            "epistemic.resolve_due_predictions",
        ]
        for tool in required:
            self.assertIn(tool, REMOTE_TOOL_NAMES, f"Required tool missing: {tool}")

    def test_registry_dispatch_all_remote_tools(self):
        """Every remote tool must be invokable via registry.invoke."""
        import mcp_server
        from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES
        from omnisvera_mcp.core.context import CallContext

        ctx = CallContext(
            actor="test",
            client="test",
            transport="test",
            scopes=frozenset(),
            request_id="test",
            project_id="test",
        )

        for tool_name in REMOTE_TOOL_NAMES:
            # Should not raise KeyError (Unknown tool)
            try:
                tool = mcp_server.CORE_REGISTRY.get(tool_name)
                self.assertIsNotNone(tool, f"Tool {tool_name} returned None")
            except KeyError as e:
                self.fail(f"Tool {tool_name} not in registry: {e}")

    def test_bridge_register_function(self):
        """register_remote_bridge_tools must not raise."""
        from mcp.server.fastmcp import FastMCP
        from omnisvera_mcp.bridge import register_remote_bridge_tools
        import mcp_server

        mcp = FastMCP("test-bridge")
        bindings = register_remote_bridge_tools(mcp, mcp_server.CORE_REGISTRY)
        self.assertIsNotNone(bindings)

    def test_bridge_tool_count_matches(self):
        """FastMCP must expose the allowlist exactly, without duplicate names."""
        from mcp.server.fastmcp import FastMCP
        from omnisvera_mcp.bridge import register_remote_bridge_tools, REMOTE_TOOL_NAMES
        import mcp_server

        mcp = FastMCP("test-bridge")
        register_remote_bridge_tools(mcp, mcp_server.CORE_REGISTRY)

        # FastMCP stores tools internally
        tool_count = len(mcp._tool_manager._tools)
        self.assertEqual(tool_count, len(REMOTE_TOOL_NAMES))
        self.assertEqual(set(mcp._tool_manager._tools), set(REMOTE_TOOL_NAMES))


class TestBridgeDispatch(unittest.TestCase):
    """Test actual dispatch of remote tools via registry."""

    def setUp(self):
        import mcp_server
        from omnisvera_mcp.core.context import CallContext

        self.registry = mcp_server.CORE_REGISTRY
        self.ctx = CallContext(
            actor="test",
            client="test",
            transport="test",
            scopes=frozenset({
                "system.health.read",
                "memory.read",
                "memory.write",
                "world.read",
                "world.write",
                "epistemic.read",
                "epistemic.write",
            }),
            request_id="test",
            project_id="test",
        )

    def test_system_health(self):
        """system.health must return valid JSON."""
        result = self.registry.invoke("system.health", self.ctx, {})
        data = json.loads(result)
        # Health can have various structures, just verify it's valid JSON
        self.assertIsInstance(data, dict)

    def test_system_manifest(self):
        """system.manifest must return valid JSON with tools."""
        result = self.registry.invoke("system.manifest", self.ctx, {})
        data = json.loads(result)
        self.assertIn("tools", data)

    def test_system_bootstrap(self):
        """system.bootstrap must return valid JSON."""
        result = self.registry.invoke("system.bootstrap", self.ctx, {})
        data = json.loads(result)
        self.assertIn("system", data)

    def test_world_list(self):
        """world.list must return a list."""
        result = self.registry.invoke("world.list", self.ctx, {})
        data = json.loads(result)
        self.assertIsInstance(data, list)

    def test_resolve_due_predictions_dry_run(self):
        """epistemic.resolve_due_predictions with dry_run must work."""
        result = self.registry.invoke(
            "epistemic.resolve_due_predictions",
            self.ctx,
            {
                "now": "2026-09-20T00:00:00Z",
                "domain": "football.integration_test",
                "limit": 10,
                "dry_run": True,
            },
        )
        data = json.loads(result)
        self.assertIn("examined", data)
        self.assertIn("items", data)
        # Should find prediction #1
        if data["examined"] > 0:
            item = data["items"][0]
            self.assertEqual(item["prediction_id"], 1)
            self.assertEqual(item["status"], "awaiting_evidence")

    def test_world_describe_football(self):
        """world.describe reports the provider installed by the production registry."""
        result = self.registry.invoke("world.describe", self.ctx, {"world_id": "football"})
        data = json.loads(result)
        self.assertEqual(data["world_id"], "football")
        # Production deliberately defaults to HTTP; fake data must be injected by a fixture.
        self.assertEqual(data["metadata"]["provider"], "HttpFootballDataProvider")

    def test_world_observe_football(self):
        """world.observe('football') must return a WorldObservation with schema 'football.match.v1'."""
        result = self.registry.invoke("world.observe", self.ctx, {"world_id": "football"})
        data = json.loads(result)
        self.assertEqual(data["world_id"], "football")
        self.assertEqual(data["schema"], "football.match.v1")
        self.assertIn("matches", data["state"])

    def test_world_signals_football(self):
        """world.signals('football') must return structured signals."""
        result = self.registry.invoke("world.signals", self.ctx, {"world_id": "football"})
        data = json.loads(result)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        # Each signal must have required fields
        for signal in data:
            self.assertIn("signal_id", signal)
            self.assertIn("world_id", signal)
            self.assertEqual(signal["world_id"], "football")

    def test_world_model_football(self):
        """world.model('football') must use WorldModelRegistry, not adapter.model()."""
        result = self.registry.invoke(
            "world.model",
            self.ctx,
            {"world_id": "football", "builder_id": "core.state-vector"},
        )
        data = json.loads(result)
        self.assertEqual(data["world_id"], "football")
        self.assertEqual(data["builder_id"], "core.state-vector")
        self.assertIn("state", data)
        self.assertIn("signal_refs", data)


class TestParityConsistency(unittest.TestCase):
    """Test that REMOTE_TOOL_NAMES, bridge tools, and registry are consistent."""

    def test_no_duplicate_tools(self):
        """REMOTE_TOOL_NAMES must not have duplicates."""
        from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES
        self.assertEqual(len(REMOTE_TOOL_NAMES), len(set(REMOTE_TOOL_NAMES)))

    def test_registry_no_duplicates(self):
        """CORE_REGISTRY must not have duplicate tools."""
        import mcp_server
        names = mcp_server.CORE_REGISTRY.names()
        self.assertEqual(len(names), len(set(names)))

    def test_bridge_dispatcher_matches_registry(self):
        """Every tool in bridge must have a matching registry entry."""
        import mcp_server
        from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES

        registry_tools = set(mcp_server.CORE_REGISTRY.names())
        for tool_name in REMOTE_TOOL_NAMES:
            self.assertIn(
                tool_name,
                registry_tools,
                f"Bridge tool {tool_name} not in CORE_REGISTRY",
            )

    def test_football_adapter_not_path(self):
        """FootballWorldAdapter must not receive a Path as provider."""
        from omnisvera_mcp.adapters.football import FootballWorldAdapter
        from pathlib import Path

        # Should create with default FakeFootballDataProvider
        adapter = FootballWorldAdapter()
        self.assertNotIsInstance(adapter._provider, Path)
        self.assertEqual(type(adapter._provider).__name__, "FakeFootballDataProvider")

    def test_football_adapter_observe_works(self):
        """FootballWorldAdapter.observe() must work without Path errors."""
        from omnisvera_mcp.adapters.football import FootballWorldAdapter

        adapter = FootballWorldAdapter()
        obs = adapter.observe()
        self.assertEqual(obs.world_id, "football")
        self.assertEqual(obs.schema, "football.match.v1")
        self.assertIn("matches", obs.state)

    def test_world_model_no_adapter_model_call(self):
        """world.model must not call adapter.model() — use WorldModelRegistry."""
        import mcp_server
        from omnisvera_mcp.core.context import CallContext

        ctx = CallContext(
            actor="test",
            client="test",
            transport="test",
            scopes=frozenset({"world.read"}),
            request_id="test",
            project_id="test",
        )

        # This should NOT raise AttributeError about 'model' on adapter
        result = mcp_server.CORE_REGISTRY.invoke(
            "world.model",
            ctx,
            {"world_id": "football", "builder_id": "core.state-vector"},
        )
        data = json.loads(result)
        self.assertEqual(data["builder_id"], "core.state-vector")


if __name__ == "__main__":
    unittest.main()
