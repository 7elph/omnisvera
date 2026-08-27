from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .adapters.git import GitAdapter
from .adapters.companion import CompanionAdapter
from .adapters.vault import VaultAdapter
from .core.context import CallContext
from .core.handoff import HandoffService
from .core.health import HealthService
from .core.registry import RegisteredTool, ToolRegistry
from .memory import MemoryStore, SQLiteAuditSink
from .resources import RegisteredResource, ResourceRegistry
from .search.coordinator import SearchCoordinator
from .search.lexical import LexicalIndex
from .search.semantic import OllamaSemanticBackend
from .tools.existing import ExistingToolHandlers


ContextFactory = Callable[[], CallContext]


@dataclass(frozen=True, slots=True)
class ToolBindings:
    get_handoff: Callable[[], str]
    get_migration_status: Callable[[], str]
    semantic_search: Callable[[str, int], str]
    assistant_status: Callable[[], str]
    create_local_proposal: Callable[[str, list[str]], str]
    audit_changed_notes: Callable[[], str]
    system_health: Callable[[], str]
    memory_get: Callable[[str], str]
    memory_list: Callable[[str | None, int], str]


def register_foundation_tools(
    mcp: FastMCP,
    root: Path,
    *,
    context_factory: ContextFactory | None = None,
) -> tuple[ToolBindings, ToolRegistry, SearchCoordinator]:
    """Register all compatible tools through the Cut 2 Core invocation path."""

    root = root.resolve()
    vault = VaultAdapter(root)
    git = GitAdapter(root)
    lexical = LexicalIndex(
        vault,
        root / ".local-index" / "lexical-v1.json",
        semantic_index_path=root / ".local-index" / "vault.jsonl",
    )
    semantic = OllamaSemanticBackend(root / ".local-index" / "vault.jsonl")
    search = SearchCoordinator(lexical, semantic)
    search.refresh()
    memory = MemoryStore(root / ".assistant-runtime" / "omnisvera-mcp" / "memory.db")
    companion = CompanionAdapter(root)
    health = HealthService(root, vault, git, lexical, semantic, companion, memory)
    handoff = HandoffService(vault, git, companion, memory, health)
    handlers = ExistingToolHandlers(vault, git, search, handoff)
    audit = SQLiteAuditSink(memory)
    registry = ToolRegistry(audit=audit)

    def read_memory(_context: CallContext, arguments: dict) -> str:
        memory_id = str(arguments.get("memory_id", "")).strip()
        if not memory_id:
            raise ValueError("memory_id is required")
        item = memory.get_memory(memory_id)
        if item is None:
            raise ValueError(f"memory item not found: {memory_id}")
        return json.dumps(item, ensure_ascii=False, indent=2)

    def list_memory(_context: CallContext, arguments: dict) -> str:
        raw_type = arguments.get("item_type")
        item_type = str(raw_type).strip() if raw_type is not None else None
        if item_type == "":
            item_type = None
        limit = int(arguments.get("limit", 20))
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        return json.dumps(
            memory.list_memories(item_type=item_type, limit=limit),
            ensure_ascii=False,
            indent=2,
        )

    for tool in (
        RegisteredTool(
            "get_handoff",
            handlers.get_handoff,
            "read",
            "omnisvera://handoff",
            frozenset({"vault.handoff.read"}),
        ),
        RegisteredTool(
            "get_migration_status",
            handlers.get_migration_status,
            "read",
            "omnisvera://migration/status",
            frozenset({"vault.migration.read"}),
        ),
        RegisteredTool(
            "semantic_search",
            handlers.semantic_search,
            "search",
            "omnisvera://vault",
            frozenset({"vault.search"}),
        ),
        RegisteredTool(
            "assistant_status",
            handlers.assistant_status,
            "read",
            "projects://current/status",
            frozenset({"project.read"}),
        ),
        RegisteredTool(
            "create_local_proposal",
            handlers.create_local_proposal,
            "propose",
            "omnisvera://proposals",
            frozenset({"vault.propose"}),
        ),
        RegisteredTool(
            "audit_changed_notes",
            handlers.audit_changed_notes,
            "audit",
            "omnisvera://vault/changed",
            frozenset({"vault.audit"}),
        ),
        RegisteredTool(
            "system.health",
            lambda _context, _arguments: json.dumps(health.collect(), ensure_ascii=False, indent=2),
            "health",
            "system://health",
            frozenset({"system.health.read"}),
        ),
        RegisteredTool(
            "memory.get",
            read_memory,
            "read",
            "memory://items",
            frozenset({"memory.read"}),
        ),
        RegisteredTool(
            "memory.list",
            list_memory,
            "read",
            "memory://items",
            frozenset({"memory.read"}),
        ),
    ):
        registry.register(tool)
    make_context = context_factory or CallContext.trusted_local_stdio

    @mcp.tool()
    def get_handoff() -> str:
        """Retorna o objetivo, regras e próximo passo compartilhados entre Codex e Ollama."""
        return registry.invoke("get_handoff", make_context(), {})

    @mcp.tool()
    def get_migration_status() -> str:
        """Retorna o registro versionado da migração de Disgraceland para Omnisvera."""
        return registry.invoke("get_migration_status", make_context(), {})

    @mcp.tool()
    def semantic_search(query: str, limit: int = 8) -> str:
        """Pesquisa o índice semântico local e retorna trechos com caminhos de origem."""
        return registry.invoke(
            "semantic_search",
            make_context(),
            {"query": query, "limit": limit},
        )

    @mcp.tool()
    def assistant_status() -> str:
        """Retorna estado Git e handoff atual sem modificar arquivos."""
        return registry.invoke("assistant_status", make_context(), {})

    @mcp.tool()
    def create_local_proposal(task: str, source_files: list[str]) -> str:
        """Gera proposta somente a partir de fontes explícitas, sem editar notas canônicas."""
        return registry.invoke(
            "create_local_proposal",
            make_context(),
            {"task": task, "source_files": source_files},
        )

    @mcp.tool()
    def audit_changed_notes() -> str:
        """Executa auditoria de YAML e wikilinks apenas nas notas modificadas."""
        return registry.invoke("audit_changed_notes", make_context(), {})

    @mcp.tool(name="system.health")
    def system_health() -> str:
        """Retorna saúde, freshness e limitações dos subsistemas do Omnisvera."""
        return registry.invoke("system.health", make_context(), {})

    @mcp.tool(name="memory.get")
    def memory_get(memory_id: str) -> str:
        """Retorna uma memória persistida por ID, incluindo sua proveniência."""

        return registry.invoke("memory.get", make_context(), {"memory_id": memory_id})

    @mcp.tool(name="memory.list")
    def memory_list(item_type: str | None = None, limit: int = 20) -> str:
        """Lista memórias persistidas, opcionalmente filtradas por tipo."""

        return registry.invoke(
            "memory.list",
            make_context(),
            {"item_type": item_type, "limit": limit},
        )

    resources = ResourceRegistry(audit=audit)
    resources.register(RegisteredResource("system://health", lambda _context: health.collect(), frozenset({"system.health.read"})))
    resources.register(RegisteredResource("omnisvera://handoff", lambda _context: handoff.snapshot(), frozenset({"vault.handoff.read"})))
    resources.register(RegisteredResource("projects://companion/current", lambda _context: companion.get_dashboard().as_dict(), frozenset({"companion.read"})))

    @mcp.resource("system://health", name="Omnisvera system health")
    def system_health_resource() -> str:
        return json.dumps(resources.read("system://health", make_context()), ensure_ascii=False, indent=2)

    @mcp.resource("omnisvera://handoff", name="Dynamic Omnisvera handoff")
    def dynamic_handoff_resource() -> str:
        return json.dumps(resources.read("omnisvera://handoff", make_context()), ensure_ascii=False, indent=2)

    @mcp.resource("projects://companion/current", name="Current Companion project state")
    def companion_state_resource() -> str:
        return json.dumps(resources.read("projects://companion/current", make_context()), ensure_ascii=False, indent=2)

    registry.services = {
        "memory": memory,
        "companion": companion,
        "health": health,
        "handoff": handoff,
        "resources": resources,
    }

    return (
        ToolBindings(
            get_handoff=get_handoff,
            get_migration_status=get_migration_status,
            semantic_search=semantic_search,
            assistant_status=assistant_status,
            create_local_proposal=create_local_proposal,
            audit_changed_notes=audit_changed_notes,
            system_health=system_health,
            memory_get=memory_get,
            memory_list=memory_list,
        ),
        registry,
        search,
    )
