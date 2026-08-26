from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .core.context import CallContext
from .core.registry import RegisteredTool, ToolRegistry
from .tools.existing import migration_status_handler


ContextFactory = Callable[[], CallContext]


def register_foundation_tools(
    mcp: FastMCP,
    root: Path,
    *,
    context_factory: ContextFactory | None = None,
) -> tuple[Callable[[], str], ToolRegistry]:
    """Register the first migrated tool without changing its public schema."""

    registry = ToolRegistry()
    registry.register(
        RegisteredTool(
            name="get_migration_status",
            handler=migration_status_handler(root),
            action="read",
            resource="omnisvera://migration/status",
            required_scopes=frozenset({"vault.migration.read"}),
        )
    )
    make_context = context_factory or CallContext.trusted_local_stdio

    @mcp.tool()
    def get_migration_status() -> str:
        """Retorna o registro versionado da migração de Disgraceland para Omnisvera."""
        return registry.invoke("get_migration_status", make_context(), {})

    return get_migration_status, registry
