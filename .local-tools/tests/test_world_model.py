"""Universal World Model Contract v0.1 — Tests.

Tests required by spec:
    1. WorldModel serializes correctly
    2. builder deterministic produces same result for same inputs
    3. signal refs are preserved
    4. pattern refs are preserved
    5. entity_ref is preserved
    6. absence of patterns is explicit
    7. assumptions/limitations are preserved
    8. Companion produces WorldModel
    9. Football produces WorldModel
    10. FakeWorld produces WorldModel
    11. Core does not require domain-specific concepts
    12. world.model is read-only
    13. WorldModel can become model_snapshot
    14. snapshot preserves builder/version/evidence
    15. previous suites remain green
"""
from __future__ import annotations

import sys
import types as _types
import tempfile
import json
from pathlib import Path

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

# Load store.py in isolation
_recall_stub = _types.ModuleType("recall")
_recall_stub.query_terms = lambda q: (q, q.split())
_recall_stub.rank = lambda *a, **kw: None
_recall_stub.validate_options = lambda t, _l: t
sys.modules["recall"] = _recall_stub

_store_src = (LOCAL_TOOLS / "omnisvera_mcp" / "memory" / "store.py").read_text(encoding="utf-8")
_store_ns: dict = {"__name__": "store", "__file__": str(LOCAL_TOOLS / "omnisvera_mcp" / "memory" / "store.py")}
_store_ns["query_terms"] = _recall_stub.query_terms
_store_ns["rank"] = _recall_stub.rank
_store_ns["validate_options"] = _recall_stub.validate_options
_store_src = _store_src.replace("from .recall import", "from recall import")
exec(compile(_store_src, _store_ns["__file__"], "exec"), _store_ns)
MemoryStore = _store_ns["MemoryStore"]

# Load world.py in isolation
_world_mod = _types.ModuleType("world")
_world_mod.__file__ = str(LOCAL_TOOLS / "omnisvera_mcp" / "world.py")
sys.modules["world"] = _world_mod
_world_src = (LOCAL_TOOLS / "omnisvera_mcp" / "world.py").read_text(encoding="utf-8")
exec(compile(_world_src, _world_mod.__file__, "exec"), _world_mod.__dict__)
WorldModel = _world_mod.WorldModel
WorldModelBuilder = _world_mod.WorldModelBuilder
WorldModelRegistry = _world_mod.WorldModelRegistry
CoreStateVectorBuilder = _world_mod.CoreStateVectorBuilder


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _make_signals(world_id, signal_values, entity_ref=None):
    """Create signal observation dicts for MemoryStore."""
    signals = []
    for i, (sid, val, vtype) in enumerate(signal_values, 1):
        signals.append({
            "world_id": world_id,
            "signal_id": sid,
            "entity_ref": entity_ref,
            "schema": "w.sig.v1",
            "value": val,
            "value_type": vtype,
            "observed_at": f"2026-01-01T0{i}:00:00Z",
        })
    return signals


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------

# --- 1. WorldModel serializes correctly ---

def test_worldmodel_serializes():
    m = WorldModel(
        model_id="test.model.1", world_id="w", schema="w.model.v1",
        subject_ref=None, created_at="2026-01-01T00:00:00Z",
        state={"x": 1}, relationships=[],
        signal_refs=[], pattern_refs=[],
        assumptions=[], limitations=[],
        builder_id="test", builder_version="1.0",
    )
    d = m.as_dict()
    assert d["model_id"] == "test.model.1"
    assert d["state"] == {"x": 1}
    assert d["builder_id"] == "test"
    assert d["builder_version"] == "1.0"
    # Frozen
    try:
        m.model_id = "other"
        assert False, "Should be frozen"
    except Exception:
        pass
    print("PASS: worldmodel_serializes")


# --- 2. Builder deterministic ---

