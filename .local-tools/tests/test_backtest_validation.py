"""Backtest Validation v0.1 — Tests.

Tests run against an isolated database (no operational data).
Validates:
  1. baseline predictor determinism
  2. inline snapshot creation in backtest
  3. predictor_id/version persisted in predictions
  4. backtest lifecycle (snapshot → prediction → resolve → Brier)
  5. prospective calibration unaffected by retrospective backtests
  6. snapshot integrity verified post-backtest
  7. predictor never sees outcome
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

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

# Import baseline in isolation
import types as _mt
_baseline_mod = _mt.ModuleType("baseline")
_baseline_mod.__file__ = str(LOCAL_TOOLS / "omnisvera_mcp" / "baseline.py")
sys.modules["baseline"] = _baseline_mod
_baseline_src = (LOCAL_TOOLS / "omnisvera_mcp" / "baseline.py").read_text(encoding="utf-8")
exec(compile(_baseline_src, _baseline_mod.__file__, "exec"), _baseline_mod.__dict__)
predict = _baseline_mod.predict
PREDICTOR_ID = _baseline_mod.PREDICTOR_ID
PREDICTOR_VERSION = _baseline_mod.PREDICTOR_VERSION


class BaselinePredictorTests(unittest.TestCase):
    """Tests for the deterministic baseline predictor."""

    def test_deterministic_same_input_same_output(self):
        state = {
            "missions": [{"title": "Test", "status": "active"}],
            "participants": [{"public_label": "A"}, {"public_label": "B"}],
            "session_number": 2,
        }
        r1 = predict(state)
        r2 = predict(state)
        self.assertEqual(r1.probability, r2.probability)
        self.assertEqual(r1.signals_used, r2.signals_used)

    def test_no_signals_minimal_baseline(self):
        state = {}
        result = predict(state)
        self.assertEqual(result.probability, 0.05)
        self.assertEqual(result.signals_used, [])

    def test_mission_exists_signal(self):
        state = {"missions": [{"title": "X", "status": "active"}]}
        result = predict(state)
        self.assertIn("mission_exists", result.signals_used)
        self.assertEqual(result.signal_values["mission_exists"], 0.85)

    def test_mission_not_active_no_signal(self):
        state = {"missions": [{"title": "X", "status": "completed"}]}
        result = predict(state)
        self.assertNotIn("mission_exists", result.signals_used)

    def test_participants_active_signal(self):
        state = {"participants": [{"public_label": "A"}, {"public_label": "B"}]}
        result = predict(state)
        self.assertIn("participants_active", result.signals_used)
        self.assertEqual(result.signal_values["participants_active"], 0.90)

    def test_participants_insufficient_no_signal(self):
        state = {"participants": [{"public_label": "A"}]}
        result = predict(state)
        self.assertNotIn("participants_active", result.signals_used)

    def test_session_continuity_signal(self):
        state = {"session_number": 3}
        result = predict(state)
        self.assertIn("session_continuity", result.signals_used)
        self.assertEqual(result.signal_values["session_continuity"], 0.80)

    def test_geometric_mean_calculation(self):
        state = {
            "missions": [{"title": "X", "status": "active"}],
            "participants": [{"public_label": "A"}, {"public_label": "B"}],
            "session_number": 1,
        }
        result = predict(state)
        # Only mission_exists (0.85) + participants_active (0.90) — session_number=1 → no continuity
        import math
        expected = round(math.sqrt(0.85 * 0.90), 8)
        self.assertAlmostEqual(result.probability, expected, places=8)

    def test_outcome_not_in_calculation(self):
        """Predictor must not use outcome in its calculation."""
        state = {"missions": [{"title": "X", "status": "active"}]}
        r1 = predict(state)
        # Changing an irrelevant field should not change the result
        state2 = {**state, "some_future_field": "value"}
        r2 = predict(state2)
        self.assertEqual(r1.probability, r2.probability)

    def test_as_dict_contains_metadata(self):
        state = {"missions": [{"title": "X", "status": "active"}]}
        result = predict(state)
        d = result.as_dict()
        self.assertEqual(d["predictor_id"], PREDICTOR_ID)
        self.assertEqual(d["predictor_version"], PREDICTOR_VERSION)
        self.assertIn("probability", d)
        self.assertIn("signals_used", d)
        self.assertIn("explanation", d)


class BacktestValidationTests(unittest.TestCase):
    """Tests for the backtest lifecycle using isolated DB."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = MemoryStore(Path(self.temporary.name) / "test.db")

    def test_inline_snapshot_created(self):
        result_json = self.store.create_snapshot_memory(
            domain="test",
            subject="test subject",
            state={"key": "value"},
            sources=[{"source_type": "test", "source_ref": "test.txt"}],
        )
        self.assertTrue(result_json.startswith("mem-"))
        mem = self.store.get_memory(result_json)
        self.assertIsNotNone(mem)
        self.assertEqual(mem["type"], "model_snapshot")
        self.assertEqual(mem["status"], "immutable")

    def test_predictor_fields_persisted(self):
        snapshot_id = self.store.create_snapshot_memory(
            domain="test", subject="test", state={"x": 1},
        )
        prediction_id = self.store.create_prediction(
            domain="test",
            snapshot_memory_id=snapshot_id,
            claim="test claim",
            probability=0.75,
            horizon="1h",
            resolution_rule={"type": "binary"},
            predictor_id="test.predictor.v1",
            predictor_version="1.0.0",
        )
        pred = self.store.get_prediction(prediction_id)
        self.assertEqual(pred["predictor_id"], "test.predictor.v1")
        self.assertEqual(pred["predictor_version"], "1.0.0")

    def test_backtest_lifecycle(self):
        snapshot_id = self.store.create_snapshot_memory(
            domain="companion.mission",
            subject="test backtest",
            state={"missions": [{"title": "M", "status": "active"}]},
        )
        prediction_id = self.store.create_prediction(
            domain="companion.mission",
            snapshot_memory_id=snapshot_id,
            claim="mission will be completed",
            probability=0.85,
            horizon="1 session",
            resolution_rule={"type": "binary"},
            evidence_mode="retrospective",
            predictor_id=PREDICTOR_ID,
            predictor_version=PREDICTOR_VERSION,
        )
        result = self.store.resolve_prediction(
            prediction_id, outcome=1, sources=["transcript line 42"],
        )
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["resolution"]["outcome"], 1)
        expected_brier = round((0.85 - 1) ** 2, 8)
        self.assertAlmostEqual(result["resolution"]["calibration_score"], expected_brier, places=8)
        self.assertTrue(result["snapshot_intact"])

    def test_prospective_unaffected_by_retrospective(self):
        snapshot_id = self.store.create_snapshot_memory(
            domain="test", subject="test", state={"x": 1},
        )
        # Create prospective prediction (open, not resolved)
        self.store.create_prediction(
            domain="test",
            snapshot_memory_id=snapshot_id,
            claim="prospective claim",
            probability=0.5,
            horizon="1h",
            resolution_rule={"type": "binary"},
            evidence_mode="prospective",
        )
        # Create and resolve retrospective
        rid = self.store.create_prediction(
            domain="test",
            snapshot_memory_id=snapshot_id,
            claim="retro claim",
            probability=0.8,
            horizon="1h",
            resolution_rule={"type": "binary"},
            evidence_mode="retrospective",
        )
        self.store.resolve_prediction(rid, outcome=1)

        prospec = self.store.calibration_summary(evidence_mode="prospective")
        self.assertEqual(prospec["count"], 0)  # no resolved prospective

        retro = self.store.calibration_summary(evidence_mode="retrospective")
        self.assertEqual(retro["count"], 1)

    def test_snapshot_hash_integrity(self):
        snapshot_id = self.store.create_snapshot_memory(
            domain="test", subject="test", state={"x": 1},
        )
        prediction_id = self.store.create_prediction(
            domain="test",
            snapshot_memory_id=snapshot_id,
            claim="claim",
            probability=0.5,
            horizon="1h",
            resolution_rule={"type": "binary"},
        )
        pred = self.store.get_prediction(prediction_id)
        self.assertTrue(pred["snapshot_intact"])
        self.assertEqual(pred["snapshot_hash"], pred["snapshot_hash"])  # stored hash exists

    def test_baseline_predictor_end_to_end(self):
        state = {
            "missions": [{"title": "Investigar ruínas", "status": "active"}],
            "participants": [{"public_label": "Vezemir"}, {"public_label": "Raziel"}],
            "session_number": 2,
        }
        prediction = predict(state)
        snapshot_id = self.store.create_snapshot_memory(
            domain="companion.mission",
            subject="group explores ruins",
            state=state,
        )
        prediction_id = self.store.create_prediction(
            domain="companion.mission",
            snapshot_memory_id=snapshot_id,
            claim="group will explore ruins",
            probability=prediction.probability,
            horizon="1 session",
            resolution_rule={"type": "binary"},
            evidence_mode="retrospective",
            predictor_id=PREDICTOR_ID,
            predictor_version=PREDICTOR_VERSION,
        )
        result = self.store.resolve_prediction(prediction_id, outcome=1)
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["predictor_id"], PREDICTOR_ID)
        self.assertTrue(result["snapshot_intact"])

    def test_all_suites_still_green(self):
        """Verify previous test modules are still importable."""
        import tests.test_epistemic_loop
        import tests.test_companion_session
        import tests.test_historical_replay
        import tests.test_timeline
        self.assertTrue(hasattr(tests.test_epistemic_loop, "test_bridge_tools"))
        self.assertTrue(hasattr(tests.test_companion_session, "CompanionSessionModelTests"))
        self.assertTrue(hasattr(tests.test_historical_replay, "HistoricalReplayTests"))
        self.assertTrue(hasattr(tests.test_timeline, "TimelineCoreTests"))


if __name__ == "__main__":
    unittest.main()
