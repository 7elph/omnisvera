from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .access import AccessMode, is_player_safe_row, normalize_text, sanitize_player_text
from .ollama_client import embed_with_ollama
from .search import STOPWORDS
from .vault_index import all_notes_for_search, row_to_note


BLOCKED_PLAYER_STATUSES = {
    "gm",
    "mestre",
    "oculto",
    "hidden",
    "velado",
    "nao revelado",
    "não revelado",
}


@dataclass
class HybridResult:
    id: int | None
    path: str
    title: str
    aliases: list[str]
    type: str | None
    visibility: str | None
    excerpt: str
    lexical_score: float
    semantic_score: float
    exact_score: float
    final_score: float


_SEMANTIC_CACHE: dict[str, Any] = {
    "path": None,
    "mtime": None,
    "chunks": [],
}


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    try:
        data = json.loads(str(value or "[]"))
        if isinstance(data, list):
            return [str(item) for item in data]
    except Exception:
        pass
    return []


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        data = json.loads(str(value or "{}"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _terms(query: str) -> list[str]:
    normalized = normalize_text(query)
    return [
        term
        for term in re.findall(r"[a-z0-9']+", normalized)
        if len(term) > 1 and term not in STOPWORDS
    ]


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", normalize_text(value)))


def _path_stem(path: str) -> str:
    return Path(path.replace("\\", "/")).stem


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\s*\n[\s\S]*?\n---\s*\n?", "", text).strip()


def _plain_wikilinks(text: str) -> str:
    text = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", text)
    return re.sub(r"\[\[([^\]]+)\]\]", lambda match: match.group(1).split("/")[-1], text)


def _clean_excerpt(text: str, max_chars: int = 520) -> str:
    text = _strip_frontmatter(text)
    text = sanitize_player_text(text)
    text = re.sub(r"```(?:dataview|datacards|leaflet)[\s\S]*?```", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"!\[\[[^\]]+\]\]", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"(?im)^>\s*\[![^\n]*\][+-]?\s*.*$", "", text)
    text = re.sub(r"(?im)^>\s*!\[\[[^\]]+\]\].*$", "", text)
    text = re.sub(r"(?im)^>\s*$", "", text)
    text = re.sub(r"(?im)^>\s?", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = _plain_wikilinks(text)
    text = re.sub(r"(?im)^\s*(?:##+\s*)?(uso em mesa|como apresentar|pend[êe]ncias|template|dataview).*?$", "", text)
    text = re.sub(r"(?im)^\s*[-*]\s*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    clipped = text[:max_chars].rsplit(".", 1)[0].strip()
    return (clipped or text[:max_chars].strip()) + "..."


def _excerpt(content: str, terms: list[str], max_chars: int = 520) -> str:
    clean = _clean_excerpt(content, max_chars=max_chars * 2)
    normalized = normalize_text(clean)
    positions = [normalized.find(term) for term in terms if normalized.find(term) >= 0]
    if not positions:
        return _clean_excerpt(clean, max_chars=max_chars)
    index = min(positions)
    start = max(index - 120, 0)
    end = min(start + max_chars, len(clean))
    return (clean[start:end].strip() + ("..." if end < len(clean) else "")).strip()


def _row_blocked_by_status(row: Any) -> bool:
    frontmatter = _json_dict(row["frontmatter"])
    status_values = [
        frontmatter.get("status"),
        frontmatter.get("NoteStatus"),
        frontmatter.get("campaign_status"),
        frontmatter.get("quest_status"),
        frontmatter.get("handout_status"),
    ]
    return any(normalize_text(value) in BLOCKED_PLAYER_STATUSES for value in status_values)


def _allowed_rows(database_path: Path, access_mode: AccessMode, type_filters: list[str] | None) -> dict[str, Any]:
    wanted_types = {normalize_text(item) for item in (type_filters or []) if item}
    rows: dict[str, Any] = {}
    for row in all_notes_for_search(database_path):
        if access_mode == "player":
            if not is_player_safe_row(row) or _row_blocked_by_status(row):
                continue
        if wanted_types and normalize_text(row["type"]) not in wanted_types:
            continue
        rows[row["path"].replace("\\", "/")] = row
    return rows


def _load_semantic_index(index_path: Path) -> list[dict[str, Any]]:
    if not index_path.exists():
        return []
    mtime = index_path.stat().st_mtime
    cache_key = str(index_path.resolve())
    if _SEMANTIC_CACHE["path"] == cache_key and _SEMANTIC_CACHE["mtime"] == mtime:
        return list(_SEMANTIC_CACHE["chunks"])

    chunks: list[dict[str, Any]] = []
    with index_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            path = str(data.get("path") or "").replace("\\", "/")
            text = str(data.get("text") or "")
            embedding = data.get("embedding")
            if path and text and isinstance(embedding, list):
                chunks.append({"path": path, "text": text, "embedding": embedding})

    _SEMANTIC_CACHE.update({"path": cache_key, "mtime": mtime, "chunks": chunks})
    return list(chunks)


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if not norm_left or not norm_right:
        return 0.0
    return dot / (norm_left * norm_right)


def _exact_score(row: Any, query: str, terms: list[str]) -> float:
    query_norm = normalize_text(query)
    phrase = " ".join(terms)
    aliases = _json_list(row["aliases"])
    candidates = [row["title"], _path_stem(row["path"]), *aliases]
    normalized = [normalize_text(item) for item in candidates if item]
    if query_norm and query_norm in normalized:
        return 1000.0
    if phrase and phrase in normalized:
        return 940.0
    if any(query_norm and query_norm in item for item in normalized):
        return 700.0
    candidate_tokens = set().union(*(_tokens(item) for item in candidates if item)) if candidates else set()
    if terms and set(terms).issubset(candidate_tokens):
        return 520.0
    if terms and any(term in candidate_tokens for term in terms):
        return 160.0
    return 0.0


def _lexical_score(row: Any, content: str, query: str, terms: list[str]) -> float:
    if not terms:
        return 0.0
    aliases = " ".join(_json_list(row["aliases"]))
    tags = " ".join(_json_list(row["tags"]))
    title = normalize_text(row["title"])
    stem = normalize_text(_path_stem(row["path"]))
    path = normalize_text(row["path"])
    alias_text = normalize_text(aliases)
    tag_text = normalize_text(tags)
    content_text = normalize_text(content)
    phrase = " ".join(terms)

    score = 0.0
    if phrase and phrase in title:
        score += 170
    if phrase and phrase in stem:
        score += 150
    if phrase and phrase in alias_text:
        score += 130
    if phrase and phrase in path:
        score += 40
    for term in terms:
        if term in title:
            score += 58
        if term in stem:
            score += 48
        if term in alias_text:
            score += 42
        if term in tag_text:
            score += 18
        if term in path:
            score += 12
        score += min(content_text.count(term), 10) * 3
    note_type = normalize_text(row["type"])
    if note_type in {"character", "location", "territory", "faction", "item", "quest", "rumor", "story", "race", "class"}:
        score += 8
    if row["path"].startswith(("Workflow/", "Templates/", "omnisvera-agent/")):
        score -= 80
    if "INDICE_" in row["path"]:
        score -= 60
    return max(score, 0.0)


def _merge_result(results: dict[str, HybridResult], candidate: HybridResult) -> None:
    existing = results.get(candidate.path)
    if not existing or candidate.final_score > existing.final_score:
        results[candidate.path] = candidate


async def hybrid_search(
    database_path: Path,
    *,
    query: str,
    ollama_base_url: str,
    embedding_model: str,
    semantic_index_path: Path,
    limit: int = 8,
    access_mode: AccessMode = "player",
    rag_mode: str = "hybrid",
    type_filters: list[str] | None = None,
) -> list[dict[str, Any]]:
    mode = rag_mode if rag_mode in {"lexical", "semantic", "hybrid"} else "hybrid"
    terms = _terms(query)
    if not terms:
        return []

    rows_by_path = _allowed_rows(database_path, access_mode, type_filters)
    merged: dict[str, HybridResult] = {}

    if mode in {"lexical", "hybrid"}:
        for path, row in rows_by_path.items():
            content = str(row["content"] or "")
            if access_mode == "player":
                content = sanitize_player_text(content)
            exact = _exact_score(row, query, terms)
            lexical = _lexical_score(row, content, query, terms)
            if exact <= 0 and lexical <= 0:
                continue
            note = row_to_note(row)
            final = exact + lexical + (35 if exact >= 700 else 0)
            _merge_result(
                merged,
                HybridResult(
                    id=int(row["id"]),
                    path=path,
                    title=note["title"],
                    aliases=note.get("aliases") or [],
                    type=note.get("type"),
                    visibility=note.get("visibility"),
                    excerpt=_excerpt(content, terms),
                    lexical_score=round(lexical, 3),
                    semantic_score=0.0,
                    exact_score=round(exact, 3),
                    final_score=round(final, 3),
                ),
            )

    if mode in {"semantic", "hybrid"}:
        chunks = _load_semantic_index(semantic_index_path)
        if chunks:
            try:
                query_embeddings = await embed_with_ollama(ollama_base_url, embedding_model, query)
            except Exception:
                query_embeddings = []
            query_embedding = query_embeddings[0] if query_embeddings else []
            if query_embedding:
                best_by_path: dict[str, tuple[float, str]] = {}
                for chunk in chunks:
                    path = str(chunk["path"]).replace("\\", "/")
                    if path not in rows_by_path:
                        continue
                    similarity = _cosine(query_embedding, [float(value) for value in chunk["embedding"]])
                    if similarity <= 0:
                        continue
                    text = str(chunk["text"] or "")
                    if access_mode == "player":
                        text = sanitize_player_text(text)
                    text = _clean_excerpt(text, max_chars=620)
                    if not text:
                        continue
                    previous = best_by_path.get(path)
                    if not previous or similarity > previous[0]:
                        best_by_path[path] = (similarity, text)

                for path, (similarity, text) in best_by_path.items():
                    row = rows_by_path[path]
                    content = sanitize_player_text(row["content"]) if access_mode == "player" else row["content"]
                    exact = _exact_score(row, query, terms)
                    lexical = _lexical_score(row, content, query, terms)
                    semantic = max(0.0, similarity)
                    note = row_to_note(row)
                    final = exact + lexical + (semantic * 280)
                    _merge_result(
                        merged,
                        HybridResult(
                            id=int(row["id"]),
                            path=path,
                            title=note["title"],
                            aliases=note.get("aliases") or [],
                            type=note.get("type"),
                            visibility=note.get("visibility"),
                            excerpt=text,
                            lexical_score=round(lexical, 3),
                            semantic_score=round(semantic, 5),
                            exact_score=round(exact, 3),
                            final_score=round(final, 3),
                        ),
                    )

    ranked = sorted(merged.values(), key=lambda item: (item.final_score, item.exact_score, item.lexical_score), reverse=True)
    return [asdict(item) for item in ranked[: max(1, min(limit, 20))]]
