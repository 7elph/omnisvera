"""Universal World Contract v0.3

Defines the minimum interface between Omnisvera MCP and any external world.
The Core does NOT understand domain semantics — it only knows:
  - which world
  - when observed
  - what schema
  - what state
  - from where
  - what signals (v0.2)
  - what model (v0.3)

Companion is one world. Football, economy, politics, cognition, simulations
are all equally valid — the Core treats them identically.

v0.2: WorldSignal — universal signal contract.
v0.3: WorldModel — universal model contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
#  World Descriptor — identity card for a world
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class WorldDescriptor:
    """Immutable identity card for a connected world."""
    world_id: str
    world_type: str
    name: str
    adapter_id: str
    capabilities: list[str] = field(default_factory=list)
    schemas: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
#  World Observation — what the Core receives from a world
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class WorldObservation:
    """A generic observation from any world. The state is domain-specific;
    the envelope is universal."""
    world_id: str
    observed_at: str
    schema: str
    state: dict[str, Any]
    sources: list[dict[str, Any]] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
#  World Signal — universal structured signal from any world
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class WorldSignal:
    """A structured, typed signal extracted from a WorldObservation.

    The Core does NOT understand the semantics of signal_id or value.
    It only knows the envelope: which world, when observed, what type, provenance.

    Signal IDs follow the pattern: {world_id}.{domain}.{name}
    Examples:
      companion.session.status
      companion.session.participant_count
      football.match.status
      football.match.home_score
    """
    signal_id: str
    world_id: str
    schema: str
    name: str
    value: Any
    value_type: str  # "number", "boolean", "string", "categorical", "datetime"
    observed_at: str
    entity_ref: str | None = None  # e.g. "match:TSDB-123456"
    unit: str | None = None
    source: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
#  Signal Pattern — universal pattern detected in signal history
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SignalPattern:
    """A mathematical pattern detected in a signal's history.

    NOT a prediction. NOT an interpretation. Pure math on observed values.

    Pattern types:
      - trend: directional movement in numeric signal
      - anomaly: statistically unusual observation
    """
    world_id: str
    signal_id: str
    entity_ref: str | None
    pattern_type: str  # "trend" | "anomaly"

    window_start: str
    window_end: str
    observation_count: int

    metrics: dict[str, Any]
    confidence: float | None = None

    method: str = ""
    method_version: str = "1.0"

    provenance: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
#  World Adapter Protocol — what every world must implement
# ---------------------------------------------------------------------------

@runtime_checkable
class WorldAdapter(Protocol):
    """Protocol that every world adapter must satisfy.

    Minimal contract:
      - describe(): identity and capabilities
      - health(): current health status
      - observe(): current state observation

    Optional contract (checked at runtime):
      - signals(observation?): extract WorldSignal[] from observation

    Additional methods are domain-specific and NOT required by the Core.
    """

    def describe(self) -> WorldDescriptor:
        """Return the world's identity card."""
        ...

    def health(self) -> dict[str, Any]:
        """Return health status as a dict with at least 'status' key."""
        ...

    def observe(self, query: dict[str, Any] | None = None) -> WorldObservation:
        """Return a current observation of the world's state."""
        ...


# ---------------------------------------------------------------------------
#  World Model — structured representation of a world's state
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class WorldModel:
    """A structured, reproducible model of a world's state built from signals and patterns.

    NOT a prediction. NOT an interpretation. A factual representation of
    what the system believes about the world, with traceable evidence.

    The Core does NOT interpret model contents. Domain semantics belong
    to the builder/world, not to the Core.
    """
    model_id: str
    world_id: str
    schema: str
    subject_ref: str | None

    created_at: str

    state: dict[str, Any]
    relationships: list[dict[str, Any]]

    signal_refs: list[dict[str, Any]]
    pattern_refs: list[dict[str, Any]]

    assumptions: list[str]
    limitations: list[str]

    builder_id: str
    builder_version: str

    provenance: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
#  World Model Builder Protocol — how models are constructed
# ---------------------------------------------------------------------------

