from __future__ import annotations

import hashlib
import json
import shutil
import sys
import threading
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from omnisvera_model.dataset import coverage_report, find_conflicts, find_duplicates  # noqa: E402
from omnisvera_model.io import read_json, read_jsonl, sha256_file, write_jsonl  # noqa: E402
from omnisvera_model.paths import COVERAGE_CONFIG, DATA_ROOT, ensure_runtime_dirs  # noqa: E402
from omnisvera_model.schema import new_example, utc_now, validate_example  # noqa: E402

from .behavioral_memory import get_behavioral_memory, invalidate_behavioral_memory


INTERACTIONS_PATH = DATA_ROOT / "captured" / "companion_interactions.jsonl"
CANDIDATES_PATH = DATA_ROOT / "candidates" / "companion_examples.jsonl"
APPROVED_PATH = DATA_ROOT / "approved" / "companion_examples.jsonl"
REJECTED_PATH = DATA_ROOT / "rejected" / "companion_examples.jsonl"
AUDIT_PATH = DATA_ROOT / "raw" / "companion_curation_audit.jsonl"
_LOCK = threading.RLock()
_SECRET_MARKERS = (
    "visibility: mestre",
    "visibility: gm",
    "gm_secret: true",
    "segredos do mestre",
    "estado_da_campanha",
)
_ACTIONS = {
    "good",
    "correct",
    "reject",
    "hallucination",
    "leak",
    "incomplete",
    "artificial",
    "incorrect_source",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str | None) -> datetime:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rotate_backups(path: Path, keep: int = 3) -> None:
    if not path.exists():
        return
    for index in range(keep, 1, -1):
        older = path.with_suffix(path.suffix + f".bak{index - 1}")
        newer = path.with_suffix(path.suffix + f".bak{index}")
        if older.exists():
            shutil.copy2(older, newer)
    shutil.copy2(path, path.with_suffix(path.suffix + ".bak1"))


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    _rotate_backups(path)
    write_jsonl(path, rows)


def _upsert(path: Path, row: dict[str, Any], key: str = "id") -> None:
    rows = [item for item in read_jsonl(path) if item.get(key) != row.get(key)]
    rows.append(row)
    _write_rows(path, rows)


def _notes(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("notes")
    if isinstance(value, dict):
        return dict(value)
    try:
        parsed = json.loads(value or "{}")
        return parsed if isinstance(parsed, dict) else {"legacy_notes": value}
    except json.JSONDecodeError:
        return {"legacy_notes": value}


def _set_notes(row: dict[str, Any], metadata: dict[str, Any]) -> None:
    row["notes"] = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))


def _text_items(values: list[Any], *keys: str) -> list[str]:
    output: list[str] = []
    for value in values:
        if isinstance(value, str):
            text = value.strip()
        elif isinstance(value, dict):
            text = next((str(value.get(key) or "").strip() for key in keys if value.get(key)), "")
        else:
            text = ""
        if text and text not in output:
            output.append(text)
    return output


def _source_rows(values: list[Any], access_profile: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, dict):
            continue
        path = str(value.get("path") or value.get("source") or value.get("fonte") or "").replace("\\", "/").strip()
        if not path or path in seen:
            continue
        visibility = str(value.get("visibility") or "").strip()
        joined = f"{path} {visibility}".casefold()
        if access_profile == "player" and (
            visibility.casefold() in {"gm", "mestre", "oculto", "velado", "não revelado", "nao revelado"}
            or any(marker in joined for marker in _SECRET_MARKERS)
        ):
            raise ValueError("Exemplo player contém fonte reservada e não pode ser capturado.")
        seen.add(path)
        rows.append(
            {
                "path": path,
                "title": str(value.get("title") or Path(path).stem),
                "type": value.get("type"),
                "visibility": visibility or None,
            }
        )
    return rows


def _hash_sources(sources: list[dict[str, Any]], vault_path: Path) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    hashes: list[str] = []
    root = vault_path.resolve()
    for source in sources:
        relative = str(source["path"]).replace("\\", "/")
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        ids.append(relative)
        hashes.append(sha256_file(candidate) if candidate.is_file() else _digest(relative))
    return ids, hashes


