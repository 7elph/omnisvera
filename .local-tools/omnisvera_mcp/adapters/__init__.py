"""Source-system adapters used by Omnisvera MCP Core."""

from .git import GitAdapter
from .vault import NoteInfo, VaultAdapter

__all__ = ["GitAdapter", "NoteInfo", "VaultAdapter"]