@runtime_checkable
class WorldModelBuilder(Protocol):
    """Protocol for building WorldModels from signals and patterns.

    Domain-specific builders interpret signals for their world.
    The Core only requires the builder to produce a WorldModel.
    """

    def describe(self) -> dict[str, Any]:
        """Return builder identity: builder_id, builder_version, description."""
        ...

    def build(
        self,
        *,
        world_id: str,
        signals: list[dict[str, Any]],
        patterns: list[dict[str, Any]],
        query: dict[str, Any] | None = None,
    ) -> WorldModel:
        """Build a WorldModel from signals and patterns."""
        ...


# ---------------------------------------------------------------------------
#  Core State Vector Builder — universal deterministic builder
# ---------------------------------------------------------------------------

class CoreStateVectorBuilder:
    """Universal builder that assembles signals and patterns into a WorldModel.

    Does NOT interpret domain semantics. Only structures evidence into
    a reproducible model with traceable provenance.

    builder_id = "core.state-vector"
    builder_version = "1.0.0"
    """

    BUILDER_ID = "core.state-vector"
    BUILDER_VERSION = "1.0.0"

    def describe(self) -> dict[str, Any]:
        return {
            "builder_id": self.BUILDER_ID,
            "builder_version": self.BUILDER_VERSION,
            "name": "Core State Vector Builder",
            "description": "Universal deterministic builder. Structures signals and patterns into a reproducible model without domain interpretation.",
        }

    def build(
        self,
        *,
        world_id: str,
        signals: list[dict[str, Any]],
        patterns: list[dict[str, Any]],
        query: dict[str, Any] | None = None,
    ) -> WorldModel:
        """Build a WorldModel from signals and patterns.

        Assembles:
          - current_signals: latest value per signal_id (grouped by entity_ref)
          - patterns: pattern summary per signal_id
          - entities: list of distinct entity_refs
        """
        from datetime import datetime, timezone
        created_at = datetime.now(timezone.utc).isoformat()

        # -- current_signals: latest value per (entity_ref, signal_id) --
        current_signals: dict[str, Any] = {}
        entities: set[str | None] = set()
        signal_refs: list[dict[str, Any]] = []

        for sig in signals:
            sid = sig.get("signal_id", "")
            entity = sig.get("entity_ref")
            entities.add(entity)
            key = f"{entity}:{sid}" if entity else sid
            # Keep the latest observation (last in list wins)
            current_signals[key] = sig.get("value")
            signal_refs.append({
                "signal_id": sid,
                "entity_ref": entity,
                "observed_at": sig.get("observed_at", ""),
                "value_type": sig.get("value_type", ""),
            })

        # -- patterns: summary per signal_id --
        patterns_summary: dict[str, Any] = {}
        pattern_refs: list[dict[str, Any]] = []

        for pat in patterns:
            sid = pat.get("signal_id", "")
            ptype = pat.get("pattern_type", "")
            entity = pat.get("entity_ref")
            key = f"{entity}:{sid}" if entity else sid
            if key not in patterns_summary:
                patterns_summary[key] = {}
            metrics = pat.get("metrics", {})
            if ptype == "trend":
                patterns_summary[key]["trend"] = metrics.get("classification", "unknown")
            elif ptype == "anomaly":
                patterns_summary[key]["anomaly"] = metrics.get("anomalous", False)
            pattern_refs.append({
                "signal_id": sid,
                "entity_ref": entity,
                "pattern_type": ptype,
                "method": pat.get("method", ""),
                "method_version": pat.get("method_version", ""),
            })

        # -- assumptions & limitations --
        assumptions: list[str] = []
        limitations: list[str] = []

        if not signals:
            limitations.append("no signals provided")
        if not patterns:
            assumptions.append("no patterns available for these signals")

        numeric_count = sum(1 for s in signals if s.get("value_type") == "number")
        if numeric_count < len(signals):
            limitations.append(f"{len(signals) - numeric_count} non-numeric signals excluded from pattern analysis")

        entity_list = sorted(set(str(e) for e in entities if e is not None))
        if not entity_list:
            entity_list = [s.get("entity_ref") for s in signals[:1] if s.get("entity_ref")]
            if not entity_list:
                entity_list = [None]

        state = {
            "current_signals": current_signals,
            "patterns": patterns_summary,
            "entities": entity_list,
        }

        return WorldModel(
            model_id=f"{world_id}.{self.BUILDER_ID}.{created_at}",
            world_id=world_id,
            schema=f"{world_id}.model.{self.BUILDER_ID}",
            subject_ref=entity_list[0] if len(entity_list) == 1 else None,
            created_at=created_at,
            state=state,
            relationships=[],
            signal_refs=signal_refs,
            pattern_refs=pattern_refs,
            assumptions=assumptions,
            limitations=limitations,
            builder_id=self.BUILDER_ID,
            builder_version=self.BUILDER_VERSION,
            provenance={
                "signal_count": len(signals),
                "pattern_count": len(patterns),
                "entity_count": len(entity_list),
                "builder_id": self.BUILDER_ID,
                "builder_version": self.BUILDER_VERSION,
            },
        )


