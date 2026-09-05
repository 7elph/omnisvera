from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .core.context import CallContext
from .core.registry import RegisteredTool, ToolRegistry


ContextFactory = Callable[[], CallContext]
REMOTE_TOOL_NAMES = (
    "system.health",
    "system.manifest",
    "system.bootstrap",
    "get_handoff",
    "get_companion_state",
    "memory.get",
    "memory.list",
    "memory.search",
    "memory.recent",
    "world.list",
    "world.describe",
    "world.observe",
    "world.signals",
    "world.signal_history",
    "world.signal_changes",
    "world.signal_patterns",
    "world.model",
    "world.context",
    "world.capture_signals",
    "experience.get",
    "experience.latest",
    "experience.history",
    "epistemic.validate_candidate",
    "epistemic.commit_candidate",
    "epistemic.create_snapshot",
    "epistemic.snapshot_from_model",
    "epistemic.create_prediction",
    "epistemic.resolve_prediction",
    "epistemic.list_predictions",
    "epistemic.get_prediction",
    "epistemic.calibration_summary",
    "epistemic.resolve_due_predictions",
)
READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
READ_WRITE = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)


@dataclass(frozen=True, slots=True)
class BridgeBindings:
    system_health: Callable[[], str]
    get_handoff: Callable[[], str]
    get_companion_state: Callable[[], str]
    memory_get: Callable[[str], str]
    memory_list: Callable[[str | None, int], str]
    memory_search: Callable[[str, str | None, int], str]
    memory_recent: Callable[[str | None, int], str]
    epistemic_commit_candidate: Callable[[dict], str] | None = None
    world_capture_signals: Callable[[str, list[dict]], str] | None = None
    epistemic_create_snapshot: Callable[[str, str, dict], str] | None = None
    epistemic_snapshot_from_model: Callable[[dict], str] | None = None
    epistemic_create_prediction: Callable[[dict], str] | None = None
    epistemic_list_predictions: Callable[[str | None, str | None, int], str] | None = None
    epistemic_get_prediction: Callable[[int], str] | None = None
    epistemic_resolve_prediction: Callable[[int, int], str] | None = None
    epistemic_calibration_summary: Callable[[str, str | None], str] | None = None
    epistemic_resolve_due_predictions: Callable[[str | None, str | None, int, bool], str] | None = None


def remote_bridge_context() -> CallContext:
    """Identity injected by the HTTP launcher, never supplied by the client."""

    return CallContext(
        actor="mia",
        client="chatgpt-mia-bridge",
        transport="streamable-http",
        scopes=frozenset(
            {"system.health.read", "vault.handoff.read", "companion.read", "memory.read",
             "memory.write",
             "world.read", "world.write", "epistemic.read", "epistemic.write",
             "epistemic.prediction.commit", "experience.read"}
        ),
        request_id=uuid4().hex,
        project_id="omnisvera",
    )


def _register_companion_reader(registry: ToolRegistry) -> None:
    try:
        registry.get("get_companion_state")
        return
    except KeyError:
        pass

    companion = registry.services["companion"]

    def read_companion(
        _context: CallContext,
        _arguments: Mapping[str, Any],
    ) -> str:
        return json.dumps(
            companion.get_dashboard().as_dict(),
            ensure_ascii=False,
            indent=2,
        )

    registry.register(
        RegisteredTool(
            "get_companion_state",
            read_companion,
            "read",
            "projects://companion/current",
            frozenset({"companion.read"}),
        )
    )


