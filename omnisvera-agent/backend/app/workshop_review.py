"""GM-confirmed review of private workshop drafts (text/code only).

This module is deliberately small and additive. It never executes draft text or
code, never publishes/activates a scene, and never edits sheets, maps or rules.
An import creates native hidden GM elements through ``scene_play``; a reject
only cancels the workshop job. Review receipts live in the workshop database,
which is separate from the campaign database.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import ai_workshop as workshop
from . import scene_play

DECISIONS = {"import", "reject"}
REVIEW_QUEUES = {"text", "code"}
REVIEW_STATUS = "awaiting_approval"
NATIVE_STATUS = "hidden"
NATIVE_VISIBILITY = "gm"
NATIVE_ELEMENT_TYPE = "clue"
NATIVE_CREATED_BY = "master"
HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class ReviewError(workshop.WorkshopError):
    """Stable review error code; never carries draft text or credentials."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
    except (TypeError, ValueError) as error:
        raise ReviewError("invalid_output") from error


def _digest(revision: str, output: dict[str, Any]) -> str:
    material = _canonical({"revision": revision, "output": output})
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def output_hash(job: dict[str, Any]) -> str:
    """SHA256 of canonical output_json plus revision.

    The revision is part of the hash so a regenerated draft with the same text
    still requires a fresh GM confirmation.
    """
    if not isinstance(job, dict):
        raise ReviewError("job_not_found")
    revision = job.get("revision")
    if not isinstance(revision, str) or not revision:
        raise ReviewError("invalid_revision")
    output = job.get("output_json")
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except (TypeError, ValueError) as error:
            raise ReviewError("output_missing") from error
    if not isinstance(output, dict):
        raise ReviewError("output_missing")
    return _digest(revision, output)


def element_request_id(job_id: int, value_hash: str) -> str:
    """Deterministic native request id for safe recovery after a partial write."""
    if type(job_id) is not int or job_id < 1:
        raise ReviewError("job_not_found")
    if not isinstance(value_hash, str) or not HASH_RE.fullmatch(value_hash):
        raise ReviewError("invalid_output_hash")
    return f"workshop-import-{job_id}-{value_hash.lower()[:40]}"


def _request_id(value: Any) -> str:
    try:
        return workshop._request_id(value)
    except workshop.WorkshopError as error:
        raise ReviewError(error.code) from None


def _expected_hash(value: Any) -> str:
    text = str(value or "").strip()
    if not HASH_RE.fullmatch(text):
        raise ReviewError("invalid_output_hash")
    return text.lower()


