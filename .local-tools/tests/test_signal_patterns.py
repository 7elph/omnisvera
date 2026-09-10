"""Universal Pattern Detection v0.1 — Tests.

Tests required by spec:
    1. trend increasing
    2. trend decreasing
    3. trend stable
    4. percent_change with zero first value
    5. mean/min/max correct
    6. slope deterministic
    7. anomaly normal not flagged
    8. anomaly extreme flagged
    9. candidate not in its own baseline
    10. insufficient data explicit
    11. categorical no numeric calculation
    12. provenance contains observation IDs
    13. Companion proof
    14. Football proof
    15. FakeWorld proof
    16. analysis is read-only
    17. trend with exactly 2 observations
    18. SignalPattern dataclass
"""
from __future__ import annotations

import sys
import types as _types
import hashlib
import json
import tempfile
from pathlib import Path

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

# Load store.py in isolation (avoid mcp import chain)
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
SignalPattern = _world_mod.SignalPattern


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------

# --- 1. Trend increasing ---

def test_trend_increasing():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "trend_inc.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "w", "signal_id": "s.temp", "entity_ref": None, "schema": "w.sig.v1",
         "value": float(i), "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i in range(1, 6)
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("w", "s.temp")
    trend = next(p for p in patterns if p["pattern_type"] == "trend")
    assert trend["metrics"]["classification"] == "increasing"
    assert trend["metrics"]["slope"] > 0
    assert trend["metrics"]["first_value"] == 1.0
    assert trend["metrics"]["last_value"] == 5.0
    assert trend["metrics"]["absolute_change"] == 4.0
    assert trend["metrics"]["percent_change"] == 400.0
    assert trend["observation_count"] == 5
    print("PASS: trend_increasing")


# --- 2. Trend decreasing ---

def test_trend_decreasing():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "trend_dec.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "w", "signal_id": "s.speed", "entity_ref": "player1", "schema": "w.sig.v1",
         "value": 100.0 - i * 10, "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i in range(1, 6)
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("w", "s.speed", entity_ref="player1")
    trend = next(p for p in patterns if p["pattern_type"] == "trend")
    assert trend["metrics"]["classification"] == "decreasing"
    assert trend["metrics"]["slope"] < 0
    assert trend["metrics"]["first_value"] == 90.0
    assert trend["metrics"]["last_value"] == 50.0
    assert trend["metrics"]["percent_change"] == -44.44
    print("PASS: trend_decreasing")


# --- 3. Trend stable ---

def test_trend_stable():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "trend_stable.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "w", "signal_id": "s.value", "entity_ref": None, "schema": "w.sig.v1",
         "value": 10.0 + (i % 2) * 0.001, "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i in range(1, 8)
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("w", "s.value")
    trend = next(p for p in patterns if p["pattern_type"] == "trend")
    assert trend["metrics"]["classification"] == "stable"
    print("PASS: trend_stable")


# --- 4. percent_change with zero first value ---

def test_percent_change_zero_first():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "pct_zero.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "w", "signal_id": "s.zero", "entity_ref": None, "schema": "w.sig.v1",
         "value": 0.0, "value_type": "number", "observed_at": "2026-01-01T01:00:00Z"},
        {"world_id": "w", "signal_id": "s.zero", "entity_ref": None, "schema": "w.sig.v1",
         "value": 5.0, "value_type": "number", "observed_at": "2026-01-01T02:00:00Z"},
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("w", "s.zero")
    trend = next(p for p in patterns if p["pattern_type"] == "trend")
    assert trend["metrics"]["percent_change"] is None
    assert trend["metrics"]["absolute_change"] == 5.0
    print("PASS: percent_change_zero_first")


# --- 5. mean/min/max correct ---

