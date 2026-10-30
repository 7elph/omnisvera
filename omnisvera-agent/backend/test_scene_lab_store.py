"""Scene lab proposal store: private versioned drafts reusing existing scenes.

TEMP fixtures only. Never production DB/tokens, no combat, no character
changes, no publishing. Content is private review state: draft/approved/
rejected never applies, publishes or executes anything.
"""
from __future__ import annotations

import json
import re
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app import scene_lab_store as lab
from app.character_play import init_character_play
from app.dice_rolls import init_dice_rolls
from app.scene_play import create_scene
from app.session_workspace import init_session_workspace


RUN_ID = "test-" + "a1b2c3d4" * 4  # test-<32hex> estrito


class LabFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "lab.sqlite3"
        # Convenção nativa (test_session_coherence/test_session8_necromancer):
        # workspace + fichas + dados antes do ledger.
        init_session_workspace(self.db)
        init_character_play(self.db)
        init_dice_rolls(self.db)
        scene, created = create_scene(
            self.db,
            request_id="lab-fixture-scene-1",
            campaign_id="omnisvera",
            title="Clareira de ensaio",
            location_name="Ruínas",
            created_by="master",
        )
        self.assertTrue(created)
        self.scene_id = int(scene["id"])
        with closing(sqlite3.connect(self.db)) as db:
            self.scene_before = db.execute(
                "SELECT * FROM scenes WHERE id=?", (self.scene_id,)
            ).fetchone()[:]
            self.actions_before = db.execute(
                "SELECT count(*) FROM scene_actions"
            ).fetchone()[0]
            self.tables_before = {
                row[0]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.tokens_before = db.execute(
                "SELECT count(*) FROM session_workspace_tokens"
            ).fetchone()[0]
            self.characters_before = db.execute(
                "SELECT count(*) FROM character_states"
            ).fetchone()[0]

    def propose(self, **overrides):
        params = {
            "scene_id": self.scene_id,
            "title": "Emboscada na clareira",
            "kind": "action",
            "content": {"beats": ["sussurro", "investida"]},
            "created_by": "master",
            "request_id": "lab-propose-001",
        }
        params.update(overrides)
        return lab.create_proposal(self.db, **params)

    def assert_untouched(self):
        allowed_new = {
            "scene_lab_proposals",
            "scene_lab_revisions",
            "scene_lab_receipts",
            "scene_lab_history",
            "session_ledger",
        }
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(
                self.scene_before,
                db.execute(
                    "SELECT * FROM scenes WHERE id=?", (self.scene_id,)
                ).fetchone()[:],
            )
            self.assertEqual(
                self.actions_before,
                db.execute("SELECT count(*) FROM scene_actions").fetchone()[0],
            )
            tables = {
                row[0]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertLessEqual(tables - self.tables_before, allowed_new)
            # Pins e fichas intactos: nenhuma linha criada, alterada ou removida.
            self.assertEqual(
                self.tokens_before,
                db.execute("SELECT count(*) FROM session_workspace_tokens").fetchone()[0],
            )
            self.assertEqual(
                self.characters_before,
                db.execute("SELECT count(*) FROM character_states").fetchone()[0],
            )


class CreateProposalTests(LabFixture):
    def test_create_starts_version_one_as_draft_with_minimum_fields(self):
        proposal = self.propose()
        self.assertEqual(1, proposal["version"])
        self.assertEqual("draft", proposal["status"])
        self.assertEqual(self.scene_id, proposal["scene_id"])
        self.assertEqual("action", proposal["kind"])
        self.assertEqual({"beats": ["sussurro", "investida"]}, proposal["content"])
        self.assertEqual("master", proposal["created_by"])
        self.assertIsNone(proposal["evidence"])
        for field in ("id", "title", "created_at", "updated_at", "history"):
            self.assertIn(field, proposal)
        self.assertEqual("created", proposal["history"][0]["event"])
        self.assert_untouched()

    def test_create_requires_existing_scene(self):
        with self.assertRaisesRegex(ValueError, "[Cc]ena"):
            self.propose(scene_id=999999, request_id="lab-propose-missing")
        with TemporaryDirectory() as empty:
            fresh = Path(empty) / "fresh.sqlite3"
            init_session_workspace(fresh)
            init_character_play(fresh)
            init_dice_rolls(fresh)
            lab.init_lab(fresh)
            with self.assertRaisesRegex(ValueError, "[Cc]ena"):
                lab.create_proposal(
                    fresh,
                    scene_id=1,
                    title="Sem cena",
                    kind="action",
                    content={},
                    created_by="master",
                    request_id="lab-propose-noscene",
                )

    def test_create_validates_kind_title_content_and_request(self):
        with self.assertRaisesRegex(ValueError, "kind"):
            self.propose(kind="spell", request_id="lab-propose-kind")
        with self.assertRaisesRegex(ValueError, "180"):
            self.propose(title="t" * 181, request_id="lab-propose-title")
        with self.assertRaisesRegex(ValueError, "[Cc]onte"):
            self.propose(content=["nao-dict"], request_id="lab-propose-content")
        with self.assertRaisesRegex(ValueError, "50 ?000"):
            self.propose(
                content={"blob": "x" * 50000}, request_id="lab-propose-huge"
            )
        with self.assertRaisesRegex(ValueError, "request_id"):
            self.propose(request_id="curto")
        self.assert_untouched()

    def test_scene_bundle_kind_is_accepted(self):
        proposal = self.propose(kind="scene_bundle", request_id="lab-propose-bundle")
        self.assertEqual("scene_bundle", proposal["kind"])

    def test_create_rejects_nan_infinity_deep_nesting_and_author_limit(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaisesRegex(ValueError, "[Cc]onte"):
                self.propose(
                    content={"beats": [bad]}, request_id=f"lab-propose-bad-{bad}",
                )
        deep: dict = {}
        cursor = deep
        for _ in range(200):
            cursor["ninho"] = {}
            cursor = cursor["ninho"]
        with self.assertRaisesRegex(ValueError, "[Cc]onte|[Pp]rofund"):
            self.propose(content=deep, request_id="lab-propose-deep")
        with self.assertRaisesRegex(ValueError, "[Aa]utor|180"):
            self.propose(
                created_by="m" * 181, request_id="lab-propose-author"
            )
        ok = self.propose(
            created_by="m" * 180, request_id="lab-propose-author-max"
        )
        self.assertEqual("m" * 180, ok["created_by"])
        self.assert_untouched()


class UpdateProposalTests(LabFixture):
    def test_update_creates_immutable_revision_and_resets_review(self):
        proposal = self.propose()
        lab.attach_evidence(
            self.db,
            proposal["id"],
            expected_version=1,
            run_id=RUN_ID,
            summary={"checks": ["grid"]},
            request_id="lab-evidence-001",
        )
        lab.set_decision(
            self.db,
            proposal["id"],
            expected_version=1,
            decision="approved",
            reason="Revisao manual do Mestre",
            request_id="lab-decision-001",
        )
        updated = lab.update_proposal(
            self.db,
            proposal["id"],
            expected_version=1,
            content={"beats": ["sussurro", "recuo"]},
            title="Emboscada revista",
            request_id="lab-update-001",
        )
        self.assertEqual(2, updated["version"])
        self.assertEqual("draft", updated["status"])
        self.assertIsNone(updated["evidence"])
        self.assertEqual({"beats": ["sussurro", "recuo"]}, updated["content"])
        full = lab.get_proposal(self.db, updated["id"])
        versions = [h["version"] for h in full["history"]]
        self.assertEqual([1, 1, 1, 2], versions)
        events = [h["event"] for h in full["history"]]
        self.assertEqual(["created", "evidence", "decision", "updated"], events)
        old_evidence = next(h for h in full["history"] if h["event"] == "evidence")
        self.assertEqual(RUN_ID, old_evidence["detail"]["run_id"])
        self.assert_untouched()

    def test_stale_expected_version_is_rejected_without_changes(self):
        proposal = self.propose()
        lab.update_proposal(
            self.db,
            proposal["id"],
            expected_version=1,
            content={"beats": ["v2"]},
            title="Segunda",
            request_id="lab-update-stale-1",
        )
        with self.assertRaisesRegex(ValueError, "[Vv]ers"):
            lab.update_proposal(
                self.db,
                proposal["id"],
                expected_version=1,
                content={"beats": ["v3"]},
                title="Terceira",
                request_id="lab-update-stale-2",
            )
        with self.assertRaisesRegex(ValueError, "[Vv]ers"):
            lab.attach_evidence(
                self.db,
                proposal["id"],
                expected_version=1,
                run_id=RUN_ID,
                summary={},
                request_id="lab-evidence-stale",
            )
        with self.assertRaisesRegex(ValueError, "[Vv]ers"):
            lab.set_decision(
                self.db,
                proposal["id"],
                expected_version=1,
                decision="approved",
                reason="Tardia",
                request_id="lab-decision-stale",
            )
        self.assertEqual(2, lab.get_proposal(self.db, proposal["id"])["version"])


class IdempotencyTests(LabFixture):
    def test_retry_after_version_advanced_returns_original_receipt(self):
        proposal = self.propose(request_id="lab-retry-create")
        first = lab.update_proposal(
            self.db,
            proposal["id"],
            expected_version=1,
            content={"beats": ["v2"]},
            title="Segunda",
            request_id="lab-retry-update",
        )
        self.assertEqual(2, first["version"])
        # Retry perdido com a revisao antiga: recibo primeiro, sem erro de versao.
        replay = lab.update_proposal(
            self.db,
            proposal["id"],
            expected_version=1,
            content={"beats": ["v2"]},
            title="Segunda",
            request_id="lab-retry-update",
        )
        self.assertEqual(first, replay)
        self.assertEqual(2, lab.get_proposal(self.db, proposal["id"])["version"])

    def test_same_request_with_different_intent_conflicts(self):
        proposal = self.propose(request_id="lab-conflict-create")
        lab.update_proposal(
            self.db,
            proposal["id"],
            expected_version=1,
            content={"beats": ["v2"]},
            title="Segunda",
            request_id="lab-conflict-update",
        )
        with self.assertRaisesRegex(ValueError, "[Oo]utro conteúdo"):
            lab.update_proposal(
                self.db,
                proposal["id"],
                expected_version=2,
                content={"beats": ["outra intencao"]},
                title="Segunda",
                request_id="lab-conflict-update",
            )

    def test_expected_version_is_part_of_update_evidence_decision_intent(self):
        proposal = self.propose(request_id="lab-fpversion-create")
        lab.update_proposal(
            self.db,
            proposal["id"],
            expected_version=1,
            content={"beats": ["v2"]},
            title="Segunda",
            request_id="lab-fpversion-update",
        )
        # Mesma intencao repetida (versao antiga) devolve o recibo original.
        replay = lab.update_proposal(
            self.db,
            proposal["id"],
            expected_version=1,
            content={"beats": ["v2"]},
            title="Segunda",
            request_id="lab-fpversion-update",
        )
        self.assertEqual(2, replay["version"])
        # Mudar expected_version com o mesmo request_id e outra intencao.
        with self.assertRaisesRegex(ValueError, "[Oo]utro conteúdo"):
            lab.update_proposal(
                self.db,
                proposal["id"],
                expected_version=2,
                content={"beats": ["v2"]},
                title="Segunda",
                request_id="lab-fpversion-update",
            )
        lab.attach_evidence(
            self.db,
            proposal["id"],
            expected_version=2,
            run_id=RUN_ID,
            summary={"n": 1},
            request_id="lab-fpversion-evidence",
        )
        with self.assertRaisesRegex(ValueError, "[Oo]utro conteúdo"):
            lab.attach_evidence(
                self.db,
                proposal["id"],
                expected_version=1,
                run_id=RUN_ID,
                summary={"n": 1},
                request_id="lab-fpversion-evidence",
            )
        lab.set_decision(
            self.db,
            proposal["id"],
            expected_version=2,
            decision="approved",
            reason="Ok manual",
            request_id="lab-fpversion-decision",
        )
        with self.assertRaisesRegex(ValueError, "[Oo]utro conteúdo"):
            lab.set_decision(
                self.db,
                proposal["id"],
                expected_version=1,
                decision="approved",
                reason="Ok manual",
                request_id="lab-fpversion-decision",
            )
        self.assertEqual(2, lab.get_proposal(self.db, proposal["id"])["version"])

    def test_concurrent_same_request_executes_once(self):
        def create(suffix):
            return lab.create_proposal(
                self.db,
                scene_id=self.scene_id,
                title="Corrida",
                kind="action",
                content={"n": 1},
                created_by="master",
                request_id="lab-race-create",
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = list(pool.map(create, (1, 2)))
        self.assertEqual(first, second)
        self.assertEqual(1, len(lab.list_proposals(self.db, scene_id=self.scene_id)))


class EvidenceDecisionTests(LabFixture):
    def test_evidence_requires_strict_run_id_and_snapshots_content(self):
        proposal = self.propose()
        with self.assertRaisesRegex(ValueError, "run_id"):
            lab.attach_evidence(
                self.db,
                proposal["id"],
                expected_version=1,
                run_id="PASS-enviado-pelo-cliente",
                summary={},
                request_id="lab-evidence-bad",
            )
        evidenced = lab.attach_evidence(
            self.db,
            proposal["id"],
            expected_version=1,
            run_id=RUN_ID,
            summary={"checks": ["grid"], "verdict": "PASS"},
            request_id="lab-evidence-002",
        )
        self.assertEqual(1, evidenced["version"])
        self.assertEqual(RUN_ID, evidenced["evidence"]["run_id"])
        self.assertEqual(
            {"beats": ["sussurro", "investida"]},
            evidenced["evidence"]["content_snapshot"],
        )
        # PASS do resumo nao aprova sozinho: aprovacao exige decisao explicita.
        self.assertEqual("draft", evidenced["status"])

    def test_second_evidence_replaces_current_but_history_keeps_old(self):
        proposal = self.propose()
        lab.attach_evidence(
            self.db,
            proposal["id"],
            expected_version=1,
            run_id=RUN_ID,
            summary={"n": 1},
            request_id="lab-evidence-old",
        )
        other = "test-" + "9" * 32
        current = lab.attach_evidence(
            self.db,
            proposal["id"],
            expected_version=1,
            run_id=other,
            summary={"n": 2},
            request_id="lab-evidence-new",
        )
        self.assertEqual(other, current["evidence"]["run_id"])
        full = lab.get_proposal(self.db, proposal["id"])
        runs = [
            h["detail"]["run_id"] for h in full["history"] if h["event"] == "evidence"
        ]
        self.assertEqual([RUN_ID, other], runs)

    def test_decision_is_explicit_manual_and_validated(self):
        proposal = self.propose()
        with self.assertRaisesRegex(ValueError, "[Dd]ecis"):
            lab.set_decision(
                self.db,
                proposal["id"],
                expected_version=1,
                decision="published",
                reason="x",
                request_id="lab-decision-bad",
            )
        with self.assertRaisesRegex(ValueError, "[Mm]otivo|[Rr]eason|[Rr]az"):
            lab.set_decision(
                self.db,
                proposal["id"],
                expected_version=1,
                decision="approved",
                reason="  ",
                request_id="lab-decision-noreason",
            )
        decided = lab.set_decision(
            self.db,
            proposal["id"],
            expected_version=1,
            decision="rejected",
            reason="Sem orcamento de cena",
            request_id="lab-decision-003",
        )
        self.assertEqual("rejected", decided["status"])
        self.assertEqual(1, decided["version"])
        self.assertEqual(
            {"beats": ["sussurro", "investida"]}, decided["content"]
        )

    def test_evidence_rejects_nan_huge_summary_and_long_reason(self):
        proposal = self.propose(request_id="lab-harden-create")
        with self.assertRaisesRegex(ValueError, "[Rr]esumo"):
            lab.attach_evidence(
                self.db,
                proposal["id"],
                expected_version=1,
                run_id=RUN_ID,
                summary={"v": float("nan")},
                request_id="lab-evidence-nan",
            )
        with self.assertRaisesRegex(ValueError, "50000"):
            lab.attach_evidence(
                self.db,
                proposal["id"],
                expected_version=1,
                run_id=RUN_ID,
                summary={"blob": "y" * 50000},
                request_id="lab-evidence-huge",
            )
        with self.assertRaisesRegex(ValueError, "[Mm]otivo|2000"):
            lab.set_decision(
                self.db,
                proposal["id"],
                expected_version=1,
                decision="approved",
                reason="r" * 2001,
                request_id="lab-decision-long",
            )
        decided = lab.set_decision(
            self.db,
            proposal["id"],
            expected_version=1,
            decision="approved",
            reason="r" * 2000,
            request_id="lab-decision-max",
        )
        self.assertEqual("approved", decided["status"])
        self.assert_untouched()

    def test_ledger_entries_are_gm_only_narrative(self):
        proposal = self.propose(request_id="lab-ledger-create")
        lab.attach_evidence(
            self.db,
            proposal["id"],
            expected_version=1,
            run_id=RUN_ID,
            summary={},
            request_id="lab-ledger-evidence",
        )
        lab.set_decision(
            self.db,
            proposal["id"],
            expected_version=1,
            decision="approved",
            reason="Ok manual",
            request_id="lab-ledger-decision",
        )
        with closing(sqlite3.connect(self.db)) as db:
            rows = db.execute(
                "SELECT source_type,visibility,title,detail_json FROM session_ledger "
                "WHERE source_type='scene_lab_proposal' ORDER BY id"
            ).fetchall()
        self.assertEqual(3, len(rows))
        for source_type, visibility, title, detail_json in rows:
            self.assertEqual("gm", visibility)
            self.assertNotIn("sussurro", title + (detail_json or ""))
        self.assert_untouched()


class EvidenceReceiptPeekTests(LabFixture):
    def test_peek_returns_immutable_saved_dto_without_writing_or_current_version_check(self):
        proposal = self.propose()
        attached = lab.attach_evidence(self.db, proposal["id"], expected_version=1,
                                      run_id=RUN_ID, summary={"verdict": "PASS"},
                                      request_id="peek-evidence-stable")
        lab.update_proposal(self.db, proposal["id"], expected_version=1, title="New revision",
                            content={"changed": True}, request_id="peek-update-later")
        before = self.db.read_bytes()
        replay = lab.peek_evidence_receipt(self.db, proposal["id"], expected_version=1,
                                          run_id=RUN_ID, request_id="peek-evidence-stable")
        self.assertEqual(replay, attached)
        self.assertEqual(self.db.read_bytes(), before)
        for other in ({"proposal_id": proposal["id"] + 1}, {"expected_version": 2},
                      {"run_id": "test-" + "b" * 32}):
            params = {"proposal_id": proposal["id"], "expected_version": 1,
                      "run_id": RUN_ID, "request_id": "peek-evidence-stable", **other}
            with self.assertRaisesRegex(ValueError, "já utilizado"):
                lab.peek_evidence_receipt(self.db, **params)
        self.assertEqual(self.db.read_bytes(), before)

    def test_peek_missing_table_database_or_receipt_performs_no_ddl(self):
        with TemporaryDirectory() as temporary:
            database = Path(temporary) / "empty.sqlite3"
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute("CREATE TABLE marker(value TEXT)")
            before = database.read_bytes()
            self.assertIsNone(lab.peek_evidence_receipt(database, 1, expected_version=1,
                                                       run_id=RUN_ID, request_id="peek-missing-safe"))
            self.assertEqual(database.read_bytes(), before)
            missing = Path(temporary) / "not-created.sqlite3"
            self.assertIsNone(lab.peek_evidence_receipt(missing, 1, expected_version=1,
                                                       run_id=RUN_ID, request_id="peek-missing-safe"))
            self.assertFalse(missing.exists())

    def test_peek_rejects_other_receipt_intent_oversize_and_invalid_json_without_echo(self):
        proposal = self.propose(request_id="peek-other-intent")
        with self.assertRaisesRegex(ValueError, "já utilizado"):
            lab.peek_evidence_receipt(self.db, proposal["id"], expected_version=1,
                                      run_id=RUN_ID, request_id="peek-other-intent")
        lab.attach_evidence(self.db, proposal["id"], expected_version=1, run_id=RUN_ID,
                            summary={}, request_id="peek-invalid-receipt")
        for raw in ("PRIVATE_INVALID_JSON", "x" * 1000001, '{"private": NaN}'):
            with closing(sqlite3.connect(self.db)) as connection, connection:
                connection.execute("UPDATE scene_lab_receipts SET response_json=? WHERE request_id=?",
                                   (raw, "peek-invalid-receipt"))
            with self.assertRaises(ValueError) as caught:
                lab.peek_evidence_receipt(self.db, proposal["id"], expected_version=1,
                                          run_id=RUN_ID, request_id="peek-invalid-receipt")
            self.assertNotIn("PRIVATE", str(caught.exception))


class ReadTests(LabFixture):
    def test_list_returns_summaries_and_get_includes_history(self):
        first = self.propose(request_id="lab-read-1")
        self.propose(
            title="Pacote da cena",
            kind="scene_bundle",
            request_id="lab-read-2",
        )
        summaries = lab.list_proposals(self.db)
        self.assertEqual(2, len(summaries))
        for summary in summaries:
            self.assertEqual(
                {"id", "scene_id", "title", "kind", "version", "status", "updated_at"},
                set(summary),
            )
        filtered = lab.list_proposals(self.db, scene_id=999999)
        self.assertEqual([], filtered)
        full = lab.get_proposal(self.db, first["id"])
        self.assertEqual(first["content"], full["content"])
        self.assertTrue(full["history"])
        with self.assertRaisesRegex(ValueError, "[Pp]roposta"):
            lab.get_proposal(self.db, 999999)

    def test_get_includes_revisions_with_previous_contents(self):
        proposal = self.propose(request_id="lab-rev-create")
        lab.update_proposal(
            self.db,
            proposal["id"],
            expected_version=1,
            content={"beats": ["recuo"]},
            title="Emboscada revista",
            request_id="lab-rev-update",
        )
        lab.attach_evidence(
            self.db,
            proposal["id"],
            expected_version=2,
            run_id=RUN_ID,
            summary={},
            request_id="lab-rev-evidence",
        )
        lab.set_decision(
            self.db,
            proposal["id"],
            expected_version=2,
            decision="approved",
            reason="Ok",
            request_id="lab-rev-decision",
        )
        full = lab.get_proposal(self.db, proposal["id"])
        self.assertEqual(
            [
                {
                    "version": 1,
                    "title": "Emboscada na clareira",
                    "content": {"beats": ["sussurro", "investida"]},
                },
                {
                    "version": 2,
                    "title": "Emboscada revista",
                    "content": {"beats": ["recuo"]},
                },
            ],
            [
                {k: r[k] for k in ("version", "title", "content")}
                for r in full["revisions"]
            ],
        )
        for revision in full["revisions"]:
            self.assertIn("created_at", revision)
        # Revisões só no detalhe: resumos de lista não carregam conteúdo.
        for summary in lab.list_proposals(self.db):
            self.assertNotIn("revisions", summary)
            self.assertNotIn("content", summary)
        self.assert_untouched()


if __name__ == "__main__":
    unittest.main()
