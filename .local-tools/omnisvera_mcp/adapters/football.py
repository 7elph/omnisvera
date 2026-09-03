"""Football World Adapter v0.2

Second real world connected to Omnisvera MCP via the Universal World Contract.
Proves that a domain semantically different from RPG can use the same
observation → snapshot → prediction → resolution cycle without any
modification to the Epistemic Core.

All football semantics live here. The Core only sees WorldObservation.

v0.2: HttpFootballDataProvider — real external data via TheSportsDB.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

from ..world import WorldDescriptor, WorldObservation, WorldSignal, utc_now

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Data Provider — interface for match data
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class MatchData:
    """Raw match data from any provider. Schema-agnostic to provider."""
    match_id: str
    status: str  # "scheduled", "live", "completed", "postponed", "cancelled"
    competition: str
    match_date: str  # ISO date
    home_id: str
    home_name: str
    away_id: str
    away_name: str
    home_score: int | None = None
    away_score: int | None = None
    venue: str | None = None
    referee: str | None = None
    minute: int | None = None  # current minute if live
    signals: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@runtime_checkable
class FootballDataProvider(Protocol):
    """Protocol for football data providers."""

    def list_matches(
        self, *, competition: str | None = None, status: str | None = None,
        limit: int = 20,
    ) -> list[MatchData]:
        """Return available matches, optionally filtered."""
        ...

    def get_match(self, match_id: str) -> MatchData | None:
        """Return a single match by ID."""
        ...


# ---------------------------------------------------------------------------
#  Fake Provider — deterministic, no external dependencies
# ---------------------------------------------------------------------------

class FakeFootballDataProvider:
    """In-memory provider for tests. Pre-loaded with realistic fixture data."""

    def __init__(self) -> None:
        self._matches: dict[str, MatchData] = {}
        self._load_fixtures()

    def _load_fixtures(self) -> None:
        fixtures = [
            MatchData(
                match_id="FUT-001",
                status="scheduled",
                competition="Premier League",
                match_date="2026-09-15T15:00:00Z",
                home_id="team-ars",
                home_name="Arsenal",
                away_id="team-che",
                away_name="Chelsea",
                venue="Emirates Stadium",
                referee="Michael Oliver",
            ),
            MatchData(
                match_id="FUT-002",
                status="scheduled",
                competition="Premier League",
                match_date="2026-09-15T17:30:00Z",
                home_id="team-mci",
                home_name="Manchester City",
                away_id="team-liv",
                away_name="Liverpool",
                venue="Etihad Stadium",
                referee="Anthony Taylor",
            ),
            MatchData(
                match_id="FUT-003",
                status="completed",
                competition="Premier League",
                match_date="2026-08-30T15:00:00Z",
                home_id="team-ars",
                home_name="Arsenal",
                away_id="team-mun",
                away_name="Manchester United",
                home_score=2,
                away_score=1,
                venue="Emirates Stadium",
                referee="Stuart Attwell",
            ),
            MatchData(
                match_id="FUT-004",
                status="scheduled",
                competition="La Liga",
                match_date="2026-09-16T20:00:00Z",
                home_id="team-rma",
                home_name="Real Madrid",
                away_id="team-bar",
                away_name="Barcelona",
                venue="Santiago Bernabéu",
                referee="Mateu Lahoz",
            ),
        ]
        for m in fixtures:
            self._matches[m.match_id] = m

    def list_matches(
        self, *, competition: str | None = None, status: str | None = None,
        limit: int = 20,
    ) -> list[MatchData]:
        results = list(self._matches.values())
        if competition:
            results = [m for m in results if m.competition == competition]
        if status:
            results = [m for m in results if m.status == status]
        return results[:limit]

    def get_match(self, match_id: str) -> MatchData | None:
        return self._matches.get(match_id)

    def complete_match(
        self, match_id: str, home_score: int, away_score: int,
    ) -> MatchData | None:
        """Simulate match completion (for testing temporal separation)."""
        m = self._matches.get(match_id)
        if m is None:
            return None
        completed = MatchData(
            match_id=m.match_id,
            status="completed",
            competition=m.competition,
            match_date=m.match_date,
            home_id=m.home_id,
            home_name=m.home_name,
            away_id=m.away_id,
            away_name=m.away_name,
            home_score=home_score,
            away_score=away_score,
            venue=m.venue,
            referee=m.referee,
        )
        self._matches[match_id] = completed
        return completed


# ---------------------------------------------------------------------------
#  HTTP Provider — real external data via TheSportsDB
# ---------------------------------------------------------------------------

# TheSportsDB status codes → our normalized statuses
_STATUS_MAP = {
    "NS": "scheduled",    # Not Started
    "TBD": "scheduled",   # Time To Be Defined
    "1H": "live",         # First Half
    "HT": "live",         # Half Time
    "2H": "live",         # Second Half
    "ET": "live",         # Extra Time
    "P": "live",          # Penalty Shootout
    "FT": "completed",    # Full Time
    "AET": "completed",   # After Extra Time
    "PEN": "completed",   # After Penalties
    "PST": "postponed",   # Postponed
    "CANC": "cancelled",  # Cancelled
    "AWD": "completed",   # Awarded (walkover)
    "WO": "completed",    # Walkover
}

# Fields that contain future information — stripped from non-completed matches
_FUTURE_FIELDS = ("intHomeScore", "intAwayScore", "strResult", "strProgress")


@dataclass(frozen=True, slots=True)
class ProviderStatus:
    """Operational status of a data provider."""
    state: str  # "healthy", "degraded", "unconfigured", "offline"
    message: str = ""
    last_success: float | None = None  # timestamp of last successful fetch
    consecutive_failures: int = 0


class HttpFootballDataProvider:
    """Real football data provider using TheSportsDB free API.

    No API key required for basic endpoints. Team IDs must be configured
    via constructor — the provider does not discover teams.

    Operational states:
      - healthy: last fetch succeeded
      - degraded: some fetches failed but recent ones succeeded
      - unconfigured: no team IDs provided
      - offline: all recent fetches failed
    """

    BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"
    REQUEST_TIMEOUT = 10  # seconds

    def __init__(
        self,
        team_ids: list[str] | None = None,
        *,
        requester: Any = None,
    ) -> None:
        self._team_ids = list(team_ids or [])
        self._requester = requester  # injectable for testing
        self._match_cache: dict[str, MatchData] = {}
        self._status = ProviderStatus(
            state="unconfigured" if not self._team_ids else "healthy",
            message="" if self._team_ids else "no team IDs configured",
        )
        self._last_fetch_time: float | None = None

    @property
    def status(self) -> ProviderStatus:
        return self._status

    def _request(self, url: str) -> dict[str, Any]:
        """Make HTTP request. Raises on failure."""
        if self._requester is not None:
            return self._requester(url)
        import urllib.request
        import json as _json
        req = urllib.request.Request(url, headers={"User-Agent": "Omnisvera/1.0"})
        with urllib.request.urlopen(req, timeout=self.REQUEST_TIMEOUT) as resp:
            return _json.loads(resp.read().decode())

    def _fetch_team_next(self, team_id: str) -> list[dict[str, Any]]:
        """Fetch upcoming events for a team from TheSportsDB."""
        url = f"{self.BASE_URL}/eventsnext.php?id={team_id}"
        data = self._request(url)
        return data.get("events", []) or []

    def _fetch_team_last(self, team_id: str) -> list[dict[str, Any]]:
        """Fetch last events for a team from TheSportsDB."""
        url = f"{self.BASE_URL}/eventslast.php?id={team_id}"
        data = self._request(url)
        return data.get("results", []) or data.get("events", []) or []

    def _fetch_event(self, event_id: str) -> dict[str, Any] | None:
        """Fetch single event detail."""
        url = f"{self.BASE_URL}/lookupevent.php?id={event_id}"
        data = self._request(url)
        events = data.get("events", []) or []
        return events[0] if events else None

    def _normalize_status(self, raw_status: str | None) -> str:
        """Map TheSportsDB status to our normalized status."""
        if raw_status is None:
            return "scheduled"
        return _STATUS_MAP.get(raw_status.upper(), "scheduled")

    def _parse_event(self, event: dict[str, Any]) -> MatchData:
        """Parse TheSportsDB event into MatchData."""
        raw_status = event.get("strStatus", "NS")
        status = self._normalize_status(raw_status)

        # Extract scores — only valid for completed/live matches
        home_score = None
        away_score = None
        if status in ("completed", "live"):
            try:
                hs = event.get("intHomeScore")
                aws = event.get("intAwayScore")
                if hs is not None:
                    home_score = int(hs)
                if aws is not None:
                    away_score = int(aws)
            except (ValueError, TypeError):
                pass

        # Extract minute for live matches
        minute = None
        if status == "live":
            progress = event.get("strProgress", "")
            try:
                minute = int(progress.replace("'", "").replace("+", "").strip())
            except (ValueError, TypeError):
                pass

        # Build MatchData
        event_id = event.get("idEvent", "")
        return MatchData(
            match_id=f"TSDB-{event_id}" if event_id else "TSDB-unknown",
            status=status,
            competition=event.get("strLeague", "Unknown"),
            match_date=event.get("strTimestamp", event.get("dateEvent", "")),
            home_id=event.get("idHomeTeam", ""),
            home_name=event.get("strHomeTeam", "Unknown"),
            away_id=event.get("idAwayTeam", ""),
            away_name=event.get("strAwayTeam", "Unknown"),
            home_score=home_score,
            away_score=away_score,
            venue=event.get("strVenue"),
            referee=event.get("strOfficial"),
            minute=minute,
            signals={
                "source_event_id": event_id,
                "source_league_id": event.get("idLeague", ""),
                "round": event.get("intRound"),
                "thumb": event.get("strThumb"),
            },
        )

    def _record_success(self) -> None:
        """Record a successful fetch."""
        now = time.time()
        self._last_fetch_time = now
        failures = self._status.consecutive_failures
        self._status = ProviderStatus(
            state="healthy" if failures == 0 else "degraded",
            message=f"recovered after {failures} failures" if failures else "",
            last_success=now,
            consecutive_failures=0,
        )

    def _record_failure(self, error: Exception) -> None:
        """Record a failed fetch."""
        failures = self._status.consecutive_failures + 1
        state = "offline" if failures >= 3 else "degraded"
        self._status = ProviderStatus(
            state=state,
            message=f"fetch failed: {error}",
            last_success=self._status.last_success,
            consecutive_failures=failures,
        )

    def list_matches(
        self, *, competition: str | None = None, status: str | None = None,
        limit: int = 20,
    ) -> list[MatchData]:
        """Fetch matches from all configured teams, merge, filter."""
        if not self._team_ids:
            return []

        all_events: list[dict[str, Any]] = []
        for team_id in self._team_ids:
            try:
                events = self._fetch_team_next(team_id)
                all_events.extend(events)
                # Also fetch last events for completed matches
                last_events = self._fetch_team_last(team_id)
                all_events.extend(last_events)
                self._record_success()
            except Exception as e:
                logger.warning("Failed to fetch data for team %s: %s", team_id, e)
                self._record_failure(e)

        # Deduplicate by event ID
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for ev in all_events:
            eid = ev.get("idEvent", "")
            if eid and eid not in seen:
                seen.add(eid)
                unique.append(ev)

        # Parse and cache
        matches: list[MatchData] = []
        for ev in unique:
            md = self._parse_event(ev)
            self._match_cache[md.match_id] = md
            matches.append(md)

        # Filter
        if competition:
            matches = [m for m in matches if m.competition == competition]
        if status:
            matches = [m for m in matches if m.status == status]

        return matches[:limit]

    def get_match(self, match_id: str) -> MatchData | None:
        """Get a single match. Uses cache if available, otherwise fetches."""
        if match_id in self._match_cache:
            return self._match_cache[match_id]

        # Extract original event ID from our prefixed ID
        raw_id = match_id.removeprefix("TSDB-")
        if raw_id == match_id:
            return None  # Not a TSDB-prefixed ID

        try:
            event = self._fetch_event(raw_id)
            if event:
                md = self._parse_event(event)
                self._match_cache[md.match_id] = md
                self._record_success()
                return md
        except Exception as e:
            logger.warning("Failed to fetch event %s: %s", raw_id, e)
            self._record_failure(e)

        return None


# ---------------------------------------------------------------------------
#  Football World Adapter
# ---------------------------------------------------------------------------

class FootballWorldAdapter:
    """WorldAdapter for football data.

    Proves the Universal World Contract works for a domain with:
    - numeric data
    - temporal series
    - objective events
    - fast resolution cycles

    Zero RPG concepts. Zero Companion coupling.
    """

    WORLD_ID = "football"
    WORLD_TYPE = "sports.football"
    ADAPTER_ID = "football.data.v1"

    def __init__(self, provider: FootballDataProvider | None = None) -> None:
        self._provider = provider or FakeFootballDataProvider()

    def describe(self) -> WorldDescriptor:
        metadata: dict[str, Any] = {"provider": type(self._provider).__name__}
        if isinstance(self._provider, HttpFootballDataProvider):
            status = self._provider.status
            metadata["provider_state"] = status.state
            metadata["provider_message"] = status.message
        return WorldDescriptor(
            world_id=self.WORLD_ID,
            world_type=self.WORLD_TYPE,
            name="Football World",
            adapter_id=self.ADAPTER_ID,
            capabilities=["observe", "history", "model"],
            schemas=["football.match.v1"],
            metadata=metadata,
        )

    def health(self) -> dict[str, Any]:
        if isinstance(self._provider, HttpFootballDataProvider):
            status = self._provider.status
            return {
                "status": status.state,
                "freshness": "fresh" if status.state == "healthy" else "stale",
                "provider": type(self._provider).__name__,
                "message": status.message,
                "last_success": status.last_success,
                "consecutive_failures": status.consecutive_failures,
            }
        return {"status": "healthy", "freshness": "fresh", "provider": type(self._provider).__name__}

    def observe(self, query: dict[str, Any] | None = None) -> WorldObservation:
        """Observe football world state.

        Query options:
          - match_id: return single match state
          - competition: filter by competition
          - status: filter by match status

        Temporal protection: scheduled matches never include final_score,
        winner, or post_match_stats. Completed matches never appear as scheduled.
        """
        match_id = (query or {}).get("match_id")
        competition = (query or {}).get("competition")
        status = (query or {}).get("status")

        if match_id:
            match = self._provider.get_match(match_id)
            if match is None:
                state = {"matches": [], "query": query, "limitation": f"match {match_id} not found"}
            else:
                state = {"matches": [self._safe_match_state(match)]}
        else:
            matches = self._provider.list_matches(
                competition=competition, status=status, limit=50,
            )
            state = {"matches": [self._safe_match_state(m) for m in matches]}

        provenance: dict[str, Any] = {
            "adapter": self.ADAPTER_ID,
            "provider": type(self._provider).__name__,
        }
        if isinstance(self._provider, HttpFootballDataProvider):
            status = self._provider.status
            provenance["provider_state"] = status.state
            provenance["provider_last_success"] = status.last_success
            provenance["freshness_seconds"] = (
                time.time() - status.last_success if status.last_success else None
            )

        return WorldObservation(
            world_id=self.WORLD_ID,
            observed_at=utc_now(),
            schema="football.match.v1",
            state=state,
            sources=[{"source_type": "football_data", "source_ref": self.ADAPTER_ID}],
            provenance=provenance,
        )

    def signals(self, observation: WorldObservation | None = None) -> list[WorldSignal]:
        """Extract universal signals from football state.

        If no observation is provided, observes first.
        Signals are derived deterministically from the observation state.
        Each match produces its own set of signals with entity_ref.
        """
        if observation is None:
            observation = self.observe()

        state = observation.state
        matches = state.get("matches", [])
        signals: list[WorldSignal] = []
        observed_at = observation.observed_at

        # football.observation.match_count — number of matches in this observation
        signals.append(WorldSignal(
            signal_id="football.observation.match_count",
            world_id=self.WORLD_ID,
            schema=observation.schema,
            name="match_count",
            value=len(matches),
            value_type="number",
            observed_at=observed_at,
            unit="count",
            source={"observation_world_id": observation.world_id, "derivation": "deterministic"},
            metadata={"derivation": "len(matches)"},
        ))

        # Per-match signals
        for match in matches:
            match_id = match.get("match_id", "unknown")
            entity_ref = f"match:{match_id}"

            # football.match.status — categorical
            status = match.get("status")
            if status is not None:
                signals.append(WorldSignal(
                    signal_id="football.match.status",
                    world_id=self.WORLD_ID,
                    schema=observation.schema,
                    name="match_status",
                    value=status,
                    value_type="categorical",
                    observed_at=observed_at,
                    entity_ref=entity_ref,
                    source={"observation_world_id": observation.world_id, "derivation": "direct"},
                    metadata={"field": "status", "home": match.get("home", {}).get("name"), "away": match.get("away", {}).get("name")},
                ))

            # football.match.date — datetime
            match_date = match.get("match_date")
            if match_date:
                signals.append(WorldSignal(
                    signal_id="football.match.date",
                    world_id=self.WORLD_ID,
                    schema=observation.schema,
                    name="match_date",
                    value=match_date,
                    value_type="datetime",
                    observed_at=observed_at,
                    entity_ref=entity_ref,
                    source={"observation_world_id": observation.world_id, "derivation": "direct"},
                    metadata={"field": "match_date"},
                ))

            # football.match.home_score — number (only when known)
            home_score = match.get("home_score")
            if home_score is not None:
                signals.append(WorldSignal(
                    signal_id="football.match.home_score",
                    world_id=self.WORLD_ID,
                    schema=observation.schema,
                    name="home_score",
                    value=home_score,
                    value_type="number",
                    observed_at=observed_at,
                    entity_ref=entity_ref,
                    unit="goals",
                    source={"observation_world_id": observation.world_id, "derivation": "direct"},
                    metadata={"field": "home_score"},
                ))

            # football.match.away_score — number (only when known)
            away_score = match.get("away_score")
            if away_score is not None:
                signals.append(WorldSignal(
                    signal_id="football.match.away_score",
                    world_id=self.WORLD_ID,
                    schema=observation.schema,
                    name="away_score",
                    value=away_score,
                    value_type="number",
                    observed_at=observed_at,
                    entity_ref=entity_ref,
                    unit="goals",
                    source={"observation_world_id": observation.world_id, "derivation": "direct"},
                    metadata={"field": "away_score"},
                ))

        # football.provider.freshness — number (seconds since last success)
        freshness = observation.provenance.get("freshness_seconds")
        if freshness is not None:
            signals.append(WorldSignal(
                signal_id="football.provider.freshness",
                world_id=self.WORLD_ID,
                schema=observation.schema,
                name="provider_freshness",
                value=freshness,
                value_type="number",
                observed_at=observed_at,
                unit="seconds",
                source={"observation_world_id": observation.world_id, "derivation": "deterministic"},
                metadata={"field": "provenance.freshness_seconds"},
            ))

        return signals

    def _safe_match_state(self, match: MatchData) -> dict[str, Any]:
        """Return match state with temporal protection.

        Scheduled/live matches NEVER include results.
        Completed matches include scores but are never served as scheduled.
        """
        base = {
            "match_id": match.match_id,
            "status": match.status,
            "competition": match.competition,
            "match_date": match.match_date,
            "home": {"id": match.home_id, "name": match.home_name},
            "away": {"id": match.away_id, "name": match.away_name},
            "venue": match.venue,
            "referee": match.referee,
        }
        if match.status == "live":
            base["minute"] = match.minute
        if match.status == "completed":
            base["home_score"] = match.home_score
            base["away_score"] = match.away_score
            base["result"] = {
                "home_score": match.home_score,
                "away_score": match.away_score,
                "winner": (
                    "home" if (match.home_score or 0) > (match.away_score or 0)
                    else "away" if (match.away_score or 0) > (match.home_score or 0)
                    else "draw"
                ),
            }
        if match.signals:
            base["signals"] = match.signals
        return base
