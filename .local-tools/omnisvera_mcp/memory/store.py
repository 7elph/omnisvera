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
