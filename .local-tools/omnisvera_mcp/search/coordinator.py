from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass

from .lexical import LexicalIndex, RefreshReport, SearchHit
from .semantic import OllamaSemanticBackend, SemanticState


@dataclass(frozen=True, slots=True)
class SearchOutcome:
    hits: tuple[SearchHit, ...]
    modes_used: tuple[str, ...]
    semantic: SemanticState
    refresh: RefreshReport

    def render_legacy_text(self) -> str:
        return "\n\n".join(
            f"{hit.score:.4f} | {hit.path}\n{hit.text}" for hit in self.hits
        )


class SearchCoordinator:
    """Refreshes derived state and combines local and optional semantic results."""

    def __init__(
        self,
        lexical: LexicalIndex,
        semantic: OllamaSemanticBackend,
        *,
        semantic_refresh_limit: int = 8,
    ) -> None:
        self.lexical = lexical
        self.semantic = semantic
        self.semantic_refresh_limit = max(semantic_refresh_limit, 1)
        self._lock = threading.RLock()

    def refresh(self) -> RefreshReport:
        return self.lexical.refresh()

    def search(self, query: str, limit: int = 8) -> SearchOutcome:
        with self._lock:
            refresh = self.lexical.refresh()
            dirty = self.lexical.dirty_documents()
            deleted = set(self.lexical.semantic_deleted())
            state = self.semantic.state(dirty_count=len(dirty))
            if state.available and (dirty or deleted):
                refresh_paths = sorted(dirty)[: self.semantic_refresh_limit]
                refresh_documents = {path: dirty[path] for path in refresh_paths}
                if self.semantic.refresh_dirty(refresh_documents, deleted):
                    self.lexical.mark_semantic_clean(
                        set(refresh_documents), deleted_paths=deleted
                    )
                    dirty = self.lexical.dirty_documents()
                    deleted = set(self.lexical.semantic_deleted())
                    state = self.semantic.state(dirty_count=len(dirty))

            lexical_hits = self.lexical.search(query, max(limit * 3, limit))
            semantic_hits = (
                self.semantic.search(query, max(limit * 3, limit))
                if state.available
                else []
            )
            blocked_semantic_paths = set(dirty) | deleted
            semantic_hits = [
                hit for hit in semantic_hits if hit.path not in blocked_semantic_paths
            ]
            combined = self._combine(lexical_hits, semantic_hits, limit)
            modes = tuple(
                mode
                for mode in ("exact", "lexical", "semantic")
                if any(mode in hit.modes for hit in combined)
            )
            return SearchOutcome(tuple(combined), modes, state, refresh)

    @staticmethod
    def _combine(
        lexical_hits: list[SearchHit],
        semantic_hits: list[SearchHit],
        limit: int,
    ) -> list[SearchHit]:
        merged: dict[tuple[str, str], dict] = {}

        def add(hits: list[SearchHit], weight: float) -> None:
            positive_scores = [max(hit.score, 0.0) for hit in hits]
            maximum = max(positive_scores, default=0.0) or 1.0
            for hit in hits:
                text_key = hashlib.sha1(hit.text.encode("utf-8")).hexdigest()
                key = (hit.path, text_key)
                item = merged.setdefault(
                    key,
                    {"path": hit.path, "text": hit.text, "score": 0.0, "modes": set()},
                )
                normalized = max(hit.score, 0.0) / maximum
                exact_bonus = 0.5 if "exact" in hit.modes else 0.0
                item["score"] += normalized * weight + exact_bonus
                item["modes"].update(hit.modes)

        add(lexical_hits, 1.0)
        add(semantic_hits, 0.6)
        results = [
            SearchHit(
                path=item["path"],
                text=item["text"],
                score=item["score"],
                modes=tuple(
                    mode
                    for mode in ("exact", "lexical", "semantic")
                    if mode in item["modes"]
                ),
            )
            for item in merged.values()
        ]
        results.sort(key=lambda item: (-item.score, item.path.casefold(), item.text))
        return results[: max(limit, 0)]
