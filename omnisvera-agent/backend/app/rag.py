from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .access import AccessMode, is_player_safe_row, normalize_text, sanitize_player_text
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
    lowered = normalize_text(question)
    has_rumor = "rumor" in lowered or "rumores" in lowered
    asks_list = any(term in lowered for term in ("quais", "lista", "liste", "ativos", "ativas", "tem", "existem"))
    return has_rumor and asks_list


def _looks_like_quest_overview(question: str) -> bool:
    lowered = normalize_text(question)
    has_quest = any(term in lowered for term in ("quest", "quests", "missao", "missoes"))
    asks_list = any(term in lowered for term in ("quais", "lista", "liste", "ativas", "ativos", "tem", "existem"))
    return has_quest and asks_list


def _looks_like_player_character_overview(question: str) -> bool:
    lowered = normalize_text(question)
    has_character = any(term in lowered for term in ("personagens", "jogadores", "grupo", "party"))
    asks_list = any(term in lowered for term in ("quem", "quais", "lista", "liste", "sao", "são"))
    return has_character and asks_list


def _looks_like_campaign_recap(question: str) -> bool:
    lowered = normalize_text(question)
    has_recap = any(term in lowered for term in ("aconteceu", "ate agora", "resumo", "recap", "diario", "historia"))
    asks_campaign = any(term in lowered for term in ("campanha", "sessao", "historia", "agora")) or "ate agora" in lowered
    return has_recap and asks_campaign


def _direct_entity_target(question: str) -> tuple[str, str] | None:
    normalized = normalize_text(question)
    candidates: list[tuple[str, str]] = []
    for prefix in ("o que sabemos sobre", "o que se sabe sobre", "me fala sobre", "fale sobre", "resuma", "resume"):
        if normalized.startswith(prefix + " "):
            candidates.append((normalized.removeprefix(prefix).strip(), "about"))
    for prefix in ("onde fica", "onde esta", "onde esta localizado", "onde fica localizado"):
        if normalized.startswith(prefix + " "):
            candidates.append((normalized.removeprefix(prefix).strip(), "where"))
    if normalized.startswith("quem "):
        target = re.sub(r"^quem\s+", "", normalized).strip()
        target = re.sub(r"^(e|eh|foi|sao|sao os|e a|e o|\?)\s*", "", target).strip()
        candidates.append((target, "who"))
    if normalized.startswith("o que ") or normalized.startswith("que "):
        target = re.sub(r"^(o que|que)\s+", "", normalized).strip()
        target = re.sub(r"^(e|eh|\?)\s*", "", target).strip()
        candidates.append((target, "what"))
    if normalized.startswith("qual "):
        target = re.sub(r"^qual\s+(?:e|eh|foi)?\s*", "", normalized).strip()
        candidates.append((target, "what"))

    for target, kind in candidates:
        target = re.sub(r"^(o|a|os|as|um|uma)\s+", "", target).strip(" ?.!")
        if len(target) >= 3:
            return target, kind
    return None


def _basename(path: str) -> str:
    return Path(path).stem


def _row_lookup(row: Any) -> str:
    aliases = ""
    try:
        aliases = " ".join(json.loads(row["aliases"] or "[]"))
    except Exception:
        aliases = ""
    return normalize_text(f"{row['title']} {_basename(row['path'])} {aliases}")


def _without_initial_article(value: str) -> str:
    return re.sub(r"^(o|a|os|as|um|uma)\s+", "", normalize_text(value)).strip()


def _find_exact_row(database_path: Path, target: str, access_mode: AccessMode | None = None) -> Any | None:
    target_norm = normalize_text(target)
    target_without_article = _without_initial_article(target)
    if not target_norm:
        return None
    matches: list[Any] = []
    for row in all_notes_for_search(database_path):
        candidates = {normalize_text(row["title"]), normalize_text(_basename(row["path"]))}
        try:
            candidates.update(normalize_text(alias) for alias in json.loads(row["aliases"] or "[]"))
        except Exception:
            pass
        candidates_without_article = {_without_initial_article(candidate) for candidate in candidates}
        if target_norm in candidates or target_without_article in candidates_without_article:
            matches.append(row)
    if not matches:
        return None

    def rank(row: Any) -> tuple[int, str]:
        score = 0
        path = row["path"]
        note_type = normalize_text(row["type"])
        if access_mode == "player" and is_player_safe_row(row):
            score += 200
        if path.startswith(("Workflow/", "Templates/", "omnisvera-agent/")):
            score -= 120
        if note_type in {"character", "location", "territory", "faction", "item", "quest", "rumor", "story"}:
            score += 30
        if normalize_text(row["title"]) == target_norm:
            score += 20
        if normalize_text(_basename(path)) == target_norm:
            score += 10
        return (score, path)

    matches.sort(key=rank, reverse=True)
    return matches[0]


