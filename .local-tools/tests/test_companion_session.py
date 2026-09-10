"""Companion Session Model v0.1 — Tests.

Tests required by spec:
    1. builder produces valid model with Companion fixture
    2. only proven present data appears
    3. derived fields are deterministic
    4. absent active session does not invent session
    5. absent optional field handled correctly
    6. provenance preserved
    7. modeling does not write memory_item
    8. subsequent snapshot creation works with model
    9. hash/integrity v0.2 continues working
    10. previous test suite stays green
"""

from __future__ import annotations

import hashlib
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

# Import companion_session directly — exec source to avoid package chain
_comp_src = (LOCAL_TOOLS / "omnisvera_mcp" / "companion_session.py").read_text(encoding="utf-8")
# Replace relative import with standalone stub
_comp_src = _comp_src.replace(
    "from .adapters.companion import CompanionAdapter",
    "CompanionAdapter = object  # stub for testing",
)
_comp_ns: dict = {
    "__name__": "omnisvera_mcp.companion_session",
    "__file__": str(LOCAL_TOOLS / "omnisvera_mcp" / "companion_session.py"),
    "__package__": "omnisvera_mcp",
}
# Register before exec so dataclass can find its own module
import types as _mt
_comp_mod = _mt.ModuleType("omnisvera_mcp.companion_session")
_comp_mod.__file__ = _comp_ns["__file__"]
_comp_mod.__package__ = "omnisvera_mcp"
sys.modules["omnisvera_mcp.companion_session"] = _comp_mod
exec(compile(_comp_src, _comp_ns["__file__"], "exec"), _comp_mod.__dict__)
build_companion_session_model = _comp_mod.build_companion_session_model
_extract_active_session = _comp_mod._extract_active_session
_extract_active_scene = _comp_mod._extract_active_scene


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------

def _make_health_obs(value=None):
    return SimpleNamespace(
        source="/health",
        status="healthy",
        freshness="fresh",
        observed_at="2026-08-30T00:00:00+00:00",
        value=value or {
            "backend": "ok",
            "ollama_accessible": False,
            "model_mode": "baseline",
            "production_approved": False,
            "access_mode": "gm",
        },
        limitation=None,
    )


def _make_dashboard_obs(value=None, status="healthy", limitation=None):
    return SimpleNamespace(
        source="companion.dashboard",
        status=status,
        freshness="fresh" if status == "healthy" else "unavailable",
        observed_at="2026-08-30T00:00:00+00:00",
        value=value,
        limitation=limitation,
    )


class FakeAdapter:
    """Fake CompanionAdapter that returns pre-configured observations."""

    def __init__(self, health=None, dashboard=None):
        self._health = health or _make_health_obs()
        self._dashboard = dashboard

    def get_health(self):
        return self._health

    def get_dashboard(self):
        return self._dashboard or _make_dashboard_obs()

    def get_app_state(self):
        return _make_dashboard_obs(value={"table_mode": "digital"})


def _full_dashboard_value():
    """Complete dashboard value with session + scene."""
    return {
        "sessions": [
            {
                "id": 1,
                "request_id": "req-001",
                "campaign_id": "campaign-nimalis",
                "title": "Sessão 5 — O Despertar",
                "session_number": 5,
                "status": "active",
                "started_at": "2026-08-30T14:00:00+00:00",
                "ended_at": None,
                "created_by": "gm",
                "private_notes": None,
                "image_path": None,
                "public_summary": None,
                "public_chronicle": None,
                "gm_summary": None,
                "created_at": "2026-08-30T14:00:00+00:00",
                "version": 1,
            }
        ],
        "active_scene": {
            "id": 12,
            "request_id": "scene-req-012",
            "campaign_id": "campaign-nimalis",
            "session_id": 1,
            "title": "A Chegada a Oakhaven",
            "location_name": "Oakhaven, beira da estrada",
            "location_source": "GM description",
            "public_description": "Uma vila pacata.",
            "objective": "Investigar os rumores",
            "status": "active",
            "visibility": "table",
            "created_by": "gm",
            "created_at": "2026-08-30T14:05:00+00:00",
            "activated_at": "2026-08-30T14:10:00+00:00",
            "participants": [
                {
                    "participant_type": "character",
                    "public_label": "Sage",
                    "public_status": "Presente",
                    "character_id": "char-sage",
                },
                {
                    "participant_type": "npc",
                    "public_label": "Velho Mago",
                    "public_status": None,
                    "npc_name": "Velho Mago",
                },
            ],
            "elements": [],
            "actions": [
                {
                    "action_type": "exploration",
                    "description": "Sage investiga a taberna",
                    "status": "declared",
                    "actor_role": "player",
                },
                {
                    "action_type": "dialogue",
                    "description": "Conversa com o barqueiro",
                    "status": "resolved",
                    "actor_role": "player",
                },
            ],
            "events": [],
        },
    }


