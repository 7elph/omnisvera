"""Experience Update Runtime v0.1 — outcome → experience version, durable, exactly-once."""
from __future__ import annotations

import traceback
from typing import Any

from ..memory.store import MemoryStore
from .updater import ExperienceUpdaterRegistry


def _sanitize_error(exc: BaseException, limit: int = 500) -> str:
    msg = f"{type(exc).__name__}: {exc}"
    return msg[:limit]


def process_experience_update_event(
    store: MemoryStore,
    registry: ExperienceUpdaterRegistry,
    update_event_id: str,
) -> dict[str, Any]:
    """Process a single update event idempotently.

    Returns the updated event dict.
    Resolution is never undone; failures are recorded on the event.
    """
    # Fetch event
    event = store.experience_update_get(update_event_id)
    if not event:
        raise ValueError(f"update event not found: {update_event_id}")
    # Idempotency for terminal states that should not be reprocessed automatically
    if event["status"] in ("applied", "no_updater", "missing_experience", "integrity_failed", "causal_reorder_required"):
        return event  # already terminal (except failed which is retryable)
    # For failed, we will retry (increment attempt)
    prediction_id: int = int(event["prediction_id"])
    world_id: str = str(event["world_id"])
    predictor_id: str = str(event["predictor_id"])
    predictor_version: str = str(event["predictor_version"])

    # Fetch prediction + resolution
    pred = store.get_prediction(prediction_id)
    if not pred:
        return store.experience_update_mark(update_event_id, status="failed", last_error=f"prediction not found: {prediction_id}")  # type: ignore

    # Fetch resolution row directly
    # Use store internal connection to get resolution + calibration
    from contextlib import closing
    resolution: dict[str, Any] | None = None
    with closing(store._connect()) as conn:  # type: ignore
        row = conn.execute("SELECT id, resolved_at, outcome, observed_value, calibration_score, sources_json, notes FROM prediction_resolutions WHERE prediction_id=?", (prediction_id,)).fetchone()
        if row:
            resolution = dict(row)

    if not resolution:
        return store.experience_update_mark(update_event_id, status="failed", last_error="resolution not found for prediction")  # type: ignore

    # Lookup updater
    updater = registry.get(predictor_id, predictor_version)
    if updater is None:
        return store.experience_update_mark(update_event_id, status="no_updater", last_error=f"no updater for {predictor_id}:{predictor_version}", increment_attempt=False)  # type: ignore

    # Check previous experience exists (B: require v1)
    prev = store.experience_latest(world_id, predictor_id, predictor_version)
    if prev is None:
        return store.experience_update_mark(update_event_id, status="missing_experience", last_error="no previous experience; v1 required", increment_attempt=False)  # type: ignore

    # Integrity check
    if not prev.get("integrity_ok", True):
        return store.experience_update_mark(update_event_id, status="integrity_failed", last_error="previous_experience_integrity_failed", increment_attempt=False)  # type: ignore

    # Check prediction's referenced experience (lineage) — prediction basis vs update base
    trigger_exp_id = pred.get("experience_id")
    trigger_exp_version = pred.get("experience_state_version")
    trigger_exp_hash = pred.get("experience_state_hash")
    trigger_experience: dict[str, Any] | None = None
    trigger_is_latest: bool | None = None
    prediction_basis = None
    update_basis = {"experience_id": prev.get("experience_id"), "state_version": prev.get("state_version")}
    if trigger_exp_id:
        trigger_experience = store.experience_get(trigger_exp_id)
        if not trigger_experience:
            return store.experience_update_mark(update_event_id, status="failed", last_error=f"trigger experience not found: {trigger_exp_id}")  # type: ignore
        if not trigger_experience.get("integrity_ok"):
            return store.experience_update_mark(update_event_id, status="failed", last_error="trigger experience integrity failed")  # type: ignore
        # Validate identity/hash already validated at commit, but re-check version/hash match
        if trigger_experience.get("learned_state_hash") != trigger_exp_hash or trigger_experience.get("state_version") != trigger_exp_version:
            return store.experience_update_mark(update_event_id, status="failed", last_error="trigger experience version/hash mismatch")  # type: ignore
        trigger_is_latest = bool(prev.get("experience_id") == trigger_exp_id)
        prediction_basis = {"experience_id": trigger_exp_id, "state_version": trigger_exp_version}
        # If trigger is historical and latest has advanced, we keep provenance but base update on latest (detect conflict explicitly)
        # For v0.1 we proceed with latest as base but record trigger lineage

    # Causal ordering check (deterministic, not thread scheduling)
    updater_desc = updater.describe()
    order_semantics = updater_desc.get("update_order_semantics", "order_sensitive")
    # Derive causal key for this event (from ledger, or fallback to resolution time)
    causal_key = event.get("causal_key")
    if not causal_key:
        # Fallback derive
        resolved_at = resolution.get("resolved_at") or ""
        causal_key = f"{resolved_at}#{prediction_id:010d}"
    if order_semantics == "order_sensitive":
        # Find max applied causal_key for this predictor
        from contextlib import closing as _closing
        with _closing(store._connect()) as conn:  # type: ignore
            row = conn.execute(
                "SELECT causal_key FROM experience_update_events WHERE world_id=? AND predictor_id=? AND predictor_version=? AND status='applied' AND causal_key IS NOT NULL ORDER BY causal_key DESC LIMIT 1",
                (world_id, predictor_id, predictor_version),
            ).fetchone()
            max_causal = row["causal_key"] if row and row["causal_key"] else None
            if max_causal and causal_key < max_causal:
                return store.experience_update_mark(update_event_id, status="causal_reorder_required", last_error=f"out-of-order: {causal_key} < max_applied {max_causal}", increment_attempt=False)  # type: ignore

    # Call updater
    try:
        result = updater.update(
            previous_experience=prev,
            prediction=pred,
            resolution=resolution,
            context={"world_id": world_id, "trigger_experience": trigger_experience, "trigger_is_latest": trigger_is_latest, "causal_key": causal_key, "prediction_basis": prediction_basis, "update_basis": update_basis},
        )
    except Exception as exc:
        err = _sanitize_error(exc)
        return store.experience_update_mark(update_event_id, status="failed", last_error=err)  # type: ignore

    # Prepare new experience fields
    # Derive source ids: previous + trigger
    prev_pred_ids: list[int] = list(prev.get("source_prediction_ids") or [])
    prev_out_ids: list[int] = list(prev.get("source_outcome_ids") or [])
    # Ensure trigger ids are included (avoid duplicate)
    new_pred_ids = prev_pred_ids[:]
    if prediction_id not in new_pred_ids:
        new_pred_ids.append(prediction_id)
    new_out_ids = prev_out_ids[:]
    # resolution id as outcome id (use prediction_id as proxy if no separate outcome id)
    res_id = int(resolution.get("id", prediction_id))
    if res_id not in new_out_ids:
        new_out_ids.append(res_id)

    observations_used = int(prev.get("observations_used", 0) or 0) + int(getattr(result, "observations_used_delta", 1) or 1)

    # Decide learned_state to persist
    # If state_changed false, we still create a new version preserving previous learned_state but updating provenance/performance
    # Policy: PERFORMANCE_ONLY still creates a version
    learned_state = result.learned_state
    learned_schema = result.learned_state_schema
    # If updater says not changed, keep previous state's schema/state? But result still carries same state per our football updater (always changed). For generic case where state_changed false, we could keep previous state to avoid drift, but we use result's state which should equal prev's state when not changed.
    # So we just use result's state.

    metadata = dict(getattr(result, "metadata", {}) or {})
    # Enrich provenance
    provenance_extra = dict(getattr(result, "provenance", {}) or {})
    # Core will add previous linkage automatically; we add trigger info via metadata/provenance extra stored in experience metadata

    # Combine update_summary into metadata
    if getattr(result, "update_summary", None):
        metadata["update_summary"] = result.update_summary[:500]

    # Provenance extra: trigger ids + experience lineage (explicit basis distinction)
    provenance_extra.update({
        "trigger_prediction_id": prediction_id,
        "trigger_resolution_id": res_id,
        "trigger_outcome": resolution.get("outcome"),
        "trigger_experience_id": trigger_exp_id,
        "trigger_experience_version": trigger_exp_version,
        "trigger_experience_hash": trigger_exp_hash,
        "trigger_is_latest": trigger_is_latest,
        "prediction_basis_experience_id": trigger_exp_id,
        "prediction_basis_version": trigger_exp_version,
        "update_basis_experience_id": prev.get("experience_id"),
        "update_basis_version": prev.get("state_version"),
        "previous_experience_id": prev.get("experience_id"),
        "previous_state_version": prev.get("state_version"),
        "causal_key": causal_key,
        "update_event_id": update_event_id,
        "updater": f"{predictor_id}:{predictor_version}",
        "update_order_semantics": order_semantics,
    })

    try:
        new_exp = store.experience_create(
            world_id=world_id,
            predictor_id=predictor_id,
            predictor_version=predictor_version,
            predictor_type=prev.get("predictor_type") or str(getattr(updater.describe(), "predictor_type", "unknown")),
            learned_state_schema=learned_schema,
            learned_state=learned_state,
            observations_used=observations_used,
            source_prediction_ids=new_pred_ids,
            source_outcome_ids=new_out_ids,
            metadata={**metadata, **provenance_extra},
            created_by="experience-runtime",
        )
    except Exception as exc:
        # Handle UNIQUE race: another worker already created the version for this prediction
        # If unique constraint on (world,predictor,version,state_version) fails, treat as already applied if latest already reflects this prediction
        err_msg = _sanitize_error(exc)
        if "UNIQUE" in err_msg or "unique" in err_msg.lower():
            # Check if latest already has this prediction in its sources
            latest = store.experience_latest(world_id, predictor_id, predictor_version)
            if latest and prediction_id in (latest.get("source_prediction_ids") or []):
                return store.experience_update_mark(update_event_id, status="applied", last_error=None, applied_experience_id=latest["experience_id"], applied_state_version=latest["state_version"], increment_attempt=False)  # type: ignore
        return store.experience_update_mark(update_event_id, status="failed", last_error=err_msg)  # type: ignore

    if not new_exp:
        return store.experience_update_mark(update_event_id, status="failed", last_error="experience_create returned None")  # type: ignore

    return store.experience_update_mark(
        update_event_id,
        status="applied",
        last_error=None,
        applied_experience_id=new_exp["experience_id"],
        applied_state_version=new_exp["state_version"],
        increment_attempt=True,
    )  # type: ignore


