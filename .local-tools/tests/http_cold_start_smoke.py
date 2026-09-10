from __future__ import annotations

import asyncio
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


TESTS = Path(__file__).resolve().parent
LOCAL_TOOLS = TESTS.parent
ROOT = LOCAL_TOOLS.parent
DATABASE = ROOT / ".assistant-runtime" / "omnisvera-mcp" / "memory.db"
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

WRITE_TOOLS = {
    "world.capture_signals", "epistemic.commit_candidate",
    "epistemic.create_snapshot", "epistemic.snapshot_from_model",
    "epistemic.create_prediction", "epistemic.resolve_prediction",
}


def available_port() -> int:
    with closing(socket.socket()) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def wait_for_port(port: int, process: subprocess.Popen, timeout: float = 15) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"HTTP bridge exited during startup with {process.returncode}")
        with closing(socket.socket()) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise TimeoutError("HTTP bridge did not bind to localhost")


def audit_count() -> int:
    if not DATABASE.exists():
        return 0
    with closing(sqlite3.connect(DATABASE)) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0])


def latest_bridge_audit() -> tuple[str, str, str, str, str] | None:
    with closing(sqlite3.connect(DATABASE)) as connection:
        row = connection.execute(
            "SELECT actor,client,transport,target,result FROM audit_events "
            "WHERE transport='streamable-http' ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
    return tuple(row) if row else None


async def probe(url: str) -> dict[str, object]:
    async with streamable_http_client(url) as (reader, writer, _session_id):
        async with ClientSession(reader, writer) as session:
            initialized = await session.initialize()
            listed = await session.list_tools()
            names = tuple(tool.name for tool in listed.tools)
            if names != EXPECTED_TOOLS:
                raise AssertionError(f"Unexpected remote tools: {names}")
            if not all(
                tool.annotations
                and tool.annotations.readOnlyHint == (tool.name not in WRITE_TOOLS)
                for tool in listed.tools
            ):
                raise AssertionError("Remote read/write annotations do not match the bounded surface")

            health_result = await session.call_tool("system.health", {})
            health = json.loads(health_result.content[0].text)
            if health["mcp_core"]["status"] != "healthy":
                raise AssertionError("Remote system.health did not reach the Core")

            companion_result = await session.call_tool("get_companion_state", {})
            companion = json.loads(companion_result.content[0].text)
            if companion["status"] not in {"healthy", "offline", "degraded", "unavailable"}:
                raise AssertionError("Companion state is not typed")

            memories_result = await session.call_tool("memory.list", {"item_type": "decision", "limit": 20})
            memories = json.loads(memories_result.content[0].text)
            if not isinstance(memories, list):
                raise AssertionError("memory.list did not return a list")

            memory = None
            if memories:
                memory_result = await session.call_tool("memory.get", {"memory_id": memories[0]["id"]})
                memory = json.loads(memory_result.content[0].text)
                if memory["id"] != memories[0]["id"] or not memory["sources"]:
                    raise AssertionError("memory.get did not return content with provenance")

            forbidden = await session.call_tool(
                "create_local_proposal",
                {"task": "must-not-run", "source_files": []},
            )
            if not forbidden.isError:
                raise AssertionError("Forbidden tool was remotely invokable")

            return {
                "server": initialized.serverInfo.name,
                "protocol_version": initialized.protocolVersion,
                "tools": list(names),
                "health": health["mcp_core"]["status"],
                "companion": companion["status"],
                "memory": memory["id"] if memory else None,
                "memory_sources": len(memory["sources"]) if memory else 0,
                "forbidden_tool_rejected": True,
            }


def cold_start() -> dict[str, object]:
    port = available_port()
    before = audit_count()
    environment = os.environ.copy()
    environment["OMNISVERA_MCP_HTTP_HOST"] = "127.0.0.1"
    environment["OMNISVERA_MCP_HTTP_PORT"] = str(port)
    with tempfile.TemporaryDirectory() as temporary:
        log_path = Path(temporary) / "bridge.log"
        with log_path.open("w+", encoding="utf-8") as log:
            process = subprocess.Popen(
                [sys.executable, str(LOCAL_TOOLS / "mcp_http_server.py")],
                cwd=ROOT,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            try:
                wait_for_port(port, process)
                result = asyncio.run(probe(f"http://127.0.0.1:{port}/mcp"))
            finally:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            log.flush()
            if process.returncode not in {0, 1, 15}:
                raise RuntimeError(log_path.read_text(encoding="utf-8", errors="replace"))

    after = audit_count()
    audit = latest_bridge_audit()
    if after <= before:
        raise AssertionError("Remote calls did not append audit events")
    if audit != (
        "mia",
        "chatgpt-mia-bridge",
        "streamable-http",
        "memory://items",
        "success",
    ):
        raise AssertionError(f"Unexpected bridge audit identity: {audit}")
    return {**result, "audit_identity": list(audit), "audit_events_added": after - before}


if __name__ == "__main__":
    print(json.dumps(cold_start(), ensure_ascii=False, indent=2))
