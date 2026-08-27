from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".obsidian",
    ".codex-tools",
    ".codex-remote-attachments",
    ".tmp_refs",
    ".omnisvera-tools",
    ".local-tools",
    ".local-index",
    ".local-proposals",
    ".assistant-runtime",
    ".ollama",
    "node_modules",
    "zz_media",
    "z_Assets",
}


@dataclass(frozen=True, slots=True)
class NoteInfo:
    path: Path
    relative_path: str
    mtime_ns: int
    size: int


class VaultAdapter:
    """Read-only Vault boundary plus the existing changed-note audit command."""

    def __init__(self, root: Path, *, python_executable: Path | None = None) -> None:
        self.root = root.resolve()
        self.python_executable = (
            python_executable.resolve()
            if python_executable
            else self.root / ".omnisvera-tools" / "Scripts" / "python.exe"
        )

    @staticmethod
    def is_legacy(path: Path) -> bool:
        return path.name.startswith("Legacy -") or (
            "Workflow" in path.parts and "Legacy" in path.parts
        )

    def note_infos(self, *, include_legacy: bool = False) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        for directory, child_directories, filenames in os.walk(self.root):
            child_directories[:] = [
                name for name in child_directories if name not in EXCLUDED_DIRS
            ]
            directory_path = Path(directory)
            for filename in filenames:
                if not filename.casefold().endswith(".md"):
                    continue
                path = directory_path / filename
                relative = path.relative_to(self.root)
                if not include_legacy and self.is_legacy(relative):
                    continue
                stat = path.stat()
                notes.append(
                    NoteInfo(
                        path=path,
                        relative_path=relative.as_posix(),
                        mtime_ns=stat.st_mtime_ns,
                        size=stat.st_size,
                    )
                )
        return sorted(notes, key=lambda item: item.relative_path.casefold())

    def read_note(self, note: NoteInfo) -> str:
        return note.path.read_text(encoding="utf-8-sig", errors="replace")

    def read_relative(self, relative_path: str) -> str:
        path = self._safe_file(relative_path)
        return path.read_text(encoding="utf-8-sig", errors="replace")

    def read_handoff(self) -> str:
        return self.read_relative("Workflow/ASSISTANT_HANDOFF.md")

    def read_migration_status(self) -> str:
        return self.read_relative("Workflow/MIGRATION_LEDGER.md")

    def _safe_file(self, relative_path: str) -> Path:
        path = (self.root / relative_path).resolve()
        if self.root not in path.parents or not path.is_file():
            raise ValueError(f"Fonte inválida: {relative_path}")
        return path

    def audit_changed_notes(self) -> str:
        result = subprocess.run(
            [
                str(self.python_executable),
                str(self.root / ".local-tools" / "vault_tools.py"),
                "audit",
                "--changed",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return result.stdout or result.stderr
