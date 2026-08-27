from __future__ import annotations

import json
from typing import Any

from ..adapters.companion import CompanionAdapter
from ..adapters.git import GitAdapter
from ..adapters.vault import VaultAdapter
from ..memory.store import MemoryStore
from .health import HealthService


class HandoffService:
    """Generates current handoff from live sources; legacy handoff is reference only."""

    def __init__(self, vault: VaultAdapter, git: GitAdapter, companion: CompanionAdapter,
                 memory: MemoryStore, health: HealthService) -> None:
        self.vault = vault
        self.git = git
        self.companion = companion
        self.memory = memory
        self.health = health

    def snapshot(self) -> dict[str, Any]:
        health = self.health.collect()
        app = self.companion.get_app_state()
        dashboard = self.companion.get_dashboard()
        companion_state = {
            "app_state": self._summarize_observation(app.as_dict()),
            "dashboard": self._summarize_observation(dashboard.as_dict()),
        }
        stored_companion_state = {
            section: {key: value for key, value in data.items() if key != "observed_at"}
            for section, data in companion_state.items()
        }
        self.memory.record_project_state(
            "companion", stored_companion_state, source="companion.api", confidence=1.0 if app.status == "healthy" else 0.4,
            freshness=app.freshness, observed_at=app.observed_at,
        )
        legacy_path = self.vault.root / "Workflow" / "ASSISTANT_HANDOFF.md"
        legacy_observed = None
        if legacy_path.exists():
            legacy_observed = legacy_path.stat().st_mtime_ns
        return {
            "generated_at": health["observed_at"],
            "git": {"value": {"branch": self.git.branch(), "head": self.git.head(), "working_tree": self.git.working_tree_status()}, "source": "git", "observed_at": health["observed_at"], "confidence": 1.0, "freshness": "fresh", "limitations": None},
            "vault": {"value": {"documents": health["vault"]["documents"], "legacy_handoff_mtime_ns": legacy_observed}, "source": "vault", "observed_at": health["observed_at"], "confidence": 1.0, "freshness": "fresh", "limitations": "Legacy handoff is reference, not current truth."},
            "companion": {"value": companion_state, "source": "companion.api", "observed_at": app.observed_at, "confidence": 1.0 if app.status == "healthy" else 0.4, "freshness": app.freshness, "limitations": app.limitation or dashboard.limitation},
            "memory": {"value": self.memory.stats()["counts"], "source": "sqlite", "observed_at": health["observed_at"], "confidence": 1.0, "freshness": "fresh", "limitations": None},
            "health": health,
        }

    @staticmethod
    def _summarize_observation(observation: dict[str, Any]) -> dict[str, Any]:
        value = observation.get("value")
        summary: Any = value
        if isinstance(value, dict):
            summary = {}
            for key, item in value.items():
                if isinstance(item, list):
                    summary[f"{key}_count"] = len(item)
                elif isinstance(item, dict):
                    summary[key] = {
                        child: child_value
                        for child, child_value in item.items()
                        if child in {"id", "title", "status", "map_id", "table_mode", "visibility", "updated_at"}
                    }
                elif key in {"id", "title", "status", "map_id", "map_title", "table_mode", "updated_at"}:
                    summary[key] = item
        return {
            "source": observation.get("source"),
            "status": observation.get("status"),
            "freshness": observation.get("freshness"),
            "observed_at": observation.get("observed_at"),
            "summary": summary,
            "limitation": observation.get("limitation"),
        }

    def render(self) -> str:
        snapshot = self.snapshot()
        lines = ["# Omnisvera — handoff dinâmico", f"Generated: {snapshot['generated_at']}"]
        for name in ("git", "vault", "companion", "memory"):
            section = snapshot[name]
            lines.extend([
                "", f"## {name.upper()}",
                f"Source: {section['source']}",
                f"Observed at: {section['observed_at']}",
                f"Confidence: {section['confidence']}",
                f"Freshness: {section['freshness']}",
                f"Limitations: {section['limitations'] or 'none'}",
                json.dumps(section["value"], ensure_ascii=False, sort_keys=True),
            ])
        return "\n".join(lines)
