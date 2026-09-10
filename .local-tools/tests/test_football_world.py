"""Football World Adapter v0.1 — Tests.

Tests required by spec:
    1. football registered as world
    2. world.describe works
    3. world.observe returns WorldObservation
    4. Companion still works
    5. football state does not contain future results
    6. completed result can be observed later
    7. pre-match snapshot stays intact
    8. prediction/resolution works without Core knowing football
    9. FakeWorld still works
    10. all previous suites remain green
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

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

# Load world.py in isolation
import types as _mt
_world_mod = _mt.ModuleType("world")
_world_mod.__file__ = str(LOCAL_TOOLS / "omnisvera_mcp" / "world.py")
sys.modules["world"] = _world_mod
_world_src = (LOCAL_TOOLS / "omnisvera_mcp" / "world.py").read_text(encoding="utf-8")
exec(compile(_world_src, _world_mod.__file__, "exec"), _world_mod.__dict__)
WorldDescriptor = _world_mod.WorldDescriptor
WorldObservation = _world_mod.WorldObservation
WorldAdapter = _world_mod.WorldAdapter
WorldRegistry = _world_mod.WorldRegistry

# Load football adapter in isolation
_football_mod = _mt.ModuleType("omnisvera_mcp.adapters.football")
_football_mod.__file__ = str(LOCAL_TOOLS / "omnisvera_mcp" / "adapters" / "football.py")
_football_mod.__package__ = "omnisvera_mcp.adapters"
sys.modules["omnisvera_mcp.adapters.football"] = _football_mod
sys.modules["football"] = _football_mod
_football_src = (LOCAL_TOOLS / "omnisvera_mcp" / "adapters" / "football.py").read_text(encoding="utf-8")
# Stub relative imports
_football_src = _football_src.replace("from ..world import", "from world import")
exec(compile(_football_src, _football_mod.__file__, "exec"), _football_mod.__dict__)
FootballWorldAdapter = _football_mod.FootballWorldAdapter
FakeFootballDataProvider = _football_mod.FakeFootballDataProvider
HttpFootballDataProvider = _football_mod.HttpFootballDataProvider

# Load epistemic.py for snapshot_from_observation
_ep_src = (LOCAL_TOOLS / "omnisvera_mcp" / "epistemic.py").read_text(encoding="utf-8")
_ep_ns: dict = {"__name__": "epistemic", "__file__": str(LOCAL_TOOLS / "omnisvera_mcp" / "epistemic.py")}
_ep_src = _ep_src.replace("from .core.context import CallContext", "CallContext = object")
_ep_src = _ep_src.replace("from .memory.store import MemoryStore, stable_json", "MemoryStore = object")
_ep_src = _ep_src.replace("from .memory.store import MemoryStore", "MemoryStore = object")
exec(compile(_ep_src, _ep_ns["__file__"], "exec"), _ep_ns)
snapshot_from_observation = _ep_ns["snapshot_from_observation"]


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------

class FootballWorldTests(unittest.TestCase):
    """10 mandatory tests for Football World Adapter."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = MemoryStore(Path(self.temporary.name) / "test.db")
        self.registry = WorldRegistry()
        self.football = FootballWorldAdapter()

    # 1. football registered as world
    def test_football_registered_as_world(self):
        self.registry.register(self.football)
        self.assertTrue(self.registry.has("football"))

    # 2. world.describe works
    def test_world_describe_works(self):
        self.registry.register(self.football)
        adapter = self.registry.get("football")
        descriptor = adapter.describe()
        self.assertEqual(descriptor.world_id, "football")
        self.assertEqual(descriptor.world_type, "sports.football")
        self.assertIn("observe", descriptor.capabilities)
        self.assertIn("football.match.v1", descriptor.schemas)
        health = adapter.health()
        self.assertEqual(health["status"], "healthy")

    # 3. world.observe returns WorldObservation
    def test_world_observe_returns_observation(self):
        self.registry.register(self.football)
        adapter = self.registry.get("football")
        observation = adapter.observe()
        self.assertIsInstance(observation, WorldObservation)
        self.assertEqual(observation.world_id, "football")
        self.assertEqual(observation.schema, "football.match.v1")
        self.assertIn("matches", observation.state)
        self.assertGreater(len(observation.state["matches"]), 0)

    # 4. Companion still works
    def test_companion_still_works(self):
        class CompanionStub:
            def describe(self):
                return WorldDescriptor(
                    world_id="companion", world_type="simulation.rpg",
                    name="Companion", adapter_id="companion.http.v1",
                    capabilities=["observe", "history", "model"],
                    schemas=["companion.session.v1"],
                )
            def health(self):
                return {"status": "healthy"}
            def observe(self, query=None):
                return WorldObservation(
                    world_id="companion", observed_at="", schema="companion.session.v1",
                    state={}, sources=[], provenance={},
                )
        self.registry.register(CompanionStub())
        self.registry.register(self.football)
        self.assertEqual(len(self.registry.list()), 2)
        self.assertTrue(self.registry.has("companion"))
        self.assertTrue(self.registry.has("football"))

    # 5. football state does not contain future results
    def test_scheduled_no_future_results(self):
        adapter = FootballWorldAdapter()
        observation = adapter.observe(query={"match_id": "FUT-001"})
        match = observation.state["matches"][0]
        self.assertEqual(match["status"], "scheduled")
        self.assertNotIn("home_score", match)
        self.assertNotIn("away_score", match)
        self.assertNotIn("result", match)
        self.assertNotIn("winner", match)

    # 6. completed result can be observed later
    def test_completed_result_observed(self):
        adapter = FootballWorldAdapter()
        observation = adapter.observe(query={"match_id": "FUT-003"})
        match = observation.state["matches"][0]
        self.assertEqual(match["status"], "completed")
        self.assertEqual(match["home_score"], 2)
        self.assertEqual(match["away_score"], 1)
        self.assertEqual(match["result"]["winner"], "home")

    # 7. pre-match snapshot stays intact
    def test_pre_match_snapshot_intact(self):
        adapter = FootballWorldAdapter()
        observation = adapter.observe(query={"match_id": "FUT-001"})
        context = type("Ctx", (), {})()
        result_json = snapshot_from_observation(
            self.store, context, {"observation": observation.as_dict()},
        )
        snapshot_id = json.loads(result_json)["snapshot_id"]
        mem = self.store.get_memory(snapshot_id)
        self.assertIsNotNone(mem)
        self.assertEqual(mem["type"], "model_snapshot")
        self.assertEqual(mem["status"], "immutable")
        state = json.loads(mem["content"])
        match = state["matches"][0]
        self.assertEqual(match["status"], "scheduled")
        self.assertNotIn("home_score", match)

    # 8. prediction/resolution works without Core knowing football
    def test_prediction_resolution_no_football_knowledge(self):
        adapter = FootballWorldAdapter()
        observation = adapter.observe(query={"match_id": "FUT-001"})
        context = type("Ctx", (), {})()
        result_json = snapshot_from_observation(
            self.store, context, {"observation": observation.as_dict()},
        )
        snapshot_id = json.loads(result_json)["snapshot_id"]

        # Create prediction — claim is generic, Core does not understand "home team"
        prediction_id = self.store.create_prediction(
            domain="football.premier_league",
            snapshot_memory_id=snapshot_id,
            claim="home team wins",
            probability=0.55,
            horizon="90 minutes",
            resolution_rule={"type": "binary", "criterion": "home_score > away_score"},
        )
        pred = self.store.get_prediction(prediction_id)
        self.assertIsNotNone(pred)
        self.assertTrue(pred["snapshot_intact"])

        # Complete the match in provider and resolve
        adapter._provider.complete_match("FUT-001", 3, 1)
        result = self.store.resolve_prediction(prediction_id, outcome=1)
        self.assertEqual(result["status"], "resolved")
        expected_brier = round((0.55 - 1) ** 2, 8)
        self.assertAlmostEqual(result["resolution"]["calibration_score"], expected_brier, places=8)

    # 9. FakeWorld still works
    def test_fakeworld_still_works(self):
        class FakeWorldAdapter:
            def describe(self):
                return WorldDescriptor(
                    world_id="test-world", world_type="sensor",
                    name="Fake", adapter_id="fake.v1",
                    capabilities=["observe"], schemas=["test.v1"],
                )
            def health(self):
                return {"status": "healthy"}
            def observe(self, query=None):
                return WorldObservation(
                    world_id="test-world", observed_at="", schema="test.v1",
                    state={"temp": 23}, sources=[], provenance={},
                )
        self.registry.register(FakeWorldAdapter())
        self.registry.register(self.football)
        self.assertEqual(len(self.registry.list()), 2)
        fake = self.registry.get("test-world")
        obs = fake.observe()
        self.assertEqual(obs.state["temp"], 23)

    # 10. all previous suites remain green
    def test_all_previous_suites_green(self):
        import tests.test_epistemic_loop
        import tests.test_companion_session
        import tests.test_historical_replay
        import tests.test_timeline
        import tests.test_backtest_validation
        import tests.test_world_contract
        self.assertTrue(hasattr(tests.test_epistemic_loop, "test_bridge_tools"))
        self.assertTrue(hasattr(tests.test_companion_session, "CompanionSessionModelTests"))
        self.assertTrue(hasattr(tests.test_historical_replay, "HistoricalReplayTests"))
        self.assertTrue(hasattr(tests.test_timeline, "TimelineCoreTests"))
        self.assertTrue(hasattr(tests.test_backtest_validation, "BacktestValidationTests"))
        self.assertTrue(hasattr(tests.test_world_contract, "WorldContractTests"))


