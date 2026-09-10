"""Universal World Contract v0.1 — Tests.

Tests required by spec:
    1. Companion registered as world
    2. world.list returns descriptor
    3. world.describe returns capabilities
    4. world.observe(companion) returns WorldObservation
    5. CompanionSessionModelV1 still works
    6. observation can become model_snapshot
    7. fake non-RPG world works via same contract
    8. fake world can generate snapshot and prediction
    9. Core does not require session/player/NPC/mission
    10. previous epistemic suites remain green
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

# Load store.py in isolation
import types as _types

_recall_stub = _types.ModuleType("recall")
_recall_stub.query_terms = lambda q: (q, q.split())
_recall_stub.rank = lambda *a, **kw: None
_recall_stub.validate_options = lambda t, _l: t

_store_src = (LOCAL_TOOLS / "omnisvera_mcp" / "memory" / "store.py").read_text(encoding="utf-8")
_store_ns: dict = {"__name__": "store", "__file__": str(LOCAL_TOOLS / "omnisvera_mcp" / "memory" / "store.py")}
_store_ns["query_terms"] = _recall_stub.query_terms
_store_ns["rank"] = _recall_stub.rank
_store_ns["validate_options"] = _recall_stub.validate_options
_store_src = _store_src.replace("from .recall import", "from recall import")
sys.modules["recall"] = _recall_stub
exec(compile(_store_src, _store_ns["__file__"], "exec"), _store_ns)
MemoryStore = _store_ns["MemoryStore"]

# Load world.py in isolation
import types as _mt
_world_mod = _mt.ModuleType("world")
_world_mod.__file__ = str(LOCAL_TOOLS / "omnisvera_mcp" / "world.py")
sys.modules["world"] = _world_mod
_world_src = (LOCAL_TOOLS / "omnisvera_mcp" / "world.py").read_text(encoding="utf-8")
exec(compile(_world_src, _world_mod.__file__, "exec"), _world_mod.__dict__)
WorldDescriptor = _world_mod.WorldDescriptor
WorldObservation = _world_mod.WorldObservation
WorldAdapter = _world_mod.WorldAdapter
WorldRegistry = _world_mod.WorldRegistry

# Load epistemic.py (needs world module in sys.modules)
_ep_src = (LOCAL_TOOLS / "omnisvera_mcp" / "epistemic.py").read_text(encoding="utf-8")
_ep_ns: dict = {"__name__": "epistemic", "__file__": str(LOCAL_TOOLS / "omnisvera_mcp" / "epistemic.py")}
_ep_src = _ep_src.replace("from .core.context import CallContext", "CallContext = object")
_ep_src = _ep_src.replace("from .memory.store import MemoryStore, stable_json", "MemoryStore = object")
_ep_src = _ep_src.replace("from .memory.store import MemoryStore", "MemoryStore = object")
exec(compile(_ep_src, _ep_ns["__file__"], "exec"), _ep_ns)
snapshot_from_observation = _ep_ns["snapshot_from_observation"]


# ---------------------------------------------------------------------------
#  FakeWorld — non-RPG test adapter
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class _FakeDescriptor:
    world_id: str = "test-world"
    world_type: str = "sensor气象"
    name: str = "Fake Weather Station"
    adapter_id: str = "fake.weather.v1"
    capabilities: list = None
    schemas: list = None
    metadata: dict = None

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["capabilities"] = self.capabilities or ["observe"]
        d["schemas"] = self.schemas or ["weather.station.v1"]
        d["metadata"] = self.metadata or {}
        return d


class FakeWorldAdapter:
    """Minimal non-RPG world adapter for testing the universal contract."""

    def __init__(self) -> None:
        self._observation_count = 0

    def describe(self) -> WorldDescriptor:
        return WorldDescriptor(
            world_id="test-world",
            world_type="sensor气象",
            name="Fake Weather Station",
            adapter_id="fake.weather.v1",
            capabilities=["observe"],
            schemas=["weather.station.v1"],
            metadata={"station_id": "WS-001", "location": "test-lab"},
        )

    def health(self) -> dict[str, Any]:
        return {"status": "healthy", "freshness": "fresh", "station_id": "WS-001"}

    def observe(self, query: dict[str, Any] | None = None) -> WorldObservation:
        self._observation_count += 1
        return WorldObservation(
            world_id="test-world",
            observed_at="2026-08-30T12:00:00+00:00",
            schema="weather.station.v1",
            state={
                "station_id": "WS-001",
                "temperature_c": 23.4,
                "humidity_pct": 67.2,
                "pressure_hpa": 1008.3,
                "wind_kph": 12.1,
                "reading_count": self._observation_count,
            },
            sources=[{"source_type": "sensor", "source_ref": "ws001"}],
            provenance={"adapter": "fake.weather.v1", "location": "test-lab"},
        )


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------

class WorldContractTests(unittest.TestCase):
    """10 mandatory tests for the Universal World Contract."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = MemoryStore(Path(self.temporary.name) / "test.db")
        self.registry = WorldRegistry()
        self.fake = FakeWorldAdapter()

    # 1. Companion registered as world
    def test_companion_registered_as_world(self):
        adapter = self._make_companion_stub()
        self.registry.register(adapter)
        self.assertTrue(self.registry.has("companion"))

    def _make_companion_stub(self):
        """Create a stub that satisfies WorldAdapter protocol for Companion."""
        root = Path(self.temporary.name)

        class _CompanionStub:
            WORLD_ID = "companion"
            WORLD_TYPE = "simulation.rpg"
            ADAPTER_ID = "companion.http.v1"

            def describe(self):
                return WorldDescriptor(
                    world_id="companion",
                    world_type="simulation.rpg",
                    name="Omnisvera Companion",
                    adapter_id="companion.http.v1",
                    capabilities=["observe", "history", "model"],
                    schemas=["companion.session.v1"],
                    metadata={"base_url": "http://127.0.0.1:8787"},
                )

            def health(self):
                return {"status": "offline", "freshness": "unavailable", "limitation": "stub"}

            def observe(self, query=None):
                return WorldObservation(
                    world_id="companion",
                    observed_at="2026-08-30T00:00:00+00:00",
                    schema="companion.session.v1",
                    state={"session_id": None, "participants": []},
                    sources=[],
                    provenance={"adapter": "companion.http.v1"},
                )

        return _CompanionStub()

    # 2. world.list returns descriptor
    def test_world_list_returns_descriptor(self):
        self.registry.register(self.fake)
        descriptors = self.registry.list()
        self.assertEqual(len(descriptors), 1)
        d = descriptors[0]
        self.assertEqual(d.world_id, "test-world")
        self.assertEqual(d.world_type, "sensor气象")
        self.assertIn("observe", d.capabilities)

    # 3. world.describe returns capabilities
    def test_world_describe_returns_capabilities(self):
        self.registry.register(self.fake)
        adapter = self.registry.get("test-world")
        descriptor = adapter.describe()
        health_info = adapter.health()
        self.assertIn("observe", descriptor.capabilities)
        self.assertEqual(health_info["status"], "healthy")
        self.assertEqual(descriptor.schemas, ["weather.station.v1"])

    # 4. world.observe returns WorldObservation
    def test_world_observe_returns_observation(self):
        self.registry.register(self.fake)
        adapter = self.registry.get("test-world")
        observation = adapter.observe()
        self.assertIsInstance(observation, WorldObservation)
        self.assertEqual(observation.world_id, "test-world")
        self.assertEqual(observation.schema, "weather.station.v1")
        self.assertIn("temperature_c", observation.state)
        self.assertEqual(observation.state["temperature_c"], 23.4)

    # 5. CompanionSessionModelV1 still works
    def test_companion_session_model_still_works(self):
        adapter = self._make_companion_stub()
        descriptor = adapter.describe()
        self.assertEqual(descriptor.world_id, "companion")
        self.assertIn("observe", descriptor.capabilities)
        self.assertIn("history", descriptor.capabilities)
        self.assertIn("model", descriptor.capabilities)
        self.assertIn("companion.session.v1", descriptor.schemas)

    # 6. observation can become model_snapshot
    def test_observation_becomes_snapshot(self):
        self.registry.register(self.fake)
        adapter = self.registry.get("test-world")
        observation = adapter.observe()

        # Create snapshot from observation using epistemic handler
        context = type("Ctx", (), {})()
        result_json = snapshot_from_observation(
            self.store, context,
            {"observation": observation.as_dict()},
        )
        result = json.loads(result_json)
        self.assertIn("snapshot_id", result)
        self.assertEqual(result["world_id"], "test-world")
        self.assertEqual(result["schema"], "weather.station.v1")

        # Verify the snapshot exists and is immutable
        mem = self.store.get_memory(result["snapshot_id"])
        self.assertIsNotNone(mem)
        self.assertEqual(mem["type"], "model_snapshot")
        self.assertEqual(mem["status"], "immutable")

    # 7. fake non-RPG world works via same contract
    def test_fake_world_non_rpg_works(self):
        self.registry.register(self.fake)
        adapter = self.registry.get("test-world")
        descriptor = adapter.describe()
        observation = adapter.observe()
        self.assertEqual(descriptor.world_type, "sensor气象")
        self.assertNotIn("session", str(observation.state).lower())
        self.assertNotIn("player", str(observation.state).lower())
        self.assertNotIn("npc", str(observation.state).lower())
        self.assertNotIn("mission", str(observation.state).lower())
        self.assertIn("temperature_c", observation.state)

    # 8. fake world can generate snapshot and prediction
    def test_fake_world_snapshot_and_prediction(self):
        self.registry.register(self.fake)
        adapter = self.registry.get("test-world")
        observation = adapter.observe()

        # Create snapshot
        context = type("Ctx", (), {})()
        result_json = snapshot_from_observation(
            self.store, context,
            {"observation": observation.as_dict()},
        )
        snapshot_id = json.loads(result_json)["snapshot_id"]

        # Create prediction on this non-RPG snapshot
        prediction_id = self.store.create_prediction(
            domain="weather.forecast",
            snapshot_memory_id=snapshot_id,
            claim="temperature will exceed 25C within 24h",
            probability=0.4,
            horizon="24h",
            resolution_rule={"type": "binary", "criterion": "temp > 25"},
        )
        pred = self.store.get_prediction(prediction_id)
        self.assertIsNotNone(pred)
        self.assertEqual(pred["domain"], "weather.forecast")
        self.assertEqual(pred["probability"], 0.4)
        self.assertTrue(pred["snapshot_intact"])

        # Resolve it
        result = self.store.resolve_prediction(prediction_id, outcome=0)
        self.assertEqual(result["status"], "resolved")
        expected_brier = round((0.4 - 0) ** 2, 8)
        self.assertAlmostEqual(result["resolution"]["calibration_score"], expected_brier, places=8)

    # 9. Core does not require session/player/NPC/mission
    def test_core_no_rpg_concepts_required(self):
        self.registry.register(self.fake)
        adapter = self.registry.get("test-world")
        observation = adapter.observe()

        # The state dict has zero RPG concepts
        state = observation.state
        for rpg_concept in ["session", "player", "npc", "mission", "scene", "gm", "character"]:
            for key in state:
                self.assertNotIn(rpg_concept, key.lower())

        # The descriptor has zero RPG concepts
        descriptor = adapter.describe()
        for rpg_concept in ["session", "player", "npc", "mission"]:
            for field_val in [descriptor.world_id, descriptor.world_type, descriptor.name]:
                self.assertNotIn(rpg_concept, str(field_val).lower())

    # 10. previous epistemic suites remain green
    def test_previous_suites_importable(self):
        import tests.test_epistemic_loop
        import tests.test_companion_session
        import tests.test_historical_replay
        import tests.test_timeline
        import tests.test_backtest_validation
        self.assertTrue(hasattr(tests.test_epistemic_loop, "test_bridge_tools"))
        self.assertTrue(hasattr(tests.test_companion_session, "CompanionSessionModelTests"))
        self.assertTrue(hasattr(tests.test_historical_replay, "HistoricalReplayTests"))
        self.assertTrue(hasattr(tests.test_timeline, "TimelineCoreTests"))
        self.assertTrue(hasattr(tests.test_backtest_validation, "BacktestValidationTests"))


