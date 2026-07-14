from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path


SMOKE_CLASSIFICATION = "EXPERIMENTAL — SMOKE TEST — NÃO USAR EM PRODUÇÃO"
EXPERIMENTAL_CLASSIFICATION = "EXPERIMENTAL — DATASET PEQUENO — NÃO USAR EM PRODUÇÃO"
ALLOWED_CLASSIFICATIONS = {SMOKE_CLASSIFICATION, EXPERIMENTAL_CLASSIFICATION}
ACK = "I_UNDERSTAND_THIS_IS_EXPERIMENTAL_NOT_FOR_PRODUCTION"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_jsonl(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip())


def expected_updates(train_examples: int, config: dict) -> int:
    batch = int(config.get("per_device_train_batch_size") or config.get("batch_size") or 1)
    accumulation = int(config.get("gradient_accumulation_steps") or config.get("gradient_accumulation") or 1)
    epochs = int(config.get("epochs") or 1)
    return math.ceil(train_examples / max(1, batch * accumulation)) * epochs


def validate(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    hashes = json.loads((root / "hashes.sha256.json").read_text(encoding="utf-8"))
    config_path = root / str(manifest.get("config_path") or "config/smoke-colab.json")
    requirements_path = root / str(manifest.get("requirements_file") or "requirements-train.txt")
    train_path = root / "dataset/train.jsonl"
    eval_path = root / "dataset/eval.jsonl"
    errors = []
    classification = manifest.get("classification")
    if classification not in ALLOWED_CLASSIFICATIONS:
        errors.append("classificação inválida")
    if not manifest.get("experimental_only") or manifest.get("production_eligible"):
        errors.append("gate experimental inválido")
    for name, expected in hashes.items():
        path = root / name
        if not path.is_file() or sha256(path) != expected:
            errors.append(f"hash inválido: {name}")
    for path in (train_path, eval_path, config_path, requirements_path):
        if not path.is_file():
            errors.append(f"arquivo ausente: {path.relative_to(root).as_posix()}")
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {}
    train_examples = count_jsonl(train_path) if train_path.is_file() else 0
    eval_examples = count_jsonl(eval_path) if eval_path.is_file() else 0
    updates = expected_updates(train_examples, config) if config else 0
    if updates != int(manifest.get("expected_optimizer_updates") or updates):
        errors.append("optimizer steps divergem do manifesto")
    if classification == EXPERIMENTAL_CLASSIFICATION and updates <= 1:
        errors.append("treino experimental exige mais de um optimizer step")
    return {
        "valid": not errors,
        "errors": errors,
        "classification": classification,
        "examples": manifest.get("eligible_examples", 0),
        "train_examples": train_examples,
        "eval_examples": eval_examples,
        "epochs": config.get("epochs"),
        "per_device_train_batch_size": config.get("per_device_train_batch_size", config.get("batch_size")),
        "per_device_eval_batch_size": config.get("per_device_eval_batch_size", 1),
        "gradient_accumulation_steps": config.get("gradient_accumulation_steps", config.get("gradient_accumulation")),
        "optimizer_steps_expected": updates,
        "learning_rate": config.get("learning_rate"),
        "config_path": str(config_path),
        "requirements_path": str(requirements_path),
    }


def prepare_dependencies(requirements_path: Path) -> None:
    # LoRA FP16 does not use torchao. Removing an incompatible preinstalled
    # release avoids PEFT's optional torchao version gate on Colab.
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "torchao"], check=False)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-r", str(requirements_path)],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Omnisvera experimental Colab runner")
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root = args.package_root.resolve()
    report = validate(root)
    report["training_started"] = False
    if not report["valid"]:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    if args.dry_run:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if not os.getenv("HF_TOKEN"):
        raise RuntimeError("HF_TOKEN ausente no ambiente do Colab")
    prepare_dependencies(Path(report["requirements_path"]))
    command = [
        sys.executable,
        "-m",
        "omnisvera_model",
        "train-lora",
        "--config",
        report["config_path"],
        "--dataset-dir",
        str(root / "dataset"),
        "--output-dir",
        str(root / "output"),
        "--acknowledgement",
        ACK,
    ]
    return subprocess.run(command, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
