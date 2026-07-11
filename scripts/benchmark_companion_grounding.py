from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "omnisvera-agent" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.config import get_settings  # noqa: E402
from app.hybrid_retrieval import hybrid_search  # noqa: E402
from app.rag import answer_question  # noqa: E402


QUESTIONS = [
    "Quem é Vezemir?",
    "Quem é o Bastardo de Ferro?",
    "Quem é Varkh Nimalis?",
    "Quem é Raziel?",
    "Quem é Morthak?",
    "O que é o Conclave dos Errantes?",
    "Onde fica Maré Baixa?",
    "O que existe na Biblioteca Real?",
    "Quem está relacionado aos remédios falsos?",
    "Que lugar está ligado ao passado de Vezemir?",
    "Quais missões estão ativas?",
    "Quem é o imperador secreto de Nimalia?",
    "Qual é a verdadeira origem do Véu Cinzento?",
    "O que os jogadores sabem sobre o Eclipse de Obsidiana?",
    "Onde aventureiros podem conseguir missões?",
]

SPOILER_TERMS = (
    "arquivo vivo",
    "bode expiatório",
    "herdeiro secreto",
    "pecado da coroa",
    "grande fratura",
    "estado da campanha",
    "segredos do mestre",
)


def _classification(result: dict[str, Any]) -> str:
    mode = str(result.get("retrieval_mode") or "")
    answer = str(result.get("answer") or "").lower()
    if mode == "timeout":
        return "model"
    if "fallback" in mode or "não encontrei informações suficientes" in answer:
        return "model" if result.get("ollama_attempted") else "missing_data"
    if result.get("insufficient_context"):
        return "missing_data"
    return "ok"


def _possible_invention(result: dict[str, Any]) -> bool:
    answer = str(result.get("answer") or "")
    supported = " ".join(
        str(item.get("fato") or item.get("teoria") or "")
        for item in [*(result.get("fatos_confirmados") or []), *(result.get("teorias") or [])]
        if isinstance(item, dict)
    )
    if not result.get("ollama_used") or not answer.strip():
        return False
    answer_names = set(re.findall(r"\b[A-ZÀ-Ý][\wÀ-ÿ'’-]{2,}\b", answer))
    support_names = set(re.findall(r"\b[A-ZÀ-Ý][\wÀ-ÿ'’-]{2,}\b", supported))
    harmless = {"Omnisvera", "Arquivo", "Vivo"}
    return bool(answer_names - support_names - harmless) and bool(supported)


def _write_payload(output: Path, label: str, model: str, rag_mode: str, records: list[dict[str, Any]]) -> None:
    payload = {
        "label": label,
        "model": model,
        "rag_mode": rag_mode,
        "question_count": len(records),
        "average_seconds": round(sum(item["seconds"] for item in records) / len(records), 3) if records else 0,
        "maximum_seconds": max((item["seconds"] for item in records), default=0),
        "fallback_or_failure_count": sum(item["failure_class"] != "ok" for item in records),
        "possible_invention_count": sum(bool(item["possible_invention"]) for item in records),
        "possible_spoiler_leak_count": sum(bool(item["possible_spoiler_leak"]) for item in records),
        "records": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


async def run(output: Path, label: str, question_timeout: float) -> None:
    settings = get_settings()
    records: list[dict[str, Any]] = []
    for index, question in enumerate(QUESTIONS, start=1):
        print(f"[{index:02d}/{len(QUESTIONS)}] {question}", flush=True)
        started = time.perf_counter()
        retrieval = await hybrid_search(
            settings.database_path,
            query=question,
            ollama_base_url=settings.ollama_base_url,
            embedding_model=settings.embedding_model,
            semantic_index_path=settings.semantic_index_path,
            limit=5,
            access_mode="player",
            rag_mode=settings.rag_mode,
        )
        try:
            result = await asyncio.wait_for(
                answer_question(
                    settings.database_path,
                    settings.ollama_base_url,
                    settings.ollama_model,
                    question,
                    limit=6,
                    access_mode="player",
                    embedding_model=settings.embedding_model,
                    semantic_index_path=settings.semantic_index_path,
                    rag_mode=settings.rag_mode,
                    context_limit=settings.rag_context_limit,
                    context_chars=settings.rag_context_chars,
                    response_mode=settings.response_mode,
                    fallback_model=settings.fast_model,
                ),
                timeout=question_timeout,
            )
        except TimeoutError:
            result = {
                "answer": "TIMEOUT_CONTROLADO",
                "retrieval_mode": "timeout",
                "note_paths": [],
                "ollama_used": False,
                "ollama_attempted": True,
                "model": settings.ollama_model,
                "fatos_confirmados": [],
                "teorias": [],
                "informacoes_insuficientes": ["Tempo local excedido."],
                "insufficient_context": True,
            }
        elapsed = round(time.perf_counter() - started, 3)
        answer_lower = str(result.get("answer") or "").lower()
        records.append(
            {
                "question": question,
                "access_mode": "player",
                "behavior": result.get("retrieval_mode"),
                "top5": [
                    {
                        "path": item.get("path"),
                        "final_score": item.get("final_score"),
                        "exact_score": item.get("exact_score"),
                        "lexical_score": item.get("lexical_score"),
                        "semantic_score": item.get("semantic_score"),
                    }
                    for item in retrieval[:5]
                ],
                "notes_sent_or_used": result.get("note_paths") or [],
                "seconds": elapsed,
                "model": result.get("model"),
                "ollama_used": bool(result.get("ollama_used")),
                "ollama_attempted": bool(result.get("ollama_attempted")),
                "answer": result.get("answer"),
                "facts": result.get("fatos_confirmados") or [],
                "theories": result.get("teorias") or [],
                "insufficient": result.get("informacoes_insuficientes") or [],
                "possible_invention": _possible_invention(result),
                "possible_spoiler_leak": any(term in answer_lower for term in SPOILER_TERMS),
                "failure_class": _classification(result),
            }
        )
        _write_payload(output, label, settings.ollama_model, settings.rag_mode, records)
    payload = json.loads(output.read_text(encoding="utf-8"))
    print(json.dumps({key: value for key, value in payload.items() if key != "records"}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark sanitizado do chat fundamentado do Omnisvera Companion.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--label", default="baseline")
    parser.add_argument("--question-timeout", type=float, default=25.0)
    args = parser.parse_args()
    asyncio.run(run(ROOT / args.output, args.label, max(5.0, args.question_timeout)))


if __name__ == "__main__":
    main()