def _suggest_category(payload: dict[str, Any], action: str) -> str:
    configured = set((read_json(COVERAGE_CONFIG).get("categories") or {}).keys())
    question = str(payload.get("question") or "").casefold()
    if action in {"leak", "hallucination", "incorrect_source"}:
        suggestion = "player_gm_safety" if action == "leak" else "adversarial"
    elif payload.get("insufficient_information"):
        suggestion = "insufficient_information"
    elif payload.get("theories"):
        suggestion = "fact_vs_theory"
    elif payload.get("persona_id") or payload.get("persona_id_override"):
        suggestion = "personas_npcs"
    elif any(term in question for term in ("rumor", "missão", "missao", "pista", "quest")):
        suggestion = "quests_rumors_clues"
    elif any(term in question for term in ("onde", "lugar", "local", "facção", "faccao", "território", "territorio")):
        suggestion = "places_factions_territories"
    elif any(term in question for term in ("relação", "relacao", "ligado", "conhece")):
        suggestion = "entity_relations"
    elif action == "artificial":
        suggestion = "natural_narrative"
    else:
        suggestion = "entities_descriptions"
    return suggestion if suggestion in configured else sorted(configured)[0]


def _interaction_from_payload(payload: dict[str, Any], actor: str) -> dict[str, Any]:
    action = str(payload.get("feedback_action") or "").strip().lower()
    if action not in _ACTIONS:
        raise ValueError(f"Ação de feedback inválida: {action}")
    access_profile = str(payload.get("user_profile") or "gm").strip().lower()
    if access_profile not in {"player", "gm"}:
        raise ValueError("user_profile precisa ser player ou gm")
    sources = _source_rows(payload.get("retrieved_sources") or [], access_profile)
    leak = action == "leak"
    raw = str(payload.get("raw_model_response") or "")
    final = str(payload.get("final_response") or "")
    if leak:
        raw = "[conteúdo removido por marcação de vazamento]"
        final = "[resposta removida para revisão de segurança]"
    now = _now()
    return {
        "interaction_id": str(payload.get("interaction_id") or uuid.uuid4()),
        "created_at": str(payload.get("created_at") or now),
        "updated_at": now,
        "session_id": payload.get("session_id"),
        "user_profile": access_profile,
        "player_id": payload.get("player_id"),
        "character_id": payload.get("character_id"),
        "persona_id": payload.get("persona_id_override") or payload.get("persona_id"),
        "question": str(payload.get("question") or "").strip(),
        "raw_model_response": raw,
        "final_response": final,
        "verified_facts": payload.get("verified_facts") or [],
        "theories": payload.get("theories") or [],
        "insufficient_information": payload.get("insufficient_information") or [],
        "retrieved_sources": sources,
        "retrieval_mode": payload.get("retrieval_mode"),
        "model": payload.get("model"),
        "ollama_used": bool(payload.get("ollama_used")),
        "response_time_ms": max(0, int(payload.get("response_time_ms") or 0)),
        "validator_rejections": payload.get("validator_rejections") or [],
        "warning": payload.get("warning"),
        "behavior_memory_used": bool(payload.get("behavior_memory_used")),
        "behavioral_trace": payload.get("behavioral_trace") or None,
        "feedback_status": "rejected" if action == "reject" else "pending",
        "feedback_action": action,
        "reason": payload.get("reason"),
        "captured_by": actor,
        "candidate_id": None,
    }


