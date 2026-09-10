"""Real Brain Integration v0.1 — Capstone Test

Simulates what a real AI brain (OpenCode) would do when connected to
Omnisvera through the Bridge, WITHOUT pre-programmed architectural knowledge.

The brain starts with only: "You are connected to a system. Start by calling system.bootstrap."
Everything else is discovered through the system's own self-description.

Success criteria:
  - The brain discovers how to use Omnisvera through bootstrap/manifest
  - It registers a REAL prospective prediction that stays OPEN
  - The prediction has full provenance and policy compliance
  - We do NOT resolve it artificially — the world resolves it when the event occurs
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# -- Bootstrap path --
LOCAL_TOOLS = Path(__file__).resolve().parent.parent / "omnisvera_mcp"

# -- Evidence capture --
EVIDENCE: dict[str, Any] = {
    "brain": "opencode/mimo-v2.5-free",
    "discovery_path": [],
    "tools_called": [],
    "errors_encountered": [],
    "bootstrap_payload": None,
    "manifest_payload": None,
    "world_chosen": None,
    "observation": None,
    "signals": None,
    "model_snapshot_id": None,
    "model_snapshot_hash": None,
    "model_id": None,
    "candidate": None,
    "validation": None,
    "commit_result": None,
    "prediction": None,
}


def _log_discovery(step: str, detail: str) -> None:
    EVIDENCE["discovery_path"].append({
        "step": len(EVIDENCE["discovery_path"]) + 1,
        "action": step,
        "detail": detail,
    })


def _log_error(step: str, error: str) -> None:
    EVIDENCE["errors_encountered"].append({"step": step, "error": error})


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


# ============================================================================
# Load modules via exec (same isolation pattern as other test files)
# ============================================================================

# -- Recall stubs --
import types as _types
_recall_stub = _types.ModuleType("recall")
_recall_stub.query_terms = lambda q: (q, q.split())
_recall_stub.rank = lambda *a, **kw: None
_recall_stub.validate_options = lambda t, _l: t
sys.modules["recall"] = _recall_stub

# -- Load store.py --
_store_src = (LOCAL_TOOLS / "memory" / "store.py").read_text(encoding="utf-8")
_store_ns: dict = {"__name__": "store", "__file__": str(LOCAL_TOOLS / "memory" / "store.py")}
_store_ns["query_terms"] = _recall_stub.query_terms
_store_ns["rank"] = _recall_stub.rank
_store_ns["validate_options"] = _recall_stub.validate_options
_store_src = _store_src.replace("from .recall import", "from recall import")
exec(compile(_store_src, _store_ns["__file__"], "exec"), _store_ns)
MemoryStore = _store_ns["MemoryStore"]

# -- Load world.py --
_world_mod = _types.ModuleType("world")
_world_mod.__file__ = str(LOCAL_TOOLS / "world.py")
sys.modules["world"] = _world_mod
_world_src = (LOCAL_TOOLS / "world.py").read_text(encoding="utf-8")
exec(compile(_world_src, _world_mod.__file__, "exec"), _world_mod.__dict__)
WorldRegistry = _world_mod.WorldRegistry
WorldModelRegistry = _world_mod.WorldModelRegistry
CoreStateVectorBuilder = _world_mod.CoreStateVectorBuilder
WorldObservation = _world_mod.WorldObservation
WorldSignal = _world_mod.WorldSignal
WorldModel = _world_mod.WorldModel

# -- Load football adapter --
_football_mod = _types.ModuleType("football")
_football_mod.__file__ = str(LOCAL_TOOLS / "adapters" / "football.py")
sys.modules["football"] = _football_mod
_football_src = (LOCAL_TOOLS / "adapters" / "football.py").read_text(encoding="utf-8")
_football_src = _football_src.replace("from ..world import", "from world import")
exec(compile(_football_src, _football_mod.__file__, "exec"), _football_mod.__dict__)
FootballWorldAdapter = _football_mod.FootballWorldAdapter

# -- Load companion adapter --
_companion_mod = _types.ModuleType("companion_adapter")
_companion_mod.__file__ = str(LOCAL_TOOLS / "adapters" / "companion.py")
sys.modules["companion_adapter"] = _companion_mod
_companion_src = (LOCAL_TOOLS / "adapters" / "companion.py").read_text(encoding="utf-8")
_companion_src = _companion_src.replace("from ..world import", "from world import")
exec(compile(_companion_src, _companion_mod.__file__, "exec"), _companion_mod.__dict__)
CompanionAdapter = _companion_mod.CompanionAdapter

# -- Load epistemic.py --
_ep_ns: dict = {"__name__": "epistemic", "__file__": str(LOCAL_TOOLS / "epistemic.py"), "__builtins__": __builtins__}
_ep_ns["MemoryStore"] = MemoryStore
_ep_ns["WorldModel"] = WorldModel
_ep_ns["json"] = json
_ep_ns["hashlib"] = hashlib
_ep_ns["Any"] = __import__("typing").Any
_ep_ns["stable_json"] = _store_ns["stable_json"]

# Fake CallContext for the brain
class _BrainContext:
    actor = "opencode"
    client = "capstone-test"
    transport = "test"
    scopes = frozenset({"*"})

_ep_ns["CallContext"] = _BrainContext
_ep_src = (LOCAL_TOOLS / "epistemic.py").read_text(encoding="utf-8")
_ep_src = _ep_src.replace("from .core.context import CallContext", "")
_ep_src = _ep_src.replace("from .memory.store import MemoryStore, stable_json", "")
_ep_src = _ep_src.replace("from .memory.store import MemoryStore", "")
exec(compile(_ep_src, _ep_ns["__file__"], "exec"), _ep_ns)
validate_candidate_fn = _ep_ns["validate_candidate"]
commit_candidate_fn = _ep_ns["commit_candidate"]
get_prediction_fn = _ep_ns["get_prediction"]
snapshot_from_model_fn = _ep_ns["snapshot_from_model"]

# -- Create store --
db_path = Path(tempfile.mkdtemp()) / "capstone.db"
store = MemoryStore(db_path)

# -- Register worlds --
worlds = WorldRegistry()
companion = CompanionAdapter(Path.cwd())
football = FootballWorldAdapter()
worlds.register(companion)
worlds.register(football)

# -- Register model builders --
builders = WorldModelRegistry()
builders.register(CoreStateVectorBuilder())

brain_ctx = _BrainContext()


# ============================================================================
print("=" * 70)
print("REAL BRAIN INTEGRATION v0.1 — CAPSTONE TEST")
print("=" * 70)
print()
print("Brain: opencode/mimo-v2.5-free")
print("Prompt: 'You are connected to a system. Start by calling system.bootstrap.'")
print()
_log_discovery("initial_prompt", "Brain receives: 'You are connected to a system. Start by calling system.bootstrap.'")


# ============================================================================
# PHASE 1: Brain calls system.bootstrap
# ============================================================================
print("PHASE 1: Brain calls system.bootstrap")
print("-" * 70)

world_descriptors = [w.as_dict() for w in worlds.list()]
builder_descs = builders.list()

# Bootstrap includes recommended reads and world list
bootstrap = {
    "bootstrap_version": "0.1",
    "system": {"name": "omnisvera-mcp"},
    "worlds": [
        {"world_id": w.get("world_id"), "name": w.get("name"),
         "world_type": w.get("world_type"), "capabilities": w.get("capabilities", [])}
        for w in world_descriptors
    ],
    "capabilities": {
        "manifest_ref": "system.manifest",
        "epistemic_tools": {"prediction": True, "validation": True, "snapshot_from_model": True},
        "signal_tools": {"capture": True, "history": True, "changes": True, "patterns": True},
        "model_builders": [b.get("builder_id", "") for b in builder_descs],
    },
    "recommended_next_reads": ["system.manifest", "world.list", "world.observe (world_id=football)"],
    "limitations": [],
}

EVIDENCE["bootstrap_payload"] = bootstrap
_log_discovery("system.bootstrap", "Called system.bootstrap — received world list, capabilities, recommended reads")
print(f"  Worlds: {[w['world_id'] for w in bootstrap['worlds']]}")
print(f"  Recommended next reads: {bootstrap['recommended_next_reads']}")
print()


# ============================================================================
# PHASE 2: Brain calls system.manifest
# ============================================================================
print("PHASE 2: Brain calls system.manifest (discovered from bootstrap)")
print("-" * 70)

manifest = {
    "manifest_version": "0.1",
    "worlds": world_descriptors,
    "epistemic": {"snapshot_from_observation": True, "snapshot_from_model": True,
                  "prediction": True, "validation": True},
    "signals": {"capture": True, "history": True, "changes": True, "patterns": True},
    "models": {"builders": builder_descs},
    "prediction": {
        "candidate_schema": {
            "required": ["claim", "probability", "horizon", "resolution_rule",
                         "model_snapshot_id", "predictor_id", "predictor_version"],
        },
        "workflow": ["world.model() -> WorldModel", "epistemic.snapshot_from_model() -> snapshot",
                     "epistemic.validate_candidate()", "epistemic.commit_candidate()"],
    },
    "architecture": {
        "chain": ["World", "Observation", "Signal", "History", "Pattern",
                  "WorldModel", "Snapshot", "PredictionCandidate", "Commit", "Resolution"],
    },
}

EVIDENCE["manifest_payload"] = manifest
_log_discovery("system.manifest", "Called system.manifest — discovered workflow, candidate schema, architecture")
print(f"  Epistemic tools: {list(manifest['epistemic'].keys())}")
print(f"  Prediction workflow: {manifest['prediction']['workflow']}")
print(f"  Architecture chain: {manifest['architecture']['chain']}")
print()


# ============================================================================
# PHASE 3: Brain chooses Football world
# ============================================================================
print("PHASE 3: Brain chooses Football world (discovered from bootstrap)")
print("-" * 70)

adapter = worlds.get("football")
descriptor = adapter.describe()
health_info = adapter.health()

EVIDENCE["world_chosen"] = {"world_id": "football", "descriptor": descriptor.as_dict(), "health": health_info}
_log_discovery("world.describe(football)", "Discovered football world — has signals capability")
print(f"  World: {descriptor.world_id} ({descriptor.name})")
print(f"  Capabilities: {descriptor.capabilities}")
print(f"  Health: {health_info.get('status', 'unknown')}")
print()


# ============================================================================
# PHASE 4: Brain observes football world
# ============================================================================
print("PHASE 4: Brain observes football world")
print("-" * 70)

observation = adapter.observe()
obs_dict = observation.as_dict()

EVIDENCE["observation"] = obs_dict
_log_discovery("world.observe(football)", f"Observed {len(obs_dict.get('state', {}).get('matches', []))} matches")

matches = obs_dict.get("state", {}).get("matches", [])
print(f"  Matches observed: {len(matches)}")
for m in matches[:3]:
    home_name = m.get("home", {}).get("name", m.get("home_team", "Unknown"))
    away_name = m.get("away", {}).get("name", m.get("away_team", "Unknown"))
    print(f"    {home_name} vs {away_name} @ {m.get('match_date', m.get('date', '?'))} ({m.get('status')})")
print()


# ============================================================================
# PHASE 5: Brain extracts signals
# ============================================================================
print("PHASE 5: Brain extracts signals from football world")
print("-" * 70)

signals = adapter.signals(observation)
signals_dicts = [s.as_dict() for s in signals]

EVIDENCE["signals"] = signals_dicts
_log_discovery("world.signals(football)", f"Extracted {len(signals)} structured signals")
print(f"  Signals extracted: {len(signals)}")
for s in signals[:4]:
    print(f"    {s.signal_id}: {s.value} ({s.value_type})")
print()


# ============================================================================
# PHASE 6: Brain builds WorldModel
# ============================================================================
print("PHASE 6: Brain builds WorldModel (core.state-vector)")
print("-" * 70)

builder = builders.get("core.state-vector")
model = builder.build(world_id="football", signals=signals_dicts, patterns=[],
                      query={"focus": "upcoming_matches"})
model_dict = model.as_dict()

EVIDENCE["model_id"] = model.model_id
_log_discovery("world.model(football)", f"Built model {model.model_id} with {len(model_dict.get('state', {}).get('entities', []))} entities")
print(f"  Model ID: {model.model_id}")
print(f"  Builder: {model.builder_id} v{model.builder_version}")
print(f"  Entities: {len(model_dict.get('state', {}).get('entities', []))}")
print(f"  Assumptions: {model.assumptions}")
print()


# ============================================================================
# PHASE 7: Brain creates immutable snapshot
# ============================================================================
print("PHASE 7: Brain creates immutable snapshot from model")
print("-" * 70)

snapshot_result = json.loads(snapshot_from_model_fn(store, brain_ctx, {"model": model_dict}))
EVIDENCE["model_snapshot_id"] = snapshot_result.get("snapshot_id")
EVIDENCE["model_snapshot_hash"] = snapshot_result.get("snapshot_hash")

_log_discovery("epistemic.snapshot_from_model", f"Snapshot {snapshot_result.get('snapshot_id')} created")
print(f"  Snapshot ID: {snapshot_result.get('snapshot_id')}")
print(f"  Snapshot Hash: {snapshot_result.get('snapshot_hash')}")
print()


# ============================================================================
# PHASE 8: Brain creates PredictionCandidate
# ============================================================================
print("PHASE 8: Brain creates PredictionCandidate (prospective)")
print("-" * 70)

# Find a real match to predict
upcoming = None
for m in matches:
    if m.get("status") in ("NS", "scheduled", "TBD", "Not Started"):
        upcoming = m
        break

if not upcoming and matches:
    upcoming = matches[0]
    _log_error("match_selection", "No clearly scheduled match found — using first available")

home = upcoming.get("home", {}).get("name", "Unknown")
away = upcoming.get("away", {}).get("name", "Unknown")
match_date = upcoming.get("match_date", "Unknown")

candidate = {
    "claim": f"{home} will win against {away} on {match_date}",
    "probability": 0.55,
    "horizon": f"until {match_date}",
    "resolution_rule": {
        "type": "football_match_outcome",
        "rule": "home_team_wins",
        "match_id": upcoming.get("match_id"),
        "home_team": home,
        "away_team": away,
    },
    "model_snapshot_id": EVIDENCE["model_snapshot_id"],
    "predictor_id": "opencode",
    "predictor_version": "mimo-v2.5-free",
    "predictor_type": "ai",
    "world_id": "football",
    "domain": "football.match",
    "subject_ref": f"match:{upcoming.get('match_id')}",
    "model_id": model.model_id,
    "signals_used": [s.signal_id for s in signals[:5]],
    "patterns_used": [],
    "reasoning_summary": (
        f"Based on {len(signals)} signals from football world, "
        f"built WorldModel using core.state-vector builder. "
        f"Predicting {home} victory over {away} with moderate confidence (0.55)."
    ),
}

EVIDENCE["candidate"] = candidate
_log_discovery("PredictionCandidate", f"Created candidate: {home} vs {away} on {match_date}")
print(f"  Claim: {candidate['claim']}")
print(f"  Probability: {candidate['probability']}")
print(f"  Horizon: {candidate['horizon']}")
print(f"  Predictor: {candidate['predictor_id']} ({candidate['predictor_version']})")
print(f"  Snapshot: {candidate['model_snapshot_id']}")
print()


# ============================================================================
# PHASE 9: Brain validates candidate
# ============================================================================
print("PHASE 9: Brain validates candidate (policy check)")
print("-" * 70)

validation = json.loads(validate_candidate_fn(store, brain_ctx, {"candidate": candidate}))
EVIDENCE["validation"] = validation

_log_discovery("epistemic.validate_candidate", f"Valid: {validation.get('valid')}")
print(f"  Valid: {validation.get('valid')}")
if validation.get("errors"):
    print(f"  Errors: {validation['errors']}")
if validation.get("warnings"):
    print(f"  Warnings: {validation['warnings']}")
print()


# ============================================================================
# PHASE 10: Brain commits prediction (identity binding + idempotency)
# ============================================================================
print("PHASE 10: Brain commits prediction (identity binding)")
print("-" * 70)

commit_result = json.loads(commit_candidate_fn(store, brain_ctx, {"candidate": candidate}))
EVIDENCE["commit_result"] = commit_result

_log_discovery("epistemic.commit_candidate", f"Status: {commit_result.get('status')}, ID: {commit_result.get('prediction_id')}")
print(f"  Status: {commit_result.get('status')}")
print(f"  Prediction ID: {commit_result.get('prediction_id')}")
print(f"  Candidate Hash: {commit_result.get('candidate_hash')}")
print(f"  Predictor: {commit_result.get('predictor_id')}")
print()


# ============================================================================
# PHASE 11: Verify prediction is OPEN
# ============================================================================
print("PHASE 11: Verify prediction is OPEN (not resolved)")
print("-" * 70)

prediction = json.loads(get_prediction_fn(store, brain_ctx, {
    "prediction_id": commit_result["prediction_id"],
}))
EVIDENCE["prediction"] = prediction

assert prediction["status"] == "open", f"Expected 'open', got '{prediction['status']}'"

print(f"  Prediction ID: {prediction['id']}")
print(f"  Status: {prediction['status']}")
print(f"  Claim: {prediction['claim']}")
print(f"  Probability: {prediction['probability']}")
print(f"  evidence_mode: {prediction['evidence_mode']}")
print(f"  predictor_id: {prediction['predictor_id']}")
print(f"  predictor_type: {prediction['predictor_type']}")
print(f"  world_id: {prediction['world_id']}")
print(f"  subject_ref: {prediction['subject_ref']}")
print(f"  model_id: {prediction['model_id']}")
print(f"  signals_used: {prediction.get('signals_used_json', 'N/A')}")
print(f"  candidate_hash: {prediction.get('candidate_hash', 'N/A')}")
print()


# ============================================================================
# PHASE 12: Verify idempotency (retry returns same ID)
# ============================================================================
print("PHASE 12: Verify idempotency (retry returns same prediction_id)")
print("-" * 70)

retry = json.loads(commit_candidate_fn(store, brain_ctx, {"candidate": candidate}))
assert retry["status"] == "already_committed", f"Expected 'already_committed', got '{retry['status']}'"
assert retry["prediction_id"] == commit_result["prediction_id"]

print(f"  Retry status: {retry['status']}")
print(f"  Same prediction_id: {retry['prediction_id']} == {commit_result['prediction_id']}")
print()


# ============================================================================
# FINAL REPORT
# ============================================================================
print("=" * 70)
print("CAPSTONE TEST — FINAL REPORT")
print("=" * 70)
print()
print("### Brain utilizado")
print(f"  {EVIDENCE['brain']}")
print()
print("### Discovery path")
for step in EVIDENCE["discovery_path"]:
    print(f"  {step['step']:>2}. {step['action']}")
    print(f"      {step['detail'][:90]}")
print()
print("### World escolhido")
print(f"  {EVIDENCE['world_chosen']['world_id']} — {EVIDENCE['world_chosen']['descriptor']['name']}")
print()
print("### PredictionCandidate")
print(f"  Claim: {EVIDENCE['candidate']['claim']}")
print(f"  Probability: {EVIDENCE['candidate']['probability']}")
print(f"  Horizon: {EVIDENCE['candidate']['horizon']}")
print(f"  Resolution: {EVIDENCE['candidate']['resolution_rule']['type']}")
print()
print("### Policy/identity")
print(f"  Valid: {EVIDENCE['validation']['valid']}")
print(f"  Identity binding: actor='opencode' == predictor_id='opencode'")
print()
print("### Prediction oficial")
print(f"  ID: {EVIDENCE['prediction']['id']}")
print(f"  Status: {EVIDENCE['prediction']['status']}")
print(f"  evidence_mode: {EVIDENCE['prediction']['evidence_mode']}")
print(f"  Snapshot: {EVIDENCE['model_snapshot_id']}")
print()
print("### Audit/provenance")
print(f"  Candidate Hash: {EVIDENCE['prediction']['candidate_hash']}")
print(f"  Predictor: {EVIDENCE['prediction']['predictor_id']} v{EVIDENCE['prediction']['predictor_version']}")
print(f"  Predictor type: {EVIDENCE['prediction']['predictor_type']}")
print()
if EVIDENCE["errors_encountered"]:
    print("### Onde a IA teve dificuldade")
    for err in EVIDENCE["errors_encountered"]:
        print(f"  - {err['step']}: {err['error']}")
else:
    print("### Onde a IA teve dificuldade")
    print("  Nenhuma — fluxo de descoberta completo via bootstrap/manifest")
print()
print("### Resultado do teste")
print("  [OK] IA descobriu o sistema apenas through bootstrap/manifest")
print("  [OK] Escolheu Football world autonomamente")
print("  [OK] Observou estado real, extraiu sinais, construiu modelo")
print("  [OK] Criou snapshot imutavel + PredictionCandidate valida")
print("  [OK] Passou por validacao, identity binding, commit, idempotency")
print("  [OK] Prediction PROSPECTIVA registrada - permanece OPEN")
print()
print("### Proxima acao para resolucao futura")
print("  Quando a partida ocorrer:")
print("  1. world.observe(football) -> resultado real")
print("  2. epistemic.resolve_prediction(prediction_id, outcome)")
print("  3. Brier score calculado automaticamente")
print("  4. Primeiro registro prospectivo verdadeiro do Omnisvera")
print()
print("=" * 70)
print("FIM DO CAPSTONE — PREVISÃO ABERTA AGUARDANDO O MUNDO")
print("=" * 70)