# ---------------------------------------------------------------------------
#  World Model Registry — manages model builders
# ---------------------------------------------------------------------------

class WorldModelRegistry:
    """Registry of model builders. No auto-discovery, no plugins."""

    def __init__(self) -> None:
        self._builders: dict[str, WorldModelBuilder] = {}

    def register(self, builder: WorldModelBuilder) -> dict[str, Any]:
        """Register a model builder. Returns its description."""
        desc = builder.describe()
        bid = desc.get("builder_id", "")
        if not bid:
            raise ValueError("builder must provide a builder_id")
        if bid in self._builders:
            raise ValueError(f"builder already registered: {bid}")
        self._builders[bid] = builder
        return desc

    def list(self) -> list[dict[str, Any]]:
        """Return descriptions for all registered builders."""
        return [b.describe() for b in self._builders.values()]

    def get(self, builder_id: str) -> WorldModelBuilder:
        """Get a registered builder by ID."""
        if builder_id not in self._builders:
            raise KeyError(f"builder not found: {builder_id}")
        return self._builders[builder_id]

    def has(self, builder_id: str) -> bool:
        """Check if a builder is registered."""
        return builder_id in self._builders


# ---------------------------------------------------------------------------
#  Prediction Candidate — proposed prediction before official commit
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class PredictionCandidate:
    """A proposed prediction from any predictor (AI, algorithm, human, etc.).

    NOT an official prediction. Must be validated and committed explicitly.
    The Core does NOT interpret the claim or reasoning — it only validates
    structure and preserves provenance.

    predictor_type examples: "ai", "deterministic", "statistical", "human", "external"
    """
    world_id: str
    domain: str
    subject_ref: str | None

    claim: str
    probability: float
    horizon: str
    resolution_rule: dict[str, Any]

    model_snapshot_id: str
    model_id: str | None

    predictor_id: str
    predictor_version: str
    predictor_type: str

    signals_used: list[dict[str, Any]]
    patterns_used: list[dict[str, Any]]

    reasoning_summary: str | None = None

    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
#  World Registry — manages connected worlds
# ---------------------------------------------------------------------------

class WorldRegistry:
    """Registry of connected worlds. No auto-discovery, no plugins."""

    def __init__(self) -> None:
        self._adapters: dict[str, WorldAdapter] = {}

    def register(self, adapter: WorldAdapter) -> WorldDescriptor:
        """Register a world adapter. Returns its descriptor."""
        descriptor = adapter.describe()
        if descriptor.world_id in self._adapters:
            raise ValueError(f"world already registered: {descriptor.world_id}")
        self._adapters[descriptor.world_id] = adapter
        return descriptor

    def list(self) -> list[WorldDescriptor]:
        """Return descriptors for all registered worlds."""
        return [a.describe() for a in self._adapters.values()]

    def get(self, world_id: str) -> WorldAdapter:
        """Get a registered world adapter by ID."""
        if world_id not in self._adapters:
            raise KeyError(f"world not found: {world_id}")
        return self._adapters[world_id]

    def has(self, world_id: str) -> bool:
        """Check if a world is registered."""
        return world_id in self._adapters