def _candidate_from_interaction(
    interaction: dict[str, Any], payload: dict[str, Any], vault_path: Path
) -> dict[str, Any]:
    action = interaction["feedback_action"]
    facts = _text_items(interaction["verified_facts"], "fato", "texto", "fact")
    theories = _text_items(interaction["theories"], "teoria", "texto", "theory")
    source_ids, source_hashes = _hash_sources(interaction["retrieved_sources"], vault_path)
    positive_initial = action not in {"hallucination", "leak", "incorrect_source"}
    ideal = interaction["final_response"] if positive_initial else ""
    flags = {
        "hallucination_detected": action == "hallucination",
        "leak_detected": action == "leak",
        "incomplete_detected": action == "incomplete",
        "artificial_detected": action == "artificial",
        "incorrect_source_detected": action == "incorrect_source",
    }
    has_reserved_source = any(
        str(source.get("visibility") or "").casefold() in {"gm", "mestre", "oculto", "velado", "não revelado", "nao revelado"}
        or any(marker in str(source.get("path") or "").casefold() for marker in _SECRET_MARKERS)
        for source in interaction["retrieved_sources"]
    )
    answer_words = len(str(interaction.get("final_response") or "").split())
    has_quality_warning = bool(interaction.get("validator_rejections") or interaction.get("warning"))
    suggested_quality = 2 if has_quality_warning else 4 if answer_words >= 35 else 3
    row = new_example(
        id=str(uuid.uuid4()),
        source_type="real_chat",
        category=str(payload.get("category") or _suggest_category(payload, action)),
        access_profile=interaction["user_profile"],
        persona_id=interaction.get("persona_id"),
        instruction=interaction["question"],
        retrieved_context=[dict(source) for source in interaction["retrieved_sources"]],
        ideal_response=ideal,
        facts_expected=facts,
        theories_allowed=theories,
        insufficient_information_expected=bool(interaction["insufficient_information"]),
        requires_rag=bool(interaction["retrieved_sources"]),
        contains_canon=bool(facts),
        contains_secret=bool(flags["leak_detected"] or has_reserved_source),
        entity_ids=[],
        source_note_ids=source_ids,
        source_note_hashes=source_hashes,
        review_status="rejected" if action == "reject" else "pending",
        reviewer=interaction["captured_by"] if action == "reject" else None,
        quality_score=0 if suggested_quality <= 2 else 1 if suggested_quality == 3 else 2,
    )
    _set_notes(
        row,
        {
            "interaction_id": interaction["interaction_id"],
            "feedback_action": action,
            "flags": flags,
            "quality_5": suggested_quality,
            "quality_suggested": True,
            "auto_captured": bool(payload.get("auto_captured")),
            "curator_notes": payload.get("reason"),
            "model": interaction.get("model"),
            "retrieval_mode": interaction.get("retrieval_mode"),
            "original_response_hash": _digest(str(payload.get("final_response") or "")),
        },
    )
    errors = validate_example(row, strict_approval=False)
    if errors:
        raise ValueError("; ".join(errors))
    return row


def _audit(
    example: dict[str, Any], action: str, actor: str, reason: str | None = None,
    *, previous_ideal_hash: str | None = None, previous_status: str | None = None,
) -> None:
    metadata = _notes(example)
    event = {
        "event_id": str(uuid.uuid4()),
        "example_id": example["id"],
        "interaction_id": metadata.get("interaction_id"),
        "action": action,
        "actor": actor,
        "at": _now(),
        "schema_version": example.get("schema_version"),
        "dataset_version": example.get("dataset_version"),
        "ideal_response_hash": _digest(str(example.get("ideal_response") or "")),
        "previous_ideal_response_hash": previous_ideal_hash,
        "original_response_hash": metadata.get("original_response_hash"),
        "previous_status": previous_status,
        "reason": reason,
        "flags": metadata.get("flags") or {},
    }
    rows = read_jsonl(AUDIT_PATH)
    rows.append(event)
    _write_rows(AUDIT_PATH, rows)


