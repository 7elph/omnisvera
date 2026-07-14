from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dataset import build_dataset, load_approved, validate_rows
from .io import read_json, sha256_file, write_json, write_jsonl
from .manifest import git_commit
from .paths import MODEL_ROOT, ROOT
from .training import SMOKE_ACK


CLASSIFICATION = "EXPERIMENTAL — SMOKE TEST — NÃO USAR EM PRODUÇÃO"
PRIVATE_PATH_PATTERN = re.compile(
    r"(?:(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/Users/|/home/|/content/drive/|file://)",
    re.IGNORECASE,
)
TOKEN_VALUE_PATTERN = re.compile(r"(?:hf_[A-Za-z0-9]{20,}|omni-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9._-]{16,})")
SECRET_MARKERS = (
    "gm_secret: true",
    "visibility: mestre",
    "visibility: gm",
    "campanha/estado_da_campanha",
    "segredos do mestre:",
)


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _sanitized_context(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or item.get("excerpt") or item.get("text") or "").strip()
        if content:
            sanitized.append({"kind": str(item.get("kind") or "authorized_context"), "content": content})
        else:
            sanitized.append(
                {
                    "kind": "authorized_source_metadata",
                    "type": str(item.get("type") or "unknown"),
                    "visibility": str(item.get("visibility") or "authorized"),
                }
            )
    return sanitized


def _sanitize_approved(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    eligible: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for source in rows:
        row_id = str(source.get("id") or "unknown")
        reason = None
        if source.get("review_status") != "approved":
            reason = "not_approved"
        elif source.get("contains_secret"):
            reason = "contains_secret"
        elif validate_rows([source]):
            reason = "schema_invalid"
        if reason:
            excluded.append({"id": row_id, "reason": reason})
            continue
        row = copy.deepcopy(source)
        row["retrieved_context"] = _sanitized_context(row.get("retrieved_context") or [])
        row["source_note_ids"] = []
        row["source_note_hashes"] = []
        row["reviewer"] = "human_reviewed"
        row["notes"] = None
        serialized = _json_text(row)
        if PRIVATE_PATH_PATTERN.search(serialized):
            excluded.append({"id": row_id, "reason": "private_path"})
            continue
        if TOKEN_VALUE_PATTERN.search(serialized):
            excluded.append({"id": row_id, "reason": "credential_like_value"})
            continue
        if any(marker in serialized.casefold() for marker in SECRET_MARKERS):
            excluded.append({"id": row_id, "reason": "secret_marker"})
            continue
        errors = validate_rows([row])
        if errors:
            excluded.append({"id": row_id, "reason": "sanitized_schema_invalid"})
            continue
        eligible.append(row)
    return eligible, excluded


def _copy_runtime(destination: Path) -> None:
    package_target = destination / "omnisvera_model"
    package_target.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / "omnisvera_model").glob("*.py")):
        shutil.copy2(source, package_target / source.name)
    shutil.copy2(MODEL_ROOT / "colab" / "runner.py", destination / "colab" / "runner.py")
    shutil.copy2(MODEL_ROOT / "requirements-train.txt", destination / "requirements-train.txt")
    for schema in sorted((MODEL_ROOT / "schemas").glob("*.json")):
        shutil.copy2(schema, destination / "schemas" / schema.name)


def _write_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != "hashes.sha256.json"):
        hashes[path.relative_to(root).as_posix()] = sha256_file(path)
    write_json(root / "hashes.sha256.json", hashes)
    return hashes


