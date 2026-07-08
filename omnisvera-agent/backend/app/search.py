from __future__ import annotations

import re
import json
from pathlib import Path

from .vault_index import all_notes_for_search


def _terms(query: str) -> list[str]:
    return [term.lower() for term in re.findall(r"[\wÀ-ÿ'-]+", query) if len(term) > 1]


def _excerpt(content: str, terms: list[str], size: int = 260) -> str:
    lowered = content.lower()
    index = min((lowered.find(term) for term in terms if term in lowered), default=0)
    start = max(index - 80, 0)
    end = min(start + size, len(content))
    excerpt = content[start:end].replace("\n", " ").strip()
    return excerpt + ("..." if end < len(content) else "")


def search_notes(database_path: Path, query: str, limit: int = 10) -> list[dict]:
    terms = _terms(query)
    if not terms:
        return []

    results: list[dict] = []
    for row in all_notes_for_search(database_path):
        haystacks = {
            "title": row["title"].lower(),
            "path": row["path"].lower(),
            "tags": row["tags"].lower(),
            "content": row["content"].lower(),
            "aliases": row["aliases"].lower(),
        }
        score = 0
        for term in terms:
            if term in haystacks["title"]:
                score += 12
            if term in haystacks["path"]:
                score += 8
            if term in haystacks["tags"] or term in haystacks["aliases"]:
                score += 6
            score += min(haystacks["content"].count(term), 8)
        if score:
            results.append(
                {
                    "id": row["id"],
                    "path": row["path"],
                    "title": row["title"],
                    "aliases": json.loads(row["aliases"] or "[]"),
                    "type": row["type"],
                    "visibility": row["visibility"],
                    "tags": json.loads(row["tags"] or "[]"),
                    "updated_at": row["updated_at"],
                    "score": score,
                    "excerpt": _excerpt(row["content"], terms),
                }
            )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[: max(1, min(limit, 50))]