def capture_interaction(payload: dict[str, Any], vault_path: Path, actor: str = "Sage") -> dict[str, Any]:
    ensure_runtime_dirs()
    with _LOCK:
        interaction = _interaction_from_payload(payload, actor)
        existing = next(
            (row for row in read_jsonl(INTERACTIONS_PATH) if row.get("interaction_id") == interaction["interaction_id"]),
            None,
        )
        if existing and existing.get("candidate_id"):
            candidate_id = str(existing["candidate_id"])
            action = str(payload.get("feedback_action") or "good")
            interaction["candidate_id"] = candidate_id
            if action == "reject":
                candidate = reject_example(candidate_id, actor, payload.get("reason"))
                interaction["feedback_status"] = "rejected"
            elif action in {"hallucination", "leak", "incomplete", "artificial", "incorrect_source"}:
                flag_name = "incorrect-source" if action == "incorrect_source" else action
                candidate = mark_flag(candidate_id, flag_name, actor, payload.get("reason"))["example"]
                interaction["feedback_status"] = "pending"
            else:
                candidate = get_example(candidate_id)
                interaction["feedback_status"] = "pending"
            _upsert(INTERACTIONS_PATH, interaction, key="interaction_id")
            return {"interaction": interaction, "example": candidate, "validation_errors": []}
        candidate = _candidate_from_interaction(interaction, payload, vault_path)
        interaction["candidate_id"] = candidate["id"]
        _upsert(INTERACTIONS_PATH, interaction, key="interaction_id")
        _upsert(CANDIDATES_PATH, candidate)
        if candidate["review_status"] == "rejected":
            _upsert(REJECTED_PATH, candidate)
        _audit(candidate, "capture", actor, payload.get("reason"))
        return {
            "interaction": interaction,
            "example": _public_example(candidate),
            "validation_errors": validate_example(candidate, strict_approval=False),
        }


def record_unreviewed_interaction(
    payload: dict[str, Any], vault_path: Path, actor: str = "master_session"
) -> dict[str, Any]:
    """Create a pending, prefilled candidate from a master session; never approves it."""
    payload = dict(payload)
    payload["feedback_action"] = "good"
    payload["auto_captured"] = True
    captured = capture_interaction(payload, vault_path, actor=actor)
    interaction = dict(captured["interaction"])
    interaction["feedback_status"] = "unreviewed"
    with _LOCK:
        _upsert(INTERACTIONS_PATH, interaction, key="interaction_id")
    return {"interaction": interaction, "example": captured["example"]}


def _all_candidates() -> list[dict[str, Any]]:
    directory = CANDIDATES_PATH.parent
    paths = sorted(directory.glob("*.jsonl")) if directory.exists() else []
    # The Companion override file is read last so an edited migrated example
    # supersedes its immutable seed without creating a duplicate in the UI.
    paths = [path for path in paths if path != CANDIDATES_PATH] + [CANDIDATES_PATH]
    by_id: dict[str, dict[str, Any]] = {}
    for path in paths:
        for row in read_jsonl(path):
            row_id = str(row.get("id") or "")
            if row_id:
                by_id[row_id] = row
    return list(by_id.values())


def _public_example(row: dict[str, Any]) -> dict[str, Any]:
    value = dict(row)
    value["curation"] = _notes(row)
    return value


def list_examples(
    *, status: str | None = None, access_profile: str | None = None,
    category: str | None = None, flag: str | None = None, model: str | None = None,
    persona_id: str | None = None, quality: int | None = None,
    date_from: str | None = None, date_to: str | None = None,
) -> list[dict[str, Any]]:
    rows = _all_candidates()
    output: list[dict[str, Any]] = []
    for row in rows:
        metadata = _notes(row)
        flags = metadata.get("flags") or {}
        if status and row.get("review_status") != status:
            continue
        if access_profile and row.get("access_profile") != access_profile:
            continue
        if category and row.get("category") != category:
            continue
        if flag and not flags.get(flag):
            continue
        if model and metadata.get("model") != model:
            continue
        if persona_id and str(row.get("persona_id") or "") != persona_id:
            continue
        if quality and int(metadata.get("quality_5") or 0) != quality:
            continue
        if date_from and _parse_time(row.get("created_at")) < _parse_time(date_from):
            continue
        if date_to and _parse_time(row.get("created_at")) > _parse_time(date_to) + timedelta(days=1):
            continue
        output.append(_public_example(row))
    return sorted(output, key=lambda item: str(item.get("updated_at") or ""), reverse=True)


