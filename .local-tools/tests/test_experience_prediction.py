"""Experience-Aware Prediction v0.1 — Tests A-H + Acceptance."""
from __future__ import annotations

import json
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
from omnisvera_mcp.core.context import CallContext
from omnisvera_mcp.epistemic import validate_candidate, commit_candidate
from omnisvera_mcp.experience.football_elo import FootballEloUpdater

def _tmp_store() -> MemoryStore:
    return MemoryStore(Path(tempfile.mkdtemp()) / "pred.db")

def _make_snapshot(mem: MemoryStore, domain="football") -> str:
    return mem.create_snapshot_memory(domain=domain, subject="match:TSDB-1", state={"x": 1})

def _make_exp(mem: MemoryStore, world_id="football", pid="football.elo", pver="v1"):
    return mem.experience_create(world_id=world_id, predictor_id=pid, predictor_version=pver, predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500, "CHE": 1500}})

class ExperiencePredictionTests(unittest.TestCase):

    def test_A_valid_experience(self):
        """A) candidate com Experience válida."""
        mem = _tmp_store()
        exp = _make_exp(mem)
        snap = _make_snapshot(mem)
        cand = {
            "world_id": "football", "domain": "football", "subject_ref": "ARS vs CHE",
            "claim": "ARS beats CHE", "probability": 0.6, "horizon": "2099-01-01T00:00:00+00:00",
            "resolution_rule": {"type": "home_win"}, "model_snapshot_id": snap, "predictor_id": "football.elo", "predictor_version": "v1",
            "experience_id": exp["experience_id"], "experience_state_version": exp["state_version"], "experience_state_hash": exp["learned_state_hash"],
        }
        ctx = CallContext.trusted_local_stdio()
        val = json.loads(validate_candidate(mem, ctx, {"candidate": cand}))
        self.assertTrue(val["valid"], val["errors"])
        self.assertTrue(val["experience"]["referenced"])
        self.assertTrue(val["experience"]["integrity_ok"])
        self.assertTrue(val["experience"]["is_latest"])
        # commit should persist
        raw = commit_candidate(mem, ctx, {"candidate": cand})
        j = json.loads(raw)
        self.assertEqual(j["status"], "created")
        pred = mem.get_prediction(j["prediction_id"])
        self.assertEqual(pred["experience_id"], exp["experience_id"])
        self.assertEqual(pred["experience_state_version"], 1)

    def test_B_wrong_world(self):
        """B) wrong world rejeitado."""
        mem = _tmp_store()
        exp = _make_exp(mem, world_id="football")
        snap = _make_snapshot(mem, domain="crypto")
        cand = {
            "world_id": "crypto", "domain": "crypto", "claim": "btc up", "probability": 0.5, "horizon": "2099-01-01T00:00:00+00:00",
            "resolution_rule": {"type": "t"}, "model_snapshot_id": snap, "predictor_id": "football.elo", "predictor_version": "v1",
            "experience_id": exp["experience_id"], "experience_state_version": exp["state_version"], "experience_state_hash": exp["learned_state_hash"],
        }
        ctx = CallContext.trusted_local_stdio()
        val = json.loads(validate_candidate(mem, ctx, {"candidate": cand}))
        self.assertFalse(val["valid"])
        self.assertTrue(any("world mismatch" in e for e in val["errors"]))

    def test_C_wrong_predictor(self):
        """C) wrong predictor rejeitado."""
        mem = _tmp_store()
        exp = _make_exp(mem, pid="football.elo", pver="v1")
        snap = _make_snapshot(mem)
        cand = {
            "world_id": "football", "domain": "football", "claim": "c", "probability": 0.5, "horizon": "2099-01-01T00:00:00+00:00",
            "resolution_rule": {"type": "t"}, "model_snapshot_id": snap, "predictor_id": "other.predictor", "predictor_version": "v1",
            "experience_id": exp["experience_id"], "experience_state_version": exp["state_version"], "experience_state_hash": exp["learned_state_hash"],
        }
        val = json.loads(validate_candidate(mem, CallContext.trusted_local_stdio(), {"candidate": cand}))
        self.assertFalse(val["valid"])
        self.assertTrue(any("predictor_id mismatch" in e for e in val["errors"]))

    def test_D_wrong_hash(self):
        """D) wrong hash rejeitado."""
        mem = _tmp_store()
        exp = _make_exp(mem)
        snap = _make_snapshot(mem)
        cand = {
            "world_id": "football", "domain": "football", "claim": "c", "probability": 0.5, "horizon": "2099-01-01T00:00:00+00:00",
            "resolution_rule": {"type": "t"}, "model_snapshot_id": snap, "predictor_id": "football.elo", "predictor_version": "v1",
            "experience_id": exp["experience_id"], "experience_state_version": exp["state_version"], "experience_state_hash": "badhash123",
        }
        val = json.loads(validate_candidate(mem, CallContext.trusted_local_stdio(), {"candidate": cand}))
        self.assertFalse(val["valid"])
        self.assertTrue(any("hash mismatch" in e for e in val["errors"]))

    def test_E_historical_version(self):
        """E) historical version aceita + is_latest false."""
        mem = _tmp_store()
        v1 = _make_exp(mem)
        # create v2 to make v1 historical
        mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1510}})
        snap = _make_snapshot(mem)
        cand = {
            "world_id": "football", "domain": "football", "claim": "c", "probability": 0.5, "horizon": "2099-01-01T00:00:00+00:00",
            "resolution_rule": {"type": "t"}, "model_snapshot_id": snap, "predictor_id": "football.elo", "predictor_version": "v1",
            "experience_id": v1["experience_id"], "experience_state_version": v1["state_version"], "experience_state_hash": v1["learned_state_hash"],
        }
        val = json.loads(validate_candidate(mem, CallContext.trusted_local_stdio(), {"candidate": cand}))
        self.assertTrue(val["valid"], val["errors"])
        self.assertFalse(val["experience"]["is_latest"])
        self.assertEqual(val["experience"]["state_version"], 1)
        # commit should succeed with historical
        raw = commit_candidate(mem, CallContext.trusted_local_stdio(), {"candidate": cand})
        j = json.loads(raw)
        self.assertEqual(j["status"], "created")
        pred = mem.get_prediction(j["prediction_id"])
        self.assertEqual(pred["experience_state_version"], 1)

    def test_F_prediction_immutable(self):
        """F) prediction imutável após Experience avançar."""
        mem = _tmp_store()
        v1 = _make_exp(mem)
        snap = _make_snapshot(mem)
        cand = {
            "world_id": "football", "domain": "football", "claim": "c", "probability": 0.6, "horizon": "2099-01-01T00:00:00+00:00",
            "resolution_rule": {"type": "t"}, "model_snapshot_id": snap, "predictor_id": "football.elo", "predictor_version": "v1",
            "experience_id": v1["experience_id"], "experience_state_version": v1["state_version"], "experience_state_hash": v1["learned_state_hash"],
        }
        j = json.loads(commit_candidate(mem, CallContext.trusted_local_stdio(), {"candidate": cand}))
        pred_id = j["prediction_id"]
        # advance experience to v2
        mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1600}})
        pred = mem.get_prediction(pred_id)
        self.assertEqual(pred["experience_state_version"], 1)
        self.assertEqual(pred["experience_id"], v1["experience_id"])

    def test_G_restart_handoff(self):
        """G) AI/process restart: A cria v1 → B recupera → predicts → outcome → v2."""
        tmp = Path(tempfile.mkdtemp()) / "restart_pred.db"
        memA = MemoryStore(tmp)
        v1 = memA.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500, "CHE": 1500}})
        v1_hash = v1["learned_state_hash"]
        v1_id = v1["experience_id"]
        # Simulate process A exit, B starts
        memB = MemoryStore(tmp)
        latest = memB.experience_latest("football", "football.elo", "v1")
        self.assertIsNotNone(latest)
        self.assertEqual(latest["experience_id"], v1_id)
        self.assertEqual(latest["learned_state_hash"], v1_hash)
        # B uses learned_state to produce candidate
        snap = memB.create_snapshot_memory(domain="football", subject="ARS vs CHE", state=latest["learned_state"])
        cand = {
            "world_id": "football", "domain": "football", "subject_ref": "ARS vs CHE",
            "claim": "ARS beats CHE", "probability": 0.6, "horizon": "2099-01-01T00:00:00+00:00",
            "resolution_rule": {"type": "home_win"}, "model_snapshot_id": snap, "predictor_id": "football.elo", "predictor_version": "v1",
            "experience_id": latest["experience_id"], "experience_state_version": latest["state_version"], "experience_state_hash": latest["learned_state_hash"],
        }
        ctx = CallContext.trusted_local_stdio()
        # attach registry for auto update
        from omnisvera_mcp.experience.updater import ExperienceUpdaterRegistry
        from omnisvera_mcp.experience.football_elo import FootballEloUpdater
        reg = ExperienceUpdaterRegistry()
        reg.register(FootballEloUpdater())
        memB._experience_updater_registry = reg  # type: ignore
        j = json.loads(commit_candidate(memB, ctx, {"candidate": cand}))
        pred_id = j["prediction_id"]
        # resolve
        from omnisvera_mcp.epistemic import resolve_prediction
        resolve_prediction(memB, ctx, {"prediction_id": str(pred_id), "outcome": 1})
        # runtime should have created v2 automatically
        latest2 = memB.experience_latest("football", "football.elo", "v1")
        self.assertEqual(latest2["state_version"], 2)
        self.assertNotEqual(latest2["learned_state"]["team_ratings"]["ARS"], 1500)
        # lineage: prediction still points to v1
        pred = memB.get_prediction(pred_id)
        self.assertEqual(pred["experience_state_version"], 1)
        # v2 provenance includes trigger
        self.assertIn(pred_id, latest2["source_prediction_ids"])

    def test_H_stateless_predictor(self):
        """H) stateless predictor continua sem Experience."""
        mem = _tmp_store()
        snap = _make_snapshot(mem)
        cand = {
            "world_id": "football", "domain": "football", "claim": "stateless", "probability": 0.5, "horizon": "2099-01-01T00:00:00+00:00",
            "resolution_rule": {"type": "t"}, "model_snapshot_id": snap, "predictor_id": "baseline.fixed", "predictor_version": "v1",
        }
        ctx = CallContext.trusted_local_stdio()
        val = json.loads(validate_candidate(mem, ctx, {"candidate": cand}))
        self.assertTrue(val["valid"], val["errors"])
        self.assertFalse(val["experience"]["referenced"])
        raw = commit_candidate(mem, ctx, {"candidate": cand})
        j = json.loads(raw)
        self.assertEqual(j["status"], "created")
        pred = mem.get_prediction(j["prediction_id"])
        self.assertIsNone(pred["experience_id"])

    def test_external_AI(self):
        """External AI scenario."""
        mem = _tmp_store()
        v1 = mem.experience_create(world_id="football", predictor_id="external.agent", predictor_version="1", predictor_type="external", learned_state_schema="ext.v1", learned_state={"s": 1})
        snap = _make_snapshot(mem)
        cand = {
            "world_id": "football", "domain": "football", "claim": "external", "probability": 0.7, "horizon": "2099-01-01T00:00:00+00:00",
            "resolution_rule": {"type": "t"}, "model_snapshot_id": snap, "predictor_id": "external.agent", "predictor_version": "1",
            "experience_id": v1["experience_id"], "experience_state_version": v1["state_version"], "experience_state_hash": v1["learned_state_hash"],
        }
        val = json.loads(validate_candidate(mem, CallContext.trusted_local_stdio(), {"candidate": cand}))
        self.assertTrue(val["valid"])
        # commit works without knowing model internals
        j = json.loads(commit_candidate(mem, CallContext.trusted_local_stdio(), {"candidate": cand}))
        self.assertEqual(j["status"], "created")

    def test_acceptance_lineage(self):
        """Acceptance: football.elo v1 ARS=1500 CHE=1500 → restart → prediction → ARS win → v2 lineage."""
        tmp = Path(tempfile.mkdtemp()) / "accept_lineage.db"
        memA = MemoryStore(tmp)
        v1 = memA.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {"ARS": 1500, "CHE": 1500}, "home_advantage": 50})
        # Simulate process A exit
        memB = MemoryStore(tmp)
        from omnisvera_mcp.experience.updater import ExperienceUpdaterRegistry
        from omnisvera_mcp.experience.football_elo import FootballEloUpdater
        reg = ExperienceUpdaterRegistry()
        reg.register(FootballEloUpdater())
        memB._experience_updater_registry = reg  # type: ignore
        latest = memB.experience_latest("football", "football.elo", "v1")
        snap = memB.create_snapshot_memory(domain="football", subject="ARS vs CHE", state=latest["learned_state"])
        cand = {
            "world_id": "football", "domain": "football", "subject_ref": "ARS vs CHE",
            "claim": "ARS beats CHE", "probability": 0.62, "horizon": "2099-01-01T00:00:00+00:00",
            "resolution_rule": {"type": "home_win"}, "model_snapshot_id": snap, "predictor_id": "football.elo", "predictor_version": "v1",
            "experience_id": latest["experience_id"], "experience_state_version": latest["state_version"], "experience_state_hash": latest["learned_state_hash"],
        }
        ctx = CallContext.trusted_local_stdio()
        pred_id = json.loads(commit_candidate(memB, ctx, {"candidate": cand}))["prediction_id"]
        # Resolve
        from omnisvera_mcp.epistemic import resolve_prediction
        resolve_prediction(memB, ctx, {"prediction_id": str(pred_id), "outcome": 1})
        v2 = memB.experience_latest("football", "football.elo", "v1")
        # lineage checks
        self.assertEqual(v2["state_version"], 2)
        self.assertEqual(v2["previous_experience_id"], v1["experience_id"])
        pred = memB.get_prediction(pred_id)
        self.assertEqual(pred["experience_id"], v1["experience_id"])
        # hashes intact
        self.assertTrue(v1["integrity_ok"])
        self.assertTrue(v2["integrity_ok"])
        # performance updated
        self.assertEqual(v2["performance"]["resolved_predictions"], 1)
        # provenance includes trigger
        self.assertEqual(v2["metadata"]["trigger_prediction_id"], pred_id)
        self.assertEqual(v2["metadata"]["trigger_experience_id"], v1["experience_id"])

    def test_manifest_workflow(self):
        """Manifest documenta workflow."""
        from mcp.server.fastmcp import FastMCP
        from omnisvera_mcp.server import register_foundation_tools
        import json as _json
        mcp = FastMCP("test-manifest2")
        root = Path(tempfile.mkdtemp())
        (root / ".assistant-runtime" / "omnisvera-mcp").mkdir(parents=True, exist_ok=True)
        _, registry, _ = register_foundation_tools(mcp, root)
        from omnisvera_mcp.core.context import CallContext
        ctx = CallContext.trusted_local_stdio()
        manifest = _json.loads(registry.invoke("system.manifest", ctx, {}))
        self.assertIn("experience", manifest)
        # workflow should mention experience.latest etc via architecture chain includes Experience
        self.assertIn("Experience", manifest["architecture"]["chain"])

if __name__ == "__main__":
    unittest.main()
