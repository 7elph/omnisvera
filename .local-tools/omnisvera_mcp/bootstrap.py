"""Universal Continuity Bootstrap v0.1

A single entry point that gives any new AI a complete picture of the
Omnisvera system: what it can do, where work stands, what changed recently,
and where to look next.

Designed for AI neutrality — no assumptions about the consumer.
Read-only, no writes, no secrets.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


BOOTSTRAP_VERSION = "0.1"


def generate_bootstrap(
    *,
    health: dict[str, Any] | None = None,
    handoff: dict[str, Any] | None = None,
    worlds: list[dict[str, Any]] | None = None,
    project_ids: list[str] | None = None,
    latest_project_states: dict[str, dict[str, Any] | None] | None = None,
    memory_stats: dict[str, Any] | None = None,
    recent_memories: list[dict[str, Any]] | None = None,
    manifest_summary: dict[str, Any] | None = None,
    signal_worlds: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a bootstrap payload from live system state.

    All parameters are optional — the bootstrap degrades gracefully
    when components are unavailable.
    """
    now = datetime.now(timezone.utc).isoformat()

    # -- System section --
    system = {
        "name": "omnisvera-mcp",
        "bootstrap_version": BOOTSTRAP_VERSION,
        "manifest_version": manifest_summary.get("manifest_version", "unknown") if manifest_summary else "unknown",
        "observed_at": now,
    }

    # -- Health section --
    health_section = {}
    if health:
        health_section = {
            "observed_at": health.get("observed_at", ""),
            "subsystems": {},
        }
        for key in ("mcp_core", "vault", "git", "companion", "memory",
                     "lexical_index", "semantic_index"):
            if key in health:
                subsystem = health[key]
                health_section["subsystems"][key] = {
                    "status": subsystem.get("status", "unknown"),
                    "freshness": subsystem.get("freshness", "unknown"),
                }

    # -- Continuity section --
    continuity = {}

    # Handoff
    if handoff:
        continuity["handoff"] = {
            "generated_at": handoff.get("generated_at", ""),
            "sources": list(handoff.keys()),
        }
        # Include companion state summary if available
        companion_data = handoff.get("companion")
        if companion_data and isinstance(companion_data, dict):
            continuity["handoff"]["companion_freshness"] = companion_data.get("freshness", "unknown")

    # Project states
    if latest_project_states:
        continuity["project_states"] = {}
        for pid, state in latest_project_states.items():
            if state:
                continuity["project_states"][pid] = {
                    "observed_at": state.get("observed_at", ""),
                    "source": state.get("source", ""),
                    "confidence": state.get("confidence", 0),
                    "freshness": state.get("freshness", "unknown"),
                }
            else:
                continuity["project_states"][pid] = {"status": "no_state"}

    # Memory summary
    if memory_stats:
        counts = memory_stats.get("counts", {})
        continuity["memory"] = {
            "total_items": counts.get("memory_items", 0),
            "total_sources": counts.get("memory_sources", 0),
            "signal_observations": counts.get("signal_observations", 0),
            "predictions": counts.get("predictions", 0),
            "project_states": counts.get("project_states", 0),
        }

    # Recent memories (compact)
    if recent_memories:
        continuity["recent_memory"] = [
            {
                "id": m.get("id", ""),
                "type": m.get("type", ""),
                "title": m.get("title", ""),
                "status": m.get("status", ""),
                "updated_at": m.get("updated_at", ""),
            }
            for m in recent_memories[:10]
        ]

    # -- Worlds section --
    worlds_section = []
    if worlds:
        for w in worlds:
            worlds_section.append({
                "world_id": w.get("world_id", ""),
                "name": w.get("name", ""),
                "world_type": w.get("world_type", ""),
                "capabilities": w.get("capabilities", []),
            })

    # -- Capabilities section --
    capabilities = {
        "manifest_ref": "system.manifest",
        "bootstrap_ref": "system.bootstrap",
    }
    if manifest_summary:
        capabilities["epistemic_tools"] = manifest_summary.get("epistemic", {})
        capabilities["signal_tools"] = manifest_summary.get("signals", {})
        capabilities["model_builders"] = [
            b.get("builder_id", "")
            for b in manifest_summary.get("models", {}).get("builders", [])
        ]

    # -- Freshness section --
    freshness = {}
    if health:
        for key in ("companion", "vault", "git", "lexical_index", "semantic_index"):
            if key in health:
                freshness[key] = health[key].get("freshness", "unknown")

    # -- Limitations section --
    limitations = []
    if not health:
        limitations.append("health data unavailable")
    if not handoff:
        limitations.append("handoff data unavailable")
    if not worlds:
        limitations.append("no worlds registered")
    if not memory_stats:
        limitations.append("memory stats unavailable")

    # Check for degraded subsystems
    if health:
        for key, subsystem in health.items():
            if isinstance(subsystem, dict) and subsystem.get("status") not in ("healthy", "unknown", None):
                limitations.append(f"subsystem {key} status: {subsystem.get('status')}")

    # -- Recommended next reads --
    recommended = ["system.manifest"]
    if worlds_section:
        recommended.append("world.list")
    if continuity.get("memory", {}).get("total_items", 0) > 0:
        recommended.append("memory.list")
    if signal_worlds:
        for wid in signal_worlds[:3]:
            recommended.append(f"world.observe (world_id={wid})")
    if continuity.get("project_states"):
        for pid in list(continuity["project_states"].keys())[:2]:
            recommended.append(f"project state: {pid}")

    return {
        "bootstrap_version": BOOTSTRAP_VERSION,
        "observed_at": now,
        "system": system,
        "continuity": continuity,
        "worlds": worlds_section,
        "capabilities": capabilities,
        "freshness": freshness,
        "limitations": limitations,
        "recommended_next_reads": recommended,
    }