def _blocked_player_entity_answer(target: str) -> dict:
    clean_target = target.strip().title()
    return {
        "answer": (
            f"A nota principal de **{clean_target}** existe no vault, "
            "mas ainda não está liberada para o modo jogador. "
            "Para evitar spoiler, não vou completar a resposta usando nota lateral, rumor ou referência indireta."
        ),
        "notes_used": [],
        "note_paths": [],
        "insufficient_context": False,
        "warning": "Nota principal não liberada no modo jogador.",
        "suggested_questions": [
            "Quais rumores estão ativos?",
            "Quais missões estão ativas?",
            "O que aconteceu até agora?",
        ],
    }


def _entity_candidate_score(item: dict, target: str, kind: str) -> int:
    target_norm = normalize_text(target)
    title_norm = normalize_text(item.get("title") or "")
    path_norm = normalize_text(_basename(item.get("path") or ""))
    tags_norm = normalize_text(" ".join(item.get("tags") or []))
    note_type = normalize_text(item.get("type") or "")

    score = int(item.get("score") or 0)
    if title_norm == target_norm or path_norm == target_norm:
        score += 120
    elif target_norm in title_norm or target_norm in path_norm:
        score += 80
    if target_norm in tags_norm:
        score += 10

    if kind == "who":
        if note_type == "character":
            score += 90
        elif note_type in {"faction", "religion"}:
            score += 20
        elif note_type == "item":
            score -= 45
    elif kind == "what":
        if note_type in {"item", "location", "territory", "lore", "race", "class", "quest", "rumor"}:
            score += 45
    elif kind == "where":
        if note_type in {"location", "territory", "map"}:
            score += 90
        elif note_type == "character":
            score += 20
        else:
            score -= 60
    elif kind == "about":
        if note_type in {"character", "location", "territory", "faction", "item", "quest", "rumor"}:
            score += 35

    return score


