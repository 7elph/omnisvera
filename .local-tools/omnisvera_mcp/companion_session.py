"""
Companion Session Model v0.1

Produces a structured, observable snapshot of the companion.session domain
using exclusively real data already available from the Companion backend.

This module does NOT persist anything. It observes, normalizes, and returns.

v0.1 — current state model (live)
v0.1 — historical reconstruction model (backtest)
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from .adapters.companion import CompanionAdapter


@dataclass(frozen=True, slots=True)
class CompanionSessionModelV1:
    schema: str = "companion.session.v1"
    observed_at: str = ""

    # session — from /gm/sessions, filtered to active
    session_id: int | None = None
    session_status: str | None = None
    session_title: str | None = None
    session_number: int | None = None
    campaign_id: str | None = None

    # participants — from active scene's scene_participants
    participants: list[dict[str, Any]] = field(default_factory=list)

    # location — from active scene
    location: str | None = None
    location_source: str | None = None

    # active threads — from active scene's actions with status != resolved
    active_threads: list[dict[str, Any]] = field(default_factory=list)

    # scenes — active scene summary
    scenes: list[dict[str, Any]] = field(default_factory=list)

    # operational — health + workspace state
    operational: dict[str, Any] = field(default_factory=dict)

    # provenance — data sources consulted
    provenance: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _extract_active_session(sessions_data: Any) -> dict[str, Any] | None:
    """Extract the active session from the /gm/sessions response.
    Returns None if no session has status 'active'."""
    if not isinstance(sessions_data, list):
        return None
    for s in sessions_data:
        if isinstance(s, dict) and s.get("status") == "active":
            return s
    return None


def _extract_active_scene(scene_data: Any) -> dict[str, Any] | None:
    """Extract the active scene from the /scenes/active response."""
    if isinstance(scene_data, dict) and scene_data.get("status") == "active":
        return scene_data
    if scene_data is None:
        return None
    return None


def _normalize_participants(scene: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract participants from the active scene."""
    raw = scene.get("participants", [])
    if not isinstance(raw, list):
        return []
    result = []
    for p in raw:
        if not isinstance(p, dict):
            continue
        entry: dict[str, Any] = {
            "participant_type": p.get("participant_type"),
            "public_label": p.get("public_label"),
            "public_status": p.get("public_status"),
        }
        if p.get("character_id"):
            entry["character_id"] = p["character_id"]
        if p.get("npc_name"):
            entry["npc_name"] = p["npc_name"]
        result.append(entry)
    return result


