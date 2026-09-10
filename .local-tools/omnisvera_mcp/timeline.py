"""
Historical Evidence Timeline v0.1

Provides reliable temporal representation of Sessions 1-4 for replay
and backtest without look-ahead leakage.

Key principles:
- Ausência de timestamp real NÃO gera timestamp inventado.
- ordinal é a ordem epistemicamente segura.
- narrative_json/posthoc NÃO entram no estado preditivo.
- Fonte bruta e derivação são sempre distinguíveis.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
#  Source classification
# ---------------------------------------------------------------------------

class SourceType:
    """Classification of historical evidence sources."""
    PRIMARY_SEQUENTIAL = "primary_sequential"   # raw transcript, sequential
    POSTHOC_SUMMARY = "posthoc_summary"         # narrative, summary, created after
    RUNTIME_RECORD = "runtime_record"           # scene_events, ledger, workspace
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
#  Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """A single event in the session timeline."""
    ordinal: int
    event_type: str           # "dialogue", "narration", "scene_created", etc.
    content: str
    source: str               # source file/path
    source_type: str          # SourceType constant
    source_position: str | None = None  # line number, timestamp range, etc.
    occurred_at: str | None = None      # real timestamp if known
    recorded_at: str | None = None      # when recorded
    imported_at: str | None = None      # when imported to system
    session_id: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SessionTimeline:
    """Ordered sequence of evidence events for a session."""
    session_id: int
    timeline_schema: str = "companion.session.timeline.v1"
    ordering: str = "ordinal"
    events: list[TimelineEvent] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    posthoc_excluded: list[str] = field(default_factory=list)

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def max_ordinal(self) -> int:
        return max((e.ordinal for e in self.events), default=0)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["event_count"] = self.event_count
        d["max_ordinal"] = self.max_ordinal
        return d

    def events_up_to(self, cutoff_ordinal: int) -> list[TimelineEvent]:
        """Return events with ordinal <= cutoff."""
        return [e for e in self.events if e.ordinal <= cutoff_ordinal]

    def events_after(self, cutoff_ordinal: int) -> list[TimelineEvent]:
        """Return events with ordinal > cutoff."""
        return [e for e in self.events if e.ordinal > cutoff_ordinal]


# ---------------------------------------------------------------------------
#  Transcript parser (Whisper STT format)
# ---------------------------------------------------------------------------

# Pattern: [00:00.000 --> 00:02.000]  text content
_TIMESTAMP_RE = re.compile(
    r"^\[(\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}\.\d{3})\]\s*(.*)"
)


def parse_transcript_line(line: str) -> tuple[str, str, str] | None:
    """Parse a Whisper transcript line. Returns (start, end, text) or None."""
    m = _TIMESTAMP_RE.match(line.strip())
    if m:
        return m.group(1), m.group(2), m.group(3).strip()
    return None


def build_timeline_from_transcript(
    transcript_path: str | Path,
    session_id: int,
    *,
    max_events: int = 500,
) -> SessionTimeline:
    """
    Parse a Whisper transcript file into a SessionTimeline.

    Each timestamped line becomes an event with:
    - ordinal = line order (1-based, starting from first timestamped line)
    - source_position = line number in file
    - occurred_at = Whisper timestamp (inferred from audio, not real wall-clock)
    - source_type = PRIMARY_SEQUENTIAL

    Lines without timestamps are skipped (metadata, detection messages).
    """
    path = Path(transcript_path)
    events: list[TimelineEvent] = []
    limitations: list[str] = []
    ordinal = 0

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        limitations.append(f"transcript unreadable: {e}")
        return SessionTimeline(
            session_id=session_id,
            events=[],
            sources=[],
            limitations=limitations,
        )

    for line_num, line in enumerate(lines, 1):
        parsed = parse_transcript_line(line)
        if parsed is None:
            continue
        start, end, text = parsed
        if not text:
            continue

        ordinal += 1
        if ordinal > max_events:
            limitations.append(f"truncated at {max_events} events")
            break

        events.append(TimelineEvent(
            ordinal=ordinal,
            event_type="transcript_segment",
            content=text,
            source=str(path.name),
            source_type=SourceType.PRIMARY_SEQUENTIAL,
            source_position=f"line:{line_num}",
            occurred_at=start,  # Whisper audio timestamp, not wall-clock
            session_id=session_id,
            metadata={"whisper_start": start, "whisper_end": end},
        ))

    sources = [{
        "source_id": str(path.name),
        "source_type": SourceType.PRIMARY_SEQUENTIAL,
        "session_id": session_id,
        "contemporaneous": True,
        "has_internal_order": True,
        "has_timestamps": True,
        "line_count": len(lines),
        "event_count": len(events),
    }]

    return SessionTimeline(
        session_id=session_id,
        events=events,
        sources=sources,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
#  Session-records.json parser (POSTHOC)
# ---------------------------------------------------------------------------

def build_timeline_from_session_records(
    records_path: str | Path,
    session_id: int,
) -> SessionTimeline:
    """
    Build a timeline from the curated session-records.json manifest.

    All events are classified as POSTHOC_SUMMARY — they represent
    interpretations created after the session, not raw evidence.

    Each category (participants, locations, discoveries, etc.) becomes
    a separate event with ordinal based on file order.
    """
    import json

    path = Path(records_path)
    limitations: list[str] = []
    events: list[TimelineEvent] = []
    posthoc_excluded: list[str] = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        limitations.append(f"session-records unreadable: {e}")
        return SessionTimeline(
            session_id=session_id,
            events=[],
            sources=[],
            limitations=limitations,
        )

    sessions = data.get("sessions", [])
    target = None
    for s in sessions:
        if isinstance(s, dict) and s.get("session_number") == session_id:
            target = s
            break

    if target is None:
        limitations.append(f"session {session_id} not found in records")
        return SessionTimeline(
            session_id=session_id,
            events=[],
            sources=[],
            limitations=limitations,
        )

    ordinal = 0

    # Each narrative category becomes a POSTHOC event
    for category in ["participants", "locations", "missions", "discoveries",
                      "world_events", "character_events", "open_threads"]:
        items = target.get(category, [])
        if not isinstance(items, list):
            continue
        for item in items:
            ordinal += 1
            if isinstance(item, dict):
                title = item.get("title", item.get("name", str(item)))
                desc = item.get("description", "")
            else:
                title = str(item)
                desc = ""
            events.append(TimelineEvent(
                ordinal=ordinal,
                event_type=f"posthoc_{category}",
                content=f"{title}: {desc}" if desc else title,
                source=str(path.name),
                source_type=SourceType.POSTHOC_SUMMARY,
                source_position=f"session.{category}",
                session_id=session_id,
                metadata={"category": category, "item": item},
            ))
            posthoc_excluded.append(f"session.{category}.{ordinal}")

    # Session-level summaries
    for field_name in ["public_summary", "public_chronicle", "gm_summary"]:
        value = target.get(field_name)
        if value:
            ordinal += 1
            events.append(TimelineEvent(
                ordinal=ordinal,
                event_type=f"posthoc_{field_name}",
                content=value,
                source=str(path.name),
                source_type=SourceType.POSTHOC_SUMMARY,
                source_position=f"session.{field_name}",
                session_id=session_id,
                metadata={"field": field_name},
            ))
            posthoc_excluded.append(f"session.{field_name}")

    sources = [{
        "source_id": str(path.name),
        "source_type": SourceType.POSTHOC_SUMMARY,
        "session_id": session_id,
        "contemporaneous": False,
        "has_internal_order": False,
        "has_timestamps": False,
        "event_count": len(events),
    }]

    return SessionTimeline(
        session_id=session_id,
        events=events,
        sources=sources,
        limitations=limitations,
        posthoc_excluded=posthoc_excluded,
    )


# ---------------------------------------------------------------------------
#  Runtime events from scene_events table
# ---------------------------------------------------------------------------

def build_timeline_from_scene_events(
    scene_events: list[dict[str, Any]],
    session_id: int,
) -> SessionTimeline:
    """
    Build a timeline from scene_events (runtime records).

    Events are ordered by id (creation order) and classified as RUNTIME_RECORD.
    """
    limitations: list[str] = []
    events: list[TimelineEvent] = []

    # Sort by id for stable ordering
    sorted_events = sorted(scene_events, key=lambda e: e.get("id", 0))

    for idx, ev in enumerate(sorted_events, 1):
        created_at = ev.get("created_at")
        events.append(TimelineEvent(
            ordinal=idx,
            event_type=ev.get("event_type", "unknown"),
            content=ev.get("title", ""),
            source="scene_events",
            source_type=SourceType.RUNTIME_RECORD,
            source_position=f"event_id:{ev.get('id')}",
            occurred_at=None,  # created_at is when it was recorded, not necessarily when it happened
            recorded_at=created_at,
            session_id=session_id,
            metadata={"scene_id": ev.get("scene_id"), "event_id": ev.get("id")},
        ))

    if not events:
        limitations.append("no scene_events found for this session")

    sources = [{
        "source_id": "scene_events",
        "source_type": SourceType.RUNTIME_RECORD,
        "session_id": session_id,
        "contemporaneous": True,
        "has_internal_order": True,
        "has_timestamps": True,
        "event_count": len(events),
    }]

    return SessionTimeline(
        session_id=session_id,
        events=events,
        sources=sources,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
#  Merged timeline
# ---------------------------------------------------------------------------

def build_session_timeline(
    *,
    session_id: int,
    transcript_path: str | Path | None = None,
    session_records_path: str | Path | None = None,
    scene_events: list[dict[str, Any]] | None = None,
) -> SessionTimeline:
    """
    Build a merged session timeline from available sources.

    Source priority for ordering:
    1. Transcript (PRIMARY_SEQUENTIAL) — most reliable
    2. Scene events (RUNTIME_RECORD) — second most reliable
    3. Session records (POSTHOC_SUMMARY) — least reliable for ordering

    All sources are included but clearly classified.
    """
    all_events: list[TimelineEvent] = []
    all_sources: list[dict[str, Any]] = []
    all_limitations: list[str] = []
    all_posthoc: list[str] = []
    max_ordinal = 0

    # 1. Transcript — PRIMARY_SEQUENTIAL
    if transcript_path:
        tl = build_timeline_from_transcript(transcript_path, session_id)
        all_events.extend(tl.events)
        all_sources.extend(tl.sources)
        all_limitations.extend(tl.limitations)
        max_ordinal = max(max_ordinal, tl.max_ordinal)

    # 2. Scene events — RUNTIME_RECORD
    if scene_events:
        tl = build_timeline_from_scene_events(scene_events, session_id)
        # Offset ordinals to avoid collision
        for ev in tl.events:
            max_ordinal += 1
            all_events.append(TimelineEvent(
                ordinal=max_ordinal,
                event_type=ev.event_type,
                content=ev.content,
                source=ev.source,
                source_type=ev.source_type,
                source_position=ev.source_position,
                occurred_at=ev.occurred_at,
                recorded_at=ev.recorded_at,
                imported_at=ev.imported_at,
                session_id=ev.session_id,
                metadata=ev.metadata,
            ))
        all_sources.extend(tl.sources)
        all_limitations.extend(tl.limitations)

    # 3. Session records — POSTHOC_SUMMARY
    if session_records_path:
        tl = build_timeline_from_session_records(session_records_path, session_id)
        for ev in tl.events:
            max_ordinal += 1
            all_events.append(TimelineEvent(
                ordinal=max_ordinal,
                event_type=ev.event_type,
                content=ev.content,
                source=ev.source,
                source_type=ev.source_type,
                source_position=ev.source_position,
                occurred_at=ev.occurred_at,
                recorded_at=ev.recorded_at,
                imported_at=ev.imported_at,
                session_id=ev.session_id,
                metadata=ev.metadata,
            ))
        all_sources.extend(tl.sources)
        all_limitations.extend(tl.limitations)
        all_posthoc.extend(tl.posthoc_excluded)

    # Deduplicate posthoc exclusions
    all_posthoc = list(dict.fromkeys(all_posthoc))

    if not all_events:
        all_limitations.append(f"no timeline sources found for session {session_id}")

    return SessionTimeline(
        session_id=session_id,
        events=all_events,
        sources=all_sources,
        limitations=all_limitations,
        posthoc_excluded=all_posthoc,
    )


# ---------------------------------------------------------------------------
#  Cutoff helpers
# ---------------------------------------------------------------------------

def filter_events_by_cutoff(
    events: list[TimelineEvent],
    *,
    cutoff_ordinal: int | None = None,
    cutoff_scene_id: int | None = None,
    cutoff_timestamp: str | None = None,
) -> tuple[list[TimelineEvent], list[TimelineEvent], list[str]]:
    """
    Filter events by cutoff criteria.
    Returns (included, excluded, exclusion_reasons).
    """
    included = []
    excluded = []
    reasons = []

    for e in events:
        exclude = False
        reason = ""

        if cutoff_ordinal is not None and e.ordinal > cutoff_ordinal:
            exclude = True
            reason = f"ordinal {e.ordinal} > cutoff {cutoff_ordinal}"

        if cutoff_scene_id is not None:
            scene_id = e.metadata.get("scene_id")
            if scene_id is not None and scene_id > cutoff_scene_id:
                exclude = True
                reason = f"scene_id {scene_id} > cutoff {cutoff_scene_id}"

        if cutoff_timestamp and e.recorded_at and e.recorded_at > cutoff_timestamp:
            exclude = True
            reason = f"recorded_at {e.recorded_at} > cutoff {cutoff_timestamp}"

        if exclude:
            excluded.append(e)
            reasons.append(reason)
        else:
            included.append(e)

    return included, excluded, reasons
