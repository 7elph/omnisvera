from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml


BLOCKED_PREFIXES = (".git/", ".obsidian/", ".codex-remote-attachments/", "omnisvera-agent/", "zz_media/", "Workflow/_audit/")


class EditConflictError(RuntimeError):
    pass


def _safe_note(vault_root: Path, relative_path: str) -> Path:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if not normalized.endswith(".md") or normalized.startswith(BLOCKED_PREFIXES):
        raise ValueError("Caminho não permitido para edição")
    target = (vault_root / normalized).resolve()
    target.relative_to(vault_root.resolve())
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(normalized)
    return target


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _validate_markdown(content: str) -> None:
    if "\x00" in content:
        raise ValueError("Conteúdo inválido")
    if content.startswith("---"):
        lines = content.splitlines()
        if not lines or lines[0].strip() != "---":
            raise ValueError("Frontmatter deve abrir em linha própria")
        closing = next((index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
        if closing is None:
            raise ValueError("Frontmatter sem fechamento")
        parsed = yaml.safe_load("\n".join(lines[1:closing])) or {}
        if not isinstance(parsed, dict):
            raise ValueError("Frontmatter precisa ser um objeto YAML")


def read_editable_note(vault_root: Path, relative_path: str) -> dict:
    target = _safe_note(vault_root, relative_path)
    content = target.read_text(encoding="utf-8")
    return {
        "path": target.relative_to(vault_root).as_posix(),
        "content": content,
        "content_hash": _hash(content),
        "updated_at": datetime.fromtimestamp(target.stat().st_mtime, timezone.utc).isoformat(),
    }


def save_editable_note(
    vault_root: Path,
    backup_root: Path,
    relative_path: str,
    content: str,
    expected_hash: str,
) -> dict:
    target = _safe_note(vault_root, relative_path)
    current = target.read_text(encoding="utf-8")
    if _hash(current) != expected_hash:
        raise EditConflictError("A nota mudou desde que foi aberta")
    _validate_markdown(content)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = backup_root / target.relative_to(vault_root)
    backup = backup.with_name(f"{backup.stem}.{stamp}.md")
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text(current, encoding="utf-8", newline="\n")

    temporary = target.with_name(f".{target.name}.companion.tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, target)
    return read_editable_note(vault_root, relative_path)