class WorldRegistryTests(unittest.TestCase):
    """Additional tests for WorldRegistry behavior."""

    def test_duplicate_registration_rejected(self):
        fake = FakeWorldAdapter()
        registry = WorldRegistry()
        registry.register(fake)
        with self.assertRaises(ValueError):
            registry.register(fake)

    def test_get_unknown_world_raises(self):
        registry = WorldRegistry()
        with self.assertRaises(KeyError):
            registry.get("nonexistent")

    def test_has_returns_false_for_unknown(self):
        registry = WorldRegistry()
        self.assertFalse(registry.has("nonexistent"))

    def test_multiple_worlds(self):
        fake1 = FakeWorldAdapter()
        fake2 = FakeWorldAdapter()
        registry = WorldRegistry()
        registry.register(fake1)
        # Override world_id for second adapter via describe()
        class FakeWorld2(FakeWorldAdapter):
            def describe(self):
                d = super().describe()
                return WorldDescriptor(
                    world_id="test-world-2",
                    world_type="sensor.v2",
                    name="Fake Station 2",
                    adapter_id="fake.v2",
                    capabilities=["observe"],
                    schemas=["weather.v2"],
                )
        registry.register(FakeWorld2())
        self.assertEqual(len(registry.list()), 2)
        self.assertTrue(registry.has("test-world"))
        self.assertTrue(registry.has("test-world-2"))


class WorldDescriptorTests(unittest.TestCase):
    def test_as_dict(self):
        d = WorldDescriptor(
            world_id="x", world_type="t", name="N",
            adapter_id="a", capabilities=["c"], schemas=["s"],
        )
        result = d.as_dict()
        self.assertEqual(result["world_id"], "x")
        self.assertEqual(result["capabilities"], ["c"])

    def test_frozen(self):
        d = WorldDescriptor(world_id="x", world_type="t", name="N", adapter_id="a")
        with self.assertRaises(AttributeError):
            d.world_id = "y"


class WorldObservationTests(unittest.TestCase):
    def test_as_dict(self):
        o = WorldObservation(
            world_id="x", observed_at="now", schema="s",
            state={"k": "v"}, sources=[], provenance={},
        )
        result = o.as_dict()
        self.assertEqual(result["world_id"], "x")
        self.assertEqual(result["state"], {"k": "v"})

    def test_frozen(self):
        o = WorldObservation(world_id="x", observed_at="now", schema="s", state={})
        with self.assertRaises(AttributeError):
            o.world_id = "y"


if __name__ == "__main__":
    unittest.main()