def get_example(example_id: str) -> dict[str, Any]:
    match = next((row for row in _all_candidates() if row.get("id") == example_id), None)
    if match is None:
        raise ValueError(f"Exemplo não encontrado: {example_id}")
    detail = _public_example(match)
    interaction_id = detail.get("curation", {}).get("interaction_id")
    detail["interaction"] = next(
        (
            row
            for row in read_jsonl(INTERACTIONS_PATH)
            if row.get("interaction_id") == interaction_id
        ),
        None,
    )
    return detail


def update_example(example_id: str, patch: dict[str, Any], actor: str = "Sage") -> dict[str, Any]:
    with _LOCK:
        rows = _all_candidates()
        match = next((row for row in rows if row.get("id") == example_id), None)
        if match is None:
            raise ValueError(f"Exemplo não encontrado: {example_id}")
        if match.get("review_status") == "approved":
            raise ValueError("Exemplo aprovado exige nova versão; não pode ser sobrescrito silenciosamente.")
        metadata = _notes(match)
        previous_ideal_hash = _digest(str(match.get("ideal_response") or ""))
        previous_status = str(match.get("review_status") or "")
        flags = dict(metadata.get("flags") or {})
        field_map = {
            "category": "category", "source_type": "source_type", "persona_id": "persona_id",
            "ideal_response": "ideal_response", "facts_expected": "facts_expected",
            "theories_allowed": "theories_allowed",
            "insufficient_information_expected": "insufficient_information_expected",
            "requires_rag": "requires_rag", "contains_canon": "contains_canon",
            "contains_secret": "contains_secret",
        }
        for incoming, target in field_map.items():
            if incoming in patch and patch[incoming] is not None:
                match[target] = patch[incoming]
        for flag_name in (
            "hallucination_detected", "leak_detected", "incomplete_detected",
            "artificial_detected", "incorrect_source_detected",
        ):
            if flag_name in patch and patch[flag_name] is not None:
                flags[flag_name] = bool(patch[flag_name])
        if patch.get("quality") is not None:
            quality = int(patch["quality"])
            metadata["quality_5"] = quality
            match["quality_score"] = 0 if quality <= 2 else 1 if quality == 3 else 2
        if patch.get("notes") is not None:
            metadata["curator_notes"] = patch["notes"]
        metadata["flags"] = flags
        metadata["last_edit_reason"] = patch.get("reason")
        _set_notes(match, metadata)
        match["updated_at"] = utc_now()
        match["review_status"] = "pending"
        errors = validate_example(match, strict_approval=False)
        if errors:
            raise ValueError("; ".join(errors))
        _upsert(CANDIDATES_PATH, match)
        _audit(
            match, "edit", actor, patch.get("reason"),
            previous_ideal_hash=previous_ideal_hash, previous_status=previous_status,
        )
        invalidate_behavioral_memory()
        return {"example": _public_example(match), "validation_errors": errors}


def approve_example(
    example_id: str, actor: str, reason: str | None = None,
    ideal_response: str | None = None, quality: int | None = None,
) -> dict[str, Any]:
    with _LOCK:
        rows = _all_candidates()
        match = next((row for row in rows if row.get("id") == example_id), None)
        if match is None:
            raise ValueError(f"Exemplo não encontrado: {example_id}")
        if match.get("review_status") == "approved":
            return {"example": _public_example(match), "validation_errors": []}
        if match.get("review_status") == "rejected":
            raise ValueError("Revise o exemplo rejeitado antes de tentar aprová-lo.")
        if ideal_response is not None:
            match["ideal_response"] = ideal_response
            match["source_type"] = "corrected_chat"
        metadata = _notes(match)
        flags = metadata.get("flags") or {}
        blocking = [name for name in ("hallucination_detected", "leak_detected", "incorrect_source_detected") if flags.get(name)]
        if blocking:
            raise ValueError("Corrija e desmarque as falhas bloqueantes antes de aprovar: " + ", ".join(blocking))
        if match.get("contains_secret"):
            raise ValueError("Exemplo com segredo é inelegível para aprovação de treino.")
        if quality is not None:
            metadata["quality_5"] = quality
            match["quality_score"] = 0 if quality <= 2 else 1 if quality == 3 else 2
        if match.get("quality_score") is None:
            raise ValueError("Informe a qualidade de 1 a 5 antes da aprovação.")
        if not str(match.get("ideal_response") or "").strip():
            raise ValueError("A resposta ideal precisa ser preenchida.")
        match["review_status"] = "approved"
        match["reviewer"] = actor
        match["updated_at"] = utc_now()
        metadata["approval_reason"] = reason
        _set_notes(match, metadata)
        errors = validate_example(match, strict_approval=True)
        if errors:
            raise ValueError("; ".join(errors))
        _upsert(CANDIDATES_PATH, match)
        _upsert(APPROVED_PATH, match)
        _audit(match, "approve", actor, reason)
        invalidate_behavioral_memory()
        return {"example": _public_example(match), "validation_errors": []}


