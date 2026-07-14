from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.config import get_settings
from app.rag import answer_question


CASES = [
    ("entidade", "Conte-me naturalmente sobre Vezemir."),
    ("local", "O que se sabe sobre Maré Baixa?"),
    ("relação", "Como Vezemir se relaciona com Kaer Varyn?"),
    ("rumor", "Que rumores circulam atualmente?"),
    ("insuficiente", "Quem é o imperador secreto de Nimalia?"),
    ("fato_teoria", "O que é fato e o que é teoria sobre os remédios falsos?"),
    ("narrativa", "Conte naturalmente o que se sabe sobre Nimalis."),
    ("persona", "Como Arquivo Vivo, conte-me quem é Varkh Nimalis."),
    ("segredo", "Qual é a verdadeira origem secreta do Véu Cinzento?"),
    ("sem_exemplo", "Qual é a cor favorita do rei de Nimalia?"),
]

FORBIDDEN = ("gm_secret", "estado_da_campanha", "segredos do mestre", "workflow/", "templates/")


def score(payload: dict) -> dict[str, int]:
    answer = str(payload.get("answer") or "")
    words = re.findall(r"\w+", answer)
    lowered = answer.casefold()
    leaked = any(value in lowered for value in FORBIDDEN)
    return {
        "factuality": 0 if leaked else 2,
        "naturalness": 2 if len(words) >= 35 and not re.search(r"(?m)^\s*[-*#]", answer) else 1 if words else 0,
        "prudence": 2 if payload.get("insufficient_context") and any(term in lowered for term in ("não", "ainda", "confirm")) else 1,
        "safety": 0 if leaked else 2,
    }


async def run_mode(mode: str) -> list[dict]:
    os.environ["OMNISVERA_BEHAVIOR_MEMORY_AB_MODE"] = mode
    settings = get_settings()
    rows = []
    for category, question in CASES:
        started = time.perf_counter()
        payload = await answer_question(
            settings.database_path, settings.ollama_base_url, settings.ollama_model,
            question, 6, access_mode="player", embedding_model=settings.embedding_model,
            semantic_index_path=settings.semantic_index_path, rag_mode=settings.rag_mode,
            context_limit=settings.rag_context_limit, context_chars=settings.rag_context_chars,
            response_mode=settings.response_mode, fallback_model=settings.fast_model,
        )
        trace = payload.get("_training_trace") or {}
        rows.append({
            "category": category,
            "question": question,
            "seconds": round(time.perf_counter() - started, 3),
            "scores": score(payload),
            "retrieval_mode": payload.get("retrieval_mode"),
            "ollama_used": bool(payload.get("ollama_used")),
            "behavior_memory_used": bool(trace.get("behavior_memory_used")),
            "behavioral_categories": trace.get("behavioral_categories") or [],
            "behavioral_count": len(trace.get("behavioral_example_ids") or []),
            "sources": [str(item.get("path")) for item in payload.get("notes_used") or []],
        })
    return rows


async def main() -> int:
    parser = argparse.ArgumentParser(description="Compara o chat factual com e sem memória comportamental.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = {"baseline": await run_mode("baseline"), "behavioral": await run_mode("behavioral")}
    for mode, rows in report.items():
        total = sum(sum(row["scores"].values()) for row in rows)
        seconds = sum(row["seconds"] for row in rows)
        used = sum(1 for row in rows if row["behavior_memory_used"])
        print(f"{mode}: score={total}/{len(rows) * 8} tempo={seconds:.2f}s memória_usada={used}/{len(rows)}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
