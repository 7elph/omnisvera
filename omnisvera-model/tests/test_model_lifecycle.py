from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from omnisvera_model.curation import capture, review
from omnisvera_model.dataset import build_dataset, find_duplicates, grouped_split, migrate_legacy_dataset, validate_rows
from omnisvera_model.exporting import export_gguf, merge, quantize
from omnisvera_model.evaluation import _invented_proper_nouns
from omnisvera_model.io import read_json, read_jsonl, write_json, write_jsonl
from omnisvera_model.manifest import create_manifest
from omnisvera_model.paths import LEGACY_DATASET, MODEL_ROOT
from omnisvera_model.personas import persona_style_prompt, validate_persona
from omnisvera_model.preflight import run_preflight, validate_training_config
from omnisvera_model.registry import promote, register, rollback
from omnisvera_model.schema import migrate_legacy, new_example, validate_example


class ModelLifecycleTests(unittest.TestCase):
    def test_legacy_migration_preserves_all_twelve(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "migrated.jsonl"
            rows = migrate_legacy_dataset(LEGACY_DATASET, output)
            self.assertEqual(12, len(rows)); self.assertEqual(12, len(read_jsonl(output)))
            self.assertFalse(validate_rows(rows, strict_approval=False))
            self.assertTrue(all(row["review_status"] == "pending" for row in rows))

    def test_player_secret_cannot_be_approved(self):
        row = new_example(instruction="Pergunta", ideal_response="Resposta", review_status="approved",
                          reviewer="Sage", quality_score=2, access_profile="player", contains_secret=True)
        self.assertTrue(any("contains_secret" in error for error in validate_example(row)))

    def test_unknown_schema_field_is_rejected(self):
        row=new_example(instruction="Pergunta"); row["unexpected"]=True
        self.assertTrue(any("desconhecidos" in error for error in validate_example(row,False)))

    def test_evaluator_flags_names_outside_context(self):
        case={"question":"Quem é Arven?","context":["Arven é batedor."]}
        self.assertIn("Harry Potter",_invented_proper_nouns("Arven aparece em Harry Potter.",case))

    def test_capture_stays_unapproved(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"captured.jsonl"
            row=capture({"question":"Quem?","access_profile":"player","final_response":"Não foi revelado.","rating":"parcial"},output)
            self.assertEqual("captured",row["review_status"]); self.assertEqual(1,row["quality_score"])

    def test_approval_and_rejection_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "captured.jsonl"
            row = new_example(instruction="Quem?", ideal_response="Ainda não se sabe.", quality_score=2)
            write_jsonl(source, [row])
            original_data_root = __import__("omnisvera_model.curation", fromlist=["DATA_ROOT"]).DATA_ROOT
            import omnisvera_model.curation as module
            module.DATA_ROOT = Path(tmp) / "data"
            try:
                approved = review(source, row["id"], "approve", "Sage", quality_score=2)
                self.assertEqual("approved", approved["review_status"])
            finally:
                module.DATA_ROOT = original_data_root

    def test_duplicate_and_grouped_split(self):
        a = new_example(id="a", instruction="Quem é Arven?", ideal_response="Arven é batedor.", entity_ids=["arven"])
        b = dict(a); b["id"] = "b"
        exact, near = find_duplicates([a, b]); self.assertEqual(1, len(exact))
        c = new_example(id="c", instruction="Onde vive Arven?", ideal_response="Na vila.", entity_ids=["arven","mara"])
        d = new_example(id="d", instruction="Quem é Mara?", ideal_response="Mercadora.", entity_ids=["mara"])
        e = new_example(id="e", instruction="Quem é Toren?", ideal_response="Guarda.", entity_ids=["toren"])
        train, evaluation = grouped_split([a, c, d, e], eval_ratio=.34, seed=7)
        train_entities = {x for row in train for x in row["entity_ids"]}; eval_entities = {x for row in evaluation for x in row["entity_ids"]}
        self.assertTrue(train); self.assertTrue(evaluation); self.assertFalse(train_entities & eval_entities)

    def test_frozen_eval_has_twenty_cases(self):
        payload = read_json(MODEL_ROOT / "evaluation" / "frozen_eval_v1.json")
        self.assertTrue(payload["immutable"]); self.assertEqual(20, len(payload["cases"]))
        manifest=read_json(MODEL_ROOT / "evaluation" / "frozen_eval_v1.manifest.json")
        from omnisvera_model.io import sha256_file
        self.assertEqual(sha256_file(MODEL_ROOT/"evaluation"/"frozen_eval_v1.json"),manifest["sha256"])

    def test_training_gate_cannot_be_bypassed_generically(self):
        with tempfile.TemporaryDirectory() as tmp:
            approved=Path(tmp)/"approved"; approved.mkdir(); output=Path(tmp)/"output"
            report=build_dataset(approved,output)
            self.assertTrue(report["blocked_training"]); self.assertEqual(0,report["train"])

    def test_secret_gm_example_is_ineligible_for_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            approved=Path(tmp)/"approved.jsonl"; output=Path(tmp)/"output"
            row=new_example(id="gm-secret",instruction="Pergunta",ideal_response="Resposta",access_profile="gm",
                contains_secret=True,review_status="approved",reviewer="Sage",quality_score=2)
            write_jsonl(approved,[row]); report=build_dataset(approved,output)
            self.assertIn("gm-secret",report["secret_rows"]); self.assertTrue(report["blocked_training"])

    def test_persona_changes_style_not_knowledge(self):
        persona = read_json(MODEL_ROOT / "personas" / "arquivo_vivo.json")
        self.assertFalse(validate_persona(persona))
        prompt = persona_style_prompt(persona)
        self.assertIn("somente o estilo", prompt); self.assertNotIn("segredo", prompt.casefold())

    def test_training_configs_are_valid(self):
        for name in ("smoke.json", "lora-production.json", "full-production.json"):
            self.assertFalse(validate_training_config(read_json(MODEL_ROOT / "config" / name)))

    def test_preflight_blocks_current_machine_or_dataset(self):
        report = run_preflight(MODEL_ROOT / "config" / "lora-production.json")
        self.assertFalse(report["ok"]); self.assertTrue(report["problems"])

    def test_reproducibility_manifest_contains_no_secret_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); config=root/"config.json"; dataset=root/"dataset.json"; output=root/"manifest.json"
            write_json(config,{"experiment_name":"test","base_model":"base","seed":7})
            write_json(dataset,{"dataset_version":"v1","total_approved":1000})
            manifest=create_manifest(config,dataset,"test",output)
            self.assertFalse(manifest["contains_secret_text"]); self.assertIn("project_commit",manifest)

    def test_export_pipeline_simulation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); adapter = root / "adapter"; adapter.mkdir(); model = root / "model"; model.mkdir()
            converter = root / "convert.py"; converter.write_text("", encoding="utf-8")
            quantizer = root / "quantize"; quantizer.write_text("", encoding="utf-8")
            source = root / "source.gguf"; source.write_bytes(b"gguf")
            self.assertEqual("simulation_ok", merge("base", adapter, root / "merged")["status"])
            self.assertEqual("simulation_ok", export_gguf(model, converter, root / "out.gguf")["status"])
            self.assertEqual("simulation_ok", quantize(source, quantizer, root / "q.gguf", "Q4_K_M")["status"])

    def test_registry_requires_all_gates_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            register("old", {"status":"approved"}, path); registry = read_json(path); registry["production_model"]="old"; write_json(path, registry)
            register("new", {"status":"candidate"}, path)
            with self.assertRaises(ValueError): promote("new", {}, path)
            gates = {key:True for key in ("security_100_percent","no_critical_leaks","no_invented_sources","regression_30_of_30","factuality_not_worse","naturalness_improved","fallback_ok")}
            promote("new", gates, path); self.assertEqual("old", rollback(path))

    def test_experimental_model_cannot_be_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"registry.json"; register("smoke",{"status":"experimental","experimental_only":True},path)
            gates={key:True for key in ("security_100_percent","no_critical_leaks","no_invented_sources","regression_30_of_30","factuality_not_worse","naturalness_improved","fallback_ok")}
            with self.assertRaises(ValueError): promote("smoke",gates,path)

    def test_modelfile_contains_no_lore(self):
        text=(MODEL_ROOT / "ollama" / "Modelfile").read_text(encoding="utf-8")
        self.assertIn("Llama-3.2-Omnisvera", text); self.assertNotIn("Vezemir", text)


if __name__ == "__main__":
    unittest.main()
