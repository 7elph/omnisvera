"""ExperienceUpdater contract and registry — universal, domain-agnostic."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ExperienceUpdateResult:
    """Result of an updater's processing of a prediction+resolution.

    Core treats learned_state as opaque.
    """
    learned_state_schema: str
    learned_state: Any
    observations_used_delta: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    update_summary: str | None = None
    state_changed: bool = True


@runtime_checkable
class ExperienceUpdater(Protocol):
    """Domain-specific updater for a predictor's learned state."""

    def describe(self) -> dict[str, Any]:
        """Return identity: predictor_id, predictor_version, predictor_type, description, update_order_semantics."""
        ...

    def update(
        self,
        *,
        previous_experience: dict[str, Any] | None,
        prediction: dict[str, Any],
        resolution: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> ExperienceUpdateResult:
        """Compute new learned_state from previous experience + outcome."""
        ...


class ExperienceUpdaterRegistry:
    """Simple registry — no hard-coded if predictor_id branches in runtime."""

    def __init__(self) -> None:
        self._updaters: dict[tuple[str, str], ExperienceUpdater] = {}

    def register(self, updater: ExperienceUpdater) -> dict[str, Any]:
        desc = updater.describe()
        pid = str(desc.get("predictor_id", "")).strip()
        pver = str(desc.get("predictor_version", "")).strip()
        if not pid or not pver:
            raise ValueError("updater must describe predictor_id and predictor_version")
        key = (pid, pver)
        if key in self._updaters:
            raise ValueError(f"updater already registered: {pid} {pver}")
        self._updaters[key] = updater
        return desc

    def get(self, predictor_id: str, predictor_version: str) -> ExperienceUpdater | None:
        return self._updaters.get((predictor_id, predictor_version))

    def has(self, predictor_id: str, predictor_version: str) -> bool:
        return (predictor_id, predictor_version) in self._updaters

    def list(self) -> list[dict[str, Any]]:
        return [u.describe() for u in self._updaters.values()]
