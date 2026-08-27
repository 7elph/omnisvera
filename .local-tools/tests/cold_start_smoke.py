from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


TESTS = Path(__file__).resolve().parent
LOCAL_TOOLS = TESTS.parent
ROOT = LOCAL_TOOLS.parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from test_mcp_core_cut1 import EXPECTED_SCHEMAS  # noqa: E402


def text_result(result) -> str:
    return "".join(
        block.text for block in result.content if getattr(block, "type", None) == "text"
    )


async def cold_start() -> dict[str, object]:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(LOCAL_TOOLS / "mcp_server.py")],
        cwd=str(ROOT),
    )
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            initialize_result = await session.initialize()
            listed = await session.list_tools()
            schemas = {tool.name: tool.inputSchema for tool in listed.tools}
            if {name: schemas.get(name) for name in EXPECTED_SCHEMAS} != EXPECTED_SCHEMAS:
                raise AssertionError("Cold-start tool schemas differ from the Cut 1 baseline")
            if "system.health" not in schemas:
                raise AssertionError("Cut 3 health tool missing after cold start")

            migration_result = await session.call_tool("get_migration_status", {})
            handoff_result = await session.call_tool("get_handoff", {})
            health_result = await session.call_tool("system.health", {})
            search_result = await session.call_tool(
                "semantic_search", {"query": "Nimalia", "limit": 2}
            )
            expected_migration = (ROOT / "Workflow" / "MIGRATION_LEDGER.md").read_text(
                encoding="utf-8-sig"
            )
            if text_result(migration_result) != expected_migration:
                raise AssertionError("Migrated tool output differs after cold start")
            handoff_text = text_result(handoff_result)
            if "handoff dinâmico" not in handoff_text or "Freshness:" not in handoff_text:
                raise AssertionError("Dynamic handoff missing evidence metadata after cold start")
            health = json.loads(text_result(health_result))
            if health["mcp_core"]["status"] != "healthy":
                raise AssertionError("MCP Core is not healthy after cold start")
            if "Territories/Nimalia.md" not in text_result(search_result):
                raise AssertionError("Resilient search failed after cold start")
            listed_resources = await session.list_resources()
            resource_uris = {str(resource.uri) for resource in listed_resources.resources}
            expected_resources = {"system://health", "omnisvera://handoff", "projects://companion/current"}
            if resource_uris != expected_resources:
                raise AssertionError("Cut 3 resources differ after cold start")
            resource = await session.read_resource("system://health")
            resource_health = json.loads(resource.contents[0].text)
            if resource_health["mcp_core"]["status"] != "healthy":
                raise AssertionError("Health resource unreadable after cold start")

            return {
                "server": initialize_result.serverInfo.name,
                "protocol_version": initialize_result.protocolVersion,
                "tools": [tool.name for tool in listed.tools],
                "schemas_match": True,
                "migrated_tool_match": True,
                "dynamic_handoff": True,
                "health": True,
                "resources": sorted(resource_uris),
                "offline_search_match": True,
            }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(cold_start()), ensure_ascii=False, indent=2))
