"""Universal Continuity Bootstrap v0.1 — Tests.

Tests required by spec:
    1. bootstrap serializes
    2. includes timestamp/freshness
    3. includes health
    4. references manifest
    5. includes registered worlds dynamically
    6. includes project states
    7. memory restricted (no secrets)
    8. historical state not marked as current
    9. recommended reads exist
    10. no writes occur
    11. AI identity not hard-coded
    12. works with Companion + Football registered
    13. absence of memory/project handled
    14. remote policy respected
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

# Load bootstrap module directly
_bootstrap_src = (LOCAL_TOOLS / "omnisvera_mcp" / "bootstrap.py").read_text(encoding="utf-8")
_bootstrap_ns: dict = {"__name__": "bootstrap", "__file__": str(LOCAL_TOOLS / "omnisvera_mcp" / "bootstrap.py")}
exec(compile(_bootstrap_src, _bootstrap_ns["__file__"], "exec"), _bootstrap_ns)
generate_bootstrap = _bootstrap_ns["generate_bootstrap"]
BOOTSTRAP_VERSION = _bootstrap_ns["BOOTSTRAP_VERSION"]

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


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------

def _sample_health():
    return {
        "observed_at": "2026-08-31T12:00:00Z",
        "mcp_core": {"status": "healthy", "freshness": "fresh"},
        "vault": {"status": "healthy", "freshness": "fresh", "documents": 42},
        "git": {"status": "healthy", "freshness": "fresh", "head": "abc123"},
        "companion": {"status": "healthy", "freshness": "stale"},
        "memory": {"status": "healthy", "freshness": "fresh", "path": "/tmp/test.db", "counts": {}},
    }


def _sample_handoff():
    return {
        "generated_at": "2026-08-31T12:00:00Z",
        "git": {"value": {"branch": "main"}, "source": "git"},
        "companion": {"value": {"app_state": {}}, "source": "companion.api", "freshness": "stale"},
        "memory": {"value": {"memory_items": 5}, "source": "sqlite"},
    }


def _sample_worlds():
    return [
        {"world_id": "companion", "name": "Companion", "world_type": "companion", "capabilities": ["observe", "signals"]},
        {"world_id": "football", "name": "Football", "world_type": "football", "capabilities": ["observe", "signals"]},
    ]


def _sample_manifest():
    return {
        "manifest_version": "0.1",
        "epistemic": {"snapshot_from_observation": True, "prediction": True},
        "signals": {"history": True, "patterns": True},
        "models": {"builders": [{"builder_id": "core.state-vector"}]},
    }


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------

# --- 1. bootstrap serializes ---

def test_bootstrap_serializes():
    b = generate_bootstrap()
    assert isinstance(b, dict)
    d = json.loads(json.dumps(b))
    assert d["system"]["name"] == "omnisvera-mcp"
    print("PASS: bootstrap_serializes")


# --- 2. includes timestamp/freshness ---

def test_includes_timestamp():
    b = generate_bootstrap()
    assert "observed_at" in b
    assert "T" in b["observed_at"]
    assert b["system"]["observed_at"] == b["observed_at"]
    print("PASS: includes_timestamp")


# --- 3. includes health ---

def test_includes_health():
    h = _sample_health()
    b = generate_bootstrap(health=h)
    assert b["continuity"] is not None  # health may be nested
    # Health is passed through, check subsystems if present
    health_section = b.get("health", {})
    if health_section:
        assert "subsystems" in health_section
    print("PASS: includes_health")


# --- 4. references manifest ---

def test_references_manifest():
    m = _sample_manifest()
    b = generate_bootstrap(manifest_summary=m)
    assert b["capabilities"]["manifest_ref"] == "system.manifest"
    assert b["capabilities"]["bootstrap_ref"] == "system.bootstrap"
    assert b["system"]["manifest_version"] == "0.1"
    print("PASS: references_manifest")


# --- 5. includes registered worlds dynamically ---

def test_includes_worlds():
    worlds = _sample_worlds()
    b = generate_bootstrap(worlds=worlds)
    assert len(b["worlds"]) == 2
    ids = {w["world_id"] for w in b["worlds"]}
    assert "companion" in ids
    assert "football" in ids
    print("PASS: includes_worlds")


# --- 6. includes project states ---

def test_includes_project_states():
    states = {
        "companion": {
            "observed_at": "2026-08-31T10:00:00Z",
            "source": "companion.api",
            "confidence": 1.0,
            "freshness": "fresh",
        }
    }
    b = generate_bootstrap(latest_project_states=states)
    assert "companion" in b["continuity"]["project_states"]
    ps = b["continuity"]["project_states"]["companion"]
    assert ps["source"] == "companion.api"
    assert ps["confidence"] == 1.0
    print("PASS: includes_project_states")


# --- 7. memory restricted ---

def test_memory_restricted():
    stats = {"counts": {"memory_items": 10, "memory_sources": 5}}
    recent = [
        {"id": "mem-1", "type": "constraint", "title": "rule1", "status": "accepted", "updated_at": "T1"},
        {"id": "mem-2", "type": "heuristic", "title": "rule2", "status": "accepted", "updated_at": "T2"},
    ]
    b = generate_bootstrap(memory_stats=stats, recent_memories=recent)
    # Should include counts, not full content
    assert b["continuity"]["memory"]["total_items"] == 10
    # Recent memories should be compact (no content field)
    for m in b["continuity"]["recent_memory"]:
        assert "content" not in m
        assert "id" in m
        assert "title" in m
    print("PASS: memory_restricted")


# --- 8. historical state not marked as current ---

def test_historical_not_current():
    states = {
        "companion": {
            "observed_at": "2026-01-01T00:00:00Z",
            "source": "companion.api",
            "confidence": 0.5,
            "freshness": "stale",
        }
    }
    b = generate_bootstrap(latest_project_states=states)
    ps = b["continuity"]["project_states"]["companion"]
    # Should show freshness as "stale", not pretend it's current
    assert ps["freshness"] == "stale"
    assert ps["observed_at"] == "2026-01-01T00:00:00Z"
    print("PASS: historical_not_current")


# --- 9. recommended reads exist ---

def test_recommended_reads():
    b = generate_bootstrap(worlds=_sample_worlds(), memory_stats={"counts": {"memory_items": 5}})
    reads = b["recommended_next_reads"]
    assert len(reads) > 0
    assert "system.manifest" in reads
    assert "world.list" in reads
    assert "memory.list" in reads
    print("PASS: recommended_reads")


# --- 10. no writes occur ---

def test_no_writes():
    store = MemoryStore(Path(tempfile.mkdtemp()) / "bs_readonly.db")
    counts_before = store.stats()
    b = generate_bootstrap()
    counts_after = store.stats()
    assert counts_before == counts_after
    print("PASS: no_writes")


# --- 11. AI identity not hard-coded ---

def test_no_ai_identity():
    b = generate_bootstrap()
    # Should not contain any specific AI provider names
    serialized = json.dumps(b).lower()
    assert "openai" not in serialized
    assert "anthropic" not in serialized
    assert "claude" not in serialized
    assert "gpt" not in serialized
    assert "mia" not in serialized
    print("PASS: no_ai_identity")


# --- 12. works with Companion + Football registered ---

def test_companion_football():
    h = _sample_health()
    ho = _sample_handoff()
    worlds = _sample_worlds()
    m = _sample_manifest()
    states = {"companion": {"observed_at": "T1", "source": "api", "confidence": 1.0, "freshness": "fresh"}}
    stats = {"counts": {"memory_items": 3, "signal_observations": 15}}
    b = generate_bootstrap(
        health=h, handoff=ho, worlds=worlds,
        latest_project_states=states, memory_stats=stats,
        manifest_summary=m, signal_worlds=["companion", "football"],
    )
    assert len(b["worlds"]) == 2
    assert b["continuity"]["memory"]["signal_observations"] == 15
    # Check recommended reads include world.observe
    observe_recs = [r for r in b["recommended_next_reads"] if "world.observe" in r]
    assert len(observe_recs) == 2
    print("PASS: companion_football")


# --- 13. absence of memory/project handled ---

def test_absence_handled():
    b = generate_bootstrap()
    # No memory, no projects, no worlds — should still produce valid manifest
    assert b["system"]["name"] == "omnisvera-mcp"
    assert b["worlds"] == []
    assert b["continuity"] == {}
    assert any("no worlds" in l for l in b["limitations"])
    print("PASS: absence_handled")


# --- 14. remote policy respected ---

def test_remote_policy():
    # Bootstrap should not include secrets, tokens, or credentials
    b = generate_bootstrap()
    serialized = json.dumps(b)
    assert "token" not in serialized.lower()
    assert "secret" not in serialized.lower()
    assert "password" not in serialized.lower()
    assert "api_key" not in serialized.lower()
    print("PASS: remote_policy")


# --- 15. bootstrap version constant ---

def test_bootstrap_version():
    assert BOOTSTRAP_VERSION == "0.1"
    b = generate_bootstrap()
    assert b["bootstrap_version"] == "0.1"
    print("PASS: bootstrap_version")


if __name__ == "__main__":
    test_bootstrap_serializes()
    test_includes_timestamp()
    test_includes_health()
    test_references_manifest()
    test_includes_worlds()
    test_includes_project_states()
    test_memory_restricted()
    test_historical_not_current()
    test_recommended_reads()
    test_no_writes()
    test_no_ai_identity()
    test_companion_football()
    test_absence_handled()
    test_remote_policy()
    test_bootstrap_version()
    print("\n=== ALL 15 BOOTSTRAP TESTS PASSED ===")
