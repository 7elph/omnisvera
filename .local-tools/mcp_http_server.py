from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server.fastmcp import FastMCP
import uvicorn

import mcp_server as local_core
from omnisvera_mcp.bridge import register_remote_bridge_tools


HOST = os.getenv("OMNISVERA_MCP_HTTP_HOST", "127.0.0.1")
PORT = int(os.getenv("OMNISVERA_MCP_HTTP_PORT", "8765"))
PATH = "/mcp"

mcp = FastMCP(
    "omnisvera-mia-bridge",
    host=HOST,
    port=PORT,
    streamable_http_path=PATH,
    stateless_http=True,
)
BRIDGE_BINDINGS = register_remote_bridge_tools(mcp, local_core.CORE_REGISTRY)


SERVER_URL = os.getenv("OMNISVERA_MCP_SERVER_URL", "http://127.0.0.1:8765")

# RFC 9728 OAuth 2.0 Protected Resource Metadata — required by MCP 2026 spec
# and probed by the OpenAI tunnel-client during startup.  A 404 here blocks
# tool discovery entirely.
PROTECTED_RESOURCE_METADATA = json.dumps(
    {
        "resource": f"{SERVER_URL}{PATH}",
        "authorization_servers": [],
        "scopes_supported": [
            "system.health.read",
            "vault.handoff.read",
            "companion.read",
            "memory.read",
            "memory.write",
            "world.read",
            "world.write",
            "epistemic.read",
            "epistemic.write",
            "epistemic.prediction.commit",
        ],
        "bearer_methods_supported": ["header"],
    },
    separators=(",", ":"),
).encode("utf-8")


class LegacyDiscoveryFallback:
    """Make the MCP 1.x HTTP server negotiate cleanly with MCP 2026 clients.

    Handles three concerns:
    1. ``/.well-known/oauth-protected-resource[/mcp]`` — RFC 9728 metadata
       required by the OpenAI tunnel for OAuth discovery.
    2. ``server/discover`` — MCP 2026 probe that legacy servers must answer
       with HTTP 404 so the client falls back to ``initialize``.
    3. Everything else — forwarded unchanged to the SDK.
    """

    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "GET")

        # --- RFC 9728 OAuth Protected Resource Metadata ---
        if method == "GET" and path in (
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp",
        ):
            await self._send_json(scope, receive, send, 200, PROTECTED_RESOURCE_METADATA)
            return

        # --- MCP 2026 server/discover probe ---
        if method == "POST" and path == PATH:
            chunks: list[bytes] = []
            while True:
                message = await receive()
                if message.get("type") != "http.request":
                    await self.app(scope, receive, send)
                    return
                chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    break

            body = b"".join(chunks)
            try:
                payload = json.loads(body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = None

            if isinstance(payload, dict) and payload.get("method") == "server/discover":
                response = json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": payload.get("id"),
                        "error": {"code": -32601, "message": "Method not found"},
                    },
                    separators=(",", ":"),
                ).encode("utf-8")
                await self._send_json(scope, receive, send, 404, response)
                return

            replayed = False

            async def replay_receive() -> dict[str, Any]:
                nonlocal replayed
                if not replayed:
                    replayed = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return await receive()

            await self.app(scope, replay_receive, send)
            return

        await self.app(scope, receive, send)

    async def _send_json(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
        status: int,
        body: bytes,
    ) -> None:
        # Drain any request body for non-POST (GET has no body, but be safe)
        if scope.get("method") == "POST":
            while True:
                message = await receive()
                if message.get("type") != "http.request":
                    break
                if not message.get("more_body", False):
                    break

        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def build_http_app() -> LegacyDiscoveryFallback:
    return LegacyDiscoveryFallback(mcp.streamable_http_app())


if __name__ == "__main__":
    uvicorn.run(build_http_app(), host=HOST, port=PORT, log_level="info")
