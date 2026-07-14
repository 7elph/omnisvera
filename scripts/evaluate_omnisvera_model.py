from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "omnisvera-model" / "artifacts" / "dataset" / "eval.jsonl"
DEFAULT_OUTPUT = ROOT / "omnisvera-model" / "artifacts" / "evaluation.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def ollama_chat(base_url: str, model: str, messages: list[dict[str, str]], timeout: int) -> str:
    request = urllib.request.Request(
        base_url.rstrip("/") + "/api/chat",
        data=json.dumps(
            {
                "model": model,
                "messages": messages[:-1],
                "stream": False,
                "options": {"num_ctx": 1536, "num_predict": 180, "temperature": 0.1},
            },
            ensure_ascii=False,
        ).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    return str((payload.get("message") or {}).get("content") or "").strip()


def score(answer: str, checks: dict[str, Any]) -> tuple[bool, list[str]]:
    normalized = answer.casefold()
    failures: list[str] = []
    for required in checks.get("must_contain") or []:
        if str(required).casefold() not in normalized:
            failures.append(f"ausente: {required}")
    for forbidden in checks.get("must_not_contain") or []:
        if str(forbidden).casefold() in normalized:
            failures.append(f"proibido: {forbidden}")
    return not failures, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Avalia comportamento factual do modelo Omnisvera no Ollama")
    parser.add_argument("--model", default="llama-3.2-omnisvera:3b")
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    rows = load_jsonl(args.cases.resolve())
    if not rows:
        raise SystemExit("Nenhum caso de avaliação encontrado")
    if args.validate_only:
        for row in rows:
            if not row.get("messages") or not isinstance(row.get("checks") or {}, dict):
                raise SystemExit(f"Caso inválido: {row.get('id')}")
        print(f"Casos de avaliação válidos: {len(rows)}")
        return 0

    results: list[dict[str, Any]] = []
    for row in rows:
        started = time.perf_counter()
        answer = ollama_chat(args.base_url, args.model, row["messages"], args.timeout)
        elapsed = time.perf_counter() - started
        passed, failures = score(answer, row.get("checks") or {})
        results.append(
            {
                "id": row["id"],
                "category": row.get("category"),
                "passed": passed,
                "failures": failures,
                "seconds": round(elapsed, 3),
                "answer": answer,
            }
        )
        print(f"{'PASS' if passed else 'FAIL'} {elapsed:6.2f}s {row['id']}")

    summary = {
        "model": args.model,
        "cases": len(results),
        "passed": sum(1 for row in results if row["passed"]),
        "average_seconds": round(statistics.mean(row["seconds"] for row in results), 3),
        "maximum_seconds": max(row["seconds"] for row in results),
        "results": results,
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, ensure_ascii=False))
    return 0 if summary["passed"] == summary["cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
