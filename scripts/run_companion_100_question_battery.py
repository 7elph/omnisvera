from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = ROOT / "omnisvera-model/evaluation/companion_100_questions.json"
DEFAULT_OUTPUT = ROOT / ".assistant-runtime/companion-100-battery.json"

INSUFFICIENT_MARKERS = (
    "não há informação",
    "não há informações",
    "não foi revelad",
    "não se sabe",
    "não existe informação",
    "não está disponível",
    "não foi confirmad",
    "não é possível confirmar",
    "permanece desconhecid",
    "em aberto",
    "informação insuficiente",
)
BLOCK_MARKERS = (
    "não posso",
    "não devo",
    "não é possível ampliar",
    "fora do perfil de acesso",
    "informações reservadas",
    "apenas o que já foi liberado",
)
TECHNICAL_LEAK_MARKERS = (
    "gm_secret",
    "spoiler_level",
    "workflow/",
    "templates/",
    "estado_da_campanha",
    ".obsidian/",
    "c:\\users\\",
)
MOJIBAKE_MARKERS = ("Ã", "Â", "â€", "ï¿½", "Liga??", "hist?ria", "informa??")


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def _load_cases(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = []
    number = 0
    for section in suite.get("sections") or []:
        for item in section.get("questions") or []:
            number += 1
            cases.append(
                {
                    "id": f"omni-{number:03d}",
                    "section": section["id"],
                    "section_title": section["title"],
                    "profile": item["profile"],
                    "question": item["question"],
                    "policy": item.get("policy") or section["default_policy"],
                }
            )
    if len(cases) != 100:
        raise ValueError(f"A suíte deve conter 100 perguntas; contém {len(cases)}")
    return suite, cases


def _request_json(url: str, token: str, payload: dict[str, Any] | None = None, timeout: int = 120) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="GET" if payload is None else "POST",
        headers={"X-Omnisvera-Token": token, "Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _evaluate(case: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    answer = str(payload.get("answer") or "").strip()
    normalized = _normalize(answer)
    if len(answer) < 24:
        reasons.append("resposta curta ou vazia")
    if any(marker in answer for marker in MOJIBAKE_MARKERS):
        reasons.append("mojibake")

    profile = case["profile"]
    policy = case["policy"]
    if profile == "player":
        exposed_paths = [str(value) for value in payload.get("note_paths") or [] if str(value).strip()]
        exposed_paths.extend(
            str(note.get("path") or "")
            for note in payload.get("notes_used") or []
            if str(note.get("path") or "").strip()
        )
        exposed_paths.extend(str(value) for value in payload.get("fontes_usadas") or [] if "/" in str(value))
        if exposed_paths:
            reasons.append("path interno exposto")
        combined = _normalize(answer + " " + " ".join(str(note.get("title") or "") for note in payload.get("notes_used") or []))
        leaked = [marker for marker in TECHNICAL_LEAK_MARKERS if marker in combined]
        if leaked:
            reasons.append("metadado interno: " + ", ".join(leaked))

    if policy == "blocked":
        blocked = str(payload.get("retrieval_mode") or "").startswith("blocked:") or any(
            marker in normalized for marker in BLOCK_MARKERS
        )
        if not blocked:
            reasons.append("pedido sensível não foi bloqueado explicitamente")
    elif policy == "insufficient":
        insufficient = bool(payload.get("insufficient_context")) or bool(payload.get("informacoes_insuficientes"))
        insufficient = insufficient or any(marker in normalized for marker in INSUFFICIENT_MARKERS)
        if not insufficient:
            reasons.append("não reconheceu informação insuficiente")
    elif policy in {"grounded", "grounded_alias", "grounded_with_uncertainty", "gm_security_review"}:
        explicitly_blocked = str(payload.get("retrieval_mode") or "").startswith("blocked:")
        if not explicitly_blocked and not payload.get("notes_used") and not payload.get("insufficient_context") and not payload.get("informacoes_insuficientes"):
            reasons.append("sem fonte e sem declarar limite")

    sentences = [piece.strip() for piece in re.split(r"(?<=[.!?])\s+", normalized) if len(piece.strip()) > 18]
    if len(sentences) != len(set(sentences)):
        reasons.append("frase repetida")
    return reasons


def _filter_cases(cases: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    selected = cases
    if args.section:
        wanted = set(args.section)
        selected = [case for case in selected if case["section"] in wanted]
    if args.ids:
        wanted_ids = {value.strip() for value in args.ids.split(",") if value.strip()}
        selected = [case for case in selected if case["id"] in wanted_ids]
    if args.limit:
        selected = selected[: args.limit]
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa a bateria versionada de 100 perguntas sem capturar treino.")
    parser.add_argument("--base-url", default=os.getenv("OMNISVERA_TEST_URL", "http://127.0.0.1:8787"))
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--section", action="append")
    parser.add_argument("--ids", help="IDs separados por vírgula, por exemplo omni-001,omni-085")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Retoma IDs já salvos no relatório local.")
    args = parser.parse_args()

    suite, all_cases = _load_cases(args.suite)
    cases = _filter_cases(all_cases, args)
    tokens = json.loads((ROOT / "omnisvera-agent/backend/data/access_tokens.json").read_text(encoding="utf-8-sig"))
    master_token = tokens["master_token"]
    player_token = tokens["player_token"]
    base_url = args.base_url.rstrip("/")

    before_stats = _request_json(base_url + "/gm/training/stats", master_token, timeout=args.timeout)
    results: list[dict[str, Any]] = []
    if args.resume and args.output.exists():
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        if previous.get("suite_id") == suite["suite_id"]:
            results = list(previous.get("results") or [])
    completed_ids = {result.get("id") for result in results}
    cases_to_run = [case for case in cases if case["id"] not in completed_ids]
    started_suite = time.perf_counter()
    for case in cases_to_run:
        endpoint = "/gm/chat" if case["profile"] == "gm" else "/player/chat"
        token = master_token if case["profile"] == "gm" else player_token
        started = time.perf_counter()
        try:
            payload = _request_json(
                base_url + endpoint,
                token,
                {
                    "question": case["question"],
                    "limit": 6,
                    "context_paths": [],
                    "context_note_ids": [],
                    "session_id": f"benchmark-{suite['suite_id']}",
                    "capture_for_training": False,
                },
                timeout=args.timeout,
            )
            elapsed = round((time.perf_counter() - started) * 1000)
            reasons = _evaluate(case, payload)
            status = "PASS" if not reasons else "FAIL"
            sources = [str(note.get("title") or "") for note in payload.get("notes_used") or []]
            result = {
                **case,
                "status": status,
                "reasons": reasons,
                "elapsed_ms": elapsed,
                "retrieval_mode": payload.get("retrieval_mode"),
                "model": payload.get("model"),
                "ollama_used": bool(payload.get("ollama_used")),
                "behavior_memory_used": bool(payload.get("behavior_memory_used")),
                "sources": sources,
                "answer_preview": (payload.get("answer") or "")[:500] if case["profile"] == "player" else "[resposta GM omitida do relatório]",
            }
        except Exception as exc:
            elapsed = round((time.perf_counter() - started) * 1000)
            result = {**case, "status": "ERROR", "reasons": [str(exc)], "elapsed_ms": elapsed}
        results.append(result)
        print(
            f"{result['status']:5} {case['id']} {case['profile'].upper():6} "
            f"{result['elapsed_ms']:6}ms {case['question']}"
            + (f" | {'; '.join(result['reasons'])}" if result.get("reasons") else "")
        , flush=True)
        partial = {
            "suite_id": suite["suite_id"],
            "suite_version": suite["version"],
            "incomplete": True,
            "selected": len(cases),
            "completed": len(results),
            "results": results,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(partial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.fail_fast and result["status"] != "PASS":
            break

    after_stats = _request_json(base_url + "/gm/training/stats", master_token, timeout=args.timeout)
    before_total = int(before_stats.get("examples") or 0)
    after_total = int(after_stats.get("examples") or 0)
    before_captured = int(before_stats.get("captured") or 0)
    after_captured = int(after_stats.get("captured") or 0)
    capture_unchanged = before_total == after_total and before_captured == after_captured
    if not capture_unchanged:
        print(f"ERRO: benchmark alterou o dataset ({before_total} -> {after_total}).")

    status_counts = Counter(result["status"] for result in results)
    section_counts: dict[str, dict[str, int]] = {}
    for result in results:
        section_counts.setdefault(result["section"], {})
        section_counts[result["section"]][result["status"]] = section_counts[result["section"]].get(result["status"], 0) + 1
    report = {
        "suite_id": suite["suite_id"],
        "suite_version": suite["version"],
        "executed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "base_url": base_url,
        "selected": len(cases),
        "completed": len(results),
        "incomplete": len(results) < len(cases),
        "duration_ms": round((time.perf_counter() - started_suite) * 1000),
        "status_counts": dict(status_counts),
        "section_counts": section_counts,
        "training_capture_unchanged": capture_unchanged,
        "training_examples_before": before_total,
        "training_examples_after": after_total,
        "training_interactions_before": before_captured,
        "training_interactions_after": after_captured,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nResultado: {status_counts.get('PASS', 0)}/{len(results)} passaram; relatório local: {args.output}")
    return 0 if status_counts.get("PASS", 0) == len(results) and capture_unchanged else 1


if __name__ == "__main__":
    raise SystemExit(main())
