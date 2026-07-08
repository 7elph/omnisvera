from __future__ import annotations

from pathlib import Path

from .ollama_client import chat_with_ollama
from .search import search_notes
from .vault_index import get_note, get_notes_by_ids


SYSTEM_PROMPT = """Você é o Omnisvera Companion, assistente local de consulta do vault.
Regras obrigatórias:
- Use apenas o contexto fornecido.
- Não invente cânone, nomes, itens, eventos, hospitais, sistemas ou poderes.
- Se algo não estiver no contexto, diga que não está no contexto.
- Não repita frases.
- Não copie trechos longos do contexto; sintetize.
- Responda em português brasileiro.
- Seja curto: no máximo 8 linhas, salvo se o usuário pedir detalhe.
- Separe informação pública, informação do mestre e pendências quando isso aparecer no contexto.
- Responda a pergunta primeiro; não responda apenas com nomes de notas.
- Não inclua bibliografia no texto: o aplicativo já mostra as notas usadas separadamente."""


def _context_from_notes(database_path: Path, note_ids: list[int], max_chars: int = 3000) -> str:
    chunks: list[str] = []
    total = 0
    for note_id in note_ids:
        note = get_note(database_path, note_id)
        if not note:
            continue
        chunk = (
            f"## {note['title']}\n"
            f"Caminho: {note['path']}\n"
            f"Tipo: {note.get('type')}\n"
            f"Visibilidade: {note.get('visibility')}\n\n"
            f"{note['content']}\n"
        )
        if total + len(chunk) > max_chars:
            remaining = max_chars - total
            if remaining > 500:
                chunks.append(chunk[:remaining])
            break
        chunks.append(chunk)
        total += len(chunk)
    return "\n---\n".join(chunks)


async def answer_question(
    database_path: Path,
    ollama_base_url: str,
    ollama_model: str,
    question: str,
    limit: int = 6,
) -> dict:
    results = search_notes(database_path, question, limit=limit)
    operational_results = [
        item
        for item in results
        if not item["path"].startswith("Workflow/")
        and not item["path"].startswith("Templates/")
        and not item["path"].startswith("omnisvera-agent/")
    ]
    if operational_results:
        results = operational_results
    note_ids = [item["id"] for item in results]
    notes_used = get_notes_by_ids(database_path, note_ids)
    context = _context_from_notes(database_path, note_ids)
    insufficient = len(notes_used) == 0 or len(context.strip()) < 300
    warning = None
    if insufficient:
        warning = "Contexto insuficiente: a resposta pode ser apenas orientação geral."

    user_prompt = f"""Pergunta do usuário:
{question}

Contexto encontrado no vault:
{context if context else '(nenhum contexto relevante encontrado)'}

Responda usando o contexto acima.
Não use conhecimento externo.
Se responder com fatos, eles precisam estar no contexto.
Faça síntese, não transcrição.
Comece com a resposta direta em 2 a 6 frases.
Se houver informação pública e segredo do mestre misturados no contexto, separe em linhas curtas."""

    answer = await chat_with_ollama(
        ollama_base_url,
        ollama_model,
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return {
        "answer": answer,
        "notes_used": notes_used,
        "note_paths": [note["path"] for note in notes_used],
        "insufficient_context": insufficient,
        "warning": warning,
    }
