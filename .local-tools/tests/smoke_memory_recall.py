"""Real launcher/SDK smoke test. Reads operational memory; only audit may grow."""

from __future__ import annotations

import asyncio
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
ROOT = LOCAL_TOOLS.parent
DATABASE = ROOT / ".assistant-runtime/omnisvera-mcp/memory.db"
LOCAL_NAMES = {
    "get_handoff", "get_migration_status", "semantic_search", "assistant_status",
    "create_local_proposal", "audit_changed_notes", "system.health",
    "memory.get", "memory.list", "memory.search", "memory.recent",
}
REMOTE_NAMES = {
    "system.health", "get_handoff", "get_companion_state", "memory.get",
    "memory.list", "memory.search", "memory.recent",
}


def database_snapshot():
    with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as connection:
        data = {name: connection.execute(f"SELECT * FROM {name} ORDER BY id").fetchall()
                for name in ("memory_items", "memory_sources", "project_states")}
        audit_cursor = connection.execute("SELECT COALESCE(MAX(rowid),0) FROM audit_events").fetchone()[0]
    return data, audit_cursor


async def probe(session, *, remote):
    await session.initialize()
    tools = (await session.list_tools()).tools
    assert {tool.name for tool in tools} == (REMOTE_NAMES if remote else LOCAL_NAMES)
    for tool in tools:
        assert not ({"actor", "client", "transport", "scopes"} & tool.inputSchema["properties"].keys())

    async def call(name, args):
        result = await session.call_tool(name, args)
        assert not result.isError, result
        return json.loads(result.content[0].text)

    canon = await call("memory.get", {"memory_id": "C-001"})
    found = await call("memory.search", {"query": "Quais restrições existem para o canon?"})
    assert found == [canon]
    decisions = await call("memory.recent", {"item_type": "decision", "limit": 2})
    assert [item["id"] for item in decisions] == ["D-002", "D-001"]
    assert all(item["sources"] for item in decisions)
    invalid = await session.call_tool("memory.search", {"query": "canon", "limit": 0})
    assert invalid.isError
    if remote:
        forbidden = await session.call_tool("create_local_proposal", {"task": "blocked", "source_files": []})
        assert forbidden.isError
    print(json.dumps({"transport": "http" if remote else "stdio", "tools": len(tools),
                      "search_ids": [item["id"] for item in found],
                      "recent_ids": [item["id"] for item in decisions], "passed": True}))


async def stdio_probe():
    parameters = StdioServerParameters(command=sys.executable,
        args=[str(LOCAL_TOOLS / "mcp_server.py")], cwd=str(ROOT))
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await probe(session, remote=False)


async def http_probe():
    with closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    environment = {**os.environ, "OMNISVERA_MCP_HTTP_HOST": "127.0.0.1",
                   "OMNISVERA_MCP_HTTP_PORT": str(port)}
    with tempfile.TemporaryFile(mode="w+b") as log:
        process = subprocess.Popen(
            [sys.executable, str(LOCAL_TOOLS / "mcp_http_server.py")], cwd=ROOT,
            env=environment, stdout=log, stderr=log,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            for _ in range(150):
                if process.poll() is not None:
                    raise RuntimeError("HTTP launcher exited before becoming ready")
                try:
                    _, writer = await asyncio.open_connection("127.0.0.1", port)
                    writer.close()
                    await writer.wait_closed()
                    break
                except OSError:
                    await asyncio.sleep(.2)
            else:
                raise TimeoutError("HTTP launcher did not become ready in 30 seconds")
            async with streamablehttp_client(f"http://127.0.0.1:{port}/mcp") as (read, write, _):
                async with ClientSession(read, write) as session:
                    await probe(session, remote=True)
        finally:
            # Only the child owned by this smoke test is terminated; production stays up.
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


async def main():
    before, cursor = database_snapshot()
    await asyncio.wait_for(stdio_probe(), timeout=45)
    await asyncio.wait_for(http_probe(), timeout=45)
    after, _ = database_snapshot()
    assert after == before, "Memory/source/project data changed during read-only smoke"
    with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as connection:
        events = connection.execute(
            "SELECT actor,client,transport,result,metadata_json FROM audit_events "
            "WHERE rowid>? ORDER BY rowid", (cursor,),
        ).fetchall()
    for identity in (("sage", "codex", "stdio"), ("mia", "chatgpt-mia-bridge", "streamable-http")):
        observed = [(row[3], json.loads(row[4])["tool"]) for row in events if row[:3] == identity]
        assert observed == [("success", "memory.get"), ("success", "memory.search"),
                            ("success", "memory.recent"), ("error", "memory.search")], observed
    print(json.dumps({"data_unchanged": True, "audit_events": len(events), "passed": True}))


if __name__ == "__main__":
    asyncio.run(main())