def process_pending_updates(
    store: MemoryStore,
    registry: ExperienceUpdaterRegistry,
    *,
    limit: int = 20,
    world_id: str | None = None,
) -> dict[str, Any]:
    """Process pending/failed update events, bounded. Causal reorder events are not auto-retried."""
    safe_limit = max(1, min(int(limit), 100))
    # Fetch pending + failed (retryable) events — causal_reorder_required is not auto-retried in v0.1
    pending = store.experience_update_list(world_id=world_id, status="pending", limit=safe_limit)
    failed = store.experience_update_list(world_id=world_id, status="failed", limit=safe_limit)
    # Combine, then sort by causal_key deterministically (not thread scheduling)
    events = (pending + failed)[:safe_limit]
    # Deterministic causal ordering: effective_at/resolved_at + prediction_id tie-breaker
    events = sorted(events, key=lambda e: (e.get("causal_key") or "", int(e.get("prediction_id", 0))))
    summary = {"examined": len(events), "applied": 0, "failed": 0, "no_updater": 0, "missing_experience": 0, "integrity_failed": 0, "causal_reorder_required": 0, "items": []}
    for ev in events:
        upd_id = ev["update_event_id"]
        result = process_experience_update_event(store, registry, upd_id)
        status = result.get("status") if result else "failed"
        if status == "applied":
            summary["applied"] += 1
        elif status == "failed":
            summary["failed"] += 1
        elif status == "no_updater":
            summary["no_updater"] += 1
        elif status == "missing_experience":
            summary["missing_experience"] += 1
        elif status == "integrity_failed":
            summary["integrity_failed"] += 1
        elif status == "causal_reorder_required":
            summary["causal_reorder_required"] += 1
        else:
            summary["failed"] += 1
        summary["items"].append({"update_event_id": upd_id, "prediction_id": ev["prediction_id"], "status": status, "causal_key": ev.get("causal_key")})
    return summary


def enqueue_and_process_for_resolution(
    store: MemoryStore,
    registry: ExperienceUpdaterRegistry,
    prediction_id: int,
) -> dict[str, Any]:
    """Enqueue idempotently and attempt to process a single resolution's update."""
    # Ensure prediction has resolution
    from contextlib import closing
    with closing(store._connect()) as conn:  # type: ignore
        res = conn.execute("SELECT id FROM prediction_resolutions WHERE prediction_id=?", (prediction_id,)).fetchone()
        if not res:
            raise ValueError(f"no resolution for prediction {prediction_id}")
    event = store.experience_update_enqueue(prediction_id=prediction_id)
    # If already applied etc, just return
    if event.get("status") == "applied":
        return event
    # Attempt process
    return process_experience_update_event(store, registry, event["update_event_id"])
