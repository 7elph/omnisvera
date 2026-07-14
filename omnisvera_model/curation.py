from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io import read_jsonl, write_jsonl
from .paths import DATA_ROOT, ensure_runtime_dirs
from .schema import new_example, utc_now, validate_example


def capture(payload: dict[str, Any], output: Path | None = None) -> dict[str, Any]:
    ensure_runtime_dirs()
    rating = str(payload.get("rating") or "").lower()
    score = {"ruim": 0, "bad": 0, "parcial": 1, "partial": 1, "boa": 2, "good": 2}.get(rating)
    context = payload.get("retrieved_context") or payload.get("chunks") or []
    row = new_example(
        source_type="real_chat", category=str(payload.get("category") or "uncategorized"),
        access_profile=str(payload.get("access_profile") or payload.get("access_mode") or "player"),
        persona_id=payload.get("persona_id"), instruction=str(payload.get("question") or ""),
        retrieved_context=context if isinstance(context, list) else [],
        ideal_response=str(payload.get("final_response") or payload.get("final_answer") or ""),
        facts_expected=[str(x) for x in payload.get("validated_facts") or payload.get("accepted_claims") or []],
        theories_allowed=[str(x) for x in payload.get("theories") or []],
        insufficient_information_expected=bool(payload.get("insufficient_information")),
        source_note_ids=[str(x) for x in payload.get("source_note_ids") or payload.get("notes_retrieved") or []],
        source_note_hashes=[str(x) for x in payload.get("source_note_hashes") or []],
        contains_canon=bool(payload.get("contains_canon")), contains_secret=bool(payload.get("contains_secret")),
        quality_score=score, review_status="captured",
        notes=json.dumps({"raw_response": payload.get("raw_response") or payload.get("raw_ollama"), "model": payload.get("model"),
                          "elapsed_seconds": payload.get("elapsed_seconds") or payload.get("timings_ms"), "rating": rating,
                          "marked_leak": bool(payload.get("leakage")),
                          "marked_invention": bool(payload.get("invention"))}, ensure_ascii=False),
    )
    errors = validate_example(row, strict_approval=False)
    if errors:
        raise ValueError("; ".join(errors))
    target = output or DATA_ROOT / "captured" / "chat_examples.jsonl"
    rows = read_jsonl(target)
    rows.append(row)
    write_jsonl(target, rows)
    return row


def review(source: Path, example_id: str, action: str, reviewer: str,
           ideal_response: str | None = None, category: str | None = None,
           persona_id: str | None = None, contains_secret: bool | None = None,
           quality_score: int | None = None, mark_leak: bool = False,
           mark_invention: bool = False) -> dict[str, Any]:
    if action not in {"approve", "reject", "edit"}:
        raise ValueError("action precisa ser approve, reject ou edit")
    rows = read_jsonl(source)
    match = next((row for row in rows if row.get("id") == example_id), None)
    if match is None:
        raise ValueError(f"exemplo não encontrado: {example_id}")
    if ideal_response is not None:
        match["ideal_response"] = ideal_response
        match["source_type"] = "corrected_chat"
    if category:
        match["category"] = category
    if persona_id is not None:
        match["persona_id"] = persona_id or None
    if contains_secret is not None:
        match["contains_secret"] = contains_secret
    if mark_leak:
        match["contains_secret"] = True
    if mark_leak or mark_invention:
        try: review_notes=json.loads(match.get("notes") or "{}")
        except json.JSONDecodeError: review_notes={"previous_notes":match.get("notes")}
        review_notes.update({"marked_leak":mark_leak,"marked_invention":mark_invention})
        match["notes"]=json.dumps(review_notes,ensure_ascii=False)
    if quality_score is not None:
        match["quality_score"] = quality_score
    match["reviewer"] = reviewer
    match["updated_at"] = utc_now()
    match["review_status"] = {"approve": "approved", "reject": "rejected", "edit": "pending"}[action]
    errors = validate_example(match)
    if errors:
        raise ValueError("; ".join(errors))
    ensure_runtime_dirs()
    destination = DATA_ROOT / ({"approve": "approved", "reject": "rejected", "edit": "reviewed"}[action]) / "examples.jsonl"
    destination_rows = [row for row in read_jsonl(destination) if row.get("id") != example_id]
    destination_rows.append(match)
    write_jsonl(destination, destination_rows)
    return match
