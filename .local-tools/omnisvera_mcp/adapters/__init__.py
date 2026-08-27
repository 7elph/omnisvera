"""Source-system adapters used by Omnisvera MCP Core."""

from .companion import CompanionAdapter, CompanionObservation
from .git import GitAdapter
from .vault import NoteInfo, VaultAdapter

__all__ = [
    "CompanionAdapter",
    "CompanionObservation",
    "GitAdapter",
    "NoteInfo",
    "VaultAdapter",
]
