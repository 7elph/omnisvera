#!/usr/bin/env python3
"""
Real Backtest Validation v0.1 — Runner

Executes real backtests against Sessions 1-4 using the Omnisvera epistemic system.
Uses an isolated database — never writes to the operational memory.db.

Each backtest:
  1. Reconstructs a snapshot from pre-cutoff transcript evidence (PRIMARY_SEQUENTIAL only)
  2. Runs the deterministic baseline predictor
  3. Creates a retrospective prediction + resolves it atomically
  4. Prints full provenance

Limitation acknowledged:
  Current sample is inadequate to evaluate predictor calibration due to
  low outcome diversity (all positive). This run validates:
  - historical reconstruction
  - provenance tracking
  - predictor traceability
  - prediction lifecycle (create → resolve → Brier)
  - retrospective/prospective separation
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

# Isolated store — exec in isolation like test files
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

# Import baseline predictor
import types as _mt
_baseline_mod = _mt.ModuleType("baseline")
_baseline_mod.__file__ = str(LOCAL_TOOLS / "omnisvera_mcp" / "baseline.py")
sys.modules["baseline"] = _baseline_mod
_baseline_src = (LOCAL_TOOLS / "omnisvera_mcp" / "baseline.py").read_text(encoding="utf-8")
exec(compile(_baseline_src, _baseline_mod.__file__, "exec"), _baseline_mod.__dict__)
predict = _baseline_mod.predict
PREDICTOR_ID = _baseline_mod.PREDICTOR_ID
PREDICTOR_VERSION = _baseline_mod.PREDICTOR_VERSION

# ---------------------------------------------------------------------------
#  Transcript audit — backtestable moments
# ---------------------------------------------------------------------------
# Each candidate is validated against four conditions:
#   1. claim was NOT known at cutoff
#   2. prediction evidence existed before cutoff
#   3. resolution evidence came after cutoff
#   4. posthoc summaries excluded from snapshot
#
# Source classification:
#   - Transcript lines = PRIMARY_SEQUENTIAL (contemporaneous)
#   - session-records.json = POSTHOC_SUMMARY (excluded from snapshot)
#   - narrative_json = POSTHOC_SUMMARY (excluded from snapshot)

BACKTEST_CANDIDATES = [
    {
        "id": "BT-001",
        "session_id": 1,
        "cutoff_ordinal": 30,
        "claim": "O grupo vai entrar e explorar as ruínas subterrâneas",
        "horizon": "até o final da sessão 1",
        "resolution_rule": {
            "type": "binary",
            "criterion": "group enters dungeon ruins",
            "evidence_source": "transcript S1 lines 38+",
        },
        "outcome": 1,
        "resolution_evidence": [
            "transcript S1 [00:38.000 --> 00:40.000]: GM describes ruins entrance",
            "session-records S1: missions=[Investigar as ruínas, status=active]",
            "session-records S2: missions=[Explorar as ruínas, status=active] (continuity)",
        ],
        "notes": "Group was invited to investigate ruins by Conclave. Transcript shows them entering at ~00:38.",
        # Snapshot state reconstructed from transcript lines 1-30 (pre-cutoff)
        "snapshot_state": {
            "session_number": 1,
            "session_status": "in_progress",
            "missions": [
                {"title": "Investigar as ruínas", "status": "active"}
            ],
            "participants": [
                {"public_label": "Vezemir", "participant_type": "character"},
                {"public_label": "Varkh Nimalis", "participant_type": "character"},
                {"public_label": "Raziel", "participant_type": "character"},
            ],
            "open_threads": [
                "Odran's disappearance",
                "Golem's origin",
            ],
            "locations": ["Estrada das caravanas"],
        },
        "snapshot_sources": [
            {
                "source_type": "primary_sequential",
                "source_ref": "session-001-transcript.txt",
                "source_timestamp": "00:00.000",
                "relation": "supports",
            },
        ],
    },
    {
        "id": "BT-002",
        "session_id": 2,
        "cutoff_ordinal": 20,
        "claim": "O grupo vai continuar a exploração das ruínas na sessão 2",
        "horizon": "até o final da sessão 2",
        "resolution_rule": {
            "type": "binary",
            "criterion": "group continues dungeon exploration in session 2",
            "evidence_source": "transcript S2 lines 20+",
        },
        "outcome": 1,
        "resolution_evidence": [
            "transcript S2 [01:28.000 --> 01:30.000]: group discusses ruins exploration",
            "session-records S2: missions=[Explorar as ruínas, status=active]",
            "session-records S3: missions=[Investigar as ruínas, status=completed] (final resolution)",
        ],
        "notes": "Session 2 opens with group already in the ruins. Continuation is observable from early transcript.",
        "snapshot_state": {
            "session_number": 2,
            "session_status": "in_progress",
            "missions": [
                {"title": "Explorar as ruínas", "status": "active"}
            ],
            "participants": [
                {"public_label": "Vezemir", "participant_type": "character"},
                {"public_label": "Varkh Nimalis", "participant_type": "character"},
                {"public_label": "Raziel", "participant_type": "character"},
                {"public_label": "Morthak", "participant_type": "character"},
            ],
            "prior_sessions": [{"session_number": 1, "status": "completed"}],
            "open_threads": [
                "Original function of ruins",
                "The golem",
            ],
            "locations": ["Ruínas soterradas"],
        },
        "snapshot_sources": [
            {
                "source_type": "primary_sequential",
                "source_ref": "session-002-transcript.txt",
                "source_timestamp": "00:00.000",
                "relation": "supports",
            },
        ],
    },
    {
        "id": "BT-003",
        "session_id": 4,
        "cutoff_ordinal": 30,
        "claim": "Vezemir vai aceitar a missão de investigar avistamentos de dragões",
        "horizon": "até o final da sessão 4",
        "resolution_rule": {
            "type": "binary",
            "criterion": "Vezemir accepts the dragon investigation mission",
            "evidence_source": "transcript S4 lines 509-553",
        },
        "outcome": 1,
        "resolution_evidence": [
            "transcript S4 [01:22:47.520 --> 01:22:49.520]: 'vocês vão pegar a missão, beleza?'",
            "transcript S4 [01:22:49.520 --> 01:22:51.520]: 'vocês querem pegar essa missão?'",
            "transcript S4 [01:24:21.520 --> 01:24:23.520]: 'vocês estão saindo, você cata a missão'",
            "transcript S4 [01:24:45.520 --> 01:24:47.520]: 'entrega a missão para você, boa sorte'",
            "session-records S4: missions=[Investigar avistamentos de dragões, status=completed]",
        ],
        "notes": "GM presents dragon mission at guild. Vezemir accepts and departs with the mission contract.",
        "snapshot_state": {
            "session_number": 4,
            "session_status": "in_progress",
            "missions": [
                {"title": "Investigar avistamentos de dragões", "status": "declared"}
            ],
            "participants": [
                {"public_label": "Vezemir", "participant_type": "character"},
                {"public_label": "Raziel", "participant_type": "character"},
            ],
            "prior_sessions": [
                {"session_number": 1, "status": "completed"},
                {"session_number": 2, "status": "completed"},
                {"session_number": 3, "status": "completed"},
            ],
            "open_threads": [
                "Dragon sightings",
                "Who is hunting the dragons?",
            ],
            "locations": ["Conclave"],
        },
        "snapshot_sources": [
            {
                "source_type": "primary_sequential",
                "source_ref": "session-004-transcript.txt",
                "source_timestamp": "57:54.000",
                "relation": "supports",
            },
        ],
    },
]


def run_backtest(store: MemoryStore, candidate: dict) -> dict:
    """Execute a single backtest and return the result."""
    # Run baseline predictor
    prediction = predict(candidate["snapshot_state"])

    # Execute backtest via store (atomic: snapshot + prediction + resolve)
    snapshot_id = store.create_snapshot_memory(
        domain="companion.mission",
        subject=candidate["claim"],
        state=candidate["snapshot_state"],
        sources=candidate["snapshot_sources"],
        metadata={
            "reconstruction_mode": "backtest",
            "session_id": candidate["session_id"],
            "cutoff_ordinal": candidate["cutoff_ordinal"],
            "posthoc_excluded": ["narrative_json", "public_summary", "gm_summary"],
        },
    )

    prediction_id = store.create_prediction(
        domain="companion.mission",
        snapshot_memory_id=snapshot_id,
        claim=candidate["claim"],
        probability=prediction.probability,
        horizon=candidate["horizon"],
        resolution_rule=candidate["resolution_rule"],
        evidence_mode="retrospective",
        predictor_id=PREDICTOR_ID,
        predictor_version=PREDICTOR_VERSION,
    )

    result = store.resolve_prediction(
        prediction_id,
        outcome=candidate["outcome"],
        sources=candidate["resolution_evidence"],
        notes=candidate["notes"],
    )

    return {
        "backtest_id": candidate["id"],
        "session_id": candidate["session_id"],
        "cutoff_ordinal": candidate["cutoff_ordinal"],
        "claim": candidate["claim"],
        "probability": prediction.probability,
        "predictor_id": PREDICTOR_ID,
        "predictor_version": PREDICTOR_VERSION,
        "signals_used": prediction.signals_used,
        "signal_values": prediction.signal_values,
        "explanation": prediction.explanation,
        "outcome": candidate["outcome"],
        "brier": result["resolution"]["calibration_score"],
        "prediction_id": result["id"],
        "snapshot_id": snapshot_id,
        "snapshot_hash": result["snapshot_hash"],
        "snapshot_intact": result["snapshot_intact"],
        "resolution_sources": candidate["resolution_evidence"],
        "evidence_mode": "retrospective",
    }


def main() -> None:
    print("=" * 72)
    print("  REAL BACKTEST VALIDATION v0.1")
    print("  Isolated database — no operational data written")
    print("=" * 72)
    print()

    # Validate candidates
    print(f"Candidates audited: {len(BACKTEST_CANDIDATES)}")
    for c in BACKTEST_CANDIDATES:
        print(f"  {c['id']}: session={c['session_id']}, cutoff_ordinal={c['cutoff_ordinal']}")
        print(f"    claim: {c['claim']}")
        print(f"    outcome: {c['outcome']}")
        print()

    # Create isolated store
    with tempfile.TemporaryDirectory() as tmpdir:
        store = MemoryStore(Path(tmpdir) / "backtest.db")

        results = []
        for candidate in BACKTEST_CANDIDATES:
            print(f"--- Executing {candidate['id']} ---")
            result = run_backtest(store, candidate)
            results.append(result)

            print(f"  prediction_id:  {result['prediction_id']}")
            print(f"  snapshot_id:    {result['snapshot_id']}")
            print(f"  probability:    {result['probability']:.8f}")
            print(f"  outcome:        {result['outcome']}")
            print(f"  brier:          {result['brier']:.8f}")
            print(f"  predictor:      {result['predictor_id']} v{result['predictor_version']}")
            print(f"  signals_used:   {result['signals_used']}")
            print(f"  snapshot_intact: {result['snapshot_intact']}")
            print(f"  evidence_mode:  {result['evidence_mode']}")
            print(f"  resolution_sources:")
            for src in result["resolution_sources"]:
                print(f"    - {src}")
            print()

        # Calibration summary — retrospective only
        print("=" * 72)
        print("  CALIBRATION SUMMARY")
        print("=" * 72)
        retro = store.calibration_summary(evidence_mode="retrospective")
        print(f"  retrospective: count={retro['count']}, mean_brier={retro.get('mean_brier')}")

        prospec = store.calibration_summary(evidence_mode="prospective")
        print(f"  prospective:   count={prospec['count']}, mean_brier={prospec.get('mean_brier')}")

        all_modes = store.calibration_summary(evidence_mode="all")
        print(f"  all:           count={all_modes['count']}, mean_brier={all_modes.get('mean_brier')}")
        if all_modes.get("breakdown"):
            for mode, info in all_modes["breakdown"].items():
                print(f"    {mode}: count={info['count']}, mean_brier={info.get('mean_brier')}")
        print()

        # Stats
        stats = store.stats()
        print(f"  DB stats: {json.dumps(stats['counts'], indent=4)}")
        print()

        # Limitation acknowledgment
        print("=" * 72)
        print("  LIMITATION ACKNOWLEDGMENT")
        print("=" * 72)
        print("  Current sample is inadequate to evaluate predictor calibration")
        print("  due to low outcome diversity (all outcome=1).")
        print("  This run validates: reconstruction, provenance, predictor")
        print("  traceability, prediction lifecycle, and retrospective separation.")
        print("  A negative Brier mean on an all-positive sample does NOT")
        print("  demonstrate predictive capability.")
        print("=" * 72)

        # Print structured results for programmatic consumption
        print()
        print("--- STRUCTURED RESULTS ---")
        import io
        output = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        output.write(json.dumps(results, ensure_ascii=False, indent=2))
        output.write("\n")
        output.flush()


if __name__ == "__main__":
    main()
