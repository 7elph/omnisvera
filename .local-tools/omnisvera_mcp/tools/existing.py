from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..core.context import CallContext


def migration_status_handler(root: Path):
    migration_path = root / "Workflow" / "MIGRATION_LEDGER.md"

    def read_migration_status(
        _context: CallContext,
        _arguments: Mapping[str, Any],
    ) -> str:
        return migration_path.read_text(encoding="utf-8-sig")

    return read_migration_status