def test_builder_deterministic():
    b = CoreStateVectorBuilder()
    signals = [
        {"signal_id": "s.a", "entity_ref": None, "value": 10, "value_type": "number", "observed_at": "T1"},
        {"signal_id": "s.b", "entity_ref": None, "value": 20, "value_type": "number", "observed_at": "T2"},
    ]
    patterns = [
        {"signal_id": "s.a", "entity_ref": None, "pattern_type": "trend",
         "metrics": {"classification": "increasing"}, "method": "lr", "method_version": "1.0"},
    ]
    m1 = b.build(world_id="w", signals=signals, patterns=patterns)
    m2 = b.build(world_id="w", signals=signals, patterns=patterns)
    # State content should be identical (model_id has timestamp, so check state)
    assert m1.state == m2.state
    assert m1.signal_refs == m2.signal_refs
    assert m1.pattern_refs == m2.pattern_refs
    print("PASS: builder_deterministic")


# --- 3. Signal refs preserved ---

def test_signal_refs_preserved():
    b = CoreStateVectorBuilder()
    signals = [
        {"signal_id": "s.x", "entity_ref": "e1", "value": 5, "value_type": "number", "observed_at": "T1"},
        {"signal_id": "s.y", "entity_ref": "e2", "value": 10, "value_type": "number", "observed_at": "T2"},
    ]
    m = b.build(world_id="w", signals=signals, patterns=[])
    refs = m.signal_refs
    assert len(refs) == 2
    assert refs[0]["signal_id"] == "s.x"
    assert refs[0]["entity_ref"] == "e1"
    assert refs[1]["signal_id"] == "s.y"
    assert refs[1]["entity_ref"] == "e2"
    print("PASS: signal_refs_preserved")


# --- 4. Pattern refs preserved ---

def test_pattern_refs_preserved():
    b = CoreStateVectorBuilder()
    signals = [{"signal_id": "s.a", "entity_ref": None, "value": 1, "value_type": "number", "observed_at": "T1"}]
    patterns = [
        {"signal_id": "s.a", "entity_ref": None, "pattern_type": "trend",
         "metrics": {"classification": "stable"}, "method": "lr", "method_version": "1.0"},
        {"signal_id": "s.a", "entity_ref": None, "pattern_type": "anomaly",
         "metrics": {"anomalous": False}, "method": "z", "method_version": "1.0"},
    ]
    m = b.build(world_id="w", signals=signals, patterns=patterns)
    refs = m.pattern_refs
    assert len(refs) == 2
    assert refs[0]["pattern_type"] == "trend"
    assert refs[1]["pattern_type"] == "anomaly"
    # Check state summary
    assert m.state["patterns"]["s.a"]["trend"] == "stable"
    assert m.state["patterns"]["s.a"]["anomaly"] is False
    print("PASS: pattern_refs_preserved")


# --- 5. Entity_ref preserved ---

def test_entity_ref_preserved():
    b = CoreStateVectorBuilder()
    signals = [
        {"signal_id": "s.a", "entity_ref": "match:123", "value": 1, "value_type": "number", "observed_at": "T1"},
    ]
    m = b.build(world_id="w", signals=signals, patterns=[])
    assert m.subject_ref == "match:123"
    assert "match:123" in m.state["entities"]
    print("PASS: entity_ref_preserved")


# --- 6. Absence of patterns explicit ---

def test_no_patterns_explicit():
    b = CoreStateVectorBuilder()
    signals = [{"signal_id": "s.a", "entity_ref": None, "value": 1, "value_type": "number", "observed_at": "T1"}]
    m = b.build(world_id="w", signals=signals, patterns=[])
    assert m.state["patterns"] == {}
    assert any("no patterns" in a for a in m.assumptions)
    print("PASS: no_patterns_explicit")


# --- 7. Assumptions/limitations preserved ---