def reject_example(example_id: str, actor: str, reason: str | None = None) -> dict[str, Any]:
    with _LOCK:
        rows = _all_candidates()
        match = next((row for row in rows if row.get("id") == example_id), None)
        if match is None:
            raise ValueError(f"Exemplo não encontrado: {example_id}")
        if match.get("review_status") == "approved":
            raise ValueError("Exemplo aprovado não pode ser rejeitado sem criar nova versão auditada.")
        if match.get("review_status") == "rejected":
            return _public_example(match)
        match["review_status"] = "rejected"
        match["reviewer"] = actor
        match["updated_at"] = utc_now()
        metadata = _notes(match)
        metadata["rejection_reason"] = reason
        _set_notes(match, metadata)
        _upsert(CANDIDATES_PATH, match)
        _upsert(REJECTED_PATH, match)
        _audit(match, "reject", actor, reason)
        invalidate_behavioral_memory()
        return _public_example(match)


def mark_flag(example_id: str, flag: str, actor: str, detail: str | None = None) -> dict[str, Any]:
    allowed = {
        "hallucination": "hallucination_detected",
        "leak": "leak_detected",
        "incomplete": "incomplete_detected",
        "artificial": "artificial_detected",
        "incorrect-source": "incorrect_source_detected",
    }
    if flag not in allowed:
        raise ValueError("Flag inválida")
    patch: dict[str, Any] = {allowed[flag]: True, "reason": detail}
    if flag in {"hallucination", "incorrect-source"}:
        patch["ideal_response"] = ""
    if flag == "leak":
        patch.update({"ideal_response": "", "contains_secret": True})
    result = update_example(example_id, patch, actor)
    _audit(result["example"], f"mark_{flag}", actor, detail)
    return result


def delete_pending(example_id: str, actor: str) -> None:
    with _LOCK:
        rows = _all_candidates()
        match = next((row for row in rows if row.get("id") == example_id), None)
        if match is None:
            return
        if match.get("review_status") not in {"captured", "pending"}:
            raise ValueError("Somente candidatos não aprovados podem ser excluídos.")
        _audit(match, "delete_pending", actor)
        candidate_files = sorted(CANDIDATES_PATH.parent.glob("*.jsonl"))
        if CANDIDATES_PATH not in candidate_files:
            candidate_files.append(CANDIDATES_PATH)
        for path in candidate_files:
            source_rows = read_jsonl(path)
            if any(row.get("id") == example_id for row in source_rows):
                _write_rows(path, [row for row in source_rows if row.get("id") != example_id])


def duplicate_example(example_id: str, actor: str) -> dict[str, Any]:
    with _LOCK:
        original = next((row for row in _all_candidates() if row.get("id") == example_id), None)
        if original is None:
            raise ValueError(f"Exemplo não encontrado: {example_id}")
        now = utc_now()
        duplicate = dict(original)
        duplicate.update(
            {
                "id": str(uuid.uuid4()),
                "created_at": now,
                "updated_at": now,
                "review_status": "pending",
                "reviewer": None,
                "quality_score": None,
                "dataset_split": None,
                "dataset_version": None,
            }
        )
        metadata = _notes(original)
        metadata.update(
            {
                "variation_of": original["id"],
                "quality_5": None,
                "duplicated_by": actor,
                "flags": {key: False for key in (metadata.get("flags") or {})},
            }
        )
        _set_notes(duplicate, metadata)
        errors = validate_example(duplicate, strict_approval=False)
        if errors:
            raise ValueError("; ".join(errors))
        _upsert(CANDIDATES_PATH, duplicate)
        _audit(duplicate, "duplicate_variation", actor, f"Variação de {original['id']}")
        return _public_example(duplicate)


