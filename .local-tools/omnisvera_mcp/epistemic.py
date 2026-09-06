"""Epistemic Loop v0.1 — predictions, resolutions, calibration.

Philosophy:
    Memory is not truth.  Every memory has source, date, and confidence.
    A prediction is not a prophecy.  Every prediction has probability,
    horizon, and a resolution rule.
    Error is not failure.  It is calibration data.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .core.context import CallContext
from .memory.store import MemoryStore, stable_json


def _require(arguments: dict, key: str) -> str:
    value = str(arguments.get(key, "")).strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def create_snapshot(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Create a model_snapshot memory item — an immutable photograph of
    what the system knew at a specific moment."""

    domain = _require(arguments, "domain")
    subject = _require(arguments, "subject")
    state = arguments.get("state")
    if not isinstance(state, dict):
        raise ValueError("state must be a JSON object")
    sources_raw = arguments.get("sources")
    sources = []
    if isinstance(sources_raw, list):
        for s in sources_raw:
            if isinstance(s, dict) and "source_type" in s and "source_ref" in s:
                sources.append(s)

    item_id = store.add_memory(
        namespace="omnisvera",
        item_type="model_snapshot",
        title=f"{domain} — {subject}",
        content=json.dumps(state, ensure_ascii=False, sort_keys=True),
        status="immutable",
        confidence=1.0,
        owner="omnisvera",
        classification="internal",
        metadata={"domain": domain, "subject": subject},
        sources=sources,
    )
    return json.dumps(
        {"snapshot_id": item_id, "domain": domain, "subject": subject},
        ensure_ascii=False,
    )