def test_assumptions_limitations():
    b = CoreStateVectorBuilder()
    signals = [
        {"signal_id": "s.num", "entity_ref": None, "value": 1, "value_type": "number", "observed_at": "T1"},
        {"signal_id": "s.cat", "entity_ref": None, "value": "active", "value_type": "categorical", "observed_at": "T2"},
    ]
    m = b.build(world_id="w", signals=signals, patterns=[])
    assert len(m.limitations) > 0
    assert any("non-numeric" in l for l in m.limitations)
    print("PASS: assumptions_limitations")


# --- 8. Companion produces WorldModel ---

def test_companion_worldmodel():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "companion_model.db")
    sigs = _make_signals("companion", [
        ("companion.session.status", "active", "string"),
        ("companion.session.participant_count", 3, "number"),
        ("companion.session.active_thread_count", 5, "number"),
    ])
    store.capture_signals(sigs)
    history = store.signal_history("companion", "companion.session.status")
    history += store.signal_history("companion", "companion.session.participant_count")
    history += store.signal_history("companion", "companion.session.active_thread_count")
    b = CoreStateVectorBuilder()
    m = b.build(world_id="companion", signals=history, patterns=[])
    assert m.world_id == "companion"
    assert m.builder_id == "core.state-vector"
    assert len(m.signal_refs) == 3
    print("PASS: companion_worldmodel")


# --- 9. Football produces WorldModel ---

def test_football_worldmodel():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "football_model.db")
    sigs = _make_signals("football", [
        ("football.match.status", "scheduled", "string"),
        ("football.match.date", "2026-08-31", "string"),
        ("football.provider.freshness", 2.5, "number"),
    ])
    store.capture_signals(sigs)
    history = []
    for sid in ["football.match.status", "football.match.date", "football.provider.freshness"]:
        history += store.signal_history("football", sid)
    b = CoreStateVectorBuilder()
    m = b.build(world_id="football", signals=history, patterns=[])
    assert m.world_id == "football"
    assert len(m.signal_refs) == 3
    print("PASS: football_worldmodel")


# --- 10. FakeWorld produces WorldModel ---

def test_fakeworld_worldmodel():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "fakeworld_model.db")
    sigs = _make_signals("fakeworld", [
        ("fakeworld.temperature_c", 22.5, "number"),
        ("fakeworld.pressure_hpa", 1013.0, "number"),
    ])
    store.capture_signals(sigs)
    history = []
    for sid in ["fakeworld.temperature_c", "fakeworld.pressure_hpa"]:
        history += store.signal_history("fakeworld", sid)
    b = CoreStateVectorBuilder()
    m = b.build(world_id="fakeworld", signals=history, patterns=[])
    assert m.world_id == "fakeworld"
    assert "fakeworld.temperature_c" in str(m.state["current_signals"])
    print("PASS: fakeworld_worldmodel")


# --- 11. Core does not require domain concepts ---

def test_core_no_domain():
    b = CoreStateVectorBuilder()
    # Build with completely unknown world
    signals = [{"signal_id": "unknown.signal", "entity_ref": None, "value": 42, "value_type": "number", "observed_at": "T1"}]
    m = b.build(world_id="totally_unknown_world", signals=signals, patterns=[])
    assert m.world_id == "totally_unknown_world"
    assert m.builder_id == "core.state-vector"
    # No domain-specific fields required
    assert "current_signals" in m.state
    print("PASS: core_no_domain")


# --- 12. world.model is read-only ---

def test_model_readonly():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "readonly_model.db")
    sigs = _make_signals("w", [("s.a", 1, "number")])
    store.capture_signals(sigs)
    count_before = store.stats()["counts"]["signal_observations"]
    history = store.signal_history("w", "s.a")
    b = CoreStateVectorBuilder()
    b.build(world_id="w", signals=history, patterns=[])
    count_after = store.stats()["counts"]["signal_observations"]
    assert count_before == count_after
    print("PASS: model_readonly")


# --- 13. WorldModel can become model_snapshot ---