def _find_direct_entity_note(
    database_path: Path,
    question: str,
    access_mode: AccessMode,
) -> dict | None:
    extracted = _direct_entity_target(question)
    if not extracted:
        return None

    target, kind = extracted
    results = search_notes(database_path, target, limit=16, access_mode=access_mode)
    if not results:
        return None

    results.sort(key=lambda item: _entity_candidate_score(item, target, kind), reverse=True)
    best = results[0]
    target_norm = normalize_text(target)
    best_lookup = normalize_text(f"{best.get('title', '')} {_basename(best.get('path', ''))} {' '.join(best.get('aliases') or [])}")
    best_entity_score = _entity_candidate_score(best, target, kind)
    best_type = normalize_text(best.get("type"))
    if kind in {"who", "what", "where"} and target_norm not in best_lookup and best_entity_score < 40:
        return None
    if kind == "where" and best_type not in {"location", "territory", "map", "character", "faction"}:
        return None

    return get_note(database_path, best["id"], access_mode=access_mode)


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
    text = _strip_code_blocks(content)
    text = re.sub(r"!\[\[[^\]]+\]\]", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = _plain_wikilinks(text)
    text = re.sub(r"^#.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^##.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s*\[![^\n]+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s*!\S.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s*[_\"“].*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\*\*[^*:\n]+:\*\*.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[-*] ", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) >= 40:
            return sentence[:260].strip()
    return text[:220].strip()


def _labeled_fields(content: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    content = _plain_wikilinks(_strip_code_blocks(content))
    content = re.sub(r"<h[1-6][^>]*>([\s\S]*?)</h[1-6]>", r"\1", content, flags=re.IGNORECASE)
    content = re.sub(r"<[^>]+>", "", content)
    for line in content.splitlines():
        match = re.match(r"^\s*\*\*([^*:\n]+):\*\*\s*(.+?)\s*$", line)
        if not match:
            continue
        key = normalize_text(match.group(1))
        value = re.sub(r"\s+", " ", match.group(2)).strip()
        if value and key not in fields:
            fields[key] = value
    return fields


def _note_kind_label(note_type: str | None) -> str:
    labels = {
        "character": "personagem",
        "faction": "facção",
        "location": "local",
        "territory": "território",
        "item": "item",
        "lore": "lore",
        "race": "raça",
        "class": "classe",
        "quest": "missão",
        "rumor": "rumor",
        "story": "capítulo",
    }
    return labels.get(normalize_text(note_type), "nota")


def _clean_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(_clean_value(item) for item in value if _clean_value(item))
    return _plain_wikilinks(str(value)).strip()


def _short_note_title(value: Any) -> str:
    title = _plain_wikilinks(str(value or "")).strip()
    if "—" in title:
        title = title.split("—", 1)[0].strip()
    if " - " in title and title[:2].isdigit():
        title = title.split(" - ", 1)[-1].strip()
    if title.isupper() and any(char.isalpha() for char in title):
        title = " ".join(word[:1].upper() + word[1:].lower() for word in title.split())
    return title


def _append_if(lines: list[str], label: str, value: Any) -> None:
    cleaned = _clean_value(value)
    if cleaned:
        lines.append(f"{label}: {cleaned}.")


def _direct_entity_answer(note: dict, question: str, access_mode: AccessMode) -> dict:
    frontmatter = note.get("frontmatter") or {}
    content = sanitize_player_text(note["content"]) if access_mode == "player" else note["content"]
    fields = _labeled_fields(content)
    title = _plain_wikilinks(str(note["title"]))
    note_type = normalize_text(note.get("type"))
    tags = [normalize_text(tag) for tag in note.get("tags") or []]
    query_kind = (_direct_entity_target(question) or ("", "about"))[1]
    lines: list[str] = []

    if query_kind == "where":
        if note_type in {"location", "territory", "map"}:
            lines.append(f"{title} é {_note_kind_label(note.get('type'))} em Omnisvera.")
            _append_if(lines, "Território", frontmatter.get("territory"))
            _append_if(lines, "Localização superior", frontmatter.get("parent_location") or frontmatter.get("location"))
            summary = _first_useful_sentence(content)
            if summary:
                lines.append(summary)
        else:
            location = fields.get("localizacao atual") or frontmatter.get("location")
            territory = fields.get("territorio") or frontmatter.get("territory")
            lines.append(f"{title} está ligado a {_clean_value(location or territory) or 'local não definido no contexto liberado'}.")
        return {
            "answer": "\n".join(f"- {line}" for line in lines[:5]),
            "notes_used": [note],
            "note_paths": [note["path"]],
            "insufficient_context": False,
            "warning": None,
            "suggested_questions": _suggested_questions_for_notes(question, [note], access_mode),
        }

    if note_type == "character":
        subtype = normalize_text(frontmatter.get("subtype"))
        role = normalize_text(frontmatter.get("role"))
        is_player = subtype == "player_character" or role == "player" or "jogador" in tags
        intro = f"{title} é {'um personagem jogador' if is_player else 'um personagem'} de Omnisvera."
        lines.append(intro)

        details: list[str] = []
        race = fields.get("raca") or frontmatter.get("race")
        char_class = fields.get("classe") or frontmatter.get("class")
        if race:
            details.append(f"raça: {_plain_wikilinks(str(race))}")
        if char_class:
            details.append(f"classe: {_plain_wikilinks(str(char_class))}")
        if details:
            lines.append("No que está liberado aos jogadores, " + "; ".join(details) + ".")

        reputation = fields.get("reputacao publica")
        location = fields.get("localizacao atual") or frontmatter.get("location")
        faction = fields.get("afiliacao") or frontmatter.get("faction")
        if reputation:
            lines.append(f"É conhecido publicamente como {reputation}.")
        if location or faction:
            parts = []
            if location:
                parts.append(f"está ligado a {_plain_wikilinks(str(location))}")
            if faction:
                parts.append(f"tem ligação com {_plain_wikilinks(str(faction))}")
            lines.append("Atualmente, " + " e ".join(parts) + ".")

        summary = _first_useful_sentence(content)
        if len(lines) < 3 and summary and not any(normalize_text(summary) in normalize_text(line) for line in lines):
            lines.append(summary)
    else:
        kind_label = _note_kind_label(note.get("type"))
        summary = _first_useful_sentence(content)
        lines.append(f"{title} é uma nota de {kind_label} em Omnisvera.")
        if note_type == "item":
            item_type = frontmatter.get("item_type") or frontmatter.get("item_category")
            owner = frontmatter.get("owner")
            if item_type or owner:
                details = []
                if item_type:
                    details.append(f"tipo: {_plain_wikilinks(str(item_type))}")
                if owner:
                    details.append(f"portador: {_plain_wikilinks(str(owner))}")
                lines.append("; ".join(details) + ".")
        elif note_type in {"location", "territory"}:
            _append_if(lines, "Território", frontmatter.get("territory"))
            _append_if(lines, "Localização superior", frontmatter.get("parent_location") or frontmatter.get("location"))
            _append_if(lines, "Função", frontmatter.get("role") or frontmatter.get("subtype"))
        elif note_type == "faction":
            _append_if(lines, "Status", frontmatter.get("status") or frontmatter.get("campaign_status"))
            _append_if(lines, "Atuação", frontmatter.get("location") or frontmatter.get("territory"))
            _append_if(lines, "Liderança", frontmatter.get("leader"))
        elif note_type in {"race", "class"}:
            _append_if(lines, "Status", frontmatter.get("status") or frontmatter.get("work_status"))
            _append_if(lines, "Sistema", frontmatter.get("ruleset") or frontmatter.get("source_system"))
        elif note_type in {"quest", "rumor"}:
            _append_if(lines, "Status", frontmatter.get("quest_status") or frontmatter.get("status"))
            _append_if(lines, "Local", frontmatter.get("location") or frontmatter.get("territory"))
        if summary:
            lines.append(summary)

    answer = "\n".join(f"- {line}" for line in lines[:5])
    return {
        "answer": answer,
        "notes_used": [note],
        "note_paths": [note["path"]],
        "insufficient_context": False,
        "warning": None,
        "suggested_questions": _suggested_questions_for_notes(question, [note], access_mode),
    }


def _answer_player_characters(database_path: Path, access_mode: AccessMode) -> dict | None:
    rows = []
    for row in all_notes_for_search(database_path):
        if row["type"] != "character":
            continue
        if access_mode == "player" and not is_player_safe_row(row):
            continue
        frontmatter = _frontmatter(row)
        tags = normalize_text(row["tags"])
        subtype = normalize_text(frontmatter.get("subtype"))
        role = normalize_text(frontmatter.get("role"))
        if subtype != "player_character" and role != "player" and "jogador" not in tags:
            continue
        rows.append((row, frontmatter))

    if not rows:
        return None

    priority = ("vezemir", "varkh", "raziel", "morthak", "mira")

    def rank(item: tuple[Any, dict]) -> tuple[int, str]:
        row, _frontmatter = item
        lookup = normalize_text(f"{row['path']} {row['title']}")
        for index, name in enumerate(priority):
            if name in lookup:
                return (index, lookup)
        return (len(priority), lookup)

    rows.sort(key=rank)
    lines = ["Personagens jogadores liberados no vault:"]
    note_ids: list[int] = []
    for row, frontmatter in rows[:8]:
        note = get_note(database_path, row["id"], access_mode=access_mode)
        if not note:
            continue
        note_ids.append(row["id"])
        content = sanitize_player_text(note["content"]) if access_mode == "player" else note["content"]
        fields = _labeled_fields(content)
        race = _clean_value(fields.get("raca") or frontmatter.get("race"))
        char_class = _clean_value(fields.get("classe") or frontmatter.get("class"))
        role_text = "; ".join(part for part in (race, char_class) if part)
        suffix = f" — {role_text}" if role_text else ""
        lines.append(f"- **{_plain_wikilinks(row['title'])}**{suffix}.")

    return {
        "answer": "\n".join(lines),
        "notes_used": get_notes_by_ids(database_path, note_ids, access_mode=access_mode),
        "note_paths": [row["path"] for row, _frontmatter in rows[:8]],
        "insufficient_context": False,
        "warning": None,
        "suggested_questions": [
            "O que aconteceu até agora?",
            "Quais missões estão ativas?",
            "Quais rumores estão ativos?",
        ],
    }


def _answer_campaign_recap(database_path: Path, access_mode: AccessMode) -> dict | None:
    wanted_paths = [
        "EARTHROPO/01 - Ecos do Mundo Perdido.md",
        "CAMPANHA/Quests/02 - Investigar Remédios Falsos de Maré Baixa.md",
        "CAMPANHA/Quests/03 - Explorar a Passagem Sob a Estrada.md",
        "CAMPANHA/Rumors/02 - Remédios Falsos da Maré Baixa.md",
        "CAMPANHA/Rumors/03 - Caravana Acidentada na Estrada de Avenor.md",
    ]
    rows_by_path = {row["path"]: row for row in all_notes_for_search(database_path)}
    notes: list[dict] = []
    for path in wanted_paths:
        row = rows_by_path.get(path)
        if not row:
            continue
        if access_mode == "player" and not is_player_safe_row(row):
            continue
        note = get_note(database_path, row["id"], access_mode=access_mode)
        if note:
            notes.append(note)

    if not notes:
        return None

    lines = ["Resumo público liberado até agora:"]
    chapter = next((note for note in notes if normalize_text(note.get("type")) == "story"), None)
    if chapter:
        summary = _first_useful_sentence(chapter["content"])
        if summary:
            lines.append(f"- **{chapter['title']}**: {summary}")

    quests = [note for note in notes if normalize_text(note.get("type")) == "quest"]
    if quests:
        quest_titles = ", ".join(f"**{note['title']}**" for note in quests[:3])
        lines.append(f"- Missões em aberto: {quest_titles}.")

    rumors = [note for note in notes if normalize_text(note.get("type")) == "rumor"]
    if rumors:
        rumor_summaries = []
        for note in rumors[:2]:
            summary = _first_useful_sentence(note["content"])
            if summary:
                rumor_summaries.append(summary)
        if rumor_summaries:
            lines.append("- Pistas públicas: " + " ".join(rumor_summaries[:2]))

    lines.append("- Mistérios maiores continuam não confirmados no modo jogador.")
    return {
        "answer": "\n".join(lines),
        "notes_used": notes,
        "note_paths": [note["path"] for note in notes],
        "insufficient_context": False,
        "warning": None,
        "suggested_questions": _suggested_questions_for_notes("O que aconteceu até agora?", notes, access_mode),
    }


def _type_hints_for_question(question: str) -> set[str]:
    lowered = normalize_text(question)
    hints: set[str] = set()
    if any(term in lowered for term in ("quem", "personagem", "npc", "jogador")):
        hints.add("character")
    if any(term in lowered for term in ("onde", "lugar", "local", "cidade", "bairro", "reino", "mapa")):
        hints.update({"location", "territory", "map"})
    if any(term in lowered for term in ("faccao", "facao", "guilda", "coroa", "guarda", "culto")):
        hints.add("faction")
    if any(term in lowered for term in ("item", "arma", "escudo", "medalhao", "remedio", "frasco")):
        hints.add("item")
    if any(term in lowered for term in ("classe", "raca", "mecanica", "regra")):
        hints.update({"class", "race"})
    if any(term in lowered for term in ("missao", "quest", "objetivo")):
        hints.add("quest")
    if any(term in lowered for term in ("rumor", "boato", "pista")):
        hints.add("rumor")
    if any(term in lowered for term in ("capitulo", "sessao", "aconteceu", "historia")):
        hints.add("story")
    return hints


def _rerank_results(question: str, results: list[dict]) -> list[dict]:
    hints = _type_hints_for_question(question)
    if not results:
        return []

    def rank(item: dict) -> tuple[int, int, str]:
        score = int(item.get("score") or 0)
        note_type = normalize_text(item.get("type"))
        path = item.get("path") or ""
        if hints and note_type in hints:
            score += 30
        if path.startswith(("Workflow/", "Templates/", "omnisvera-agent/")) or "INDICE_" in path:
            score -= 80
        if note_type == "index":
            score -= 80
        if note_type in {"quest", "rumor", "story", "character", "location", "faction", "item"}:
            score += 5
        return (score, -len(path), item.get("title") or "")

    return sorted(results, key=rank, reverse=True)


def _suggested_questions_for_notes(question: str, notes: list[dict], access_mode: AccessMode) -> list[str]:
    suggestions: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        if value not in seen:
            seen.add(value)
            suggestions.append(value)

    lowered = normalize_text(question)
    for note in notes[:4]:
        title = _short_note_title(note.get("title"))
        note_type = normalize_text(note.get("type"))
        if not title:
            continue
        if note_type == "character":
            add(f"O que sabemos sobre {title}?")
            add(f"Com quem {title} está ligado?")
        elif note_type in {"location", "territory"}:
            add(f"O que sabemos sobre {title}?")
            add(f"Quem está ligado a {title}?")
        elif note_type == "faction":
            add(f"O que a facção {title} quer?")
            add(f"Quem está ligado a {title}?")
        elif note_type == "item":
            add(f"O que é {title}?")
            add(f"Quem está ligado a {title}?")
        elif note_type == "quest":
            add("Quais missões estão ativas?")
            add(f"O que sabemos sobre {title}?")
        elif note_type == "rumor":
            add("Quais rumores estão ativos?")
            add(f"O que sabemos sobre {title}?")
        elif note_type == "story":
            add("O que aconteceu até agora?")

    if "rumor" not in lowered:
        add("Quais rumores estão ativos?")
    if "miss" not in lowered and "quest" not in lowered:
        add("Quais missões estão ativas?")
    if access_mode == "player":
        add("Quem são os personagens jogadores?")
    else:
        add("O que precisa preparar para a próxima sessão?")

    return suggestions[:5]


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
        title = frontmatter.get("name") or row["title"]
        status = frontmatter.get("status") or "sem status"
        visibility = frontmatter.get("visibility") or row["visibility"] or "sem visibilidade"
        location = frontmatter.get("location") or frontmatter.get("territory") or ""
        content = sanitize_player_text(row["content"]) if access_mode == "player" else row["content"]
        summary = _first_useful_sentence(content)
        if access_mode == "player" and not summary:
            continue
        note_ids.append(row["id"])
        secret_marker = "" if access_mode == "player" else (" — contém informação de mestre" if _is_secret(frontmatter) else "")
        location_text = f" ({_plain_wikilinks(str(location))})" if location else ""
        lines.append(f"- **{_plain_wikilinks(str(title))}**{location_text}: {summary} _[{status}; {visibility}{secret_marker}]_")

    return {
        "answer": "\n".join(lines),
        "notes_used": get_notes_by_ids(database_path, note_ids, access_mode=access_mode),
        "note_paths": [row["path"] for row, _ in rows[:10]],
        "insufficient_context": False,
        "warning": None,
        "suggested_questions": [
            "O que aconteceu até agora?",
            "Quem são os personagens jogadores?",
            "Quais lugares conhecemos?",
        ]
        if access_mode == "player"
        else [
            "O que precisa preparar para a próxima sessão?",
            "Quais pendências existem?",
            "Quais notas precisam revisão?",
        ],
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

    if _looks_like_player_character_overview(question):
        character_answer = _answer_player_characters(database_path, access_mode)
        if character_answer:
            return character_answer

    if _looks_like_campaign_recap(question):
        recap_answer = _answer_campaign_recap(database_path, access_mode)
        if recap_answer:
            return recap_answer

    extracted = _direct_entity_target(question)
    if extracted and access_mode == "player":
        target, _kind = extracted
        exact_row = _find_exact_row(database_path, target, access_mode=access_mode)
        if exact_row is not None and not is_player_safe_row(exact_row):
            return _blocked_player_entity_answer(target)

    direct_note = _find_direct_entity_note(database_path, question, access_mode)
    if direct_note:
        return _direct_entity_answer(direct_note, question, access_mode)

    results = search_notes(database_path, question, limit=max(limit, 12), access_mode=access_mode)
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
    results = _rerank_results(question, results)[: max(3, min(limit, 8))]
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
Considere a primeira nota do contexto como a mais relevante.
Não troque o assunto principal por item, nota ou referência relacionada.
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
        "suggested_questions": _suggested_questions_for_notes(question, notes_used, access_mode),
    }