def test_mean_min_max():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "mmm.db")
    pass  # MemoryStore auto-initializes in __init__
    values = [10.0, 20.0, 5.0, 30.0, 15.0]
    signals = [
        {"world_id": "w", "signal_id": "s.mmm", "entity_ref": None, "schema": "w.sig.v1",
         "value": v, "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i, v in enumerate(values, 1)
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("w", "s.mmm")
    trend = next(p for p in patterns if p["pattern_type"] == "trend")
    assert trend["metrics"]["mean"] == 16.0
    assert trend["metrics"]["min"] == 5.0
    assert trend["metrics"]["max"] == 30.0
    print("PASS: mean_min_max")


# --- 6. Slope deterministic ---

def test_slope_deterministic():
    store1 = MemoryStore(Path(tempfile.mkdtemp()) / "slope1.db")
    store2 = MemoryStore(Path(tempfile.mkdtemp()) / "slope2.db")
    signals = [
        {"world_id": "w", "signal_id": "s.slope", "entity_ref": None, "schema": "w.sig.v1",
         "value": float(i * 3 + 1), "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i in range(1, 7)
    ]
    store1.capture_signals(signals)
    store2.capture_signals(signals)
    t1 = next(p for p in store1.signal_patterns("w", "s.slope") if p["pattern_type"] == "trend")
    t2 = next(p for p in store2.signal_patterns("w", "s.slope") if p["pattern_type"] == "trend")
    assert t1["metrics"]["slope"] == t2["metrics"]["slope"]
    assert abs(t1["metrics"]["slope"] - 3.0) < 0.01
    print("PASS: slope_deterministic")


# --- 7. Anomaly normal not flagged ---

def test_anomaly_normal_not_flagged():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "anom_norm.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "w", "signal_id": "s.normal", "entity_ref": None, "schema": "w.sig.v1",
         "value": 10.0, "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i in range(1, 8)
    ]
    store.capture_signals(signals)
    anomalies = [p for p in store.signal_patterns("w", "s.normal") if p["pattern_type"] == "anomaly"]
    assert len(anomalies) == 0
    print("PASS: anomaly_normal_not_flagged")


# --- 8. Anomaly extreme flagged ---

def test_anomaly_extreme_flagged():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "anom_ext.db")
    pass  # MemoryStore auto-initializes in __init__
    values = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 100.0]
    signals = [
        {"world_id": "w", "signal_id": "s.extreme", "entity_ref": None, "schema": "w.sig.v1",
         "value": v, "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i, v in enumerate(values, 1)
    ]
    store.capture_signals(signals)
    anomalies = [p for p in store.signal_patterns("w", "s.extreme") if p["pattern_type"] == "anomaly"]
    assert len(anomalies) == 1
    a = anomalies[0]
    assert a["metrics"]["anomalous"] is True
    assert a["metrics"]["value"] == 100.0
    assert a["metrics"]["baseline_mean"] == 10.0
    assert a["metrics"]["baseline_std"] == 0.0
    print("PASS: anomaly_extreme_flagged")


# --- 9. Candidate not in its own baseline ---

def test_candidate_not_in_own_baseline():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "no_leak.db")
    pass  # MemoryStore auto-initializes in __init__
    values = [10.0, 10.0, 10.0, 10.0, 10.0, 50.0]
    signals = [
        {"world_id": "w", "signal_id": "s.noleak", "entity_ref": None, "schema": "w.sig.v1",
         "value": v, "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i, v in enumerate(values, 1)
    ]
    store.capture_signals(signals)
    anomalies = [p for p in store.signal_patterns("w", "s.noleak") if p["pattern_type"] == "anomaly"]
    assert len(anomalies) == 1
    a = anomalies[0]
    assert a["metrics"]["baseline_mean"] == 10.0
    assert a["metrics"]["value"] == 50.0
    assert a["provenance"]["baseline_count"] == 5
    print("PASS: candidate_not_in_own_baseline")


# --- 10. Insufficient data explicit ---

def test_insufficient_data():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "insuff.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "w", "signal_id": "s.few", "entity_ref": None, "schema": "w.sig.v1",
         "value": 42.0, "value_type": "number", "observed_at": "2026-01-01T01:00:00Z"},
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("w", "s.few")
    assert len(patterns) == 0
    print("PASS: insufficient_data")


# --- 11. Categorical no numeric calculation ---

def test_categorical_no_calc():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "cat.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "w", "signal_id": "s.status", "entity_ref": None, "schema": "w.sig.v1",
         "value": v, "value_type": "categorical", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i, v in enumerate(["active", "idle", "active", "error", "active", "idle", "active"], 1)
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("w", "s.status")
    assert len(patterns) == 0
    print("PASS: categorical_no_calc")


# --- 12. Provenance contains observation IDs ---

def test_provenance_observation_ids():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "prov.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "w", "signal_id": "s.prov", "entity_ref": None, "schema": "w.sig.v1",
         "value": float(i), "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i in range(1, 6)
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("w", "s.prov")
    for p in patterns:
        assert "observation_ids" in p["provenance"]
        assert len(p["provenance"]["observation_ids"]) >= 2
        assert p["method"] != ""
        assert p["method_version"] == "1.0"
        assert p["window_start"] != ""
        assert p["window_end"] != ""
    print("PASS: provenance_observation_ids")


# --- 13. Companion proof ---

def test_companion_proof():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "companion.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "companion", "signal_id": "companion.session.active_thread_count",
         "entity_ref": None, "schema": "w.sig.v1",
         "value": v, "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i, v in enumerate([2.0, 3.0, 4.0, 5.0], 1)
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("companion", "companion.session.active_thread_count")
    trend = next(p for p in patterns if p["pattern_type"] == "trend")
    assert trend["metrics"]["classification"] == "increasing"
    assert trend["metrics"]["first_value"] == 2.0
    assert trend["metrics"]["last_value"] == 5.0
    assert trend["metrics"]["slope"] == 1.0
    print("PASS: companion_proof")


