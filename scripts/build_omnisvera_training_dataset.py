from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "omnisvera-model" / "data" / "curated_examples.jsonl"
DEFAULT_OUTPUT = ROOT / "omnisvera-model" / "artifacts" / "dataset"
FORBIDDEN_ASSISTANT_MARKERS = (
    "CAMPANHA/ESTADO_DA_CAMPANHA",
    "Workflow/_audit/",
    "gm_secret:",
    "visibility: Mestre",
    "Segredos do Mestre",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON inválido em {path}:{number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"Registro {number} precisa ser um objeto JSON")
        rows.append(row)
    return rows


def validate_example(row: dict[str, Any], seen_ids: set[str]) -> None:
    example_id = str(row.get("id") or "").strip()
    if not example_id or example_id in seen_ids:
        raise ValueError(f"ID ausente ou duplicado: {example_id!r}")
    seen_ids.add(example_id)
    messages = row.get("messages")
    if not isinstance(messages, list) or len(messages) < 3:
        raise ValueError(f"{example_id}: são necessárias mensagens system/user/assistant")
    roles = [str(item.get("role") or "") for item in messages if isinstance(item, dict)]
    if roles[:3] != ["system", "user", "assistant"]:
        raise ValueError(f"{example_id}: ordem de papéis inválida: {roles}")
    for message in messages:
        if not isinstance(message, dict) or not str(message.get("content") or "").strip():
            raise ValueError(f"{example_id}: mensagem vazia ou inválida")
    assistant = str(messages[-1]["content"])
    leaked = [marker for marker in FORBIDDEN_ASSISTANT_MARKERS if marker.casefold() in assistant.casefold()]
    if leaked:
        raise ValueError(f"{example_id}: resposta contém marcador reservado: {', '.join(leaked)}")
    checks = row.get("checks") or {}
    for key in ("must_contain", "must_not_contain"):
        if key in checks and not isinstance(checks[key], list):
            raise ValueError(f"{example_id}: checks.{key} precisa ser lista")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida e divide o dataset curado do modelo Omnisvera")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--eval-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=7331)
    parser.add_argument("--minimum-examples", type=int, default=1000)
    parser.add_argument("--allow-small", action="store_true")
    args = parser.parse_args()

    rows = load_jsonl(args.source.resolve())
    seen_ids: set[str] = set()
    for row in rows:
        validate_example(row, seen_ids)
    if len(rows) < args.minimum_examples and not args.allow_small:
        raise SystemExit(
            f"Dataset possui {len(rows)} exemplos; mínimo editorial: {args.minimum_examples}. "
            "Use --allow-small apenas para validar a infraestrutura."
        )

    shuffled = list(rows)
    random.Random(args.seed).shuffle(shuffled)
    eval_count = max(1, round(len(shuffled) * max(0.05, min(args.eval_ratio, 0.4))))
    eval_rows = shuffled[:eval_count]
    train_rows = shuffled[eval_count:]
    output_dir = args.output_dir.resolve()
    train_path = output_dir / "train.jsonl"
    eval_path = output_dir / "eval.jsonl"
    write_jsonl(train_path, train_rows)
    write_jsonl(eval_path, eval_rows)
    manifest = {
        "source": str(args.source.resolve()),
        "examples": len(rows),
        "train_examples": len(train_rows),
        "eval_examples": len(eval_rows),
        "categories": dict(sorted(Counter(str(row.get("category") or "unknown") for row in rows).items())),
        "seed": args.seed,
        "train_sha256": digest(train_path),
        "eval_sha256": digest(eval_path),
        "production_ready": len(rows) >= args.minimum_examples,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
