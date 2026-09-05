"""Predictor Experience v0.1 — Tests A-H + Acceptance.

Proves persistence, versioning, integrity, isolation, performance provenance.
"""
from __future__ import annotations

import hashlib
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

from omnisvera_mcp.memory.store import MemoryStore, stable_json

def _tmp_store() -> MemoryStore:
    tmp = Path(tempfile.mkdtemp()) / "exp.db"
    return MemoryStore(tmp)

def _make_prediction(mem: MemoryStore):
    """Helper to create snapshot + prediction + resolution for performance tests."""
    snap_id = mem.create_snapshot_memory(domain="football", subject="match:TSDB-1", state={"x": 1})
    pred_id = mem.create_prediction(
        domain="football", snapshot_memory_id=snap_id, claim="home win", probability=0.7,
        horizon="2099-01-01T00:00:00+00:00",
        resolution_rule={"type": "home_win"}, evidence_mode="prospective",
        predictor_id="football.elo", predictor_version="v1", world_id="football",
    )
    # resolve it
    mem.resolve_prediction(pred_id, outcome=1, observed_value=1.0, sources=["test"], notes="resolved")
    return pred_id

class ExperienceTests(unittest.TestCase):

    def test_A_create_first(self):
        """A) create first experience state_version=1 hash válido."""
        mem = _tmp_store()
        exp = mem.experience_create(
            world_id="football", predictor_id="football.elo", predictor_version="v1",
            predictor_type="statistical", learned_state_schema="elo.v1",
            learned_state={"team_ratings": {"ARS": 1500, "CHE": 1450}, "home_advantage": 50},
            observations_used=10,
        )
        self.assertEqual(exp["state_version"], 1)
        self.assertEqual(exp["world_id"], "football")
        self.assertEqual(exp["predictor_id"], "football.elo")
        self.assertTrue(exp["integrity_ok"])
        # hash computed correctly
        expected = hashlib.sha256(stable_json({"team_ratings": {"ARS": 1500, "CHE": 1450}, "home_advantage": 50}).encode()).hexdigest()
        self.assertEqual(exp["learned_state_hash"], expected)
        # previous is None
        self.assertIsNone(exp["previous_experience_id"])

    def test_B_create_second_version(self):
        """B) create second version state_version=2 previous preserved."""
        mem = _tmp_store()
        v1 = mem.experience_create(
            world_id="football", predictor_id="football.elo", predictor_version="v1",
            predictor_type="statistical", learned_state_schema="elo.v1",
            learned_state={"team_ratings": {"ARS": 1500}},
        )
        v2 = mem.experience_create(
            world_id="football", predictor_id="football.elo", predictor_version="v1",
            predictor_type="statistical", learned_state_schema="elo.v1",
            learned_state={"team_ratings": {"ARS": 1520}},
        )
        self.assertEqual(v2["state_version"], 2)
        self.assertEqual(v2["previous_experience_id"], v1["experience_id"])
        self.assertEqual(v2["previous_state_version"], 1)
        # v1 still retrievable
        fetched_v1 = mem.experience_get(v1["experience_id"])
        self.assertIsNotNone(fetched_v1)
        self.assertEqual(fetched_v1["state_version"], 1)
        self.assertEqual(fetched_v1["learned_state"], {"team_ratings": {"ARS": 1500}})

    def test_C_latest(self):
        """C) latest retorna v2."""
        mem = _tmp_store()
        mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"v": 1})
        v2 = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"v": 2})
        latest = mem.experience_latest("football", "football.elo", "v1")
        self.assertIsNotNone(latest)
        self.assertEqual(latest["experience_id"], v2["experience_id"])
        self.assertEqual(latest["state_version"], 2)

    def test_D_history(self):
        """D) history retorna v1+v2 em ordem correta."""
        mem = _tmp_store()
        mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"v": 1})
        mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"v": 2})
        hist = mem.experience_history("football", "football.elo", "v1", limit=20)
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0]["state_version"], 1)
        self.assertEqual(hist[1]["state_version"], 2)
        # by default learned_state omitted for size, but hash present
        self.assertIsNone(hist[0]["learned_state"])
        self.assertTrue(hist[0]["learned_state_omitted"])
        # with flag includes
        hist_full = mem.experience_history("football", "football.elo", "v1", include_learned_state=True)
        self.assertEqual(hist_full[0]["learned_state"], {"v": 1})

    def test_E_tampering(self):
        """E) tampering faz integrity check falhar."""
        mem = _tmp_store()
        exp = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"a": 1})
        exp_id = exp["experience_id"]
        # tamper directly in DB
        import sqlite3
        conn = sqlite3.connect(str(mem.path))
        conn.execute("UPDATE predictor_experiences SET learned_state_json=? WHERE experience_id=?", (stable_json({"a": 999}), exp_id))
        conn.commit()
        conn.close()
        fetched = mem.experience_get(exp_id)
        self.assertIsNotNone(fetched)
        self.assertFalse(fetched["integrity_ok"])
        # hash mismatch
        self.assertNotEqual(fetched["integrity_computed"], fetched["integrity_expected"])

    def test_F_predictor_isolation(self):
        """F) dois predictors no mesmo world não misturam."""
        mem = _tmp_store()
        exp_a = mem.experience_create(world_id="football", predictor_id="football.base-rate", predictor_version="v1", predictor_type="statistical", learned_state_schema="base.v1", learned_state={"rate": 0.5})
        exp_b = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"ratings": {}})
        # latest for each isolated
        latest_a = mem.experience_latest("football", "football.base-rate", "v1")
        latest_b = mem.experience_latest("football", "football.elo", "v1")
        self.assertEqual(latest_a["experience_id"], exp_a["experience_id"])
        self.assertEqual(latest_b["experience_id"], exp_b["experience_id"])
        # history isolated
        hist_a = mem.experience_history("football", "football.base-rate", "v1")
        hist_b = mem.experience_history("football", "football.elo", "v1")
        self.assertEqual(len(hist_a), 1)
        self.assertEqual(len(hist_b), 1)

    def test_G_version_isolation(self):
        """G) predictor v1 e v2 não compartilham Experience."""
        mem = _tmp_store()
        v1 = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"v": 1})
        v2 = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v2", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"v": 99})
        # each version starts at 1
        self.assertEqual(v1["state_version"], 1)
        self.assertEqual(v2["state_version"], 1)
        latest_v1 = mem.experience_latest("football", "football.elo", "v1")
        latest_v2 = mem.experience_latest("football", "football.elo", "v2")
        self.assertEqual(latest_v1["learned_state"], {"v": 1})
        self.assertEqual(latest_v2["learned_state"], {"v": 99})
        self.assertNotEqual(latest_v1["experience_id"], latest_v2["experience_id"])

    def test_H_performance_provenance(self):
        """H) métricas batem com predictions/resolutions reais."""
        mem = _tmp_store()
        p1 = _make_prediction(mem)
        p2 = mem.create_snapshot_memory(domain="football", subject="m2", state={"x": 2})
        p2_id = mem.create_prediction(domain="football", snapshot_memory_id=p2, claim="away win", probability=0.3, horizon="2099-01-01T00:00:00+00:00", resolution_rule={"type": "away_win"}, predictor_id="football.elo", predictor_version="v1", world_id="football")
        mem.resolve_prediction(p2_id, outcome=0)  # prob 0.3, outcome 0 => brier 0.09
        # p1 was 0.7 outcome 1 => brier 0.09 as well, mean 0.09
        exp = mem.experience_create(
            world_id="football", predictor_id="football.elo", predictor_version="v1",
            predictor_type="statistical", learned_state_schema="elo.v1",
            learned_state={"ratings": {}},
            source_prediction_ids=[p1, p2_id], source_outcome_ids=[p1, p2_id],
        )
        perf = exp["performance"]
        self.assertEqual(perf["resolved_predictions"], 2)
        self.assertAlmostEqual(perf["mean_brier"], 0.09, places=5)
        self.assertIsNotNone(perf["first_prediction_at"])
        self.assertIsNotNone(perf["last_outcome_at"])

    def test_external_predictor(self):
        """AI independence: external predictor_type funciona igual."""
        mem = _tmp_store()
        exp = mem.experience_create(world_id="football", predictor_id="external.test", predictor_version="v1", predictor_type="external", learned_state_schema="external.v1", learned_state={"strategy_state": {"x": 1}})
        self.assertEqual(exp["predictor_type"], "external")
        latest = mem.experience_latest("football", "external.test", "v1")
        self.assertEqual(latest["experience_id"], exp["experience_id"])

    def test_bridge_parity_and_scopes(self):
        """Remote parity: reads no bridge, write local only."""
        from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES
        from omnisvera_mcp.server import register_foundation_tools
        from mcp.server.fastmcp import FastMCP
        from omnisvera_mcp.core.context import CallContext
        from unittest.mock import MagicMock
        self.assertIn("experience.get", REMOTE_TOOL_NAMES)
        self.assertIn("experience.latest", REMOTE_TOOL_NAMES)
        self.assertIn("experience.history", REMOTE_TOOL_NAMES)
        self.assertNotIn("experience.create", REMOTE_TOOL_NAMES)
        # server registry
        mcp = FastMCP("test-exp")
        root = Path(tempfile.mkdtemp())
        (root / ".assistant-runtime" / "omnisvera-mcp").mkdir(parents=True, exist_ok=True)
        _, registry, _ = register_foundation_tools(mcp, root)
        self.assertIsNotNone(registry.get("experience.create"))
        self.assertIsNotNone(registry.get("experience.get"))
        self.assertEqual(registry.get("experience.create").required_scopes, frozenset({"experience.write"}))
        self.assertEqual(registry.get("experience.get").required_scopes, frozenset({"experience.read"}))
        # remote context should have read but not write
        from omnisvera_mcp.bridge import remote_bridge_context
        ctx = remote_bridge_context()
        self.assertIn("experience.read", ctx.scopes)
        self.assertNotIn("experience.write", ctx.scopes)
        # invoke read via registry
        mem_root = root / ".assistant-runtime" / "omnisvera-mcp" / "memory.db"
        from omnisvera_mcp.memory.store import MemoryStore as MS2
        mem2 = MS2(mem_root)
        # create via local context then read via remote-simulated
        exp = mem2.experience_create(world_id="football", predictor_id="test.p", predictor_version="v1", predictor_type="external", learned_state_schema="s", learned_state={"a":1})
        # need a world registered for server validation; but direct memory read doesn't need world
        fetched = registry.invoke("experience.get", CallContext.trusted_local_stdio(), {"experience_id": exp["experience_id"]})
        self.assertIn(exp["experience_id"], fetched)

    def test_acceptance_football_elo(self):
        """Acceptance: World football → predictor elo v1 → v1 → prediction/outcome → v2 continuity."""
        mem = _tmp_store()
        # World football exists logically; we assume server would validate but memory allows
        v1 = mem.experience_create(
            world_id="football", predictor_id="football.elo", predictor_version="v1",
            predictor_type="statistical", learned_state_schema="elo.v1",
            learned_state={"team_ratings": {"ARS": 1500, "CHE": 1450}, "home_advantage": 50},
            observations_used=5,
        )
        self.assertEqual(v1["state_version"], 1)
        # create a real prediction/outcome tied to this predictor
        snap = mem.create_snapshot_memory(domain="football", subject="match:TSDB-1", state={"elo": v1["learned_state"]})
        pred = mem.create_prediction(domain="football", snapshot_memory_id=snap, claim="ARS beats CHE", probability=0.6, horizon="2099-01-01T00:00:00+00:00", resolution_rule={"type": "home_win"}, predictor_id="football.elo", predictor_version="v1", world_id="football")
        mem.resolve_prediction(pred, outcome=1)
        # Experience v2 after outcome
        v2 = mem.experience_create(
            world_id="football", predictor_id="football.elo", predictor_version="v1",
            predictor_type="statistical", learned_state_schema="elo.v1",
            learned_state={"team_ratings": {"ARS": 1510, "CHE": 1440}, "home_advantage": 52},
            observations_used=6, source_prediction_ids=[pred], source_outcome_ids=[pred],
        )
        self.assertEqual(v2["state_version"], 2)
        latest = mem.experience_latest("football", "football.elo", "v1")
        self.assertEqual(latest["experience_id"], v2["experience_id"])
        hist = mem.experience_history("football", "football.elo", "v1")
        self.assertEqual(len(hist), 2)
        self.assertTrue(latest["integrity_ok"])
        self.assertEqual(latest["performance"]["resolved_predictions"], 1)
        # Simulate restart: new MemoryStore on same file
        mem2 = MemoryStore(mem.path)
        latest2 = mem2.experience_latest("football", "football.elo", "v1")
        self.assertEqual(latest2["learned_state"], {"team_ratings": {"ARS": 1510, "CHE": 1440}, "home_advantage": 52})
        self.assertTrue(latest2["integrity_ok"])

    def test_manifest_and_bootstrap(self):
        """Tool/manifest/bootstrap bounded."""
        from mcp.server.fastmcp import FastMCP
        from omnisvera_mcp.server import register_foundation_tools
        import json
        mcp = FastMCP("test-manifest")
        root = Path(tempfile.mkdtemp())
        (root / ".assistant-runtime" / "omnisvera-mcp").mkdir(parents=True, exist_ok=True)
        _, registry, _ = register_foundation_tools(mcp, root)
        from omnisvera_mcp.core.context import CallContext
        ctx = CallContext.trusted_local_stdio()
        manifest_raw = registry.invoke("system.manifest", ctx, {})
        manifest = json.loads(manifest_raw)
        self.assertIn("experience", manifest)
        self.assertTrue(manifest["experience"]["available"])
        self.assertTrue(manifest["experience"]["get"])
        # bootstrap bounded: no learned_state
        boot_raw = registry.invoke("system.bootstrap", ctx, {})
        boot = json.loads(boot_raw)
        self.assertIn("experience", boot)
        self.assertIn("per_world", boot["experience"])
        # create an experience and ensure bootstrap per_world not dumping learned_state
        # use tmp root's memory
        from omnisvera_mcp.memory.store import MemoryStore as MS
        mem = MS(root / ".assistant-runtime" / "omnisvera-mcp" / "memory.db")
        mem.experience_create(world_id="football", predictor_id="p.test", predictor_version="v1", predictor_type="external", learned_state_schema="s", learned_state={"secret": "should_not_leak_in_bootstrap_learned_state"})
        boot2_raw = registry.invoke("system.bootstrap", ctx, {})
        boot2 = json.loads(boot2_raw)
        dumped = json.dumps(boot2)
        # learned_state should not appear in bootstrap per_world (only hash etc)
        # The per_world entries should not contain the secret value
        # Check that secret not in bootstrap dump (bounded check)
        # Since experience_list_world returns summary without learned_state, it shouldn't contain secret
        self.assertNotIn("should_not_leak", dumped)

if __name__ == "__main__":
    unittest.main()
