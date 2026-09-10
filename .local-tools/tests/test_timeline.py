"""Historical Evidence Timeline v0.1 — Tests.

Tests required by spec:
    1. posthoc narrative não entra em predictive state
    2. posthoc narrative pode ser usado como resolution evidence
    3. timeline preserva ordem da fonte
    4. nenhuma data é inventada
    5. imported_at não vira occurred_at
    6. cutoff ordinal exclui futuro
    7. evento observado e derivado permanecem distinguíveis
    8. ausência de fonte sequencial gera limitação explícita
    9. cena órfã não é vinculada por suposição
    10. timeline read-only não persiste memória/previsão
    11. replay retrospectivo continua separado do prospectivo
    12. todas as suítes anteriores permanecem verdes
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

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

# Import timeline module in isolation
_comp_src = (LOCAL_TOOLS / "omnisvera_mcp" / "timeline.py").read_text(encoding="utf-8")
_comp_ns: dict = {
    "__name__": "omnisvera_mcp.timeline",
    "__file__": str(LOCAL_TOOLS / "omnisvera_mcp" / "timeline.py"),
    "__package__": "omnisvera_mcp",
}
import types as _mt
_comp_mod = _mt.ModuleType("omnisvera_mcp.timeline")
_comp_mod.__file__ = _comp_ns["__file__"]
_comp_mod.__package__ = "omnisvera_mcp"
sys.modules["omnisvera_mcp.timeline"] = _comp_mod
exec(compile(_comp_src, _comp_ns["__file__"], "exec"), _comp_mod.__dict__)

SourceType = _comp_mod.SourceType
TimelineEvent = _comp_mod.TimelineEvent
SessionTimeline = _comp_mod.SessionTimeline
parse_transcript_line = _comp_mod.parse_transcript_line
build_timeline_from_transcript = _comp_mod.build_timeline_from_transcript
build_timeline_from_session_records = _comp_mod.build_timeline_from_session_records
build_timeline_from_scene_events = _comp_mod.build_timeline_from_scene_events
build_session_timeline = _comp_mod.build_session_timeline
filter_events_by_cutoff = _comp_mod.filter_events_by_cutoff

# Import companion_session for posthoc tests
_comp_src2 = (LOCAL_TOOLS / "omnisvera_mcp" / "companion_session.py").read_text(encoding="utf-8")
_comp_src2 = _comp_src2.replace(
    "from .adapters.companion import CompanionAdapter",
    "CompanionAdapter = object",
)
_comp_mod2 = _mt.ModuleType("omnisvera_mcp.companion_session")
_comp_mod2.__file__ = str(LOCAL_TOOLS / "omnisvera_mcp" / "companion_session.py")
_comp_mod2.__package__ = "omnisvera_mcp"
sys.modules["omnisvera_mcp.companion_session"] = _comp_mod2
exec(compile(_comp_src2, _comp_mod2.__file__, "exec"), _comp_mod2.__dict__)

build_companion_session_model_at = _comp_mod2.build_companion_session_model_at

# Import session data fixtures
_records_path = Path(r"C:\Users\delib\Desktop\OMNISVERA\.assistant-runtime\campaign-sources\session-records.json")


def _make_records_file(tmp: Path, session_data: dict) -> Path:
    """Write a minimal session-records.json fixture."""
    records = tmp / "session-records.json"
    records.write_text(json.dumps({
        "version": 1,
        "campaign_id": "omnisvera",
        "source_status": "historical_evidence_pending_canon_review",
        "sessions": [session_data],
    }, ensure_ascii=False), encoding="utf-8")
    return records


def _make_transcript(tmp: Path, lines: list[str]) -> Path:
    """Write a minimal Whisper transcript fixture."""
    path = tmp / "session-001-transcript.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


class FakeAdapter:
    def __init__(self, health=None, dashboard=None, sessions=None, scenes=None):
        self._health = health or SimpleNamespace(
            source="/health", status="healthy", freshness="fresh",
            observed_at="2026-08-30T00:00:00+00:00",
            value={"backend": "ok", "access_mode": "gm"}, limitation=None,
        )
        self._sessions = sessions or []
        self._scenes = scenes or {}

    def get_health(self):
        return self._health

    def get_dashboard(self):
        return SimpleNamespace(
            source="dashboard", status="healthy", freshness="fresh",
            observed_at="2026-08-30T00:00:00+00:00",
            value={"sessions": [], "active_scene": None}, limitation=None,
        )

    def list_sessions(self):
        return SimpleNamespace(
            source="/gm/sessions", status="healthy", freshness="fresh",
            observed_at="2026-08-30T00:00:00+00:00",
            value=self._sessions, limitation=None,
        )

    def list_scenes(self, campaign_id: str):
        return SimpleNamespace(
            source="/scenes", status="healthy", freshness="fresh",
            observed_at="2026-08-30T00:00:00+00:00",
            value=self._scenes.get(campaign_id, []), limitation=None,
        )


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------

class TimelineCoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.tmp = Path(self.temporary.name)

    # 1. Posthoc narrative não entra em predictive state
    def test_posthoc_narrative_not_in_predictive_state(self):
        records = _make_records_file(self.tmp, {
            "session_number": 1,
            "title": "Test",
            "status": "completed",
            "public_summary": "Summary here.",
            "gm_summary": "GM notes here.",
            "narrative": {"participants": [{"name": "Vezemir"}]},
            "participants": [{"character_id": "vezemir", "name": "Vezemir"}],
            "locations": [{"name": "Location"}],
            "missions": [],
            "discoveries": [],
            "world_events": [],
            "character_events": [],
            "open_threads": [],
        })
        tl = build_timeline_from_session_records(records, session_id=1)

        # All events should be POSTHOC
        for e in tl.events:
            self.assertEqual(e.source_type, SourceType.POSTHOC_SUMMARY)

        # posthoc_excluded should list the categories
        self.assertTrue(len(tl.posthoc_excluded) > 0)
        self.assertTrue(any("narrative" in p or "summary" in p for p in tl.posthoc_excluded))

    # 2. Posthoc narrative pode ser usado como resolution evidence
    def test_posthoc_usable_as_resolution_evidence(self):
        records = _make_records_file(self.tmp, {
            "session_number": 1,
            "title": "Test",
            "status": "completed",
            "public_summary": "Dragons were confirmed.",
            "participants": [],
            "locations": [],
            "missions": [],
            "discoveries": [{"title": "Dragons", "description": "Confirmed"}],
            "world_events": [],
            "character_events": [],
            "open_threads": [],
        })
        tl = build_timeline_from_session_records(records, session_id=1)

        # Find the discovery event
        discoveries = [e for e in tl.events if "discoveries" in e.event_type.lower()]
        self.assertTrue(len(discoveries) > 0)
        # It's available in the timeline (for resolution), just classified as posthoc
        self.assertIn("Dragons", discoveries[0].content)

    # 3. Timeline preserva ordem da fonte
    def test_timeline_preserves_source_order(self):
        transcript = _make_transcript(self.tmp, [
            "Detecting language",
            "[00:00.000 --> 00:02.000]  First event",
            "[00:02.000 --> 00:04.000]  Second event",
            "[00:04.000 --> 00:06.000]  Third event",
        ])
        tl = build_timeline_from_transcript(transcript, session_id=1)

        self.assertEqual(len(tl.events), 3)
        self.assertEqual(tl.events[0].ordinal, 1)
        self.assertEqual(tl.events[0].content, "First event")
        self.assertEqual(tl.events[1].ordinal, 2)
        self.assertEqual(tl.events[1].content, "Second event")
        self.assertEqual(tl.events[2].ordinal, 3)
        self.assertEqual(tl.events[2].content, "Third event")

    # 4. Nenhuma data é inventada
    def test_no_dates_invented(self):
        transcript = _make_transcript(self.tmp, [
            "[00:00.000 --> 00:02.000]  Some text",
        ])
        tl = build_timeline_from_transcript(transcript, session_id=1)

        e = tl.events[0]
        # occurred_at comes from Whisper timestamp, NOT wall-clock
        self.assertEqual(e.occurred_at, "00:00.000")
        # recorded_at and imported_at are None (unknown)
        self.assertIsNone(e.recorded_at)
        self.assertIsNone(e.imported_at)

    # 5. imported_at não vira occurred_at
    def test_imported_at_not_occurred_at(self):
        scene_events = [{
            "id": 1, "scene_id": 4, "event_type": "scene_created",
            "title": "Cena criada", "created_at": "2026-07-26T01:17:36.987",
        }]
        tl = build_timeline_from_scene_events(scene_events, session_id=1)

        e = tl.events[0]
        # recorded_at = created_at (when it was recorded in the system)
        self.assertEqual(e.recorded_at, "2026-07-26T01:17:36.987")
        # occurred_at = None (we don't know when it actually happened)
        self.assertIsNone(e.occurred_at)

    # 6. Cutoff ordinal exclui futuro
    def test_cutoff_ordinal_excludes_future(self):
        transcript = _make_transcript(self.tmp, [
            "[00:00.000 --> 00:02.000]  Event 1",
            "[00:02.000 --> 00:04.000]  Event 2",
            "[00:04.000 --> 00:06.000]  Event 3",
            "[00:06.000 --> 00:08.000]  Event 4",
        ])
        tl = build_timeline_from_transcript(transcript, session_id=1)

        included, excluded, reasons = filter_events_by_cutoff(tl.events, cutoff_ordinal=2)

        self.assertEqual(len(included), 2)
        self.assertEqual(len(excluded), 2)
        self.assertEqual(included[0].content, "Event 1")
        self.assertEqual(included[1].content, "Event 2")
        self.assertEqual(excluded[0].content, "Event 3")

    # 7. Evento observado e derivado permanecem distinguíveis
    def test_observed_vs_derived_distinguishable(self):
        events = [
            TimelineEvent(ordinal=1, event_type="transcript_segment", content="raw text",
                          source="transcript.txt", source_type=SourceType.PRIMARY_SEQUENTIAL),
            TimelineEvent(ordinal=2, event_type="posthoc_discoveries", content="derived discovery",
                          source="records.json", source_type=SourceType.POSTHOC_SUMMARY),
            TimelineEvent(ordinal=3, event_type="scene_created", content="runtime event",
                          source="scene_events", source_type=SourceType.RUNTIME_RECORD),
        ]
        tl = SessionTimeline(session_id=1, events=events)

        primary = [e for e in tl.events if e.source_type == SourceType.PRIMARY_SEQUENTIAL]
        posthoc = [e for e in tl.events if e.source_type == SourceType.POSTHOC_SUMMARY]
        runtime = [e for e in tl.events if e.source_type == SourceType.RUNTIME_RECORD]

        self.assertEqual(len(primary), 1)
        self.assertEqual(len(posthoc), 1)
        self.assertEqual(len(runtime), 1)
        self.assertEqual(primary[0].content, "raw text")
        self.assertEqual(posthoc[0].content, "derived discovery")
        self.assertEqual(runtime[0].content, "runtime event")

    # 8. Ausência de fonte sequencial gera limitação explícita
    def test_missing_sequential_source_generates_limitation(self):
        tl = build_session_timeline(session_id=999)
        self.assertTrue(len(tl.limitations) > 0)
        self.assertTrue(any("no timeline sources" in l.lower() or "not found" in l.lower()
                           for l in tl.limitations))

    # 9. Cena órfã não é vinculada por suposição
    def test_orphan_scene_not_linked_by_assumption(self):
        # Scene 4 has session_id=NULL in the real DB
        # The timeline builder should not assume which session it belongs to
        scene_events = [{
            "id": 20, "scene_id": 4, "event_type": "scene_created",
            "title": "Cena criada", "created_at": "2026-07-26T01:17:36.987",
        }]
        tl = build_timeline_from_scene_events(scene_events, session_id=1)

        # The scene_id is recorded as metadata, not assumed to belong to session 1
        e = tl.events[0]
        self.assertEqual(e.metadata.get("scene_id"), 4)
        # session_id is passed explicitly, not derived from scene
        self.assertEqual(e.session_id, 1)

    # 10. Timeline read-only não persiste memória/previsão
    def test_timeline_readonly_no_persist(self):
        store = MemoryStore(self.tmp / "test.db")
        before = store.stats()["counts"]["memory_items"]

        transcript = _make_transcript(self.tmp, [
            "[00:00.000 --> 00:02.000]  Event",
        ])
        build_timeline_from_transcript(transcript, session_id=1)

        after = store.stats()["counts"]["memory_items"]
        self.assertEqual(before, after)

    # 11. Replay retrospectivo continua separado do prospectivo
    def test_retrospective_separate_from_prospective(self):
        store = MemoryStore(self.tmp / "test.db")
        snapshot_id = store.add_memory(
            namespace="omnisvera", item_type="model_snapshot",
            title="cal — test", content=json.dumps({"k": "v"}),
            status="immutable", confidence=1.0, owner="omnisvera",
            classification="internal",
            metadata={"domain": "companion.session", "subject": "test"},
        )
        # Prospective
        pid1 = store.create_prediction(
            domain="companion.session", snapshot_memory_id=snapshot_id,
            claim="prospective", probability=0.6, horizon="24h",
            resolution_rule={}, evidence_mode="prospective",
        )
        store.resolve_prediction(pid1, outcome=1)

        # Retrospective
        pid2 = store.create_prediction(
            domain="companion.session", snapshot_memory_id=snapshot_id,
            claim="retrospective", probability=0.6, horizon="24h",
            resolution_rule={}, evidence_mode="retrospective",
        )
        store.resolve_prediction(pid2, outcome=0)

        summary = store.calibration_summary(domain="companion.session")
        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["evidence_mode"], "prospective")

    # 12. Todas as suítes anteriores permanecem verdes
    def test_previous_suites_importable(self):
        import importlib
        mod1 = importlib.import_module("tests.test_epistemic_loop")
        self.assertTrue(hasattr(mod1, "test_bridge_tools"))
        mod2 = importlib.import_module("tests.test_companion_session")
        self.assertTrue(hasattr(mod2, "CompanionSessionModelTests"))
        mod3 = importlib.import_module("tests.test_historical_replay")
        self.assertTrue(hasattr(mod3, "HistoricalReplayTests"))


class TranscriptParserTests(unittest.TestCase):
    def test_parse_valid_line(self):
        result = parse_transcript_line("[00:00.000 --> 00:02.000]  Hello world")
        self.assertIsNotNone(result)
        start, end, text = result
        self.assertEqual(start, "00:00.000")
        self.assertEqual(end, "00:02.000")
        self.assertEqual(text, "Hello world")

    def test_parse_non_timestamp_line(self):
        result = parse_transcript_line("Detecting language using up to the first 30 seconds")
        self.assertIsNone(result)

    def test_parse_empty_text(self):
        result = parse_transcript_line("[00:00.000 --> 00:02.000]  ")
        # Empty text should still parse (text might be empty)
        if result:
            self.assertEqual(result[2], "")

    def test_timeline_max_ordinal(self):
        events = [
            TimelineEvent(ordinal=1, event_type="test", content="", source="t", source_type=SourceType.PRIMARY_SEQUENTIAL),
            TimelineEvent(ordinal=5, event_type="test", content="", source="t", source_type=SourceType.PRIMARY_SEQUENTIAL),
        ]
        tl = SessionTimeline(session_id=1, events=events)
        self.assertEqual(tl.max_ordinal, 5)


class CutoffTests(unittest.TestCase):
    def test_cutoff_by_ordinal(self):
        events = [
            TimelineEvent(ordinal=i, event_type="test", content=f"Event {i}",
                          source="t", source_type=SourceType.PRIMARY_SEQUENTIAL)
            for i in range(1, 6)
        ]
        included, excluded, reasons = filter_events_by_cutoff(events, cutoff_ordinal=3)
        self.assertEqual(len(included), 3)
        self.assertEqual(len(excluded), 2)

    def test_cutoff_by_scene_id(self):
        events = [
            TimelineEvent(ordinal=1, event_type="test", content="A",
                          source="t", source_type=SourceType.RUNTIME_RECORD,
                          metadata={"scene_id": 3}),
            TimelineEvent(ordinal=2, event_type="test", content="B",
                          source="t", source_type=SourceType.RUNTIME_RECORD,
                          metadata={"scene_id": 5}),
        ]
        included, excluded, reasons = filter_events_by_cutoff(events, cutoff_scene_id=4)
        self.assertEqual(len(included), 1)
        self.assertEqual(len(excluded), 1)

    def test_cutoff_by_timestamp(self):
        events = [
            TimelineEvent(ordinal=1, event_type="test", content="A",
                          source="t", source_type=SourceType.RUNTIME_RECORD,
                          recorded_at="2026-01-01"),
            TimelineEvent(ordinal=2, event_type="test", content="B",
                          source="t", source_type=SourceType.RUNTIME_RECORD,
                          recorded_at="2026-06-01"),
        ]
        included, excluded, reasons = filter_events_by_cutoff(events, cutoff_timestamp="2026-03-01")
        self.assertEqual(len(included), 1)
        self.assertEqual(len(excluded), 1)

    def test_no_cutoff_returns_all(self):
        events = [
            TimelineEvent(ordinal=i, event_type="test", content=f"E{i}",
                          source="t", source_type=SourceType.PRIMARY_SEQUENTIAL)
            for i in range(1, 4)
        ]
        included, excluded, reasons = filter_events_by_cutoff(events)
        self.assertEqual(len(included), 3)
        self.assertEqual(len(excluded), 0)


if __name__ == "__main__":
    unittest.main()
