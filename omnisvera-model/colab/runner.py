from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


CLASSIFICATION = "EXPERIMENTAL — SMOKE TEST — NÃO USAR EM PRODUÇÃO"
ACK = "I_UNDERSTAND_THIS_IS_EXPERIMENTAL_NOT_FOR_PRODUCTION"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    hashes = json.loads((root / "hashes.sha256.json").read_text(encoding="utf-8"))
    errors = []
    if manifest.get("classification") != CLASSIFICATION:
        errors.append("classificação inválida")
    if not manifest.get("experimental_only") or manifest.get("production_eligible"):
        errors.append("gate experimental inválido")
    for name, expected in hashes.items():
        path = root / name
        if not path.is_file() or sha256(path) != expected:
            errors.append(f"hash inválido: {name}")
    for name in ("dataset/train.jsonl", "dataset/eval.jsonl", "config/smoke-colab.json"):
        if not (root / name).is_file():
            errors.append(f"arquivo ausente: {name}")
    return {"valid": not errors, "errors": errors, "examples": manifest.get("eligible_examples", 0)}


def main() -> int:
    parser = argparse.ArgumentParser(description=CLASSIFICATION)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root = args.package_root.resolve()
    report = validate(root)
    if not report["valid"]:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    if args.dry_run:
        report.update({"classification": CLASSIFICATION, "training_started": False})
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if not os.getenv("HF_TOKEN"):
        raise RuntimeError("HF_TOKEN ausente no ambiente do Colab")
    command = [
        sys.executable,
        "-m",
        "omnisvera_model",
        "train-lora",
        "--config",
        str(root / "config" / "smoke-colab.json"),
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