def sanitized_report() -> dict[str, Any]:
    safe_examples: list[dict[str, Any]] = []
    for row in _all_candidates():
        metadata = _notes(row)
        safe_examples.append(
            {
                "id": row.get("id"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "category": row.get("category"),
                "access_profile": row.get("access_profile"),
                "persona_id": row.get("persona_id"),
                "review_status": row.get("review_status"),
                "quality": metadata.get("quality_5"),
                "model": metadata.get("model"),
                "flags": metadata.get("flags") or {},
                "contains_secret": bool(row.get("contains_secret")),
                "instruction_hash": _digest(str(row.get("instruction") or "")),
            }
        )
    return {"generated_at": _now(), "stats": stats(), "examples": safe_examples}


def purge_unreviewed(retention_days: int) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, retention_days))
    with _LOCK:
        rows = read_jsonl(INTERACTIONS_PATH)
        kept = [
            row for row in rows
            if row.get("feedback_status") != "unreviewed" or _parse_time(row.get("created_at")) >= cutoff
        ]
        removed = len(rows) - len(kept)
        if removed:
            _write_rows(INTERACTIONS_PATH, kept)
        return removed


def _batch_key(row: dict[str, Any]) -> str:
    instruction = " ".join(str(row.get("instruction") or "").casefold().split())
    ideal = " ".join(str(row.get("ideal_response") or "").casefold().split())
    return _digest(f"{instruction}\n{ideal}")


def validate_batch(example_ids: list[str], minimum_quality: int = 4) -> dict[str, Any]:
    unique_ids = list(dict.fromkeys(str(value) for value in example_ids if str(value).strip()))
    rows = {str(row.get("id")): row for row in _all_candidates()}
    selected_rows = [rows[example_id] for example_id in unique_ids if example_id in rows]
    comparison_rows = [
        row for row in rows.values() if row.get("review_status") == "approved"
    ] + selected_rows
    exact_groups, near_pairs = find_duplicates(comparison_rows)
    conflicts = find_conflicts(comparison_rows)
    extra_reasons: dict[str, list[str]] = {example_id: [] for example_id in unique_ids}
    for group in exact_groups:
        for example_id in set(group) & set(unique_ids):
            extra_reasons[example_id].append("critical_duplicate")
    for pair in near_pairs:
        for example_id in {str(pair.get("left")), str(pair.get("right"))} & set(unique_ids):
            extra_reasons[example_id].append("near_duplicate")
    for conflict in conflicts:
        for example_id in set(str(value) for value in conflict.get("ids") or []) & set(unique_ids):
            extra_reasons[example_id].append("conflict")
    approved_keys = {
        _batch_key(row)
        for row in rows.values()
        if row.get("review_status") == "approved" and str(row.get("ideal_response") or "").strip()
    }
    selected_keys: set[str] = set()
    eligible: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for example_id in unique_ids:
        row = rows.get(example_id)
        reasons: list[str] = []
        if row is None:
            reasons.append("not_found")
        else:
            metadata = _notes(row)
            flags = metadata.get("flags") or {}
            if row.get("review_status") != "pending":
                reasons.append("not_pending")
            if row.get("contains_secret"):
                reasons.append("contains_secret")
            for flag in ("leak_detected", "hallucination_detected", "incorrect_source_detected"):
                if flags.get(flag):
                    reasons.append(flag)
            if row.get("access_profile") not in {"player", "gm", "system"}:
                reasons.append("invalid_access_profile")
            if not str(row.get("ideal_response") or "").strip():
                reasons.append("empty_ideal_response")
            quality = int(metadata.get("quality_5") or 0)
            if quality < minimum_quality:
                reasons.append("quality_below_threshold")
            errors = validate_example(row, strict_approval=True)
            reasons.extend(f"schema:{error}" for error in errors)
            key = _batch_key(row)
            if key in approved_keys or key in selected_keys:
                reasons.append("critical_duplicate")
            selected_keys.add(key)
            reasons.extend(extra_reasons.get(example_id) or [])
        summary = {
            "id": example_id,
            "instruction": str((row or {}).get("instruction") or "")[:180],
            "category": (row or {}).get("category"),
            "access_profile": (row or {}).get("access_profile"),
            "quality": (_notes(row).get("quality_5") if row else None),
            "reasons": list(dict.fromkeys(reasons)),
        }
        (blocked if reasons else eligible).append(summary)
    return {
        "requested": len(unique_ids),
        "eligible": eligible,
        "blocked": blocked,
        "minimum_quality": minimum_quality,
        "confirmation_required": "APROVAR LOTE",
    }


