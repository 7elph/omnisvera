from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import assistant_bridge

from ..adapters.git import GitAdapter
from ..adapters.vault import VaultAdapter
from ..core.context import CallContext
from ..search.coordinator import SearchCoordinator


class ExistingToolHandlers:
    """Core-backed implementations of the six legacy public tools."""

    def __init__(
        self,
        vault: VaultAdapter,
        git: GitAdapter,
        search: SearchCoordinator,
    ) -> None:
        self.vault = vault
        self.git = git
        self.search = search

    def get_handoff(
        self,
        _context: CallContext,
        _arguments: Mapping[str, Any],
    ) -> str:
        return self.vault.read_handoff()

    def get_migration_status(
        self,
        _context: CallContext,
        _arguments: Mapping[str, Any],
    ) -> str:
        return self.vault.read_migration_status()

    def semantic_search(
        self,
        _context: CallContext,
        arguments: Mapping[str, Any],
    ) -> str:
        return self.search.search(
            str(arguments["query"]),
            int(arguments.get("limit", 8)),
        ).render_legacy_text()

    def assistant_status(
        self,
        _context: CallContext,
        _arguments: Mapping[str, Any],
    ) -> str:
        return "\n".join(
            [
                "# Estado do assistente",
                f"Branch: {self.git.branch()}",
                f"Último commit: {self.git.head()}",
                "Mudanças locais:",
                self.git.working_tree_status() or "(nenhuma)",
                "",
                self.vault.read_handoff(),
            ]
        )

    def create_local_proposal(
        self,
        _context: CallContext,
        arguments: Mapping[str, Any],
    ) -> str:
        return str(
            assistant_bridge.propose(
                str(arguments["task"]),
                list(arguments["source_files"]),
            )
        )

    def audit_changed_notes(
        self,
        _context: CallContext,
        _arguments: Mapping[str, Any],
    ) -> str:
        return self.vault.audit_changed_notes()
