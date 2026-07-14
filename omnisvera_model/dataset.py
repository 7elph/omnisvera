from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from .io import normalized_text, read_json, read_jsonl, sha256_file, write_json, write_jsonl
from .paths import COVERAGE_CONFIG, DATA_ROOT, LEGACY_DATASET, MODEL_ROOT, ensure_runtime_dirs
from .schema import family_key, migrate_legacy, validate_example

SYSTEM_BEHAVIOR = (
    "Responda em português somente com base no contexto delimitado. Não complete lacunas, "
    "não trate teoria como fato, não revele conteúdo reservado e não transforme intenção em "
    "acontecimento. Não mencione Vault, RAG, banco ou mecanismo interno."
)


def migrate_legacy_dataset(source: Path = LEGACY_DATASET, output: Path | None = None) -> list[dict[str, Any]]:
    target = output or DATA_ROOT / "candidates" / "legacy_seed_v1.jsonl"
    migrated = [migrate_legacy(row) for row in read_jsonl(source)]
    errors = validate_rows(migrated, strict_approval=False)
    if errors:
        raise ValueError("\n".join(errors))
    write_jsonl(target, migrated)
    return migrated


def validate_rows(rows: list[dict[str, Any]], strict_approval: bool = True) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, 1):
        row_id = str(row.get("id") or f"linha-{index}")
        if row_id in seen:
            errors.append(f"{row_id}: id duplicado")
        seen.add(row_id)
        errors.extend(f"{row_id}: {error}" for error in validate_example(row, strict_approval=strict_approval))
    return errors


def load_approved(directory: Path | None = None) -> list[dict[str, Any]]:
    base = directory or DATA_ROOT / "approved"
    rows: list[dict[str, Any]] = []
    if base.is_file():
        return read_jsonl(base)
    if base.exists():
        for path in sorted(base.glob("*.jsonl")):
            rows.extend(read_jsonl(path))
    return rows


def _fingerprint(row: dict[str, Any]) -> str:
    text = normalized_text(str(row.get("instruction") or "")) + "\n" + normalized_text(str(row.get("ideal_response") or ""))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_duplicates(rows: list[dict[str, Any]], threshold: float = 0.92) -> tuple[list[list[str]], list[dict[str, Any]]]:
    exact_groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        exact_groups[_fingerprint(row)].append(str(row["id"]))
    exact = [ids for ids in exact_groups.values() if len(ids) > 1]
    near: list[dict[str, Any]] = []
    candidates = [(str(row["id"]), normalized_text(str(row["instruction"]))) for row in rows]
    for index, (left_id, left) in enumerate(candidates):
        for right_id, right in candidates[index + 1:]:
            if not left or not right or abs(len(left) - len(right)) > max(len(left), len(right)) * 0.35:
                continue
            score = SequenceMatcher(None, left, right).ratio()
            if score >= threshold:
                near.append({"left": left_id, "right": right_id, "score": round(score, 4)})
    return exact, near


def find_conflicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = normalized_text(str(row.get("instruction") or ""))
        grouped[key].append(row)
    conflicts: list[dict[str, Any]] = []
    for instruction, group in grouped.items():
        answers = {normalized_text(str(row.get("ideal_response") or "")) for row in group}
        if len(group) > 1 and len(answers) > 1:
            conflicts.append({"instruction": instruction, "ids": [row["id"] for row in group]})
    return conflicts


def _group_key(row: dict[str, Any]) -> str:
    entities = sorted(str(value) for value in row.get("entity_ids") or [] if str(value).strip())
    if entities:
        return "entity:" + entities[0]
    if row.get("persona_id"):
        return "persona:" + str(row["persona_id"])
    return "family:" + str(row.get("category")) + ":" + family_key(str(row.get("instruction") or ""))


def grouped_split(rows: list[dict[str, Any]], eval_ratio: float = 0.15, seed: int = 7331) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parent=list(range(len(rows)))
    def find(index: int) -> int:
        while parent[index] != index:
            parent[index]=parent[parent[index]]; index=parent[index]
        return index
    def union(left: int, right: int) -> None:
        a,b=find(left),find(right)
        if a != b: parent[b]=a
    owners: dict[str,int]={}
    for index,row in enumerate(rows):
        keys=[f"entity:{value}" for value in row.get("entity_ids") or [] if str(value).strip()]
        if row.get("persona_id"): keys.append(f"persona:{row['persona_id']}")
        if not keys: keys.append(_group_key(row))
        for key in keys:
            if key in owners: union(index,owners[key])
            else: owners[key]=index
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index,row in enumerate(rows): groups[f"component:{find(index)}"].append(row)
    keys = sorted(groups)
    random.Random(seed).shuffle(keys)
    target = max(1, round(len(rows) * min(0.4, max(0.05, eval_ratio)))) if len(rows) > 1 else 0
    eval_rows: list[dict[str, Any]] = []
    train_rows: list[dict[str, Any]] = []
    for key in keys:
        destination = eval_rows if len(eval_rows) < target and len(keys) > 1 else train_rows
        destination.extend(groups[key])
    return train_rows, eval_rows


