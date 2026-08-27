from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .adapters.git import GitAdapter
from .adapters.vault import VaultAdapter
from .core.context import CallContext
from .core.registry import RegisteredTool, ToolRegistry
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
    handlers = ExistingToolHandlers(vault, git, search)
    registry = ToolRegistry()
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

    return (
        ToolBindings(
            get_handoff=get_handoff,
            get_migration_status=get_migration_status,
            semantic_search=semantic_search,
            assistant_status=assistant_status,
            create_local_proposal=create_local_proposal,
            audit_changed_notes=audit_changed_notes,
        ),
        registry,
        search,
    )
