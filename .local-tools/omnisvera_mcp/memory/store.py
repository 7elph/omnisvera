from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class MemoryConflictError(ValueError):
    """Raised when a stable memory ID already represents different evidence."""


class MemoryStore:
    """Minimal SQLite store for memory, provenance, project state, and audit."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    namespace TEXT NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    owner TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    valid_from TEXT,
                    valid_until TEXT
                );
                CREATE TABLE IF NOT EXISTS memory_sources (
                    id TEXT PRIMARY KEY,
                    memory_item_id TEXT NOT NULL REFERENCES memory_items(id) ON DELETE CASCADE,
                    source_type TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    source_timestamp TEXT,
                    relation TEXT NOT NULL,
                    excerpt_hash TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_states (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    state_hash TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    freshness TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_project_states_latest
                    ON project_states(project_id, observed_at DESC);
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    client TEXT NOT NULL,
                    transport TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL,
                    result TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    arguments_hash TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                """
            )

    def add_memory(
        self,
        *,
        namespace: str,
        item_type: str,
        title: str,
        content: str,
        status: str = "accepted",
        confidence: float = 1.0,
        owner: str = "omnisvera",
        classification: str = "internal",
        metadata: dict[str, Any] | None = None,
        sources: list[dict[str, Any]] | None = None,
        item_id: str | None = None,
    ) -> str:
        item_id = item_id or f"mem-{uuid4().hex}"
        now = utc_now()
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO memory_items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (item_id, namespace, item_type, title, content, status, confidence,
                 owner, classification, stable_json(metadata or {}), now, now, None, None),
            )
            for source in sources or []:
                connection.execute(
                    "INSERT INTO memory_sources VALUES (?,?,?,?,?,?,?,?)",
                    (f"src-{uuid4().hex}", item_id, source["source_type"],
                     source["source_ref"], source.get("source_timestamp"),
                     source.get("relation", "supports"), source.get("excerpt_hash"), now),
                )
        return item_id

    def apply_seed(self, items: list[dict[str, Any]]) -> dict[str, int]:
        """Insert an explicit seed atomically, skipping only exact matches."""

        required = {
            "id", "namespace", "type", "title", "content", "status", "confidence",
            "owner", "classification", "created_at", "updated_at", "sources",
        }
        identifiers = [str(item.get("id", "")) for item in items]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("memory seed contains duplicate IDs")

        inserted = 0
        skipped = 0
        with closing(self._connect()) as connection, connection:
            for item in items:
                missing = sorted(required - item.keys())
                if missing:
                    raise ValueError(f"memory seed {item.get('id', '<unknown>')} missing fields: {', '.join(missing)}")

                item_id = str(item["id"])
                expected_item = (
                    item_id,
                    str(item["namespace"]),
                    str(item["type"]),
                    str(item["title"]),
                    str(item["content"]),
                    str(item["status"]),
                    float(item["confidence"]),
                    str(item["owner"]),
                    str(item["classification"]),
                    stable_json(item.get("metadata", {})),
                    str(item["created_at"]),
                    str(item["updated_at"]),
                    item.get("valid_from"),
                    item.get("valid_until"),
                )
                expected_sources = [
                    (
                        str(source["source_type"]),
                        str(source["source_ref"]),
                        source.get("source_timestamp"),
                        str(source.get("relation", "supports")),
                        source.get("excerpt_hash"),
                        str(source.get("created_at", item["created_at"])),
                    )
                    for source in item["sources"]
                ]

                existing = connection.execute(
                    "SELECT id,namespace,type,title,content,status,confidence,owner,classification,"
                    "metadata_json,created_at,updated_at,valid_from,valid_until "
                    "FROM memory_items WHERE id=?",
                    (item_id,),
                ).fetchone()
                if existing:
                    existing_sources = connection.execute(
                        "SELECT source_type,source_ref,source_timestamp,relation,excerpt_hash,created_at "
                        "FROM memory_sources WHERE memory_item_id=? ORDER BY id",
                        (item_id,),
                    ).fetchall()
                    if tuple(existing) != expected_item or [tuple(row) for row in existing_sources] != expected_sources:
                        raise MemoryConflictError(f"memory seed conflict for {item_id}")
                    skipped += 1
                    continue

                connection.execute(
                    "INSERT INTO memory_items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    expected_item,
                )
                for index, source in enumerate(expected_sources, start=1):
                    connection.execute(
                        "INSERT INTO memory_sources VALUES (?,?,?,?,?,?,?,?)",
                        (f"src-{item_id}-{index:02d}", item_id, *source),
                    )
                inserted += 1
        return {"inserted": inserted, "skipped": skipped}

    def record_project_state(
        self,
        project_id: str,
        state: Any,
        *,
        source: str,
        confidence: float,
        freshness: str,
        observed_at: str | None = None,
    ) -> str:
        serialized = stable_json(state)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        with closing(self._connect()) as connection, connection:
            latest = connection.execute(
                "SELECT id,state_hash FROM project_states WHERE project_id=? ORDER BY observed_at DESC LIMIT 1",
                (project_id,),
            ).fetchone()
            if latest and latest["state_hash"] == digest:
                return str(latest["id"])
            identifier = f"state-{uuid4().hex}"
            connection.execute(
                "INSERT INTO project_states VALUES (?,?,?,?,?,?,?,?)",
                (identifier, project_id, observed_at or utc_now(), source, serialized,
                 digest, confidence, freshness),
            )
        return identifier

    def latest_project_state(self, project_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM project_states WHERE project_id=? ORDER BY observed_at DESC LIMIT 1",
                (project_id,),
            ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["state"] = json.loads(result.pop("state_json"))
        result.pop("state_hash", None)
        return result

    def recent_memories(self, limit: int = 20) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT id,namespace,type,title,status,confidence,owner,classification,created_at,updated_at "
                "FROM memory_items ORDER BY updated_at DESC LIMIT ?", (max(1, min(limit, 100)),)
            ).fetchall()
        return [dict(row) for row in rows]

    def list_memories(self, *, item_type: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 100))
        with closing(self._connect()) as connection:
            if item_type:
                rows = connection.execute(
                    "SELECT id FROM memory_items WHERE type=? ORDER BY updated_at DESC,id LIMIT ?",
                    (item_type, safe_limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT id FROM memory_items ORDER BY updated_at DESC,id LIMIT ?",
                    (safe_limit,),
                ).fetchall()
        return [memory for row in rows if (memory := self.get_memory(str(row["id"]))) is not None]

    def get_memory(self, item_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            item = connection.execute("SELECT * FROM memory_items WHERE id=?", (item_id,)).fetchone()
            if not item:
                return None
            sources = connection.execute(
                "SELECT source_type,source_ref,source_timestamp,relation,excerpt_hash,created_at "
                "FROM memory_sources WHERE memory_item_id=? ORDER BY created_at", (item_id,)
            ).fetchall()
        result = dict(item)
        result["metadata"] = json.loads(result.pop("metadata_json"))
        result["sources"] = [dict(source) for source in sources]
        return result

    def record_audit(self, event: dict[str, Any]) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"audit-{uuid4().hex}", event["timestamp"], event["actor"],
                 event["client"], event["transport"], event["action"], event["target"],
                 event["result"], event["duration_ms"], event["arguments_hash"],
                 event["request_id"], stable_json(event.get("metadata", {}))),
            )

    def stats(self) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            counts = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("memory_items", "memory_sources", "project_states", "audit_events")
            }
        return {"path": str(self.path), "counts": counts}


class SQLiteAuditSink:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def record(self, event: dict[str, Any]) -> None:
        self.store.record_audit(event)