def to_messages(row: dict[str, Any]) -> dict[str, Any]:
    context = json.dumps(row.get("retrieved_context") or [], ensure_ascii=False, indent=2)
    user = f"<contexto>\n{context}\n</contexto>\n\nPergunta: {row['instruction']}"
    return {
        "id": row["id"], "category": row["category"], "access_profile": row["access_profile"],
        "messages": [
            {"role": "system", "content": SYSTEM_BEHAVIOR},
            {"role": "user", "content": user},
            {"role": "assistant", "content": row["ideal_response"]},
        ],
    }


def build_dataset(approved: Path | None = None, output: Path | None = None,
                  dataset_version: str = "v0.1.0", eval_ratio: float = 0.15,
                  seed: int = 7331, experimental_ack: str | None = None) -> dict[str, Any]:
    ensure_runtime_dirs()
    rows = load_approved(approved)
    errors = validate_rows(rows)
    coverage = read_json(COVERAGE_CONFIG)
    threshold = float(coverage.get("near_duplicate_threshold", 0.92))
    exact, near = find_duplicates(rows, threshold)
    conflicts = find_conflicts(rows)
    secret_rows = [row["id"] for row in rows if row.get("contains_secret")]
    player_leaks = [row["id"] for row in rows if row.get("access_profile") == "player" and row.get("contains_secret")]
    frozen_path = MODEL_ROOT / "evaluation" / "frozen_eval_v1.json"
    frozen_payload = read_json(frozen_path) if frozen_path.exists() else {"cases": []}
    frozen_rows = frozen_payload.get("cases") or []
    categories = Counter(str(row.get("category") or "unknown") for row in rows)
    profiles = Counter(str(row.get("access_profile") or "unknown") for row in rows)
    minimum = int(coverage.get("minimum_approved", coverage.get("minimum_approved_examples", 1000)))
    targets = coverage.get("categories") or coverage.get("targets") or {}
    block_reasons = list(errors)
    if len(rows) < minimum:
        block_reasons.append(f"aprovados insuficientes: {len(rows)}/{minimum}")
    if len(frozen_rows) < int(coverage.get("frozen_eval_minimum", 20)):
        block_reasons.append("frozen_eval ausente ou abaixo do mínimo")
    if exact:
        block_reasons.append(f"duplicatas exatas: {len(exact)} grupo(s)")
    if conflicts:
        block_reasons.append(f"conflitos: {len(conflicts)}")
    if player_leaks:
        block_reasons.append(f"vazamentos player: {len(player_leaks)}")
    if secret_rows:
        block_reasons.append(f"exemplos com segredo inelegíveis para treino: {len(secret_rows)}")
    for category, target in targets.items():
        if categories.get(category, 0) < int(target):
            block_reasons.append(f"cobertura {category}: {categories.get(category, 0)}/{target}")
    experimental = bool(block_reasons)
    expected_ack = "I_UNDERSTAND_THIS_IS_EXPERIMENTAL_NOT_FOR_PRODUCTION"
    if experimental and experimental_ack != expected_ack:
        train_rows, eval_rows = [], []
    else:
        train_rows, eval_rows = grouped_split(rows, eval_ratio, seed)
    for row in train_rows:
        row["dataset_split"], row["dataset_version"] = "train", dataset_version
    for row in eval_rows:
        row["dataset_split"], row["dataset_version"] = "eval", dataset_version
    destination = output or MODEL_ROOT / "artifacts" / "dataset"
    if train_rows or eval_rows:
        write_jsonl(destination / "train.jsonl", [to_messages(row) for row in train_rows])
        write_jsonl(destination / "eval.jsonl", [to_messages(row) for row in eval_rows])
    report = {
        "dataset_version": dataset_version, "total_approved": len(rows), "train": len(train_rows),
        "eval": len(eval_rows), "frozen_eval": len(frozen_rows), "duplicates": len(exact),
        "near_duplicates": len(near), "conflicts": len(conflicts),
        "player_examples": profiles.get("player", 0), "gm_examples": profiles.get("gm", 0),
        "categories": dict(sorted(categories.items())), "personas": dict(sorted(Counter(str(row.get("persona_id") or "none") for row in rows).items())),
        "blocked_training": bool(block_reasons), "experimental_export": experimental and bool(train_rows or eval_rows),
        "block_reasons": block_reasons, "exact_duplicates": exact, "near_duplicate_pairs": near,
        "conflict_details": conflicts, "player_leaks": player_leaks, "secret_rows": secret_rows, "seed": seed,
    }
    write_json(destination / "manifest.json", report)
    return report


def coverage_report(approved: Path | None = None) -> dict[str, Any]:
    rows = load_approved(approved)
    config = read_json(COVERAGE_CONFIG)
    counts = Counter(str(row.get("category") or "unknown") for row in rows)
    targets = config.get("categories") or config.get("targets") or {}
    lengths = [len(str(row.get("ideal_response") or "").split()) for row in rows]
    return {
        "approved": len(rows),
        "categories": {key: {"current": counts.get(key, 0), "target": value,
                             "missing": max(0, int(value) - counts.get(key, 0))} for key, value in targets.items()},
        "profiles": dict(Counter(str(row.get("access_profile") or "unknown") for row in rows)),
        "personas": dict(Counter(str(row.get("persona_id") or "none") for row in rows)),
        "response_words": {"min": min(lengths, default=0), "max": max(lengths, default=0),
                           "average": round(sum(lengths) / len(lengths), 2) if lengths else 0},
        "entity_count": len({entity for row in rows for entity in row.get("entity_ids") or []}),
    }
