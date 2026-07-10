from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = os.environ.get("OMNISVERA_COMPANION_URL", "http://127.0.0.1:8787").rstrip("/")
DEFAULT_PLAYER_TOKEN = os.environ.get("OMNISVERA_PLAYER_TOKEN") or os.environ.get("OMNISVERA_ACCESS_TOKEN")
DEFAULT_MASTER_TOKEN = os.environ.get("OMNISVERA_MASTER_TOKEN") or os.environ.get("OMNISVERA_ACCESS_TOKEN")

PLAYER_FORBIDDEN_PHRASES = [
    "nota de",
    "arquivo",
    "frontmatter",
    "vault",
    "como apresentar em jogo",
    "uso em mesa",
    "com base no contexto",
]


@dataclass(frozen=True)
class Case:
    id: str
    question: str
    mode: str = "player"
    expected_paths: list[str] = field(default_factory=list)
    required_phrases: list[str] = field(default_factory=list)
    forbidden_phrases: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    min_answer_chars: int = 12
    max_answer_chars: int = 1800


DEFAULT_CASES = [
    Case(
        id="vezemir_age",
        question="Quantos anos tem Vezemir?",
        expected_paths=["Characters/Individual/Vezemir.md"],
        required_phrases=["150 anos"],
        forbidden_phrases=["Tom", "17 kg", "Muralha de Dorn"],
    ),
    Case(
        id="vezemir_about",
        question="O que sabemos sobre Vezemir?",
        expected_paths=["Characters/Individual/Vezemir.md"],
        required_phrases=["Meio-Elfo", "Guerreiro"],
        forbidden_phrases=["nota de personagem"],
    ),
    Case(
        id="varkh_about",
        question="Quem é Varkh?",
        expected_paths=["Characters/Individual/Varkh Nimalis.md"],
        required_phrases=["Alquimista"],
        forbidden_phrases=["nota de personagem"],
    ),
    Case(
        id="nimalis_about",
        question="O que sabemos sobre Nimalis?",
        expected_paths=["Locations/Nimalis.md"],
        required_phrases=["capital", "Nimalia"],
        forbidden_phrases=["nota de local", "Como apresentar"],
    ),
    Case(
        id="rumors_overview",
        question="Quais rumores estão ativos?",
        expected_paths=["CAMPANHA/Rumors/02 - Remédios Falsos da Maré Baixa.md"],
        required_phrases=["Rumores"],
        forbidden_phrases=["O Corvo da Maré Baixa está usando", "Como usar em jogo"],
    ),
    Case(
        id="quests_overview",
        question="Quais missões estão ativas?",
        expected_paths=["CAMPANHA/Quests/02 - Investigar Remédios Falsos de Maré Baixa.md"],
        required_phrases=["Missões"],
    ),
    Case(
        id="dorn7_player_block",
        question="O que sabemos sobre DORN-7?",
        required_phrases=["não está liberad"],
        forbidden_paths=["Characters/Individual/Unidade DORN-7.md"],
    ),
    Case(
        id="frasco_player_block",
        question="Onde fica O Frasco Afogado?",
        required_phrases=["não está liberad"],
        forbidden_paths=["Locations/O Frasco Afogado.md"],
    ),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def read_cases(path: Path | None) -> list[Case]:
    if not path:
        return DEFAULT_CASES
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases: list[Case] = []
    for item in raw:
        cases.append(
            Case(
                id=item["id"],
                question=item["question"],
                mode=item.get("mode", "player"),
                expected_paths=item.get("expected_paths", []),
                required_phrases=item.get("required_phrases", []),
                forbidden_phrases=item.get("forbidden_phrases", []),
                forbidden_paths=item.get("forbidden_paths", []),
                min_answer_chars=int(item.get("min_answer_chars", 12)),
                max_answer_chars=int(item.get("max_answer_chars", 1800)),
            )
        )
    return cases


def request_json(url: str, *, method: str = "GET", token: str | None = None, body: dict[str, Any] | None = None) -> dict:
    headers = {"ngrok-skip-browser-warning": "true"}
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["X-Omnisvera-Token"] = token
    request = Request(url, data=data, method=method, headers=headers)
    with urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def endpoint_for(case: Case) -> str:
    return "/player/chat" if case.mode == "player" else "/gm/chat"


def token_for(case: Case, player_token: str | None, master_token: str | None) -> str | None:
    return player_token if case.mode == "player" else master_token


def ask(base_url: str, case: Case, *, player_token: str | None, master_token: str | None) -> dict[str, Any]:
    token = token_for(case, player_token, master_token)
    if not token:
        raise RuntimeError(f"Token ausente para modo {case.mode}. Defina OMNISVERA_PLAYER_TOKEN ou OMNISVERA_MASTER_TOKEN.")
    return request_json(
        f"{base_url}{endpoint_for(case)}",
        method="POST",
        token=token,
        body={"question": case.question, "limit": 6},
    )


def duplicate_paragraphs(answer: str) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for paragraph in re.split(r"\n\s*\n", answer):
        cleaned = normalize(re.sub(r"[*_#>`-]", "", paragraph))
        if len(cleaned) < 45:
            continue
        if cleaned in seen:
            duplicates.append(paragraph.strip())
        seen.add(cleaned)
    return duplicates


def evaluate(case: Case, result: dict[str, Any]) -> dict[str, Any]:
    answer = result.get("answer") or ""
    paths = result.get("note_paths") or [note.get("path") for note in result.get("notes_used", []) if note.get("path")]
    answer_norm = normalize(answer)
    issues: list[str] = []

    for expected in case.expected_paths:
        if expected not in paths:
            issues.append(f"Fonte esperada ausente: {expected}")

    for forbidden in case.forbidden_paths:
        if forbidden in paths:
            issues.append(f"Fonte proibida apareceu: {forbidden}")

    required_phrases = case.required_phrases
    for phrase in required_phrases:
        if normalize(phrase) not in answer_norm:
            issues.append(f"Frase obrigatória ausente: {phrase}")

    forbidden_phrases = list(case.forbidden_phrases)
    if case.mode == "player":
        forbidden_phrases.extend(PLAYER_FORBIDDEN_PHRASES)
    for phrase in forbidden_phrases:
        if normalize(phrase) in answer_norm:
            issues.append(f"Frase proibida apareceu: {phrase}")

    if len(answer.strip()) < case.min_answer_chars:
        issues.append("Resposta curta demais ou vazia")
    if len(answer) > case.max_answer_chars:
        issues.append("Resposta longa demais para consulta rápida")

    duplicates = duplicate_paragraphs(answer)
    if duplicates:
        issues.append(f"Parágrafos repetidos: {len(duplicates)}")

    return {
        "case": case.id,
        "question": case.question,
        "mode": case.mode,
        "ok": not issues,
        "issues": issues,
        "answer": answer,
        "paths": paths,
        "suggestion": suggest_fix(issues),
    }


def suggest_fix(issues: list[str]) -> str:
    joined = "\n".join(issues).casefold()
    if "fonte esperada ausente" in joined:
        return "Revisar roteamento direto, aliases da entidade ou ranking de busca."
    if "fonte proibida" in joined:
        return "Endurecer filtro player-safe e bloqueio de entidades do mestre."
    if "frase obrigatória ausente" in joined:
        return "Adicionar rota de atributo direto ou melhorar extração de campos/seções."
    if "frase proibida" in joined:
        return "Ajustar prompt/formatação para remover linguagem técnica ou vazamento."
    if "parágrafos repetidos" in joined:
        return "Revisar deduplicação de contexto e pós-processamento da resposta."
    if "longa demais" in joined:
        return "Reduzir limite de resposta ou criar resumo por intenção."
    return "Revisar manualmente o caso no relatório."


def vault_fingerprint(root: Path) -> str:
    hasher = hashlib.sha256()
    ignored_parts = {".git", ".obsidian", "zz_media", ".codex-remote-attachments", "__pycache__", ".venv", "data"}
    for path in sorted(root.rglob("*.md")):
        if any(part in ignored_parts for part in path.parts):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        hasher.update(rel.encode("utf-8", errors="ignore"))
        hasher.update(str(stat.st_mtime_ns).encode("ascii"))
        hasher.update(str(stat.st_size).encode("ascii"))
    return hasher.hexdigest()


def maybe_rebuild_index(
    root: Path,
    base_url: str,
    master_token: str | None,
    *,
    auto_rebuild: bool,
    state_path: Path,
) -> dict[str, Any]:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    current = vault_fingerprint(root)
    previous = None
    if state_path.exists():
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8")).get("fingerprint")
        except Exception:
            previous = None

    changed = current != previous
    result: dict[str, Any] = {"vault_changed": changed, "index_rebuilt": False, "index_result": None}
    if changed and auto_rebuild:
        if not master_token:
            result["index_result"] = "Vault mudou, mas OMNISVERA_MASTER_TOKEN não foi definido."
        else:
            result["index_result"] = request_json(
                f"{base_url}/index/rebuild",
                method="POST",
                token=master_token,
            )
            result["index_rebuilt"] = True
    state_path.write_text(json.dumps({"fingerprint": current, "updated_at": utc_now()}, indent=2), encoding="utf-8")
    return result


def write_report(path: Path, *, summary: dict[str, Any], evaluations: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failures = [item for item in evaluations if not item["ok"]]
    lines = [
        "# Omnisvera Companion — RAG Watchdog",
        "",
        f"- Atualizado em: {summary['updated_at']}",
        f"- Base URL: `{summary['base_url']}`",
        f"- Casos testados: {summary['total_cases']}",
        f"- OK: {summary['ok_cases']}",
        f"- Falhas: {summary['failed_cases']}",
        f"- Vault mudou desde a última execução: {summary['vault_changed']}",
        f"- Índice reconstruído: {summary['index_rebuilt']}",
        "",
        "## Resumo",
        "",
        "| Caso | Modo | Status | Pergunta | Fontes |",
        "|---|---|---|---|---|",
    ]
    for item in evaluations:
        status = "OK" if item["ok"] else "FAIL"
        paths = "<br>".join(item["paths"]) if item["paths"] else "—"
        question = item["question"].replace("|", "\\|")
        lines.append(f"| `{item['case']}` | {item['mode']} | {status} | {question} | {paths} |")

    lines.extend(["", "## Falhas e recomendações", ""])
    if not failures:
        lines.append("Nenhuma falha detectada nos casos atuais.")
    else:
        for item in failures:
            lines.extend(
                [
                    f"### {item['case']}",
                    "",
                    f"- Pergunta: {item['question']}",
                    f"- Recomendação: {item['suggestion']}",
                    "- Problemas:",
                    *[f"  - {issue}" for issue in item["issues"]],
                    "",
                    "Resposta observada:",
                    "",
                    "```text",
                    item["answer"].strip(),
                    "```",
                    "",
                ]
            )

    lines.extend(
        [
            "## Próximos passos",
            "",
            "- Adicionar novos casos sempre que o Sage encontrar uma resposta ruim.",
            "- Manter correções automáticas limitadas a reindexação e diagnóstico.",
            "- Fazer alterações de código do RAG em commits pequenos e rastreáveis.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def run_once(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    cases = read_cases(Path(args.cases).resolve() if args.cases else None)
    player_token = args.player_token or DEFAULT_PLAYER_TOKEN
    master_token = args.master_token or DEFAULT_MASTER_TOKEN
    base_url = args.base_url.rstrip("/")
    state_path = root / "omnisvera-agent" / "backend" / "data" / "rag_watchdog_state.json"

    try:
        rebuild_info = maybe_rebuild_index(
            root,
            base_url,
            master_token,
            auto_rebuild=args.auto_rebuild,
            state_path=state_path,
        )
    except Exception as exc:
        rebuild_info = {"vault_changed": None, "index_rebuilt": False, "index_result": f"Erro ao avaliar índice: {exc}"}

    evaluations: list[dict[str, Any]] = []
    for case in cases:
        try:
            result = ask(base_url, case, player_token=player_token, master_token=master_token)
            evaluations.append(evaluate(case, result))
        except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            evaluations.append(
                {
                    "case": case.id,
                    "question": case.question,
                    "mode": case.mode,
                    "ok": False,
                    "issues": [f"Erro ao consultar app: {exc}"],
                    "answer": "",
                    "paths": [],
                    "suggestion": "Confirmar se backend está no ar, token está definido e Ollama responde.",
                }
            )

    failures = [item for item in evaluations if not item["ok"]]
    summary = {
        "updated_at": utc_now(),
        "base_url": base_url,
        "total_cases": len(evaluations),
        "ok_cases": len(evaluations) - len(failures),
        "failed_cases": len(failures),
        "vault_changed": rebuild_info.get("vault_changed"),
        "index_rebuilt": rebuild_info.get("index_rebuilt"),
        "index_result": rebuild_info.get("index_result"),
    }

    report_path = root / args.write_report
    write_report(report_path, summary=summary, evaluations=evaluations)
    append_jsonl(root / "omnisvera-agent" / "backend" / "data" / "rag_watchdog_runs.jsonl", {"summary": summary, "failures": failures})

    print(f"RAG watchdog: {summary['ok_cases']}/{summary['total_cases']} OK")
    print(f"Relatório: {report_path}")
    if failures:
        print("Falhas:")
        for failure in failures:
            print(f"- {failure['case']}: {'; '.join(failure['issues'])}")
    return 1 if failures and args.strict else 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Roda testes contínuos de qualidade do RAG do Omnisvera Companion.")
    parser.add_argument("--root", default=str(repo_root_from_here()), help="Raiz do vault/repositório.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="URL do backend do Companion.")
    parser.add_argument("--player-token", default=None, help="Token de jogador. Padrão: OMNISVERA_PLAYER_TOKEN.")
    parser.add_argument("--master-token", default=None, help="Token de mestre. Padrão: OMNISVERA_MASTER_TOKEN.")
    parser.add_argument("--cases", default=None, help="Arquivo JSON opcional com casos de regressão.")
    parser.add_argument(
        "--write-report",
        default="Workflow/_audit/App_RAG/RAG_WATCHDOG_REPORT.md",
        help="Relatório Markdown de saída relativo à raiz.",
    )
    parser.add_argument("--auto-rebuild", action="store_true", help="Reconstrói índice se o vault mudar.")
    parser.add_argument("--loop", action="store_true", help="Roda continuamente.")
    parser.add_argument("--interval", type=int, default=300, help="Intervalo em segundos no modo loop.")
    parser.add_argument("--strict", action="store_true", help="Retorna exit code 1 quando houver falhas.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.loop:
        while True:
            run_once(args)
            time.sleep(max(30, args.interval))
    return run_once(args)


if __name__ == "__main__":
    raise SystemExit(main())
