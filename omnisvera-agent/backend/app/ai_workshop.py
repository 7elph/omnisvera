"""Persistent, private AI workshop queue (AI-WORKSHOP-20261020).

This is the first production block: deterministic planning, explicit
dependencies, one-worker leases, retries/backoff/quota gates, measured runs and
draft-only outputs. It never publishes, approves, edits sheets/Vault content or
executes model suggestions. Provider adapters live in ``ai_workshop_adapters``.

Only SQLite is used. The workshop database is separate by default so planning
and tests cannot mutate the campaign database.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

QUEUES = ("text", "image", "code")
JOB_STATUSES = {
    "queued",
    "running",
    "awaiting_approval",
    "external_pending",
    "completed",
    "failed",
    "blocked",
    "needs_review",
    "waiting_permission",
    "cancelled",
}
SUCCESS_STATUSES = {"completed", "awaiting_approval"}
FAILURE_STATUSES = {"failed", "cancelled"}
DRAFT_STATUSES = {"awaiting_approval", "completed", "external_pending", "needs_review"}
WORKER_STATES = {"stopped", "running", "paused"}
TABLE_STATES = {"inactive", "session", "combat", "unknown"}
OUTPUT_FIELDS = ("sources", "revision", "facts", "suggestions", "questions")
MAX_JSON_CHARS = 50000
MAX_DEPTH = 48
MAX_ATTEMPTS = 5
BACKOFF_BASE_SECONDS = 15
BACKOFF_CAP_SECONDS = 3600
MAX_VARIANTS = 3
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{8,120}$")
_RAM_UNSET = object()
_SECRET_ENV_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "APIKEY", "ACCESS_KEY", "PRIVATE_KEY")
_SECRET_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret|password)\s*[:=]\s*)[^\s\"',;]{6,}"),
)


class WorkshopError(ValueError):
    """Bounded workshop error with a stable code (never secret material)."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class CheckoutLockBusy(RuntimeError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _now_iso(now: datetime | None) -> str:
    return _iso(now or _utcnow())


def new_request_id(prefix: str = "aw") -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _request_id(value: Any) -> str:
    request_id = str(value or "").strip()
    if not REQUEST_ID_RE.fullmatch(request_id):
        raise WorkshopError("invalid_request_id")
    return request_id


def _text(value: Any, code: str, *, limit: int = 200) -> str:
    result = str(value or "").strip()
    if not result or len(result) > limit:
        raise WorkshopError(code)
    return result


def _check_depth(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise WorkshopError("json_too_deep")
    if isinstance(value, dict):
        for item in value.values():
            _check_depth(item, depth + 1)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_depth(item, depth + 1)


def _json_text(value: Any) -> str:
    _check_depth(value)
    try:
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError, RecursionError) as error:
        raise WorkshopError("invalid_json") from error
    if len(raw) > MAX_JSON_CHARS:
        raise WorkshopError("json_too_large")
    return raw


def _sensitive_values() -> tuple[str, ...]:
    values = set()
    for name, value in os.environ.items():
        if any(marker in name.upper() for marker in _SECRET_ENV_MARKERS):
            if value and len(value) >= 6:
                values.add(value)
    return tuple(sorted(values, key=len, reverse=True))


def scrub_secrets(text: Any) -> str:
    """Remove obvious credentials and configured secret values before storage."""
    result = str(text)
    for secret in _sensitive_values():
        if secret in result:
            result = result.replace(secret, "[redacted]")
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(r"\1[redacted]", result)
    return result


def _scrub_value(value: Any) -> Any:
    if isinstance(value, str):
        return scrub_secrets(value)
    if isinstance(value, dict):
        return {scrub_secrets(key): _scrub_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub_value(item) for item in value]
    return value


