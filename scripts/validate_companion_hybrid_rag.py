from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "omnisvera-agent" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.config import get_settings  # noqa: E402
from app.hybrid_retrieval import hybrid_search  # noqa: E402
from app.rag import _extract_json_object, _validate_grounded_payload, answer_question  # noqa: E402
from app.vault_index import get_note, resolve_note  # noqa: E402


TEST_QUERIES = [
    ("Consulta exata", "Varkh Nimalis"),
    ("Consulta semântica", "quem está usando remédios adulterados?"),
    ("Consulta sobre local", "o que existe em Maré Baixa?"),
    ("Consulta sem evidência", "quem é o imperador secreto de Nimalia?"),
    ("Tentativa de mestre", "o que o Estado da Campanha diz sobre Criadores?"),
]


def _short(value: str, limit: int = 420) -> str:
    value = " ".join(str(value or "").split())
    return value if len(value) <= limit else value[:limit].rstrip() + "..."


def _result_table(results: list[dict[str, Any]]) -> str:
    lines = [
        "| Rank | Arquivo | Tipo | Visibilidade | Exact | Lexical | Semantic | Final | Trecho |",
        "|---:|---|---|---|---:|---:|---:|---:|---|",
    ]
    for index, item in enumerate(results[:8], start=1):
        lines.append(
            "| {rank} | `{path}` | {type} | {visibility} | {exact:.2f} | {lexical:.2f} | {semantic:.4f} | {final:.2f} | {excerpt} |".format(
                rank=index,
                path=item.get("path"),
                type=item.get("type") or "",
                visibility=item.get("visibility") or "",
                exact=float(item.get("exact_score") or 0),
                lexical=float(item.get("lexical_score") or 0),
                semantic=float(item.get("semantic_score") or 0),
                final=float(item.get("final_score") or 0),
                excerpt=_short(item.get("excerpt") or "", 160).replace("|", "\\|"),
            )
        )
    return "\n".join(lines)


async def _run(output: Path, include_chat: bool) -> None:
    settings = get_settings()
    output.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "# Validação — Hybrid RAG do Omnisvera Companion",
        "",
        "## Configuração",
        "",
        f"- RAG mode: `{settings.rag_mode}`",
        f"- Modelo principal: `{settings.ollama_model}`",
        f"- Modelo de embeddings: `{settings.embedding_model}`",
        f"- Índice semântico: `{settings.semantic_index_path}`",
        "",
    ]

    for label, query in TEST_QUERIES:
        results = await hybrid_search(
            settings.database_path,
            query=query,
            ollama_base_url=settings.ollama_base_url,
            embedding_model=settings.embedding_model,
            semantic_index_path=settings.semantic_index_path,
            access_mode="player",
            rag_mode="hybrid",
            limit=8,
        )
        lines.extend(
            [
                f"## {label}",
                "",
                f"- Pergunta: `{query}`",
                f"- Resultados recuperados: {len(results)}",
                "",
                _result_table(results),
                "",
            ]
        )
        blocked = [item for item in results if item.get("path") == "CAMPANHA/ESTADO_DA_CAMPANHA.md"]
        if "mestre" in label.lower():
            lines.append(f"- Checagem player-safe: {'PASS' if not blocked else 'FAIL'}")
            lines.append("")

        if include_chat and label in {"Consulta semântica", "Consulta sem evidência"}:
            response = await answer_question(
                settings.database_path,
                settings.ollama_base_url,
                settings.ollama_model,
                query,
                access_mode="player",
                embedding_model=settings.embedding_model,
                semantic_index_path=settings.semantic_index_path,
                rag_mode="hybrid",
                context_limit=6,
                context_chars=4200,
            )
            lines.extend(
                [
                    "### Resposta estruturada",
                    "",
                    f"- Ollama usado: `{response.get('ollama_used')}`",
                    f"- Retrieval: `{response.get('retrieval_mode')}`",
                    f"- Fontes: {', '.join(f'`{path}`' for path in response.get('note_paths', [])) or '(nenhuma)'}",
                    "",
                    "```json",
                    json.dumps(
                        {
                            "fatos_confirmados": response.get("fatos_confirmados", []),
                            "teorias": response.get("teorias", []),
                            "informacoes_insuficientes": response.get("informacoes_insuficientes", []),
                            "resposta_ao_jogador": response.get("answer", ""),
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    "```",
                    "",
                ]
            )

    short_note = resolve_note(settings.database_path, "Maré Baixa", access_mode="player")
    short_ok = False
    if short_note:
        detail = get_note(settings.database_path, short_note["id"], access_mode="player")
        short_ok = bool(detail and detail.get("content") is not None)
    missing_note = resolve_note(settings.database_path, "Lugar Inexistente de Teste", access_mode="player")
    invalid_json = _validate_grounded_payload(_extract_json_object("isto não é json"), {"Characters/Individual/Varkh Nimalis.md"})

    lines.extend(
        [
            "## Checagens de comportamento",
            "",
            f"- Nota curta/liberada abre: {'PASS' if short_ok else 'FAIL'}",
            f"- Link inexistente retorna desconhecido: {'PASS' if missing_note is None else 'FAIL'}",
            f"- JSON inválido cai em fallback: {'PASS' if invalid_json is None else 'FAIL'}",
            "",
            "## Observações",
            "",
            "- Este relatório roda em modo jogador e não registra conteúdo de mestre no contexto.",
            "- Scores técnicos ficam apenas neste relatório de validação, não aparecem para jogadores no app.",
            "- Se o Ollama estiver indisponível, o backend deve manter fallback seguro.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Relatório gerado em {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida a busca híbrida e respostas fundamentadas do Omnisvera Companion.")
    parser.add_argument(
        "--output",
        default="Workflow/_audit/App_RAG/HYBRID_RAG_VALIDATION.md",
        help="Caminho do relatório Markdown.",
    )
    parser.add_argument(
        "--no-chat",
        action="store_true",
        help="Pula chamadas completas ao modelo de chat e valida apenas recuperação.",
    )
    args = parser.parse_args()
    asyncio.run(_run(ROOT / args.output, include_chat=not args.no_chat))


if __name__ == "__main__":
    main()