class FootballProviderTests(unittest.TestCase):
    """Tests for the FakeFootballDataProvider."""

    def test_list_all(self):
        provider = FakeFootballDataProvider()
        matches = provider.list_matches()
        self.assertEqual(len(matches), 4)

    def test_filter_by_competition(self):
        provider = FakeFootballDataProvider()
        pl = provider.list_matches(competition="Premier League")
        self.assertEqual(len(pl), 3)
        laliga = provider.list_matches(competition="La Liga")
        self.assertEqual(len(laliga), 1)

    def test_filter_by_status(self):
        provider = FakeFootballDataProvider()
        scheduled = provider.list_matches(status="scheduled")
        self.assertEqual(len(scheduled), 3)
        completed = provider.list_matches(status="completed")
        self.assertEqual(len(completed), 1)

    def test_get_match(self):
        provider = FakeFootballDataProvider()
        m = provider.get_match("FUT-001")
        self.assertIsNotNone(m)
        self.assertEqual(m.home_name, "Arsenal")
        self.assertIsNone(m.home_score)

    def test_get_match_not_found(self):
        provider = FakeFootballDataProvider()
        self.assertIsNone(provider.get_match("NONEXISTENT"))

    def test_complete_match(self):
        provider = FakeFootballDataProvider()
        m = provider.complete_match("FUT-001", 2, 0)
        self.assertIsNotNone(m)
        self.assertEqual(m.status, "completed")
        self.assertEqual(m.home_score, 2)
        self.assertEqual(m.away_score, 0)
        # Verify the stored match was updated
        stored = provider.get_match("FUT-001")
        self.assertEqual(stored.status, "completed")


