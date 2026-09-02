from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .recall import query_terms, rank, validate_options


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

    def _compute_observation_hash(
        self,
        world_id: str,
        signal_id: str,
        entity_ref: str | None,
        observed_at: str,
        value: Any,
    ) -> str:
        """Compute deterministic SHA-256 hash for signal observation identity.

        Hashes: world_id, signal_id, entity_ref, observed_at, canonical(value).
        source/metadata do NOT participate in identity (v0.2).
        """
        canonical_value = stable_json(value)
        entity_part = entity_ref if entity_ref is not None else ""
        payload = f"{world_id}\x00{signal_id}\x00{entity_part}\x00{observed_at}\x00{canonical_value}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

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
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    snapshot_memory_id TEXT NOT NULL REFERENCES memory_items(id),
                    snapshot_hash TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    probability REAL NOT NULL CHECK(probability >= 0.0 AND probability <= 1.0),
                    horizon TEXT NOT NULL,
                    resolution_rule_json TEXT NOT NULL,
                    evidence_mode TEXT NOT NULL DEFAULT 'prospective' CHECK(evidence_mode IN ('prospective','retrospective')),
                    predictor_id TEXT,
                    predictor_version TEXT,
                    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','resolved','expired')),
                    created_at TEXT NOT NULL,
                    world_id TEXT,
                    subject_ref TEXT,
                    model_id TEXT,
                    predictor_type TEXT,
                    signals_used_json TEXT,
                    patterns_used_json TEXT,
                    reasoning_summary TEXT,
                    candidate_hash TEXT
                );
                CREATE TABLE IF NOT EXISTS prediction_resolutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER NOT NULL UNIQUE REFERENCES predictions(id),
                    resolved_at TEXT NOT NULL,
                    observed_value REAL,
                    outcome INTEGER NOT NULL CHECK(outcome IN (0, 1)),
                    calibration_score REAL,
                    sources_json TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_predictions_domain
                    ON predictions(domain, status);
                CREATE INDEX IF NOT EXISTS idx_predictions_status
                    ON predictions(status, created_at);
                CREATE TRIGGER IF NOT EXISTS trg_predictions_immutable
                    AFTER UPDATE ON predictions
                    FOR EACH ROW
                    WHEN OLD.domain != NEW.domain
                        OR OLD.snapshot_memory_id != NEW.snapshot_memory_id
                        OR OLD.snapshot_hash != NEW.snapshot_hash
                        OR OLD.claim != NEW.claim
                        OR OLD.probability != NEW.probability
                        OR OLD.horizon != NEW.horizon
                        OR OLD.resolution_rule_json != NEW.resolution_rule_json
                        OR OLD.evidence_mode != NEW.evidence_mode
                        OR (OLD.predictor_id IS NOT NULL AND OLD.predictor_id != NEW.predictor_id)
                        OR (OLD.predictor_version IS NOT NULL AND OLD.predictor_version != NEW.predictor_version)
                        OR OLD.created_at != NEW.created_at
                    BEGIN
                        SELECT RAISE(ABORT, 'prediction fields are immutable');
                    END;
                CREATE TABLE IF NOT EXISTS signal_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    world_id TEXT NOT NULL,
                    signal_id TEXT NOT NULL,
                    entity_ref TEXT,
                    schema TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    value_type TEXT NOT NULL,
                    unit TEXT,
                    observed_at TEXT NOT NULL,
                    source_json TEXT NOT NULL,
                    metadata_json TEXT,
                    recorded_at TEXT NOT NULL,
                    observation_hash TEXT
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_obs_hash
                    ON signal_observations(observation_hash);
                CREATE INDEX IF NOT EXISTS idx_signal_obs_world_signal
                    ON signal_observations(world_id, signal_id, observed_at);
                CREATE INDEX IF NOT EXISTS idx_signal_obs_entity
                    ON signal_observations(entity_ref, signal_id, observed_at);
                """
            )
            # Migration: add observation_hash to existing signal_observations
            try:
                connection.execute(
                    "ALTER TABLE signal_observations ADD COLUMN observation_hash TEXT"
                )
            except sqlite3.OperationalError:
                pass  # column already exists
            # Backfill hashes for existing rows without one
            rows = connection.execute(
                "SELECT id, world_id, signal_id, entity_ref, observed_at, value_json "
                "FROM signal_observations WHERE observation_hash IS NULL"
            ).fetchall()
            for row in rows:
                entity_part = row["entity_ref"] if row["entity_ref"] is not None else ""
                payload = (
                    f"{row['world_id']}\x00{row['signal_id']}\x00"
                    f"{entity_part}\x00{row['observed_at']}\x00{row['value_json']}"
                )
                obs_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
                connection.execute(
                    "UPDATE signal_observations SET observation_hash=? WHERE id=?",
                    (obs_hash, row["id"]),
                )
            # Create unique index if not exists (safe for existing data)
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_obs_hash "
                "ON signal_observations(observation_hash)"
            )
            # Migration: add prediction provenance columns
            for col in ("world_id", "subject_ref", "model_id", "predictor_type",
                        "signals_used_json", "patterns_used_json", "reasoning_summary"):
                try:
                    connection.execute(f"ALTER TABLE predictions ADD COLUMN {col} TEXT")
                except sqlite3.OperationalError:
                    pass  # column already exists
            # Migration: add evidence_mode for retrospective predictions
            try:
                connection.execute(
                    "ALTER TABLE predictions ADD COLUMN evidence_mode TEXT NOT NULL DEFAULT 'prospective'"
                )
            except sqlite3.OperationalError:
                pass  # column already exists
            # Create index on evidence_mode (safe for existing data)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_predictions_evidence "
                "ON predictions(evidence_mode, status)"
            )
            # Migration: add candidate_hash for idempotency
            try:
                connection.execute("ALTER TABLE predictions ADD COLUMN candidate_hash TEXT")
            except sqlite3.OperationalError:
                pass  # column already exists
            # Create unique index on candidate_hash (safe for existing data)
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_predictions_candidate_hash "
                "ON predictions(candidate_hash)"
            )
            # Migration: add snapshot_hash for integrity verification
            try:
                connection.execute(
                    "ALTER TABLE predictions ADD COLUMN snapshot_hash TEXT NOT NULL DEFAULT ''"
                )
            except sqlite3.OperationalError:
                pass  # column already exists
            # Migration: add predictor_id and predictor_version
            for col in ("predictor_id", "predictor_version"):
                try:
                    connection.execute(f"ALTER TABLE predictions ADD COLUMN {col} TEXT")
                except sqlite3.OperationalError:
                    pass  # column already exists
            # Backfill snapshot_hash for existing predictions
            rows = connection.execute(
                "SELECT p.id, m.content FROM predictions p "
                "JOIN memory_items m ON p.snapshot_memory_id = m.id "
                "WHERE p.snapshot_hash IS NULL OR p.snapshot_hash = ''"
            ).fetchall()
            for row in rows:
                content_hash = hashlib.sha256(
                    row["content"].encode("utf-8")
                ).hexdigest()
                connection.execute(
                    "UPDATE predictions SET snapshot_hash=? WHERE id=?",
                    (content_hash, row["id"]),
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

    def search_memories(
        self, query: str, *, item_type: str | None = None, limit: int = 10,
    ) -> list[dict[str, Any]]:
        item_type = validate_options(item_type, limit)
        normalized, terms = query_terms(query)
        with closing(self._connect()) as connection:
            # Rank the entire eligible collection before applying the result limit.
            rows = connection.execute(
                "SELECT id,title,content FROM memory_items WHERE (? IS NULL OR type=?)",
                (item_type, item_type),
            )
            ranked = []
            for row in rows:
                score = rank(normalized, terms, item_id=row["id"],
                             title=row["title"], content=row["content"])
                if score is not None:
                    ranked.append((tuple(-part for part in score), row["id"]))
        ranked.sort()  # Equal scores break by stable ID, never insertion order.
        return [item for _, item_id in ranked[:limit]
                if (item := self.get_memory(item_id)) is not None]

    def recall_recent(
        self, *, item_type: str | None = None, limit: int = 10,
    ) -> list[dict[str, Any]]:
        item_type = validate_options(item_type, limit)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT id FROM memory_items WHERE (? IS NULL OR type=?) "
                "ORDER BY julianday(updated_at) DESC,id LIMIT ?",
                (item_type, item_type, limit),
            ).fetchall()
        return [item for row in rows
                if (item := self.get_memory(row["id"])) is not None]

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

    # -- Epistemic Loop ---------------------------------------------------

    def create_snapshot_memory(
        self,
        *,
        domain: str,
        subject: str,
        state: dict[str, Any],
        sources: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a model_snapshot memory item. Returns the memory item ID."""
        return self.add_memory(
            namespace="omnisvera",
            item_type="model_snapshot",
            title=f"{domain} — {subject}",
            content=stable_json(state),
            status="immutable",
            confidence=1.0,
            owner="omnisvera",
            classification="internal",
            metadata={**(metadata or {}), "domain": domain, "subject": subject},
            sources=sources or [],
        )

    def create_prediction(
        self,
        *,
        domain: str,
        snapshot_memory_id: str,
        claim: str,
        probability: float,
        horizon: str,
        resolution_rule: dict[str, Any],
        evidence_mode: str = "prospective",
        predictor_id: str | None = None,
        predictor_version: str | None = None,
        world_id: str | None = None,
        subject_ref: str | None = None,
        model_id: str | None = None,
        predictor_type: str | None = None,
        signals_used: list[dict[str, Any]] | None = None,
        patterns_used: list[dict[str, Any]] | None = None,
        reasoning_summary: str | None = None,
        candidate_hash: str | None = None,
    ) -> int:
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be between 0.0 and 1.0")
        if evidence_mode not in ("prospective", "retrospective"):
            raise ValueError("evidence_mode must be 'prospective' or 'retrospective'")
        now = utc_now()
        with closing(self._connect()) as connection, connection:
            snapshot = connection.execute(
                "SELECT id, content FROM memory_items WHERE id=?", (snapshot_memory_id,),
            ).fetchone()
            if not snapshot:
                raise ValueError(f"snapshot not found: {snapshot_memory_id}")
            snapshot_hash = hashlib.sha256(
                snapshot["content"].encode("utf-8")
            ).hexdigest()
            cursor = connection.execute(
                "INSERT INTO predictions "
                "(domain, snapshot_memory_id, snapshot_hash, claim, probability, "
                "horizon, resolution_rule_json, evidence_mode, predictor_id, predictor_version, "
                "status, created_at, world_id, subject_ref, model_id, predictor_type, "
                "signals_used_json, patterns_used_json, reasoning_summary, candidate_hash) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (domain, snapshot_memory_id, snapshot_hash, claim, probability, horizon,
                 stable_json(resolution_rule), evidence_mode, predictor_id, predictor_version,
                 "open", now, world_id, subject_ref, model_id, predictor_type,
                 stable_json(signals_used) if signals_used else None,
                 stable_json(patterns_used) if patterns_used else None,
                 reasoning_summary, candidate_hash),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_prediction(self, prediction_id: int) -> dict[str, Any] | None:
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT * FROM predictions WHERE id=?", (prediction_id,),
            ).fetchone()
            if not row:
                return None
            result = dict(row)
            result["resolution_rule"] = json.loads(result.pop("resolution_rule_json"))
            # Verify snapshot integrity
            snapshot = connection.execute(
                "SELECT content FROM memory_items WHERE id=?",
                (result["snapshot_memory_id"],),
            ).fetchone()
            if snapshot:
                current_hash = hashlib.sha256(
                    snapshot["content"].encode("utf-8")
                ).hexdigest()
                result["snapshot_intact"] = current_hash == result["snapshot_hash"]
            else:
                result["snapshot_intact"] = False
            resolution = connection.execute(
                "SELECT * FROM prediction_resolutions WHERE prediction_id=?",
                (prediction_id,),
            ).fetchone()
            if resolution:
                result["resolution"] = dict(resolution)
            return result

    def find_prediction_by_hash(self, candidate_hash: str) -> int | None:
        """Find existing prediction by candidate_hash for idempotency.

        Returns prediction_id if found, None otherwise.
        """
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT id FROM predictions WHERE candidate_hash=?",
                (candidate_hash,),
            ).fetchone()
            return row["id"] if row else None

    def list_predictions(
        self,
        *,
        domain: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 100))
        clauses = []
        params: list[Any] = []
        if domain:
            clauses.append("domain=?")
            params.append(domain)
        if status:
            clauses.append("status=?")
            params.append(status)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(safe_limit)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT id FROM predictions{where} ORDER BY created_at DESC, id LIMIT ?",
                params,
            ).fetchall()
        return [p for row in rows if (p := self.get_prediction(int(row["id"]))) is not None]

    def resolve_prediction(
        self,
        prediction_id: int,
        *,
        observed_value: float | None = None,
        outcome: int,
        sources: list[str] | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if outcome not in (0, 1):
            raise ValueError("outcome must be 0 or 1")
        now = utc_now()
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT id, status, probability, snapshot_memory_id, snapshot_hash "
                "FROM predictions WHERE id=?",
                (prediction_id,),
            ).fetchone()
            if not row:
                raise ValueError(f"prediction not found: {prediction_id}")
            if row["status"] != "open":
                raise ValueError(
                    f"prediction {prediction_id} already {row['status']}, cannot resolve"
                )
            # Verify snapshot integrity before resolution
            snapshot = connection.execute(
                "SELECT content FROM memory_items WHERE id=?",
                (row["snapshot_memory_id"],),
            ).fetchone()
            if snapshot:
                current_hash = hashlib.sha256(
                    snapshot["content"].encode("utf-8")
                ).hexdigest()
                if current_hash != row["snapshot_hash"]:
                    raise ValueError("snapshot integrity mismatch")
            probability = float(row["probability"])
            calibration_score = round((probability - outcome) ** 2, 8)
            connection.execute(
                "INSERT INTO prediction_resolutions "
                "(prediction_id, resolved_at, observed_value, outcome, calibration_score, "
                "sources_json, notes, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (prediction_id, now, observed_value, outcome, calibration_score,
                 stable_json(sources or []), notes, now),
            )
            connection.execute(
                "UPDATE predictions SET status='resolved' WHERE id=?",
                (prediction_id,),
            )
        return self.get_prediction(prediction_id)  # type: ignore[return-value]

    def calibration_summary(
        self,
        *,
        domain: str | None = None,
        evidence_mode: str = "prospective",
    ) -> dict[str, Any]:
        if evidence_mode not in ("prospective", "retrospective", "all"):
            raise ValueError("evidence_mode must be 'prospective', 'retrospective', or 'all'")
        with closing(self._connect()) as connection:
            if evidence_mode == "all":
                if domain:
                    row = connection.execute(
                        "SELECT COUNT(*) as count, AVG(r.calibration_score) as mean_brier, "
                        "p.evidence_mode "
                        "FROM predictions p "
                        "JOIN prediction_resolutions r ON r.prediction_id = p.id "
                        "WHERE p.domain=? "
                        "GROUP BY p.evidence_mode",
                        (domain,),
                    ).fetchall()
                else:
                    row = connection.execute(
                        "SELECT COUNT(*) as count, AVG(r.calibration_score) as mean_brier, "
                        "p.evidence_mode "
                        "FROM predictions p "
                        "JOIN prediction_resolutions r ON r.prediction_id = p.id "
                        "GROUP BY p.evidence_mode",
                    ).fetchall()
                breakdown = {}
                total_count = 0
                total_brier_sum = 0.0
                for r in row:
                    mode = r["evidence_mode"]
                    breakdown[mode] = {
                        "count": r["count"],
                        "mean_brier": round(r["mean_brier"], 8) if r["mean_brier"] is not None else None,
                    }
                    total_count += r["count"]
                    if r["mean_brier"] is not None:
                        total_brier_sum += r["mean_brier"] * r["count"]
                return {
                    "domain": domain,
                    "evidence_mode": "all",
                    "count": total_count,
                    "mean_brier": round(total_brier_sum / total_count, 8) if total_count else None,
                    "breakdown": breakdown,
                }
            else:
                if domain:
                    row = connection.execute(
                        "SELECT COUNT(*) as count, AVG(r.calibration_score) as mean_brier "
                        "FROM predictions p "
                        "JOIN prediction_resolutions r ON r.prediction_id = p.id "
                        "WHERE p.domain=? AND p.evidence_mode=?",
                        (domain, evidence_mode),
                    ).fetchone()
                else:
                    row = connection.execute(
                        "SELECT COUNT(*) as count, AVG(r.calibration_score) as mean_brier "
                        "FROM predictions p "
                        "JOIN prediction_resolutions r ON r.prediction_id = p.id "
                        "WHERE p.evidence_mode=?",
                        (evidence_mode,),
                    ).fetchone()
            return {
                "domain": domain,
                "evidence_mode": evidence_mode,
                "count": row["count"],
                "mean_brier": round(row["mean_brier"], 8) if row["mean_brier"] is not None else None,
            }

    def get_due_predictions(
        self,
        *,
        now: str | None = None,
        domain: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Find open predictions whose horizon has passed (due for resolution)."""
        now = now or utc_now()
        safe_limit = max(1, min(int(limit), 200))
        clauses = ["status='open'", "horizon<=?"]
        params: list[Any] = [now]
        if domain:
            clauses.append("domain=?")
            params.append(domain)
        params.append(safe_limit)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT id FROM predictions WHERE {' AND '.join(clauses)} "
                "ORDER BY horizon ASC, id LIMIT ?",
                params,
            ).fetchall()
        return [p for row in rows if (p := self.get_prediction(int(row["id"]))) is not None]

    def void_prediction(self, prediction_id: int, *, notes: str | None = None) -> dict[str, Any]:
        """Mark a prediction as void (cancelled/invalid) without Brier score."""
        now = utc_now()
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT id, status FROM predictions WHERE id=?",
                (prediction_id,),
            ).fetchone()
            if not row:
                raise ValueError(f"prediction not found: {prediction_id}")
            if row["status"] != "open":
                raise ValueError(
                    f"prediction {prediction_id} already {row['status']}, cannot void"
                )
            connection.execute(
                "UPDATE predictions SET status='expired' WHERE id=?",
                (prediction_id,),
            )
            # Record void resolution (no Brier)
            connection.execute(
                "INSERT INTO prediction_resolutions "
                "(prediction_id, resolved_at, observed_value, outcome, calibration_score, "
                "sources_json, notes, created_at) VALUES (?,?,NULL,?,NULL,?,?,?)",
                (prediction_id, now, None, stable_json(["void"]), notes or "voided", now),
            )
        return self.get_prediction(prediction_id)  # type: ignore[return-value]

    # -- Signal History --------------------------------------------------------

    def capture_signal(
        self,
        *,
        world_id: str,
        signal_id: str,
        entity_ref: str | None,
        schema: str,
        value: Any,
        value_type: str,
        unit: str | None,
        observed_at: str,
        source: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist a single signal observation. Idempotent.

        Returns:
            {"status": "recorded", "id": <row_id>}
            or {"status": "duplicate", "id": <existing_row_id>}
        """
        observation_hash = self._compute_observation_hash(
            world_id, signal_id, entity_ref, observed_at, value,
        )
        recorded_at = utc_now()
        with closing(self._connect()) as connection, connection:
            # Check if hash already exists
            existing = connection.execute(
                "SELECT id FROM signal_observations WHERE observation_hash=?",
                (observation_hash,),
            ).fetchone()
            if existing is not None:
                return {"status": "duplicate", "id": existing["id"]}
            try:
                cursor = connection.execute(
                    "INSERT INTO signal_observations "
                    "(world_id, signal_id, entity_ref, schema, value_json, value_type, "
                    "unit, observed_at, source_json, metadata_json, recorded_at, observation_hash) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        world_id,
                        signal_id,
                        entity_ref,
                        schema,
                        stable_json(value),
                        value_type,
                        unit,
                        observed_at,
                        stable_json(source),
                        stable_json(metadata or {}),
                        recorded_at,
                        observation_hash,
                    ),
                )
                return {"status": "recorded", "id": cursor.lastrowid or 0}
            except sqlite3.IntegrityError:
                # Race condition: another connection inserted the same hash
                existing = connection.execute(
                    "SELECT id FROM signal_observations WHERE observation_hash=?",
                    (observation_hash,),
                ).fetchone()
                return {"status": "duplicate", "id": existing["id"] if existing else 0}

    def capture_signals(self, signals: list[dict[str, Any]]) -> dict[str, Any]:
        """Persist a batch of WorldSignal dicts. Idempotent.

        Returns summary: observed, recorded, duplicates_ignored, world_id.
        """
        recorded = 0
        duplicates = 0
        world_id = ""
        for sig in signals:
            world_id = sig.get("world_id", "")
            result = self.capture_signal(
                world_id=world_id,
                signal_id=sig.get("signal_id", ""),
                entity_ref=sig.get("entity_ref"),
                schema=sig.get("schema", ""),
                value=sig.get("value"),
                value_type=sig.get("value_type", ""),
                unit=sig.get("unit"),
                observed_at=sig.get("observed_at", ""),
                source=sig.get("source", {}),
                metadata=sig.get("metadata"),
            )
            if result["status"] == "recorded":
                recorded += 1
            else:
                duplicates += 1
        return {
            "observed": len(signals),
            "recorded": recorded,
            "duplicates_ignored": duplicates,
            "world_id": world_id,
        }

    def signal_history(
        self,
        world_id: str,
        signal_id: str,
        entity_ref: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query signal observations ordered by observed_at ascending."""
        query = (
            "SELECT id, world_id, signal_id, entity_ref, schema, "
            "value_json, value_type, unit, observed_at, source_json, "
            "metadata_json, recorded_at "
            "FROM signal_observations "
            "WHERE world_id=? AND signal_id=?"
        )
        params: list[Any] = [world_id, signal_id]

        if entity_ref is not None:
            query += " AND entity_ref=?"
            params.append(entity_ref)
        if since is not None:
            query += " AND observed_at>=?"
            params.append(since)
        if until is not None:
            query += " AND observed_at<=?"
            params.append(until)

        query += " ORDER BY observed_at ASC LIMIT ?"
        params.append(limit)

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()
            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "world_id": row["world_id"],
                    "signal_id": row["signal_id"],
                    "entity_ref": row["entity_ref"],
                    "schema": row["schema"],
                    "value": json.loads(row["value_json"]),
                    "value_type": row["value_type"],
                    "unit": row["unit"],
                    "observed_at": row["observed_at"],
                    "source": json.loads(row["source_json"]),
                    "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else {},
                    "recorded_at": row["recorded_at"],
                })
            return results

    def signal_changes(
        self,
        world_id: str,
        signal_id: str,
        entity_ref: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Detect changes between consecutive signal observations.

        Returns list of SignalChange dicts comparing each observation
        to its predecessor.
        """
        history = self.signal_history(world_id, signal_id, entity_ref, limit=limit)
        if len(history) < 2:
            return []

        changes = []
        for i in range(1, len(history)):
            prev = history[i - 1]
            curr = history[i]
            prev_val = prev["value"]
            curr_val = curr["value"]

            if prev_val == curr_val:
                change_type = "unchanged"
                delta = None
                delta_percent = None
            elif prev_val is None and curr_val is not None:
                change_type = "appeared"
                delta = None
                delta_percent = None
            elif prev_val is not None and curr_val is None:
                change_type = "disappeared"
                delta = None
                delta_percent = None
            else:
                change_type = "changed"
                delta = None
                delta_percent = None
                # Calculate numeric delta when valid
                if isinstance(prev_val, (int, float)) and isinstance(curr_val, (int, float)):
                    delta = curr_val - prev_val
                    if prev_val != 0:
                        delta_percent = round((delta / abs(prev_val)) * 100, 2)

            changes.append({
                "world_id": world_id,
                "signal_id": signal_id,
                "entity_ref": entity_ref,
                "previous_value": prev_val,
                "current_value": curr_val,
                "previous_observed_at": prev["observed_at"],
                "current_observed_at": curr["observed_at"],
                "change_type": change_type,
                "delta": delta,
                "delta_percent": delta_percent,
            })

        return changes

    # -- Pattern Detection -----------------------------------------------------

    def signal_patterns(
        self,
        world_id: str,
        signal_id: str,
        entity_ref: str | None = None,
        since: str | None = None,
        until: str | None = None,
        pattern_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Detect patterns in signal history. Derived on demand, not persisted.

        Returns list of SignalPattern dicts.
        """
        history = self.signal_history(world_id, signal_id, entity_ref, since, until, limit)
        patterns: list[dict[str, Any]] = []

        if pattern_type is None or pattern_type == "trend":
            trend = self._detect_trend(history)
            if trend is not None:
                patterns.append(trend)

        if pattern_type is None or pattern_type == "anomaly":
            anomalies = self._detect_anomalies(history)
            patterns.extend(anomalies)

        return patterns

    def signals_for_world(
        self,
        world_id: str,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Return all signal observations for a world, ordered by observed_at ascending."""
        query = (
            "SELECT id, world_id, signal_id, entity_ref, schema, "
            "value_json, value_type, unit, observed_at, source_json, "
            "metadata_json, recorded_at "
            "FROM signal_observations "
            "WHERE world_id=? "
            "ORDER BY observed_at ASC LIMIT ?"
        )
        with closing(self._connect()) as connection:
            rows = connection.execute(query, (world_id, limit)).fetchall()
            return [
                {
                    "id": row["id"],
                    "world_id": row["world_id"],
                    "signal_id": row["signal_id"],
                    "entity_ref": row["entity_ref"],
                    "schema": row["schema"],
                    "value": json.loads(row["value_json"]),
                    "value_type": row["value_type"],
                    "unit": row["unit"],
                    "observed_at": row["observed_at"],
                    "source": json.loads(row["source_json"]),
                    "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else {},
                    "recorded_at": row["recorded_at"],
                }
                for row in rows
            ]

    def patterns_for_world(
        self,
        world_id: str,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Return all signal patterns for a world, derived on demand."""
        signals = self.signals_for_world(world_id, limit=limit)
        # Group by (entity_ref, signal_id) to compute patterns per signal
        seen: set[tuple[str | None, str]] = set()
        patterns: list[dict[str, Any]] = []
        for sig in signals:
            key = (sig.get("entity_ref"), sig.get("signal_id", ""))
            if key in seen:
                continue
            seen.add(key)
            sig_patterns = self.signal_patterns(
                world_id=world_id,
                signal_id=sig["signal_id"],
                entity_ref=sig.get("entity_ref"),
            )
            patterns.extend(sig_patterns)
        return patterns

    def _detect_trend(self, history: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Detect trend in numeric signal history.

        Requires >= 2 observations with numeric values.
        Method: linear regression slope + structural classification.
        """
        numeric = [(h["observed_at"], h["value"], h["id"])
                    for h in history
                    if isinstance(h["value"], (int, float))]

        if len(numeric) < 2:
            return None

        values = [v for _, v, _ in numeric]
        n = len(values)

        first_value = values[0]
        last_value = values[-1]
        abs_change = last_value - first_value
        pct_change = (abs_change / abs(first_value) * 100) if first_value != 0 else None
        mean_val = sum(values) / n
        min_val = min(values)
        max_val = max(values)

        # Slope via least squares
        x_mean = (n - 1) / 2
        y_mean = mean_val
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0.0

        # Structural classification
        threshold = abs(mean_val) * 0.01 if mean_val != 0 else 0.001
        if slope > threshold:
            classification = "increasing"
        elif slope < -threshold:
            classification = "decreasing"
        else:
            classification = "stable"

        observation_ids = [oid for _, _, oid in numeric]

        return {
            "world_id": history[0]["world_id"] if history else "",
            "signal_id": history[0]["signal_id"] if history else "",
            "entity_ref": history[0].get("entity_ref"),
            "pattern_type": "trend",
            "window_start": numeric[0][0],
            "window_end": numeric[-1][0],
            "observation_count": n,
            "metrics": {
                "first_value": first_value,
                "last_value": last_value,
                "absolute_change": round(abs_change, 8),
                "percent_change": round(pct_change, 2) if pct_change is not None else None,
                "mean": round(mean_val, 8),
                "min": min_val,
                "max": max_val,
                "slope": round(slope, 8),
                "classification": classification,
            },
            "confidence": None,
            "method": "linear_regression",
            "method_version": "1.0",
            "provenance": {
                "observation_ids": observation_ids,
                "input_count": n,
                "numeric_values": values,
            },
        }

    def _detect_anomalies(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Detect anomalies using z-score method.

        For each observation, compute z-score against all PREVIOUS observations.
        Requires >= 5 prior observations for baseline.
        An observation is anomalous if |z-score| > 2.0.
        """
        numeric = [(h["observed_at"], h["value"], h["id"])
                    for h in history
                    if isinstance(h["value"], (int, float))]

        MIN_BASELINE = 5
        Z_THRESHOLD = 2.0
        anomalies: list[dict[str, Any]] = []

        for i in range(MIN_BASELINE, len(numeric)):
            candidate_at, candidate_val, candidate_id = numeric[i]
            baseline_vals = [v for _, v, _ in numeric[:i]]

            mean_val = sum(baseline_vals) / len(baseline_vals)
            variance = sum((v - mean_val) ** 2 for v in baseline_vals) / len(baseline_vals)
            std_val = variance ** 0.5

            if std_val == 0:
                # Baseline is constant; any different value is infinitely anomalous
                z_score = float("inf") if candidate_val != mean_val else 0.0
            else:
                z_score = (candidate_val - mean_val) / std_val

            is_anomalous = abs(z_score) > Z_THRESHOLD

            if is_anomalous:
                anomalies.append({
                    "world_id": history[0]["world_id"] if history else "",
                    "signal_id": history[0]["signal_id"] if history else "",
                    "entity_ref": history[0].get("entity_ref"),
                    "pattern_type": "anomaly",
                    "window_start": numeric[0][0],
                    "window_end": candidate_at,
                    "observation_count": i + 1,
                    "metrics": {
                        "value": candidate_val,
                        "baseline_mean": round(mean_val, 8),
                        "baseline_std": round(std_val, 8),
                        "z_score": round(z_score, 4),
                        "threshold": Z_THRESHOLD,
                        "anomalous": True,
                    },
                    "confidence": None,
                    "method": "z_score",
                    "method_version": "1.0",
                    "provenance": {
                        "observation_ids": [oid for _, _, oid in numeric[:i + 1]],
                        "candidate_id": candidate_id,
                        "baseline_count": i,
                        "candidate_index": i,
                    },
                })

        return anomalies

    def stats(self) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            counts = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in (
                    "memory_items", "memory_sources", "project_states", "audit_events",
                    "predictions", "prediction_resolutions", "signal_observations",
                )
            }
        return {"path": str(self.path), "counts": counts}


class SQLiteAuditSink:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def record(self, event: dict[str, Any]) -> None:
        self.store.record_audit(event)
