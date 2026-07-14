from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "omnisvera-model"
DATA_ROOT = MODEL_ROOT / "data"
SCHEMA_PATH = MODEL_ROOT / "schemas" / "training_example.schema.json"
PERSONA_SCHEMA_PATH = MODEL_ROOT / "schemas" / "npc_persona.schema.json"
LEGACY_DATASET = DATA_ROOT / "curated_examples.jsonl"
COVERAGE_CONFIG = MODEL_ROOT / "config" / "coverage_targets.json"
ARTIFACT_ROOT = MODEL_ROOT / "artifacts"
REGISTRY_PATH = ARTIFACT_ROOT / "model_registry.json"

DATA_STAGES = (
    "raw", "captured", "candidates", "reviewed", "approved", "rejected",
    "train", "eval", "frozen_eval",
)


def ensure_runtime_dirs() -> None:
    for stage in DATA_STAGES:
        (DATA_ROOT / stage).mkdir(parents=True, exist_ok=True)
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)