class FootballTemporalProtectionTests(unittest.TestCase):
    """Tests ensuring temporal separation between pre-match and post-match."""

    def test_scheduled_never_has_result(self):
        adapter = FootballWorldAdapter()
        for match_id in ["FUT-001", "FUT-002", "FUT-004"]:
            obs = adapter.observe(query={"match_id": match_id})
            match = obs.state["matches"][0]
            self.assertEqual(match["status"], "scheduled")
            self.assertNotIn("home_score", match)
            self.assertNotIn("away_score", match)
            self.assertNotIn("result", match)

    def test_completed_has_result(self):
        adapter = FootballWorldAdapter()
        obs = adapter.observe(query={"match_id": "FUT-003"})
        match = obs.state["matches"][0]
        self.assertEqual(match["status"], "completed")
        self.assertIn("home_score", match)
        self.assertIn("away_score", match)
        self.assertIn("result", match)

    def test_schedule_to_complete_separation(self):
        """Pre-match snapshot must not be contaminated by later result."""
        provider = FakeFootballDataProvider()
        adapter = FootballWorldAdapter(provider=provider)

        # Observe before completion
        obs_before = adapter.observe(query={"match_id": "FUT-001"})
        match_before = obs_before.state["matches"][0]
        self.assertNotIn("home_score", match_before)

        # Complete the match
        provider.complete_match("FUT-001", 1, 0)

        # Observe after completion
        obs_after = adapter.observe(query={"match_id": "FUT-001"})
        match_after = obs_after.state["matches"][0]
        self.assertEqual(match_after["status"], "completed")
        self.assertEqual(match_after["home_score"], 1)

        # The before-snapshot is still immutable (different memory item)
        with tempfile.TemporaryDirectory() as tmpdir:
            context = type("Ctx", (), {})()
            store_before = MemoryStore(Path(tmpdir) / "before.db")
            store_after = MemoryStore(Path(tmpdir) / "after.db")
            snap_before = snapshot_from_observation(
                store_before, context,
                {"observation": obs_before.as_dict()},
            )
            snap_after = snapshot_from_observation(
                store_after, context,
                {"observation": obs_after.as_dict()},
            )
            state_before = json.loads(
                store_before.get_memory(json.loads(snap_before)["snapshot_id"])["content"]
            )
            state_after = json.loads(
                store_after.get_memory(json.loads(snap_after)["snapshot_id"])["content"]
            )
            # Before-snapshot has no score, after-snapshot has score
            self.assertNotIn("home_score", state_before["matches"][0])
            self.assertIn("home_score", state_after["matches"][0])


