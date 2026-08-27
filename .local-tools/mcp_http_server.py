from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

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


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
