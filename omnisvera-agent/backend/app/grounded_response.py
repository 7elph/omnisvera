from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .access import AccessMode, normalize_text, sanitize_player_text


def _plain_wikilinks(text: str) -> str:
    text = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", text)
    return re.sub(
        r"\[\[([^\]]+)\]\]",
        lambda match: match.group(1).split("/")[-1].replace(".md", ""),
        text,
    )


def _dedupe_paragraphs(text: str) -> str:
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
    seen: set[str] = set()
    kept: list[str] = []
    for paragraph in paragraphs:
        key = re.sub(r"\s+", " ", paragraph.casefold())
        if key not in seen:
            seen.add(key)
            kept.append(paragraph)
    return "\n\n".join(kept)


def _clean_answer(answer: str) -> str:
    answer = _dedupe_paragraphs(answer)
    if len(answer) <= 1800:
        return answer
    clipped = answer[:1800].rsplit(".", 1)[0].strip()
    return (clipped or answer[:1800].strip()) + "..."


def _lower_initial(value: Any) -> str:
    cleaned = re.sub(r"\s+", " ", str(value or "")).strip()
    return cleaned[:1].lower() + cleaned[1:] if cleaned else ""


def _context_from_hybrid_results(
    results: list[dict[str, Any]],
    *,
    max_chars: int = 5200,
) -> str:
    chunks: list[str] = []
    total = 0
    for index, result in enumerate(results, start=1):
        excerpt = str(result.get("excerpt") or "").strip()
        if not excerpt:
            continue
        chunk = (
            f"[{index}] Caminho: {result.get('path')}\n"
            f"Título: {result.get('title')}\n"
            f"Tipo: {result.get('type')}\n"
            f"Visibilidade: {result.get('visibility')}\n"
            f"Trecho liberado:\n{excerpt}\n"
        )
        if total + len(chunk) > max_chars:
            remaining = max_chars - total
            if remaining > 450:
                chunks.append(chunk[:remaining].rsplit("\n", 1)[0].strip())
            break
        chunks.append(chunk)
        total += len(chunk)
    return "\n---\n".join(chunks)


def _evidence_by_path(results: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(item.get("path")): str(item.get("excerpt") or "").strip()
        for item in results
        if item.get("path") and str(item.get("excerpt") or "").strip()
    }


def _query_requests_technical_context(question: str) -> bool:
    normalized = normalize_text(question)
    return any(
        term in normalized
        for term in (
            "workflow",
            "template",
            "frontmatter",
            "yaml",
            "dataview",
            "datacards",
            "auditoria",
            "plugin",
        )
    )


def _grounded_fallback() -> dict[str, Any]:
    return {
        "fatos_confirmados": [],
        "teorias": [],
        "informacoes_insuficientes": [
            "Não foi possível produzir uma resposta confiável com as informações disponíveis."
        ],
        "fontes_usadas": [],
        "resposta_ao_jogador": "Não encontrei informações suficientes no que já foi revelado.",
    }


_QUERY_GENERIC_TERMS = {
    "a", "ao", "aos", "as", "como", "conseguir", "da", "das", "de", "do", "dos", "e", "em", "esta",
    "estao", "existe", "fica", "ligado", "lugar", "na", "nas", "no", "nos", "o", "onde", "os", "pode",
    "podem", "qual", "que", "quem", "real", "relacionado", "sobre", "earthropo", "nimalia", "nimalis",
}

_EXTRACTIVE_NOISE_TERMS = (
    "a consulta abaixo",
    "frontmatter",
    "onde pode ser ouvido",
    "pendência",
    "pendencia",
    "template",
    "dataview",
    "datacards",
    "permanece apenas como texto provisório",
)


