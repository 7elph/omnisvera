"""Resilient exact, lexical, and optional semantic retrieval."""

from .coordinator import SearchCoordinator, SearchOutcome
from .lexical import LexicalIndex, RefreshReport, SearchHit
from .semantic import OllamaSemanticBackend, SemanticState

__all__ = [
    "LexicalIndex",
    "OllamaSemanticBackend",
    "RefreshReport",
    "SearchCoordinator",
    "SearchHit",
    "SearchOutcome",
    "SemanticState",
]
