"""Read-only OpenCode stdio facade; same registry/handlers as the MIA bridge."""
from uuid import uuid4

from mcp.server.fastmcp import FastMCP

import mcp_server as local_core
from omnisvera_mcp.bridge import register_remote_bridge_tools
from omnisvera_mcp.core.context import CallContext


def opencode_context() -> CallContext:
    return CallContext(
        actor="sage",
        client="opencode",
        transport="stdio",
        scopes=frozenset(
            {"system.health.read", "vault.handoff.read", "companion.read", "memory.read"}
        ),
        request_id=uuid4().hex,
        project_id="omnisvera",
    )


mcp = FastMCP("omnisvera-opencode")
BRIDGE_BINDINGS = register_remote_bridge_tools(
    mcp, local_core.CORE_REGISTRY, context_factory=opencode_context
)

if __name__ == "__main__":
    mcp.run(transport="stdio")
