"""Private versioned storage for Scene-lab proposals.

Drafts reuse existing scenes (`scenes` table, owned by scene_play) and never
apply, publish or execute anything: draft/approved/rejected is review state
only. Integration (routes/authorization/UI) belongs to Codex; this module is
pure storage with native ledger (visibility=gm) and receipt-first idempotency.
"""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .session_ledger import append_session_ledger_event, init_session_ledger

KINDS = {"action", "scene_bundle"}
STATUSES = {"draft", "approved", "rejected"}
DECISIONS = {"approved", "rejected"}
MAX_CONTENT_CHARS = 50000
MAX_SUMMARY_CHARS = 50000
MAX_TITLE = 180
MAX_AUTHOR = 180
MAX_REASON = 2000
MAX_DEPTH = 64
RUN_ID_RE = re.compile(r"^test-[0-9a-f]{32}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def _request_id(value: Any) -> str:
    request_id = str(value or "").strip()
    if (
        not 8 <= len(request_id) <= 120
        or not all(char.isalnum() or char in "._:-" for char in request_id)
    ):
        raise ValueError("request_id inválido")
    return request_id


def _title(value: Any) -> str:
    title = str(value or "").strip()
    if not title:
        raise ValueError("Título é obrigatório")
    if len(title) > MAX_TITLE:
        raise ValueError(f"Título excede {MAX_TITLE} caracteres")
    return title


def _kind(value: Any) -> str:
    kind = str(value or "").strip()
    if kind not in KINDS:
        raise ValueError(f"kind inválido: {kind!r} (use action ou scene_bundle)")
    return kind


def _check_depth(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise ValueError("Profundidade excessiva no objeto JSON")
    if isinstance(value, dict):
        for item in value.values():
            _check_depth(item, depth + 1)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_depth(item, depth + 1)


def _dump_strict(value: Any, label: str) -> str:
    _check_depth(value)
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        raise ValueError(f"{label} inválido: JSON inválido (NaN/Infinity)")


def _content(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Conteúdo da proposta inválido: objeto JSON esperado")
    raw = _dump_strict(value, "Conteúdo da proposta")
    if len(raw) > MAX_CONTENT_CHARS:
        raise ValueError(f"Conteúdo excede {MAX_CONTENT_CHARS} caracteres")
    return value


def _summary(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Resumo da evidência inválido: objeto JSON esperado")
    raw = _dump_strict(value, "Resumo da evidência")
    if len(raw) > MAX_SUMMARY_CHARS:
        raise ValueError(f"Resumo excede {MAX_SUMMARY_CHARS} caracteres")
    return json.loads(raw)


def _author(value: Any) -> str:
    author = str(value or "").strip()
    if not author:
        raise ValueError("Autor é obrigatório")
    if len(author) > MAX_AUTHOR:
        raise ValueError(f"Autor excede {MAX_AUTHOR} caracteres")
    return author


def init_lab(database_path: Path) -> None:
    """Create lab tables only. Scenes keep belonging to scene_play."""
    database_path = Path(database_path)
    init_session_ledger(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS scene_lab_proposals (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              scene_id INTEGER NOT NULL,
              title TEXT NOT NULL,
              kind TEXT NOT NULL,
              version INTEGER NOT NULL DEFAULT 1,
              status TEXT NOT NULL DEFAULT 'draft',
              content_json TEXT NOT NULL,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              evidence_json TEXT,
              decision_reason TEXT
            );
            CREATE TABLE IF NOT EXISTS scene_lab_revisions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              proposal_id INTEGER NOT NULL,
              version INTEGER NOT NULL,
              title TEXT NOT NULL,
              content_json TEXT NOT NULL,
              created_at TEXT NOT NULL,
              request_id TEXT NOT NULL,
              UNIQUE(proposal_id, version)
            );
            CREATE TABLE IF NOT EXISTS scene_lab_receipts (
              request_id TEXT PRIMARY KEY,
              fingerprint TEXT NOT NULL,
              response_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS scene_lab_history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              proposal_id INTEGER NOT NULL,
              version INTEGER NOT NULL,
              event TEXT NOT NULL,
              detail_json TEXT,
              request_id TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_scene_lab_proposals_scene
              ON scene_lab_proposals(scene_id, id DESC);
            CREATE INDEX IF NOT EXISTS idx_scene_lab_history_proposal
              ON scene_lab_history(proposal_id, id);
            """
        )


def _scene_exists(connection: sqlite3.Connection, scene_id: Any) -> bool:
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if "scenes" not in tables:
        return False
    if type(scene_id) is not int:
        return False
    return (
        connection.execute("SELECT 1 FROM scenes WHERE id=?", (scene_id,)).fetchone()
        is not None
    )


def _history(connection: sqlite3.Connection, proposal_id: int) -> list[dict[str, Any]]:
    return [
        {
            "version": row["version"],
            "event": row["event"],
            "detail": json.loads(row["detail_json"]) if row["detail_json"] else None,
            "request_id": row["request_id"],
            "created_at": row["created_at"],
        }
        for row in connection.execute(
            "SELECT version,event,detail_json,request_id,created_at"
            " FROM scene_lab_history WHERE proposal_id=? ORDER BY id",
            (proposal_id,),
        )
    ]


def _revisions(connection: sqlite3.Connection, proposal_id: int) -> list[dict[str, Any]]:
    return [
        {
            "version": row["version"],
            "title": row["title"],
            "content": json.loads(row["content_json"]),
            "created_at": row["created_at"],
        }
        for row in connection.execute(
            "SELECT version,title,content_json,created_at"
            " FROM scene_lab_revisions WHERE proposal_id=? ORDER BY version",
            (proposal_id,),
        )
    ]


def _dto(
    connection: sqlite3.Connection, proposal_id: int, *, include_revisions: bool = False
) -> dict[str, Any]:
    row = connection.execute(
        "SELECT * FROM scene_lab_proposals WHERE id=?", (proposal_id,)
    ).fetchone()
    if row is None:
        raise ValueError("Proposta não encontrada")
    dto = {
        "id": row["id"],
        "scene_id": row["scene_id"],
        "title": row["title"],
        "kind": row["kind"],
        "version": row["version"],
        "status": row["status"],
        "content": json.loads(row["content_json"]),
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "evidence": json.loads(row["evidence_json"]) if row["evidence_json"] else None,
        "decision_reason": row["decision_reason"],
        "history": _history(connection, row["id"]),
    }
    if include_revisions:
        dto["revisions"] = _revisions(connection, row["id"])
    return dto


def _record_history(
    connection: sqlite3.Connection,
    *,
    proposal_id: int,
    version: int,
    event: str,
    detail: dict[str, Any] | None,
    request_id: str,
    now: str,
) -> None:
    connection.execute(
        "INSERT INTO scene_lab_history(proposal_id,version,event,detail_json,request_id,created_at)"
        " VALUES(?,?,?,?,?,?)",
        (
            proposal_id,
            version,
            event,
            json.dumps(detail, ensure_ascii=False) if detail is not None else None,
            request_id,
            now,
        ),
    )


def _ledger(
    connection: sqlite3.Connection,
    *,
    request_id: str,
    event_kind: str,
    actor: str,
    title: str,
    detail: dict[str, Any],
    now: str,
) -> None:
    append_session_ledger_event(
        connection,
        source_type="scene_lab_proposal",
        source_id=request_id,
        event_kind=event_kind,
        actor_id=actor,
        actor_name=actor,
        actor_role="gm",
        character_id=None,
        title=title,
        detail=detail,
        visibility="gm",
        created_at=now,
    )


def _receipt(
    connection: sqlite3.Connection, request_id: str, fingerprint: list[Any]
) -> dict[str, Any] | None:
    """Receipt first: retries after the version advanced still recover."""
    previous = connection.execute(
        "SELECT fingerprint,response_json FROM scene_lab_receipts WHERE request_id=?",
        (request_id,),
    ).fetchone()
    if previous is None:
        return None
    if json.loads(previous[0]) != fingerprint:
        raise ValueError("request_id já utilizado com outro conteúdo")
    return json.loads(previous[1])


def _store_receipt(
    connection: sqlite3.Connection,
    request_id: str,
    fingerprint: list[Any],
    response: dict[str, Any],
) -> None:
    connection.execute(
        "INSERT INTO scene_lab_receipts(request_id,fingerprint,response_json)"
        " VALUES(?,?,?)",
        (request_id, json.dumps(fingerprint, ensure_ascii=False), json.dumps(response, ensure_ascii=False)),
    )


def _current(connection: sqlite3.Connection, proposal_id: Any) -> sqlite3.Row:
    if type(proposal_id) is not int:
        raise ValueError("Proposta não encontrada")
    row = connection.execute(
        "SELECT * FROM scene_lab_proposals WHERE id=?", (proposal_id,)
    ).fetchone()
    if row is None:
        raise ValueError("Proposta não encontrada")
    return row


def _check_version(row: sqlite3.Row, expected_version: Any) -> None:
    if type(expected_version) is not int or row["version"] != expected_version:
        raise ValueError(
            f"Versão desatualizada: proposta está na revisão {row['version']}"
        )


def create_proposal(
    database_path: Path,
    *,
    scene_id: int,
    title: str,
    kind: str,
    content: dict[str, Any],
    created_by: str,
    request_id: str,
) -> dict[str, Any]:
    request_id = _request_id(request_id)
    title = _title(title)
    kind = _kind(kind)
    content = _content(content)
    created_by = _author(created_by)
    if type(scene_id) is not int:
        raise ValueError("Cena não encontrada")
    fingerprint = ["create", scene_id, title, kind, content, created_by]
    init_lab(Path(database_path))
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        replay = _receipt(connection, request_id, fingerprint)
        if replay is not None:
            return replay
        if not _scene_exists(connection, scene_id):
            raise ValueError("Cena não encontrada")
        now = _now()
        cursor = connection.execute(
            "INSERT INTO scene_lab_proposals(scene_id,title,kind,version,status,"
            "content_json,created_by,created_at,updated_at)"
            " VALUES(?,?,?,1,'draft',?,?,?,?)",
            (scene_id, title, kind, json.dumps(content, ensure_ascii=False), created_by, now, now),
        )
        proposal_id = int(cursor.lastrowid)
        connection.execute(
            "INSERT INTO scene_lab_revisions(proposal_id,version,title,content_json,created_at,request_id)"
            " VALUES(?,1,?,?,?,?)",
            (proposal_id, title, json.dumps(content, ensure_ascii=False), now, request_id),
        )
        _record_history(
            connection,
            proposal_id=proposal_id,
            version=1,
            event="created",
            detail={"scene_id": scene_id, "kind": kind},
            request_id=request_id,
            now=now,
        )
        _ledger(
            connection,
            request_id=request_id,
            event_kind="proposal_created",
            actor=created_by,
            title=f"Proposta '{title}' criada para a cena {scene_id}",
            detail={"proposal_id": proposal_id, "version": 1, "scene_id": scene_id, "kind": kind},
            now=now,
        )
        response = _dto(connection, proposal_id)
        _store_receipt(connection, request_id, fingerprint, response)
        return response


def update_proposal(
    database_path: Path,
    proposal_id: int,
    *,
    expected_version: int,
    content: dict[str, Any],
    title: str,
    request_id: str,
) -> dict[str, Any]:
    request_id = _request_id(request_id)
    title = _title(title)
    content = _content(content)
    fingerprint = ["update", proposal_id, expected_version, title, content]
    init_lab(Path(database_path))
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        replay = _receipt(connection, request_id, fingerprint)
        if replay is not None:
            return replay
        row = _current(connection, proposal_id)
        _check_version(row, expected_version)
        now = _now()
        version = int(row["version"]) + 1
        connection.execute(
            "UPDATE scene_lab_proposals SET title=?,content_json=?,version=?,"
            "status='draft',evidence_json=NULL,decision_reason=NULL,updated_at=? WHERE id=?",
            (title, json.dumps(content, ensure_ascii=False), version, now, row["id"]),
        )
        connection.execute(
            "INSERT INTO scene_lab_revisions(proposal_id,version,title,content_json,created_at,request_id)"
            " VALUES(?,?,?,?,?,?)",
            (row["id"], version, title, json.dumps(content, ensure_ascii=False), now, request_id),
        )
        _record_history(
            connection,
            proposal_id=row["id"],
            version=version,
            event="updated",
            detail={"from_version": row["version"]},
            request_id=request_id,
            now=now,
        )
        _ledger(
            connection,
            request_id=request_id,
            event_kind="proposal_updated",
            actor=row["created_by"],
            title=f"Proposta '{title}' revisada (v{version})",
            detail={"proposal_id": row["id"], "version": version, "scene_id": row["scene_id"]},
            now=now,
        )
        response = _dto(connection, row["id"])
        _store_receipt(connection, request_id, fingerprint, response)
        return response


def list_proposals(
    database_path: Path, *, scene_id: int | None = None
) -> list[dict[str, Any]]:
    init_lab(Path(database_path))
    with closing(_connect(Path(database_path))) as connection:
        if scene_id is None:
            rows = connection.execute(
                "SELECT id,scene_id,title,kind,version,status,updated_at"
                " FROM scene_lab_proposals ORDER BY id"
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT id,scene_id,title,kind,version,status,updated_at"
                " FROM scene_lab_proposals WHERE scene_id=? ORDER BY id",
                (scene_id,),
            ).fetchall()
    return [dict(row) for row in rows]


def get_proposal(database_path: Path, proposal_id: int) -> dict[str, Any]:
    init_lab(Path(database_path))
    with closing(_connect(Path(database_path))) as connection:
        return _dto(connection, proposal_id, include_revisions=True)


def peek_evidence_receipt(
    database_path: Path,
    proposal_id: int,
    *,
    expected_version: int,
    run_id: str,
    request_id: str,
) -> dict[str, Any] | None:
    """Read a prior evidence receipt before reading an ephemeral MCP report.

    No initialization, DDL, writes or current-version lookup. A repeated intent
    recovers its immutable response even after the report disappeared or the
    proposal advanced. Reusing the ID for another proposal/version/run conflicts.
    Stored JSON is bounded and invalid data is never echoed in errors.
    """
    request_id = _request_id(request_id)
    if type(proposal_id) is not int or proposal_id < 1:
        raise ValueError("Proposta não encontrada")
    if type(expected_version) is not int or expected_version < 1:
        raise ValueError("Versão da proposta inválida")
    run_id = str(run_id or "").strip()
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id inválido: use test-<32hex>")
    database = Path(database_path).resolve()
    if not database.is_file():
        return None
    try:
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=30)) as connection:
            connection.execute("PRAGMA query_only=ON")
            if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='scene_lab_receipts'").fetchone() is None:
                return None
            row = connection.execute(
                "SELECT CASE WHEN length(fingerprint)<=? THEN fingerprint END,"
                " CASE WHEN length(response_json)<=1000000 THEN response_json END"
                " FROM scene_lab_receipts WHERE request_id=?",
                (MAX_SUMMARY_CHARS + 512, request_id),
            ).fetchone()
    except sqlite3.DatabaseError as error:
        raise ValueError("Recibo de evidência inválido") from error
    if row is None:
        return None
    if row[0] is None or row[1] is None:
        raise ValueError("Recibo de evidência excede limite ou está inválido")
    try:
        fingerprint = json.loads(row[0])
        if (not isinstance(fingerprint, list) or len(fingerprint) != 5
                or type(fingerprint[1]) is not int or type(fingerprint[2]) is not int
                or fingerprint[:4] != ["attach_evidence", proposal_id, expected_version, run_id]):
            raise ValueError("request_id já utilizado com outro conteúdo")
        _summary(fingerprint[4])
    except (TypeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Recibo de evidência inválido") from error
    try:
        response = json.loads(row[1])
        if not isinstance(response, dict):
            raise ValueError("Recibo de evidência inválido")
        _dump_strict(response, "Recibo de evidência")
        saved_evidence = response.get("evidence")
        if (response.get("id") != proposal_id or response.get("version") != expected_version
                or not isinstance(saved_evidence, dict) or saved_evidence.get("run_id") != run_id
                or saved_evidence.get("version") != expected_version):
            raise ValueError("Recibo de evidência inválido")
    except (ValueError, TypeError, RecursionError) as error:
        raise ValueError("Recibo de evidência inválido") from error
    return response


def attach_evidence(
    database_path: Path,
    proposal_id: int,
    *,
    expected_version: int,
    run_id: str,
    summary: dict[str, Any],
    request_id: str,
) -> dict[str, Any]:
    request_id = _request_id(request_id)
    run_id = str(run_id or "").strip()
    if not RUN_ID_RE.match(run_id):
        raise ValueError("run_id inválido: use test-<32hex>")
    summary = _summary(summary)
    summary_raw = json.dumps(summary, ensure_ascii=False)
    fingerprint = ["attach_evidence", proposal_id, expected_version, run_id, summary]
    init_lab(Path(database_path))
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        replay = _receipt(connection, request_id, fingerprint)
        if replay is not None:
            return replay
        row = _current(connection, proposal_id)
        _check_version(row, expected_version)
        now = _now()
        evidence = {
            "run_id": run_id,
            "summary": json.loads(summary_raw),
            "version": row["version"],
            "content_snapshot": json.loads(row["content_json"]),
            "created_at": now,
        }
        connection.execute(
            "UPDATE scene_lab_proposals SET evidence_json=?,updated_at=? WHERE id=?",
            (json.dumps(evidence, ensure_ascii=False), now, row["id"]),
        )
        _record_history(
            connection,
            proposal_id=row["id"],
            version=row["version"],
            event="evidence",
            detail={"run_id": run_id, "summary": json.loads(summary_raw)},
            request_id=request_id,
            now=now,
        )
        _ledger(
            connection,
            request_id=request_id,
            event_kind="proposal_evidence",
            actor=row["created_by"],
            title=f"Evidência vinculada à proposta '{row['title']}' (v{row['version']})",
            detail={"proposal_id": row["id"], "version": row["version"], "run_id": run_id},
            now=now,
        )
        response = _dto(connection, row["id"])
        _store_receipt(connection, request_id, fingerprint, response)
        return response


def set_decision(
    database_path: Path,
    proposal_id: int,
    *,
    expected_version: int,
    decision: str,
    reason: str,
    request_id: str,
) -> dict[str, Any]:
    request_id = _request_id(request_id)
    decision = str(decision or "").strip()
    if decision not in DECISIONS:
        raise ValueError("Decisão inválida: use approved ou rejected")
    reason = str(reason or "").strip()
    if not reason:
        raise ValueError("Motivo da decisão é obrigatório")
    if len(reason) > MAX_REASON:
        raise ValueError(f"Motivo da decisão excede {MAX_REASON} caracteres")
    fingerprint = ["set_decision", proposal_id, expected_version, decision, reason]
    init_lab(Path(database_path))
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        replay = _receipt(connection, request_id, fingerprint)
        if replay is not None:
            return replay
        row = _current(connection, proposal_id)
        _check_version(row, expected_version)
        now = _now()
        connection.execute(
            "UPDATE scene_lab_proposals SET status=?,decision_reason=?,updated_at=? WHERE id=?",
            (decision, reason, now, row["id"]),
        )
        _record_history(
            connection,
            proposal_id=row["id"],
            version=row["version"],
            event="decision",
            detail={"decision": decision, "reason": reason},
            request_id=request_id,
            now=now,
        )
        _ledger(
            connection,
            request_id=request_id,
            event_kind="proposal_decision",
            actor=row["created_by"],
            title=f"Proposta '{row['title']}' {decision} (v{row['version']})",
            detail={"proposal_id": row["id"], "version": row["version"], "decision": decision},
            now=now,
        )
        response = _dto(connection, row["id"])
        _store_receipt(connection, request_id, fingerprint, response)
        return response
