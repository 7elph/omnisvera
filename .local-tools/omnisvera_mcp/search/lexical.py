from __future__ import annotations

import hashlib
import json
import math
import re
import threading
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..adapters.vault import NoteInfo, VaultAdapter


INDEX_VERSION = 1
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
HEADING = re.compile(r"(?m)^#{1,6}\s+.+$")
TOKEN = re.compile(r"[\w]+", re.UNICODE)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(TOKEN.findall(without_marks))


def tokens(value: str) -> list[str]:
    normalized = normalize(value)
    return normalized.split() if normalized else []


def split_chunks(text: str, max_chars: int = 1800) -> list[str]:
    frontmatter = FRONTMATTER.match(text)
    if frontmatter:
        text = text[frontmatter.end() :]
    starts = [match.start() for match in HEADING.finditer(text)]
    starts = [0, *starts, len(text)]
    sections = [text[start:end].strip() for start, end in zip(starts, starts[1:])]
    chunks: list[str] = []
    for section in sections:
        if not section:
            continue
        for offset in range(0, len(section), max_chars):
            body = section[offset : offset + max_chars].strip()
            if body:
                chunks.append(body)
    return chunks


@dataclass(frozen=True, slots=True)
class SearchHit:
    path: str
    text: str
    score: float
    modes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RefreshReport:
    changed: tuple[str, ...]
    deleted: tuple[str, ...]
    unchanged: int
    rebuilt: bool
    checked_at: str