# --- 14. Football proof ---

def test_football_proof():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "football.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "football", "signal_id": "football.provider.freshness",
         "entity_ref": None, "schema": "w.sig.v1",
         "value": v, "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i, v in enumerate([1.0, 2.0, 3.0, 4.0, 5.0, 15.0], 1)
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("football", "football.provider.freshness")
    trend = next(p for p in patterns if p["pattern_type"] == "trend")
    assert trend["metrics"]["classification"] == "increasing"
    anomalies = [p for p in patterns if p["pattern_type"] == "anomaly"]
    assert len(anomalies) == 1
    assert anomalies[0]["metrics"]["value"] == 15.0
    print("PASS: football_proof")


# --- 15. FakeWorld proof ---

def test_fakeworld_proof():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "fakeworld.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "fakeworld", "signal_id": "fakeworld.temperature_c",
         "entity_ref": None, "schema": "w.sig.v1",
         "value": v, "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i, v in enumerate([20.0, 20.5, 21.0, 20.8, 20.2, 40.0], 1)
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("fakeworld", "fakeworld.temperature_c")
    trend = next(p for p in patterns if p["pattern_type"] == "trend")
    assert trend["metrics"]["classification"] == "increasing"
    anomalies = [p for p in patterns if p["pattern_type"] == "anomaly"]
    assert len(anomalies) == 1
    assert anomalies[0]["metrics"]["value"] == 40.0
    assert anomalies[0]["metrics"]["anomalous"] is True
    print("PASS: fakeworld_proof")


# --- 16. Analysis is read-only ---

def test_readonly():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "readonly.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "w", "signal_id": "s.ro", "entity_ref": None, "schema": "w.sig.v1",
         "value": float(i), "value_type": "number", "observed_at": f"2026-01-01T0{i}:00:00Z"}
        for i in range(1, 8)
    ]
    store.capture_signals(signals)
    count_before = store.stats()["counts"]["signal_observations"]
    store.signal_patterns("w", "s.ro")
    count_after = store.stats()["counts"]["signal_observations"]
    assert count_before == count_after
    print("PASS: readonly")


# --- 17. Trend with exactly 2 observations ---

def test_trend_two_observations():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "two_obs.db")
    pass  # MemoryStore auto-initializes in __init__
    signals = [
        {"world_id": "w", "signal_id": "s.two", "entity_ref": None, "schema": "w.sig.v1",
         "value": 10.0, "value_type": "number", "observed_at": "2026-01-01T01:00:00Z"},
        {"world_id": "w", "signal_id": "s.two", "entity_ref": None, "schema": "w.sig.v1",
         "value": 20.0, "value_type": "number", "observed_at": "2026-01-01T02:00:00Z"},
    ]
    store.capture_signals(signals)
    patterns = store.signal_patterns("w", "s.two")
    trend = next(p for p in patterns if p["pattern_type"] == "trend")
    assert trend["metrics"]["classification"] == "increasing"
    assert trend["metrics"]["slope"] == 10.0
    assert trend["observation_count"] == 2
    assert trend["metrics"]["percent_change"] == 100.0
    print("PASS: trend_two_observations")


# --- 18. SignalPattern dataclass ---

def test_signal_pattern_dataclass():
    sp = SignalPattern(
        world_id="w", signal_id="s", entity_ref=None, pattern_type="trend",
        window_start="2026-01-01T01:00:00Z", window_end="2026-01-01T05:00:00Z",
        observation_count=5, metrics={"slope": 1.0, "classification": "increasing"},
        confidence=None, method="linear_regression", method_version="1.0",
        provenance={"observation_ids": [1, 2, 3, 4, 5]},
    )
    d = sp.as_dict()
    assert d["pattern_type"] == "trend"
    assert d["metrics"]["slope"] == 1.0
    assert d["confidence"] is None
    try:
        sp.pattern_type = "other"
        assert False, "Should be frozen"
    except Exception:
        pass
    print("PASS: signal_pattern_dataclass")


if __name__ == "__main__":
    test_trend_increasing()
    test_trend_decreasing()
    test_trend_stable()
    test_percent_change_zero_first()
    test_mean_min_max()
    test_slope_deterministic()
    test_anomaly_normal_not_flagged()
    test_anomaly_extreme_flagged()
    test_candidate_not_in_own_baseline()
    test_insufficient_data()
    test_categorical_no_calc()
    test_provenance_observation_ids()
    test_companion_proof()
    test_football_proof()
    test_fakeworld_proof()
    test_readonly()
    test_trend_two_observations()
    test_signal_pattern_dataclass()
    print("\n=== ALL 18 SIGNAL PATTERN TESTS PASSED ===")