def _expected_revision(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise ReviewError("invalid_revision")
    return value


def _scene_id(value: Any) -> int:
    if type(value) is not int or value < 1:
        raise ReviewError("invalid_scene")
    return value


def _workshop_connect(database_path: Path) -> sqlite3.Connection:
    database_path = Path(database_path)
    if not database_path.is_file():
        raise ReviewError("job_not_found")
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def _campaign_connect(database_path: Path) -> sqlite3.Connection:
    database_path = Path(database_path)
    if not database_path.is_file():
        raise ReviewError("campaign_unavailable")
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_receipt_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS ai_workshop_reviews ("
        "request_id TEXT PRIMARY KEY,"
        "job_id INTEGER NOT NULL,"
        "output_hash TEXT NOT NULL,"
        "decision TEXT NOT NULL,"
        "scene_id INTEGER,"
        "element_id INTEGER,"
        "fingerprint TEXT NOT NULL,"
        "response_json TEXT NOT NULL,"
        "created_at TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_workshop_reviews_result "
        "ON ai_workshop_reviews(job_id, output_hash)"
    )


def _load_job(connection: sqlite3.Connection, job_id: int) -> dict[str, Any]:
    if type(job_id) is not int or job_id < 1:
        raise ReviewError("job_not_found")
    row = connection.execute(
        "SELECT * FROM ai_workshop_jobs WHERE id=?", (job_id,)
    ).fetchone()
    if row is None:
        raise ReviewError("job_not_found")
    job = dict(row)
    output = job.get("output_json")
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except (TypeError, ValueError) as error:
            raise ReviewError("output_missing") from error
    job["output_json"] = output
    return job


def _fingerprint(decision: str, job_id: int, value_hash: str, scene_id: int | None) -> str:
    material: dict[str, Any] = {
        "decision": decision,
        "job_id": job_id,
        "output_hash": value_hash,
    }
    if decision == "import":
        material["scene_id"] = scene_id
    return _canonical(material)


def _load_scene_and_element(campaign_path: Path, scene_id: int, native_request: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    connection = _campaign_connect(campaign_path)
    try:
        with closing(connection):
            scene = connection.execute(
                "SELECT id,title,status,archived FROM scenes WHERE id=?", (scene_id,)
            ).fetchone()
            if scene is None:
                raise ReviewError("scene_not_found")
            if int(scene["archived"] or 0):
                raise ReviewError("scene_archived")
            element = connection.execute(
                "SELECT * FROM scene_elements WHERE request_id=?", (native_request,)
            ).fetchone()
    except sqlite3.DatabaseError as error:
        raise ReviewError("campaign_unavailable") from error
    return dict(scene), (dict(element) if element is not None else None)


def _private_text(job: dict[str, Any], value_hash: str, review_request: str,
                  native_request: str) -> str:
    output = job.get("output_json")
    draft = output.get("draft") if isinstance(output, dict) else None
    if not isinstance(draft, str) or not draft.strip():
        raise ReviewError("empty_output")
    references = "\n".join((
        "Referências da oficina (privado)",
        f"job={job['id']}",
        f"hash={value_hash}",
        f"revision={job.get('revision')}",
        'Fontes e recibo completos: consultar este bloco na oficina.',
        "Sugestão textual; não executada.",
    ))
    text = f"{draft}\n\n---\n{references}"
    if len(draft) > 50000:
        raise ReviewError("output_exceeds_native_limit")
    return text


def _store_receipt(connection: sqlite3.Connection, *, request_id: str, job_id: int,
                   value_hash: str, decision: str, scene_id: int | None,
                   element_id: int | None, fingerprint: str,
                   response: dict[str, Any], now: str) -> None:
    connection.execute(
        "INSERT INTO ai_workshop_reviews(request_id,job_id,output_hash,decision,scene_id,"
        "element_id,fingerprint,response_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (request_id, job_id, value_hash, decision, scene_id, element_id, fingerprint,
         _canonical(response), now),
    )


def _event(connection: sqlite3.Connection, job_id: int, event: str,
           detail: dict[str, Any], now: str) -> None:
    connection.execute(
        "INSERT INTO ai_workshop_events(job_id,event,detail_json,created_at) VALUES(?,?,?,?)",
        (job_id, event, _canonical(detail), now),
    )


def _same_intent(row: sqlite3.Row, decision: str, scene_id: int | None) -> bool:
    if row["decision"] != decision:
        return False
    if decision == "import" and int(row["scene_id"] or 0) != int(scene_id or 0):
        return False
    return True


def review_job(
    workshop_database: Path,
    campaign_database: Path,
    job_id: int,
    *,
    decision: str,
    scene_id: int | None,
    expected_revision: str,
    expected_output_hash: str,
    request_id: str,
) -> dict[str, Any]:
    """Confirm one draft as an explicit import or reject.

    The campaign write happens before the workshop receipt commit. A retry after
    a partial failure finds the deterministic native element and completes the
    receipt instead of creating a second one.
    """
    if decision not in DECISIONS:
        raise ReviewError("invalid_decision")
    request_id = _request_id(request_id)
    expected_revision = _expected_revision(expected_revision)
    expected_hash = _expected_hash(expected_output_hash)
    if decision == "import":
        scene_id = _scene_id(scene_id)

    workshop_path = Path(workshop_database)
    campaign_path = Path(campaign_database)
    now = _iso(_utcnow())

    with closing(_workshop_connect(workshop_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        _ensure_receipt_schema(connection)
        job = _load_job(connection, job_id)
        value_hash = output_hash(job)

        if job.get("revision") != expected_revision:
            raise ReviewError("revision_mismatch")
        if value_hash != expected_hash:
            raise ReviewError("output_hash_mismatch")

        fingerprint = _fingerprint(decision, job_id, value_hash, scene_id)
        previous_request = connection.execute(
            "SELECT * FROM ai_workshop_reviews WHERE request_id=?", (request_id,)
        ).fetchone()
        if previous_request is not None:
            if previous_request["fingerprint"] != fingerprint:
                raise ReviewError("request_id_conflict")
            return json.loads(previous_request["response_json"])

        previous_result = connection.execute(
            "SELECT * FROM ai_workshop_reviews WHERE job_id=? AND output_hash=?",
            (job_id, value_hash),
        ).fetchone()
        if previous_result is not None:
            if _same_intent(previous_result, decision, scene_id):
                return json.loads(previous_result["response_json"])
            if previous_result["decision"] == "import":
                raise ReviewError("imported_elsewhere")
            raise ReviewError("already_reviewed")

        if job.get("status") != REVIEW_STATUS and not (decision=='reject' and job.get('status')=='needs_review'):
            raise ReviewError("job_not_awaiting_approval")
        if job.get("queue") not in REVIEW_QUEUES:
            raise ReviewError("review_queue_not_supported")

        if decision == "reject":
            response = {
                "job_id": job_id,
                "decision": "reject",
                "status": "cancelled",
                "scene_id": None,
                "element_id": None,
                "output_hash": value_hash,
                "revision": job.get("revision"),
                "request_id": request_id,
                "reviewed_at": now,
            }
            _store_receipt(
                connection, request_id=request_id, job_id=job_id, value_hash=value_hash,
                decision="reject", scene_id=None, element_id=None,
                fingerprint=fingerprint, response=response, now=now,
            )
            connection.execute(
                "UPDATE ai_workshop_jobs SET status='cancelled',lease_owner=NULL,"
                "lease_token=NULL,lease_expires_at=NULL,finished_at=?,updated_at=? "
                "WHERE id=?",
                (now, now, job_id),
            )
            _event(connection, job_id, "review_rejected",
                   {"output_hash": value_hash, "request_id": request_id}, now)
            return response

        assert scene_id is not None
        native_request = element_request_id(job_id, value_hash)
        _private = _private_text(job, value_hash, request_id, native_request)
        elements = []
        for part, offset in enumerate(range(0, len(_private), scene_play.MAX_TEXT - 2)):
            part_request = native_request if part == 0 else f"{native_request}:part:{part + 1}"
            _scene, existing = _load_scene_and_element(campaign_path, scene_id, part_request)
            if existing is not None and int(existing["scene_id"]) != scene_id:
                raise ReviewError("imported_elsewhere")
            if existing is None:
                try:
                    element, _created = scene_play.create_element(
                        campaign_path, scene_id, request_id=part_request,
                        element_type=NATIVE_ELEMENT_TYPE,
                        title=f"Bloco da oficina #{job_id}" + (f" · parte {part + 1}" if part else ""),
                        status=NATIVE_STATUS, visibility=NATIVE_VISIBILITY,
                        created_by=NATIVE_CREATED_BY, public_description="",
                        private_description=("‹" + _private[offset:offset + scene_play.MAX_TEXT - 2] + "›") if len(_private) > scene_play.MAX_TEXT else _private,
                    )
                except ValueError as error:
                    raise ReviewError("native_element_rejected") from error
            else:
                element = existing
            if int(element["scene_id"]) != scene_id:
                raise ReviewError("imported_elsewhere")
            elements.append(int(element["id"]))
        element = {"id": elements[0]}

        response = {
            "job_id": job_id,
            "decision": "import",
            "status": "completed",
            "scene_id": scene_id,
            "element_id": int(element["id"]),
            "element_ids": elements,
            "output_hash": value_hash,
            "revision": job.get("revision"),
            "request_id": request_id,
            "reviewed_at": now,
        }
        _store_receipt(
            connection, request_id=request_id, job_id=job_id, value_hash=value_hash,
            decision="import", scene_id=scene_id, element_id=int(element["id"]),
            fingerprint=fingerprint, response=response, now=now,
        )
        connection.execute(
            "UPDATE ai_workshop_jobs SET status='completed',lease_owner=NULL,"
            "lease_token=NULL,lease_expires_at=NULL,finished_at=?,updated_at=?,"
            "error_code=NULL WHERE id=?",
            (now, now, job_id),
        )
        _event(connection, job_id, "review_imported",
               {"output_hash": value_hash, "scene_id": scene_id,
                "element_id": int(element["id"]), "request_id": request_id}, now)
        return response


def review_for_job(workshop_database: Path, job_id: int, *,
                   output_hash: str | None = None) -> dict[str, Any] | None:
    """Read-only review projection for the private GM detail response."""
    if type(job_id) is not int or job_id < 1:
        return None
    path = Path(workshop_database)
    if not path.is_file():
        return None
    try:
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=30)
        connection.row_factory = sqlite3.Row
    except sqlite3.DatabaseError:
        return None
    with closing(connection):
        try:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            if "ai_workshop_reviews" not in tables:
                return None
            if output_hash is None:
                row = connection.execute(
                    "SELECT response_json FROM ai_workshop_reviews WHERE job_id=? "
                    "ORDER BY created_at DESC LIMIT 1", (job_id,),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT response_json FROM ai_workshop_reviews WHERE job_id=? "
                    "AND output_hash=?", (job_id, _expected_hash(output_hash)),
                ).fetchone()
        except (sqlite3.DatabaseError, ReviewError):
            return None
    return json.loads(row["response_json"]) if row is not None else None
