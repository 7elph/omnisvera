from __future__ import annotations

import importlib.metadata
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io import read_json, sha256_file, write_json
from .paths import ROOT


def git_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip() or "unknown"


def create_manifest(config_path: Path, dataset_manifest: Path, status: str,
                    output: Path, checkpoints: list[str] | None = None,
                    metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    config = read_json(config_path)
    dataset = read_json(dataset_manifest) if dataset_manifest.exists() else {}
    dependencies: dict[str, str] = {}
    for name in ("torch", "transformers", "datasets", "peft", "accelerate", "safetensors"):
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            dependencies[name] = "missing"
    manifest = {
        "model_id": config.get("experiment_name"), "base_model": config.get("base_model"),
        "dataset_version": dataset.get("dataset_version"), "dataset_examples": dataset.get("total_approved", 0),
        "dataset_manifest_sha256": sha256_file(dataset_manifest) if dataset_manifest.exists() else None,
        "seed": config.get("seed"), "hyperparameters": config, "dependencies": dependencies,
        "project_commit": git_commit(), "created_at": datetime.now(timezone.utc).isoformat(),
        "checkpoints": checkpoints or [], "metrics": metrics or {}, "status": status,
        "contains_secret_text": False,
    }
    write_json(output, manifest)
    return manifest

