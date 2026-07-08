from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .access import AccessMode, is_player_safe_row
from .ollama_client import chat_with_ollama
from .search import search_notes
from .vault_index import all_notes_for_search, get_note, get_notes_by_ids


SYSTEM_PROMPT = """Você é o Omnisvera Companion, assistente local de consulta do vault.
Regras obrigatórias:
- Use apenas o contexto fornecido.
- Não invente cânone, nomes, itens, eventos, hospitais, sistemas ou poderes.
- Se algo não estiver no contexto, diga que não está no contexto.
- Não repita frases.
- Não copie trechos longos do contexto; sintetize.
- Converta wikilinks como [[Varkh Nimalis]] em texto normal quando isso deixar a resposta mais legível.
- Responda em português brasileiro.
- Seja curto: no máximo 8 linhas, salvo se o usuário pedir detalhe.
- Separe informação pública, informação do mestre e pendências quando isso aparecer no contexto.
- Responda a pergunta primeiro; não responda apenas com nomes de notas.
- Não inclua bibliografia no texto: o aplicativo já mostra as notas usadas separadamente."""


def _plain_wikilinks(text: str) -> str:
    text = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", text)

    def replace_simple(match: re.Match[str]) -> str:
        target = match.group(1)
        return target.split("/")[-1].replace(".md", "")

    return re.sub(r"\[\[([^\]]+)\]\]", replace_simple, text)


