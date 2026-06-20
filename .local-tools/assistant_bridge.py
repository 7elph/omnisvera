from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import ollama

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / ".local-index" / "vault.jsonl"
PROPOSALS = ROOT / ".local-proposals"
HANDOFF = ROOT / "Workflow" / "ASSISTANT_HANDOFF.md"
CANON = ROOT / "Workflow" / "CANON.md"
MIGRATION = ROOT / "Workflow" / "MIGRATION_LEDGER.md"


def cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return (result.stdout or result.stderr).strip()


def semantic_context(query: str, limit: int = 8) -> list[dict]:
    if not INDEX.exists():
        raise RuntimeError("Índice ausente. Execute vault_tools.py index.")
    query_vector = ollama.embed(model="nomic-embed-text", input=query)["embeddings"][0]
    rows = []
    with INDEX.open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            embedding = item.pop("embedding")
            item["score"] = cosine(query_vector, embedding)
            rows.append(item)
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows[:limit]


def shared_state() -> str:
    sections = []
    for path in (HANDOFF, MIGRATION, CANON):
        sections.append(f"\n===== {path.name} =====\n{path.read_text(encoding='utf-8-sig')}")
    return "\n".join(sections)


def status() -> str:
    return "\n".join(
        [
            "# Estado do assistente",
            f"Branch: {git_output('branch', '--show-current')}",
            f"Último commit: {git_output('log', '-1', '--oneline')}",
            "Mudanças locais:",
            git_output("status", "--short") or "(nenhuma)",
            "",
            HANDOFF.read_text(encoding="utf-8-sig"),
        ]
    )


def read_sources(paths: list[str]) -> str:
    sections = []
    for raw_path in paths:
        path = (ROOT / raw_path).resolve()
        if ROOT not in path.parents or not path.is_file():
            raise ValueError(f"Fonte inválida: {raw_path}")
        sections.append(
            f"\n===== FONTE: {path.relative_to(ROOT)} =====\n"
            f"{path.read_text(encoding='utf-8-sig', errors='replace')}"
        )
    return "\n".join(sections)


def build_prompt(task: str, evidence: str) -> str:
    state = shared_state()
    return f"""
Você é a assistente local de continuidade do vault Omnisvera.
Use somente o estado compartilhado e as evidências abaixo.
Não invente cânone. Indique conflitos e lacunas. Cite os caminhos das fontes.
Não sugira que uma proposta já foi aplicada.
Se as fontes não sustentarem uma conclusão, escreva "fontes insuficientes".

TAREFA:
{task}

ESTADO COMPARTILHADO:
{state[:24000]}

EVIDÊNCIAS:
{evidence}
""".strip()


def ask(task: str, sources: list[str]) -> str:
    if not sources:
        raise ValueError("Informe ao menos uma fonte explícita.")
    evidence = read_sources(sources)
    response = ollama.generate(
        model="omnisvera-local",
        prompt=build_prompt(task, evidence),
        options={"num_predict": 700, "temperature": 0.1},
    )
    return response["response"].strip()


def propose(task: str, sources: list[str]) -> Path:
    answer = ask(
        f"Prepare uma proposta revisável para a tarefa a seguir. "
        f"Separe fatos, conflitos, arquivos afetados e alterações sugeridas. {task}",
        sources,
    )
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", task.casefold()).strip("-")[:60] or "proposta"
    path = PROPOSALS / f"{stamp}-{slug}.md"
    path.write_text(
        f"# Proposta local\n\n**Tarefa:** {task}\n\n"
        f"**Fontes:** {', '.join(sources)}\n\n{answer}\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Ponte entre Codex e Ollama para Omnisvera")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    ask_parser = sub.add_parser("ask")
    ask_parser.add_argument("task")
    ask_parser.add_argument("--file", action="append", required=True, dest="files")
    propose_parser = sub.add_parser("propose")
    propose_parser.add_argument("task")
    propose_parser.add_argument("--file", action="append", required=True, dest="files")
    args = parser.parse_args()

    if args.command == "status":
        print(status())
    elif args.command == "ask":
        print(ask(args.task, args.files))
    else:
        print(propose(args.task, args.files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