def create_prediction(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Create a prediction — a formal, frozen statement about the future."""

    domain = _require(arguments, "domain")
    snapshot_id = _require(arguments, "snapshot_id")
    claim = _require(arguments, "claim")
    horizon = _require(arguments, "horizon")

    probability_raw = arguments.get("probability")
    if probability_raw is None:
        raise ValueError("probability is required")
    probability = float(probability_raw)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between 0.0 and 1.0")

    resolution_rule = arguments.get("resolution_rule")
    if not isinstance(resolution_rule, dict):
        raise ValueError("resolution_rule must be a JSON object")

    evidence_mode_raw = arguments.get("evidence_mode", "prospective")
    evidence_mode = str(evidence_mode_raw).strip() if evidence_mode_raw else "prospective"
    if evidence_mode not in ("prospective", "retrospective"):
        raise ValueError("evidence_mode must be 'prospective' or 'retrospective'")

    predictor_id_raw = arguments.get("predictor_id")
    predictor_id = str(predictor_id_raw).strip() if predictor_id_raw else None
    predictor_version_raw = arguments.get("predictor_version")
    predictor_version = str(predictor_version_raw).strip() if predictor_version_raw else None
    exp_id_raw = arguments.get("experience_id")
    exp_id = str(exp_id_raw).strip() if exp_id_raw else None
    exp_ver_raw = arguments.get("experience_state_version")
    exp_ver = int(exp_ver_raw) if exp_ver_raw is not None and str(exp_ver_raw).strip() != "" else None
    exp_hash_raw = arguments.get("experience_state_hash")
    exp_hash = str(exp_hash_raw).strip() if exp_hash_raw else None

    prediction_id = store.create_prediction(
        domain=domain,
        snapshot_memory_id=snapshot_id,
        claim=claim,
        probability=probability,
        horizon=horizon,
        resolution_rule=resolution_rule,
        evidence_mode=evidence_mode,
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        world_id=arguments.get("world_id"),
        experience_id=exp_id,
        experience_state_version=exp_ver,
        experience_state_hash=exp_hash,
    )
    return json.dumps(
        {"prediction_id": prediction_id, "status": "open", "evidence_mode": evidence_mode},
        ensure_ascii=False,
    )


def list_predictions(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """List predictions, optionally filtered by domain and status."""

    domain_raw = arguments.get("domain")
    domain = str(domain_raw).strip() if domain_raw else None
    status_raw = arguments.get("status")
    status = str(status_raw).strip() if status_raw else None
    limit = int(arguments.get("limit", 20))

    predictions = store.list_predictions(domain=domain, status=status, limit=limit)
    return json.dumps(predictions, ensure_ascii=False, indent=2)


def get_prediction(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Get a single prediction with its resolution if resolved."""

    prediction_id = int(_require(arguments, "prediction_id"))
    prediction = store.get_prediction(prediction_id)
    if prediction is None:
        raise ValueError(f"prediction not found: {prediction_id}")
    return json.dumps(prediction, ensure_ascii=False, indent=2)


def resolve_prediction(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Resolve a prediction — atomic: insert resolution + update status."""

    prediction_id = int(_require(arguments, "prediction_id"))
    outcome = int(arguments.get("outcome", -1))
    if outcome not in (0, 1):
        raise ValueError("outcome must be 0 (did not occur) or 1 (occurred)")

    observed_value_raw = arguments.get("observed_value")
    observed_value = float(observed_value_raw) if observed_value_raw is not None else None

    sources_raw = arguments.get("sources")
    sources = list(sources_raw) if isinstance(sources_raw, list) else None

    notes = arguments.get("notes")
    notes_str = str(notes).strip() if notes else None

    result = store.resolve_prediction(
        prediction_id,
        observed_value=observed_value,
        outcome=outcome,
        sources=sources,
        notes=notes_str,
    )
    # Durable experience update (exactly-once, retryable) — never undoes resolution
    try:
        from .experience.runtime import enqueue_and_process_for_resolution
        from .experience.updater import ExperienceUpdaterRegistry
        from .experience.football_elo import FootballEloUpdater

        _reg = ExperienceUpdaterRegistry()
        try:
            _reg.register(FootballEloUpdater())
        except ValueError:
            pass
        # Expose hook for tests to inject custom registry via store attribute (optional)
        reg = getattr(store, "_experience_updater_registry", None) or _reg
        enqueue_and_process_for_resolution(store, reg, prediction_id)
    except Exception:
        # Never fail the resolution; ledger will capture failure for retry
        pass
    return json.dumps(result, ensure_ascii=False, indent=2)


def calibration_summary(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Return calibration stats filtered by evidence_mode."""

    domain_raw = arguments.get("domain")
    domain = str(domain_raw).strip() if domain_raw else None

    evidence_mode_raw = arguments.get("evidence_mode", "prospective")
    evidence_mode = str(evidence_mode_raw).strip() if evidence_mode_raw else "prospective"

    summary = store.calibration_summary(domain=domain, evidence_mode=evidence_mode)
    return json.dumps(summary, ensure_ascii=False, indent=2)


def model_companion_session(
    _store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Observe the current Companion and return a structured
    CompanionSessionModelV1. Does NOT create memory_item or prediction."""

    from .adapters.companion import CompanionAdapter
    from .companion_session import build_companion_session_model

    # Reconstruct adapter from arguments (passed by server.py)
    root = arguments.get("_root")
    if root is None:
        raise ValueError("_root is required (internal)")

    from pathlib import Path
    adapter = CompanionAdapter(root=Path(root))
    model = build_companion_session_model(adapter)
    return json.dumps(model.as_dict(), ensure_ascii=False, indent=2)


def model_companion_session_at(
    _store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Reconstruct a historical CompanionSessionModelV1 for a specific
    session, limited to information knowable at a cutoff point.
    Does NOT create memory_item or prediction."""

    from .adapters.companion import CompanionAdapter
    from .companion_session import build_companion_session_model_at

    root = arguments.get("_root")
    if root is None:
        raise ValueError("_root is required (internal)")

    session_id_raw = arguments.get("session_id")
    if session_id_raw is None:
        raise ValueError("session_id is required")
    session_id = int(session_id_raw)

    cutoff_scene_id_raw = arguments.get("cutoff_scene_id")
    cutoff_scene_id = int(cutoff_scene_id_raw) if cutoff_scene_id_raw is not None else None

    cutoff_timestamp = arguments.get("cutoff_timestamp")
    if cutoff_timestamp and not isinstance(cutoff_timestamp, str):
        cutoff_timestamp = str(cutoff_timestamp)

    cutoff_ordinal_raw = arguments.get("cutoff_ordinal")
    cutoff_ordinal = int(cutoff_ordinal_raw) if cutoff_ordinal_raw is not None else None

    from pathlib import Path
    adapter = CompanionAdapter(root=Path(root))
    historical = build_companion_session_model_at(
        adapter, session_id,
        cutoff_scene_id=cutoff_scene_id,
        cutoff_timestamp=cutoff_timestamp,
        cutoff_ordinal=cutoff_ordinal,
    )
    return json.dumps(historical.as_dict(), ensure_ascii=False, indent=2)


def get_session_timeline(
    _store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Build an evidence timeline for a historical session.
    Returns ordered events, source classifications, and limitations.
    Does NOT persist anything."""

    from .adapters.companion import CompanionAdapter
    from .timeline import build_session_timeline

    session_id_raw = arguments.get("session_id")
    if session_id_raw is None:
        raise ValueError("session_id is required")
    session_id = int(session_id_raw)

    root = arguments.get("_root")
    if root is None:
        raise ValueError("_root is required (internal)")

    from pathlib import Path
    root_path = Path(root)

    # Resolve transcript path
    transcript_path = root_path / ".assistant-runtime" / "campaign-sources" / f"session-{session_id:03d}-transcript.txt"
    if not transcript_path.exists():
        transcript_path = None

    # Resolve session records path
    records_path = root_path / ".assistant-runtime" / "campaign-sources" / "session-records.json"
    if not records_path.exists():
        records_path = None

    timeline = build_session_timeline(
        session_id=session_id,
        transcript_path=transcript_path,
        session_records_path=records_path,
        scene_events=None,  # would need adapter for live data
    )

    return json.dumps(timeline.as_dict(), ensure_ascii=False, indent=2)


def snapshot_from_observation(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Create a model_snapshot from a WorldObservation.

    Accepts a WorldObservation dict (as returned by world.observe) and
    creates an immutable snapshot memory item. The Core does NOT interpret
    the state — it only wraps it with provenance.
    """
    observation = arguments.get("observation")
    if not isinstance(observation, dict):
        raise ValueError("observation must be a WorldObservation dict")

    world_id = str(observation.get("world_id", "")).strip()
    if not world_id:
        raise ValueError("observation.world_id is required")

    schema = str(observation.get("schema", "")).strip()
    state = observation.get("state")
    if not isinstance(state, dict):
        raise ValueError("observation.state must be a dict")
    sources = observation.get("sources", [])
    observed_at = str(observation.get("observed_at", "")).strip()

    metadata = {
        "world_id": world_id,
        "schema": schema,
        "observation_observed_at": observed_at,
        "provenance": observation.get("provenance", {}),
    }

    item_id = store.create_snapshot_memory(
        domain=f"world.{world_id}",
        subject=f"{schema} @ {observed_at}" if observed_at else schema,
        state=state,
        sources=[{
            "source_type": "world_observation",
            "source_ref": f"{world_id}:{schema}",
            "source_timestamp": observed_at or None,
            "relation": "supports",
        }] if not sources else sources,
        metadata=metadata,
    )
    return json.dumps(
        {"snapshot_id": item_id, "world_id": world_id, "schema": schema},
        ensure_ascii=False,
    )


def snapshot_from_model(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Create a model_snapshot from a WorldModel dict.

    Accepts a WorldModel dict (as returned by world.model) and creates an
    immutable snapshot memory item. Preserves model_id, builder info,
    evidence refs, assumptions, and limitations.
    """
    model = arguments.get("model")
    if not isinstance(model, dict):
        raise ValueError("model must be a WorldModel dict")

    world_id = str(model.get("world_id", "")).strip()
    if not world_id:
        raise ValueError("model.world_id is required")

    model_id = str(model.get("model_id", "")).strip()
    builder_id = str(model.get("builder_id", "")).strip()
    builder_version = str(model.get("builder_version", "")).strip()
    schema = str(model.get("schema", "")).strip()
    state = model.get("state")
    if not isinstance(state, dict):
        raise ValueError("model.state must be a dict")

    metadata = {
        "world_id": world_id,
        "model_id": model_id,
        "builder_id": builder_id,
        "builder_version": builder_version,
        "schema": schema,
        "created_at": model.get("created_at", ""),
        "signal_refs": model.get("signal_refs", []),
        "pattern_refs": model.get("pattern_refs", []),
        "assumptions": model.get("assumptions", []),
        "limitations": model.get("limitations", []),
        "provenance": model.get("provenance", {}),
    }

    sources = [{
        "source_type": "world_model",
        "source_ref": f"{world_id}:{builder_id}:{model_id}",
        "source_timestamp": model.get("created_at") or None,
        "relation": "supports",
    }]

    item_id = store.create_snapshot_memory(
        domain=f"world.{world_id}",
        subject=f"{builder_id}@{builder_version} @ {model.get('created_at', '')}" if model.get("created_at") else builder_id,
        state=state,
        sources=sources,
        metadata=metadata,
    )
    return json.dumps(
        {"snapshot_id": item_id, "world_id": world_id, "model_id": model_id, "builder_id": builder_id},
        ensure_ascii=False,
    )


def backtest_prediction(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Execute a complete backtest: create snapshot + prediction (retrospective)
    + resolve in a single atomic operation. Does NOT generate predictions
    via LLM — the claim, probability, and outcome must be provided explicitly.

    Two modes:
      - snapshot_id provided: use existing snapshot
      - inline: provide domain, subject, snapshot_state, (optional) snapshot_sources
        → auto-create snapshot before prediction
    """

    domain = _require(arguments, "domain")
    claim = _require(arguments, "claim")
    horizon = _require(arguments, "horizon")

    probability_raw = arguments.get("probability")
    if probability_raw is None:
        raise ValueError("probability is required")
    probability = float(probability_raw)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between 0.0 and 1.0")

    resolution_rule = arguments.get("resolution_rule")
    if not isinstance(resolution_rule, dict):
        raise ValueError("resolution_rule must be a JSON object")

    outcome_raw = arguments.get("outcome")
    if outcome_raw is None:
        raise ValueError("outcome is required for backtest")
    outcome = int(outcome_raw)
    if outcome not in (0, 1):
        raise ValueError("outcome must be 0 (did not occur) or 1 (occurred)")

    observed_value_raw = arguments.get("observed_value")
    observed_value = float(observed_value_raw) if observed_value_raw is not None else None

    sources_raw = arguments.get("sources")
    sources = list(sources_raw) if isinstance(sources_raw, list) else None

    notes = arguments.get("notes")
    notes_str = str(notes).strip() if notes else None

    predictor_id_raw = arguments.get("predictor_id")
    predictor_id = str(predictor_id_raw).strip() if predictor_id_raw else None
    predictor_version_raw = arguments.get("predictor_version")
    predictor_version = str(predictor_version_raw).strip() if predictor_version_raw else None

    # Resolve snapshot_id: either provided or inline
    snapshot_id = arguments.get("snapshot_id")
    if snapshot_id:
        snapshot_id = str(snapshot_id).strip()
    else:
        # Inline snapshot creation
        subject = _require(arguments, "subject")
        snapshot_state = arguments.get("snapshot_state")
        if not isinstance(snapshot_state, dict):
            raise ValueError("snapshot_state must be a JSON object when snapshot_id is omitted")
        snapshot_sources_raw = arguments.get("snapshot_sources")
        snapshot_sources = list(snapshot_sources_raw) if isinstance(snapshot_sources_raw, list) else None

        # Build provenance metadata for the snapshot
        snapshot_metadata: dict[str, Any] = {
            "reconstruction_mode": "backtest_inline",
        }
        session_id_raw = arguments.get("session_id")
        if session_id_raw is not None:
            snapshot_metadata["session_id"] = int(session_id_raw)
        cutoff_ordinal_raw = arguments.get("cutoff_ordinal")
        if cutoff_ordinal_raw is not None:
            snapshot_metadata["cutoff_ordinal"] = int(cutoff_ordinal_raw)
        cutoff_scene_id_raw = arguments.get("cutoff_scene_id")
        if cutoff_scene_id_raw is not None:
            snapshot_metadata["cutoff_scene_id"] = int(cutoff_scene_id_raw)
        excluded_scenes_raw = arguments.get("excluded_scenes")
        if isinstance(excluded_scenes_raw, list):
            snapshot_metadata["excluded_scenes"] = excluded_scenes_raw
        posthoc_excluded_raw = arguments.get("posthoc_excluded")
        if isinstance(posthoc_excluded_raw, list):
            snapshot_metadata["posthoc_excluded"] = posthoc_excluded_raw

        snapshot_id = store.create_snapshot_memory(
            domain=domain,
            subject=subject,
            state=snapshot_state,
            sources=snapshot_sources,
            metadata=snapshot_metadata,
        )

    # Create prediction (retrospective)
    prediction_id = store.create_prediction(
        domain=domain,
        snapshot_memory_id=snapshot_id,
        claim=claim,
        probability=probability,
        horizon=horizon,
        resolution_rule=resolution_rule,
        evidence_mode="retrospective",
        predictor_id=predictor_id,
        predictor_version=predictor_version,
    )

    # Resolve immediately
    result = store.resolve_prediction(
        prediction_id,
        observed_value=observed_value,
        outcome=outcome,
        sources=sources,
        notes=notes_str,
    )
    try:
        from .experience.runtime import enqueue_and_process_for_resolution
        from .experience.updater import ExperienceUpdaterRegistry
        from .experience.football_elo import FootballEloUpdater

        _reg = ExperienceUpdaterRegistry()
        try:
            _reg.register(FootballEloUpdater())
        except ValueError:
            pass
        reg = getattr(store, "_experience_updater_registry", None) or _reg
        enqueue_and_process_for_resolution(store, reg, prediction_id)
    except Exception:
        pass

    return json.dumps({
        "backtest": True,
        "prediction_id": prediction_id,
        "snapshot_id": snapshot_id,
        **result,
    }, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
#  Prediction Candidate — validate and commit
# ---------------------------------------------------------------------------

def validate_candidate(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Validate a PredictionCandidate without creating a prediction.

    Checks structure, probability range, snapshot existence and integrity.
    Returns {"valid": bool, "errors": [...], "warnings": [...]}.
    """
    candidate = arguments.get("candidate")
    if not isinstance(candidate, dict):
        return json.dumps({"valid": False, "errors": ["candidate must be a dict"], "warnings": []}, ensure_ascii=False)

    errors: list[str] = []
    warnings: list[str] = []

    # Required fields
    claim = str(candidate.get("claim", "")).strip()
    if not claim:
        errors.append("claim is required and must be non-empty")

    prob_raw = candidate.get("probability")
    if prob_raw is None:
        errors.append("probability is required")
    else:
        try:
            prob = float(prob_raw)
            if not 0.0 <= prob <= 1.0:
                errors.append("probability must be between 0.0 and 1.0")
        except (TypeError, ValueError):
            errors.append("probability must be a number")

    horizon = str(candidate.get("horizon", "")).strip()
    if not horizon:
        errors.append("horizon is required")

    resolution_rule = candidate.get("resolution_rule")
    if not isinstance(resolution_rule, dict) or not resolution_rule:
        errors.append("resolution_rule is required and must be a non-empty dict")

    predictor_id = str(candidate.get("predictor_id", "")).strip()
    if not predictor_id:
        errors.append("predictor_id is required")

    predictor_version = str(candidate.get("predictor_version", "")).strip()
    if not predictor_version:
        errors.append("predictor_version is required")

    # Snapshot validation
    snapshot_id = str(candidate.get("model_snapshot_id", "")).strip()
    if not snapshot_id:
        errors.append("model_snapshot_id is required")
    else:
        with store._connect() as conn:
            snap = conn.execute(
                "SELECT id, content FROM memory_items WHERE id=?", (snapshot_id,),
            ).fetchone()
            if not snap:
                errors.append(f"snapshot not found: {snapshot_id}")
            else:
                # Verify integrity
                current_hash = hashlib.sha256(snap["content"].encode("utf-8")).hexdigest()
                stored = conn.execute(
                    "SELECT snapshot_hash FROM predictions WHERE snapshot_memory_id=? LIMIT 1",
                    (snapshot_id,),
                ).fetchone()
                # If snapshot is used in existing predictions, verify hash matches
                if stored and stored["snapshot_hash"] != current_hash:
                    warnings.append("snapshot content has changed since last prediction")

    # Experience validation (optional)
    exp_id = str(candidate.get("experience_id", "")).strip() or None
    exp_version_raw = candidate.get("experience_state_version")
    exp_version = int(exp_version_raw) if exp_version_raw is not None and str(exp_version_raw).strip() != "" else None
    exp_hash = str(candidate.get("experience_state_hash", "")).strip() or None
    experience_info: dict[str, Any] = {"referenced": bool(exp_id or exp_version is not None or exp_hash)}
    has_experience_ref = bool(exp_id or exp_version is not None or exp_hash)
    if has_experience_ref:
        # All three should be present for valid reference
        if not exp_id:
            errors.append("experience_id is required when experience is referenced")
        if exp_version is None:
            errors.append("experience_state_version is required when experience is referenced")
        if not exp_hash:
            errors.append("experience_state_hash is required when experience is referenced")
        if exp_id and exp_version is not None and exp_hash:
            exp = store.experience_get(exp_id)
            if not exp:
                errors.append(f"experience not found: {exp_id}")
            else:
                # integrity
                if not exp.get("integrity_ok"):
                    errors.append(f"experience integrity failed: {exp_id}")
                # world match (candidate world_id or domain vs experience world_id)
                cand_world = str(candidate.get("world_id", "")).strip() or str(candidate.get("domain", "")).strip()
                exp_world = str(exp.get("world_id", "")).strip()
                world_match = (cand_world == exp_world) if cand_world and exp_world else False
                if cand_world and exp_world and cand_world != exp_world:
                    errors.append(f"experience world mismatch: candidate {cand_world} vs experience {exp_world}")
                # predictor match
                if exp.get("predictor_id") != predictor_id:
                    errors.append(f"experience predictor_id mismatch: candidate {predictor_id} vs experience {exp.get('predictor_id')}")
                if exp.get("predictor_version") != predictor_version:
                    errors.append(f"experience predictor_version mismatch: candidate {predictor_version} vs experience {exp.get('predictor_version')}")
                if exp.get("state_version") != exp_version:
                    errors.append(f"experience state_version mismatch: candidate {exp_version} vs experience {exp.get('state_version')}")
                if exp.get("learned_state_hash") != exp_hash:
                    errors.append(f"experience hash mismatch: candidate {exp_hash[:8]} vs experience {exp.get('learned_state_hash','')[:8]}")
                # is_latest
                latest = store.experience_latest(exp.get("world_id"), exp.get("predictor_id"), exp.get("predictor_version"))
                is_latest = bool(latest and latest.get("experience_id") == exp_id)
                experience_info.update({
                    "experience_id": exp_id,
                    "state_version": exp_version,
                    "integrity_ok": bool(exp.get("integrity_ok")),
                    "identity_match": exp.get("predictor_id") == predictor_id and exp.get("predictor_version") == predictor_version,
                    "world_match": world_match,
                    "is_latest": is_latest,
                })
                if not is_latest:
                    warnings.append(f"experience is not latest (referenced v{exp_version}, latest v{latest.get('state_version') if latest else '?'})")
            if not experience_info.get("experience_id"):
                experience_info.update({"experience_id": exp_id, "state_version": exp_version, "integrity_ok": False, "is_latest": False})
    else:
        # No experience reference — check if predictor is stateful (has existing experience)
        cand_world = str(candidate.get("world_id", "")).strip() or str(candidate.get("domain", "")).strip()
        if predictor_id and predictor_version and cand_world:
            try:
                latest_existing = store.experience_latest(cand_world, predictor_id, predictor_version)
                if latest_existing:
                    # Stateful predictor without reference — reject per spec section 3
                    errors.append(f"experience required for stateful predictor {predictor_id}:{predictor_version} (latest v{latest_existing.get('state_version')})")
                    experience_info.update({"referenced": False, "reason": "stateful predictor requires experience reference"})
                else:
                    experience_info.update({"referenced": False, "is_latest": None})
            except Exception:
                experience_info.update({"referenced": False})
        else:
            experience_info.update({"referenced": False})

    # Warnings for missing optional fields
    if not candidate.get("world_id"):
        warnings.append("world_id not provided")
    if not candidate.get("signals_used"):
        warnings.append("signals_used not provided — provenance will be incomplete")
    if not candidate.get("patterns_used"):
        warnings.append("patterns_used not provided — provenance will be incomplete")

    return json.dumps({
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "experience": experience_info,
    }, ensure_ascii=False, indent=2)


def commit_candidate(
    store: MemoryStore,
    _context: CallContext,
    arguments: dict,
) -> str:
    """Validate and commit a PredictionCandidate as an official prediction.

    Flow: validate → identity binding → idempotency check → create prediction.
    Enforces:
      - predictor identity must match caller's authorized identity
      - candidate_hash for idempotency (retry → already_committed)
    """
    candidate = arguments.get("candidate")
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dict")

    # Validate first
    validation = json.loads(validate_candidate(store, _context, {"candidate": candidate}))
    if not validation["valid"]:
        raise ValueError(f"candidate invalid: {'; '.join(validation['errors'])}")

    # Extract fields
    world_id = str(candidate.get("world_id", "")).strip() or None
    domain = str(candidate.get("domain", "")).strip()
    subject_ref = str(candidate.get("subject_ref", "")).strip() or None
    claim = str(candidate.get("claim", "")).strip()
    probability = float(candidate.get("probability", 0))
    horizon = str(candidate.get("horizon", "")).strip()
    resolution_rule = candidate.get("resolution_rule", {})
    model_snapshot_id = str(candidate.get("model_snapshot_id", "")).strip()
    model_id = str(candidate.get("model_id", "")).strip() or None
    predictor_id = str(candidate.get("predictor_id", "")).strip()
    predictor_version = str(candidate.get("predictor_version", "")).strip()
    predictor_type = str(candidate.get("predictor_type", "")).strip() or None
    signals_used = candidate.get("signals_used", [])
    patterns_used = candidate.get("patterns_used", [])
    reasoning_summary = str(candidate.get("reasoning_summary", "")).strip() or None
    experience_id = str(candidate.get("experience_id", "")).strip() or None
    exp_ver_raw = candidate.get("experience_state_version")
    experience_state_version = int(exp_ver_raw) if exp_ver_raw is not None and str(exp_ver_raw).strip() != "" else None
    experience_state_hash = str(candidate.get("experience_state_hash", "")).strip() or None

    # --- Identity binding ---
    # For remote callers: predictor_id must match caller's authorized identity
    caller_actor = _context.actor
    caller_scopes = _context.scopes
    # Wildcard scope (local trusted) bypasses identity binding
    if "*" not in caller_scopes:
        # Remote caller: predictor_id must be derivable from actor
        # Policy: predictor_id must equal actor, or actor must have explicit override
        authorized_predictor = _resolve_authorized_predictor(caller_actor, _context)
        if authorized_predictor and predictor_id != authorized_predictor:
            raise ValueError(
                f"predictor identity not authorized for caller: "
                f"caller={caller_actor}, predictor_id={predictor_id}, "
                f"authorized={authorized_predictor}"
            )

    # --- Compute candidate_hash for idempotency ---
    candidate_hash = _compute_candidate_hash(
        world_id=world_id,
        domain=domain,
        subject_ref=subject_ref,
        claim=claim,
        probability=probability,
        horizon=horizon,
        resolution_rule=resolution_rule,
        model_snapshot_id=model_snapshot_id,
        model_id=model_id,
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        predictor_type=predictor_type,
        signals_used=signals_used,
        patterns_used=patterns_used,
        experience_id=experience_id,
        experience_state_version=experience_state_version,
        experience_state_hash=experience_state_hash,
    )

    # --- Idempotency check ---
    existing = store.find_prediction_by_hash(candidate_hash)
    if existing is not None:
        return json.dumps({
            "status": "already_committed",
            "prediction_id": existing,
            "predictor_id": predictor_id,
            "model_snapshot_id": model_snapshot_id,
        }, ensure_ascii=False, indent=2)

    prediction_id = store.create_prediction(
        domain=domain,
        snapshot_memory_id=model_snapshot_id,
        claim=claim,
        probability=probability,
        horizon=horizon,
        resolution_rule=resolution_rule,
        evidence_mode="prospective",
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        world_id=world_id,
        subject_ref=subject_ref,
        model_id=model_id,
        predictor_type=predictor_type,
        signals_used=signals_used,
        patterns_used=patterns_used,
        reasoning_summary=reasoning_summary,
        candidate_hash=candidate_hash,
        experience_id=experience_id,
        experience_state_version=experience_state_version,
        experience_state_hash=experience_state_hash,
    )

    return json.dumps({
        "status": "created",
        "prediction_id": prediction_id,
        "predictor_id": predictor_id,
        "model_snapshot_id": model_snapshot_id,
        "candidate_hash": candidate_hash,
        "warnings": validation.get("warnings", []),
    }, ensure_ascii=False, indent=2)


def _resolve_authorized_predictor(actor: str, context: CallContext) -> str | None:
    """Resolve the authorized predictor_id for a given actor.

    Generic mechanism: actor identity maps to allowed predictor_id.
    No hardcoded AI-specific logic. Configuration-driven.
    """
    # Default policy: actor must match predictor_id
    # Future: externalize to config/policy file
    return actor


def _compute_candidate_hash(
    *,
    world_id: str | None,
    domain: str,
    subject_ref: str | None,
    claim: str,
    probability: float,
    horizon: str,
    resolution_rule: dict,
    model_snapshot_id: str,
    model_id: str | None,
    predictor_id: str,
    predictor_version: str,
    predictor_type: str | None,
    signals_used: list,
    patterns_used: list,
    experience_id: str | None = None,
    experience_state_version: int | None = None,
    experience_state_hash: str | None = None,
) -> str:
    """Compute deterministic SHA-256 hash of epistemically immutable candidate fields.

    Fields included: world_id, domain, subject_ref, claim, probability,
    horizon, resolution_rule, model_snapshot_id, model_id, predictor_id,
    predictor_version, predictor_type, signals_used, patterns_used,
    experience_id, experience_state_version, experience_state_hash.

    reasoning_summary is intentionally excluded — it is metadata, not identity.
    """
    payload = stable_json({
        "world_id": world_id,
        "domain": domain,
        "subject_ref": subject_ref,
        "claim": claim,
        "probability": probability,
        "horizon": horizon,
        "resolution_rule": resolution_rule,
        "model_snapshot_id": model_snapshot_id,
        "model_id": model_id,
        "predictor_id": predictor_id,
        "predictor_version": predictor_version,
        "predictor_type": predictor_type,
        "signals_used": signals_used,
        "patterns_used": patterns_used,
        "experience_id": experience_id,
        "experience_state_version": experience_state_version,
        "experience_state_hash": experience_state_hash,
    })
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
#  Resolve Due Predictions — orchestrator
# ---------------------------------------------------------------------------

def resolve_due_predictions(
    store: MemoryStore,
    context: CallContext,
    arguments: dict,
) -> str:
    """Resolve open predictions whose horizon has passed.

    Orchestrator: consults world adapter for evidence, then resolves,
    voids, or re-schedules. Uses resolve_prediction as the final
    atomic operation.

    Returns summary: {examined, resolved, awaiting_evidence, voided, failed, items}
    """
    now_raw = arguments.get("now")
    now = str(now_raw).strip() if now_raw else None
    domain_raw = arguments.get("domain")
    domain = str(domain_raw).strip() if domain_raw else None
    limit = int(arguments.get("limit", 50))
    dry_run = bool(arguments.get("dry_run", False))

    # Get due predictions
    due = store.get_due_predictions(now=now, domain=domain, limit=limit)

    summary = {
        "examined": len(due),
        "resolved": 0,
        "awaiting_evidence": 0,
        "voided": 0,
        "failed": 0,
        "items": [],
    }

    for pred in due:
        pred_id = pred["id"]
        resolution_rule = pred.get("resolution_rule", {})
        world_id = resolution_rule.get("world_id") or pred.get("world_id")
        entity_ref = resolution_rule.get("entity_ref") or pred.get("subject_ref")
        resolver_id = resolution_rule.get("resolver_id")

        item = {
            "prediction_id": pred_id,
            "domain": pred.get("domain"),
            "world_id": world_id,
            "entity_ref": entity_ref,
            "resolver_id": resolver_id,
            "horizon": pred.get("horizon"),
            "status": "pending",
        }

        # Check if resolver is available
        if not resolver_id:
            # No structured resolver — cannot auto-resolve
            item["status"] = "awaiting_evidence"
            item["reason"] = "no resolver_id in resolution_rule"
            summary["awaiting_evidence"] += 1
            summary["items"].append(item)
            continue

        # Future: consult world adapter based on resolver_id
        # For now, if resolver_id exists but we can't determine outcome,
        # mark as awaiting_evidence
        # Real implementation would:
        # 1. Find the world adapter for world_id
        # 2. Call adapter.resolve(resolver_id, entity_ref)
        # 3. Get outcome: resolved (0/1), void (cancelled), or not_ready

        if dry_run:
            item["status"] = "would_resolve"
            summary["items"].append(item)
            continue

        # Test hook: allow deterministic outcome via resolution_rule.test_outcome
        test_outcome = resolution_rule.get("test_outcome")
        if isinstance(test_outcome, int) and test_outcome in (0, 1):
            try:
                store.resolve_prediction(pred_id, outcome=test_outcome)
                # experience update (same runtime as manual resolve)
                try:
                    from .experience.runtime import enqueue_and_process_for_resolution
                    from .experience.updater import ExperienceUpdaterRegistry
                    from .experience.football_elo import FootballEloUpdater

                    _reg = ExperienceUpdaterRegistry()
                    try:
                        _reg.register(FootballEloUpdater())
                    except ValueError:
                        pass
                    reg = getattr(store, "_experience_updater_registry", None) or _reg
                    enqueue_and_process_for_resolution(store, reg, pred_id)
                except Exception:
                    pass
                item["status"] = "resolved"
                item["outcome"] = test_outcome
                summary["resolved"] += 1
                summary["items"].append(item)
                continue
            except Exception as e:
                item["status"] = "failed"
                item["reason"] = str(e)
                summary["failed"] += 1
                summary["items"].append(item)
                continue

        # Default: cannot determine outcome yet
        item["status"] = "awaiting_evidence"
        item["reason"] = "world adapter resolution not yet implemented"
        summary["awaiting_evidence"] += 1
        summary["items"].append(item)

    return json.dumps(summary, ensure_ascii=False, indent=2)
