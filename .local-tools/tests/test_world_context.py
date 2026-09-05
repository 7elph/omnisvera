"""World Context v0.1 — Tests A-F.

Proves:
A) Football context retorna descriptor, state, changes, predictions, freshness, provenance
B) Crypto context: latest prices em state, polling unchanged não aparece como recent change
C) Scheduler offline/gap: contexto retorna último estado com freshness stale/gap
D) Unknown world: erro claro
E) No predictions/patterns: arrays vazios, sem erro
F) Remote parity: Core registry, Bridge allowlist, remote discovery incluem world.context
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))
if str(LOCAL_TOOLS.parent) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS.parent))

from omnisvera_mcp.memory.store import MemoryStore
from omnisvera_mcp.world import WorldRegistry, WorldModelRegistry, CoreStateVectorBuilder
from omnisvera_mcp.adapters.football import FootballWorldAdapter, FakeFootballDataProvider
from omnisvera_mcp.adapters.crypto import CryptoWorldAdapter
from omnisvera_mcp.server import _build_world_context, WORLD_CONTEXT_OPERATIONAL

# helper to capture with change-aware
def _now_minus(hours: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

def _make_worlds() -> tuple[WorldRegistry, WorldModelRegistry]:
    worlds = WorldRegistry()
    builders = WorldModelRegistry()
    builders.register(CoreStateVectorBuilder())
    worlds.register(FootballWorldAdapter(provider=FakeFootballDataProvider()))
    # crypto with dummy provider that won't hit network
    class DummyCrypto:
        def get_prices(self, coin_ids=None):
            return []
        def __class_names(self):
            return "Dummy"
    # We'll register Crypto adapter with fake provider via direct adapter but avoid network
    # Use a stub provider object with same interface as CoinGecko but no requests
    from unittest.mock import MagicMock
    stub = MagicMock()
    stub.get_prices.return_value = []
    # But CryptoWorldAdapter expects provider with get_prices; we can inject a minimal stub
    class StubProvider:
        def get_prices(self, coin_ids=None):
            return []
    worlds.register(CryptoWorldAdapter(provider=StubProvider()))
    return worlds, builders

class WorldContextTests(unittest.TestCase):

    def test_A_football_context(self):
        """A) Football context retorna todos os campos obrigatórios."""
        tmp = Path(tempfile.mkdtemp()) / "a.db"
        mem = MemoryStore(tmp)
        worlds, builders = _make_worlds()
        # insert domain signals for football
        now = datetime.now(timezone.utc).isoformat()
        # scheduled match
        mem.capture_signal(world_id="football", signal_id="football.match.status", entity_ref="match:TSDB-1", schema="football.match.v1", value="scheduled", value_type="categorical", unit="", observed_at=now, source={}, metadata={})
        mem.capture_signal(world_id="football", signal_id="football.match.date", entity_ref="match:TSDB-1", schema="football.match.v1", value="2026-09-10T15:00:00", value_type="datetime", unit="", observed_at=now, source={}, metadata={})
        # completed match with score
        mem.capture_signal(world_id="football", signal_id="football.match.status", entity_ref="match:TSDB-2", schema="football.match.v1", value="completed", value_type="categorical", unit="", observed_at=now, source={}, metadata={})
        mem.capture_signal(world_id="football", signal_id="football.match.home_score", entity_ref="match:TSDB-2", schema="football.match.v1", value=2, value_type="number", unit="goals", observed_at=now, source={}, metadata={})
        mem.capture_signal(world_id="football", signal_id="football.match.away_score", entity_ref="match:TSDB-2", schema="football.match.v1", value=1, value_type="number", unit="goals", observed_at=now, source={}, metadata={})
        # operational signals (should be separated)
        mem.capture_signal(world_id="football", signal_id="football.observation.match_count", entity_ref=None, schema="football.match.v1", value=8, value_type="number", unit="count", observed_at=now, source={}, metadata={})
        # scheduler telemetry recent
        mem._capture_scheduler_telemetry(run_id="run-a1", world_id="football", provider="FakeFootballDataProvider", run_started_at=now, run_finished_at=now, success=True, signals_seen=10, signals_changed=5, signals_unchanged=0)

        ctx = _build_world_context(mem, worlds, builders, world_id="football", lookback_hours=24)

        # world descriptor
        self.assertEqual(ctx["world"]["world_id"], "football")
        self.assertEqual(ctx["world"]["world_type"], "sports.football")
        # current domain state not empty and does NOT contain operational signals
        sig_ids = {s["signal_id"] for s in ctx["current_state"]["signals"]}
        self.assertIn("football.match.status", sig_ids)
        self.assertIn("football.match.home_score", sig_ids)
        self.assertNotIn("football.observation.match_count", sig_ids)
        # operational separated
        op_ids = {s["signal_id"] for s in ctx["operational"]["signals"]}
        self.assertIn("football.observation.match_count", op_ids)
        # entities
        self.assertIn("match:TSDB-1", ctx["current_state"]["entities"])
        # provenance
        self.assertEqual(ctx["provenance"]["world_id"], "football")
        self.assertIn("generated_at", ctx["provenance"])
        # freshness
        self.assertIsNotNone(ctx["freshness"]["last_observation_at"])
        self.assertIsNotNone(ctx["freshness"]["scheduler_last_run"])
        # health
        self.assertIn("status", ctx["health"])
        # model may be present (since we have signals)
        # limitations is list
        self.assertIsInstance(ctx["limitations"], list)
        # payload bounded
        self.assertLessEqual(len(ctx["recent_changes"]), 20)
        self.assertLessEqual(len(ctx["patterns"]), 20)
        self.assertLessEqual(len(ctx["open_predictions"]), 20)
        self.assertLessEqual(len(ctx["recent_outcomes"]), 20)

    def test_B_crypto_unchanged_not_in_recent_changes(self):
        """B) Crypto: latest price em state, polling unchanged não vira recent_change."""
        tmp = Path(tempfile.mkdtemp()) / "b.db"
        mem = MemoryStore(tmp)
        worlds, builders = _make_worlds()
        base = datetime.now(timezone.utc)
        # Insert 3 observations: 100 at T-3h, 100 again at T-2h (unchanged), 105 at T-1h (changed)
        # Use change-aware to simulate scheduler behavior
        t1 = (base - timedelta(hours=3)).isoformat()
        t2 = (base - timedelta(hours=2)).isoformat()
        t3 = (base - timedelta(hours=1)).isoformat()
        r1 = mem.capture_signal_change_aware(world_id="crypto", signal_id="crypto.price.usd", entity_ref="coin:btc", schema="crypto.price.v1", value=100.0, value_type="number", unit="usd", observed_at=t1, source={}, metadata={})
        self.assertEqual(r1["status"], "initial_recorded")
        r2 = mem.capture_signal_change_aware(world_id="crypto", signal_id="crypto.price.usd", entity_ref="coin:btc", schema="crypto.price.v1", value=100.0, value_type="number", unit="usd", observed_at=t2, source={}, metadata={})
        self.assertEqual(r2["status"], "unchanged_skipped")
        r3 = mem.capture_signal_change_aware(world_id="crypto", signal_id="crypto.price.usd", entity_ref="coin:btc", schema="crypto.price.v1", value=105.0, value_type="number", unit="usd", observed_at=t3, source={}, metadata={})
        self.assertEqual(r3["status"], "changed_recorded")

        ctx = _build_world_context(mem, worlds, builders, world_id="crypto", lookback_hours=24)
        # current_state should have latest value 105
        btc_signals = [s for s in ctx["current_state"]["signals"] if s["entity_ref"] == "coin:btc" and s["signal_id"] == "crypto.price.usd"]
        self.assertEqual(len(btc_signals), 1)
        self.assertEqual(btc_signals[0]["value"], 105.0)
        # recent_changes should have exactly 1 change (100 -> 105), not 2
        # Filter to btc price changes
        btc_changes = [c for c in ctx["recent_changes"] if c["entity_ref"] == "coin:btc" and c["signal_id"] == "crypto.price.usd"]
        self.assertEqual(len(btc_changes), 1)
        self.assertEqual(btc_changes[0]["previous_value"], 100.0)
        self.assertEqual(btc_changes[0]["current_value"], 105.0)

    def test_C_scheduler_gap_stale(self):
        """C) Scheduler offline: contexto continua, freshness stale/gap."""
        tmp = Path(tempfile.mkdtemp()) / "c.db"
        mem = MemoryStore(tmp)
        worlds, builders = _make_worlds()
        # One old signal 5h ago
        old_time = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        mem.capture_signal(world_id="football", signal_id="football.match.status", entity_ref="match:TSDB-99", schema="football.match.v1", value="scheduled", value_type="categorical", unit="", observed_at=old_time, source={}, metadata={})
        # Scheduler last run also 5h ago, failed
        mem._capture_scheduler_telemetry(run_id="run-old", world_id="football", provider="FakeFootballDataProvider", run_started_at=old_time, run_finished_at=old_time, success=False, signals_seen=0, signals_changed=0, signals_unchanged=0, error="timeout")

        ctx = _build_world_context(mem, worlds, builders, world_id="football", lookback_hours=24)
        # still returns last state
        self.assertEqual(len(ctx["current_state"]["signals"]), 1)
        self.assertEqual(ctx["current_state"]["signals"][0]["value"], "scheduled")
        # freshness indicates stale
        self.assertIsNotNone(ctx["freshness"]["last_observation_at"])
        age = ctx["freshness"]["data_age_seconds"]
        self.assertGreater(age, 4*3600)  # >4h
        # limitations mentions stale or failure
        lim_text = " ".join(ctx["limitations"]).lower()
        self.assertTrue("stale" in lim_text or "failed" in lim_text or "provider" in lim_text)

    def test_D_unknown_world(self):
        """D) Unknown world: erro claro."""
        tmp = Path(tempfile.mkdtemp()) / "d.db"
        mem = MemoryStore(tmp)
        worlds, builders = _make_worlds()
        with self.assertRaises(KeyError) as cm:
            _build_world_context(mem, worlds, builders, world_id="unknown", lookback_hours=24)
        self.assertIn("unknown", str(cm.exception).lower())

    def test_E_no_predictions_patterns(self):
        """E) Sem predictions/patterns: arrays vazios, sem erro."""
        tmp = Path(tempfile.mkdtemp()) / "e.db"
        mem = MemoryStore(tmp)
        worlds, builders = _make_worlds()
        now = datetime.now(timezone.utc).isoformat()
        mem.capture_signal(world_id="football", signal_id="football.match.status", entity_ref="match:TSDB-10", schema="football.match.v1", value="scheduled", value_type="categorical", unit="", observed_at=now, source={}, metadata={})
        ctx = _build_world_context(mem, worlds, builders, world_id="football", lookback_hours=24)
        self.assertEqual(ctx["open_predictions"], [])
        self.assertEqual(ctx["recent_outcomes"], [])
        # patterns may be empty (needs 2 numeric points etc.)
        self.assertIsInstance(ctx["patterns"], list)
        # still valid context
        self.assertEqual(ctx["world"]["world_id"], "football")

    def test_F_remote_parity(self):
        """F) Core registry e Bridge allowlist incluem world.context."""
        from omnisvera_mcp.bridge import REMOTE_TOOL_NAMES
        self.assertIn("world.context", REMOTE_TOOL_NAMES)
        # Check server registry via building a temporary mcp registration
        from unittest.mock import MagicMock
        from mcp.server.fastmcp import FastMCP
        from omnisvera_mcp.server import register_foundation_tools
        import tempfile
        mcp = FastMCP("test")
        root = Path(tempfile.mkdtemp())
        # need vault structure minimal
        (root / ".assistant-runtime" / "omnisvera-mcp").mkdir(parents=True, exist_ok=True)
        bindings, registry, search = register_foundation_tools(mcp, root)
        # registry should have tool
        tool = registry.get("world.context")
        self.assertIsNotNone(tool)
        self.assertIn("world.read", tool.required_scopes)

    def test_acceptance_bootstrap_list_context(self):
        """Acceptance: system.bootstrap → world.list → world.context chain works."""
        tmp_root = Path(tempfile.mkdtemp())
        (tmp_root / ".assistant-runtime" / "omnisvera-mcp").mkdir(parents=True, exist_ok=True)
        from mcp.server.fastmcp import FastMCP
        from omnisvera_mcp.server import register_foundation_tools
        from omnisvera_mcp.core.context import CallContext
        mcp = FastMCP("test2")
        bindings, registry, search = register_foundation_tools(mcp, tmp_root)
        ctx = CallContext.trusted_local_stdio()
        # bootstrap
        boot_raw = registry.invoke("system.bootstrap", ctx, {})
        boot = json.loads(boot_raw)
        self.assertIn("worlds", boot)
        self.assertTrue(len(boot["worlds"]) >= 1)
        # list
        worlds_raw = registry.invoke("world.list", ctx, {})
        worlds_list = json.loads(worlds_raw)
        self.assertTrue(any(w["world_id"] == "football" for w in worlds_list))
        # context for each world should be valid without knowing internals
        for w in worlds_list:
            wid = w["world_id"]
            c_raw = registry.invoke("world.context", ctx, {"world_id": wid})
            c = json.loads(c_raw)
            self.assertIn("world", c)
            self.assertIn("current_state", c)
            self.assertIn("recent_changes", c)
            self.assertIn("open_predictions", c)
            self.assertIn("freshness", c)
            self.assertIn("limitations", c)
            self.assertIn("provenance", c)

    def test_payload_bounded(self):
        """Payload bounded: limits geram no máximo 20 por seção."""
        tmp = Path(tempfile.mkdtemp()) / "bounded.db"
        mem = MemoryStore(tmp)
        worlds, builders = _make_worlds()
        base = datetime.now(timezone.utc)
        # Insert 30 different entities to exceed limits
        for i in range(30):
            t = (base - timedelta(minutes=i*10)).isoformat()
            mem.capture_signal(world_id="football", signal_id="football.match.status", entity_ref=f"match:TSDB-{1000+i}", schema="football.match.v1", value="scheduled", value_type="categorical", unit="", observed_at=t, source={}, metadata={})
        ctx = _build_world_context(mem, worlds, builders, world_id="football", lookback_hours=24)
        # current_state may be larger than 20 because entities, but recent_changes etc capped at 20
        self.assertLessEqual(len(ctx["recent_changes"]), 20)
        self.assertLessEqual(len(ctx["patterns"]), 20)
        self.assertLessEqual(len(ctx["open_predictions"]), 20)
        self.assertLessEqual(len(ctx["recent_outcomes"]), 20)

    def test_operational_not_in_domain_state(self):
        """Operational não mistura com domain por default."""
        tmp = Path(tempfile.mkdtemp()) / "op.db"
        mem = MemoryStore(tmp)
        worlds, builders = _make_worlds()
        now = datetime.now(timezone.utc).isoformat()
        mem.capture_signal(world_id="football", signal_id="football.match.status", entity_ref="match:TSDB-1", schema="football.match.v1", value="scheduled", value_type="categorical", unit="", observed_at=now, source={}, metadata={})
        mem.capture_signal(world_id="football", signal_id="football.observation.match_count", entity_ref=None, schema="football.match.v1", value=8, value_type="number", unit="count", observed_at=now, source={}, metadata={})
        ctx = _build_world_context(mem, worlds, builders, world_id="football", lookback_hours=24)
        domain_ids = {s["signal_id"] for s in ctx["current_state"]["signals"]}
        self.assertNotIn("football.observation.match_count", domain_ids)
        op_ids = {s["signal_id"] for s in ctx["operational"]["signals"]}
        self.assertIn("football.observation.match_count", op_ids)

if __name__ == "__main__":
    unittest.main()