def _strip_code_blocks(text: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", text)


def _dedupe_paragraphs(text: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    seen: set[str] = set()
    kept: list[str] = []
    for paragraph in paragraphs:
        key = re.sub(r"\s+", " ", paragraph.lower())
        if key in seen:
            continue
        seen.add(key)
        kept.append(paragraph)
    return "\n\n".join(kept).strip()


def _compact_markdown(content: str, max_chars: int = 850) -> str:
    text = _strip_code_blocks(content)
    text = re.sub(r"!\[\[[^\]]+\]\]", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"## Liga[çc][ãa]o com Quests[\s\S]*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"## Dataview[\s\S]*$", "", text, flags=re.IGNORECASE)
    text = _dedupe_paragraphs(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) <= max_chars:
        return text
    clipped = text[:max_chars].rsplit(".", 1)[0].strip()
    return (clipped or text[:max_chars].strip()) + "..."


def _context_from_notes(
    database_path: Path,
    note_ids: list[int],
    access_mode: AccessMode = "gm",
    max_chars: int = 3200,
) -> str:
    chunks: list[str] = []
    total = 0
    seen_paths: set[str] = set()
    for note_id in note_ids:
        note = get_note(database_path, note_id, access_mode=access_mode)
        if not note or note["path"] in seen_paths:
            continue
        seen_paths.add(note["path"])
        body = _compact_markdown(note["content"])
        chunk = (
            f"## {note['title']}\n"
            f"Caminho: {note['path']}\n"
            f"Tipo: {note.get('type')}\n"
            f"Visibilidade: {note.get('visibility')}\n"
            f"Tags: {', '.join(note.get('tags') or [])}\n\n"
            f"{body}\n"
        )
        if total + len(chunk) > max_chars:
            remaining = max_chars - total
            if remaining > 600:
                chunks.append(chunk[:remaining].rsplit("\n", 1)[0].strip())
            break
        chunks.append(chunk)
        total += len(chunk)
    return "\n---\n".join(chunks)


def _looks_like_rumor_overview(question: str) -> bool:
    lowered = question.lower()
    has_rumor = "rumor" in lowered or "rumores" in lowered
    asks_list = any(term in lowered for term in ("quais", "lista", "liste", "ativos", "ativas", "tem", "existem"))
    return has_rumor and asks_list


def _looks_like_quest_overview(question: str) -> bool:
    lowered = question.lower()
    has_quest = any(term in lowered for term in ("quest", "quests", "missão", "missões", "missao", "missoes"))
    asks_list = any(term in lowered for term in ("quais", "lista", "liste", "ativas", "ativos", "tem", "existem"))
    return has_quest and asks_list


def _frontmatter(row: Any) -> dict[str, Any]:
    try:
        data = json.loads(row["frontmatter"] or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _is_secret(frontmatter: dict[str, Any]) -> bool:
    return frontmatter.get("gm_secret") is True or str(frontmatter.get("spoiler_level", "")).lower() in {
        "medium",
        "heavy",
    }


def _first_useful_sentence(content: str) -> str:
    text = _plain_wikilinks(_strip_code_blocks(content))
    text = re.sub(r"^#.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^##.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[-*] ", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) >= 40:
            return sentence[:260].strip()
    return text[:220].strip()


def _answer_index_overview(
    database_path: Path,
    *,
    folder: str,
    note_type: str,
    label: str,
    access_mode: AccessMode,
) -> dict | None:
    rows = []
    for row in all_notes_for_search(database_path):
        path = row["path"]
        if not path.startswith(folder) or "INDICE_" in path:
            continue
        if row["type"] != note_type:
            continue
        if access_mode == "player" and not is_player_safe_row(row):
            continue
        frontmatter = _frontmatter(row)
        status = str(frontmatter.get("status") or "").lower()
        if status in {"arquivado", "deprecated", "non canon", "non-canon"}:
            continue
        rows.append((row, frontmatter))

    if not rows:
        return None

    rows.sort(key=lambda item: item[0]["path"])
    adjective = "ativas" if label.lower().endswith("ões") or label.lower().endswith("sões") else "ativos"
    lines = [f"{label} {adjective} no vault:"]
    note_ids: list[int] = []
    for row, frontmatter in rows[:10]:
        note_ids.append(row["id"])
        title = frontmatter.get("name") or row["title"]
        status = frontmatter.get("status") or "sem status"
        visibility = frontmatter.get("visibility") or row["visibility"] or "sem visibilidade"
        location = frontmatter.get("location") or frontmatter.get("territory") or ""
        summary = _first_useful_sentence(row["content"])
        secret_marker = " — contém informação de mestre" if _is_secret(frontmatter) else ""
        location_text = f" ({_plain_wikilinks(str(location))})" if location else ""
        lines.append(f"- **{_plain_wikilinks(str(title))}**{location_text}: {summary} _[{status}; {visibility}{secret_marker}]_")

    return {
        "answer": "\n".join(lines),
        "notes_used": get_notes_by_ids(database_path, note_ids, access_mode=access_mode),
        "note_paths": [row["path"] for row, _ in rows[:10]],
        "insufficient_context": False,
        "warning": None,
    }


def _clean_answer(answer: str) -> str:
    answer = _dedupe_paragraphs(answer)
    if len(answer) <= 1800:
        return answer
    clipped = answer[:1800].rsplit(".", 1)[0].strip()
    return (clipped or answer[:1800].strip()) + "..."


async def answer_question(
    database_path: Path,
    ollama_base_url: str,
    ollama_model: str,
    question: str,
    limit: int = 6,
    access_mode: AccessMode = "gm",
) -> dict:
    if _looks_like_rumor_overview(question):
        rumor_answer = _answer_index_overview(
            database_path,
            folder="CAMPANHA/Rumors/",
            note_type="rumor",
            label="Rumores",
            access_mode=access_mode,
        )
        if rumor_answer:
            return rumor_answer

    if _looks_like_quest_overview(question):
        quest_answer = _answer_index_overview(
            database_path,
            folder="CAMPANHA/Quests/",
            note_type="quest",
            label="Missões",
            access_mode=access_mode,
        )
        if quest_answer:
            return quest_answer

    results = search_notes(database_path, question, limit=limit, access_mode=access_mode)
    operational_results = [
        item
        for item in results
        if not item["path"].startswith("Workflow/")
        and not item["path"].startswith("Templates/")
        and not item["path"].startswith("omnisvera-agent/")
        and "INDICE_" not in item["path"]
    ]
    if operational_results:
        results = operational_results
    note_ids = list(dict.fromkeys(item["id"] for item in results))
    notes_used = get_notes_by_ids(database_path, note_ids, access_mode=access_mode)
    context = _context_from_notes(database_path, note_ids, access_mode=access_mode)
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
Evite repetir a mesma informação.
Comece com a resposta direta em 2 a 6 frases ou bullets.
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
        "answer": _clean_answer(answer),
        "notes_used": notes_used,
        "note_paths": [note["path"] for note in notes_used],
        "insufficient_context": insufficient,
        "warning": warning,
    }
