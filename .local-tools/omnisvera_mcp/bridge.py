from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .core.context import CallContext
from .core.registry import RegisteredTool, ToolRegistry


ContextFactory = Callable[[], CallContext]
REMOTE_TOOL_NAMES = ("system.health", "get_handoff", "get_companion_state")
READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


@dataclass(frozen=True, slots=True)
class BridgeBindings:
    system_health: Callable[[], str]
    get_handoff: Callable[[], str]
    get_companion_state: Callable[[], str]


def remote_bridge_context() -> CallContext:
    """Identity injected by the HTTP launcher, never supplied by the client."""

    return CallContext(
        actor="mia",
        client="chatgpt-mia-bridge",
        transport="streamable-http",
        scopes=frozenset(
            {"system.health.read", "vault.handoff.read", "companion.read"}
        ),
        request_id=uuid4().hex,
        project_id="omnisvera",
    )


def _register_companion_reader(registry: ToolRegistry) -> None:
    try:
        registry.get("get_companion_state")
        return
    except KeyError:
        pass

    companion = registry.services["companion"]

    def read_companion(
        _context: CallContext,
        _arguments: Mapping[str, Any],
    ) -> str:
        return json.dumps(
            companion.get_dashboard().as_dict(),
            ensure_ascii=False,
            indent=2,
        )

    registry.register(
        RegisteredTool(
            "get_companion_state",
            read_companion,
            "read",
            "projects://companion/current",
            frozenset({"companion.read"}),
        )
    )


def register_remote_bridge_tools(
    mcp: FastMCP,
    registry: ToolRegistry,
    *,
    context_factory: ContextFactory = remote_bridge_context,
) -> BridgeBindings:
    """Expose only the read-only Proof-of-Connection allowlist."""

    _register_companion_reader(registry)

    @mcp.tool(name="system.health", annotations=READ_ONLY)
    def system_health() -> str:
        """Read current Omnisvera subsystem health and freshness."""

        return registry.invoke("system.health", context_factory(), {})

    @mcp.tool(name="get_handoff", annotations=READ_ONLY)
    def get_handoff() -> str:
        """Read the current dynamic Omnisvera handoff."""

        return registry.invoke("get_handoff", context_factory(), {})

    @mcp.tool(name="get_companion_state", annotations=READ_ONLY)
    def get_companion_state() -> str:
        """Read the current Companion session/dashboard state."""

        return registry.invoke("get_companion_state", context_factory(), {})

    return BridgeBindings(system_health, get_handoff, get_companion_state)
