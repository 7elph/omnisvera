from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal


AccessMode = Literal["gm", "player"]


@dataclass(frozen=True)
class AccessContext:
    mode: AccessMode


PLAYER_VISIBILITIES = {"jogadores", "publico", "público", "player", "players", "public"}
BLOCKED_SPOILER_LEVELS = {"medium", "heavy"}
BLOCKED_PLAYER_PATH_PREFIXES = (
    ".obsidian/",
    "Workflow/",
    "Templates/",
    "omnisvera-agent/",
)


def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return normalize_text(value) in {"1", "true", "yes", "sim", "s", "y"}


def load_frontmatter(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        data = json.loads(str(value))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def is_player_safe(path: str, visibility: Any, frontmatter: dict[str, Any]) -> bool:
    normalized_path = path.replace("\\", "/")
    if normalized_path.startswith(BLOCKED_PLAYER_PATH_PREFIXES):
        return False

    effective_visibility = normalize_text(frontmatter.get("visibility") or visibility)
    if effective_visibility not in PLAYER_VISIBILITIES:
        return False

    if truthy(frontmatter.get("gm_secret")):
        return False

    spoiler_level = normalize_text(frontmatter.get("spoiler_level"))
    if spoiler_level in BLOCKED_SPOILER_LEVELS:
        return False

    return True


def is_player_safe_row(row: Any) -> bool:
    frontmatter = load_frontmatter(row["frontmatter"])
    return is_player_safe(row["path"], row["visibility"], frontmatter)


def is_player_safe_note(note: dict[str, Any]) -> bool:
    return is_player_safe(
        note.get("path", ""),
        note.get("visibility"),
        load_frontmatter(note.get("frontmatter", {})),
    )


def sanitize_player_text(text: str) -> str:
    sanitized = text
    sanitized = re.sub(
        r"\[\[CAMPANHA/ESTADO_DA_CAMPANHA(?:\|[^\]]+)?\]\]|\[\[ESTADO_DA_CAMPANHA(?:\|[^\]]+)?\]\]",
        "notas do mestre",
        sanitized,
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(
        r"^\s*##\s*Segredos do Mestre[\s\S]*?(?=^\s*##\s+|\Z)",
        "",
        sanitized,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    sanitized = re.sub(
        r"^\s*##\s*Encaminhamento para o Estado da Campanha[\s\S]*?(?=^\s*##\s+|\Z)",
        "",
        sanitized,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return sanitized


def sanitize_player_note(note: dict[str, Any]) -> dict[str, Any]:
    if "content" in note:
        note = dict(note)
        note["content"] = sanitize_player_text(str(note.get("content") or ""))
    return note
