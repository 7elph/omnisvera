from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.behavioral_memory import BehavioralMemory, project_example
from app.narrative_composer import build_prompt
from app import training_curation as curation
from omnisvera_model.io import read_jsonl


def row(example_id: str = "example-1", **updates):
    value = {
        "id": example_id,
        "review_status": "approved",
        "access_profile": "player",
        "persona_id": None,
        "category": "grounded_qa",
        "instruction": "Quem é o Cavaleiro Azul?",
        "ideal_response": "O Cavaleiro Azul protege a ponte. Outros detalhes ainda não foram revelados.",
        "insufficient_information_expected": True,
        "theories_allowed": [],
        "contains_secret": False,
        "notes": json.dumps({"flags": {}, "quality_5": 5}),
    }
    value.update(updates)
    return value


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in rows), encoding="utf-8")


class BehavioralMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.approved = self.root / "approved"

    def tearDown(self):
        self.temp.cleanup()

    def memory(self, rows, **kwargs):
        write_rows(self.approved / "examples.jsonl", rows)
        return BehavioralMemory(self.approved, min_score=0.0, **kwargs)

    def test_01_approved_is_projected(self):
        projection, reason = project_example(row())
        self.assertIsNone(reason); self.assertIsNotNone(projection)

    def test_02_pending_is_excluded(self):
        projection, reason = project_example(row(review_status="pending"))
        self.assertIsNone(projection); self.assertEqual("status_not_approved", reason)

    def test_03_rejected_is_excluded(self):
        projection, _ = project_example(row(review_status="rejected"))
        self.assertIsNone(projection)

    def test_04_secret_is_excluded(self):
        projection, reason = project_example(row(contains_secret=True))
        self.assertIsNone(projection); self.assertEqual("contains_secret", reason)

    def test_05_leak_is_excluded(self):
        projection, _ = project_example(row(notes=json.dumps({"flags": {"leak_detected": True}})))
        self.assertIsNone(projection)

    def test_06_hallucination_is_excluded(self):
        projection, _ = project_example(row(notes=json.dumps({"flags": {"hallucination_detected": True}})))
        self.assertIsNone(projection)

    def test_07_empty_ideal_is_excluded(self):
        projection, reason = project_example(row(ideal_response=""))
        self.assertIsNone(projection); self.assertEqual("empty_ideal_response", reason)

    def test_08_projection_has_no_source_path(self):
        projection, _ = project_example(row(ideal_response="Veja Characters/Individual/Segredo.md"))
        self.assertNotIn("Characters/", json.dumps(projection, ensure_ascii=False))

    def test_09_projection_does_not_copy_entity_name(self):
        projection, _ = project_example(row())
        self.assertNotIn("Cavaleiro Azul", projection["sanitized_demonstration"])

    def test_10_projection_uses_placeholders(self):
        projection, _ = project_example(row())
        self.assertIn("[ENTIDADE]", projection["sanitized_demonstration"])

    def test_11_only_approved_rows_are_indexed(self):
        memory = self.memory([row(), row("pending", review_status="pending")])
        self.assertEqual(1, memory.stats()["indexed"])

    def test_12_player_does_not_receive_gm(self):
        memory = self.memory([row(access_profile="gm")])
        self.assertEqual([], memory.retrieve("Quem é alguém?", access_profile="player").examples)

    def test_13_gm_can_use_player_style(self):
        memory = self.memory([row()])
        self.assertEqual(1, len(memory.retrieve("Quem é alguém?", access_profile="gm").examples))

    def test_14_persona_mismatch_is_excluded(self):
        memory = self.memory([row(persona_id="oraculo")])
        self.assertEqual([], memory.retrieve("Quem é alguém?", access_profile="player", persona_id="arquivo").examples)

    def test_15_matching_persona_is_used(self):
        memory = self.memory([row(persona_id="oraculo")])
        self.assertEqual(1, len(memory.retrieve("Quem é alguém?", access_profile="player", persona_id="oraculo").examples))

    def test_16_top_k_is_respected(self):
        memory = self.memory([row(str(index)) for index in range(5)], top_k=2)
        self.assertEqual(2, len(memory.retrieve("Quem é alguém?", access_profile="player").examples))

    def test_17_threshold_can_disable_weak_match(self):
        write_rows(self.approved / "examples.jsonl", [row()])
        memory = BehavioralMemory(self.approved, min_score=1.0)
        self.assertEqual([], memory.retrieve("pedido completamente diferente", access_profile="player").examples)

    def test_18_disabled_memory_falls_back(self):
        memory = self.memory([row()], enabled=False)
        self.assertEqual("baseline", memory.retrieve("Quem?", access_profile="player").mode)

    def test_19_baseline_ab_mode_falls_back(self):
        memory = self.memory([row()], ab_mode="baseline")
        self.assertEqual([], memory.retrieve("Quem?", access_profile="player").examples)

    def test_20_mtime_refresh_adds_approval_without_restart(self):
        memory = self.memory([row()])
        self.assertEqual(1, memory.stats()["indexed"])
        write_rows(self.approved / "examples.jsonl", [row(), row("second")])
        self.assertEqual(2, memory.stats()["indexed"])

    def test_21_invalidate_reloads(self):
        memory = self.memory([row()])
        memory.refresh(); memory.invalidate(); memory.refresh()
        self.assertEqual(1, memory.stats()["indexed"])

    def test_22_prompt_labels_examples_as_non_factual(self):
        projection, _ = project_example(row())
        prompt = build_prompt("Quem é alguém?", {"entidade": "Alguém", "tipo": "personagem"}, "player", [projection])
        self.assertIn("não são fontes de fatos", prompt)

    def test_23_prompt_keeps_facts_before_behavior(self):
        projection, _ = project_example(row())
        prompt = build_prompt("Pergunta", {"entidade": "X", "tipo": "local"}, "player", [projection])
        self.assertLess(prompt.index("FATOS PERMITIDOS"), prompt.index("<behavioral_examples>"))

    def test_24_behavior_is_not_listed_as_source(self):
        projection, _ = project_example(row())
        prompt = build_prompt("Pergunta", {"entidade": "X", "tipo": "local", "fontes": ["Public.md"]}, "player", [projection])
        self.assertNotIn("Public.md", projection["sanitized_demonstration"])

    def test_25_stats_report_exclusions(self):
        memory = self.memory([row(), row("secret", contains_secret=True)])
        self.assertEqual(1, len(memory.stats()["excluded"]))

    def test_26_usage_is_observed_admin_side(self):
        memory = self.memory([row()])
        memory.retrieve("Quem é alguém?", access_profile="player")
        self.assertEqual(1, memory.stats()["recent_responses_using_memory"])

    def test_27_mode_is_reported(self):
        memory = self.memory([row()], mode="metadata_only")
        self.assertEqual("metadata_only", memory.stats()["mode"])

    def test_28_question_pattern_is_generic(self):
        projection, _ = project_example(row())
        self.assertEqual("entidade", projection["question_pattern"])

    def test_29_theory_policy_is_separate(self):
        projection, _ = project_example(row(theories_allowed=["Uma hipótese"])); self.assertEqual("separate", projection["fact_theory_policy"])

    def test_30_no_raw_ideal_response_is_stored(self):
        projection, _ = project_example(row())
        self.assertNotIn("ideal_response", projection)


class BatchCurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"; self.vault.mkdir()
        (self.vault / "Public.md").write_text("Fato público.", encoding="utf-8")
        self.originals = {name: getattr(curation, name) for name in (
            "INTERACTIONS_PATH", "CANDIDATES_PATH", "APPROVED_PATH", "REJECTED_PATH", "AUDIT_PATH"
        )}
        data = self.root / "data"
        curation.INTERACTIONS_PATH = data / "captured" / "interactions.jsonl"
        curation.CANDIDATES_PATH = data / "candidates" / "examples.jsonl"
        curation.APPROVED_PATH = data / "approved" / "examples.jsonl"
        curation.REJECTED_PATH = data / "rejected" / "examples.jsonl"
        curation.AUDIT_PATH = data / "raw" / "audit.jsonl"

    def tearDown(self):
        for name, value in self.originals.items(): setattr(curation, name, value)
        self.temp.cleanup()

    def capture(self, interaction_id="i-1", action="good", question="Pergunta repetível", answer="Resposta confirmada com contexto suficiente para revisão humana detalhada e segura."):
        result = curation.capture_interaction({
            "interaction_id": interaction_id, "user_profile": "gm", "question": question,
            "raw_model_response": answer,
            "final_response": answer,
            "verified_facts": [{"fato": "Fato público.", "fonte": "Public.md"}], "theories": [],
            "insufficient_information": [], "retrieved_sources": [{"path": "Public.md", "visibility": "Público"}],
            "feedback_action": action,
        }, self.vault)
        if action == "good":
            curation.update_example(result["example"]["id"], {"quality": 5})
        return result["example"]["id"]

    def test_31_master_session_creates_pending_candidate(self):
        result = curation.record_unreviewed_interaction({
            "interaction_id": "auto", "user_profile": "gm", "question": "Pergunta automática",
            "final_response": "Resposta automática longa o bastante para revisão, ainda sem qualquer aprovação.",
            "retrieved_sources": [{"path": "Public.md", "visibility": "Público"}],
        }, self.vault)
        self.assertEqual("pending", result["example"]["review_status"])
        self.assertEqual("unreviewed", result["interaction"]["feedback_status"])

    def test_32_batch_requires_text_confirmation(self):
        example_id = self.capture()
        with self.assertRaises(ValueError):
            curation.approve_batch([example_id], confirmation="sim", reviewed=True)

    def test_33_batch_requires_visual_review(self):
        example_id = self.capture()
        with self.assertRaises(ValueError):
            curation.approve_batch([example_id], confirmation="APROVAR LOTE", reviewed=False)

    def test_34_safe_batch_approves(self):
        example_id = self.capture()
        result = curation.approve_batch([example_id], confirmation="APROVAR LOTE", reviewed=True)
        self.assertEqual(1, result["approved_count"])

    def test_35_hallucination_is_blocked_from_batch(self):
        example_id = self.capture(action="hallucination")
        result = curation.validate_batch([example_id])
        self.assertIn("hallucination_detected", result["blocked"][0]["reasons"])

    def test_36_duplicate_is_blocked(self):
        first = self.capture("a"); curation.approve_batch([first], confirmation="APROVAR LOTE", reviewed=True)
        second = self.capture("b")
        result = curation.validate_batch([second])
        self.assertIn("critical_duplicate", result["blocked"][0]["reasons"])

    def test_37_pending_never_counts_as_approved(self):
        self.capture()
        self.assertEqual([], read_jsonl(curation.APPROVED_PATH))

    def test_38_feedback_updates_auto_captured_candidate(self):
        payload = {
            "interaction_id": "auto-feedback", "user_profile": "gm", "question": "Pergunta automática",
            "final_response": "Resposta automática para revisão.",
            "retrieved_sources": [{"path": "Public.md", "visibility": "Público"}],
        }
        automatic = curation.record_unreviewed_interaction(payload, self.vault)
        payload.update({"feedback_action": "hallucination", "reason": "Inventou um vínculo"})
        updated = curation.capture_interaction(payload, self.vault)
        self.assertEqual(automatic["example"]["id"], updated["example"]["id"])
        self.assertTrue(updated["example"]["curation"]["flags"]["hallucination_detected"])

    def test_39_conflicting_answer_is_blocked(self):
        first = self.capture("conflict-a", answer="Primeira resposta suficientemente longa e revisada para servir como resposta aprovada segura.")
        curation.approve_batch([first], confirmation="APROVAR LOTE", reviewed=True)
        second = self.capture("conflict-b", answer="Segunda resposta diferente e suficientemente longa para entrar em conflito com a primeira.")
        result = curation.validate_batch([second])
        self.assertIn("conflict", result["blocked"][0]["reasons"])

    def test_40_near_duplicate_is_blocked(self):
        first = self.capture("near-a", question="Quem é o guardião da ponte antiga?")
        curation.approve_batch([first], confirmation="APROVAR LOTE", reviewed=True)
        second = self.capture("near-b", question="Quem é o guardião daquela ponte antiga?")
        result = curation.validate_batch([second])
        self.assertIn("near_duplicate", result["blocked"][0]["reasons"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"behavioral memory and batch curation: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
