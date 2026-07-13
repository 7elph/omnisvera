from __future__ import annotations

import json
import re
import unicodedata
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Literal


AccessMode = Literal["gm", "player"]
_PLAYER_PROFILE: ContextVar[str | None] = ContextVar("omnisvera_player_profile", default=None)


@dataclass(frozen=True)
class AccessContext:
    mode: AccessMode
    profile_id: str | None = None
    character_path: str | None = None
    character_title: str | None = None


PLAYER_VISIBILITIES = {"jogadores", "publico", "player", "players", "public"}
BLOCKED_SPOILER_LEVELS = {"medium", "heavy"}
BLOCKED_PLAYER_PATH_PREFIXES = (
    ".obsidian/",
    "Workflow/",
    "Templates/",
    "omnisvera-agent/",
)
BLOCKED_PLAYER_PATHS = {
    "CAMPANHA/ESTADO_DA_CAMPANHA.md",
    "CAMPANHA/SESSAO_01_ROTEIRO_DE_MESA.md",
    "CAMPANHA/SESSÃO_01_ROTEIRO_DE_MESA.md",
}
BLOCKED_PLAYER_TYPES = {"workflow", "template", "index"}
PLAYER_SENSITIVE_LINE_PATTERNS = (
    r"CAMPANHA/ESTADO_DA_CAMPANHA",
    r"ESTADO_DA_CAMPANHA",
    r"Estado da Campanha",
    r"Segredos? do Mestre",
    r"gm_secret",
    r"spoiler_level",
    r"visibility\s*[:=]\s*[\"']?Mestre",
    r"arquivo vivo",
    r"bode expiat[óo]rio",
    r"herdeiro secreto",
    r"pecado da Coroa",
    r"verdades poss[íi]veis",
    r"Grande Fratura",
    r"Sangue Antigo",
    r"Criadores",
)
PLAYER_SENSITIVE_SECTION_HEADINGS = (
    "Segredos do Mestre",
    "Segredos",
    "Bastidores",
    "Bastidores do Mestre",
    "Encaminhamento para o Estado da Campanha",
    "Pendências do Sage",
    "Pendencias do Sage",
    "Pendências",
    "Pendencias",
    "Pendências Canônicas",
    "Pendencias Canonicas",
    "Notas do Mestre",
    "Mistérios para depois",
    "Misterios para depois",
    "Uso em Mesa",
    "Como usar em mesa",
    "Como apresentar em jogo",
    "Função em jogo",
    "Funcao em jogo",
    "Ganchos",
    "Ganchos de aventura",
    "Possíveis Ganchos",
    "Possiveis Ganchos",
    "Template",
    "Templates",
    "Template aplicado",
    "Notas técnicas",
    "Notas tecnicas",
)
PLAYER_BLOCKED_LOOKUP_TERMS = (
    "estado da campanha",
    "estado_da_campanha",
    "sangue antigo",
    "criadores",
    "grande fratura",
    "fraturamento",
    "eclipse de obsidiana",
    "anciao primordial",
    "véu cinzento",
    "veu cinzento",
    "sangue-antigo",
    "veu-cinzento",
    "grande-fratura",
    "eclipse-de-obsidiana",
)
PLAYER_SENSITIVE_TAG_TERMS = (
    "sangue",
    "criador",
    "fratura",
    "eclipse",
    "veu",
    "véu",
    "segredo",
    "mestre",
)


def _strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def normalize_text(value: Any) -> str:
    return _strip_accents(str(value or "").strip().lower())


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


@contextmanager
def player_profile_scope(profile_id: str | None):
    token = _PLAYER_PROFILE.set(normalize_text(profile_id) or None)
    try:
        yield
    finally:
        _PLAYER_PROFILE.reset(token)


def is_player_safe(path: str, visibility: Any, frontmatter: dict[str, Any]) -> bool:
    normalized_path = path.replace("\\", "/")
    if normalized_path.startswith(BLOCKED_PLAYER_PATH_PREFIXES):
        return False
    if normalized_path in BLOCKED_PLAYER_PATHS:
        return False
    if "/INDICE_" in normalized_path or normalized_path.startswith("INDICE_"):
        return False

    effective_visibility = normalize_text(frontmatter.get("visibility") or visibility)
    if effective_visibility not in PLAYER_VISIBILITIES:
        return False

    revealed_to = frontmatter.get("revealed_to")
    if revealed_to:
        values = revealed_to if isinstance(revealed_to, list) else [revealed_to]
        allowed_profiles = {normalize_text(value) for value in values if normalize_text(value)}
        current_profile = normalize_text(_PLAYER_PROFILE.get())
        if not current_profile or current_profile not in allowed_profiles:
            return False

    note_type = normalize_text(frontmatter.get("type"))
    if note_type in BLOCKED_PLAYER_TYPES:
        return False

    if truthy(frontmatter.get("gm_secret")):
        return False

    spoiler_level = normalize_text(frontmatter.get("spoiler_level"))
    if spoiler_level in BLOCKED_SPOILER_LEVELS:
        return False

    return True


def is_player_safe_row(row: Any) -> bool:
    frontmatter = load_frontmatter(row["frontmatter"])
    if not is_player_safe(row["path"], row["visibility"], frontmatter):
        return False

    lookup = normalize_text(f"{row['path']} {row['title']}")
    if any(normalize_text(term) in lookup for term in PLAYER_BLOCKED_LOOKUP_TERMS):
        return False

    return True


def is_player_safe_note(note: dict[str, Any]) -> bool:
    return is_player_safe(
        note.get("path", ""),
        note.get("visibility"),
        load_frontmatter(note.get("frontmatter", {})),
    )


def sanitize_player_text(text: str) -> str:
    sanitized = text
    sanitized = re.sub(
        r"```(?:dataview|datacards|leaflet)[\s\S]*?```",
        "",
        sanitized,
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(
        r"\[\[CAMPANHA/ESTADO_DA_CAMPANHA(?:\|[^\]]+)?\]\]|\[\[ESTADO_DA_CAMPANHA(?:\|[^\]]+)?\]\]",
        "notas do mestre",
        sanitized,
        flags=re.IGNORECASE,
    )
    for heading in PLAYER_SENSITIVE_SECTION_HEADINGS:
        sanitized = re.sub(
            rf"^\s*##+\s*{re.escape(heading)}[\s\S]*?(?=^\s*##+\s+|\Z)",
            "",
            sanitized,
            flags=re.IGNORECASE | re.MULTILINE,
        )

    kept_lines: list[str] = []
    sensitive_pattern = re.compile("|".join(PLAYER_SENSITIVE_LINE_PATTERNS), re.IGNORECASE)
    for line in sanitized.splitlines():
        if sensitive_pattern.search(line):
            continue
        kept_lines.append(line)

    sanitized = "\n".join(kept_lines)
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized).strip()
    return sanitized


def sanitize_player_summary(note: dict[str, Any]) -> dict[str, Any]:
    note = dict(note)
    if isinstance(note.get("tags"), list):
        note["tags"] = [
            tag
            for tag in note["tags"]
            if not any(normalize_text(term) in normalize_text(tag) for term in PLAYER_SENSITIVE_TAG_TERMS)
        ]
    if note.get("description"):
        note["description"] = sanitize_player_text(str(note["description"]))
    return note


def sanitize_player_note(note: dict[str, Any]) -> dict[str, Any]:
    note = sanitize_player_summary(note)
    if "content" in note:
        note = dict(note)
        note["content"] = sanitize_player_text(str(note.get("content") or ""))
    return note
