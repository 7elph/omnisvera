from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from omnisvera_mcp import register_foundation_tools


ROOT = Path(__file__).resolve().parents[1]
mcp = FastMCP("omnisvera-local")
TOOL_BINDINGS, CORE_REGISTRY, SEARCH_COORDINATOR = register_foundation_tools(mcp, ROOT)
get_handoff = TOOL_BINDINGS.get_handoff
get_migration_status = TOOL_BINDINGS.get_migration_status
semantic_search = TOOL_BINDINGS.semantic_search
assistant_status = TOOL_BINDINGS.assistant_status
create_local_proposal = TOOL_BINDINGS.create_local_proposal
audit_changed_notes = TOOL_BINDINGS.audit_changed_notes
system_health = TOOL_BINDINGS.system_health
memory_get = TOOL_BINDINGS.memory_get
memory_list = TOOL_BINDINGS.memory_list
memory_search = TOOL_BINDINGS.memory_search
memory_recent = TOOL_BINDINGS.memory_recent
CORE_SERVICES = CORE_REGISTRY.services


if __name__ == "__main__":
    mcp.run(transport="stdio")