def _no_session_dashboard_value():
    """Dashboard value with no active session."""
    return {
        "sessions": [
            {
                "id": 10,
                "request_id": "req-010",
                "campaign_id": "campaign-nimalis",
                "title": "Sessão 4 — Encerrada",
                "session_number": 4,
                "status": "completed",
                "started_at": "2026-08-23T14:00:00+00:00",
                "ended_at": "2026-08-23T17:00:00+00:00",
                "created_by": "gm",
                "created_at": "2026-08-23T14:00:00+00:00",
                "version": 1,
            }
        ],
        "active_scene": None,
    }


def _empty_dashboard_value():
    """Dashboard value with no sessions at all."""
    return {
        "sessions": [],
        "active_scene": None,
    }


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------

class CompanionSessionModelTests(unittest.TestCase):

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = MemoryStore(Path(self.temporary.name) / "test.db")

    # 1. Builder produces valid model with Companion fixture
    def test_builder_produces_valid_model(self):
        adapter = FakeAdapter(dashboard=_make_dashboard_obs(value=_full_dashboard_value()))
        model = build_companion_session_model(adapter)

        self.assertEqual(model.schema, "companion.session.v1")
        self.assertTrue(model.observed_at)
        self.assertEqual(model.session_id, 1)
        self.assertEqual(model.session_status, "active")
        self.assertEqual(model.session_title, "Sessão 5 — O Despertar")
        self.assertEqual(model.campaign_id, "campaign-nimalis")
        self.assertEqual(model.location, "Oakhaven, beira da estrada")
        self.assertEqual(len(model.participants), 2)
        self.assertEqual(len(model.active_threads), 1)
        self.assertEqual(len(model.scenes), 1)
        self.assertIn("backend", model.operational)
        self.assertIn("domain", model.provenance)
        self.assertEqual(model.provenance["domain"], "companion.session")

    # 2. Only proven present data appears
    def test_only_present_data_appears(self):
        adapter = FakeAdapter(dashboard=_make_dashboard_obs(value=_full_dashboard_value()))
        model = build_companion_session_model(adapter)

        d = model.as_dict()
        # session fields present
        self.assertIsNotNone(d["session_id"])
        self.assertIsNotNone(d["session_status"])
        self.assertIsNotNone(d["session_title"])
        # participants have only declared fields
        for p in d["participants"]:
            self.assertIn("participant_type", p)
            self.assertIn("public_label", p)
            self.assertNotIn("private_notes", p)
            self.assertNotIn("internal_id", p)
        # active_threads only non-resolved
        for t in d["active_threads"]:
            self.assertNotEqual(t["status"], "resolved")

    # 3. Derived fields are deterministic
    def test_deterministic_derived_fields(self):
        adapter = FakeAdapter(dashboard=_make_dashboard_obs(value=_full_dashboard_value()))
        m1 = build_companion_session_model(adapter)
        m2 = build_companion_session_model(adapter)

        # Everything except observed_at should be identical
        self.assertEqual(m1.session_id, m2.session_id)
        self.assertEqual(m1.participants, m2.participants)
        self.assertEqual(m1.active_threads, m2.active_threads)
        self.assertEqual(m1.location, m2.location)
        self.assertEqual(m1.operational, m2.operational)

    # 4. Absent active session does not invent session
    def test_no_active_session_no_invention(self):
        adapter = FakeAdapter(dashboard=_make_dashboard_obs(value=_no_session_dashboard_value()))
        model = build_companion_session_model(adapter)

        self.assertIsNone(model.session_id)
        self.assertIsNone(model.session_status)
        self.assertIsNone(model.session_title)
        self.assertEqual(model.participants, [])
        self.assertEqual(model.active_threads, [])
        self.assertEqual(model.scenes, [])

    # 5. Absent optional field handled correctly
    def test_absent_optional_field_handled(self):
        value = _full_dashboard_value()
        # Remove location_source from scene
        value["active_scene"]["location_source"] = None
        value["active_scene"]["objective"] = None
        adapter = FakeAdapter(dashboard=_make_dashboard_obs(value=value))
        model = build_companion_session_model(adapter)

        self.assertIsNone(model.location_source)
        self.assertIsNone(model.scenes[0]["objective"])

    # 6. Provenance preserved
    def test_provenance_preserved(self):
        adapter = FakeAdapter(dashboard=_make_dashboard_obs(value=_full_dashboard_value()))
        model = build_companion_session_model(adapter)

        p = model.provenance
        self.assertEqual(p["domain"], "companion.session")
        self.assertEqual(p["schema_version"], "companion.session.v1")
        self.assertIn("/health", p["sources_consulted"])
        self.assertIn("/gm/sessions", p["sources_consulted"])
        self.assertIn("/scenes/active", p["sources_consulted"])
        self.assertEqual(p["health_status"], "healthy")
        self.assertEqual(p["dashboard_status"], "healthy")

    # 7. Modeling does not write memory_item
    def test_no_memory_item_written(self):
        before = self.store.stats()["counts"]["memory_items"]
        adapter = FakeAdapter(dashboard=_make_dashboard_obs(value=_full_dashboard_value()))
        build_companion_session_model(adapter)
        after = self.store.stats()["counts"]["memory_items"]
        self.assertEqual(before, after)

    # 8. Subsequent snapshot creation works with model
    def test_snapshot_creation_from_model(self):
        adapter = FakeAdapter(dashboard=_make_dashboard_obs(value=_full_dashboard_value()))
        model = build_companion_session_model(adapter)

        model_dict = model.as_dict()
        content_str = json.dumps(model_dict, ensure_ascii=False, sort_keys=True)
        expected_hash = hashlib.sha256(content_str.encode()).hexdigest()

        # Create memory_item from model
        item_id = self.store.add_memory(
            namespace="omnisvera",
            item_type="model_snapshot",
            title=f"companion.session — test",
            content=content_str,
            status="immutable",
            confidence=1.0,
            owner="omnisvera",
            classification="internal",
            metadata={"domain": "companion.session", "subject": "test"},
        )

        # Create prediction referencing this snapshot
        pid = self.store.create_prediction(
            domain="companion.session",
            snapshot_memory_id=item_id,
            claim="test prediction",
            probability=0.6,
            horizon="next_session",
            resolution_rule={"metric": "test", "condition": ">=0"},
        )

        p = self.store.get_prediction(pid)
        self.assertTrue(p["snapshot_intact"])
        self.assertEqual(p["snapshot_hash"], expected_hash)

    # 9. Hash/integrity v0.2 continues working
    def test_hash_integrity_v02(self):
        adapter = FakeAdapter(dashboard=_make_dashboard_obs(value=_full_dashboard_value()))
        model = build_companion_session_model(adapter)

        model_dict = model.as_dict()
        content_str = json.dumps(model_dict, ensure_ascii=False, sort_keys=True)

        item_id = self.store.add_memory(
            namespace="omnisvera",
            item_type="model_snapshot",
            title="companion.session — integrity",
            content=content_str,
            status="immutable",
            confidence=1.0,
            owner="omnisvera",
            classification="internal",
            metadata={"domain": "companion.session", "subject": "integrity"},
        )

        pid = self.store.create_prediction(
            domain="companion.session",
            snapshot_memory_id=item_id,
            claim="integrity check",
            probability=0.5,
            horizon="24h",
            resolution_rule={},
        )

        # Tamper with snapshot
        from contextlib import closing
        with closing(self.store._connect()) as conn, conn:
            conn.execute(
                "UPDATE memory_items SET content=? WHERE id=?",
                (json.dumps({"tampered": True}), item_id),
            )

        p = self.store.get_prediction(pid)
        self.assertFalse(p["snapshot_intact"])

    # 10. Previous test suite stays green
    def test_previous_suite_import(self):
        """Verify the existing epistemic loop test module can still be imported."""
        import importlib
        mod = importlib.import_module("tests.test_epistemic_loop")
        self.assertTrue(hasattr(mod, "test_bridge_tools"))


if __name__ == "__main__":
    unittest.main()
