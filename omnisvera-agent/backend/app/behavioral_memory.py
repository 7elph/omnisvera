from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import unicodedata
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
APPROVED_ROOT = PROJECT_ROOT / "omnisvera-model" / "data" / "approved"

_BLOCKING_FLAGS = {"hallucination_detected", "leak_detected"}
_PATH_PATTERN = re.compile(r"(?:[A-Za-z]:[\\/]|(?:^|\s)(?:Characters|Locations|Factions|CAMPANHA|Workflow)/)[^\n]+")
_WIKILINK_PATTERN = re.compile(r"\[\[[^\]]+\]\]")
_WORD_PATTERN = re.compile(r"[a-z0-9]+")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalized(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(_WORD_PATTERN.findall("".join(ch for ch in plain if not unicodedata.combining(ch))))


def _tokens(value: str) -> set[str]:
    return {token for token in _normalized(value).split() if len(token) > 2}


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("notes")
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


def _read_approved(root: Path) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    if not root.exists():
        return []
    for path in sorted(root.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            row_id = str(row.get("id") or "").strip()
            if row_id:
                by_id[row_id] = row
    return list(by_id.values())


def _question_pattern(question: str) -> str:
    normalized = _normalized(question)
    if any(term in normalized for term in ("nao sabemos", "nao se sabe", "ainda nao", "desconhecid")):
        return "informacao_ausente"
    if any(term in normalized for term in ("rumor", "teoria", "suspeita")):
        return "rumor_ou_teoria"
    if any(term in normalized for term in ("relacao", "ligado", "conhece", "aliado")):
        return "relacao"
    if any(term in normalized for term in ("onde", "local", "lugar", "territorio", "fronteira")):
        return "local"
    if normalized.startswith(("quem ", "o que ", "conte me ", "fale sobre ")):
        return "entidade"
    return "consulta_aberta"


def _structure(row: dict[str, Any]) -> list[str]:
    if row.get("insufficient_information_expected"):
        return ["resposta direta", "limite do que foi revelado", "próximo ponto útil"]
    if row.get("theories_allowed"):
        return ["fatos confirmados", "teoria explicitamente rotulada", "limite de conhecimento"]
    category = str(row.get("category") or "")
    if category in {"entity_relations", "relations", "relation_grounding"}:
        return ["resposta direta", "relações confirmadas", "lacunas sem invenção"]
    if category in {"quests_rumors_clues", "rumors", "missions"}:
        return ["situação conhecida", "pistas públicas", "incerteza explícita"]
    return ["resposta direta", "contextualização relevante", "limite de conhecimento"]


def _length_class(text: str) -> str:
    words = len(text.split())
    return "short" if words < 70 else "long" if words > 180 else "medium"


def _safe_demonstration(row: dict[str, Any]) -> str:
    pattern = _question_pattern(str(row.get("instruction") or ""))
    structures = _structure(row)
    entity = {
        "entidade": "[ENTIDADE]",
        "relacao": "[PERSONAGEM] e [ENTIDADE]",
        "local": "[LOCAL]",
        "rumor_ou_teoria": "[RUMOR]",
        "informacao_ausente": "[INFORMAÇÃO]",
    }.get(pattern, "[ASSUNTO]")
    if row.get("insufficient_information_expected"):
        text = (
            f"Responda primeiro o que está confirmado sobre {entity}. "
            "Depois indique, em linguagem natural, o que ainda não foi revelado, sem preencher a lacuna."
        )
    elif row.get("theories_allowed"):
        text = (
            f"Apresente os fatos confirmados sobre {entity} e separe qualquer hipótese com uma transição clara, "
            "sem transformar possibilidade em acontecimento."
        )
    else:
        text = (
            f"Comece respondendo diretamente sobre {entity}; conecte apenas os fatos relevantes e encerre "
            "com prudência quando o contexto não sustentar mais detalhes."
        )
    text = _WIKILINK_PATTERN.sub("[ENTIDADE]", text)
    return _PATH_PATTERN.sub("[FONTE]", text)


def project_example(row: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    if row.get("review_status") != "approved":
        return None, "status_not_approved"
    if row.get("contains_secret"):
        return None, "contains_secret"
    profile = str(row.get("access_profile") or "").lower()
    if profile not in {"player", "gm", "system"}:
        return None, "invalid_access_profile"
    metadata = _metadata(row)
    flags = metadata.get("flags") or {}
    if any(flags.get(name) for name in _BLOCKING_FLAGS):
        return None, "blocking_safety_flag"
    ideal = str(row.get("ideal_response") or "").strip()
    if not ideal:
        return None, "empty_ideal_response"
    example_id = str(row.get("id") or "")
    projection = {
        "example_id": example_id,
        "access_profile": profile,
        "persona_id": row.get("persona_id"),
        "category": str(row.get("category") or "uncategorized"),
        "question_pattern": _question_pattern(str(row.get("instruction") or "")),
        "question_tokens": sorted(_tokens(str(row.get("instruction") or ""))),
        "response_structure": _structure(row),
        "tone": ["natural", "prudente", "narrativo"],
        "length_class": _length_class(ideal),
        "uncertainty_policy": "explicit" if row.get("insufficient_information_expected") else "when_needed",
        "fact_theory_policy": "separate",
        "citation_policy": "evidence_based",
        "refusal_pattern": "natural_limit" if row.get("insufficient_information_expected") else None,
        "sanitized_demonstration": _safe_demonstration(row),
    }
    projection["hash"] = hashlib.sha256(
        json.dumps(projection, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return projection, None


@dataclass(frozen=True)
class BehavioralSelection:
    examples: list[dict[str, Any]]
    retrieval_time_ms: int
    mode: str


class BehavioralMemory:
    def __init__(
        self,
        approved_root: Path = APPROVED_ROOT,
        *,
        enabled: bool = True,
        top_k: int = 3,
        min_score: float = 0.32,
        mode: str = "sanitized",
        ab_mode: str = "behavioral",
    ) -> None:
        self.approved_root = approved_root
        self.enabled = enabled
        self.top_k = max(1, min(3, top_k))
        self.min_score = max(0.0, min(1.0, min_score))
        self.mode = mode
        self.ab_mode = ab_mode
        self._signature: tuple[tuple[str, int, int], ...] = ()
        self._projections: list[dict[str, Any]] = []
        self._projection_by_id: dict[str, dict[str, Any]] = {}
        self._row_hashes: dict[str, str] = {}
        self._excluded: list[dict[str, str]] = []
        self._approved_total = 0
        self._updated_at: str | None = None
        self._usage: deque[dict[str, Any]] = deque(maxlen=200)
        self._lock = threading.RLock()

    def _current_signature(self) -> tuple[tuple[str, int, int], ...]:
        output: list[tuple[str, int, int]] = []
        if self.approved_root.exists():
            for path in sorted(self.approved_root.glob("*.jsonl")):
                try:
                    stat = path.stat()
                except OSError:
                    continue
                output.append((path.name, stat.st_mtime_ns, stat.st_size))
        return tuple(output)

    def invalidate(self) -> None:
        with self._lock:
            self._signature = ()

    def refresh(self, force: bool = False) -> None:
        signature = self._current_signature()
        with self._lock:
            if not force and signature == self._signature:
                return
            rows = _read_approved(self.approved_root)
            projections: list[dict[str, Any]] = []
            excluded: list[dict[str, str]] = []
            next_projection_by_id: dict[str, dict[str, Any]] = {}
            next_row_hashes: dict[str, str] = {}
            for row in rows:
                row_id = str(row.get("id") or "unknown")
                row_hash = hashlib.sha256(
                    json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()
                next_row_hashes[row_id] = row_hash
                if self._row_hashes.get(row_id) == row_hash and row_id in self._projection_by_id:
                    projection, reason = self._projection_by_id[row_id], None
                else:
                    projection, reason = project_example(row)
                if projection:
                    projections.append(projection)
                    next_projection_by_id[row_id] = projection
                else:
                    excluded.append({"example_id": row_id, "reason": reason or "invalid"})
            self._approved_total = len(rows)
            self._projections = projections
            self._projection_by_id = next_projection_by_id
            self._row_hashes = next_row_hashes
            self._excluded = excluded
            self._signature = signature
            self._updated_at = _now()

    def retrieve(
        self,
        question: str,
        *,
        access_profile: str,
        category: str | None = None,
        intent: str | None = None,
        persona_id: str | None = None,
    ) -> BehavioralSelection:
        started = time.perf_counter()
        if not self.enabled or self.mode == "off" or self.ab_mode == "baseline":
            return BehavioralSelection([], 0, "baseline")
        self.refresh()
        query_tokens = _tokens(question)
        pattern = _question_pattern(question)
        scored: list[tuple[float, dict[str, Any]]] = []
        for projection in self._projections:
            profile = projection["access_profile"]
            if access_profile == "player" and profile != "player":
                continue
            if access_profile == "gm" and profile not in {"player", "gm", "system"}:
                continue
            example_persona = projection.get("persona_id")
            if example_persona and example_persona != persona_id:
                continue
            overlap = len(query_tokens & set(projection.get("question_tokens") or [])) / max(1, len(query_tokens))
            score = overlap * 0.45
            if projection.get("question_pattern") == pattern:
                score += 0.25
            if category and projection.get("category") == category:
                score += 0.2
            if intent and _normalized(str(projection.get("category"))) in _normalized(intent):
                score += 0.08
            intent_value = _normalized(intent or "")
            category_value = str(projection.get("category") or "")
            if "entity" in intent_value and category_value in {
                "entities_descriptions", "grounded_qa", "natural_narration", "npc_persona"
            }:
                score += 0.25
            elif "rag" in intent_value and category_value in {
                "grounded_qa", "fact_theory_separation", "insufficient_information", "context_injection"
            }:
                score += 0.18
            if profile == access_profile:
                score += 0.08
            if persona_id and example_persona == persona_id:
                score += 0.15
            score = min(1.0, score)
            if score >= self.min_score:
                value = {key: item for key, item in projection.items() if key != "question_tokens"}
                value["score"] = round(score, 4)
                scored.append((score, value))
        selected = [item for _, item in sorted(scored, key=lambda pair: pair[0], reverse=True)[: self.top_k]]
        elapsed = round((time.perf_counter() - started) * 1000)
        with self._lock:
            self._usage.append(
                {
                    "at": _now(),
                    "count": len(selected),
                    "categories": sorted({str(item.get("category")) for item in selected}),
                    "access_profile": access_profile,
                    "retrieval_time_ms": elapsed,
                }
            )
        return BehavioralSelection(selected, elapsed, self.mode)

    def stats(self) -> dict[str, Any]:
        self.refresh()
        categories = Counter(str(row.get("category") or "unknown") for row in self._projections)
        personas = Counter(str(row.get("persona_id") or "none") for row in self._projections)
        profiles = Counter(str(row.get("access_profile") or "unknown") for row in self._projections)
        used = [row for row in self._usage if row.get("count")]
        average = round(sum(int(row["count"]) for row in used) / len(used), 2) if used else 0.0
        return {
            "enabled": self.enabled and self.mode != "off" and self.ab_mode == "behavioral",
            "mode": self.mode,
            "ab_mode": self.ab_mode,
            "approved_total": self._approved_total,
            "eligible": len(self._projections),
            "indexed": len(self._projections),
            "excluded": list(self._excluded),
            "categories": dict(categories),
            "personas": dict(personas),
            "access_profiles": dict(profiles),
            "last_updated_at": self._updated_at,
            "recent_responses_using_memory": len(used),
            "average_examples_per_response": average,
        }


_MEMORY: BehavioralMemory | None = None
_MEMORY_KEY: tuple[Any, ...] | None = None


def get_behavioral_memory(settings: Any | None = None) -> BehavioralMemory:
    global _MEMORY, _MEMORY_KEY
    if settings is None:
        from .config import get_settings

        settings = get_settings()
    key = (
        settings.behavior_memory_enabled,
        settings.behavior_memory_top_k,
        settings.behavior_memory_min_score,
        settings.behavior_memory_mode,
        settings.behavior_memory_ab_mode,
    )
    if _MEMORY is None or key != _MEMORY_KEY:
        _MEMORY = BehavioralMemory(
            enabled=settings.behavior_memory_enabled,
            top_k=settings.behavior_memory_top_k,
            min_score=settings.behavior_memory_min_score,
            mode=settings.behavior_memory_mode,
            ab_mode=settings.behavior_memory_ab_mode,
        )
        _MEMORY_KEY = key
    return _MEMORY


def invalidate_behavioral_memory() -> None:
    if _MEMORY is not None:
        _MEMORY.invalidate()
