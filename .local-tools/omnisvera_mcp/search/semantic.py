from __future__ import annotations

import json
import math
import os
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .lexical import SearchHit


def cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


@dataclass(frozen=True, slots=True)
class SemanticState:
    available: bool
    freshness: str
    indexed_at: str | None
    limitation: str | None = None


class OllamaSemanticBackend:
    """Optional compatibility backend for the existing JSONL vector index."""

    def __init__(
        self,
        index_path: Path,
        *,
        model: str = "nomic-embed-text",
        host: str | None = None,
        availability_timeout: float = 0.35,
    ) -> None:
        self.index_path = index_path
        self.model = model
        self.host = (host or os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip(
            "/"
        )
        self.availability_timeout = availability_timeout

    def is_available(self) -> bool:
        try:
            with urllib.request.urlopen(
                f"{self.host}/api/tags", timeout=self.availability_timeout
            ) as response:
                return response.status == 200
        except Exception:
            return False

    def state(self, *, dirty_count: int) -> SemanticState:
        indexed_at = None
        if self.index_path.exists():
            indexed_at = datetime.fromtimestamp(
                self.index_path.stat().st_mtime, timezone.utc
            ).isoformat()
        available = self.is_available()
        if not available:
            freshness = "stale" if self.index_path.exists() else "unavailable"
            return SemanticState(False, freshness, indexed_at, "Ollama offline")
        if not self.index_path.exists():
            return SemanticState(True, "dirty", None, "semantic index absent")
        return SemanticState(True, "dirty" if dirty_count else "fresh", indexed_at)

    def refresh_dirty(
        self,
        documents: dict[str, list[str]],
        deleted_paths: set[str],
    ) -> bool:
        if not documents and not deleted_paths:
            return True
        if not self.is_available():
            return False
        import ollama

        replaced_paths = set(documents) | deleted_paths
        retained: list[dict] = []
        if self.index_path.exists():
            try:
                with self.index_path.open(encoding="utf-8") as handle:
                    for line in handle:
                        item = json.loads(line)
                        if str(item.get("path", "")).replace("\\", "/") not in replaced_paths:
                            retained.append(item)
            except (OSError, json.JSONDecodeError, TypeError):
                return False

        new_rows: list[dict] = []
        flattened = [
            (path, text)
            for path, chunks in sorted(documents.items())
            for text in chunks
        ]
        client = ollama.Client(host=self.host)
        batch_size = 16
        try:
            for offset in range(0, len(flattened), batch_size):
                batch = flattened[offset : offset + batch_size]
                response = client.embed(
                    model=self.model,
                    input=[text for _, text in batch],
                )
                for (path, text), embedding in zip(batch, response["embeddings"]):
                    new_rows.append({"path": path, "text": text, "embedding": embedding})
        except Exception:
            return False

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.index_path.with_suffix(self.index_path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for item in [*retained, *new_rows]:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        temporary.replace(self.index_path)
        return True

    def search(self, query: str, limit: int) -> list[SearchHit]:
        if limit <= 0 or not self.index_path.exists() or not self.is_available():
            return []
        import ollama

        try:
            query_vector = ollama.Client(host=self.host).embed(
                model=self.model,
                input=query,
            )["embeddings"][0]
            rows: list[SearchHit] = []
            with self.index_path.open(encoding="utf-8") as handle:
                for line in handle:
                    item = json.loads(line)
                    rows.append(
                        SearchHit(
                            path=str(item["path"]).replace("\\", "/"),
                            text=str(item["text"]),
                            score=cosine(query_vector, item["embedding"]),
                            modes=("semantic",),
                        )
                    )
            rows.sort(key=lambda item: (-item.score, item.path.casefold(), item.text))
            return rows[:limit]
        except Exception:
            return []