def _extractive_grounded_payload(question: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    all_query_terms = _grounding_tokens(question)
    query_terms = all_query_terms - _QUERY_GENERIC_TERMS
    if not query_terms:
        query_terms = all_query_terms
    candidates: list[tuple[float, str, str]] = []
    for rank, item in enumerate(results[:6]):
        path = str(item.get("path") or "")
        excerpt = str(item.get("excerpt") or "").strip()
        if not path or not excerpt:
            continue
        result_title = str(item.get("title") or Path(path).stem)
        is_exact_result = float(item.get("exact_score") or 0.0) >= 900.0
        cleaned = re.sub(r"[#>*_]+", " ", excerpt)
        for label in (result_title, Path(path).stem):
            if label:
                cleaned = re.sub(re.escape(label), " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(
            r"\b(?:Gancho Público|Visão Geral|Overview|História|Legado|Status|Objetivo Conhecido)\b[:\s-]*",
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        for sentence in re.split(r"(?<=[.!?])\s+", cleaned):
            sentence = sentence.strip(" -")
            if len(sentence) < 28 or len(sentence) > 360:
                continue
            if any(term in normalize_text(sentence) for term in _EXTRACTIVE_NOISE_TERMS):
                continue
            sentence_terms = _grounding_tokens(sentence)
            overlap = query_terms & sentence_terms
            if not overlap and not is_exact_result:
                continue
            if is_exact_result and not overlap:
                sentence = f"{result_title} {sentence}" if normalize_text(sentence).startswith("e ") else f"{result_title}: {sentence}"
            score = (
                (len(overlap) * 3.0)
                + (len(overlap) / max(1, len(query_terms)))
                + (20.0 if is_exact_result else 0.0)
                - (rank * 0.2)
            )
            candidates.append((score, path, sentence))

    candidates.sort(key=lambda item: item[0], reverse=True)
    facts: list[dict[str, str]] = []
    seen_sentences: set[str] = set()
    best_score = candidates[0][0] if candidates else 0.0
    for score, path, sentence in candidates:
        normalized_sentence = normalize_text(sentence)
        if normalized_sentence in seen_sentences:
            continue
        seen_sentences.add(normalized_sentence)
        evidence = sentence
        sentence = re.sub(r"^\d+\s*[-—]\s*", "", sentence).strip()
        if normalize_text(sentence).startswith("organizacao que"):
            remainder = re.sub(r"^Organiza(?:ção|cao) que\s+", "", sentence, flags=re.IGNORECASE)
            sentence = f"{Path(path).stem} é uma organização que {_lower_initial(remainder)}"
        elif normalize_text(sentence).startswith("foi nessa"):
            sentence = f"{Path(path).stem}: {sentence}"
        facts.append({"fato": sentence, "fonte": path, "evidencia": evidence})
        if len(facts) >= (2 if best_score >= 6.0 and score >= 5.5 else 1):
            break

    if not facts:
        return {
            "fatos_confirmados": [],
            "teorias": [],
            "informacoes_insuficientes": [
                "Ainda não há evidência recuperada suficiente para responder a essa pergunta."
            ],
            "fontes_usadas": [],
            "resposta_ao_jogador": "Ainda não há informação revelada suficiente para confirmar isso.",
        }

    missing: list[str] = []
    best_overlap = len(query_terms & _grounding_tokens(facts[0]["fato"]))
    primary_path = facts[0]["fonte"]
    primary_result = next((item for item in results if item.get("path") == primary_path), {})
    primary_type = normalize_text(primary_result.get("type"))
    asks_for_place = normalize_text(question).startswith(("que lugar", "qual lugar", "onde fica"))
    place_answered = asks_for_place and primary_type in {"location", "territory", "map"}
    if len(query_terms) >= 2 and best_overlap < 2 and best_score < 5.5 and not place_answered:
        missing.append("A relação exata perguntada ainda não aparece de forma explícita nas informações reveladas.")
    return {
        "fatos_confirmados": facts,
        "teorias": [],
        "informacoes_insuficientes": missing,
        "fontes_usadas": [item["fonte"] for item in facts],
        "resposta_ao_jogador": _safe_grounded_answer(facts, [], missing),
    }


def _extract_json_object(text: str) -> dict[str, Any] | None:
    clean = text.strip()
    clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s*```$", "", clean)
    start = clean.find("{")
    end = clean.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(clean[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


_GROUNDING_STOPWORDS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos", "e", "em", "entre",
    "essa", "esse", "esta", "este", "foi", "ha", "mais", "na", "nas", "no", "nos", "o", "os", "ou",
    "para", "pela", "pelas", "pelo", "pelos", "por", "que", "se", "sem", "sua", "suas", "um", "uma",
}


def _grounding_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9']+", normalize_text(value))
        if len(token) > 2 and token not in _GROUNDING_STOPWORDS
    }


def _evidence_is_present(evidence: str, source_text: str) -> bool:
    evidence_norm = re.sub(r"\s+", " ", normalize_text(evidence)).strip()
    source_norm = re.sub(r"\s+", " ", normalize_text(source_text)).strip()
    return len(evidence_norm) >= 12 and evidence_norm in source_norm


def _claim_matches_evidence(claim: str, evidence: str) -> bool:
    claim_tokens = _grounding_tokens(claim)
    evidence_tokens = _grounding_tokens(evidence)
    if not claim_tokens:
        return False
    overlap = claim_tokens & evidence_tokens
    return len(overlap) >= min(2, len(claim_tokens)) and len(overlap) / len(claim_tokens) >= 0.28


def _safe_grounded_answer(facts: list[dict[str, Any]], theories: list[dict[str, Any]], missing: list[str]) -> str:
    def sentence(value: Any) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        return text if not text or text.endswith((".", "!", "?")) else f"{text}."

    fact_sentences = [sentence(item.get("fato")) for item in facts[:3] if sentence(item.get("fato"))]
    natural_facts: list[str] = []
    previous_subject = ""
    for index, fact in enumerate(fact_sentences):
        words = fact.split()
        subject = normalize_text(" ".join(words[:2])) if len(words) >= 2 else ""
        if index == 0:
            natural_facts.append(fact)
        elif subject and subject == previous_subject and len(words) > 2:
            remainder = " ".join(words[2:])
            natural_facts.append(f"Também {_lower_initial(remainder)}")
        else:
            natural_facts.append(f"Além disso, {_lower_initial(fact)}")
        previous_subject = subject

    blocks: list[str] = []
    if natural_facts:
        blocks.append(" ".join(natural_facts))
    if theories:
        theory_text = " ".join(sentence(item.get("teoria")) for item in theories[:2] if sentence(item.get("teoria")))
        if theory_text:
            blocks.append(f"Uma possibilidade é esta: {_lower_initial(theory_text)}")
    if missing:
        missing_text = "; ".join(sentence(item).rstrip(".") for item in missing[:2] if sentence(item))
        if missing_text:
            blocks.append(f"Ainda assim, {_lower_initial(missing_text)}.")
    return "\n\n".join(blocks).strip() or (
        "Isso ainda não foi revelado com segurança. Por enquanto, não há informação confiável suficiente para responder."
    )


def _answer_is_represented(answer: str, facts: list[dict[str, Any]], theories: list[dict[str, Any]], missing: list[str]) -> bool:
    if not facts and not theories:
        normalized_answer = normalize_text(answer)
        return bool(missing) and any(
            term in normalized_answer
            for term in ("nao", "ainda", "insuficiente", "sem confirmacao", "nao foi confirmado")
        )
    support = " ".join(
        [*(str(item["fato"]) for item in facts), *(str(item["teoria"]) for item in theories), *missing]
    )
    if not support.strip():
        return False
    support_tokens = _grounding_tokens(support)
    answer_tokens = _grounding_tokens(answer)
    if not answer_tokens:
        return False
    # Names and numbers are the most dangerous unsupported additions.
    anchor_pattern = r"\b(?:\d+(?:[.,]\d+)?|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç'’.-]{2,})\b"
    answer_anchors = {normalize_text(item) for item in re.findall(anchor_pattern, answer)}
    support_anchors = {normalize_text(item) for item in re.findall(anchor_pattern, support)}
    if answer_anchors and not answer_anchors.issubset(support_anchors):
        return False
    overlap = answer_tokens & support_tokens
    return len(overlap) / len(answer_tokens) >= 0.42


def _validate_grounded_payload(
    data: dict[str, Any] | None,
    allowed_paths: set[str],
    evidence_by_path: dict[str, str] | None = None,
    *,
    strict_evidence: bool = False,
    access_mode: AccessMode = "gm",
) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None

    evidence_map = evidence_by_path or {}

    facts: list[dict[str, str]] = []
    for item in data.get("fatos") or data.get("fatos_confirmados") or []:
        if not isinstance(item, dict):
            continue
        fact = str(item.get("texto") or item.get("fato") or "").strip()
        source = str(item.get("fonte") or "").strip()
        evidence = str(item.get("evidencia") or "").strip()
        if not fact or source not in allowed_paths:
            continue
        if strict_evidence:
            source_text = evidence_map.get(source, "")
            if not _evidence_is_present(evidence, source_text) or not _claim_matches_evidence(fact, evidence):
                continue
        facts.append({"fato": fact, "fonte": source, "evidencia": evidence})

    theories: list[dict[str, Any]] = []
    for item in data.get("teorias") or []:
        if not isinstance(item, dict):
            continue
        theory = str(item.get("texto") or item.get("teoria") or "").strip()
        bases = [
            path
            for path in _coerce_string_list(item.get("fontes") or item.get("base"))
            if path in allowed_paths
        ]
        if theory and bases:
            theories.append({"teoria": theory, "base": bases})

    missing = _coerce_string_list(data.get("informacoes_insuficientes"))
    validated_sources = {item["fonte"] for item in facts} | {path for item in theories for path in item["base"]}
    sources = sorted(validated_sources)

    answer = str(data.get("resposta_ao_usuario") or data.get("resposta_ao_jogador") or "").strip()
    if not answer and facts:
        answer = " ".join(item["fato"] for item in facts[:3])
    if not answer and not missing:
        return None

    answer = _plain_wikilinks(_clean_answer(answer)) if answer else ""
    if access_mode == "player":
        answer = sanitize_player_text(answer)
    if not _answer_is_represented(answer, facts, theories, missing):
        answer = _safe_grounded_answer(facts, theories, missing)
    return {
        "fatos_confirmados": facts,
        "teorias": theories,
        "informacoes_insuficientes": missing,
        "fontes_usadas": sources,
        "resposta_ao_jogador": answer,
    }
