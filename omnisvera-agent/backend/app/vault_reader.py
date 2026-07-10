from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - fallback for minimal local envs
    yaml = None


IGNORED_DIRS = {
    ".git",
    ".obsidian",
    ".codex-remote-attachments",
    ".trash",
    ".tmp_refs",
    "omnisvera-agent",
    "zz_media",
    "node_modules",
    "__pycache__",
    "omnisvera-agent/frontend/node_modules",
}


@dataclass
class VaultNote:
    path: str
    title: str
    aliases: list[str]
    type: str | None
    visibility: str | None
    tags: list[str]
    content: str
    frontmatter: dict[str, Any]
    updated_at: str


def _is_ignored(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    if not rel_parts:
        return False
    if rel_parts[0] in IGNORED_DIRS:
        return True
    joined = "/".join(rel_parts)
    return any(joined.startswith(prefix + "/") for prefix in IGNORED_DIRS if "/" in prefix)


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}, text

    raw_frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")

    if yaml is not None:
        parsed = yaml.safe_load(raw_frontmatter) or {}
        if isinstance(parsed, dict):
            return parsed, body
        return {}, body

    # Tiny fallback parser for simple key/value and list frontmatter.
    parsed: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw_frontmatter.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            parsed.setdefault(current_key, []).append(line[4:].strip().strip('"'))
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            parsed[current_key] = value.strip('"') if value else None
    return parsed, body


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        return [part.strip() for part in re.split(r"[,;]", stripped) if part.strip()]
    return [str(value)]


def _title_from_body(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def read_markdown_note(path: Path, root: Path) -> VaultNote:
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = _parse_frontmatter(text)
    rel_path = path.relative_to(root).as_posix()
    title = str(frontmatter.get("name") or frontmatter.get("title") or _title_from_body(body, path.stem))
    aliases = _as_list(frontmatter.get("aliases") or frontmatter.get("alias"))
    tags = _as_list(frontmatter.get("tags") or frontmatter.get("tag"))
    updated_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    return VaultNote(
        path=rel_path,
        title=title,
        aliases=aliases,
        type=str(frontmatter.get("type")) if frontmatter.get("type") is not None else None,
        visibility=str(frontmatter.get("visibility")) if frontmatter.get("visibility") is not None else None,
        tags=tags,
        content=body,
        frontmatter=frontmatter,
        updated_at=updated_at,
    )


def iter_markdown_notes(root: Path) -> tuple[list[VaultNote], int]:
    notes: list[VaultNote] = []
    skipped = 0
    for path in root.rglob("*.md"):
        if _is_ignored(path, root):
            skipped += 1
            continue
        try:
            notes.append(read_markdown_note(path, root))
        except Exception:
            skipped += 1
    return notes, skipped


def markdown_signature(root: Path) -> tuple[int, str | None]:
    count = 0
    latest: str | None = None
    for path in root.rglob("*.md"):
        if _is_ignored(path, root):
            continue
        try:
            updated_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        except OSError:
            continue
        count += 1
        if latest is None or updated_at > latest:
            latest = updated_at
    return count, latest