class LexicalIndex:
    """Regenerable per-note manifest and deterministic local retrieval index."""

    def __init__(
        self,
        vault: VaultAdapter,
        index_path: Path,
        *,
        semantic_index_path: Path | None = None,
    ) -> None:
        self.vault = vault
        self.index_path = index_path
        self.semantic_index_path = semantic_index_path
        self._lock = threading.RLock()
        self._state = self._load_state()

    def _empty_state(self) -> dict:
        return {
            "version": INDEX_VERSION,
            "updated_at": None,
            "documents": {},
            "semantic_deleted": [],
        }

    def _load_state(self) -> dict:
        if not self.index_path.exists():
            return self._empty_state()
        try:
            state = json.loads(self.index_path.read_text(encoding="utf-8"))
            if state.get("version") != INDEX_VERSION or not isinstance(
                state.get("documents"), dict
            ):
                return self._empty_state()
            state.setdefault("semantic_deleted", [])
            return state
        except (OSError, json.JSONDecodeError, TypeError):
            return self._empty_state()

    def _semantic_baseline(self) -> tuple[set[str], int | None]:
        path = self.semantic_index_path
        if not path or not path.exists():
            return set(), None
        indexed_paths: set[str] = set()
        try:
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    item = json.loads(line)
                    raw_path = str(item.get("path", "")).replace("\\", "/")
                    if raw_path:
                        indexed_paths.add(raw_path)
        except (OSError, json.JSONDecodeError, TypeError):
            return set(), None
        return indexed_paths, path.stat().st_mtime_ns

    def refresh(self) -> RefreshReport:
        with self._lock:
            checked_at = utc_now()
            stored = self._state["documents"]
            current_infos = {item.relative_path: item for item in self.vault.note_infos()}
            stored_paths = set(stored)
            current_paths = set(current_infos)
            deleted = sorted(stored_paths - current_paths)
            changed: list[str] = []
            metadata_updated = False
            rebuilt = not self.index_path.exists() or not stored
            new_paths = current_paths - stored_paths
            semantic_paths, semantic_mtime_ns = (
                self._semantic_baseline() if new_paths else (set(), None)
            )

            for relative_path in sorted(current_paths, key=str.casefold):
                info = current_infos[relative_path]
                previous = stored.get(relative_path)
                if previous and (
                    previous.get("mtime_ns") == info.mtime_ns
                    and previous.get("size") == info.size
                ):
                    continue
                text = self.vault.read_note(info)
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                if previous and previous.get("sha256") == digest:
                    previous["mtime_ns"] = info.mtime_ns
                    previous["size"] = info.size
                    metadata_updated = True
                    continue
                is_semantically_dirty = True
                if previous is None and semantic_mtime_ns is not None:
                    is_semantically_dirty = (
                        relative_path not in semantic_paths or info.mtime_ns > semantic_mtime_ns
                    )
                stored[relative_path] = {
                    "mtime_ns": info.mtime_ns,
                    "size": info.size,
                    "sha256": digest,
                    "chunks": split_chunks(text),
                    "embedding_dirty": is_semantically_dirty,
                }
                changed.append(relative_path)

            if deleted:
                pending_deleted = set(self._state.get("semantic_deleted", []))
                pending_deleted.update(deleted)
                self._state["semantic_deleted"] = sorted(pending_deleted)
                for relative_path in deleted:
                    stored.pop(relative_path, None)

            if changed or deleted or rebuilt or metadata_updated:
                self._state["updated_at"] = checked_at
                self._save_state()

            return RefreshReport(
                changed=tuple(changed),
                deleted=tuple(deleted),
                unchanged=len(current_paths) - len(changed),
                rebuilt=rebuilt,
                checked_at=checked_at,
            )

    def _save_state(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.index_path.with_suffix(self.index_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.index_path)

    def dirty_documents(self) -> dict[str, list[str]]:
        with self._lock:
            return {
                path: list(document.get("chunks", []))
                for path, document in self._state["documents"].items()
                if document.get("embedding_dirty", True)
            }

    def semantic_deleted(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._state.get("semantic_deleted", []))

    def mark_semantic_clean(
        self,
        paths: set[str],
        *,
        deleted_paths: set[str] | None = None,
    ) -> None:
        with self._lock:
            changed = False
            for path in paths:
                document = self._state["documents"].get(path)
                if document and document.get("embedding_dirty", True):
                    document["embedding_dirty"] = False
                    changed = True
            if deleted_paths:
                remaining = set(self._state.get("semantic_deleted", [])) - deleted_paths
                if remaining != set(self._state.get("semantic_deleted", [])):
                    self._state["semantic_deleted"] = sorted(remaining)
                    changed = True
            if changed:
                self._state["updated_at"] = utc_now()
                self._save_state()

    def search(self, query: str, limit: int) -> list[SearchHit]:
        with self._lock:
            query_tokens = tokens(query)
            normalized_query = normalize(query)
            if not query_tokens or limit <= 0:
                return []

            rows: list[tuple[str, str, list[str]]] = []
            for path, document in self._state["documents"].items():
                for text in document.get("chunks", []):
                    rows.append((path, text, tokens(text)))
            if not rows:
                return []

            document_frequency = Counter()
            for _, _, row_tokens in rows:
                document_frequency.update(set(row_tokens))
            average_length = sum(len(row_tokens) for _, _, row_tokens in rows) / len(rows)
            total_rows = len(rows)
            raw_hits: list[SearchHit] = []

            for path, text, row_tokens in rows:
                counts = Counter(row_tokens)
                lexical_score = 0.0
                for term in query_tokens:
                    frequency = counts.get(term, 0)
                    if not frequency:
                        continue
                    inverse_frequency = math.log(
                        1 + (total_rows - document_frequency[term] + 0.5)
                        / (document_frequency[term] + 0.5)
                    )
                    denominator = frequency + 1.5 * (
                        1 - 0.75 + 0.75 * len(row_tokens) / max(average_length, 1)
                    )
                    lexical_score += inverse_frequency * frequency * 2.5 / denominator

                normalized_path = normalize(path)
                normalized_stem = normalize(Path(path).stem)
                normalized_text = normalize(text)
                stem_exact = bool(normalized_query and normalized_stem == normalized_query)
                path_exact = bool(normalized_query and normalized_query in normalized_path)
                text_exact = bool(normalized_query and normalized_query in normalized_text)
                exact = stem_exact or path_exact or text_exact
                if not exact and lexical_score <= 0:
                    continue
                modes = tuple(
                    mode
                    for mode, enabled in (("exact", exact), ("lexical", lexical_score > 0))
                    if enabled
                )
                raw_hits.append(
                    SearchHit(
                        path=path,
                        text=text,
                        score=(
                            lexical_score
                            + (8.0 if stem_exact else 0.0)
                            + (4.0 if path_exact and not stem_exact else 0.0)
                            + (2.0 if text_exact else 0.0)
                        ),
                        modes=modes,
                    )
                )

            raw_hits.sort(key=lambda item: (-item.score, item.path.casefold(), item.text))
            return raw_hits[:limit]