def validate_colab_directory(root: Path) -> dict[str, Any]:
    required = (
        "EXPERIMENTAL_SMOKE_TEST_ONLY.txt",
        "manifest.json",
        "hashes.sha256.json",
        "config/smoke-colab.json",
        "dataset/train.jsonl",
        "dataset/eval.jsonl",
        "dataset/manifest.json",
        "evaluation/frozen_eval_v1.json",
        "colab/runner.py",
    )
    missing = [name for name in required if not (root / name).is_file()]
    hashes = read_json(root / "hashes.sha256.json") if not missing else {}
    hash_errors = [name for name, expected in hashes.items() if not (root / name).is_file() or sha256_file(root / name) != expected]
    markdown = [path.relative_to(root).as_posix() for path in root.rglob("*.md")]
    private_paths: list[str] = []
    credentials: list[str] = []
    for path in (item for item in root.rglob("*") if item.is_file()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(root).as_posix()
        # This module contains the detector's literal patterns as source code.
        if relative != "omnisvera_model/colab.py" and PRIVATE_PATH_PATTERN.search(text):
            private_paths.append(relative)
        if TOKEN_VALUE_PATTERN.search(text):
            credentials.append(relative)
    manifest = read_json(root / "manifest.json") if (root / "manifest.json").exists() else {}
    errors = []
    errors.extend(f"missing:{name}" for name in missing)
    errors.extend(f"hash:{name}" for name in hash_errors)
    errors.extend(f"markdown:{name}" for name in markdown)
    errors.extend(f"private_path:{name}" for name in private_paths)
    errors.extend(f"credential:{name}" for name in credentials)
    if manifest.get("classification") != CLASSIFICATION:
        errors.append("classification")
    if not manifest.get("experimental_only") or manifest.get("production_eligible"):
        errors.append("production_gate")
    return {
        "valid": not errors,
        "errors": errors,
        "files": len([item for item in root.rglob("*") if item.is_file()]),
        "hashes": len(hashes),
        "examples": manifest.get("eligible_examples", 0),
    }


def prepare_colab_package(
    output: Path,
    approved: Path | None = None,
    config_path: Path | None = None,
    frozen_eval_path: Path | None = None,
    acknowledgement: str | None = None,
) -> dict[str, Any]:
    if acknowledgement != SMOKE_ACK:
        raise RuntimeError(f"prepare-colab exige --acknowledgement {SMOKE_ACK}")
    source_rows = load_approved(approved)
    eligible, excluded = _sanitize_approved(source_rows)
    if len(eligible) < 2:
        raise RuntimeError("smoke test exige pelo menos dois exemplos aprovados e elegíveis")
    canonical_config = config_path or MODEL_ROOT / "config" / "smoke.json"
    frozen_eval = frozen_eval_path or MODEL_ROOT / "evaluation" / "frozen_eval_v1.json"
    if not canonical_config.is_file() or not frozen_eval.is_file():
        raise FileNotFoundError("config de smoke ou frozen eval ausente")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="omnisvera-colab-") as temporary:
        root = Path(temporary) / "omnisvera-smoke"
        for folder in ("config", "dataset", "evaluation", "schemas", "colab"):
            (root / folder).mkdir(parents=True, exist_ok=True)
        sanitized_source = Path(temporary) / "approved_sanitized.jsonl"
        write_jsonl(sanitized_source, eligible)
        dataset_report = build_dataset(
            sanitized_source,
            root / "dataset",
            dataset_version="smoke-v0.1.0",
            seed=7331,
            experimental_ack=SMOKE_ACK,
        )
        config = read_json(canonical_config)
        config["allow_model_download"] = True
        config["license_acknowledged"] = True
        config["experimental_only"] = True
        config["package_classification"] = CLASSIFICATION
        write_json(root / "config" / "smoke-colab.json", config)
        shutil.copy2(frozen_eval, root / "evaluation" / "frozen_eval_v1.json")
        frozen_manifest = frozen_eval.with_name(frozen_eval.stem + ".manifest.json")
        if frozen_manifest.exists():
            shutil.copy2(frozen_manifest, root / "evaluation" / frozen_manifest.name)
        _copy_runtime(root)
        (root / "EXPERIMENTAL_SMOKE_TEST_ONLY.txt").write_text(
            CLASSIFICATION + "\n\nEste pacote não é elegível para promoção ou produção.\n",
            encoding="utf-8",
        )
        (root / "README_COLAB.txt").write_text(
            "Omnisvera smoke test experimental.\n"
            "1. Instale requirements-train.txt.\n"
            "2. Rode: python colab/runner.py --package-root . --dry-run\n"
            "3. Para o smoke autorizado: python colab/runner.py --package-root . --execute\n"
            "O runner exige HF_TOKEN no ambiente e nunca promove o resultado.\n",
            encoding="utf-8",
        )
        manifest = {
            "package_version": "smoke-v0.1.0",
            "classification": CLASSIFICATION,
            "experimental_only": True,
            "production_eligible": False,
            "training_started": False,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "project_commit": git_commit(),
            "approved_source_examples": len(source_rows),
            "eligible_examples": len(eligible),
            "excluded_examples": excluded,
            "train_examples": dataset_report["train"],
            "eval_examples": dataset_report["eval"],
            "frozen_eval_examples": dataset_report["frozen_eval"],
            "dataset_manifest_sha256": sha256_file(root / "dataset" / "manifest.json"),
            "runner": "colab/runner.py",
            "smoke_acknowledgement": SMOKE_ACK,
        }
        write_json(root / "manifest.json", manifest)
        _write_hashes(root)
        validation = validate_colab_directory(root)
        if not validation["valid"]:
            raise RuntimeError("pacote Colab inválido: " + "; ".join(validation["errors"]))
        if output.exists():
            output.unlink()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            archive.comment = CLASSIFICATION.encode("utf-8")
            for path in sorted(item for item in root.rglob("*") if item.is_file()):
                archive.write(path, path.relative_to(root).as_posix())
    with zipfile.ZipFile(output, "r") as archive:
        bad_member = archive.testzip()
        members = archive.namelist()
    if bad_member:
        raise RuntimeError(f"ZIP corrompido em {bad_member}")
    return {
        "command": "prepare-colab",
        "classification": CLASSIFICATION,
        "approved": len(source_rows),
        "eligible": len(eligible),
        "excluded": excluded,
        "zip": str(output),
        "size_bytes": output.stat().st_size,
        "sha256": sha256_file(output),
        "runner": "colab/runner.py",
        "members": len(members),
        "validation": validation,
        "training_started": False,
    }
