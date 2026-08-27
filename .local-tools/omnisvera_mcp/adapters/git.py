from __future__ import annotations

import subprocess
from pathlib import Path


class GitAdapter:
    """Read-only access to repository state through the Git CLI."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def output(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return (result.stdout or result.stderr).strip()

    def branch(self) -> str:
        return self.output("branch", "--show-current")

    def head(self) -> str:
        return self.output("log", "-1", "--oneline")

    def working_tree_status(self) -> str:
        return self.output("status", "--short")
