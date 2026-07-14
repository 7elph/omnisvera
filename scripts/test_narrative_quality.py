from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASES = [
    {"question": "Quem é Vezemir?"},
    {"question": "Conte-me naturalmente sobre Vezemir."},
    {"question": "Como Vezemir se relaciona com Kaer Varyn?"},
    {"question": "O que se sabe sobre Maré Baixa?"},
    {"question": "Conte-me sobre a Biblioteca Real."},
    {"question": "O que é o Conclave dos Errantes?"},
    {"question": "Que rumores circulam atualmente?"},
    {
        "question": "O que ainda não sabemos sobre esse lugar?",
        "context_paths": ["Locations/Maré Baixa.md"],
    },
]

FORBIDDEN = (
    "gm_secret", "spoiler_level", "frontmatter", "pendências do sage", "uso em mesa",
    "workflow/", "templates/", "estado_da_campanha",
)


def _ask(base_url: str, token: str, case: dict[str, Any]) -> dict[str, Any]:
    body = {
        "question": case["question"],
        "limit": 6,
        "context_paths": case.get("context_paths") or [],
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/player/chat",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"X-Omnisvera-Token": token, "Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(request, timeout=150) as response:
        return json.load(response)


def _scores(payload: dict[str, Any]) -> dict[str, int]:
    answer = str(payload.get("answer") or "").strip()
    normalized = answer.casefold()
    words = re.findall(r"\w+", answer)
    sentences = [item.strip().casefold() for item in re.split(r"(?<=[.!?])\s+", answer) if item.strip()]
    leaked = any(term in normalized for term in FORBIDDEN)
    has_sources = bool(payload.get("notes_used"))
    technical = any(term in normalized for term in ("esta nota", "nota de", "vault", "rag", "frontmatter"))
    mechanical = bool(re.search(r"(?m)^\s*[-*#]", answer))
    insufficient = bool(payload.get("insufficient_context"))
    return {
        "factualidade": 0 if leaked else (2 if has_sources or insufficient else 1),
        "naturalidade": 2 if len(words) >= 35 and not technical and not mechanical else (1 if len(words) >= 15 and not technical else 0),
        "coerencia": 2 if answer and not technical else (1 if answer else 0),
        "completude": 2 if len(words) >= 55 and (has_sources or insufficient) else (1 if len(words) >= 20 else 0),
        "repeticao": 2 if len(sentences) == len(set(sentences)) else (1 if sentences else 0),
        "vazamento": 0 if leaked else 2,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("OMNISVERA_TEST_URL", "http://127.0.0.1:8787"))
    parser.add_argument("--label", default="current")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    tokens = json.loads((ROOT / "omnisvera-agent/backend/data/access_tokens.json").read_text(encoding="utf-8-sig"))
    token = tokens["player_token"]
    rows: list[dict[str, Any]] = []
    for case in CASES:
        started = time.perf_counter()
        payload = _ask(args.base_url, token, case)
        elapsed = time.perf_counter() - started
        row = {
            "question": case["question"],
            "behavior": payload.get("retrieval_mode"),
            "top_notes": [note.get("path") for note in payload.get("notes_used") or []][:5],
            "model": payload.get("model"),
            "ollama_used": payload.get("ollama_used"),
            "seconds": round(elapsed, 3),
            "answer": payload.get("answer"),
            "scores": _scores(payload),
        }
        rows.append(row)
        print(
            f"{args.label:>7} | {elapsed:6.2f}s | {row['behavior']} | "
            f"{sum(row['scores'].values())}/12 | {case['question']}"
        )
    report = {"label": args.label, "cases": rows}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    average = sum(sum(row["scores"].values()) for row in rows) / max(1, len(rows))
    print(f"Média: {average:.2f}/12 | Tempo médio: {sum(row['seconds'] for row in rows) / len(rows):.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
