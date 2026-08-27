"""Deterministic lexical recall; no provider, index, or persistent state."""

from __future__ import annotations

import re
import unicodedata


# Function words only: do not discard negations or invent semantic synonyms.
STOP_WORDS = frozenset(
    "a ao aos as com da das de do dos e em o os para por que qual quais "
    "se sobre um uma uns umas ja existe existem temos "
    "a an and are about for in is of on the to what which with".split()
)


def normalize(text: str) -> str:
    unaccented = "".join(
        character for character in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(character)
    )
    return " ".join(re.findall(r"[^\W_]+", unaccented, flags=re.UNICODE))


def query_terms(query: str) -> tuple[str, frozenset[str]]:
    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        raise ValueError("query must contain 1 to 1000 characters")
    normalized = normalize(query)
    terms = frozenset(normalized.split()) - STOP_WORDS
    if not terms:
        raise ValueError("query must contain at least one searchable term")
    return normalized, terms


def validate_options(item_type: str | None, limit: int) -> str | None:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer between 1 and 100")
    if item_type is not None:
        if not isinstance(item_type, str) or len(item_type) > 100:
            raise ValueError("item_type must be a string of at most 100 characters")
        item_type = item_type.strip() or None
    return item_type


def rank(
    query: str, terms: frozenset[str], *, item_id: str, title: str, content: str,
) -> tuple[int, int, int, int] | None:
    """Descending: exact ID, exact title, distinct term coverage, title hits."""
    normalized_id = normalize(item_id)
    normalized_title = normalize(title)
    title_terms = set(normalized_title.split())
    searchable = title_terms | set(normalize(content).split()) | set(normalized_id.split())
    hits = len(terms & searchable)
    if not hits:
        return None
    return (int(query == normalized_id), int(query == normalized_title), hits,
            len(terms & title_terms))
