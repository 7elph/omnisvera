from __future__ import annotations

import re
from pathlib import Path

from .access import AccessMode, is_player_safe_row, normalize_text, sanitize_player_text
from .vault_index import all_notes_for_search, row_to_note


STOPWORDS = {
    "a",
    "as",
    "ao",
    "aos",
    "de",
    "da",
    "das",
    "do",
    "dos",
    "e",
    "eh",
    "em",
    "o",
    "os",
    "que",
    "quem",
    "qual",
    "quais",
    "sobre",
    "um",
    "uma",
}


def _terms(query: str) -> list[str]:
    normalized = normalize_text(query)
    return [
        term
        for term in re.findall(r"[\w'-]+", normalized)
        if len(term) > 1 and term not in STOPWORDS
    ]


def _excerpt(content: str, terms: list[str], size: int = 260) -> str:
    lowered = content.lower()
    normalized = normalize_text(content)
    index = min(
        (
            position
            for term in terms
            for position in (normalized.find(term), lowered.find(term))
            if position >= 0
        ),
        default=0,
    )
    start = max(index - 80, 0)
    end = min(start + size, len(content))
    excerpt = content[start:end].replace("\n", " ").strip()
    return excerpt + ("..." if end < len(content) else "")


def _starts_with_term(value: str, terms: list[str]) -> bool:
    normalized = normalize_text(value)
    return any(normalized == term or normalized.startswith(f"{term} ") for term in terms)


def _contains_exact_token(value: str, terms: list[str]) -> bool:
    normalized = normalize_text(value)
    tokens = set(re.findall(r"[a-z0-9]+", normalized))
    return any(term in tokens for term in terms)


def search_notes(database_path: Path, query: str, limit: int = 10, access_mode: AccessMode = "gm") -> list[dict]:
    terms = _terms(query)
    if not terms:
        return []

    results: list[dict] = []
    for row in all_notes_for_search(database_path):
        if access_mode == "player" and not is_player_safe_row(row):
            continue
        content = row["content"]
        if access_mode == "player":
            content = sanitize_player_text(content)

        haystacks = {
            "title": normalize_text(row["title"]),
            "path": normalize_text(row["path"]),
            "tags": normalize_text(row["tags"]),
            "content": normalize_text(content),
            "aliases": normalize_text(row["aliases"]),
        }
        stem = Path(row["path"]).stem
        score = 0
        phrase = " ".join(terms)
        if phrase and phrase in haystacks["title"]:
            score += 30
        if phrase and phrase in haystacks["path"]:
            score += 18
        if _starts_with_term(row["title"], terms):
            score += 45
        if _starts_with_term(stem, terms):
            score += 45
        if row["type"] == "character" and (
            _contains_exact_token(row["title"], terms) or _contains_exact_token(stem, terms)
        ):
            score += 24
        for term in terms:
            if term in haystacks["title"]:
                score += 16
            if term in haystacks["path"]:
                score += 10
            if term in haystacks["tags"] or term in haystacks["aliases"]:
                score += 8
            score += min(haystacks["content"].count(term), 8)
        if score:
            note = row_to_note(row)
            results.append(
                {
                    **note,
                    "score": score,
                    "excerpt": _excerpt(content, terms),
                }
            )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[: max(1, min(limit, 50))]