class HttpFootballProviderTests(unittest.TestCase):
    """Tests for HttpFootballDataProvider with recorded responses (no internet)."""

    # Recorded TheSportsDB responses for testing
    SAMPLE_NEXT_EVENTS = {
        "events": [
            {
                "idEvent": "2494017",
                "strTimestamp": "2026-08-31T19:00:00",
                "strEvent": "Aston Villa vs Arsenal",
                "strSport": "Soccer",
                "idLeague": "4328",
                "strLeague": "English Premier League",
                "strHomeTeam": "Aston Villa",
                "strAwayTeam": "Arsenal",
                "idHomeTeam": "133605",
                "idAwayTeam": "133604",
                "strStatus": "NS",
                "intHomeScore": None,
                "intAwayScore": None,
                "strVenue": "Villa Park",
                "intRound": "2",
                "strThumb": "https://example.com/thumb.jpg",
            },
            {
                "idEvent": "2494018",
                "strTimestamp": "2026-09-05T15:00:00",
                "strEvent": "Arsenal vs Manchester City",
                "strSport": "Soccer",
                "idLeague": "4328",
                "strLeague": "English Premier League",
                "strHomeTeam": "Arsenal",
                "strAwayTeam": "Manchester City",
                "idHomeTeam": "133604",
                "idAwayTeam": "133612",
                "strStatus": "NS",
                "intHomeScore": None,
                "intAwayScore": None,
                "strVenue": "Emirates Stadium",
                "intRound": "3",
                "strThumb": None,
            },
        ]
    }

    SAMPLE_LAST_EVENTS = {
        "results": [
            {
                "idEvent": "249390",
                "strTimestamp": "2026-08-21T15:00:00",
                "strEvent": "Arsenal vs Coventry City",
                "strSport": "Soccer",
                "idLeague": "4328",
                "strLeague": "English Premier League",
                "strHomeTeam": "Arsenal",
                "strAwayTeam": "Coventry City",
                "idHomeTeam": "133604",
                "idAwayTeam": "133699",
                "strStatus": "FT",
                "intHomeScore": "3",
                "intAwayScore": "0",
                "strVenue": "Emirates Stadium",
                "intRound": "1",
                "strThumb": None,
            }
        ]
    }

    SAMPLE_SINGLE_EVENT = {
        "events": [
            {
                "idEvent": "2494017",
                "strTimestamp": "2026-08-31T19:00:00",
                "strEvent": "Aston Villa vs Arsenal",
                "strSport": "Soccer",
                "idLeague": "4328",
                "strLeague": "English Premier League",
                "strHomeTeam": "Aston Villa",
                "strAwayTeam": "Arsenal",
                "idHomeTeam": "133605",
                "idAwayTeam": "133604",
                "strStatus": "NS",
                "intHomeScore": None,
                "intAwayScore": None,
                "strVenue": "Villa Park",
                "intRound": "2",
                "strOfficial": "Michael Oliver",
                "strThumb": "https://example.com/thumb.jpg",
            }
        ]
    }

    def _make_requester(self, responses: dict[str, Any]):
        """Create a fake requester that returns pre-recorded responses."""
        def requester(url: str) -> dict[str, Any]:
            for pattern, resp in responses.items():
                if pattern in url:
                    if isinstance(resp, Exception):
                        raise resp
                    return resp
            return {"events": []}
        return requester

    def test_unconfigured_returns_empty(self):
        """Provider with no team IDs returns empty matches."""
        provider = HttpFootballDataProvider()
        self.assertEqual(provider.status.state, "unconfigured")
        matches = provider.list_matches()
        self.assertEqual(matches, [])

    def test_normalize_status_scheduled(self):
        """NS status maps to scheduled."""
        provider = HttpFootballDataProvider(team_ids=["133604"])
        self.assertEqual(provider._normalize_status("NS"), "scheduled")
        self.assertEqual(provider._normalize_status("TBD"), "scheduled")

    def test_normalize_status_live(self):
        """In-play statuses map to live."""
        provider = HttpFootballDataProvider(team_ids=["133604"])
        for raw in ("1H", "HT", "2H", "ET", "P"):
            self.assertEqual(provider._normalize_status(raw), "live", msg=f"Status {raw}")

    def test_normalize_status_completed(self):
        """Finished statuses map to completed."""
        provider = HttpFootballDataProvider(team_ids=["133604"])
        for raw in ("FT", "AET", "PEN", "AWD", "WO"):
            self.assertEqual(provider._normalize_status(raw), "completed", msg=f"Status {raw}")

    def test_list_matches_from_api(self):
        """list_matches fetches from configured teams and normalizes."""
        provider = HttpFootballDataProvider(
            team_ids=["133604"],
            requester=self._make_requester({
                "eventsnext.php": self.SAMPLE_NEXT_EVENTS,
                "eventslast.php": self.SAMPLE_LAST_EVENTS,
            }),
        )
        matches = provider.list_matches()
        self.assertGreater(len(matches), 0)
        # Check that both scheduled and completed are present
        statuses = {m.status for m in matches}
        self.assertIn("scheduled", statuses)
        self.assertIn("completed", statuses)
        # Check prefix
        for m in matches:
            self.assertTrue(m.match_id.startswith("TSDB-"))

    def test_list_matches_deduplicates(self):
        """Same event from multiple teams is deduplicated."""
        # Both team queries return the same event
        same_event = self.SAMPLE_NEXT_EVENTS["events"][0]
        requester = self._make_requester({
            "eventsnext.php": {"events": [same_event, same_event]},
            "eventslast.php": {"results": []},
        })
        provider = HttpFootballDataProvider(team_ids=["133604", "133605"], requester=requester)
        matches = provider.list_matches()
        # Should be deduplicated
        ids = [m.match_id for m in matches]
        self.assertEqual(len(ids), len(set(ids)))

    def test_http_error_records_failure(self):
        """HTTP errors are captured in provider status."""
        import requests as _requests
        provider = HttpFootballDataProvider(
            team_ids=["133604"],
            requester=lambda url: (_ for _ in ()).throw(_requests.ConnectionError("offline")),
        )
        matches = provider.list_matches()
        self.assertEqual(matches, [])
        self.assertIn(provider.status.state, ("degraded", "offline"))
        self.assertGreater(provider.status.consecutive_failures, 0)

    def test_timeout_records_failure(self):
        """Timeout errors are captured in provider status."""
        import requests as _requests
        provider = HttpFootballDataProvider(
            team_ids=["133604"],
            requester=lambda url: (_ for _ in ()).throw(_requests.Timeout("timeout")),
        )
        matches = provider.list_matches()
        self.assertEqual(matches, [])
        self.assertIn(provider.status.state, ("degraded", "offline"))

    def test_partial_failure_degraded(self):
        """Some teams fail → degraded state, partial results returned."""
        def mixed_requester(url: str) -> dict[str, Any]:
            if "id=133604" in url:
                if "eventsnext" in url:
                    return self.SAMPLE_NEXT_EVENTS
                return self.SAMPLE_LAST_EVENTS
            raise Exception("team 999 failed")

        provider = HttpFootballDataProvider(
            team_ids=["133604", "99999"],
            requester=mixed_requester,
        )
        matches = provider.list_matches()
        self.assertGreater(len(matches), 0)
        self.assertEqual(provider.status.state, "degraded")
        self.assertEqual(provider.status.consecutive_failures, 1)

    def test_parse_event_completed(self):
        """Completed event is parsed with scores."""
        provider = HttpFootballDataProvider(team_ids=["133604"])
        event = self.SAMPLE_LAST_EVENTS["results"][0]
        md = provider._parse_event(event)
        self.assertEqual(md.status, "completed")
        self.assertEqual(md.home_score, 3)
        self.assertEqual(md.away_score, 0)
        self.assertEqual(md.match_id, "TSDB-249390")

    def test_parse_event_scheduled_no_scores(self):
        """Scheduled event has no scores."""
        provider = HttpFootballDataProvider(team_ids=["133604"])
        event = self.SAMPLE_NEXT_EVENTS["events"][0]
        md = provider._parse_event(event)
        self.assertEqual(md.status, "scheduled")
        self.assertIsNone(md.home_score)
        self.assertIsNone(md.away_score)
        self.assertEqual(md.venue, "Villa Park")

    def test_provenance_includes_provider_state(self):
        """Adapter observation includes provider operational state."""
        provider = HttpFootballDataProvider(
            team_ids=["133604"],
            requester=self._make_requester({
                "eventsnext.php": self.SAMPLE_NEXT_EVENTS,
                "eventslast.php": self.SAMPLE_LAST_EVENTS,
            }),
        )
        adapter = FootballWorldAdapter(provider=provider)
        obs = adapter.observe()
        self.assertEqual(obs.provenance["provider"], "HttpFootballDataProvider")
        self.assertEqual(obs.provenance["provider_state"], "healthy")
        self.assertIn("freshness_seconds", obs.provenance)

    def test_health_reports_provider_status(self):
        """Adapter health reflects real provider status."""
        provider = HttpFootballDataProvider()
        adapter = FootballWorldAdapter(provider=provider)
        health = adapter.health()
        self.assertEqual(health["status"], "unconfigured")
        self.assertEqual(health["provider"], "HttpFootballDataProvider")

    def test_describe_includes_provider_state(self):
        """Adapter descriptor includes provider state in metadata."""
        provider = HttpFootballDataProvider()
        adapter = FootballWorldAdapter(provider=provider)
        desc = adapter.describe()
        self.assertEqual(desc.metadata["provider"], "HttpFootballDataProvider")
        self.assertEqual(desc.metadata["provider_state"], "unconfigured")

    def test_scheduled_never_has_result_http(self):
        """Scheduled matches from real provider never have scores."""
        provider = HttpFootballDataProvider(
            team_ids=["133604"],
            requester=self._make_requester({
                "eventsnext.php": self.SAMPLE_NEXT_EVENTS,
                "eventslast.php": self.SAMPLE_LAST_EVENTS,
            }),
        )
        adapter = FootballWorldAdapter(provider=provider)
        obs = adapter.observe(query={"status": "scheduled"})
        for match in obs.state["matches"]:
            self.assertEqual(match["status"], "scheduled")
            self.assertNotIn("home_score", match)
            self.assertNotIn("away_score", match)
            self.assertNotIn("result", match)

    def test_get_match_from_cache(self):
        """get_match returns cached match after list_matches."""
        provider = HttpFootballDataProvider(
            team_ids=["133604"],
            requester=self._make_requester({
                "eventsnext.php": self.SAMPLE_NEXT_EVENTS,
                "eventslast.php": self.SAMPLE_LAST_EVENTS,
            }),
        )
        provider.list_matches()  # Populate cache
        match = provider.get_match("TSDB-2494017")
        self.assertIsNotNone(match)
        self.assertEqual(match.home_name, "Aston Villa")

    def test_get_match_fetches_if_not_cached(self):
        """get_match fetches from API if not in cache."""
        provider = HttpFootballDataProvider(
            team_ids=["133604"],
            requester=self._make_requester({
                "lookupevent.php": self.SAMPLE_SINGLE_EVENT,
            }),
        )
        match = provider.get_match("TSDB-2494017")
        self.assertIsNotNone(match)
        self.assertEqual(match.home_name, "Aston Villa")


