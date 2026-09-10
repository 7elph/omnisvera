"""Omnisvera Capability Manifest v0.1 — Tests.

Tests required by spec:
    1. manifest serializes correctly
    2. manifest version is present
    3. worlds are listed
    4. epistemic capabilities present
    5. signal capabilities present
    6. model builders listed
    7. prediction schema present
    8. predictor types listed
    9. tool catalog present
    10. permissions summary present
    11. architecture chain present
    12. empty worlds produces valid manifest
    13. memory stats included when provided
    14. manifest is read-only
    15. all previous suites remain green
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

# Load manifest module directly
_manifest_src = (LOCAL_TOOLS / "omnisvera_mcp" / "manifest.py").read_text(encoding="utf-8")
_manifest_ns: dict = {"__name__": "manifest", "__file__": str(LOCAL_TOOLS / "omnisvera_mcp" / "manifest.py")}
exec(compile(_manifest_src, _manifest_ns["__file__"], "exec"), _manifest_ns)
generate_manifest = _manifest_ns["generate_manifest"]
MANIFEST_VERSION = _manifest_ns["MANIFEST_VERSION"]

# Load store.py in isolation for memory stats
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


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------

def _sample_worlds():
    return [
        {
            "world_id": "companion", "world_type": "companion",
            "name": "Companion", "adapter_id": "companion.v1",
            "capabilities": ["observe", "signals"],
            "schemas": ["companion.session.v1"],
        },
        {
            "world_id": "football", "world_type": "football",
            "name": "Football", "adapter_id": "football.v1",
            "capabilities": ["observe", "signals"],
            "schemas": ["football.match.v1"],
        },
    ]


def _sample_builders():
    return [
        {"builder_id": "core.state-vector", "builder_version": "1.0.0",
         "name": "Core State Vector Builder"},
    ]


def _sample_tools():
    return [
        {"name": "world.list", "access_mode": "read", "resource": "world://registry"},
        {"name": "world.observe", "access_mode": "read", "resource": "world://observations"},
        {"name": "world.signals", "access_mode": "read", "resource": "world://signals"},
        {"name": "world.capture_signals", "access_mode": "write", "resource": "world://signals"},
        {"name": "world.signal_history", "access_mode": "read", "resource": "world://signals"},
        {"name": "world.signal_changes", "access_mode": "read", "resource": "world://signals"},
        {"name": "world.signal_patterns", "access_mode": "read", "resource": "world://signals"},
        {"name": "world.model", "access_mode": "read", "resource": "world://models"},
        {"name": "epistemic.snapshot_from_observation", "access_mode": "write", "resource": "epistemic://snapshots"},
        {"name": "epistemic.snapshot_from_model", "access_mode": "write", "resource": "epistemic://snapshots"},
        {"name": "epistemic.validate_candidate", "access_mode": "read", "resource": "epistemic://predictions"},
        {"name": "epistemic.commit_candidate", "access_mode": "write", "resource": "epistemic://predictions"},
        {"name": "system.health", "access_mode": "read", "resource": "system://health"},
        {"name": "system.manifest", "access_mode": "read", "resource": "system://manifest"},
    ]


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------

# --- 1. manifest serializes correctly ---

def test_manifest_serializes():
    m = generate_manifest(worlds=[], model_builders=[], tools=[])
    assert isinstance(m, dict)
    d = json.loads(json.dumps(m))  # roundtrip
    assert d["system"] == "omnisvera-mcp"
    print("PASS: manifest_serializes")


# --- 2. manifest version is present ---

def test_manifest_version():
    m = generate_manifest(worlds=[], model_builders=[], tools=[])
    assert m["manifest_version"] == MANIFEST_VERSION
    assert m["manifest_version"] == "0.1"
    print("PASS: manifest_version")


# --- 3. worlds are listed ---

def test_worlds_listed():
    m = generate_manifest(worlds=_sample_worlds(), model_builders=[], tools=[])
    assert len(m["worlds"]) == 2
    ids = {w["world_id"] for w in m["worlds"]}
    assert "companion" in ids
    assert "football" in ids
    # Check capabilities preserved
    comp = next(w for w in m["worlds"] if w["world_id"] == "companion")
    assert "observe" in comp["capabilities"]
    print("PASS: worlds_listed")


# --- 4. epistemic capabilities present ---

def test_epistemic_capabilities():
    m = generate_manifest(worlds=[], model_builders=[], tools=_sample_tools())
    e = m["epistemic"]
    assert e["snapshot_from_observation"] is True
    assert e["snapshot_from_model"] is True
    assert e["prediction"] is True
    assert e["validation"] is True
    print("PASS: epistemic_capabilities")


# --- 5. signal capabilities present ---

def test_signal_capabilities():
    m = generate_manifest(worlds=[], model_builders=[], tools=_sample_tools())
    s = m["signals"]
    assert s["capture"] is True
    assert s["history"] is True
    assert s["changes"] is True
    assert s["patterns"] is True
    assert "trend" in s["pattern_types"]
    assert "anomaly" in s["pattern_types"]
    print("PASS: signal_capabilities")


# --- 6. model builders listed ---

def test_model_builders():
    m = generate_manifest(worlds=[], model_builders=_sample_builders(), tools=_sample_tools())
    builders = m["models"]["builders"]
    assert len(builders) == 1
    assert builders[0]["builder_id"] == "core.state-vector"
    assert m["models"]["tools"]["build_model"] is True
    print("PASS: model_builders")


# --- 7. prediction schema present ---

def test_prediction_schema():
    m = generate_manifest(worlds=[], model_builders=[], tools=_sample_tools())
    p = m["prediction"]
    assert "candidate_schema" in p
    assert "required" in p["candidate_schema"]
    assert "claim" in p["candidate_schema"]["required"]
    assert "probability" in p["candidate_schema"]["required"]
    assert "workflow" in p
    assert len(p["workflow"]) > 0
    print("PASS: prediction_schema")


# --- 8. predictor types listed ---

def test_predictor_types():
    m = generate_manifest(worlds=[], model_builders=[], tools=[])
    pts = m["prediction"]["predictor_types"]
    assert "ai" in pts
    assert "deterministic" in pts
    assert "statistical" in pts
    assert "human" in pts
    assert "external" in pts
    print("PASS: predictor_types")


# --- 9. tool catalog present ---

def test_tool_catalog():
    m = generate_manifest(worlds=[], model_builders=[], tools=_sample_tools())
    catalog = m["tools"]
    assert len(catalog) == len(_sample_tools())
    names = {t["name"] for t in catalog}
    assert "world.list" in names
    assert "system.manifest" in names
    # Check structure
    for t in catalog:
        assert "name" in t
        assert "access" in t
        assert "resource" in t
    print("PASS: tool_catalog")


# --- 10. permissions summary present ---

def test_permissions():
    m = generate_manifest(worlds=[], model_builders=[], tools=_sample_tools())
    perm = m["permissions"]["remote_bridge"]
    assert "read" in perm
    assert "write" in perm
    assert isinstance(perm["read"], list)
    assert isinstance(perm["write"], list)
    assert "world.list" in perm["read"]
    assert "world.capture_signals" in perm["write"]
    print("PASS: permissions")


# --- 11. architecture chain present ---

def test_architecture():
    m = generate_manifest(worlds=[], model_builders=[], tools=[])
    arch = m["architecture"]
    assert "chain" in arch
    assert "World" in arch["chain"]
    assert "Score" in arch["chain"]
    assert arch["chain"][0] == "World"
    assert arch["chain"][-1] == "Score"
    assert "principles" in arch
    assert len(arch["principles"]) > 0
    print("PASS: architecture")


# --- 12. empty worlds produces valid manifest ---

def test_empty_worlds():
    m = generate_manifest(worlds=[], model_builders=[], tools=[])
    assert m["worlds"] == []
    assert m["tools"] == []
    assert m["system"] == "omnisvera-mcp"
    assert m["manifest_version"] == "0.1"
    print("PASS: empty_worlds")


# --- 13. memory stats included when provided ---

def test_memory_stats():
    stats = {"path": "/tmp/test.db", "counts": {"memory_items": 10}}
    m = generate_manifest(worlds=[], model_builders=[], tools=[], memory_stats=stats)
    assert m["memory"]["stats"] == stats
    assert m["memory"]["read"] is False  # no memory tools provided
    print("PASS: memory_stats")


# --- 14. manifest is read-only ---

def test_manifest_readonly():
    # The manifest generation does not modify any state
    store = MemoryStore(Path(tempfile.mkdtemp()) / "readonly.db")
    counts_before = store.stats()
    m = generate_manifest(worlds=[], model_builders=[], tools=[])
    counts_after = store.stats()
    assert counts_before == counts_after
    print("PASS: manifest_readonly")


# --- 15. manifest with all components ---

def test_full_manifest():
    m = generate_manifest(
        worlds=_sample_worlds(),
        model_builders=_sample_builders(),
        tools=_sample_tools(),
        memory_stats={"counts": {"memory_items": 5}},
    )
    assert len(m["worlds"]) == 2
    assert len(m["tools"]) == len(_sample_tools())
    assert m["epistemic"]["prediction"] is True
    assert m["signals"]["patterns"] is True
    assert len(m["models"]["builders"]) == 1
    assert m["prediction"]["predictor_types"] == ["ai", "deterministic", "statistical", "human", "external"]
    assert m["memory"]["read"] is False
    assert "read" in m["permissions"]["remote_bridge"]
    assert "write" in m["permissions"]["remote_bridge"]
    print("PASS: full_manifest")


if __name__ == "__main__":
    test_manifest_serializes()
    test_manifest_version()
    test_worlds_listed()
    test_epistemic_capabilities()
    test_signal_capabilities()
    test_model_builders()
    test_prediction_schema()
    test_predictor_types()
    test_tool_catalog()
    test_permissions()
    test_architecture()
    test_empty_worlds()
    test_memory_stats()
    test_manifest_readonly()
    test_full_manifest()
    print("\n=== ALL 15 MANIFEST TESTS PASSED ===")