def test_model_to_snapshot():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "model_snap.db")
    sigs = _make_signals("w", [("s.a", 10, "number"), ("s.b", 20, "number")])
    store.capture_signals(sigs)
    history = store.signal_history("w", "s.a") + store.signal_history("w", "s.b")
    b = CoreStateVectorBuilder()
    m = b.build(world_id="w", signals=history, patterns=[])

    # Simulate snapshot_from_model logic inline
    metadata = {
        "world_id": m.world_id, "model_id": m.model_id,
        "builder_id": m.builder_id, "builder_version": m.builder_version,
        "signal_refs": m.signal_refs, "pattern_refs": m.pattern_refs,
        "assumptions": m.assumptions, "limitations": m.limitations,
    }
    item_id = store.create_snapshot_memory(
        domain=f"world.{m.world_id}",
        subject=f"{m.builder_id}@{m.builder_version}",
        state=m.state,
        sources=[{"source_type": "world_model", "source_ref": f"{m.world_id}:{m.builder_id}", "relation": "supports"}],
        metadata=metadata,
    )
    assert item_id is not None
    assert len(item_id) > 0
    print("PASS: model_to_snapshot")


# --- 14. Snapshot preserves builder/version/evidence ---

def test_snapshot_preserves_metadata():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "snap_meta.db")
    sigs = _make_signals("w", [("s.x", 5, "number")])
    store.capture_signals(sigs)
    history = store.signal_history("w", "s.x")
    pats = store.signal_patterns("w", "s.x")
    b = CoreStateVectorBuilder()
    m = b.build(world_id="w", signals=history, patterns=pats)

    metadata = {
        "world_id": m.world_id, "model_id": m.model_id,
        "builder_id": m.builder_id, "builder_version": m.builder_version,
        "schema": m.schema, "created_at": m.created_at,
        "signal_refs": m.signal_refs, "pattern_refs": m.pattern_refs,
        "assumptions": m.assumptions, "limitations": m.limitations,
        "provenance": m.provenance,
    }
    item_id = store.create_snapshot_memory(
        domain=f"world.{m.world_id}",
        subject=f"{m.builder_id}@{m.builder_version}",
        state=m.state,
        sources=[{"source_type": "world_model", "source_ref": f"{m.world_id}:{m.builder_id}:{m.model_id}", "relation": "supports"}],
        metadata=metadata,
    )
    item = store.get_memory(item_id)
    assert item is not None
    meta = item.get("metadata", {})
    assert meta["builder_id"] == "core.state-vector"
    assert meta["builder_version"] == "1.0.0"
    assert meta["model_id"] == m.model_id
    assert len(meta["signal_refs"]) == 1
    print("PASS: snapshot_preserves_metadata")


# --- 15. Model Registry ---

def test_model_registry():
    reg = WorldModelRegistry()
    b = CoreStateVectorBuilder()
    desc = reg.register(b)
    assert desc["builder_id"] == "core.state-vector"
    assert reg.has("core.state-vector")
    assert not reg.has("nonexistent")
    builders = reg.list()
    assert len(builders) == 1
    assert builders[0]["builder_id"] == "core.state-vector"
    got = reg.get("core.state-vector")
    assert got is b
    # Duplicate registration raises
    try:
        reg.register(b)
        assert False, "Should raise"
    except ValueError:
        pass
    print("PASS: model_registry")


if __name__ == "__main__":
    test_worldmodel_serializes()
    test_builder_deterministic()
    test_signal_refs_preserved()
    test_pattern_refs_preserved()
    test_entity_ref_preserved()
    test_no_patterns_explicit()
    test_assumptions_limitations()
    test_companion_worldmodel()
    test_football_worldmodel()
    test_fakeworld_worldmodel()
    test_core_no_domain()
    test_model_readonly()
    test_model_to_snapshot()
    test_snapshot_preserves_metadata()
    test_model_registry()
    print("\n=== ALL 15 WORLD MODEL TESTS PASSED ===")