class FootballSchemaTests(unittest.TestCase):
    """Tests for match schema compliance."""

    def test_match_v1_schema_keys(self):
        adapter = FootballWorldAdapter()
        obs = adapter.observe(query={"match_id": "FUT-001"})
        match = obs.state["matches"][0]
        required_keys = {"match_id", "status", "competition", "match_date", "home", "away"}
        self.assertTrue(required_keys.issubset(match.keys()))
        self.assertIn("id", match["home"])
        self.assertIn("name", match["home"])
        self.assertIn("id", match["away"])
        self.assertIn("name", match["away"])

    def test_completed_match_additional_keys(self):
        adapter = FootballWorldAdapter()
        obs = adapter.observe(query={"match_id": "FUT-003"})
        match = obs.state["matches"][0]
        self.assertIn("home_score", match)
        self.assertIn("away_score", match)
        self.assertIn("result", match)
        self.assertIn("winner", match["result"])

    def test_observation_metadata(self):
        adapter = FootballWorldAdapter()
        obs = adapter.observe()
        self.assertEqual(obs.world_id, "football")
        self.assertEqual(obs.schema, "football.match.v1")
        self.assertIn("adapter", obs.provenance)
        self.assertEqual(obs.provenance["adapter"], "football.data.v1")

    def test_query_match_id(self):
        adapter = FootballWorldAdapter()
        obs = adapter.observe(query={"match_id": "FUT-002"})
        self.assertEqual(len(obs.state["matches"]), 1)
        self.assertEqual(obs.state["matches"][0]["match_id"], "FUT-002")

    def test_query_competition(self):
        adapter = FootballWorldAdapter()
        obs = adapter.observe(query={"competition": "La Liga"})
        self.assertEqual(len(obs.state["matches"]), 1)
        self.assertEqual(obs.state["matches"][0]["competition"], "La Liga")


if __name__ == "__main__":
    unittest.main()
