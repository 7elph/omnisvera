from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from omnisvera_model.dataset import load_approved
from omnisvera_model.io import read_jsonl, write_jsonl
from app import training_curation as curation


class CompanionModelCurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        (self.vault / "Public.md").write_text("Varkh é um alquimista.", encoding="utf-8")
        (self.vault / "Secret.md").write_text("Segredo de teste.", encoding="utf-8")
        self.originals = {
            name: getattr(curation, name)
            for name in ("INTERACTIONS_PATH", "CANDIDATES_PATH", "APPROVED_PATH", "REJECTED_PATH", "AUDIT_PATH")
        }
        data = self.root / "data"
        curation.INTERACTIONS_PATH = data / "captured" / "interactions.jsonl"
        curation.CANDIDATES_PATH = data / "candidates" / "examples.jsonl"
        curation.APPROVED_PATH = data / "approved" / "examples.jsonl"
        curation.REJECTED_PATH = data / "rejected" / "examples.jsonl"
        curation.AUDIT_PATH = data / "raw" / "audit.jsonl"
        self.original_coverage = curation.coverage_report
        curation.coverage_report = lambda: {
            "approved": len(read_jsonl(curation.APPROVED_PATH)),
            "categories": {}, "profiles": {}, "personas": {},
        }

    def tearDown(self) -> None:
        for name, value in self.originals.items():
            setattr(curation, name, value)
        curation.coverage_report = self.original_coverage
        self.temp.cleanup()

    def payload(self, action: str = "good", **updates):
        value = {
            "interaction_id": "interaction-1",
            "user_profile": "gm",
            "question": "Quem é Varkh?",
            "raw_model_response": "Varkh é um alquimista.",
            "final_response": "Varkh é um alquimista.",
            "verified_facts": [{"fato": "Varkh é um alquimista.", "fonte": "Public.md"}],
            "theories": [],
            "insufficient_information": [],
            "retrieved_sources": [{"path": "Public.md", "title": "Varkh", "visibility": "Público"}],
            "retrieval_mode": "rag:hybrid:grounded",
            "model": "qwen2:1.5b",
            "ollama_used": True,
            "response_time_ms": 1200,
            "validator_rejections": [],
            "feedback_action": action,
        }
        value.update(updates)
        return value

    def capture(self, action: str = "good", **updates):
        return curation.capture_interaction(self.payload(action, **updates), self.vault, actor="Sage")

    def test_01_manual_capture_creates_pending_candidate(self):
        result = self.capture()
        self.assertEqual("pending", result["example"]["review_status"])

    def test_02_capture_persists_interaction(self):
        self.capture()
        self.assertEqual(1, len(read_jsonl(curation.INTERACTIONS_PATH)))

    def test_03_capture_is_idempotent_by_interaction_id(self):
        first = self.capture()["example"]["id"]
        second = self.capture()["example"]["id"]
        self.assertEqual(first, second)
        self.assertEqual(1, len(read_jsonl(curation.CANDIDATES_PATH)))

    def test_04_good_uses_current_answer_only_as_pending_draft(self):
        example = self.capture()["example"]
        self.assertEqual("Varkh é um alquimista.", example["ideal_response"])
        self.assertNotEqual("approved", example["review_status"])

    def test_05_hallucination_never_uses_bad_answer_as_target(self):
        example = self.capture("hallucination")["example"]
        self.assertEqual("", example["ideal_response"])
        self.assertTrue(example["curation"]["flags"]["hallucination_detected"])

    def test_06_leak_redacts_interaction_and_blocks_candidate(self):
        result = self.capture("leak", final_response="segredo", raw_model_response="segredo")
        self.assertNotIn("segredo", result["interaction"]["final_response"])
        self.assertTrue(result["example"]["contains_secret"])

    def test_07_reject_action_writes_rejected_stage(self):
        example = self.capture("reject")["example"]
        self.assertEqual("rejected", example["review_status"])
        self.assertEqual(1, len(read_jsonl(curation.REJECTED_PATH)))

    def test_08_edit_preserves_pending_status(self):
        example = self.capture()["example"]
        updated = curation.update_example(example["id"], {"ideal_response": "Resposta corrigida.", "quality": 4}, "Sage")
        self.assertEqual("pending", updated["example"]["review_status"])

    def test_09_valid_approval_enters_approved_stage(self):
        example = self.capture()["example"]
        approved = curation.approve_example(example["id"], "Sage", quality=5)
        self.assertEqual("approved", approved["example"]["review_status"])
        self.assertEqual(1, len(read_jsonl(curation.APPROVED_PATH)))

    def test_10_duplicate_approval_is_idempotent(self):
        example = self.capture()["example"]
        curation.approve_example(example["id"], "Sage", quality=5)
        curation.approve_example(example["id"], "Sage", quality=5)
        self.assertEqual(1, len(read_jsonl(curation.APPROVED_PATH)))

    def test_11_approved_example_cannot_be_rejected_silently(self):
        example = self.capture()["example"]
        curation.approve_example(example["id"], "Sage", quality=5)
        with self.assertRaises(ValueError):
            curation.reject_example(example["id"], "Sage")

    def test_12_explicit_rejection_excludes_approved_stage(self):
        example = self.capture()["example"]
        curation.reject_example(example["id"], "Sage", "Resposta ruim")
        self.assertFalse(read_jsonl(curation.APPROVED_PATH))

    def test_13_rejected_example_requires_edit_before_approval(self):
        example = self.capture("reject")["example"]
        with self.assertRaises(ValueError):
            curation.approve_example(example["id"], "Sage", quality=5)
        updated = curation.update_example(example["id"], {"ideal_response": "Corrigida.", "quality": 5}, "Sage")
        self.assertEqual("pending", updated["example"]["review_status"])

    def test_14_mark_invention_blocks_approval(self):
        example = self.capture()["example"]
        curation.mark_flag(example["id"], "hallucination", "Sage", "Nome inventado")
        with self.assertRaises(ValueError):
            curation.approve_example(example["id"], "Sage", quality=5)

    def test_15_mark_wrong_source_blocks_approval(self):
        example = self.capture()["example"]
        curation.mark_flag(example["id"], "incorrect-source", "Sage")
        with self.assertRaises(ValueError):
            curation.approve_example(example["id"], "Sage", quality=5)

    def test_16_incomplete_is_recorded_but_correctable(self):
        example = self.capture("incomplete")["example"]
        self.assertTrue(example["curation"]["flags"]["incomplete_detected"])

    def test_17_artificial_preserves_facts_for_rewrite(self):
        example = self.capture("artificial")["example"]
        self.assertTrue(example["ideal_response"])
        self.assertTrue(example["curation"]["flags"]["artificial_detected"])

    def test_18_player_source_marked_gm_is_denied(self):
        with self.assertRaises(ValueError):
            self.capture(user_profile="player", retrieved_sources=[{"path": "Secret.md", "visibility": "gm"}])

    def test_19_player_secret_path_is_denied(self):
        with self.assertRaises(ValueError):
            self.capture(user_profile="player", retrieved_sources=[{"path": "CAMPANHA/ESTADO_DA_CAMPANHA.md", "visibility": "Público"}])

    def test_20_secret_candidate_cannot_be_approved(self):
        example = self.capture()["example"]
        curation.update_example(example["id"], {"contains_secret": True, "quality": 5}, "Sage")
        with self.assertRaises(ValueError):
            curation.approve_example(example["id"], "Sage")

    def test_21_pending_candidate_can_be_deleted(self):
        example = self.capture()["example"]
        curation.delete_pending(example["id"], "Sage")
        self.assertFalse(read_jsonl(curation.CANDIDATES_PATH))

    def test_22_approved_example_cannot_be_deleted(self):
        example = self.capture()["example"]
        curation.approve_example(example["id"], "Sage", quality=5)
        with self.assertRaises(ValueError):
            curation.delete_pending(example["id"], "Sage")

    def test_23_retention_removes_only_expired_unreviewed(self):
        old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat().replace("+00:00", "Z")
        write_jsonl(curation.INTERACTIONS_PATH, [
            {"interaction_id": "old", "created_at": old, "feedback_status": "unreviewed"},
            {"interaction_id": "kept", "created_at": old, "feedback_status": "pending"},
        ])
        self.assertEqual(1, curation.purge_unreviewed(30))

    def test_24_pending_does_not_count_as_approved(self):
        self.capture()
        self.assertEqual(0, curation.stats()["approved"])

    def test_25_counter_changes_only_after_approval(self):
        example = self.capture()["example"]
        curation.approve_example(example["id"], "Sage", quality=5)
        self.assertEqual(1, curation.stats()["approved"])

    def test_26_builder_finds_approved_example(self):
        example = self.capture()["example"]
        curation.approve_example(example["id"], "Sage", quality=5)
        self.assertEqual(1, len(load_approved(curation.APPROVED_PATH.parent)))

    def test_27_every_mutation_has_audit_event(self):
        example = self.capture()["example"]
        curation.update_example(example["id"], {"quality": 4}, "Sage")
        curation.approve_example(example["id"], "Sage")
        self.assertGreaterEqual(len(read_jsonl(curation.AUDIT_PATH)), 3)

    def test_28_rewrites_create_rotating_backup(self):
        example = self.capture()["example"]
        curation.update_example(example["id"], {"quality": 4}, "Sage")
        self.assertTrue(curation.CANDIDATES_PATH.with_suffix(".jsonl.bak1").exists())

    def test_29_source_hash_is_recorded_without_context_text(self):
        example = self.capture()["example"]
        self.assertEqual(1, len(example["source_note_hashes"]))
        self.assertNotIn("Varkh é", json.dumps(example["retrieved_context"], ensure_ascii=False))

    def test_30_filters_find_only_requested_status_and_profile(self):
        self.capture()
        rows = curation.list_examples(status="pending", access_profile="gm")
        self.assertEqual(1, len(rows))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CompanionModelCurationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"companion model curation: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
