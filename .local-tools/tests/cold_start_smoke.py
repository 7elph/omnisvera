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
            if schemas != EXPECTED_SCHEMAS:
                raise AssertionError("Cold-start tool schemas differ from the Cut 1 baseline")

            migration_result = await session.call_tool("get_migration_status", {})
            handoff_result = await session.call_tool("get_handoff", {})
            expected_migration = (ROOT / "Workflow" / "MIGRATION_LEDGER.md").read_text(
                encoding="utf-8-sig"
            )
            expected_handoff = (ROOT / "Workflow" / "ASSISTANT_HANDOFF.md").read_text(
                encoding="utf-8-sig"
            )
            if text_result(migration_result) != expected_migration:
                raise AssertionError("Migrated tool output differs after cold start")
            if text_result(handoff_result) != expected_handoff:
                raise AssertionError("Legacy tool output differs after cold start")

            return {
                "server": initialize_result.serverInfo.name,
                "protocol_version": initialize_result.protocolVersion,
                "tools": [tool.name for tool in listed.tools],
                "schemas_match": True,
                "migrated_tool_match": True,
                "legacy_tool_match": True,
            }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(cold_start()), ensure_ascii=False, indent=2))