def _normalize_active_threads(scene: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract active (non-resolved) actions as threads."""
    raw = scene.get("actions", [])
    if not isinstance(raw, list):
        return []
    result = []
    for a in raw:
        if not isinstance(a, dict):
            continue
        status = a.get("status", "")
        if status in ("resolved", "cancelled", "rejected"):
            continue
        result.append({
            "action_type": a.get("action_type"),
            "description": a.get("description"),
            "status": status,
            "actor_role": a.get("actor_role"),
        })
    return result


def _normalize_scenes(scene: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a single-element list for the active scene."""
    if not scene:
        return []
    return [{
        "id": scene.get("id"),
        "title": scene.get("title"),
        "location_name": scene.get("location_name"),
        "status": scene.get("status"),
        "objective": scene.get("objective"),
    }]


def _build_operational(
    health: Any,
    dashboard_status: str,
    dashboard_limitation: str | None,
) -> dict[str, Any]:
    """Build the operational section from health and dashboard status."""
    result: dict[str, Any] = {
        "companion_dashboard_status": dashboard_status,
    }
    if dashboard_limitation:
        result["companion_dashboard_limitation"] = dashboard_limitation

    if isinstance(health, dict):
        result["backend"] = health.get("backend")
        result["ollama_accessible"] = health.get("ollama_accessible")
        result["model_mode"] = health.get("model_mode")
        result["production_approved"] = health.get("production_approved")
        result["access_mode"] = health.get("access_mode")
    elif hasattr(health, "value") and isinstance(health.value, dict):
        result["backend"] = health.value.get("backend")
        result["ollama_accessible"] = health.value.get("ollama_accessible")
        result["model_mode"] = health.value.get("model_mode")
        result["production_approved"] = health.value.get("production_approved")
        result["access_mode"] = health.value.get("access_mode")

    return result


def _build_provenance(
    health_obs: Any,
    dashboard_obs: Any,
    sources_used: list[str],
) -> dict[str, Any]:
    """Build provenance metadata."""
    return {
        "domain": "companion.session",
        "schema_version": "companion.session.v1",
        "sources_consulted": sources_used,
        "health_status": getattr(health_obs, "status", "unknown"),
        "health_freshness": getattr(health_obs, "freshness", "unknown"),
        "dashboard_status": getattr(dashboard_obs, "status", "unknown"),
        "dashboard_freshness": getattr(dashboard_obs, "freshness", "unknown"),
    }


def build_companion_session_model(adapter: CompanionAdapter) -> CompanionSessionModelV1:
    """
    Query the Companion via the existing adapter and produce
    a CompanionSessionModelV1. Does NOT persist anything.

    Returns the model even if the Companion is offline/degraded —
    provenance will reflect the actual status.
    """
    observed_at = datetime.now(timezone.utc).isoformat()
    sources_used: list[str] = []

    # 1. Health — always consulted
    health_obs = adapter.get_health()
    sources_used.append("/health")

    # 2. Dashboard — sessions + active scene
    dashboard_obs = adapter.get_dashboard()
    sources_used.append("/gm/sessions")
    sources_used.append("/scenes/active")

    # 3. Extract raw data
    sessions_raw = None
    scene_raw = None
    dashboard_status = dashboard_obs.status
    dashboard_limitation = dashboard_obs.limitation

    if isinstance(dashboard_obs.value, dict):
        sessions_raw = dashboard_obs.value.get("sessions")
        scene_raw = dashboard_obs.value.get("active_scene")

    # 4. Normalize
    active_session = _extract_active_session(sessions_raw)
    active_scene = _extract_active_scene(scene_raw)

    # 5. Build model
    session_id = active_session.get("id") if active_session else None
    session_status = active_session.get("status") if active_session else None

    location = active_scene.get("location_name") if active_scene else None
    location_source = active_scene.get("location_source") if active_scene else None

    participants = _normalize_participants(active_scene) if active_scene else []
    active_threads = _normalize_active_threads(active_scene) if active_scene else []
    scenes = _normalize_scenes(active_scene)
    operational = _build_operational(health_obs.value, dashboard_status, dashboard_limitation)
    provenance = _build_provenance(health_obs, dashboard_obs, sources_used)

    return CompanionSessionModelV1(
        observed_at=observed_at,
        session_id=session_id,
        session_status=session_status,
        session_title=active_session.get("title") if active_session else None,
        session_number=active_session.get("session_number") if active_session else None,
        campaign_id=active_session.get("campaign_id") if active_session else None,
        participants=participants,
        location=location,
        location_source=location_source,
        active_threads=active_threads,
        scenes=scenes,
        operational=operational,
        provenance=provenance,
    )


# ---------------------------------------------------------------------------
#  Historical / Backtest support
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class BacktestInfo:
    """Metadata for historical reconstruction."""
    target_session_id: int
    cutoff_scene_id: int | None = None
    cutoff_timestamp: str | None = None
    cutoff_ordinal: int | None = None
    ordering_basis: str = "scene_id"  # "scene_id" | "ordinal" | "timestamp"
    excluded_scenes: list[int] = field(default_factory=list)
    excluded_actions: list[int] = field(default_factory=list)
    excluded_events: list[int] = field(default_factory=list)
    excluded_by_rule: list[str] = field(default_factory=list)
    posthoc_sources_excluded: list[str] = field(default_factory=list)
    data_available: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HistoricalSessionModel:
    """A CompanionSessionModelV1 with backtest metadata."""
    model: CompanionSessionModelV1
    backtest: BacktestInfo

    def as_dict(self) -> dict[str, Any]:
        d = self.model.as_dict()
        d["backtest"] = asdict(self.backtest)
        return d


def _narrative_participants(session: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract participants from session narrative_json."""
    narrative = session.get("narrative", {})
    if not isinstance(narrative, dict):
        return []
    raw = narrative.get("participants", [])
    if not isinstance(raw, list):
        return []
    result = []
    for p in raw:
        if isinstance(p, str):
            result.append({"public_label": p, "participant_type": "character"})
        elif isinstance(p, dict):
            entry: dict[str, Any] = {"public_label": p.get("name", p.get("label", ""))}
            if p.get("role"):
                entry["participant_type"] = p["role"]
            result.append(entry)
    return result


def _narrative_locations(session: dict[str, Any]) -> list[str]:
    """Extract locations from session narrative_json."""
    narrative = session.get("narrative", {})
    if not isinstance(narrative, dict):
        return []
    raw = narrative.get("locations", [])
    if not isinstance(raw, list):
        return []
    return [loc for loc in raw if isinstance(loc, str)]


def _narrative_missions(session: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract missions from session narrative_json."""
    narrative = session.get("narrative", {})
    if not isinstance(narrative, dict):
        return []
    raw = narrative.get("missions", [])
    if not isinstance(raw, list):
        return []
    result = []
    for m in raw:
        if isinstance(m, dict):
            result.append({
                "title": m.get("title", ""),
                "status": m.get("status", "unknown"),
            })
    return result


def _narrative_threads(session: dict[str, Any]) -> list[str]:
    """Extract open threads from session narrative_json."""
    narrative = session.get("narrative", {})
    if not isinstance(narrative, dict):
        return []
    raw = narrative.get("open_threads", [])
    if not isinstance(raw, list):
        return []
    return [t for t in raw if isinstance(t, str)]


def _filter_scenes_by_cutoff(
    scenes: list[dict[str, Any]],
    cutoff_scene_id: int | None,
    cutoff_timestamp: str | None,
) -> tuple[list[dict[str, Any]], list[int], list[str]]:
    """Filter scenes to only those knowable at the cutoff point.
    Returns (included_scenes, excluded_ids, exclusion_rules)."""
    if not scenes:
        return [], [], []

    included = []
    excluded_ids = []
    rules = []

    for s in scenes:
        scene_id = s.get("id", 0)
        created_at = s.get("created_at", "")

        exclude = False
        reason = ""

        if cutoff_scene_id is not None and scene_id > cutoff_scene_id:
            exclude = True
            reason = f"scene_id {scene_id} > cutoff {cutoff_scene_id}"

        if cutoff_timestamp and created_at and created_at > cutoff_timestamp:
            exclude = True
            reason = f"created_at {created_at} > cutoff {cutoff_timestamp}"

        if exclude:
            excluded_ids.append(scene_id)
            rules.append(reason)
        else:
            included.append(s)

    return included, excluded_ids, rules


def _filter_actions_by_cutoff(
    actions: list[dict[str, Any]],
    eligible_scene_ids: set[int],
    cutoff_timestamp: str | None,
) -> tuple[list[dict[str, Any]], list[int], list[str]]:
    """Filter actions: must be in eligible scenes and before cutoff."""
    included = []
    excluded_ids = []
    rules = []

    for a in actions:
        scene_id = a.get("scene_id", 0)
        created_at = a.get("created_at", "")
        action_id = a.get("id", 0)

        exclude = False
        reason = ""

        if scene_id not in eligible_scene_ids:
            exclude = True
            reason = f"scene {scene_id} not in eligible set"

        if cutoff_timestamp and created_at and created_at > cutoff_timestamp:
            exclude = True
            reason = f"action created_at {created_at} > cutoff {cutoff_timestamp}"

        if exclude:
            excluded_ids.append(action_id)
            rules.append(reason)
        else:
            included.append(a)

    return included, excluded_ids, rules


def _filter_events_by_cutoff(
    events: list[dict[str, Any]],
    eligible_scene_ids: set[int],
    cutoff_timestamp: str | None,
) -> tuple[list[dict[str, Any]], list[int], list[str]]:
    """Filter events: must be in eligible scenes and before cutoff."""
    included = []
    excluded_ids = []
    rules = []

    for e in events:
        scene_id = e.get("scene_id", 0)
        created_at = e.get("created_at", "")
        event_id = e.get("id", 0)

        exclude = False
        reason = ""

        if scene_id not in eligible_scene_ids:
            exclude = True
            reason = f"scene {scene_id} not in eligible set"

        if cutoff_timestamp and created_at and created_at > cutoff_timestamp:
            exclude = True
            reason = f"event created_at {created_at} > cutoff {cutoff_timestamp}"

        if exclude:
            excluded_ids.append(event_id)
            rules.append(reason)
        else:
            included.append(e)

    return included, excluded_ids, rules


def build_companion_session_model_at(
    adapter: CompanionAdapter,
    session_id: int,
    cutoff_scene_id: int | None = None,
    cutoff_timestamp: str | None = None,
    cutoff_ordinal: int | None = None,
) -> HistoricalSessionModel:
    """
    Reconstruct a CompanionSessionModelV1 for a specific historical session,
    limited to information knowable at the cutoff point.

    Does NOT persist anything.

    Leakage protection:
    - Scenes with id > cutoff_scene_id are excluded
    - Actions/events with created_at > cutoff_timestamp are excluded
    - Session-level summaries written post-session are marked unavailable_for_backtest
    - Narrative data (narrative_json, public_summary, gm_summary) is classified as POSTHOC
      and excluded from predictive state — can only be used as resolution evidence
    - cutoff_ordinal limits to events with ordinal <= cutoff when timeline is available
    """
    observed_at = datetime.now(timezone.utc).isoformat()
    sources_used: list[str] = []

    # 1. Health
    health_obs = adapter.get_health()
    sources_used.append("/health")

    # 2. Fetch all sessions to find the target
    sessions_obs = adapter.list_sessions()
    sources_used.append("/gm/sessions")

    sessions_raw = sessions_obs.value if isinstance(sessions_obs.value, list) else []

    # 3. Find target session
    target_session = None
    for s in sessions_raw:
        if isinstance(s, dict) and s.get("id") == session_id:
            target_session = s
            break

    if target_session is None:
        # Session not found — return empty model with provenance
        return HistoricalSessionModel(
            model=CompanionSessionModelV1(
                observed_at=observed_at,
                session_id=session_id,
                provenance=_build_provenance(health_obs, sessions_obs, sources_used),
            ),
            backtest=BacktestInfo(
                target_session_id=session_id,
                excluded_by_rule=[f"session {session_id} not found"],
                data_available={"session": False},
            ),
        )

    # 4. Fetch scenes for this session's campaign
    campaign_id = target_session.get("campaign_id", "")
    scenes_obs = adapter.list_scenes(campaign_id) if campaign_id else None
    scenes_raw = []
    if scenes_obs and isinstance(scenes_obs.value, list):
        scenes_raw = scenes_obs.value
        sources_used.append(f"/campaigns/{campaign_id}/scenes")

    # 5. Filter scenes by cutoff
    eligible_scenes, excluded_scene_ids, scene_rules = _filter_scenes_by_cutoff(
        scenes_raw, cutoff_scene_id, cutoff_timestamp,
    )

    # 6. Filter actions and events
    eligible_scene_ids = {s.get("id", 0) for s in eligible_scenes}

    all_actions = []
    all_events = []
    for s in eligible_scenes:
        all_actions.extend(s.get("actions", []))
        all_events.extend(s.get("events", []))

    filtered_actions, excluded_action_ids, action_rules = _filter_actions_by_cutoff(
        all_actions, eligible_scene_ids, cutoff_timestamp,
    )
    filtered_events, excluded_event_ids, event_rules = _filter_events_by_cutoff(
        all_events, eligible_scene_ids, cutoff_timestamp,
    )

    # 7. Build model from session-level data
    narrative = target_session.get("narrative", {})
    if isinstance(narrative, str):
        try:
            import json
            narrative = json.loads(narrative)
        except (json.JSONDecodeError, TypeError):
            narrative = {}

    participants_from_narrative = _narrative_participants(target_session)
    locations_from_narrative = _narrative_locations(target_session)

    # Scene-level participants (from eligible scenes)
    scene_participants = []
    for s in eligible_scenes:
        for p in s.get("participants", []):
            if isinstance(p, dict):
                scene_participants.append({
                    "public_label": p.get("public_label"),
                    "participant_type": p.get("participant_type"),
                    "character_id": p.get("character_id"),
                    "npc_name": p.get("npc_name"),
                })

    # Merge: scene participants take precedence over narrative participants
    all_participants = scene_participants if scene_participants else participants_from_narrative

    # Location: first eligible scene's location, or narrative locations
    location = None
    location_source = None
    if eligible_scenes:
        location = eligible_scenes[0].get("location_name")
        location_source = eligible_scenes[0].get("location_source")
    elif locations_from_narrative:
        location = locations_from_narrative[0]
        location_source = "narrative"

    # Active threads from filtered actions
    active_threads = []
    for a in filtered_actions:
        status = a.get("status", "")
        if status not in ("resolved", "cancelled", "rejected"):
            active_threads.append({
                "action_type": a.get("action_type"),
                "description": a.get("description"),
                "status": status,
                "actor_role": a.get("actor_role"),
            })

    # Scenes summary
    scenes_summary = []
    for s in eligible_scenes:
        scenes_summary.append({
            "id": s.get("id"),
            "title": s.get("title"),
            "location_name": s.get("location_name"),
            "status": s.get("status"),
            "objective": s.get("objective"),
        })

    # Operational
    operational = _build_operational(
        health_obs.value, sessions_obs.status, sessions_obs.limitation,
    )

    # Provenance
    provenance = _build_provenance(health_obs, sessions_obs, sources_used)
    provenance["reconstruction_mode"] = "historical"
    provenance["target_session_id"] = session_id
    if cutoff_scene_id is not None:
        provenance["cutoff_scene_id"] = cutoff_scene_id
    if cutoff_timestamp:
        provenance["cutoff_timestamp"] = cutoff_timestamp

    # Data availability
    data_available = {
        "session": True,
        "narrative_posthoc": bool(narrative),
        "public_summary_posthoc": target_session.get("public_summary") is not None,
        "gm_summary_posthoc": target_session.get("gm_summary") is not None,
        "scenes": bool(eligible_scenes),
        "participants": bool(all_participants),
        "actions": bool(filtered_actions),
        "events": bool(filtered_events),
    }

    # Excluded by rule (session-level fields unavailable for backtest)
    excluded_by_rule = list(scene_rules) + list(action_rules) + list(event_rules)

    # Posthoc sources — explicitly excluded from predictive state
    posthoc_sources = []
    if narrative:
        posthoc_sources.append("narrative_json")
        excluded_by_rule.append("narrative_json: posthoc — created after session, use only as resolution evidence")
    if target_session.get("public_summary"):
        posthoc_sources.append("public_summary")
        excluded_by_rule.append("public_summary: posthoc — written after session, use only as resolution evidence")
    if target_session.get("public_chronicle"):
        posthoc_sources.append("public_chronicle")
        excluded_by_rule.append("public_chronicle: posthoc — written after session")
    if target_session.get("gm_summary"):
        posthoc_sources.append("gm_summary")
        excluded_by_rule.append("gm_summary: posthoc — written after session, excluded from backtest")

    if cutoff_ordinal is not None:
        excluded_by_rule.append(f"cutoff_ordinal={cutoff_ordinal}: events with ordinal > {cutoff_ordinal} excluded")

    model = CompanionSessionModelV1(
        observed_at=observed_at,
        session_id=session_id,
        session_status=target_session.get("status"),
        session_title=target_session.get("title"),
        session_number=target_session.get("session_number"),
        campaign_id=campaign_id,
        participants=all_participants,
        location=location,
        location_source=location_source,
        active_threads=active_threads,
        scenes=scenes_summary,
        operational=operational,
        provenance=provenance,
    )

    # Determine ordering basis
    ordering_basis = "scene_id"
    if cutoff_ordinal is not None:
        ordering_basis = "ordinal"
    elif cutoff_timestamp:
        ordering_basis = "timestamp"

    backtest = BacktestInfo(
        target_session_id=session_id,
        cutoff_scene_id=cutoff_scene_id,
        cutoff_timestamp=cutoff_timestamp,
        cutoff_ordinal=cutoff_ordinal,
        ordering_basis=ordering_basis,
        excluded_scenes=excluded_scene_ids,
        excluded_actions=excluded_action_ids,
        excluded_events=excluded_event_ids,
        excluded_by_rule=excluded_by_rule,
        posthoc_sources_excluded=posthoc_sources,
        data_available=data_available,
    )

    return HistoricalSessionModel(model=model, backtest=backtest)
