"""TEMP-only tests for GM-confirmed workshop review/import.

No provider, browser, operational database, real scene or heavy suite is used.
Every test creates isolated workshop and campaign SQLite files under a
temporary directory.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from app import ai_workshop as workshop
from app import scene_play
from app import workshop_review as review


def _now() -> datetime:
    return datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)


class ReviewFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workshop_db = self.root / "workshop.sqlite3"
        self.campaign_db = self.root / "campaign.sqlite3"
        workshop.init_workshop(self.workshop_db)
        scene_play.init_scene_play(self.campaign_db)
        self.now = _now()
        self.counter = 0

    def make_job(self, *, draft: str = "O anão oferece reparos.", queue: str = "text",
                 revision: str = "r1") -> dict:
        self.counter += 1
        request_id = f"job-request-{self.counter:03d}"
        enqueued = workshop.enqueue_job(
            self.workshop_db, queue=queue, entity_type="session",
            entity_id=f"session-{self.counter}", revision=revision,
            purpose=f"review-{self.counter}", request_id=request_id,
            payload={"sources": [
                {"path": "fixture.txt", "sha256": "a" * 64, "text": "fonte"},
            ]},
            now=self.now,
        )
        claimed = workshop.claim_next_job(
            self.workshop_db, queue=queue, worker_id="fixture-worker",
            table_state="inactive", lease_seconds=300, now=self.now,
        )["job"]
        self.assertIsNotNone(claimed)
        output = {
            "sources": [{"path": "fixture.txt", "sha256": "a" * 64}],
            "revision": revision,
            "facts": ["Fato privado"],
            "suggestions": ["Sugestão privada"],
            "questions": [],
            "draft": draft,
        }
        return workshop.finish_job(
            self.workshop_db, enqueued["job"]["id"],
            worker_id="fixture-worker", lease_token=claimed["lease_token"],
            status="awaiting_approval", output=output,
            metrics={"provider": "fixture", "model": "fixture", "duration_ms": 5},
            now=self.now,
        )

    def make_scene(self, title: str, *, archived: bool = False) -> dict:
        self.counter += 1
        scene, _created = scene_play.create_scene(
            self.campaign_db, request_id=f"scene-request-{self.counter:03d}",
            campaign_id="omnisvera", title=title, location_name="Fixture",
            created_by="master",
        )
        if archived:
            scene_play.archive_scene(self.campaign_db, int(scene["id"]), True)
        return scene

    def review(self, job: dict, *, decision: str = "import", scene_id: int | None,
               request_id: str, expected_hash: str | None = None,
               expected_revision: str | None = None) -> dict:
        return review.review_job(
            self.workshop_db, self.campaign_db, int(job["id"]),
            decision=decision, scene_id=scene_id,
            expected_revision=expected_revision or job["revision"],
            expected_output_hash=expected_hash or review.output_hash(job),
            request_id=request_id,
        )

    def elements(self, scene_id: int | None = None) -> list[dict]:
        with closing(sqlite3.connect(self.campaign_db)) as connection:
            connection.row_factory = sqlite3.Row
            if scene_id is None:
                rows = connection.execute("SELECT * FROM scene_elements ORDER BY id").fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM scene_elements WHERE scene_id=? ORDER BY id", (scene_id,)
                ).fetchall()
        return [dict(row) for row in rows]


class PrivateImportTests(ReviewFixture):
    def test_import_creates_one_hidden_gm_element_and_completes_job(self):
        scene = self.make_scene("Cena privada")
        job = self.make_job(draft="Rascunho com pista privada.")
        result = self.review(job, scene_id=int(scene["id"]), request_id="review-import-001")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["decision"], "import")
        self.assertEqual(result["scene_id"], int(scene["id"]))
        self.assertEqual(result["output_hash"], review.output_hash(job))

        elements = self.elements()
        self.assertEqual(len(elements), 1)
        element = elements[0]
        self.assertEqual(int(element["scene_id"]), int(scene["id"]))
        self.assertEqual(element["visibility"], "gm")
        self.assertEqual(element["status"], "hidden")
        self.assertTrue(element["public_description"] in (None, ""))
        self.assertIn("Rascunho com pista privada.", element["private_description"])
        self.assertIn(f"job={job['id']}", element["private_description"])
        self.assertIn(result["output_hash"], element["private_description"])
        self.assertIn("não executada", element["private_description"])
        self.assertEqual(result["element_id"], int(element["id"]))

        stored = workshop.get_job(self.workshop_db, int(job["id"]))
        self.assertEqual(stored["status"], "completed")
        self.assertEqual(stored["output_json"]["draft"], "Rascunho com pista privada.")
        self.assertEqual(review.review_for_job(self.workshop_db, int(job["id"]))["element_id"],
                         int(element["id"]))

    def test_retry_and_repeated_result_do_not_duplicate_element(self):
        scene = self.make_scene("Cena idempotente")
        job = self.make_job()
        first = self.review(job, scene_id=int(scene["id"]), request_id="review-retry-001")
        retry = self.review(job, scene_id=int(scene["id"]), request_id="review-retry-001")
        repeated = self.review(job, scene_id=int(scene["id"]), request_id="review-other-001")

        self.assertEqual(first, retry)
        self.assertEqual(first["element_id"], repeated["element_id"])
        self.assertEqual(len(self.elements()), 1)

    def test_same_request_id_with_changed_intent_is_conflict(self):
        scene_a = self.make_scene("Cena A")
        scene_b = self.make_scene("Cena B")
        job = self.make_job()
        self.review(job, scene_id=int(scene_a["id"]), request_id="review-conflict-001")
        with self.assertRaises(review.ReviewError) as caught:
            self.review(job, scene_id=int(scene_b["id"]), request_id="review-conflict-001")
        self.assertEqual(caught.exception.code, "request_id_conflict")

    def test_code_queue_is_stored_as_text_not_executed(self):
        scene = self.make_scene("Cena de código")
        code = "def nao_executar():\n    raise SystemExit('nunca')"
        job = self.make_job(queue="code", draft=code)
        result = self.review(job, scene_id=int(scene["id"]), request_id="review-code-001")
        self.assertEqual(result["status"], "completed")
        element = self.elements()[0]
        self.assertIn(code, element["private_description"])
        self.assertEqual(element["visibility"], "gm")
        self.assertEqual(workshop.get_job(self.workshop_db, int(job["id"]))["status"], "completed")


class DestinationAndHashTests(ReviewFixture):
    def test_import_to_another_scene_is_rejected(self):
        scene_a = self.make_scene("Cena A")
        scene_b = self.make_scene("Cena B")
        job = self.make_job()
        hash_value = review.output_hash(job)
        self.review(job, scene_id=int(scene_a["id"]), request_id="review-dest-001")
        with self.assertRaises(review.ReviewError) as caught:
            self.review(job, scene_id=int(scene_b["id"]), request_id="review-dest-002")
        self.assertEqual(caught.exception.code, "imported_elsewhere")
        self.assertEqual(len(self.elements(int(scene_b["id"]))), 0)
        self.assertEqual(len(self.elements()), 1)
        stored = workshop.get_job(self.workshop_db, int(job["id"]))
        self.assertEqual(stored["status"], "completed")
        self.assertEqual(stored["output_json"]["draft"], job["output_json"]["draft"])
        self.assertEqual(hash_value, review.output_hash(stored))

    def test_changed_output_hash_is_rejected_without_campaign_write(self):
        scene = self.make_scene("Cena protegida")
        job = self.make_job(draft="Original.")
        original_hash = review.output_hash(job)
        changed = dict(job["output_json"])
        changed["draft"] = "Alterado depois da revisão."
        with closing(sqlite3.connect(self.workshop_db)) as connection, connection:
            connection.execute(
                "UPDATE ai_workshop_jobs SET output_json=? WHERE id=?",
                (json.dumps(changed, ensure_ascii=False, sort_keys=True), int(job["id"])),
            )
        with self.assertRaises(review.ReviewError) as caught:
            self.review(job, scene_id=int(scene["id"]), request_id="review-hash-001",
                        expected_hash=original_hash)
        self.assertEqual(caught.exception.code, "output_hash_mismatch")
        self.assertEqual(self.elements(), [])
        self.assertEqual(workshop.get_job(self.workshop_db, int(job["id"]))["status"],
                         "awaiting_approval")

    def test_revision_mismatch_and_invalid_hash_are_rejected(self):
        scene = self.make_scene("Cena revisão")
        job = self.make_job()
        with self.assertRaises(review.ReviewError) as caught:
            self.review(job, scene_id=int(scene["id"]), request_id="review-rev-001",
                        expected_revision="outra")
        self.assertEqual(caught.exception.code, "revision_mismatch")
        with self.assertRaises(review.ReviewError) as caught:
            self.review(job, scene_id=int(scene["id"]), request_id="review-rev-002",
                        expected_hash="not-a-hash")
        self.assertEqual(caught.exception.code, "invalid_output_hash")
        self.assertEqual(self.elements(), [])

    def test_archived_or_missing_scene_is_rejected(self):
        archived = self.make_scene("Arquivada", archived=True)
        job = self.make_job()
        with self.assertRaises(review.ReviewError) as caught:
            self.review(job, scene_id=int(archived["id"]), request_id="review-arch-001")
        self.assertEqual(caught.exception.code, "scene_archived")
        with self.assertRaises(review.ReviewError) as caught:
            self.review(job, scene_id=99999, request_id="review-arch-002")
        self.assertEqual(caught.exception.code, "scene_not_found")
        self.assertEqual(self.elements(), [])

    def test_campaign_without_scene_schema_is_unavailable(self):
        job = self.make_job()
        broken = self.root / "broken-campaign.sqlite3"
        with closing(sqlite3.connect(broken)) as connection, connection:
            connection.execute("CREATE TABLE unrelated(id INTEGER)")
        original = self.campaign_db
        self.campaign_db = broken
        try:
            with self.assertRaises(review.ReviewError) as caught:
                self.review(job, scene_id=1, request_id="review-broken-001")
        finally:
            self.campaign_db = original
        self.assertEqual(caught.exception.code, "campaign_unavailable")
        self.assertEqual(workshop.get_job(self.workshop_db, int(job["id"]))["status"],
                         "awaiting_approval")


class RejectionTests(ReviewFixture):
    def test_reject_cancels_job_without_touching_campaign(self):
        self.make_scene("Cena intocada")
        job = self.make_job(draft="Rascunho que será rejeitado.")
        before = hashlib.sha256(self.campaign_db.read_bytes()).hexdigest()
        result = self.review(job, decision="reject", scene_id=None,
                             request_id="review-reject-001")
        after = hashlib.sha256(self.campaign_db.read_bytes()).hexdigest()

        self.assertEqual(before, after)
        self.assertEqual(result["status"], "cancelled")
        self.assertIsNone(result["scene_id"])
        self.assertIsNone(result["element_id"])
        stored = workshop.get_job(self.workshop_db, int(job["id"]))
        self.assertEqual(stored["status"], "cancelled")
        self.assertEqual(stored["output_json"]["draft"], "Rascunho que será rejeitado.")
        self.assertEqual(review.review_for_job(self.workshop_db, int(job["id"]))["decision"],
                         "reject")

    def test_import_after_reject_is_conflict(self):
        scene = self.make_scene("Cena pós-rejeição")
        job = self.make_job()
        self.review(job, decision="reject", scene_id=None, request_id="review-reject-002")
        with self.assertRaises(review.ReviewError) as caught:
            self.review(job, scene_id=int(scene["id"]), request_id="review-after-reject-001")
        self.assertEqual(caught.exception.code, "already_reviewed")
        self.assertEqual(self.elements(), [])


class RecoveryAndLimitTests(ReviewFixture):
    def test_recovers_native_element_created_before_receipt(self):
        scene = self.make_scene("Cena recuperável")
        job = self.make_job()
        hash_value = review.output_hash(job)
        native_request = review.element_request_id(int(job["id"]), hash_value)
        existing, created = scene_play.create_element(
            self.campaign_db, int(scene["id"]), request_id=native_request,
            element_type="clue", title="Parcial", status="hidden", visibility="gm",
            created_by="master", public_description="", private_description="parcial",
        )
        self.assertTrue(created)

        result = self.review(job, scene_id=int(scene["id"]), request_id="review-recover-001")
        self.assertEqual(result["element_id"], int(existing["id"]))
        self.assertEqual(len(self.elements()), 1)
        self.assertEqual(workshop.get_job(self.workshop_db, int(job["id"]))["status"], "completed")
        self.assertEqual(review.review_for_job(self.workshop_db, int(job["id"]))["element_id"],
                         int(existing["id"]))

    def test_partial_element_in_another_scene_blocks_import(self):
        scene_a = self.make_scene("Cena A")
        scene_b = self.make_scene("Cena B")
        job = self.make_job()
        hash_value = review.output_hash(job)
        native_request = review.element_request_id(int(job["id"]), hash_value)
        scene_play.create_element(
            self.campaign_db, int(scene_b["id"]), request_id=native_request,
            element_type="clue", title="Parcial", status="hidden", visibility="gm",
            created_by="master", public_description="", private_description="parcial",
        )
        with self.assertRaises(review.ReviewError) as caught:
            self.review(job, scene_id=int(scene_a["id"]), request_id="review-recover-002")
        self.assertEqual(caught.exception.code, "imported_elsewhere")
        self.assertEqual(workshop.get_job(self.workshop_db, int(job["id"]))["status"],
                         "awaiting_approval")
        self.assertEqual(len(self.elements()), 1)

    def test_empty_or_oversized_text_is_rejected_without_truncation(self):
        scene = self.make_scene("Cena limite")
        empty = self.make_job(draft="   ")
        with self.assertRaises(review.ReviewError) as caught:
            self.review(empty, scene_id=int(scene["id"]), request_id="review-empty-001")
        self.assertEqual(caught.exception.code, "empty_output")

        oversized = self.make_job(draft="temporary")
        oversized['output_json']['draft'] = 'x' * 50001
        with closing(sqlite3.connect(self.workshop_db)) as connection, connection:
            connection.execute('UPDATE ai_workshop_jobs SET output_json=? WHERE id=?',
                (json.dumps(oversized['output_json']), oversized['id']))
        with self.assertRaises(review.ReviewError) as caught:
            self.review(oversized, scene_id=int(scene["id"]), request_id="review-large-001")
        self.assertEqual(caught.exception.code, "output_exceeds_native_limit")
        self.assertEqual(self.elements(), [])
        self.assertEqual(workshop.get_job(self.workshop_db, int(oversized["id"]))["status"],
                         "awaiting_approval")

    def test_long_import_preserves_text_and_retries_without_duplicate(self):
        scene = self.make_scene("Longa")
        draft = "texto preservado " * 350
        job = self.make_job(draft=draft)
        result = self.review(job, scene_id=scene['id'], request_id='review-long-001')
        self.assertGreater(len(result['element_ids']), 1)
        elements = self.elements(scene['id'])
        self.assertTrue(''.join(e['private_description'][1:-1] for e in sorted(elements, key=lambda e:e['id'])).startswith(draft))
        self.assertTrue(all(len(e['private_description']) <= scene_play.MAX_TEXT for e in elements))
        again = self.review(job, scene_id=scene['id'], request_id='review-long-002')
        self.assertEqual(result, again)
        self.assertEqual(len(self.elements(scene['id'])), len(elements))

    def test_long_import_recovers_after_second_part_failure(self):
        from unittest.mock import patch
        scene = self.make_scene("Recuperar")
        job = self.make_job(draft='preservar ' * 600)
        original = scene_play.create_element
        calls = 0
        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2: raise RuntimeError('fixture interruption')
            return original(*args, **kwargs)
        with patch.object(scene_play, 'create_element', side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                self.review(job, scene_id=scene['id'], request_id='review-partial-001')
        self.assertEqual(len(self.elements()), 1)
        result = self.review(job, scene_id=scene['id'], request_id='review-partial-001')
        self.assertEqual(len(self.elements()), len(result['element_ids']))

    def test_image_queue_is_not_reviewable(self):
        scene = self.make_scene("Cena imagem")
        job = self.make_job(queue="image")
        with self.assertRaises(review.ReviewError) as caught:
            self.review(job, scene_id=int(scene["id"]), request_id="review-image-001")
        self.assertEqual(caught.exception.code, "review_queue_not_supported")
        self.assertEqual(self.elements(), [])


if __name__ == "__main__":
    unittest.main()