def register_remote_bridge_tools(
    mcp: FastMCP,
    registry: ToolRegistry,
    *,
    context_factory: ContextFactory = remote_bridge_context,
) -> BridgeBindings:
    """Expose the bounded remote read/write surface for the MIA bridge."""

    _register_companion_reader(registry)

    @mcp.tool(name="system.health", annotations=READ_ONLY)
    def system_health() -> str:
        """Read current Omnisvera subsystem health and freshness."""

        return registry.invoke("system.health", context_factory(), {})

    @mcp.tool(name="system.manifest", annotations=READ_ONLY)
    def system_manifest() -> str:
        """Discover Omnisvera capabilities: worlds, model builders, tools, memory stats."""

        return registry.invoke("system.manifest", context_factory(), {})

    @mcp.tool(name="system.bootstrap", annotations=READ_ONLY)
    def system_bootstrap() -> str:
        """Universal continuity bootstrap: system identity, capabilities, worlds, state, memories, recent changes."""

        return registry.invoke("system.bootstrap", context_factory(), {})

    @mcp.tool(name="get_handoff", annotations=READ_ONLY)
    def get_handoff() -> str:
        """Read the current dynamic Omnisvera handoff."""

        return registry.invoke("get_handoff", context_factory(), {})

    @mcp.tool(name="get_companion_state", annotations=READ_ONLY)
    def get_companion_state() -> str:
        """Read the current Companion session/dashboard state."""

        return registry.invoke("get_companion_state", context_factory(), {})

    @mcp.tool(name="memory.get", annotations=READ_ONLY)
    def memory_get(memory_id: str) -> str:
        """Read one persistent memory by stable ID, including provenance."""

        return registry.invoke("memory.get", context_factory(), {"memory_id": memory_id})

    @mcp.tool(name="memory.list", annotations=READ_ONLY)
    def memory_list(item_type: str | None = None, limit: int = 20) -> str:
        """List persistent memories, optionally filtered by type."""

        return registry.invoke(
            "memory.list",
            context_factory(),
            {"item_type": item_type, "limit": limit},
        )

    @mcp.tool(name="memory.search", annotations=READ_ONLY)
    def memory_search(query: str, item_type: str | None = None, limit: int = 10) -> str:
        """Lexical search of memory ID/title/content, including provenance.

        Case/accent insensitive; no semantic synonyms. Limit: 1-100.
        """
        return registry.invoke(
            "memory.search", context_factory(),
            {"query": query, "item_type": item_type, "limit": limit},
        )

    @mcp.tool(name="memory.recent", annotations=READ_ONLY)
    def memory_recent(item_type: str | None = None, limit: int = 10) -> str:
        """Read full memories by updated_at descending, then stable ID. Limit: 1-100."""
        return registry.invoke(
            "memory.recent", context_factory(), {"item_type": item_type, "limit": limit},
        )

    # --- World tools (read-only) ---

    @mcp.tool(name="world.list", annotations=READ_ONLY)
    def world_list() -> str:
        """List connected worlds with identity, capabilities and health."""

        return registry.invoke("world.list", context_factory(), {})

    @mcp.tool(name="world.describe", annotations=READ_ONLY)
    def world_describe(world_id: str) -> str:
        """Describe a connected world: identity, capabilities, health."""

        return registry.invoke("world.describe", context_factory(), {"world_id": world_id})

    @mcp.tool(name="world.observe", annotations=READ_ONLY)
    def world_observe(world_id: str, query: dict | None = None) -> str:
        """Observe the current state of a connected world. Returns WorldObservation."""

        args: dict[str, Any] = {"world_id": world_id}
        if query is not None:
            args["query"] = query
        return registry.invoke("world.observe", context_factory(), args)

    @mcp.tool(name="world.signals", annotations=READ_ONLY)
    def world_signals(world_id: str, query: dict | None = None) -> str:
        """Extract structured universal signals from a connected world. Returns WorldSignal[]."""

        args: dict[str, Any] = {"world_id": world_id}
        if query is not None:
            args["query"] = query
        return registry.invoke("world.signals", context_factory(), args)

    @mcp.tool(name="world.signal_history", annotations=READ_ONLY)
    def world_signal_history(
        world_id: str, signal_id: str,
        entity_ref: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 100,
    ) -> str:
        """Query signal observation history for a world. Returns temporally ordered observations."""

        args: dict[str, Any] = {"world_id": world_id, "signal_id": signal_id}
        if entity_ref is not None:
            args["entity_ref"] = entity_ref
        if since is not None:
            args["since"] = since
        if until is not None:
            args["until"] = until
        args["limit"] = limit
        return registry.invoke("world.signal_history", context_factory(), args)

    @mcp.tool(name="world.signal_changes", annotations=READ_ONLY)
    def world_signal_changes(
        world_id: str, signal_id: str,
        entity_ref: str | None = None,
        limit: int = 100,
    ) -> str:
        """Detect changes between consecutive signal observations. Returns list of SignalChange."""

        args: dict[str, Any] = {"world_id": world_id, "signal_id": signal_id}
        if entity_ref is not None:
            args["entity_ref"] = entity_ref
        args["limit"] = limit
        return registry.invoke("world.signal_changes", context_factory(), args)

    @mcp.tool(name="world.signal_patterns", annotations=READ_ONLY)
    def world_signal_patterns(
        world_id: str, signal_id: str,
        entity_ref: str | None = None,
        since: str | None = None,
        until: str | None = None,
        pattern_type: str | None = None,
        limit: int = 100,
    ) -> str:
        """Query signal patterns detected in observation history."""

        args: dict[str, Any] = {"world_id": world_id, "signal_id": signal_id}
        if entity_ref is not None:
            args["entity_ref"] = entity_ref
        if since is not None:
            args["since"] = since
        if until is not None:
            args["until"] = until
        if pattern_type is not None:
            args["pattern_type"] = pattern_type
        args["limit"] = limit
        return registry.invoke("world.signal_patterns", context_factory(), args)

    @mcp.tool(name="world.model", annotations=READ_ONLY)
    def world_model(
        world_id: str,
        builder_id: str = "core.state-vector",
        signal_ids: list[str] | None = None,
        entity_ref: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> str:
        """Build a world model from signals and patterns using a registered builder."""

        args: dict[str, Any] = {"world_id": world_id, "builder_id": builder_id}
        if signal_ids is not None:
            args["signal_ids"] = signal_ids
        if entity_ref is not None:
            args["entity_ref"] = entity_ref
        if since is not None:
            args["since"] = since
        if until is not None:
            args["until"] = until
        return registry.invoke("world.model", context_factory(), args)

    @mcp.tool(name="world.context", annotations=READ_ONLY)
    def world_context(world_id: str, lookback_hours: int = 24) -> str:
        """Aggregated read-only view of a world: current state, recent changes, predictions, outcomes, freshness."""

        return registry.invoke("world.context", context_factory(), {"world_id": world_id, "lookback_hours": lookback_hours})

    @mcp.tool(name="experience.get", annotations=READ_ONLY)
    def experience_get(experience_id: str) -> str:
        """Get predictor experience by experience_id (integrity verified)."""
        return registry.invoke("experience.get", context_factory(), {"experience_id": experience_id})

    @mcp.tool(name="experience.latest", annotations=READ_ONLY)
    def experience_latest(world_id: str, predictor_id: str, predictor_version: str) -> str:
        """Get latest experience version for a predictor/world."""
        return registry.invoke(
            "experience.latest", context_factory(),
            {"world_id": world_id, "predictor_id": predictor_id, "predictor_version": predictor_version},
        )

    @mcp.tool(name="experience.history", annotations=READ_ONLY)
    def experience_history(world_id: str, predictor_id: str, predictor_version: str, limit: int = 20) -> str:
        """Get versioned experience history for a predictor/world."""
        return registry.invoke(
            "experience.history", context_factory(),
            {"world_id": world_id, "predictor_id": predictor_id, "predictor_version": predictor_version, "limit": limit},
        )

    # --- World tools (write) ---

    @mcp.tool(name="world.capture_signals", annotations=READ_WRITE)
    def world_capture_signals(world_id: str, signals: list[dict]) -> str:
        """Capture and persist universal signals from a world observation."""

        return registry.invoke(
            "world.capture_signals", context_factory(),
            {"world_id": world_id, "signals": signals},
        )

    # --- Epistemic tools (read-only + governed write) ---

    @mcp.tool(name="epistemic.validate_candidate", annotations=READ_ONLY)
    def epistemic_validate_candidate(candidate: dict) -> str:
        """Validate an epistemic prediction candidate without committing."""

        return registry.invoke(
            "epistemic.validate_candidate", context_factory(), {"candidate": candidate},
        )

    # --- Governed write: epistemic.commit_candidate ---
    # Requires epistemic.prediction.commit scope (granted in context)
    # Identity binding enforced inside commit_candidate handler
    def _commit_handler(ctx, args):
        from . import epistemic
        return epistemic.commit_candidate(registry.services.get("memory", None), ctx, args)

    commit_candidate_tool = RegisteredTool(
        "epistemic.commit_candidate",
        _commit_handler,
        "write",
        "epistemic://predictions",
        frozenset({"epistemic.prediction.commit"}),
    )
    try:
        registry.register(commit_candidate_tool)
    except ValueError:
        pass  # already registered

    @mcp.tool(name="epistemic.commit_candidate", annotations=READ_WRITE)
    def epistemic_commit_candidate(candidate: dict) -> str:
        """Commit a validated epistemic prediction candidate. Governed write."""

        return registry.invoke(
            "epistemic.commit_candidate", context_factory(), {"candidate": candidate},
        )

    # --- Epistemic tools (write) ---

    @mcp.tool(name="epistemic.create_snapshot", annotations=READ_WRITE)
    def epistemic_create_snapshot(domain: str, subject: str, state: dict, sources: list[dict] | None = None) -> str:
        """Create an immutable model snapshot of system state."""

        args: dict[str, Any] = {"domain": domain, "subject": subject, "state": state}
        if sources is not None:
            args["sources"] = sources
        return registry.invoke("epistemic.create_snapshot", context_factory(), args)

    @mcp.tool(name="epistemic.snapshot_from_model", annotations=READ_WRITE)
    def epistemic_snapshot_from_model(model: dict) -> str:
        """Create an immutable snapshot from a world model dict."""

        return registry.invoke(
            "epistemic.snapshot_from_model", context_factory(), {"model": model},
        )

    @mcp.tool(name="epistemic.create_prediction", annotations=READ_WRITE)
    def epistemic_create_prediction(
        domain: str,
        snapshot_id: str,
        claim: str,
        probability: float,
        horizon: str,
        resolution_rule: dict,
        predictor_id: str = "",
        predictor_version: str = "",
        evidence_mode: str = "prospective",
    ) -> str:
        """Create a formal prediction with all required fields."""

        args: dict[str, Any] = {
            "domain": domain,
            "snapshot_id": snapshot_id,
            "claim": claim,
            "probability": probability,
            "horizon": horizon,
            "resolution_rule": resolution_rule,
            "predictor_id": predictor_id,
            "predictor_version": predictor_version,
            "evidence_mode": evidence_mode,
        }
        return registry.invoke("epistemic.create_prediction", context_factory(), args)

    @mcp.tool(name="epistemic.resolve_prediction", annotations=READ_WRITE)
    def epistemic_resolve_prediction(
        prediction_id: int,
        outcome: int,
        observed_value: float | None = None,
        sources: list[dict] | None = None,
        notes: str = "",
    ) -> str:
        """Resolve a prediction: insert resolution + atomically update status."""

        args: dict[str, Any] = {
            "prediction_id": prediction_id,
            "outcome": outcome,
            "notes": notes,
        }
        if observed_value is not None:
            args["observed_value"] = observed_value
        if sources is not None:
            args["sources"] = sources
        return registry.invoke("epistemic.resolve_prediction", context_factory(), args)

    # --- Epistemic tools (read) ---

    @mcp.tool(name="epistemic.list_predictions", annotations=READ_ONLY)
    def epistemic_list_predictions(
        domain: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> str:
        """List predictions with optional domain/status filters."""

        args: dict[str, Any] = {"limit": limit}
        if domain is not None:
            args["domain"] = domain
        if status is not None:
            args["status"] = status
        return registry.invoke("epistemic.list_predictions", context_factory(), args)

    @mcp.tool(name="epistemic.get_prediction", annotations=READ_ONLY)
    def epistemic_get_prediction(prediction_id: int) -> str:
        """Get a single prediction with its resolution if resolved."""

        return registry.invoke(
            "epistemic.get_prediction", context_factory(), {"prediction_id": prediction_id},
        )

    @mcp.tool(name="epistemic.calibration_summary", annotations=READ_ONLY)
    def epistemic_calibration_summary(
        evidence_mode: str = "all",
        domain: str | None = None,
    ) -> str:
        """Return calibration statistics (count, mean_brier) filtered by evidence_mode."""

        args: dict[str, Any] = {"evidence_mode": evidence_mode}
        if domain is not None:
            args["domain"] = domain
        return registry.invoke("epistemic.calibration_summary", context_factory(), args)

    @mcp.tool(name="epistemic.resolve_due_predictions", annotations=READ_WRITE)
    def epistemic_resolve_due_predictions(
        now: str | None = None,
        domain: str | None = None,
        limit: int = 50,
        dry_run: bool = False,
    ) -> str:
        """Resolve open predictions whose horizon has passed.

        Orchestrator: consults world adapter for evidence, then resolves,
        voids, or re-schedules. Returns summary with counts.
        """

        args: dict[str, Any] = {"limit": limit, "dry_run": dry_run}
        if now is not None:
            args["now"] = now
        if domain is not None:
            args["domain"] = domain
        return registry.invoke("epistemic.resolve_due_predictions", context_factory(), args)

    return BridgeBindings(
        system_health, get_handoff, get_companion_state, memory_get, memory_list,
        memory_search, memory_recent,
        epistemic_commit_candidate=lambda candidate: registry.invoke(
            "epistemic.commit_candidate", context_factory(), {"candidate": candidate}
        ),
        world_capture_signals=lambda world_id, signals: registry.invoke(
            "world.capture_signals", context_factory(), {"world_id": world_id, "signals": signals}
        ),
        epistemic_create_snapshot=lambda domain, subject, state, sources=None: registry.invoke(
            "epistemic.create_snapshot", context_factory(),
            {"domain": domain, "subject": subject, "state": state, "sources": sources},
        ),
        epistemic_snapshot_from_model=lambda model: registry.invoke(
            "epistemic.snapshot_from_model", context_factory(), {"model": model},
        ),
        epistemic_create_prediction=lambda **kwargs: registry.invoke(
            "epistemic.create_prediction", context_factory(), kwargs,
        ),
        epistemic_list_predictions=lambda domain=None, status=None, limit=50: registry.invoke(
            "epistemic.list_predictions", context_factory(),
            {"domain": domain, "status": status, "limit": limit},
        ),
        epistemic_get_prediction=lambda prediction_id: registry.invoke(
            "epistemic.get_prediction", context_factory(), {"prediction_id": prediction_id},
        ),
        epistemic_resolve_prediction=lambda prediction_id, outcome, **kwargs: registry.invoke(
            "epistemic.resolve_prediction", context_factory(),
            {"prediction_id": prediction_id, "outcome": outcome, **kwargs},
        ),
        epistemic_calibration_summary=lambda evidence_mode="all", domain=None: registry.invoke(
            "epistemic.calibration_summary", context_factory(),
            {"evidence_mode": evidence_mode, "domain": domain},
        ),
        epistemic_resolve_due_predictions=lambda now=None, domain=None, limit=50, dry_run=False: registry.invoke(
            "epistemic.resolve_due_predictions", context_factory(),
            {"now": now, "domain": domain, "limit": limit, "dry_run": dry_run},
        ),
    )
