"""Omnisvera Capability Manifest v0.1

Generates a structured capability manifest from the actual system state.
Any AI connecting to the MCP can call system.manifest to discover what
the system can do without needing a pre-written prompt.

The manifest is derived from:
  - registered worlds and their capabilities
  - registered model builders
  - registered tools and their access modes
  - epistemic loop capabilities
  - signal analysis capabilities
  - predictor type support
"""
from __future__ import annotations

from typing import Any


MANIFEST_VERSION = "0.1"


def generate_manifest(
    *,
    worlds: list[dict[str, Any]],
    model_builders: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    memory_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a capability manifest from system state.

    Args:
        worlds: list of world descriptors (from WorldRegistry.list())
        model_builders: list of builder descriptions (from WorldModelRegistry.list())
        tools: list of tool info dicts [{name, access_mode, resource, permissions}]
        memory_stats: optional memory store stats

    Returns:
        Structured capability manifest dict.
    """
    # -- Worlds --
    world_entries = []
    for w in worlds:
        wid = w.get("world_id", "")
        caps = w.get("capabilities", [])
        world_entries.append({
            "world_id": wid,
            "world_type": w.get("world_type", ""),
            "name": w.get("name", ""),
            "adapter_id": w.get("adapter_id", ""),
            "capabilities": caps,
            "schemas": w.get("schemas", []),
        })

    # -- Epistemic capabilities --
    epistemic_tools = [t for t in tools if t.get("name", "").startswith("epistemic.")]
    epistemic_names = {t["name"] for t in epistemic_tools}

    epistemic = {
        "snapshot_from_observation": "epistemic.snapshot_from_observation" in epistemic_names,
        "snapshot_from_model": "epistemic.snapshot_from_model" in epistemic_names,
        "prediction": "epistemic.commit_candidate" in epistemic_names,
        "validation": "epistemic.validate_candidate" in epistemic_names,
        "resolution": any("resolve" in t.get("name", "") for t in tools),
        "calibration": any("calibration" in t.get("name", "") for t in tools),
        "backtest": any("backtest" in t.get("name", "") for t in tools),
    }

    # -- Signal capabilities --
    signal_tools = [t for t in tools if t.get("name", "").startswith("world.signal") or t.get("name") == "world.capture_signals"]
    signal_names = {t["name"] for t in signal_tools}

    signals = {
        "capture": "world.capture_signals" in signal_names,
        "history": "world.signal_history" in signal_names,
        "changes": "world.signal_changes" in signal_names,
        "patterns": "world.signal_patterns" in signal_names,
        "pattern_types": ["trend", "anomaly"],
    }

    # -- Experience capabilities --
    experience_tools = [t for t in tools if t.get("name", "").startswith("experience.")]
    experience_names = {t["name"] for t in experience_tools}
    experience = {
        "available": bool(experience_tools),
        "create": "experience.create" in experience_names,
        "get": "experience.get" in experience_names,
        "latest": "experience.latest" in experience_names,
        "history": "experience.history" in experience_names,
        "persistence": "predictor_experiences (append-only, versioned, hash-verified)",
    }

    # -- Model capabilities --
    model = {
        "builders": [
            {
                "builder_id": b.get("builder_id", ""),
                "builder_version": b.get("builder_version", ""),
                "name": b.get("name", ""),
            }
            for b in model_builders
        ],
        "tools": {
            "build_model": any(t.get("name") == "world.model" for t in tools),
            "snapshot_from_model": epistemic.get("snapshot_from_model", False),
        },
    }

    # -- Prediction capabilities --
    prediction = {
        "candidate_schema": {
            "required": ["claim", "probability", "horizon", "resolution_rule", "snapshot_id", "predictor_id", "predictor_version"],
            "optional": ["world_id", "domain", "subject_ref", "model_id", "predictor_type", "signals_used", "patterns_used", "reasoning_summary"],
        },
        "predictor_types": ["ai", "deterministic", "statistical", "human", "external"],
        "workflow": [
            "world.model() → WorldModel",
            "epistemic.snapshot_from_model() → immutable snapshot",
            "epistemic.validate_candidate() → validation result",
            "epistemic.commit_candidate() → official Prediction",
            "resolution + Brier score",
        ],
    }

    # -- Memory capabilities --
    memory = {
        "read": any(t.get("name", "").startswith("memory.") for t in tools),
        "search": any("search" in t.get("name", "") for t in tools),
        "types": ["model_snapshot", "evidence", "context", "interaction"],
    }
    if memory_stats:
        memory["stats"] = memory_stats

    # -- Tool catalog --
    tool_catalog = []
    for t in tools:
        tool_catalog.append({
            "name": t.get("name", ""),
            "access": t.get("access_mode", ""),
            "resource": t.get("resource", ""),
        })

    # -- Permissions summary --
    read_tools = [t["name"] for t in tools if t.get("access_mode") == "read"]
    write_tools = [t["name"] for t in tools if t.get("access_mode") == "write"]

    permissions = {
        "remote_bridge": {
            "read": sorted(read_tools),
            "write": sorted(write_tools),
        },
    }

    # -- Architecture --
    architecture = {
        "chain": [
            "World",
            "Observation",
            "Signal",
            "History",
            "Change",
            "Pattern",
            "WorldModel",
            "Snapshot",
            "PredictionCandidate",
            "Commit",
            "Resolution",
            "Score",
        ],
        "principles": [
            "Core does not interpret domain semantics",
            "All worlds treated identically",
            "Predictions carry full provenance",
            "Models are reproducible from evidence",
            "Any AI can be a predictor",
        ],
    }

    return {
        "manifest_version": MANIFEST_VERSION,
        "system": "omnisvera-mcp",
        "worlds": world_entries,
        "epistemic": epistemic,
        "signals": signals,
        "models": model,
        "experience": experience,
        "prediction": prediction,
        "memory": memory,
        "tools": tool_catalog,
        "permissions": permissions,
        "architecture": architecture,
    }