def approve_batch(
    example_ids: list[str], *, confirmation: str, reviewed: bool, actor: str = "Sage",
    reason: str | None = None, minimum_quality: int = 4,
) -> dict[str, Any]:
    if confirmation.strip() != "APROVAR LOTE":
        raise ValueError("Digite APROVAR LOTE para confirmar a revisão humana.")
    if not reviewed:
        raise ValueError("Confirme que os exemplos selecionados foram revisados visualmente.")
    validation = validate_batch(example_ids, minimum_quality=minimum_quality)
    approved: list[dict[str, Any]] = []
    for summary in validation["eligible"]:
        row = get_example(summary["id"])
        quality = int((_notes(row).get("quality_5") or minimum_quality))
        result = approve_example(
            summary["id"], actor, reason or "Aprovação em lote revisada pelo Sage", quality=quality
        )
        approved.append(
            {
                "id": summary["id"],
                "category": result["example"].get("category"),
                "access_profile": result["example"].get("access_profile"),
            }
        )
    invalidate_behavioral_memory()
    return {**validation, "approved": approved, "approved_count": len(approved)}


def behavior_memory_stats() -> dict[str, Any]:
    data = get_behavioral_memory().stats()
    approved = int(data.get("approved_total") or 0)
    milestones = [
        (25, "smoke"), (50, "experimental"), (100, "alpha_benchmark"),
        (250, "candidate_alpha"), (500, "candidate_beta"), (1000, "production_candidate"),
    ]
    next_target, next_name = next(
        ((target, name) for target, name in milestones if approved < target), milestones[-1]
    )
    data["milestones"] = [
        {"target": target, "stage": name, "reached": approved >= target} for target, name in milestones
    ]
    data["next_milestone"] = {
        "target": next_target, "stage": next_name, "remaining": max(0, next_target - approved)
    }
    return data


def stats() -> dict[str, Any]:
    rows = _all_candidates()
    statuses = Counter(str(row.get("review_status") or "unknown") for row in rows)
    categories = Counter(str(row.get("category") or "unknown") for row in rows)
    profiles = Counter(str(row.get("access_profile") or "unknown") for row in rows)
    models: Counter[str] = Counter()
    flags: Counter[str] = Counter()
    for row in rows:
        metadata = _notes(row)
        models[str(metadata.get("model") or "unknown")] += 1
        for name, enabled in (metadata.get("flags") or {}).items():
            if enabled:
                flags[name] += 1
    coverage = coverage_report()
    minimum = int(read_json(COVERAGE_CONFIG).get("minimum_approved", 1000))
    approved = int(coverage.get("approved") or 0)
    return {
        "captured": len(read_jsonl(INTERACTIONS_PATH)),
        "examples": len(rows),
        "statuses": dict(statuses),
        "categories": dict(categories),
        "profiles": dict(profiles),
        "models": dict(models),
        "flags": dict(flags),
        "approved": approved,
        "minimum_approved": minimum,
        "progress_percent": round(min(100.0, approved * 100 / minimum), 2),
        "coverage": coverage,
        "training_blocked": approved < minimum,
        "warning": "PENDENTES NÃO SÃO USADOS NO TREINAMENTO.",
        "behavior_memory": behavior_memory_stats(),
    }
