"""Local operator dashboard. No Core initialization, providers or write connections."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import sys
from contextlib import closing
from uuid import uuid4
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".local-tools"))
from omnisvera_mcp.core.context import CallContext
from omnisvera_mcp.core.policy import PolicyEngine, AuthorizationDenied
from omnisvera_mcp.memory.store import MemoryStore

SCOPES = frozenset({"epistemic.read", "experience.read", "memory.read", "world.read", "monitor.read"})


def decoded(raw, fallback):
    try:
        return json.loads(raw) if raw else fallback
    except (ValueError, TypeError):
        return fallback


def source_projection(source):
    """Allowlisted provenance; never send headers, credentials or URL queries."""
    if not isinstance(source, dict):
        return {}
    result = {key: source[key] for key in ("provider", "observation_world_id", "derivation", "sha256")
              if isinstance(source.get(key), str)}
    # URLs are displayed as text, never fetched by this app.
    url = source.get("url")
    if isinstance(url, str):
        try:
            parts = urlsplit(url)
            if parts.scheme in {"https", "http"} and parts.hostname:
                result["url"] = urlunsplit((parts.scheme, parts.hostname, parts.path, "", ""))
        except ValueError:
            pass
    return result


def age_seconds(timestamp, now):
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return max(0, int((now - parsed).total_seconds()))
    except (ValueError, TypeError, AttributeError):
        return None


def signal_projection(row, now):
    result = {key: row.get(key) for key in ("id", "signal_id", "entity_ref", "schema", "value_type",
              "unit", "observed_at", "recorded_at", "observation_hash")}
    value = decoded(row.get("value_json"), None)
    # WorldSignal's documented types are scalar. Unexpected objects are withheld.
    result["value"] = value if value is None or isinstance(value, (str, int, float, bool)) else None
    result["source"] = source_projection(decoded(row.get("source_json"), {}))
    metadata = decoded(row.get("metadata_json"), {})
    freshness = metadata.get("freshness") if isinstance(metadata, dict) else None
    result["freshness_at_capture"] = freshness if freshness in {"fresh", "stale", "unavailable", "error"} else "unknown"
    result["age_seconds"] = age_seconds(result["observed_at"], now)
    return result


class ReadStore(MemoryStore):
    def __init__(self, path: Path):
        self.path = Path(path).resolve()  # Deliberately bypass schema initialization.

    def _connect(self):
        connection = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=2)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        return connection

    def rows(self, sql, args=()):
        with closing(self._connect()) as connection:
            return [dict(row) for row in connection.execute(sql, args)]


def create_app(db: Path, token: str, scopes=SCOPES, dist: Path | None = None, *, clock=None, environment_label="Dados persistidos"):
    if len(token) < 32:
        raise ValueError("A dedicated operator token of at least 32 characters is required")
    store = ReadStore(db)
    now = clock or (lambda: datetime.now(timezone.utc))
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def safety(request: Request, call_next):
        try:
            response = await call_next(request)
        except (sqlite3.Error, json.JSONDecodeError):
            from fastapi.responses import JSONResponse
            response = JSONResponse({"detail": "Persisted store unavailable or incompatible"}, status_code=503)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'"
        return response

    def authorize(*required):
        def check(request: Request):
            supplied = request.headers.get("X-Omnisvera-App-Token", "")
            if not hmac.compare_digest(supplied.encode(), token.encode()):
                raise HTTPException(401, "Operator authentication required")
            if set(request.query_params) & {"actor", "client", "transport", "scopes", "request_id", "project_id", "task_id"}:
                raise HTTPException(400, "Identity is server-controlled")
            context = CallContext(actor="sage", client="omnisvera-app", transport="http-read-only",
                                  scopes=frozenset(scopes), request_id=uuid4().hex)
            try:
                PolicyEngine().require(context, required_scopes=frozenset(required))
            except AuthorizationDenied:
                raise HTTPException(403, "Read scope denied")
            return context
        return check

    @app.get("/api/football/signals", dependencies=[Depends(authorize("world.read"))])
    def signals(signal_id: str | None = Query(None, max_length=200), entity_ref: str | None = Query(None, max_length=300),
                since: datetime | None = None, until: datetime | None = None,
                limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0)):
        for date in (since, until):
            if date and date.tzinfo is None:
                raise HTTPException(422, "Period timestamps must include a timezone")
        if since and until and since > until:
            raise HTTPException(422, "Period start must precede end")
        clauses, args = ["world_id='football'"], []
        for field, value in (("signal_id", signal_id), ("entity_ref", entity_ref)):
            if value is not None:
                clauses.append(f"{field}=?")
                args.append(value)
        for operator, date in ((">=", since), ("<=", until)):
            if date:
                clauses.append(f"julianday(observed_at){operator}julianday(?)")
                args.append(date.isoformat())
        where = " AND ".join(clauses)
        rows = store.rows(f"SELECT * FROM signal_observations WHERE {where} ORDER BY julianday(observed_at) DESC,id DESC LIMIT ? OFFSET ?", (*args, limit, offset))
        total = store.rows(f"SELECT COUNT(*) AS n FROM signal_observations WHERE {where}", args)[0]["n"]
        stamp = now()
        return {"items": [signal_projection(row, stamp) for row in rows], "total": total,
                "read_at": stamp.isoformat(), "freshness_rule": "age-only; no inferred TTL"}

    def experience_projection(exp):
        result = {key: exp.get(key) for key in ("experience_id", "world_id", "predictor_id", "predictor_version",
                  "state_version", "previous_experience_id", "previous_state_version", "created_at", "updated_at",
                  "learned_state_schema", "learned_state_hash", "integrity_ok", "integrity_computed",
                  "observations_used", "predictions_made", "outcomes_seen")}
        performance = exp.get("performance") or {}
        result["performance"] = {key: performance.get(key) for key in ("resolved_predictions", "mean_brier",
                               "first_prediction_at", "last_prediction_at", "last_outcome_at")}
        result["source_predictions"] = []
        for pid in exp.get("source_prediction_ids", []):
            rows = store.rows("SELECT id,claim,status,evidence_mode FROM predictions WHERE id=? AND world_id='football'", (pid,))
            result["source_predictions"].append(rows[0] if rows else {"id": pid, "status": "unavailable"})
        result["source_outcomes"] = []
        for oid in exp.get("source_outcome_ids", []):
            rows = store.rows("""SELECT r.id,r.prediction_id,r.outcome,r.resolved_at,r.calibration_score
                FROM prediction_resolutions r JOIN predictions p ON p.id=r.prediction_id
                WHERE r.id=? AND p.world_id='football'""", (oid,))
            result["source_outcomes"].append(rows[0] if rows else {"id": oid, "status": "unavailable"})
        return result

    @app.get("/api/football/experiences", dependencies=[Depends(authorize("experience.read", "epistemic.read"))])
    def experiences(predictor_id: str = Query(..., min_length=1, max_length=200),
                    predictor_version: str = Query(..., min_length=1, max_length=100),
                    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
        args = (predictor_id, predictor_version)
        clause = "world_id='football' AND predictor_id=? AND predictor_version=?"
        rows = store.rows(f"SELECT experience_id FROM predictor_experiences WHERE {clause} ORDER BY state_version DESC LIMIT ? OFFSET ?", (*args, limit, offset))
        total = store.rows(f"SELECT COUNT(*) AS n FROM predictor_experiences WHERE {clause}", args)[0]["n"]
        return {"items": [experience_projection(store.experience_get(row["experience_id"])) for row in rows], "total": total}

    @app.get("/api/football", dependencies=[Depends(authorize("epistemic.read", "experience.read"))])
    def football(limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0)):
        predictions = store.rows("""SELECT id, claim, probability, horizon, status, created_at,
            evidence_mode, predictor_id, predictor_version, experience_id
            FROM predictions WHERE world_id='football' ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?""", (limit, offset))
        metrics = store.rows("""SELECT p.evidence_mode,COUNT(*) AS count,AVG(r.calibration_score) AS mean_brier,
            MIN(r.resolved_at) AS first_resolved_at,MAX(r.resolved_at) AS last_resolved_at
            FROM predictions p JOIN prediction_resolutions r ON r.prediction_id=p.id
            WHERE p.world_id='football' GROUP BY p.evidence_mode""")
        total = store.rows("SELECT COUNT(*) AS count FROM predictions WHERE world_id='football'")[0]["count"]
        return {"predictions": predictions, "total": total, "metrics": metrics,
                "experiences": store.experience_list_world("football"),
                "accuracy": None, "roi": None, "mode": "persisted-only", "environment_label": environment_label}

    @app.get("/api/football/predictions/{prediction_id}", dependencies=[Depends(authorize("epistemic.read", "experience.read", "memory.read", "world.read"))])
    def prediction(prediction_id: int):
        found = store.rows("SELECT id FROM predictions WHERE id=? AND world_id='football'", (prediction_id,))
        if not found:
            raise HTTPException(404, "Football prediction not found")
        item = store.get_prediction(prediction_id)
        fields = ("id", "claim", "probability", "horizon", "status", "created_at", "evidence_mode",
                  "predictor_id", "predictor_version", "snapshot_memory_id", "snapshot_hash", "snapshot_intact",
                  "candidate_hash", "experience_id", "experience_state_version", "experience_state_hash", "subject_ref")
        result = {key: item.get(key) for key in fields}
        resolution = item.get("resolution")
        result["resolution"] = None if not resolution else {key: resolution.get(key) for key in
            ("id", "resolved_at", "observed_value", "outcome", "calibration_score")}
        snapshot = store.get_memory(item["snapshot_memory_id"])
        result["evidence"] = None
        if snapshot and snapshot.get("type") == "model_snapshot" and snapshot.get("classification") in {"internal", "public"}:
            result["evidence"] = {"id": snapshot["id"], "created_at": snapshot["created_at"],
                "sha256": hashlib.sha256(snapshot["content"].encode()).hexdigest(),
                "sources": [{key: source.get(key) for key in ("source_type", "source_timestamp", "relation", "excerpt_hash")}
                            for source in snapshot.get("sources", [])]}
        result["experience"] = None
        if item.get("experience_id"):
            experience = store.experience_get(item["experience_id"])
            if experience and experience["world_id"] == "football":
                result["experience"] = {key: experience.get(key) for key in
                    ("experience_id", "state_version", "learned_state_schema", "learned_state_hash", "integrity_ok", "previous_experience_id", "created_at")}
                result["experience_reference_intact"] = (experience["state_version"] == item.get("experience_state_version")
                    and experience["learned_state_hash"] == item.get("experience_state_hash"))
                result["experience"].update({key: experience[key] for key in ("predictor_id", "predictor_version")})
        # References only: never infer that a recent observation was used by an older prediction.
        result["signal_refs"] = []
        for ref in decoded(item.get("signals_used_json"), []):
            if isinstance(ref, str):
                result["signal_refs"].append({"signal_id": ref})
            elif isinstance(ref, dict) and isinstance(ref.get("signal_id"), str):
                result["signal_refs"].append({key: ref[key] for key in
                    ("signal_id", "entity_ref", "observed_at", "observation_hash")
                    if isinstance(ref.get(key), str)})
        return result

    @app.get("/api/monitor", dependencies=[Depends(authorize("monitor.read"))])
    def monitor():
        # No raw error, arguments, metadata, target, request IDs or source URLs leave the store.
        events = store.rows("""SELECT timestamp,action,result,duration_ms FROM audit_events
            ORDER BY timestamp DESC LIMIT 40""")
        allowed_results = {"success", "error", "denied", "ok"}
        for event in events:
            event["action"] = event["action"] if isinstance(event["action"], str) and all(c.isalnum() or c in "._-" for c in event["action"]) else "tool"
            event["result"] = event["result"] if event["result"] in allowed_results else "recorded"
        runs = store.rows("""SELECT run_started_at,run_finished_at,success,signals_seen,signals_changed,
            signals_unchanged FROM scheduler_runs ORDER BY id DESC LIMIT 20""")
        # Restrict impact to the World displayed. A recorded success is not live health.
        football_runs = store.rows("""SELECT run_started_at,run_finished_at,success,signals_seen
            FROM scheduler_runs WHERE world_id='football' ORDER BY id DESC LIMIT 1""")
        return {"database": "readable", "live_services": "not_probed", "events": events, "scheduler": runs,
                "football_last_run": football_runs[0] if football_runs else None,
                "read_at": now().isoformat()}

    if dist and dist.is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")
        @app.get("/")
        def index():
            return FileResponse(dist / "omnisvera.html")
    return app


def configured_app():
    return create_app(Path(os.environ["OMNISVERA_APP_DB"]), os.environ["OMNISVERA_APP_TOKEN"],
                      dist=Path(__file__).resolve().parents[1] / "frontend" / "dist-omnisvera",
                      environment_label="Banco operacional · leitura autenticada · sem execução de providers")
