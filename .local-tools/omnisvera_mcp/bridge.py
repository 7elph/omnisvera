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
REMOTE_TOOL_NAMES = (
    "system.health",
    "get_handoff",
    "get_companion_state",
    "memory.get",
    "memory.list",
    "memory.search",
    "memory.recent",
)
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
    memory_get: Callable[[str], str]
    memory_list: Callable[[str | None, int], str]
    memory_search: Callable[[str, str | None, int], str]
    memory_recent: Callable[[str | None, int], str]


def remote_bridge_context() -> CallContext:
    """Identity injected by the HTTP launcher, never supplied by the client."""

    return CallContext(
        actor="mia",
        client="chatgpt-mia-bridge",
        transport="streamable-http",
        scopes=frozenset(
            {"system.health.read", "vault.handoff.read", "companion.read", "memory.read"}
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

    @mcp.tool(name="memory.get", annotations=READ_ONLY)
    def memory_get(memory_id: str) -> str:
        """Read one persistent memory by stable ID, including provenance."""

        return registry.invoke("memory.get", context_factory(), {"memory_id": memory_id})

    @mcp.tool(name="memory.list", annotations=READ_ONLY)
    def memory_list(item_type: str | None = None, limit: int = 20) -> str:
        """List persistent memories, optionally filtered by type."""

        return registry.invoke(
            "memory.list",
            context_factory(),
            {"item_type": item_type, "limit": limit},
        )

    @mcp.tool(name="memory.search", annotations=READ_ONLY)
    def memory_search(query: str, item_type: str | None = None, limit: int = 10) -> str:
        """Lexical search of memory ID/title/content, including provenance.

        Case/accent insensitive; no semantic synonyms. Limit: 1–100.
        """
        return registry.invoke(
            "memory.search", context_factory(),
            {"query": query, "item_type": item_type, "limit": limit},
        )

    @mcp.tool(name="memory.recent", annotations=READ_ONLY)
    def memory_recent(item_type: str | None = None, limit: int = 10) -> str:
        """Read full memories by updated_at descending, then stable ID. Limit: 1–100."""
        return registry.invoke(
            "memory.recent", context_factory(), {"item_type": item_type, "limit": limit},
        )

    return BridgeBindings(
        system_health, get_handoff, get_companion_state, memory_get, memory_list,
        memory_search, memory_recent,
    )
