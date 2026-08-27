from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..adapters.companion import CompanionAdapter
from ..adapters.git import GitAdapter
from ..adapters.vault import VaultAdapter
from ..memory.store import MemoryStore
from ..search.lexical import LexicalIndex
from ..search.semantic import OllamaSemanticBackend


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HealthService:
    def __init__(self, root: Path, vault: VaultAdapter, git: GitAdapter, lexical: LexicalIndex,
                 semantic: OllamaSemanticBackend, companion: CompanionAdapter, memory: MemoryStore) -> None:
        self.root = root
        self.vault = vault
        self.git = git
        self.lexical = lexical
        self.semantic = semantic
        self.companion = companion
        self.memory = memory

    def collect(self) -> dict[str, Any]:
        observed_at = utc_now()
        notes = self.vault.note_infos()
        lexical = self.lexical.status()
        semantic = self.semantic.state(dirty_count=lexical["dirty_documents"])
        companion = self.companion.get_health()
        head = self.git.head()
        return {
            "observed_at": observed_at,
            "mcp_core": {"status": "healthy", "freshness": "fresh"},
            "vault": {"status": "healthy", "freshness": "fresh", "documents": len(notes)},
            "git": {"status": "healthy" if head else "degraded", "freshness": "fresh", "head": head},
            "companion": companion.as_dict(),
            "lexical_index": {"status": "healthy", "freshness": lexical["freshness"], **lexical},
            "semantic_index": {"status": "healthy" if semantic.available else "stale" if semantic.indexed_at else "unavailable", "freshness": semantic.freshness, "indexed_at": semantic.indexed_at, "limitation": semantic.limitation},
            "ollama_or_embedding_provider": {"status": "healthy" if semantic.available else "offline"},
            "memory": {"status": "healthy", "freshness": "fresh", **self.memory.stats()},
        }
