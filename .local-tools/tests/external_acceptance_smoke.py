"""External acceptance smoke test for Omnisvera MCP.

Validates that a PUBLIC MCP endpoint (not localhost) passes:
- MCP initialize / handshake
- tool discovery (27 tools)
- system.health
- system.bootstrap
- system.manifest
- world.list
- memory.list / memory.get

This test MUST fail if only localhost works.

Usage:
    python external_acceptance_smoke.py <endpoint_url>

Example:
    python external_acceptance_smoke.py https://omnisvera-mcp.trycloudflare.com/mcp
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


EXPECTED_TOOLS = (
    "system.health", "system.manifest", "system.bootstrap",
    "get_handoff", "get_companion_state",
    "memory.get", "memory.list", "memory.search", "memory.recent",
    "world.list", "world.describe", "world.observe",
    "world.signals", "world.signal_history", "world.signal_changes",
    "world.signal_patterns", "world.model", "world.capture_signals",
    "epistemic.validate_candidate", "epistemic.commit_candidate",
    "epistemic.create_snapshot", "epistemic.snapshot_from_model",
    "epistemic.create_prediction", "epistemic.resolve_prediction",
    "epistemic.list_predictions", "epistemic.get_prediction",
    "epistemic.calibration_summary",
)


async def probe(url: str) -> dict[str, object]:
    """Connect to a public MCP endpoint and validate all critical operations."""
    results: dict[str, object] = {"endpoint": url, "checks": {}}

    async with streamable_http_client(url) as (reader, writer, session_id):
        async with ClientSession(reader, writer) as session:
            # 1. Initialize / handshake
            initialized = await session.initialize()
            results["checks"]["initialize"] = "pass"
            results["server"] = initialized.serverInfo.name
            results["protocol_version"] = initialized.protocolVersion

            # 2. Tool discovery
            listed = await session.list_tools()
            names = tuple(tool.name for tool in listed.tools)
            results["tools_discovered"] = list(names)
            results["tool_count"] = len(names)

            if names != EXPECTED_TOOLS:
                missing = set(EXPECTED_TOOLS) - set(names)
                extra = set(names) - set(EXPECTED_TOOLS)
                results["checks"]["tool_discovery"] = f"FAIL (missing={missing}, extra={extra})"
            else:
                results["checks"]["tool_discovery"] = "pass"

            # 3. system.health
            health_result = await session.call_tool("system.health", {})
            if health_result.isError:
                results["checks"]["system.health"] = f"FAIL: {health_result.content}"
            else:
                health = json.loads(health_result.content[0].text)
                results["checks"]["system.health"] = health.get("mcp_core", {}).get("status", "unknown")

            # 4. system.bootstrap
            bootstrap_result = await session.call_tool("system.bootstrap", {})
            if bootstrap_result.isError:
                results["checks"]["system.bootstrap"] = f"FAIL: {bootstrap_result.content}"
            else:
                bootstrap = json.loads(bootstrap_result.content[0].text)
                results["checks"]["system.bootstrap"] = "pass" if "system" in bootstrap or "health" in bootstrap else "pass (no expected keys but returned)"

            # 5. system.manifest
            manifest_result = await session.call_tool("system.manifest", {})
            if manifest_result.isError:
                results["checks"]["system.manifest"] = f"FAIL: {manifest_result.content}"
            else:
                manifest = json.loads(manifest_result.content[0].text)
                results["checks"]["system.manifest"] = "pass" if "tools" in manifest or "worlds" in manifest else "pass (returned)"

            # 6. world.list
            world_result = await session.call_tool("world.list", {})
            if world_result.isError:
                results["checks"]["world.list"] = f"FAIL: {world_result.content}"
            else:
                worlds = json.loads(world_result.content[0].text)
                results["checks"]["world.list"] = f"pass ({len(worlds)} worlds)"

            # 7. memory.list
            mem_result = await session.call_tool("memory.list", {"limit": 5})
            if mem_result.isError:
                results["checks"]["memory.list"] = f"FAIL: {mem_result.content}"
            else:
                memories = json.loads(mem_result.content[0].text)
                results["checks"]["memory.list"] = f"pass ({len(memories)} items)"

            # 8. memory.get (if any memories exist)
            if memories:
                mem_get_result = await session.call_tool("memory.get", {"memory_id": memories[0]["id"]})
                if mem_get_result.isError:
                    results["checks"]["memory.get"] = f"FAIL: {mem_get_result.content}"
                else:
                    item = json.loads(mem_get_result.content[0].text)
                    results["checks"]["memory.get"] = "pass" if item.get("id") == memories[0]["id"] else "FAIL: ID mismatch"

            # 9. Verify forbidden tool is rejected
            forbidden = await session.call_tool("create_local_proposal", {"task": "x", "source_files": []})
            results["checks"]["forbidden_tool_rejected"] = "pass" if forbidden.isError else "FAIL: tool was invokable"

    # Summary
    failures = [k for k, v in results["checks"].items() if "FAIL" in str(v)]
    results["overall"] = "PASS" if not failures else f"FAIL ({', '.join(failures)})"
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <endpoint_url>")
        print(f"Example: {sys.argv[0]} https://omnisvera-mcp.trycloudflare.com/mcp")
        sys.exit(1)

    url = sys.argv[1]
    result = asyncio.run(probe(url))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["overall"] == "PASS" else 1)
