"""Historical Replay / Backtest v0.1 — Tests.

Tests required by spec:
    1. historical reconstruction produces valid model
    2. cutoff excludes subsequent scenes
    3. post-cutoff data does not leak into snapshot
    4. absent temporal info does not generate invention
    5. historical model does not persist automatically
    6. backtest creates prediction evidence_mode=retrospective
    7. resolution calculates Brier normally
    8. backtest does not alter default prospective calibration
    9. historical provenance is preserved
    10. v0.1/v0.2/Companion Session suites stay green
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
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

# Import companion_session module in isolation
_comp_src = (LOCAL_TOOLS / "omnisvera_mcp" / "companion_session.py").read_text(encoding="utf-8")
_comp_src = _comp_src.replace(
    "from .adapters.companion import CompanionAdapter",
    "CompanionAdapter = object  # stub for testing",
)
_comp_ns: dict = {
    "__name__": "omnisvera_mcp.companion_session",
    "__file__": str(LOCAL_TOOLS / "omnisvera_mcp" / "companion_session.py"),
    "__package__": "omnisvera_mcp",
}
import types as _mt
_comp_mod = _mt.ModuleType("omnisvera_mcp.companion_session")
_comp_mod.__file__ = _comp_ns["__file__"]
_comp_mod.__package__ = "omnisvera_mcp"
sys.modules["omnisvera_mcp.companion_session"] = _comp_mod
exec(compile(_comp_src, _comp_ns["__file__"], "exec"), _comp_mod.__dict__)

build_companion_session_model = _comp_mod.build_companion_session_model
build_companion_session_model_at = _comp_mod.build_companion_session_model_at
_filter_scenes_by_cutoff = _comp_mod._filter_scenes_by_cutoff
_filter_actions_by_cutoff = _comp_mod._filter_actions_by_cutoff
_filter_events_by_cutoff = _comp_mod._filter_events_by_cutoff


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------

def _make_health_obs(value=None):
    return SimpleNamespace(
        source="/health", status="healthy", freshness="fresh",
        observed_at="2026-08-30T00:00:00+00:00",
        value=value or {"backend": "ok", "access_mode": "gm"},
        limitation=None,
    )


def _make_obs(value, status="healthy", source="test"):
    return SimpleNamespace(
        source=source, status=status,
        freshness="fresh" if status == "healthy" else "unavailable",
        observed_at="2026-08-30T00:00:00+00:00",
        value=value, limitation=None if status == "healthy" else "offline",
    )


class FakeAdapter:
    def __init__(self, health=None, dashboard=None, sessions=None, scenes=None):
        self._health = health or _make_health_obs()
        self._dashboard = dashboard
        self._sessions = sessions or []
        self._scenes = scenes or {}

    def get_health(self):
        return self._health

    def get_dashboard(self):
        return self._dashboard or _make_obs({"sessions": [], "active_scene": None})

    def list_sessions(self):
        return _make_obs(self._sessions, source="/gm/sessions")

    def get_session(self, session_id: int):
        for s in self._sessions:
            if s.get("id") == session_id:
                return _make_obs(s)
        return _make_obs(None, status="offline")

    def list_scenes(self, campaign_id: str):
        return _make_obs(self._scenes.get(campaign_id, []), source="/scenes")


def _session_1():
    return {
        "id": 1, "title": "A Ruína Sob a Estrada", "session_number": 1,
        "status": "completed", "campaign_id": "omnisvera",
        "created_at": "2026-08-30T14:32:23.124",
        "public_summary": "Road collapse revealed ruins.",
        "gm_summary": "Auto-transcription record.",
        "narrative": {
            "participants": ["Vezemir", "Varkh Nimalis", "Raziel"],
            "locations": ["Estrada das caravanas", "Ruínas soterradas"],
            "missions": [{"title": "Investigar as ruínas", "status": "active"}],
            "open_threads": ["Odran's disappearance", "Golem's origin"],
        },
    }


def _session_2():
    return {
        "id": 2, "title": "A Party Toma Forma", "session_number": 2,
        "status": "completed", "campaign_id": "omnisvera",
        "created_at": "2026-08-30T14:32:23.159",
        "public_summary": "Exploration continued.",
        "gm_summary": "Auto-transcription record.",
        "narrative": {
            "participants": ["Vezemir", "Varkh Nimalis", "Raziel", "Morthak"],
            "locations": ["Ruínas soterradas"],
            "missions": [{"title": "Explorar as ruínas", "status": "active"}],
            "open_threads": ["Original function of ruins"],
        },
    }


def _scene_3(session_id=1):
    return {
        "id": 3, "session_id": session_id, "title": "Cena 3",
        "location_name": "Corredor escuro", "status": "resolved",
        "created_at": "2026-08-30T14:40:00+00:00",
        "participants": [
            {"participant_type": "character", "public_label": "Vezemir", "character_id": "vezemir"},
        ],
        "actions": [
            {"id": 10, "action_type": "exploration", "description": "Investigar corredor",
             "status": "resolved", "actor_role": "player", "scene_id": 3, "created_at": "2026-08-30T14:45:00+00:00"},
        ],
        "events": [
            {"id": 20, "event_type": "scene_created", "title": "Cena criada",
             "scene_id": 3, "created_at": "2026-08-30T14:40:00+00:00"},
        ],
    }


def _scene_4(session_id=1):
    return {
        "id": 4, "session_id": session_id, "title": "Cena 4",
        "location_name": "Sala do trono", "status": "active",
        "created_at": "2026-08-30T15:00:00+00:00",
        "participants": [
            {"participant_type": "character", "public_label": "Vezemir", "character_id": "vezemir"},
            {"participant_type": "npc", "public_label": "Endro", "npc_name": "Endro"},
        ],
        "actions": [
            {"id": 11, "action_type": "combat", "description": "Lutar contra o guardião",
             "status": "declared", "actor_role": "player", "scene_id": 4, "created_at": "2026-08-30T15:10:00+00:00"},
        ],
        "events": [
            {"id": 21, "event_type": "character_consequence", "title": "Vezemir fica Abalado",
             "scene_id": 4, "created_at": "2026-08-30T15:15:00+00:00"},
        ],
    }


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------

class HistoricalReplayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = MemoryStore(Path(self.temporary.name) / "test.db")

    # 1. Historical reconstruction produces valid model
    def test_historical_reconstruction_valid(self):
        adapter = FakeAdapter(
            sessions=[_session_1(), _session_2()],
            scenes={"omnisvera": [_scene_3(1), _scene_4(1)]},
        )
        model = build_companion_session_model_at(adapter, session_id=1)

        self.assertEqual(model.model.schema, "companion.session.v1")
        self.assertEqual(model.model.session_id, 1)
        self.assertEqual(model.model.session_title, "A Ruína Sob a Estrada")
        self.assertEqual(model.backtest.target_session_id, 1)
        self.assertEqual(model.backtest.data_available["session"], True)

    # 2. Cutoff excludes subsequent scenes
    def test_cutoff_excludes_subsequent_scenes(self):
        adapter = FakeAdapter(
            sessions=[_session_1()],
            scenes={"omnisvera": [_scene_3(1), _scene_4(1)]},
        )
        model = build_companion_session_model_at(adapter, session_id=1, cutoff_scene_id=3)

        # Scene 4 (id=4) should be excluded
        self.assertEqual(len(model.model.scenes), 1)
        self.assertEqual(model.model.scenes[0]["id"], 3)
        self.assertIn(4, model.backtest.excluded_scenes)

    # 3. Post-cutoff data does not leak into snapshot
    def test_no_lookahead_leakage(self):
        adapter = FakeAdapter(
            sessions=[_session_1()],
            scenes={"omnisvera": [_scene_3(1), _scene_4(1)]},
        )
        model = build_companion_session_model_at(adapter, session_id=1, cutoff_scene_id=3)

        # Scene 4's location should not appear
        self.assertNotEqual(model.model.location, "Sala do trono")
        # Scene 4's actions should not appear
        for t in model.model.active_threads:
            self.assertNotEqual(t.get("description"), "Lutar contra o guardião")
        # Scene 4 is excluded
        self.assertIn(4, model.backtest.excluded_scenes)
        # Only scene 3's participants should appear (scene 4's filtered out)
        participant_labels = [p.get("public_label") for p in model.model.participants]
        self.assertNotIn("Endro", participant_labels)

    # 4. Absent temporal info does not generate invention
    def test_absent_session_no_invention(self):
        adapter = FakeAdapter(sessions=[], scenes={})
        model = build_companion_session_model_at(adapter, session_id=999)

        self.assertEqual(model.model.session_id, 999)
        self.assertIsNone(model.model.session_title)
        self.assertEqual(model.model.participants, [])
        self.assertEqual(model.backtest.data_available["session"], False)

    # 5. Historical model does not persist automatically
    def test_no_auto_persist(self):
        before = self.store.stats()["counts"]["memory_items"]
        adapter = FakeAdapter(
            sessions=[_session_1()],
            scenes={"omnisvera": [_scene_3(1)]},
        )
        build_companion_session_model_at(adapter, session_id=1)
        after = self.store.stats()["counts"]["memory_items"]
        self.assertEqual(before, after)

    # 6. Backtest creates prediction evidence_mode=retrospective
    def test_backtest_creates_retrospective_prediction(self):
        snapshot_id = self.store.add_memory(
            namespace="omnisvera", item_type="model_snapshot",
            title="backtest — test", content=json.dumps({"k": "v"}),
            status="immutable", confidence=1.0, owner="omnisvera",
            classification="internal",
            metadata={"domain": "companion.session", "subject": "test"},
        )
        pid = self.store.create_prediction(
            domain="companion.session", snapshot_memory_id=snapshot_id,
            claim="test backtest", probability=0.7, horizon="next_session",
            resolution_rule={"metric": "test"}, evidence_mode="retrospective",
        )
        p = self.store.get_prediction(pid)
        self.assertEqual(p["evidence_mode"], "retrospective")

    # 7. Resolution calculates Brier normally
    def test_backtest_resolution_brier(self):
        snapshot_id = self.store.add_memory(
            namespace="omnisvera", item_type="model_snapshot",
            title="backtest — brier", content=json.dumps({"k": "v"}),
            status="immutable", confidence=1.0, owner="omnisvera",
            classification="internal",
            metadata={"domain": "companion.session", "subject": "brier"},
        )
        pid = self.store.create_prediction(
            domain="companion.session", snapshot_memory_id=snapshot_id,
            claim="brier test", probability=0.7, horizon="next_session",
            resolution_rule={"metric": "test"}, evidence_mode="retrospective",
        )
        result = self.store.resolve_prediction(pid, outcome=1, observed_value=1.0)
        expected_brier = round((0.7 - 1) ** 2, 8)
        self.assertAlmostEqual(result["resolution"]["calibration_score"], expected_brier, places=6)
        self.assertEqual(result["status"], "resolved")

    # 8. Backtest does not alter default prospective calibration
    def test_backtest_no_prospective_contamination(self):
        snapshot_id = self.store.add_memory(
            namespace="omnisvera", item_type="model_snapshot",
            title="cal — test", content=json.dumps({"k": "v"}),
            status="immutable", confidence=1.0, owner="omnisvera",
            classification="internal",
            metadata={"domain": "companion.session", "subject": "cal"},
        )
        # Prospective prediction
        pid1 = self.store.create_prediction(
            domain="companion.session", snapshot_memory_id=snapshot_id,
            claim="prospective", probability=0.6, horizon="24h",
            resolution_rule={}, evidence_mode="prospective",
        )
        self.store.resolve_prediction(pid1, outcome=1)

        # Retrospective backtest
        pid2 = self.store.create_prediction(
            domain="companion.session", snapshot_memory_id=snapshot_id,
            claim="retrospective", probability=0.6, horizon="24h",
            resolution_rule={}, evidence_mode="retrospective",
        )
        self.store.resolve_prediction(pid2, outcome=0)

        # Default calibration = prospective only
        summary = self.store.calibration_summary(domain="companion.session")
        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["evidence_mode"], "prospective")

    # 9. Historical provenance is preserved
    def test_historical_provenance(self):
        adapter = FakeAdapter(
            sessions=[_session_1()],
            scenes={"omnisvera": [_scene_3(1)]},
        )
        model = build_companion_session_model_at(
            adapter, session_id=1, cutoff_scene_id=3,
        )

        p = model.model.provenance
        self.assertEqual(p["domain"], "companion.session")
        self.assertEqual(p["reconstruction_mode"], "historical")
        self.assertEqual(p["target_session_id"], 1)
        self.assertEqual(p["cutoff_scene_id"], 3)
        self.assertIn("/gm/sessions", p["sources_consulted"])

    # 10. Previous suites stay green (import check)
    def test_previous_suites_importable(self):
        import importlib
        mod_epistemic = importlib.import_module("tests.test_epistemic_loop")
        self.assertTrue(hasattr(mod_epistemic, "test_bridge_tools"))
        mod_companion = importlib.import_module("tests.test_companion_session")
        self.assertTrue(hasattr(mod_companion, "CompanionSessionModelTests"))


class LeakageDetectionTests(unittest.TestCase):
    def test_filter_scenes_by_cutoff_id(self):
        scenes = [{"id": 1, "created_at": "2026-01-01"}, {"id": 2, "created_at": "2026-01-02"}, {"id": 3, "created_at": "2026-01-03"}]
        included, excluded, rules = _filter_scenes_by_cutoff(scenes, cutoff_scene_id=2, cutoff_timestamp=None)
        self.assertEqual(len(included), 2)
        self.assertEqual(len(excluded), 1)
        self.assertEqual(excluded, [3])

    def test_filter_scenes_by_cutoff_timestamp(self):
        scenes = [{"id": 1, "created_at": "2026-01-01"}, {"id": 2, "created_at": "2026-01-05"}]
        included, excluded, rules = _filter_scenes_by_cutoff(scenes, cutoff_scene_id=None, cutoff_timestamp="2026-01-03")
        self.assertEqual(len(included), 1)
        self.assertEqual(len(excluded), 1)

    def test_filter_actions_by_scene_eligibility(self):
        actions = [{"id": 1, "scene_id": 3, "created_at": "2026-01-01"}, {"id": 2, "scene_id": 4, "created_at": "2026-01-01"}]
        included, excluded, rules = _filter_actions_by_cutoff(actions, eligible_scene_ids={3}, cutoff_timestamp=None)
        self.assertEqual(len(included), 1)
        self.assertEqual(excluded, [2])

    def test_filter_events_by_timestamp(self):
        events = [{"id": 1, "scene_id": 3, "created_at": "2026-01-01"}, {"id": 2, "scene_id": 3, "created_at": "2026-01-10"}]
        included, excluded, rules = _filter_events_by_cutoff(events, eligible_scene_ids={3}, cutoff_timestamp="2026-01-05")
        self.assertEqual(len(included), 1)
        self.assertEqual(excluded, [2])


if __name__ == "__main__":
    unittest.main()
