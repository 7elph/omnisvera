from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "1.0"
SOURCE_TYPES = {"real_chat", "corrected_chat", "synthetic_candidate", "manual"}
ACCESS_PROFILES = {"player", "gm", "system"}
REVIEW_STATUSES = {"captured", "pending", "approved", "rejected"}
SPLITS = {None, "train", "eval", "frozen_eval"}
SECRET_MARKERS = (
    "visibility: mestre", "visibility: gm", "gm_secret: true",
    "segredos do mestre", "campanha/estado_da_campanha",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(prefix: str, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def new_example(**overrides: Any) -> dict[str, Any]:
    now = utc_now()
    row: dict[str, Any] = {
        "id": str(uuid.uuid4()), "schema_version": SCHEMA_VERSION,
        "created_at": now, "updated_at": now, "source_type": "manual",
        "category": "uncategorized", "access_profile": "player", "persona_id": None,
        "instruction": "", "retrieved_context": [], "ideal_response": "",
        "facts_expected": [], "theories_allowed": [], "must_not_reveal": [],
        "insufficient_information_expected": False, "requires_rag": True,
        "contains_canon": False, "contains_secret": False, "entity_ids": [],
        "source_note_ids": [], "source_note_hashes": [], "review_status": "captured",
        "reviewer": None, "quality_score": None, "dataset_split": None,
        "dataset_version": None, "notes": None,
    }
    row.update(overrides)
    return row


def validate_example(row: dict[str, Any], strict_approval: bool = True) -> list[str]:
    errors: list[str] = []
    required = set(new_example())
    unknown = set(row) - required
    missing = required - set(row)
    if unknown:
        errors.append("campos desconhecidos: " + ", ".join(sorted(unknown)))
    if missing:
        errors.append("campos ausentes: " + ", ".join(sorted(missing)))
        return errors
    if row["schema_version"] != SCHEMA_VERSION:
        errors.append("schema_version precisa ser 1.0")
    if row["source_type"] not in SOURCE_TYPES:
        errors.append("source_type inválido")
    if row["access_profile"] not in ACCESS_PROFILES:
        errors.append("access_profile inválido")
    if row["review_status"] not in REVIEW_STATUSES:
        errors.append("review_status inválido")
    if row["dataset_split"] not in SPLITS:
        errors.append("dataset_split inválido")
    for key in ("id", "category", "instruction"):
        if not isinstance(row[key], str) or not row[key].strip():
            errors.append(f"{key} precisa ser texto não vazio")
    if not isinstance(row["ideal_response"], str):
        errors.append("ideal_response precisa ser texto")
    for key in ("retrieved_context", "facts_expected", "theories_allowed", "must_not_reveal",
                "entity_ids", "source_note_ids", "source_note_hashes"):
        if not isinstance(row[key], list):
            errors.append(f"{key} precisa ser lista")
    if isinstance(row["retrieved_context"], list) and not all(isinstance(item, dict) for item in row["retrieved_context"]):
        errors.append("retrieved_context aceita somente objetos")
    if row["source_note_hashes"] and len(row["source_note_hashes"]) != len(row["source_note_ids"]):
        errors.append("source_note_hashes precisa corresponder a source_note_ids")
    for key in ("created_at", "updated_at"):
        try:
            datetime.fromisoformat(str(row[key]).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{key} precisa ser ISO-8601")
    for key in ("insufficient_information_expected", "requires_rag", "contains_canon", "contains_secret"):
        if not isinstance(row[key], bool):
            errors.append(f"{key} precisa ser booleano")
    if row["quality_score"] is not None and row["quality_score"] not in (0, 1, 2):
        errors.append("quality_score precisa ser 0, 1, 2 ou null")
    if strict_approval and row["review_status"] == "approved":
        if not str(row.get("reviewer") or "").strip():
            errors.append("approved exige reviewer")
        if row["quality_score"] is None:
            errors.append("approved exige quality_score")
        if not row["ideal_response"].strip():
            errors.append("approved exige ideal_response")
        if row["access_profile"] == "player" and row["contains_secret"]:
            errors.append("exemplo player não pode ser aprovado com contains_secret=true")
    if row["access_profile"] == "player":
        import json
        joined = json.dumps({
            "instruction": row["instruction"], "ideal_response": row["ideal_response"],
            "retrieved_context": row["retrieved_context"], "source_note_ids": row["source_note_ids"],
            "notes": row["notes"],
        }, ensure_ascii=False).casefold()
        leaked = [marker for marker in SECRET_MARKERS if marker in joined]
        if leaked:
            errors.append("marcador reservado em exemplo player: " + ", ".join(leaked))
    try:
        row["instruction"].encode("utf-8")
        row["ideal_response"].encode("utf-8")
    except UnicodeError:
        errors.append("texto não é UTF-8 válido")
    return errors


def migrate_legacy(row: dict[str, Any]) -> dict[str, Any]:
    messages = row.get("messages") or []
    system = str(messages[0].get("content") or "") if len(messages) > 0 else ""
    user = str(messages[1].get("content") or "") if len(messages) > 1 else ""
    assistant = str(messages[2].get("content") or "") if len(messages) > 2 else ""
    access = str(row.get("access") or "player").lower()
    checks = row.get("checks") or {}
    fixed_time = "2026-07-14T00:00:00Z"
    return new_example(
        id=str(row.get("id") or stable_id("legacy", user)),
        created_at=fixed_time, updated_at=fixed_time, source_type="manual",
        category=str(row.get("category") or "legacy"),
        access_profile=access if access in ACCESS_PROFILES else "player",
        instruction=user, ideal_response=assistant,
        retrieved_context=[{"kind": "legacy_prompt", "content": system}],
        facts_expected=[str(value) for value in checks.get("must_contain") or []],
        must_not_reveal=[str(value) for value in checks.get("must_not_contain") or []],
        insufficient_information_expected="insufficient" in str(row.get("category") or ""),
        contains_canon=False, contains_secret=False, review_status="pending",
        notes="Migrado sem perda do dataset legado; requer revisão humana explícita.",
    )


def family_key(instruction: str) -> str:
    words = re.findall(r"[\wÀ-ÿ]+", instruction.casefold())
    return "_".join(words[:4]) or "unknown"
