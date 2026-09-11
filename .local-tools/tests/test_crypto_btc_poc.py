import json
import gc
import sys
import tempfile
import unittest
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from omnisvera_mcp.memory.store import MemoryStore
from omnisvera_mcp.core.context import CallContext
from omnisvera_mcp import epistemic
from omnisvera_mcp.adapters.crypto_btc import SOURCE, resolve_direction
from omnisvera_mcp.experience.crypto_btc import CryptoBtcDirectionUpdater, direction_state


class CryptoPoCTest(unittest.TestCase):
    def setUp(self):
        # Coinbase minute fixtures and prospective commit share an explicit clock.
        self.clock = self.enterContext(patch.object(epistemic, "datetime", wraps=datetime))
        self.clock.now.return_value = datetime(2026, 1, 1, 0, 0, 20, tzinfo=timezone.utc)
        self.enterContext(patch("omnisvera_mcp.memory.store.utc_now",
                                side_effect=lambda: self.clock.now.return_value.isoformat()))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(gc.collect)
        self.store = MemoryStore(Path(self.tmp.name) / "test.db")
        self.ctx = CallContext(actor="crypto.btc.direction", client="omnisvera-ai-console",
            transport="streamable-http", scopes=frozenset({"epistemic.prediction.commit"}), request_id="test")
        self.exp = self.store.experience_create(world_id="crypto", predictor_id="crypto.btc.direction",
            predictor_version="v1", predictor_type="statistical", learned_state_schema="btc.direction.v1",
            learned_state=direction_state(3, 2), observations_used=5)
        self.snap = self.store.create_snapshot_memory(domain="crypto", subject="BTC", state={"price": 100})
        self.rule = dict(type="price_direction", coin_id="bitcoin", quote="usd", reference_price=100,
            reference_observed_at="2026-01-01T00:00:00Z", comparison="horizon_price_gt_reference",
            source=SOURCE, resolver_id="crypto.btc.direction.v1", price_basis="closed_1m_candle")
        self.candidate = dict(world_id="crypto", domain="crypto", claim="BTC rises", probability=4/7,
            horizon="2026-01-01T01:00:00Z", model_snapshot_id=self.snap,
            predictor_id="crypto.btc.direction", predictor_version="v1", resolution_rule=self.rule,
            experience_id=self.exp["experience_id"], experience_state_version=1,
            experience_state_hash=self.exp["learned_state_hash"])

    def test_validation_and_hash(self):
        self.assertTrue(json.loads(epistemic.validate_candidate(self.store,self.ctx,{"candidate":self.candidate}))["valid"])
        for key in ("experience_id", "experience_state_hash", "experience_state_version"):
            bad = {k:v for k,v in self.candidate.items() if k != key}
            self.assertFalse(json.loads(epistemic.validate_candidate(self.store,self.ctx,{"candidate":bad}))["valid"])
        bad = dict(self.candidate, experience_state_hash="bad")
        self.assertFalse(json.loads(epistemic.validate_candidate(self.store,self.ctx,{"candidate":bad}))["valid"])

    def test_horizon_at_commit_time_is_rejected(self):
        self.assertTrue(json.loads(epistemic.validate_candidate(self.store, self.ctx,
                             {"candidate": self.candidate}))["valid"])
        self.clock.now.return_value = datetime(2026, 1, 1, 1, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, "horizon must be in the future"):
            epistemic.commit_candidate(self.store, self.ctx, {"candidate": self.candidate})
        self.assertEqual(self.store.stats()["counts"]["predictions"], 0)

    def test_non_iso_horizon_is_invalid_before_commit(self):
        candidate = dict(self.candidate, horizon="until tomorrow")
        self.assertFalse(json.loads(epistemic.validate_candidate(self.store, self.ctx,
                              {"candidate": candidate}))["valid"])
        with self.assertRaisesRegex(ValueError, "ISO-8601"):
            epistemic.commit_candidate(self.store, self.ctx, {"candidate": candidate})

    def test_validation_closes_every_database_connection(self):
        connections = []
        connect = self.store._connect
        def tracked_connect():
            connection = connect()
            connections.append(connection)
            return connection
        with patch.object(self.store, "_connect", side_effect=tracked_connect):
            result = json.loads(epistemic.validate_candidate(self.store, self.ctx,
                                              {"candidate": self.candidate}))
        self.assertTrue(result["valid"])
        self.assertTrue(connections)
        for connection in connections:
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute("SELECT 1")

    def test_identity_and_idempotence(self):
        wrong = CallContext(actor="football.elo",client="omnisvera-ai-console",transport="streamable-http",
                            scopes=self.ctx.scopes,request_id="wrong")
        with self.assertRaisesRegex(ValueError,"not authorized"):
            epistemic.commit_candidate(self.store,wrong,{"candidate":self.candidate})
        first = json.loads(epistemic.commit_candidate(self.store,self.ctx,{"candidate":self.candidate}))
        second = json.loads(epistemic.commit_candidate(self.store,self.ctx,{"candidate":self.candidate}))
        self.assertEqual(first["status"],"created")
        self.assertEqual(second["status"],"already_committed")
        self.assertEqual(first["prediction_id"],second["prediction_id"])
        pred=self.store.get_prediction(first["prediction_id"])
        self.assertEqual(pred["experience_state_hash"], self.exp["learned_state_hash"])
        self.assertEqual(pred["candidate_hash"],first["candidate_hash"])

    def test_direction_evidence(self):
        pred=dict(self.candidate,created_at="2026-01-01T00:00:20Z")
        for price,outcome in ((110,1),(100,0),(90,0)):
            def fetch(start,end,granularity):
                return [[start,0,0,0,100 if start == 1767225540 else price,0]]
            result=resolve_direction(pred,now="2026-01-01T01:01:00Z",fetch=fetch)
            self.assertEqual(result["outcome"],outcome)
            self.assertEqual(result["evidence"]["horizon_price"],price)
        self.assertIsNone(resolve_direction(pred,now="2026-01-01T00:30:00Z"))
        self.assertIsNone(resolve_direction(pred,now="2026-01-01T01:01:00Z",fetch=lambda *a:[]))
        with self.assertRaisesRegex(ValueError,"reference_price"):
            resolve_direction(pred,now="2026-01-01T01:01:00Z",fetch=lambda a,b,c:[[a,0,0,0,200,0]])

    def test_dry_run_and_runtime_v2(self):
        from omnisvera_mcp.world import CoreStateVectorBuilder
        from omnisvera_mcp.experience.runtime import process_experience_update_event
        from omnisvera_mcp.experience.updater import ExperienceUpdaterRegistry
        from contextlib import closing
        model = CoreStateVectorBuilder().build(world_id="crypto", signals=[{
            "signal_id": "crypto.price", "entity_ref": "BTC", "value": 100,
            "observed_at": "2026-01-01T00:00:00Z", "value_type": "number",
        }], patterns=[])
        snapshot = json.loads(epistemic.snapshot_from_model(self.store, self.ctx,
                                                    {"model": model.as_dict()}))
        self.candidate["model_snapshot_id"] = snapshot["snapshot_id"]
        self.candidate["model_id"] = model.model_id
        self.assertTrue(json.loads(epistemic.validate_candidate(self.store, self.ctx,
                                    {"candidate": self.candidate}))["valid"])
        first=json.loads(epistemic.commit_candidate(self.store,self.ctx,{"candidate":self.candidate}))
        self.clock.now.return_value = datetime(2026, 1, 1, 1, 1, tzinfo=timezone.utc)
        evidence=dict(outcome=1,evidence=dict(reference_price=100,horizon_price=110,
            reference_observed_at=self.rule["reference_observed_at"],horizon_observed_at=self.candidate["horizon"],source=SOURCE))
        def fixture(start,end,granularity):
            return [[start,0,0,0,100 if start == 1767225540 else 110,0]]
        with patch('omnisvera_mcp.adapters.crypto_btc.resolve_direction',side_effect=lambda pred,now:resolve_direction(pred,now=now,fetch=fixture)):
            dry=json.loads(epistemic.resolve_due_predictions(self.store,self.ctx,{"now":"2026-12-01T00:00:00Z","dry_run":True}))
            self.assertEqual(dry["items"][0]["status"],"would_resolve")
            self.assertEqual(self.store.get_prediction(first["prediction_id"])["status"],"open")
            resolved=json.loads(epistemic.resolve_due_predictions(self.store,self.ctx,{"now":"2026-12-01T00:00:00Z"}))
            self.assertEqual(resolved["resolved"],1)
        latest=self.store.experience_latest("crypto","crypto.btc.direction","v1")
        self.assertEqual(latest["state_version"],2)
        self.assertEqual(latest["learned_state"],direction_state(4,2))
        self.assertTrue(latest["integrity_ok"])
        self.assertEqual(latest["previous_experience_id"], self.exp["experience_id"])
        persisted = self.store.get_prediction(first["prediction_id"])
        self.assertEqual(persisted["predictor_id"], self.ctx.actor)
        self.assertEqual(persisted["experience_id"], self.exp["experience_id"])
        self.assertEqual(persisted["experience_state_version"], 1)
        self.assertEqual(persisted["experience_state_hash"], self.exp["learned_state_hash"])
        self.assertEqual(persisted["candidate_hash"], first["candidate_hash"])
        self.assertTrue(self.store.get_memory(snapshot["snapshot_id"])["sources"])
        events = self.store.experience_update_list(world_id="crypto")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "applied")
        updaters = ExperienceUpdaterRegistry()
        updaters.register(CryptoBtcDirectionUpdater())
        for _ in range(2):
            process_experience_update_event(self.store, updaters, events[0]["update_event_id"])
        self.assertEqual(len(self.store.experience_history("crypto", "crypto.btc.direction", "v1")), 2)
        with self.assertRaisesRegex(ValueError, "already resolved"):
            self.store.resolve_prediction(first["prediction_id"], outcome=1)
        with closing(self.store._connect()) as connection:
            rows = connection.execute("SELECT calibration_score FROM prediction_resolutions").fetchall()
            self.assertEqual(len(rows), 1)
            self.assertAlmostEqual(rows[0][0], (4/7-1)**2, places=7)
        again=json.loads(epistemic.resolve_due_predictions(self.store,self.ctx,{"now":"2026-12-01T00:00:00Z"}))
        self.assertEqual(again["examined"],0)

    def test_updater_validation(self):
        updater=CryptoBtcDirectionUpdater()
        with self.assertRaises(ValueError):
            updater.update(previous_experience=self.exp,prediction={},resolution={"outcome":2})
        self.assertEqual(updater.update(previous_experience=self.exp,prediction={},resolution={"outcome":0}).learned_state,direction_state(3,3))

    def test_seed_idempotence(self):
        from tools.seed_crypto_btc import seed
        with tempfile.TemporaryDirectory() as directory:
            store = MemoryStore(Path(directory) / "seed.db")
            def fixture(start,end,step):
                return [[t,1,3,1,1+i%2,1] for i,t in enumerate(range(start,end,step))]
            exp = seed(store, Path(directory) / "data", fetch=fixture)
            self.assertEqual(exp["state_version"],1)
            self.assertEqual(exp["observations_used"],239)
            self.assertTrue(exp["integrity_ok"])
            self.assertEqual(seed(store,directory,fetch=fixture)["experience_id"],exp["experience_id"])

    def test_transport_identity_and_commit(self):
        import asyncio
        import importlib.util
        import types
        path = Path(__file__).resolve().parents[1] / "mcp_http_server.py"
        spec = importlib.util.spec_from_file_location("crypto_test_http", path)
        module = importlib.util.module_from_spec(spec)
        # No operational Core import, index refresh or DB writes.
        with patch.dict(sys.modules, {"mcp_server":types.SimpleNamespace(CORE_REGISTRY=object())}), patch('omnisvera_mcp.bridge.register_remote_bridge_tools'), patch.dict('os.environ', {"OMNISVERA_AI_CONSOLE_CRYPTO_TOKEN":"crypto-test-token"}):
            spec.loader.exec_module(module)
        module._CONSOLE_TOKEN="football-test-token"
        module._CRYPTO_TOKEN="crypto-test-token"
        async def request(secret, host="127.0.0.1"):
            captured=[]
            async def inner(scope,receive,send):
                ctx=module.dynamic_remote_context()
                captured.append(ctx)
                if ctx.actor == "crypto.btc.direction":
                    captured.append(json.loads(epistemic.commit_candidate(self.store,ctx,{"candidate":self.candidate})))
            async def receive(): return {"type":"http.request","body":b'{"method":"tools/call"}',"more_body":False}
            async def send(message): pass
            await module.LegacyDiscoveryFallback(inner)({"type":"http","path":"/mcp","method":"POST",
                "client":(host,1234),"headers":[(b'x-omnisvera-caller',b'omnisvera-ai-console'),
                (b'x-omnisvera-console-token',secret.encode())]},receive,send)
            self.assertEqual(module.dynamic_remote_context().actor,"mia")
            return captured
        crypto=asyncio.run(request("crypto-test-token"))
        self.assertEqual(crypto[0].actor,"crypto.btc.direction")
        self.assertEqual(crypto[0].client,"omnisvera-ai-console")
        self.assertEqual(crypto[1]["status"],"created")
        self.assertEqual(asyncio.run(request("football-test-token"))[0].actor,"football.elo")
        self.assertEqual(asyncio.run(request("wrong"))[0].actor,"mia")
        self.assertEqual(asyncio.run(request("crypto-test-token","192.0.2.1"))[0].actor,"mia")


if __name__ == '__main__':
    unittest.main()