def _payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise WorkshopError("payload_must_be_object")
    return _scrub_value(value)


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def _read_connection(database_path: Path) -> sqlite3.Connection:
    database_path = Path(database_path).resolve()
    if not database_path.is_file():
        raise FileNotFoundError("workshop database unavailable")
    connection = sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def init_workshop(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS ai_workshop_jobs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              queue TEXT NOT NULL,
              entity_type TEXT NOT NULL,
              entity_id TEXT NOT NULL,
              revision TEXT NOT NULL,
              purpose TEXT NOT NULL,
              priority INTEGER NOT NULL DEFAULT 100,
              gap INTEGER NOT NULL DEFAULT 0,
              variant_of INTEGER,
              dedupe_key TEXT NOT NULL UNIQUE,
              depends_on_json TEXT NOT NULL DEFAULT '[]',
              status TEXT NOT NULL DEFAULT 'queued',
              attempts INTEGER NOT NULL DEFAULT 0,
              max_attempts INTEGER NOT NULL DEFAULT 5,
              recoveries INTEGER NOT NULL DEFAULT 0,
              available_at TEXT NOT NULL,
              lease_owner TEXT,
              lease_token TEXT,
              lease_expires_at TEXT,
              payload_json TEXT NOT NULL DEFAULT '{}',
              output_json TEXT,
              error_code TEXT,
              blocked_reason TEXT,
              external_ref TEXT,
              request_id TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              started_at TEXT,
              finished_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_ai_workshop_claim
              ON ai_workshop_jobs(status, queue, available_at, priority);
            CREATE TABLE IF NOT EXISTS ai_workshop_receipts (
              request_id TEXT PRIMARY KEY,
              fingerprint TEXT NOT NULL,
              response_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ai_workshop_metrics (
              job_id INTEGER PRIMARY KEY,
              queue TEXT NOT NULL,
              provider TEXT,
              model TEXT,
              duration_ms INTEGER,
              wait_ms INTEGER,
              samples INTEGER,
              ok INTEGER NOT NULL,
              tokens_in INTEGER,
              tokens_out INTEGER,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ai_workshop_providers (
              queue TEXT NOT NULL,
              provider TEXT NOT NULL,
              documented_limit TEXT,
              configured_limit INTEGER,
              observed_remaining INTEGER,
              observed_reset_at TEXT,
              retry_after_at TEXT,
              cooldown_until TEXT,
              auth_failed INTEGER NOT NULL DEFAULT 0,
              blocked_reason TEXT,
              updated_at TEXT NOT NULL,
              PRIMARY KEY(queue, provider)
            );
            CREATE TABLE IF NOT EXISTS ai_workshop_control (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ai_workshop_queue_state (
              queue TEXT PRIMARY KEY,
              paused INTEGER NOT NULL DEFAULT 0,
              reason TEXT,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ai_workshop_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              job_id INTEGER,
              event TEXT NOT NULL,
              detail_json TEXT,
              created_at TEXT NOT NULL
            );
            INSERT OR IGNORE INTO ai_workshop_control(key,value,updated_at)
              VALUES('worker_state','stopped',datetime('now'));
            """
        )


def _event(connection: sqlite3.Connection, job_id: int | None, event: str,
           detail: dict[str, Any] | None = None, now: datetime | None = None) -> None:
    connection.execute(
        "INSERT INTO ai_workshop_events(job_id,event,detail_json,created_at) VALUES(?,?,?,?)",
        (job_id, event, _json_text(_scrub_value(detail or {})), _now_iso(now)),
    )


def _job_dto(row: sqlite3.Row) -> dict[str, Any]:
    record = dict(row)
    for key in ("depends_on_json", "payload_json", "output_json"):
        if key in record and isinstance(record[key], str):
            try:
                record[key] = json.loads(record[key])
            except (TypeError, ValueError):
                record[key] = None
    record["gap"] = bool(record.get("gap"))
    return record


def _job_by_id(connection: sqlite3.Connection, job_id: int) -> dict[str, Any]:
    row = connection.execute("SELECT * FROM ai_workshop_jobs WHERE id=?", (job_id,)).fetchone()
    if row is None:
        raise WorkshopError("job_not_found")
    return _job_dto(row)


def _dedupe_key(queue: str, entity_type: str, entity_id: str, revision: str,
                purpose: str, variant_of: int | None) -> str:
    raw = "\0".join((queue, entity_type, entity_id, revision, purpose, str(variant_of or "")))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate_queue(queue: Any) -> str:
    value = str(queue or "").strip()
    if value not in QUEUES:
        raise WorkshopError("invalid_queue")
    return value


def enqueue_job(
    database_path: Path,
    *,
    queue: str,
    entity_type: str,
    entity_id: str,
    revision: str,
    purpose: str,
    request_id: str,
    priority: int = 100,
    gap: bool = False,
    depends_on: Iterable[int] = (),
    variant_of: int | None = None,
    payload: dict[str, Any] | None = None,
    max_attempts: int = MAX_ATTEMPTS,
    max_variants: int = MAX_VARIANTS,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Enqueue one explicit job. Repeating the same intent returns the same job."""
    request_id = _request_id(request_id)
    queue = _validate_queue(queue)
    entity_type = _text(entity_type, "invalid_entity_type", limit=80)
    entity_id = _text(entity_id, "invalid_entity_id", limit=160)
    revision = _text(revision, "invalid_revision", limit=160)
    purpose = _text(purpose, "invalid_purpose", limit=160)
    if type(priority) is not int or not -100000 <= priority <= 100000:
        raise WorkshopError("invalid_priority")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 20:
        raise WorkshopError("invalid_max_attempts")
    if type(max_variants) is not int or not 0 <= max_variants <= 50:
        raise WorkshopError("invalid_max_variants")
    dependencies = sorted({int(item) for item in depends_on})
    if len(dependencies) > 50 or any(item < 1 for item in dependencies):
        raise WorkshopError("invalid_dependency")
    if variant_of is not None and (type(variant_of) is not int or variant_of < 1):
        raise WorkshopError("invalid_variant")
    payload = _payload(payload)
    timestamp = _now_iso(now)
    dedupe_key = _dedupe_key(queue, entity_type, entity_id, revision, purpose, variant_of)
    if variant_of is not None:
        # Equivalent attempts share intent but differ by explicit payload; exact
        # repeats still dedupe, while the variant ceiling caps the family.
        dedupe_key = hashlib.sha256(
            (dedupe_key + "\0" + _json_text(payload)).encode("utf-8")
        ).hexdigest()
    fingerprint = _json_text({
        "queue": queue,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "revision": revision,
        "purpose": purpose,
        "priority": priority,
        "gap": bool(gap),
        "depends_on": dependencies,
        "variant_of": variant_of,
        "payload": payload,
        "max_attempts": max_attempts,
    })
    init_workshop(Path(database_path))
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        receipt = connection.execute(
            "SELECT fingerprint,response_json FROM ai_workshop_receipts WHERE request_id=?",
            (request_id,),
        ).fetchone()
        if receipt is not None:
            if receipt["fingerprint"] != fingerprint:
                raise WorkshopError("request_id_conflict")
            return json.loads(receipt["response_json"])
        existing = connection.execute(
            "SELECT * FROM ai_workshop_jobs WHERE dedupe_key=?", (dedupe_key,)
        ).fetchone()
        if existing is not None:
            response = {"job": _job_dto(existing), "created": False}
            _store_receipt(connection, request_id, fingerprint, response)
            return response
        if variant_of is not None:
            parent = connection.execute(
                "SELECT * FROM ai_workshop_jobs WHERE id=?", (variant_of,)
            ).fetchone()
            if parent is None:
                raise WorkshopError("variant_parent_not_found")
            count = connection.execute(
                "SELECT COUNT(*) FROM ai_workshop_jobs WHERE variant_of=? AND entity_type=? "
                "AND entity_id=? AND revision=? AND purpose=?",
                (variant_of, entity_type, entity_id, revision, purpose),
            ).fetchone()[0]
            if int(count) >= max_variants:
                raise WorkshopError("variant_limit")
        for dependency in dependencies:
            row = connection.execute(
                "SELECT id FROM ai_workshop_jobs WHERE id=?", (dependency,)
            ).fetchone()
            if row is None:
                raise WorkshopError("dependency_not_found")
        cursor = connection.execute(
            "INSERT INTO ai_workshop_jobs(queue,entity_type,entity_id,revision,purpose,priority,"
            "gap,variant_of,dedupe_key,depends_on_json,status,attempts,max_attempts,available_at,"
            "payload_json,request_id,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,'queued',0,?,?,?,?,?,?)",
            (
                queue, entity_type, entity_id, revision, purpose, priority, int(bool(gap)),
                variant_of, dedupe_key, _json_text(dependencies), max_attempts, timestamp,
                _json_text(payload), request_id, timestamp, timestamp,
            ),
        )
        job_id = int(cursor.lastrowid)
        _event(connection, job_id, "enqueued", {"queue": queue, "gap": bool(gap)}, now)
        response = {"job": _job_by_id(connection, job_id), "created": True}
        _store_receipt(connection, request_id, fingerprint, response)
        return response


def _store_receipt(connection: sqlite3.Connection, request_id: str, fingerprint: str,
                   response: dict[str, Any]) -> None:
    connection.execute(
        "INSERT INTO ai_workshop_receipts(request_id,fingerprint,response_json) VALUES(?,?,?)",
        (request_id, fingerprint, _json_text(response)),
    )


def plan_jobs(targets: list[dict[str, Any]], *, max_variants: int = MAX_VARIANTS) -> dict[str, Any]:
    """Deterministic, side-effect-free plan. Real gaps sort before variants."""
    if not isinstance(targets, list):
        raise WorkshopError("plan_must_be_list")
    planned: dict[str, dict[str, Any]] = {}
    for target in targets:
        if not isinstance(target, dict):
            raise WorkshopError("invalid_plan_target")
        queue = _validate_queue(target.get("queue"))
        entity_type = _text(target.get("entity_type"), "invalid_entity_type", limit=80)
        entity_id = _text(target.get("entity_id"), "invalid_entity_id", limit=160)
        revision = _text(target.get("revision"), "invalid_revision", limit=160)
        purpose = _text(target.get("purpose"), "invalid_purpose", limit=160)
        gap = bool(target.get("gap", False))
        priority = target.get("priority", 100)
        if type(priority) is not int:
            raise WorkshopError("invalid_priority")
        variant_of = target.get("variant_of")
        if variant_of is not None and (type(variant_of) is not int or variant_of < 1):
            raise WorkshopError("invalid_variant")
        dependencies = target.get("depends_on") or []
        if not isinstance(dependencies, list) or any(type(item) is not int for item in dependencies):
            raise WorkshopError("invalid_dependency")
        sources = target.get("sources")
        if sources is not None:
            if not isinstance(sources, list) or len(sources) > 20 or not all(
                isinstance(item, dict) for item in sources
            ):
                raise WorkshopError("invalid_source_metadata")
            sources = [
                {"path": _text(item.get("path"), "invalid_source_metadata", limit=500),
                 "sha256": _text(item.get("sha256"), "invalid_source_metadata", limit=64)}
                for item in sources
            ]
            if any(not re.fullmatch(r"[0-9a-fA-F]{64}", item["sha256"]) for item in sources):
                raise WorkshopError("invalid_source_metadata")
        key = _dedupe_key(queue, entity_type, entity_id, revision, purpose, variant_of)
        item = {
            "queue": queue,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "revision": revision,
            "purpose": purpose,
            "priority": priority,
            "gap": gap,
            "depends_on": sorted(set(dependencies)),
            "variant_of": variant_of,
            "dedupe_key": key,
        }
        if sources is not None:
            item["sources"] = sources
        current = planned.get(key)
        if current is None or (gap and not current["gap"]):
            planned[key] = item
    items = sorted(
        planned.values(),
        key=lambda item: (
            not item["gap"],
            item["priority"],
            item["queue"],
            item["entity_type"],
            item["entity_id"],
            item["revision"],
            item["purpose"],
            item["variant_of"] or 0,
        ),
    )
    capped = []
    variant_counts: dict[tuple[str, str, str, str, str], int] = {}
    for item in items:
        if item["variant_of"] is not None:
            variant_key = (item["queue"], item["entity_type"], item["entity_id"],
                           item["revision"], item["purpose"])
            if variant_counts.get(variant_key, 0) >= max_variants:
                continue
            variant_counts[variant_key] = variant_counts.get(variant_key, 0) + 1
        capped.append(item)
    return {"items": capped, "count": len(capped), "mutated": False}


def _lease_token() -> str:
    return uuid.uuid4().hex


def _expire_leases(connection: sqlite3.Connection, now: datetime) -> None:
    stamp = _iso(now)
    rows = connection.execute(
        "SELECT id,status FROM ai_workshop_jobs WHERE status='running' AND lease_expires_at<=?",
        (stamp,),
    ).fetchall()
    for row in rows:
        job = _job_by_id(connection, int(row["id"]))
        status = "needs_review" if job.get("error_code") == "timeout_ambiguous" else "queued"
        connection.execute(
            "UPDATE ai_workshop_jobs SET status=?,lease_owner=NULL,lease_token=NULL,"
            "lease_expires_at=NULL,available_at=?,recoveries=recoveries+1,"
            "error_code='lease_expired',updated_at=? WHERE id=?",
            (status, stamp, stamp, row["id"]),
        )
        _event(connection, int(row["id"]), "lease_expired", {"recovered_as": status}, now)


def _unblock_due(connection: sqlite3.Connection, now: datetime) -> None:
    stamp = _iso(now)
    rows = connection.execute(
        "SELECT id FROM ai_workshop_jobs WHERE status='blocked' AND available_at<=? "
        "AND COALESCE(blocked_reason,'') NOT LIKE 'adapter_config:%' "
        "AND COALESCE(blocked_reason,'') <> 'dependency_failed'",
        (stamp,),
    ).fetchall()
    for row in rows:
        connection.execute(
            "UPDATE ai_workshop_jobs SET status='queued',blocked_reason=NULL,updated_at=? WHERE id=?",
            (stamp, row["id"]),
        )
        _event(connection, int(row["id"]), "unblocked", {}, now)


def _queue_pause(connection: sqlite3.Connection, queue: str) -> str | None:
    row = connection.execute(
        "SELECT paused,reason FROM ai_workshop_queue_state WHERE queue=?", (queue,)
    ).fetchone()
    if row is not None and row["paused"]:
        return row["reason"] or "queue_paused"
    return None


def _provider_gate(connection: sqlite3.Connection, queue: str, now: datetime) -> str | None:
    row = connection.execute(
        "SELECT auth_failed,cooldown_until,configured_limit FROM ai_workshop_providers WHERE queue=? "
        "ORDER BY updated_at DESC LIMIT 1",
        (queue,),
    ).fetchone()
    if row is None:
        return None
    if row["auth_failed"]:
        return "provider_auth_permanent"
    if row["cooldown_until"] and _parse(row["cooldown_until"]) > now:
        return "provider_cooldown"
    if row['configured_limit'] is not None:
        start=now.astimezone(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
        used=connection.execute("SELECT COUNT(*) FROM ai_workshop_events e JOIN ai_workshop_jobs j ON j.id=e.job_id "
            "WHERE e.event='claimed' AND j.queue=? AND e.created_at>=? AND e.created_at<?",
            (queue,_iso(start),_iso(start+timedelta(days=1)))).fetchone()[0]
        if used>=row['configured_limit']:return 'provider_daily_budget'
    return None


def _dependencies_state(connection: sqlite3.Connection,
                        dependencies: list[int]) -> tuple[bool, bool]:
    if not dependencies:
        return True, False
    placeholders = ",".join("?" for _ in dependencies)
    rows = connection.execute(
        f"SELECT id,status FROM ai_workshop_jobs WHERE id IN ({placeholders})",
        tuple(dependencies),
    ).fetchall()
    statuses = {int(row["id"]): row["status"] for row in rows}
    if len(statuses) != len(set(dependencies)):
        return False, False
    if any(statuses[item] in FAILURE_STATUSES for item in dependencies):
        return False, True
    return all(statuses[item] in SUCCESS_STATUSES for item in dependencies), False


def claim_next_job(
    database_path: Path,
    *,
    queue: str | None,
    worker_id: str,
    table_state: str = "inactive",
    lease_seconds: int = 300,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Claim at most one eligible job. Heavy work never starts on unknown/active table."""
    queue = _validate_queue(queue) if queue is not None else None
    if type(lease_seconds) is not int or not 10 <= lease_seconds <= 86400:
        raise WorkshopError("invalid_lease_seconds")
    worker_id = _text(worker_id, "invalid_worker_id", limit=160)
    if table_state not in TABLE_STATES:
        raise WorkshopError("invalid_table_state")
    init_workshop(Path(database_path))
    stamp_now = now or _utcnow()
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        _expire_leases(connection, stamp_now)
        _unblock_due(connection, stamp_now)
        if table_state == "unknown":
            return {"job": None, "reason": "table_state_unknown"}
        if table_state in {"session", "combat"}:
            return {"job": None, "reason": "table_active"}
        queues = [queue] if queue is not None else list(QUEUES)
        for candidate_queue in queues:
            paused = _queue_pause(connection, candidate_queue)
            if paused:
                if queue is not None:
                    return {"job": None, "reason": paused}
                continue
            gate = _provider_gate(connection, candidate_queue, stamp_now)
            if gate:
                if queue is not None:
                    return {"job": None, "reason": gate}
                continue
            rows = connection.execute(
                "SELECT * FROM ai_workshop_jobs WHERE status='queued' AND queue=? "
                "AND available_at<=? AND attempts<max_attempts "
                "ORDER BY gap DESC,priority ASC,id ASC LIMIT 100",
                (candidate_queue, _iso(stamp_now)),
            ).fetchall()
            for row in rows:
                job = _job_dto(row)
                dependencies = job.get("depends_on_json") or []
                ready, failed = _dependencies_state(connection, dependencies)
                if failed:
                    connection.execute(
                        "UPDATE ai_workshop_jobs SET status='blocked',blocked_reason="
                        "'dependency_failed',updated_at=? WHERE id=?",
                        (_iso(stamp_now), job["id"]),
                    )
                    _event(connection, job["id"], "dependency_failed", {}, stamp_now)
                    continue
                if not ready:
                    continue
                token = _lease_token()
                starts = job["started_at"] or _iso(stamp_now)
                connection.execute(
                    "UPDATE ai_workshop_jobs SET status='running',lease_owner=?,lease_token=?,"
                    "lease_expires_at=?,attempts=attempts+1,started_at=?,updated_at=?,"
                    "error_code=NULL,blocked_reason=NULL WHERE id=?",
                    (worker_id, token, _iso(stamp_now + timedelta(seconds=lease_seconds)),
                     starts, _iso(stamp_now), job["id"]),
                )
                _event(connection, job["id"], "claimed",
                       {"worker": worker_id, "queue": candidate_queue}, stamp_now)
                claimed = _job_by_id(connection, job["id"])
                return {"job": claimed, "reason": "claimed"}
        return {"job": None, "reason": "idle"}


def _lease_guard(connection: sqlite3.Connection, job_id: int, worker_id: str,
                 lease_token: str) -> dict[str, Any]:
    job = _job_by_id(connection, job_id)
    if job["status"] != "running" or job["lease_owner"] != worker_id or job["lease_token"] != lease_token:
        raise WorkshopError("lease_conflict")
    return job


def renew_lease(database_path: Path, job_id: int, *, worker_id: str, lease_token: str,
                lease_seconds: int = 300, now: datetime | None = None) -> dict[str, Any]:
    if type(lease_seconds) is not int or not 10 <= lease_seconds <= 86400:
        raise WorkshopError("invalid_lease_seconds")
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        _lease_guard(connection, job_id, worker_id, lease_token)
        connection.execute(
            "UPDATE ai_workshop_jobs SET lease_expires_at=?,updated_at=? WHERE id=?",
            (_iso((now or _utcnow()) + timedelta(seconds=lease_seconds)),
             _now_iso(now), job_id),
        )
        return _job_by_id(connection, job_id)


def validate_output(job: dict[str, Any], output: Any) -> dict[str, Any]:
    if not isinstance(output, dict):
        raise WorkshopError("output_must_be_object")
    cleaned = _scrub_value(output)
    missing = [field for field in OUTPUT_FIELDS if field not in cleaned]
    if missing:
        raise WorkshopError("output_missing_contract")
    if cleaned.get("revision") != job["revision"]:
        raise WorkshopError("output_revision_mismatch")
    for field in ("facts", "suggestions", "questions", "sources"):
        if not isinstance(cleaned.get(field), list):
            raise WorkshopError("output_invalid_contract")
    if len(cleaned["sources"]) > 200 or len(cleaned["facts"]) > 500:
        raise WorkshopError("output_too_large")
    cleaned["role"] = "assistant_output_not_instructions"
    _json_text(cleaned)
    return cleaned


def _metric_int(metrics: dict[str, Any], key: str) -> int | None:
    value = metrics.get(key)
    if value is None:
        return None
    if type(value) is not int or value < 0 or value > 2**53:
        raise WorkshopError("invalid_metric")
    return value


def finish_job(
    database_path: Path,
    job_id: int,
    *,
    worker_id: str,
    lease_token: str,
    status: str,
    output: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    external_ref: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Finish a job as a draft/external result. Never approves or publishes."""
    if status not in DRAFT_STATUSES:
        raise WorkshopError("invalid_completion_status")
    timestamp = now or _utcnow()
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        job = _lease_guard(connection, job_id, worker_id, lease_token)
        cleaned = validate_output(job, output)
        metrics = dict(metrics or {})
        duration = _metric_int(metrics, "duration_ms")
        samples = _metric_int(metrics, "samples")
        tokens_in = _metric_int(metrics, "tokens_in")
        tokens_out = _metric_int(metrics, "tokens_out")
        wait_ms = 0
        if job.get("started_at"):
            wait_ms = max(0, int((_parse(job["started_at"]) - _parse(job["created_at"])).total_seconds() * 1000))
        if duration is None and job.get("started_at"):
            duration = max(0, int((timestamp - _parse(job["started_at"])).total_seconds() * 1000))
        connection.execute(
            "UPDATE ai_workshop_jobs SET status=?,output_json=?,external_ref=?,lease_owner=NULL,"
            "lease_token=NULL,lease_expires_at=NULL,finished_at=?,updated_at=?,error_code=NULL "
            "WHERE id=?",
            (status, _json_text(cleaned), scrub_secrets(external_ref) if external_ref else None,
             _iso(timestamp), _iso(timestamp), job_id),
        )
        connection.execute(
            "INSERT OR REPLACE INTO ai_workshop_metrics(job_id,queue,provider,model,duration_ms,"
            "wait_ms,samples,ok,tokens_in,tokens_out,created_at) VALUES(?,?,?,?,?,?,?,1,?,?,?)",
            (job_id, job["queue"], scrub_secrets(metrics.get("provider") or ""),
             scrub_secrets(metrics.get("model") or ""), duration, wait_ms, samples,
             tokens_in, tokens_out, _iso(timestamp)),
        )
        _event(connection, job_id, "finished", {"status": status}, timestamp)
        return _job_by_id(connection, job_id)


def apply_failure(
    database_path: Path,
    job_id: int,
    *,
    worker_id: str,
    lease_token: str,
    kind: str,
    retry_after_seconds: int | None = None,
    reset_at: str | None = None,
    message_code: str | None = None,
    provider_override: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Classify a provider failure without inventing quota or retrying ambiguity."""
    timestamp = now or _utcnow()
    kind = str(kind or "unknown")
    if retry_after_seconds is not None and (
        type(retry_after_seconds) is not int or not 0 <= retry_after_seconds <= 7 * 86400
    ):
        raise WorkshopError("invalid_retry_after")
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        job = _lease_guard(connection, job_id, worker_id, lease_token)
        attempts = int(job["attempts"])
        max_attempts = int(job["max_attempts"])
        code = scrub_secrets(message_code or kind)[:120]
        provider = str(provider_override or (job.get("payload_json") or {}).get("provider") or {
            "text": "ollama", "image": "asset_generation", "code": "opencode",
        }.get(job["queue"], "unknown"))
        status = "queued"
        available = timestamp
        blocked_reason = None
        error_code = code
        if kind == "auth_permanent":
            status, error_code = "failed", "auth_permanent"
            _upsert_provider(connection, job["queue"], provider, auth_failed=1,
                             blocked_reason=error_code, now=timestamp)
        elif kind == "timeout_ambiguous":
            status, error_code = "needs_review", "timeout_ambiguous"
        elif kind == "waiting_permission":
            status, error_code = "waiting_permission", "waiting_permission"
        elif kind == "quota":
            status, blocked_reason = "blocked", "quota"
            if reset_at:
                try:
                    reset = _parse(reset_at)
                except ValueError as error:
                    raise WorkshopError("invalid_reset_at") from error
                available = reset
            elif retry_after_seconds is not None:
                available = timestamp + timedelta(seconds=retry_after_seconds)
            _upsert_provider(connection, job["queue"], provider,
                             cooldown_until=_iso(available), observed_reset_at=reset_at,
                             blocked_reason="quota", now=timestamp)
        elif kind == "retry_after":
            delay = retry_after_seconds if retry_after_seconds is not None else BACKOFF_BASE_SECONDS
            available = timestamp + timedelta(seconds=delay)
            _upsert_provider(connection, job["queue"], provider,
                             retry_after_at=_iso(available), cooldown_until=_iso(available),
                             blocked_reason="retry_after", now=timestamp)
        else:
            if retry_after_seconds is not None:
                delayed = timestamp + timedelta(seconds=retry_after_seconds)
                _upsert_provider(connection, job["queue"], provider,
                                 retry_after_at=_iso(delayed), cooldown_until=_iso(delayed),
                                 blocked_reason="retry_after", now=timestamp)
            else:
                delay = min(BACKOFF_BASE_SECONDS * (2 ** max(0, attempts - 1)),
                            BACKOFF_CAP_SECONDS)
                available = timestamp + timedelta(seconds=delay)
        if status == "queued" and attempts >= max_attempts:
            status, error_code = "failed", "attempts_exhausted"
        connection.execute(
            "UPDATE ai_workshop_jobs SET status=?,available_at=?,blocked_reason=?,error_code=?,"
            "lease_owner=NULL,lease_token=NULL,lease_expires_at=NULL,finished_at=?,updated_at=? "
            "WHERE id=?",
            (status, _iso(available), blocked_reason, error_code,
             _iso(timestamp) if status in {"failed", "needs_review", "waiting_permission"} else None,
             _iso(timestamp), job_id),
        )
        wait_ms = 0
        if job.get("started_at"):
            wait_ms = max(0, int((_parse(job["started_at"]) - _parse(job["created_at"])).total_seconds() * 1000))
        duration = None
        if job.get("started_at"):
            duration = max(0, int((timestamp - _parse(job["started_at"])).total_seconds() * 1000))
        connection.execute(
            "INSERT OR REPLACE INTO ai_workshop_metrics(job_id,queue,provider,model,duration_ms,"
            "wait_ms,samples,ok,tokens_in,tokens_out,created_at) VALUES(?,?,?,?,?,?,?,0,NULL,NULL,?)",
            (job_id, job["queue"], provider, str((job.get("payload_json") or {}).get("model") or ""),
             duration, wait_ms, None, _iso(timestamp)),
        )
        _event(connection, job_id, "failed", {"kind": code, "status": status}, timestamp)
        return _job_by_id(connection, job_id)


def _upsert_provider(connection: sqlite3.Connection, queue: str, provider: str, *,
                     documented_limit: str | None = None, configured_limit: int | None = None,
                     observed_remaining: int | None = None, observed_reset_at: str | None = None,
                     retry_after_at: str | None = None, cooldown_until: str | None = None,
                     auth_failed: int | None = None, blocked_reason: str | None = None,
                     now: datetime | None = None) -> None:
    existing = connection.execute(
        "SELECT * FROM ai_workshop_providers WHERE queue=? AND provider=?", (queue, provider)
    ).fetchone()
    values = dict(existing) if existing else {
        "documented_limit": None, "configured_limit": None, "observed_remaining": None,
        "observed_reset_at": None, "retry_after_at": None, "cooldown_until": None,
        "auth_failed": 0, "blocked_reason": None,
    }
    updates = {
        "documented_limit": documented_limit, "configured_limit": configured_limit,
        "observed_remaining": observed_remaining, "observed_reset_at": observed_reset_at,
        "retry_after_at": retry_after_at, "cooldown_until": cooldown_until,
        "auth_failed": auth_failed, "blocked_reason": blocked_reason,
    }
    for key, value in updates.items():
        if value is not None:
            values[key] = value
    connection.execute(
        "INSERT INTO ai_workshop_providers(queue,provider,documented_limit,configured_limit,"
        "observed_remaining,observed_reset_at,retry_after_at,cooldown_until,auth_failed,"
        "blocked_reason,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(queue,provider) DO UPDATE SET documented_limit=excluded.documented_limit,"
        "configured_limit=excluded.configured_limit,observed_remaining=excluded.observed_remaining,"
        "observed_reset_at=excluded.observed_reset_at,retry_after_at=excluded.retry_after_at,"
        "cooldown_until=excluded.cooldown_until,auth_failed=excluded.auth_failed,"
        "blocked_reason=excluded.blocked_reason,updated_at=excluded.updated_at",
        (queue, provider, values["documented_limit"], values["configured_limit"],
         values["observed_remaining"], values["observed_reset_at"], values["retry_after_at"],
         values["cooldown_until"], int(values["auth_failed"] or 0), values["blocked_reason"],
         _now_iso(now)),
    )


def configure_provider(
    database_path: Path,
    *,
    queue: str,
    provider: str,
    documented_limit: str | None = None,
    configured_limit: int | None = None,
    observed_remaining: int | None = None,
    observed_reset_at: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Keep documented, configured and observed limits explicitly separate."""
    queue = _validate_queue(queue)
    provider = _text(provider, "invalid_provider", limit=80)
    for value in (configured_limit, observed_remaining):
        if value is not None and (type(value) is not int or value < 0):
            raise WorkshopError("invalid_limit")
    if documented_limit is not None and not isinstance(documented_limit, str):
        raise WorkshopError("invalid_documented_limit")
    init_workshop(Path(database_path))
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        _upsert_provider(connection, queue, provider, documented_limit=documented_limit,
                         configured_limit=configured_limit, observed_remaining=observed_remaining,
                         observed_reset_at=observed_reset_at, auth_failed=0,
                         blocked_reason=None, now=now)
    return provider_status(database_path, queue=queue, provider=provider)


def budget_known(database_path: Path, queue: str) -> bool:
    """Only configured or observed budget counts; documented pricing is not a balance."""
    try:
        with closing(_read_connection(Path(database_path))) as connection:
            row = connection.execute(
                "SELECT configured_limit,observed_remaining FROM ai_workshop_providers "
                "WHERE queue=? ORDER BY updated_at DESC LIMIT 1",
                (queue,),
            ).fetchone()
    except (sqlite3.DatabaseError, FileNotFoundError):
        return False
    return bool(row and (row["configured_limit"] is not None or row["observed_remaining"] is not None))


def set_worker_state(database_path: Path, state: str, *, reason: str = "",
                     now: datetime | None = None) -> dict[str, Any]:
    if state not in WORKER_STATES:
        raise WorkshopError("invalid_worker_state")
    if len(str(reason)) > 500:
        raise WorkshopError("invalid_reason")
    init_workshop(Path(database_path))
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        stamp = _now_iso(now)
        connection.execute(
            "INSERT INTO ai_workshop_control(key,value,updated_at) VALUES('worker_state',?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
            (state, stamp),
        )
        connection.execute(
            "INSERT INTO ai_workshop_control(key,value,updated_at) VALUES('worker_reason',?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
            (scrub_secrets(reason), stamp),
        )
        _event(connection, None, "worker_state", {"state": state, "reason": scrub_secrets(reason)}, now)
    return worker_status(database_path)


def get_worker_state(database_path: Path) -> dict[str, Any]:
    try:
        with closing(_read_connection(Path(database_path))) as connection:
            rows = connection.execute("SELECT key,value FROM ai_workshop_control").fetchall()
    except (sqlite3.DatabaseError, FileNotFoundError):
        return {"state": "stopped", "reason": "", "initialized": False}
    values = {row["key"]: row["value"] for row in rows}
    return {"state": values.get("worker_state", "stopped"),
            "reason": values.get("worker_reason", ""), "initialized": True}


def set_queue_paused(database_path: Path, queue: str, paused: bool, *,
                     reason: str = "", now: datetime | None = None) -> dict[str, Any]:
    queue = _validate_queue(queue)
    if len(str(reason)) > 500:
        raise WorkshopError("invalid_reason")
    init_workshop(Path(database_path))
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "INSERT INTO ai_workshop_queue_state(queue,paused,reason,updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(queue) DO UPDATE SET paused=excluded.paused,reason=excluded.reason,"
            "updated_at=excluded.updated_at",
            (queue, int(bool(paused)), scrub_secrets(reason), _now_iso(now)),
        )
        _event(connection, None, "queue_state", {"queue": queue, "paused": bool(paused)}, now)
    return {"queue": queue, "paused": bool(paused), "reason": scrub_secrets(reason)}


def worker_status(database_path: Path) -> dict[str, Any]:
    state = get_worker_state(database_path)
    try:
        with closing(_read_connection(Path(database_path))) as connection:
            rows = connection.execute(
                "SELECT queue,paused,reason FROM ai_workshop_queue_state ORDER BY queue"
            ).fetchall()
            state["queues"] = {row["queue"]: {"paused": bool(row["paused"]),
                                               "reason": row["reason"]} for row in rows}
    except (sqlite3.DatabaseError, FileNotFoundError):
        state["queues"] = {}
    return state


def list_jobs(database_path: Path, *, queue: str | None = None, status: str | None = None,
              limit: int = 100) -> list[dict[str, Any]]:
    if queue is not None:
        queue = _validate_queue(queue)
    if status is not None and status not in JOB_STATUSES:
        raise WorkshopError("invalid_status")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise WorkshopError("invalid_limit")
    try:
        with closing(_read_connection(Path(database_path))) as connection:
            clauses = []
            args: list[Any] = []
            if queue is not None:
                clauses.append("queue=?")
                args.append(queue)
            if status is not None:
                clauses.append("status=?")
                args.append(status)
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            rows = connection.execute(
                f"SELECT * FROM ai_workshop_jobs{where} ORDER BY id DESC LIMIT ?",
                (*args, limit),
            ).fetchall()
    except (sqlite3.DatabaseError, FileNotFoundError):
        return []
    return [_job_dto(row) for row in rows]


def get_job(database_path: Path, job_id: int) -> dict[str, Any]:
    with closing(_read_connection(Path(database_path))) as connection:
        return _job_by_id(connection, job_id)


def _percentile(values: list[int], percentile: int) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((percentile / 100) * (len(ordered) - 1)))))
    return ordered[index]


def stats(database_path: Path, *, queue: str | None = None) -> dict[str, Any]:
    """Measured latency only. Fixtures never become production latency."""
    if queue is not None:
        queue = _validate_queue(queue)
    try:
        with closing(_read_connection(Path(database_path))) as connection:
            where = " WHERE queue=?" if queue is not None else ""
            args = (queue,) if queue is not None else ()
            rows = connection.execute(
                f"SELECT duration_ms,wait_ms,tokens_in,tokens_out FROM ai_workshop_metrics{where}",
                args,
            ).fetchall()
            successes = connection.execute(
                f"SELECT COUNT(*) FROM ai_workshop_metrics{where} AND ok=1"
                if where else "SELECT COUNT(*) FROM ai_workshop_metrics WHERE ok=1",
                args,
            ).fetchone()[0]
            failures = connection.execute(
                f"SELECT COUNT(*) FROM ai_workshop_metrics{where} AND ok=0"
                if where else "SELECT COUNT(*) FROM ai_workshop_metrics WHERE ok=0",
                args,
            ).fetchone()[0]
    except (sqlite3.DatabaseError, FileNotFoundError):
        return {"samples": 0, "average_ms": None, "p50_ms": None, "p95_ms": None,
                "average_wait_ms": None, "wait_p50_ms": None, "wait_p95_ms": None,
                "successes": 0, "failures": 0, "tokens_in": None, "tokens_out": None}
    durations = [row["duration_ms"] for row in rows if row["duration_ms"] is not None]
    waits = [row["wait_ms"] for row in rows if row["wait_ms"] is not None]
    tokens_in = [row["tokens_in"] for row in rows if row["tokens_in"] is not None]
    tokens_out = [row["tokens_out"] for row in rows if row["tokens_out"] is not None]
    return {
        "samples": len(durations),
        "average_ms": int(sum(durations) / len(durations)) if durations else None,
        "p50_ms": _percentile(durations, 50),
        "p95_ms": _percentile(durations, 95),
        "average_wait_ms": int(sum(waits) / len(waits)) if waits else None,
        "wait_p50_ms": _percentile(waits, 50),
        "wait_p95_ms": _percentile(waits, 95),
        "successes": int(successes),
        "failures": int(failures),
        "tokens_in": sum(tokens_in) if tokens_in else None,
        "tokens_out": sum(tokens_out) if tokens_out else None,
    }


def provider_status(database_path: Path, *, queue: str | None = None,
                    provider: str | None = None) -> dict[str, Any]:
    if queue is not None:
        queue = _validate_queue(queue)
    try:
        with closing(_read_connection(Path(database_path))) as connection:
            clauses, args = [], []
            if queue is not None:
                clauses.append("queue=?")
                args.append(queue)
            if provider is not None:
                clauses.append("provider=?")
                args.append(provider)
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            rows = connection.execute(
                f"SELECT * FROM ai_workshop_providers{where} ORDER BY queue,provider", tuple(args)
            ).fetchall()
    except (sqlite3.DatabaseError, FileNotFoundError):
        return {"providers": []}
    return {"providers": [
        {
            "queue": row["queue"],
            "provider": row["provider"],
            "documented_limit": row["documented_limit"],
            "configured_limit": row["configured_limit"],
            "observed_remaining": row["observed_remaining"],
            "observed_reset_at": row["observed_reset_at"],
            "retry_after_at": row["retry_after_at"],
            "cooldown_until": row["cooldown_until"],
            "auth_failed": bool(row["auth_failed"]),
            "blocked_reason": row["blocked_reason"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]}


def status(database_path: Path, *, table_state: str | None = None) -> dict[str, Any]:
    """Read-only operational summary. Missing DB is reported, never created."""
    if table_state is not None and table_state not in TABLE_STATES:
        raise WorkshopError("invalid_table_state")
    result: dict[str, Any] = {
        "db": str(Path(database_path)),
        "initialized": False,
        "worker": {"state": "stopped", "reason": ""},
        "counts": {},
        "queues": {},
        "active_leases": 0,
        "expired_leases": 0,
        "stats": stats(Path(database_path)),
        "providers": provider_status(Path(database_path))["providers"],
        "table_state": table_state,
    }
    try:
        with closing(_read_connection(Path(database_path))) as connection:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            if "ai_workshop_jobs" not in tables:
                return result
            result["initialized"] = True
            for row in connection.execute(
                "SELECT queue,status,COUNT(*) AS total FROM ai_workshop_jobs "
                "GROUP BY queue,status ORDER BY queue,status"
            ):
                result["counts"].setdefault(row["queue"], {})[row["status"]] = int(row["total"])
            now = _iso(_utcnow())
            result["active_leases"] = int(connection.execute(
                "SELECT COUNT(*) FROM ai_workshop_jobs WHERE status='running' "
                "AND lease_expires_at>?", (now,)
            ).fetchone()[0])
            result["expired_leases"] = int(connection.execute(
                "SELECT COUNT(*) FROM ai_workshop_jobs WHERE status='running' "
                "AND lease_expires_at<=?", (now,)
            ).fetchone()[0])
            controls = {row["key"]: row["value"] for row in connection.execute(
                "SELECT key,value FROM ai_workshop_control"
            )}
            result["worker"] = {"state": controls.get("worker_state", "stopped"),
                                "reason": controls.get("worker_reason", "")}
            for row in connection.execute(
                "SELECT queue,paused,reason FROM ai_workshop_queue_state"
            ):
                result["queues"][row["queue"]] = {
                    "paused": bool(row["paused"]), "reason": row["reason"],
                }
    except (sqlite3.DatabaseError, FileNotFoundError):
        return result
    return result


def tick(database_path: Path, adapters: dict, **options) -> dict[str, Any]:
    """Share heavy-work admission with native QA before claiming a job."""
    from scripts.memory_guard import workload_slot
    with workload_slot() as acquired:
        if not acquired:
            return {'status': 'blocked', 'reason': 'resource_busy', 'job': None}
        return _tick_admitted(database_path, adapters, **options)


def _tick_admitted(
    database_path: Path,
    adapters: dict[str, Callable[[dict[str, Any]], dict[str, Any]]],
    *,
    table_state: str = "inactive",
    worker_id: str = "tick",
    queue: str | None = None,
    continuous: bool = False,
    lease_seconds: int = 300,
    min_free_ram_mb: int | None = None,
    ram_available_mb: Any = _RAM_UNSET,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run at most one job. Local test adapters opt out of the external-budget gate."""
    if table_state == "unknown":
        return {"status": "paused", "reason": "table_state_unknown", "job": None}
    if table_state in {"session", "combat"}:
        return {"status": "paused", "reason": "table_active", "job": None}
    required_ram = configured_min_free_ram_mb() if min_free_ram_mb is None else int(min_free_ram_mb)
    if required_ram > 0:
        free_ram = (available_memory_mb() if ram_available_mb is _RAM_UNSET
                    else ram_available_mb)
        if free_ram is None:
            return {"status": "paused", "reason": "memory_unknown", "job": None,
                    "required_free_ram_mb": required_ram}
        if free_ram < required_ram:
            return {"status": "paused", "reason": "insufficient_memory", "job": None,
                    "required_free_ram_mb": required_ram, "free_ram_mb": free_ram}
    queues = [queue] if queue is not None else list(QUEUES)
    if continuous:
        allowed = []
        for candidate in queues:
            adapter = adapters.get(candidate)
            if adapter is None:
                continue
            if getattr(adapter, "uses_external_budget", True) and not budget_known(
                database_path, candidate
            ):
                continue
            allowed.append(candidate)
        if not allowed:
            return {"status": "blocked", "reason": "external_budget_unknown", "job": None}
        queues = allowed
    for candidate in queues:
        if candidate not in adapters:
            continue
        claim = claim_next_job(database_path, queue=candidate, worker_id=worker_id,
                               table_state=table_state, lease_seconds=lease_seconds, now=now)
        job = claim.get("job")
        if job is None:
            continue
        adapter = adapters[candidate]
        try:
            outcome = adapter(job)
        except Exception as error:  # Adapter errors are classified, never echoed raw.
            kind = getattr(error, "kind", "adapter_error")
            if kind == "config":
                message_code = getattr(error, "message_code", "adapter_config")
                return {
                    "status": "blocked",
                    "reason": message_code,
                    "job": block_job_for_config(
                        database_path, job, worker_id,
                        reason=f"adapter_config:{message_code}", now=now,
                    ),
                }
            if kind == "waiting_permission":
                return {
                    "status": "waiting_permission",
                    "reason": "permission_not_approved_automatically",
                    "job": apply_failure(
                        database_path, job["id"], worker_id=worker_id,
                        lease_token=job["lease_token"], kind=kind,
                        message_code=getattr(error, "message_code", kind), now=now,
                    ),
                }
            return {
                "status": "failed",
                "job": apply_failure(
                    database_path, job["id"], worker_id=worker_id,
                    lease_token=job["lease_token"], kind=kind,
                    retry_after_seconds=getattr(error, "retry_after_seconds", None),
                    reset_at=getattr(error, "reset_at", None),
                    message_code=getattr(error, "message_code", kind), now=now,
                    provider_override=getattr(error,'provider',None),
                ),
            }
        if not isinstance(outcome, dict):
            apply_failure(database_path, job["id"], worker_id=worker_id,
                          lease_token=job["lease_token"], kind="invalid_adapter_result", now=now)
            return {"status": "failed", "job": get_job(database_path, job["id"])}
        outcome_status = outcome.get("status")
        if outcome_status in DRAFT_STATUSES:
            finished = finish_job(
                database_path, job["id"], worker_id=worker_id,
                lease_token=job["lease_token"], status=outcome_status,
                output=outcome.get("output"), metrics=outcome.get("metrics"),
                external_ref=outcome.get("external_ref"), now=now,
            )
            return {"status": "completed", "job": finished}
        if outcome_status == "failure":
            return {
                "status": "failed",
                "job": apply_failure(
                    database_path, job["id"], worker_id=worker_id,
                    lease_token=job["lease_token"], kind=outcome.get("kind", "provider_error"),
                    retry_after_seconds=outcome.get("retry_after_seconds"),
                    reset_at=outcome.get("reset_at"),
                    message_code=outcome.get("message_code"), now=now,
                ),
            }
        apply_failure(database_path, job["id"], worker_id=worker_id,
                      lease_token=job["lease_token"], kind="invalid_adapter_status", now=now)
        return {"status": "failed", "job": get_job(database_path, job["id"])}
    return {"status": "idle", "reason": "idle", "job": None}


def finish_if_possible(database_path: Path, job: dict[str, Any], worker_id: str, *,
                       kind: str, now: datetime | None = None) -> dict[str, Any]:
    """Cancel a claimed job whose adapter is not configured, without retry loops."""
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        _lease_guard(connection, job["id"], worker_id, job["lease_token"])
        connection.execute(
            "UPDATE ai_workshop_jobs SET status='cancelled',error_code=?,lease_owner=NULL,"
            "lease_token=NULL,lease_expires_at=NULL,finished_at=?,updated_at=? WHERE id=?",
            (f"adapter_{kind}", _now_iso(now), _now_iso(now), job["id"]),
        )
        _event(connection, job["id"], "cancelled", {"reason": f"adapter_{kind}"}, now)
        return _job_by_id(connection, job["id"])


def available_memory_mb() -> int | None:
    """Free physical RAM in MB, or None when it cannot be measured faithfully."""
    try:
        if os.name == "nt":
            class _MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            status = _MemoryStatusEx()
            status.dwLength = ctypes.sizeof(_MemoryStatusEx)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return None
            return int(status.ullAvailPhys // (1024 * 1024))
        with open("/proc/meminfo", "r", encoding="ascii") as stream:
            for line in stream:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except (OSError, ValueError, AttributeError):
        return None
    return None


def configured_min_free_ram_mb() -> int:
    try:
        value = int(os.getenv("AI_WORKSHOP_MIN_FREE_RAM_MB", "512"))
    except ValueError:
        return 512
    return max(0, min(value, 262144))


def block_job_for_config(database_path: Path, job: dict[str, Any], worker_id: str, *,
                         reason: str, now: datetime | None = None) -> dict[str, Any]:
    """Park a claimed job until an operator fixes configuration; never spin."""
    timestamp = now or _utcnow()
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        _lease_guard(connection, job["id"], worker_id, job["lease_token"])
        connection.execute(
            "UPDATE ai_workshop_jobs SET status='blocked',blocked_reason=?,error_code=?,"
            "available_at=?,lease_owner=NULL,lease_token=NULL,lease_expires_at=NULL,"
            "updated_at=? WHERE id=?",
            (scrub_secrets(reason)[:120], scrub_secrets(reason)[:120],
             _iso(timestamp + timedelta(days=1)), _iso(timestamp), job["id"]),
        )
        _event(connection, job["id"], "blocked", {"reason": reason}, timestamp)
        return _job_by_id(connection, job["id"])


def requeue_job(database_path: Path, job_id: int, *, confirm: bool = False,
                now: datetime | None = None) -> dict[str, Any]:
    """Explicitly return a parked job to the queue after an operator fix.

    Configuration blocks and permission prompts never requeue themselves, so
    this is the only path back for those states. It does not approve output,
    clear provider auth/cooldown, or reset attempts.
    """
    if confirm is not True:
        raise WorkshopError("confirmation_required")
    database_path = Path(database_path).resolve()
    if not database_path.is_file():
        raise WorkshopError("database_not_found")
    timestamp = now or _utcnow()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        job = _job_by_id(connection, job_id)
        if job["status"] not in {"blocked", "needs_review", "waiting_permission"}:
            raise WorkshopError("job_not_requeueable")
        connection.execute(
            "UPDATE ai_workshop_jobs SET status='queued',available_at=?,blocked_reason=NULL,"
            "error_code=NULL,lease_owner=NULL,lease_token=NULL,lease_expires_at=NULL,"
            "finished_at=NULL,updated_at=? WHERE id=?",
            (_iso(timestamp), _iso(timestamp), job_id),
        )
        _event(connection, job_id, "requeued", {"previous_status": job["status"]}, timestamp)
        return _job_by_id(connection, job_id)


def read_table_state(campaign_database: Path) -> str:
    """Fail closed: any read error means unknown, which suspends heavy work."""
    try:
        with closing(_read_connection(Path(campaign_database))) as connection:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            if "game_sessions" not in tables:
                return "unknown"
            active = connection.execute(
                "SELECT COUNT(*) FROM game_sessions WHERE status='active'"
            ).fetchone()[0]
            combat = _combat_state(connection, tables)
            if combat == "unknown":
                return "unknown"
            if combat == "active":
                return "combat"
            return "session" if active else "inactive"
    except (sqlite3.DatabaseError, OSError, FileNotFoundError):
        return "unknown"


def _combat_state(connection: sqlite3.Connection, tables: set[str]) -> str:
    """Authoritative encounter state only.

    Old pending attack receipts do not prove an active encounter. ``active`` is
    decisive even when ``battle_mode`` is absent; residual battle_mode with
    active=false is inactive. Invalid structure means unknown (fail closed).
    """
    if "combat_effect_clock" not in tables:
        return "inactive"
    row = connection.execute(
        "SELECT encounter_json FROM combat_effect_clock LIMIT 1"
    ).fetchone()
    if row is None:
        return "inactive"
    try:
        encounter = json.loads(row[0] or "{}")
    except (TypeError, ValueError):
        return "unknown"
    if not isinstance(encounter, dict):
        return "unknown"
    return "active" if encounter.get("active") else "inactive"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes

            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        except Exception:
            return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_checkout_lock(path: Path, worker_id: str, *, now: datetime | None = None,
                          stale_seconds: int = 6 * 3600) -> str:
    """One worker per checkout. Stale/dead locks are replaced once."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    payload = _json_text({"worker_id": scrub_secrets(worker_id), "token": token,
                          "pid": os.getpid(), "created_at": _now_iso(now)})
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    for attempt in range(2):
        try:
            descriptor = os.open(path, flags, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(payload)
            return token
        except FileExistsError:
            if attempt:
                raise CheckoutLockBusy("checkout lock is busy")
            try:
                info = json.loads(path.read_text(encoding="utf-8"))
                age = (_utcnow() - _parse(info["created_at"])).total_seconds()
                alive = _pid_alive(int(info.get("pid", 0)))
            except (OSError, ValueError, KeyError, TypeError):
                info, age, alive = {}, stale_seconds + 1, False
            if alive:
                raise CheckoutLockBusy("checkout lock is busy")
            try:
                path.unlink()
            except OSError:
                raise CheckoutLockBusy("checkout lock is busy")
    raise CheckoutLockBusy("checkout lock is busy")


def release_checkout_lock(path: Path, token: str) -> None:
    try:
        info = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if info.get("token") == token:
        try:
            Path(path).unlink()
        except OSError:
            pass
