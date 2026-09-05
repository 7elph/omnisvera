"""Outcome → Experience Update Runtime v0.1 — Tests A-J.

Covers durable ledger, exactly-once, retry, integrity, isolation, restart, concurrency, due resolver.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))
if str(LOCAL_TOOLS.parent) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS.parent))

from omnisvera_mcp.memory.store import MemoryStore
from omnisvera_mcp.experience.updater import ExperienceUpdater, ExperienceUpdaterRegistry, ExperienceUpdateResult
from omnisvera_mcp.experience.runtime import enqueue_and_process_for_resolution, process_pending_updates, process_experience_update_event
from omnisvera_mcp.experience.football_elo import FootballEloUpdater

def _tmp_store() -> MemoryStore:
    return MemoryStore(Path(tempfile.mkdtemp()) / "upd.db")

def _make_pred_and_resolve(mem: MemoryStore, predictor_id="football.elo", predictor_version="v1", world_id="football"):
    snap = mem.create_snapshot_memory(domain=world_id, subject="match:TSDB-1", state={"x": 1})
    pred = mem.create_prediction(domain=world_id, snapshot_memory_id=snap, claim="ARS beats CHE", probability=0.6, horizon="2099-01-01T00:00:00+00:00", resolution_rule={"type": "home_win"}, predictor_id=predictor_id, predictor_version=predictor_version, world_id=world_id)
    mem.resolve_prediction(pred, outcome=1)
    return pred

def _reg_with_football() -> ExperienceUpdaterRegistry:
    reg = ExperienceUpdaterRegistry()
    reg.register(FootballEloUpdater())
    return reg

class UpdateRuntimeTests(unittest.TestCase):

    def test_A_successful_outcome_update(self):
        """A) Experience v1 → resolution → v2."""
        mem = _tmp_store()
        reg = _reg_with_football()
        mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500, "CHE": 1500}, "home_advantage": 50})
        pred = _make_pred_and_resolve(mem)
        event = mem.experience_update_enqueue(prediction_id=pred)
        self.assertEqual(event["status"], "pending")
        # process
        result = process_experience_update_event(mem, reg, event["update_event_id"])
        self.assertEqual(result["status"], "applied")
        latest = mem.experience_latest("football", "football.elo", "v1")
        self.assertEqual(latest["state_version"], 2)
        self.assertNotEqual(latest["learned_state"]["team_ratings"]["ARS"], 1500)  # updated
        self.assertTrue(latest["integrity_ok"])
        self.assertEqual(latest["previous_state_version"], 1)

    def test_B_exactly_once(self):
        """B) mesma resolution processada 3x → somente v2."""
        mem = _tmp_store()
        reg = _reg_with_football()
        mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500}})
        pred = _make_pred_and_resolve(mem)
        ev = mem.experience_update_enqueue(prediction_id=pred)
        # process 3 times
        r1 = process_experience_update_event(mem, reg, ev["update_event_id"])
        r2 = process_experience_update_event(mem, reg, ev["update_event_id"])
        r3 = process_experience_update_event(mem, reg, ev["update_event_id"])
        self.assertEqual(r1["status"], "applied")
        self.assertEqual(r2["status"], "applied")
        self.assertEqual(r3["status"], "applied")
        hist = mem.experience_history("football", "football.elo", "v1")
        self.assertEqual(len(hist), 2)  # v1 + v2 only
        # enqueue again should not create new event
        ev2 = mem.experience_update_enqueue(prediction_id=pred)
        self.assertEqual(ev2["update_event_id"], ev["update_event_id"])

    def test_C_provenance(self):
        """C) v2 aponta para v1 + prediction + resolution + update event."""
        mem = _tmp_store()
        reg = _reg_with_football()
        v1 = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500}})
        pred = _make_pred_and_resolve(mem)
        ev = mem.experience_update_enqueue(prediction_id=pred)
        process_experience_update_event(mem, reg, ev["update_event_id"])
        v2 = mem.experience_latest("football", "football.elo", "v1")
        self.assertEqual(v2["previous_experience_id"], v1["experience_id"])
        self.assertEqual(v2["previous_state_version"], 1)
        # provenance via metadata includes trigger
        self.assertIn(pred, v2["source_prediction_ids"])
        self.assertEqual(v2["provenance"]["previous_experience_id"], v1["experience_id"])
        # update_event should be in provenance extra stored in metadata
        self.assertEqual(v2["metadata"]["trigger_prediction_id"], pred)
        # event should point to new experience
        ev_after = mem.experience_update_get(ev["update_event_id"])
        self.assertEqual(ev_after["applied_experience_id"], v2["experience_id"])
        self.assertEqual(ev_after["applied_state_version"], 2)

    def test_D_no_updater(self):
        """D) resolution válida + NO_UPDATER."""
        mem = _tmp_store()
        reg = ExperienceUpdaterRegistry()  # empty, no football updater
        # create an experience for external predictor (so not missing)
        mem.experience_create(world_id="football", predictor_id="external.test", predictor_version="v1", predictor_type="external", learned_state_schema="ext.v1", learned_state={"x": 1})
        # prediction with external predictor
        snap = mem.create_snapshot_memory(domain="football", subject="x", state={})
        pred = mem.create_prediction(domain="football", snapshot_memory_id=snap, claim="c", probability=0.5, horizon="2099-01-01T00:00:00+00:00", resolution_rule={}, predictor_id="external.test", predictor_version="v1", world_id="football")
        mem.resolve_prediction(pred, outcome=1)
        ev = mem.experience_update_enqueue(prediction_id=pred)
        result = process_experience_update_event(mem, reg, ev["update_event_id"])
        self.assertEqual(result["status"], "no_updater")
        # resolution intact
        pred_info = mem.get_prediction(pred)
        self.assertEqual(pred_info["status"], "resolved")
        # no new experience
        hist = mem.experience_history("football", "external.test", "v1")
        self.assertEqual(len(hist), 1)  # still v1

    def test_E_missing_initial_experience(self):
        """E) sem estado inicial → missing_experience, sem inventar."""
        mem = _tmp_store()
        reg = _reg_with_football()
        # No experience created
        pred = _make_pred_and_resolve(mem)
        ev = mem.experience_update_enqueue(prediction_id=pred)
        result = process_experience_update_event(mem, reg, ev["update_event_id"])
        self.assertEqual(result["status"], "missing_experience")
        # no experience created
        latest = mem.experience_latest("football", "football.elo", "v1")
        self.assertIsNone(latest)
        # resolution still valid
        self.assertEqual(mem.get_prediction(pred)["status"], "resolved")

    def test_F_corrupted_previous_state(self):
        """F) corrupted previous state bloqueado, resolution preservada."""
        mem = _tmp_store()
        reg = _reg_with_football()
        v1 = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500}})
        # tamper
        import sqlite3, json as _json
        conn = sqlite3.connect(str(mem.path))
        conn.execute("UPDATE predictor_experiences SET learned_state_json=? WHERE experience_id=?", (_json.dumps({"team_ratings": {"ARS": 9999}}), v1["experience_id"]))
        conn.commit()
        conn.close()
        pred = _make_pred_and_resolve(mem)
        ev = mem.experience_update_enqueue(prediction_id=pred)
        result = process_experience_update_event(mem, reg, ev["update_event_id"])
        self.assertEqual(result["status"], "integrity_failed")
        # no new version
        # latest should still be the tampered v1 (but integrity fails)
        latest = mem.experience_latest("football", "football.elo", "v1")
        # latest will be fetched and show integrity false
        self.assertFalse(latest["integrity_ok"])
        # history still 1
        self.assertEqual(len(mem.experience_history("football", "football.elo", "v1")), 1)

    def test_G_updater_exception_and_retry(self):
        """G) updater exception → failed + retry."""
        mem = _tmp_store()

        class FailingUpdater(ExperienceUpdater):
            def describe(self): return {"predictor_id": "test.fail", "predictor_version": "v1", "predictor_type": "external"}
            def update(self, **kw): raise RuntimeError("boom deterministic")

        reg_fail = ExperienceUpdaterRegistry()
        reg_fail.register(FailingUpdater())
        mem.experience_create(world_id="football", predictor_id="test.fail", predictor_version="v1", predictor_type="external", learned_state_schema="s", learned_state={"x": 1})
        snap = mem.create_snapshot_memory(domain="football", subject="x", state={})
        pred = mem.create_prediction(domain="football", snapshot_memory_id=snap, claim="c", probability=0.5, horizon="2099-01-01T00:00:00+00:00", resolution_rule={}, predictor_id="test.fail", predictor_version="v1", world_id="football")
        mem.resolve_prediction(pred, outcome=1)
        ev = mem.experience_update_enqueue(prediction_id=pred)
        res1 = process_experience_update_event(mem, reg_fail, ev["update_event_id"])
        self.assertEqual(res1["status"], "failed")
        self.assertIn("boom", res1["last_error"])
        # previous experience intact
        self.assertEqual(len(mem.experience_history("football", "test.fail", "v1")), 1)
        # Now replace with working updater via store override
        class WorkingUpdater(ExperienceUpdater):
            def describe(self): return {"predictor_id": "test.fail", "predictor_version": "v1", "predictor_type": "external"}
            def update(self, previous_experience, prediction, resolution, context=None):
                from omnisvera_mcp.experience.updater import ExperienceUpdateResult
                return ExperienceUpdateResult(learned_state_schema="s", learned_state={"x": 2}, state_changed=True)
        reg_ok = ExperienceUpdaterRegistry()
        reg_ok.register(WorkingUpdater())
        # store override for retry path (simulate registry swap)
        mem._experience_updater_registry = reg_ok  # type: ignore
        res2 = process_experience_update_event(mem, reg_ok, ev["update_event_id"])
        self.assertEqual(res2["status"], "applied")
        self.assertEqual(mem.experience_latest("football", "test.fail", "v1")["state_version"], 2)
        # exactly one new version despite retry
        self.assertEqual(len(mem.experience_history("football", "test.fail", "v1")), 2)

    def test_H_restart(self):
        """H) pending sobrevive e é aplicado depois do restart."""
        tmp = Path(tempfile.mkdtemp()) / "restart.db"
        mem = MemoryStore(tmp)
        reg = _reg_with_football()
        mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500}})
        pred = _make_pred_and_resolve(mem)
        ev = mem.experience_update_enqueue(prediction_id=pred)
        # Do NOT process, simulate crash
        self.assertEqual(ev["status"], "pending")
        # Restart
        mem2 = MemoryStore(tmp)
        # process_pending should pick it up
        summary = process_pending_updates(mem2, reg, limit=20)
        self.assertEqual(summary["applied"], 1)
        latest = mem2.experience_latest("football", "football.elo", "v1")
        self.assertEqual(latest["state_version"], 2)

    def test_I_concurrent_duplicate(self):
        """I) duas tentativas simultâneas → uma única nova version."""
        mem = _tmp_store()
        reg = _reg_with_football()
        mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500}})
        pred = _make_pred_and_resolve(mem)
        ev = mem.experience_update_enqueue(prediction_id=pred)
        # Simulate concurrent: two calls to process same event (without awaiting)
        r1 = process_experience_update_event(mem, reg, ev["update_event_id"])
        r2 = process_experience_update_event(mem, reg, ev["update_event_id"])
        # Both should be applied (second is idempotent)
        self.assertEqual(r1["status"], "applied")
        self.assertEqual(r2["status"], "applied")
        # Only one new version
        hist = mem.experience_history("football", "football.elo", "v1")
        self.assertEqual(len(hist), 2)
        # Applied experience ids same
        self.assertEqual(r1["applied_experience_id"], r2["applied_experience_id"])

    def test_J_resolve_due_predictions_same_runtime(self):
        """J) resolve_due_predictions usa mesmo runtime."""
        mem = _tmp_store()
        reg = _reg_with_football()
        # Attach registry to store for epistemic to use
        mem._experience_updater_registry = reg  # type: ignore
        mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500}})
        snap = mem.create_snapshot_memory(domain="football", subject="due", state={})
        # horizon in past, with test_outcome and resolver_id to make due resolver trigger
        pred = mem.create_prediction(domain="football", snapshot_memory_id=snap, claim="due", probability=0.6, horizon="2020-01-01T00:00:00+00:00", resolution_rule={"resolver_id": "test", "test_outcome": 1}, predictor_id="football.elo", predictor_version="v1", world_id="football")
        # Now call resolve_due
        from omnisvera_mcp.epistemic import resolve_due_predictions
        from omnisvera_mcp.core.context import CallContext
        ctx = CallContext.trusted_local_stdio()
        raw = resolve_due_predictions(mem, ctx, {"limit": 10})
        import json as _json
        summary = _json.loads(raw)
        self.assertEqual(summary["resolved"], 1)
        # Experience should have been updated via same runtime
        latest = mem.experience_latest("football", "football.elo", "v1")
        self.assertEqual(latest["state_version"], 2)
        # Check that manual resolve also uses same path (already tested in A), so they converge
        # Ensure event exists and is applied
        ev = mem.experience_update_get_by_prediction(pred)
        self.assertIsNotNone(ev)
        self.assertEqual(ev["status"], "applied")

    def test_acceptance_football(self):
        """Acceptance: Experience v1 ARS=1500 CHE=1500 → prediction → ARS vence → v2 rating atualizado, hash íntegro, restart."""
        tmp = Path(tempfile.mkdtemp()) / "accept.db"
        mem = MemoryStore(tmp)
        reg = _reg_with_football()
        mem._experience_updater_registry = reg  # for epistemic auto path
        v1 = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500, "CHE": 1500}, "home_advantage": 50, "k_factor": 20}, observations_used=1)
        self.assertEqual(v1["state_version"], 1)
        # Prediction ARS vs CHE
        snap = mem.create_snapshot_memory(domain="football", subject="ARS vs CHE", state={"elo": v1["learned_state"]})
        pred = mem.create_prediction(domain="football", snapshot_memory_id=snap, claim="ARS beats CHE", probability=0.6, horizon="2099-01-01T00:00:00+00:00", resolution_rule={"team_home": "ARS", "team_away": "CHE"}, predictor_id="football.elo", predictor_version="v1", world_id="football", subject_ref="ARS vs CHE")
        # Resolve via epistemic path (auto update)
        from omnisvera_mcp.epistemic import resolve_prediction
        from omnisvera_mcp.core.context import CallContext
        ctx = CallContext.trusted_local_stdio()
        # Use resolve_prediction to trigger automatic update
        resolve_prediction(mem, ctx, {"prediction_id": str(pred), "outcome": 1})
        # After, latest should be v2
        latest = mem.experience_latest("football", "football.elo", "v1")
        self.assertEqual(latest["state_version"], 2)
        self.assertNotEqual(latest["learned_state"]["team_ratings"]["ARS"], 1500)
        self.assertTrue(latest["integrity_ok"])
        self.assertEqual(latest["previous_experience_id"], v1["experience_id"])
        self.assertIn(pred, latest["source_prediction_ids"])
        self.assertEqual(latest["performance"]["resolved_predictions"], 1)
        # Restart
        mem2 = MemoryStore(tmp)
        latest2 = mem2.experience_latest("football", "football.elo", "v1")
        self.assertEqual(latest2["experience_id"], latest["experience_id"])
        self.assertEqual(latest2["learned_state"], latest["learned_state"])
        self.assertTrue(latest2["integrity_ok"])
        # Check update event applied
        ev = mem2.experience_update_get_by_prediction(pred)
        self.assertEqual(ev["status"], "applied")
        self.assertEqual(ev["applied_state_version"], 2)

if __name__ == "__main__":
    unittest.main()
