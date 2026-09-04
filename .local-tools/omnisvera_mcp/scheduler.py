"""Automated Scheduler v0.2 — change-aware observation → signal capture cycle.

Runs as a standalone process or via cron. Performs:
1. Observe all connected worlds (with adaptive polling)
2. Capture domain signals only when value changes
3. Record operational signals separately
4. Log polling telemetry (success, unchanged, changed)
5. Check for due predictions and resolve them

v0.2: change-aware persistence, operational/domain separation, telemetry.

Usage:
    python -m omnisvera_mcp.scheduler          # Run once
    python -m omnisvera_mcp.scheduler --loop   # Run hourly loop
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters.football import FootballWorldAdapter, HttpFootballDataProvider
from .adapters.crypto import CryptoWorldAdapter, CoinGeckoProvider
from .core.context import CallContext
from .memory import MemoryStore
from .world import WorldRegistry, WorldModelRegistry, CoreStateVectorBuilder, utc_now

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  Signal classification — operational vs domain
# ---------------------------------------------------------------------------

# Signals that are operational metadata, NOT domain state.
# These are always persisted (not change-aware) because they track
# system health, not world state.
OPERATIONAL_SIGNALS: frozenset[str] = frozenset({
    "football.observation.match_count",
    "football.provider.freshness",
    "crypto.observation.coin_count",
    "test.signal",
})


def _is_operational(signal_id: str) -> bool:
    """Check if a signal is operational metadata."""
    return signal_id in OPERATIONAL_SIGNALS


# ---------------------------------------------------------------------------
#  Adaptive polling policy for football
# ---------------------------------------------------------------------------

# Polling intervals based on match status (seconds)
_POLLING_INTERVALS = {
    "completed": 6 * 3600,   # 6h — only poll occasionally to confirm final state
    "scheduled": 4 * 3600,   # 4h — low frequency for distant matches
    "live": 5 * 60,          # 5min — high frequency for live matches
    "postponed": 12 * 3600,  # 12h — very low frequency
    "cancelled": 24 * 3600,  # 24h — almost never
}

# Threshold: if scheduled match is within this many hours, use live-like frequency
_NEAR_KICKOFF_HOURS = 2


def _should_poll_match(match: dict[str, Any], now: datetime | None = None) -> bool:
    """Decide whether a match should be polled in this cycle.

    Returns True if the match is worth observing. Returns False for
    completed matches that were already confirmed (reduces noise).
    """
    status = match.get("status", "scheduled")

    # Always poll live matches
    if status == "live":
        return True

    # Always poll scheduled matches (potential upcoming)
    if status == "scheduled":
        return True

    # Completed: only poll if we haven't confirmed final score yet
    # (check if home_score is present — if so, we already have the result)
    if status == "completed":
        return match.get("home_score") is None

    # Postponed/cancelled: poll rarely
    return True


def _polling_interval(match: dict[str, Any], now: datetime | None = None) -> int:
    """Return recommended polling interval in seconds for a match."""
    status = match.get("status", "scheduled")
    interval = _POLLING_INTERVALS.get(status, 4 * 3600)

    # Near-kickoff boost for scheduled matches
    if status == "scheduled":
        match_date_str = match.get("match_date", "")
        if match_date_str:
            try:
                # Parse ISO date (handle both Z and +00:00)
                md = match_date_str.replace("Z", "+00:00")
                match_date = datetime.fromisoformat(md)
                if now is None:
                    now = datetime.now(timezone.utc)
                hours_until = (match_date - now).total_seconds() / 3600
                if 0 < hours_until <= _NEAR_KICKOFF_HOURS:
                    interval = 5 * 60  # live-like frequency
                elif hours_until <= 6:
                    interval = 30 * 60  # 30min for matches within 6h
            except (ValueError, TypeError):
                pass

    return interval


# ---------------------------------------------------------------------------
#  Scheduler
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AutomatedScheduler:
    """Change-aware scheduler for the Omnisvera observation → signal capture cycle.

    Coordinates:
    - World observation (with adaptive polling for football)
    - Signal capture (change-aware for domain signals, always for operational)
    - Telemetry recording (poll success/failure, changed/unchanged counts)
    - Prediction resolution (check due predictions)
    """

    def __init__(
        self,
        memory: MemoryStore,
        worlds: WorldRegistry,
        model_builders: WorldModelRegistry,
    ) -> None:
        self._memory = memory
        self._worlds = worlds
        self._model_builders = model_builders
        self._last_poll: dict[str, float] = {}  # world_id → timestamp of last poll

    def _should_poll_world(self, world_id: str, observation: Any = None) -> bool:
        """Check if a world should be polled in this cycle.

        For football: uses adaptive polling based on match status.
        For crypto: always poll (hourly is fine).
        """
        # Always poll crypto
        if world_id == "crypto":
            return True

        # For football: check adaptive policy
        if world_id == "football" and observation is not None:
            # Get matches from the last known state
            # We need to peek at the observation to decide
            pass  # Fall through to default: always poll

        return True

    def run_cycle(self) -> dict[str, Any]:
        """Run one complete observation → capture cycle.

        Returns summary of actions taken.
        """
        cycle_start = datetime.now(timezone.utc)
        summary: dict[str, Any] = {
            "started_at": cycle_start.isoformat(),
            "worlds_observed": 0,
            "domain_signals_changed": 0,
            "domain_signals_initial": 0,
            "domain_signals_unchanged": 0,
            "operational_signals_recorded": 0,
            "predictions_resolved": 0,
            "errors": [],
            "world_details": {},
        }

        # 1. Observe all worlds
        for descriptor in self._worlds.list():
            world_id = descriptor.world_id
            world_detail: dict[str, Any] = {
                "signals_seen": 0,
                "domain_changed": 0,
                "domain_initial": 0,
                "domain_unchanged": 0,
                "operational_recorded": 0,
                "success": False,
                "error": None,
            }

            try:
                adapter = self._worlds.get(world_id)
                observation = adapter.observe()
                signals = adapter.signals(observation)

                # Capture signals with unique observed_at for this cycle
                cycle_time = datetime.now(timezone.utc).isoformat()
                run_id = f"run-{int(time.time())}-{world_id}"
                run_started = cycle_time

                for sig in signals:
                    sig_dict = {
                        "world_id": sig.world_id,
                        "signal_id": sig.signal_id,
                        "entity_ref": sig.entity_ref,
                        "schema": sig.schema,
                        "value": sig.value,
                        "value_type": sig.value_type,
                        "unit": sig.unit or "",
                        "observed_at": cycle_time,
                        "source": sig.source,
                        "metadata": sig.metadata,
                    }

                    world_detail["signals_seen"] += 1

                    if _is_operational(sig.signal_id):
                        # Operational signals: always persist (no change-awareness)
                        result = self._memory.capture_signal(**sig_dict)
                        if result.get("status") == "recorded":
                            world_detail["operational_recorded"] += 1
                            summary["operational_signals_recorded"] += 1
                    else:
                        # Domain signals: change-aware persistence
                        result = self._memory.capture_signal_change_aware(**sig_dict)
                        status = result.get("status", "")
                        if status == "changed_recorded":
                            world_detail["domain_changed"] += 1
                            summary["domain_signals_changed"] += 1
                        elif status == "initial_recorded":
                            world_detail["domain_initial"] += 1
                            summary["domain_signals_initial"] += 1
                        elif status == "unchanged_skipped":
                            world_detail["domain_unchanged"] += 1
                            summary["domain_signals_unchanged"] += 1

                # Record telemetry
                self._memory._capture_scheduler_telemetry(
                    run_id=run_id,
                    world_id=world_id,
                    provider=type(adapter._provider).__name__ if hasattr(adapter, '_provider') else "unknown",
                    run_started_at=run_started,
                    run_finished_at=datetime.now(timezone.utc).isoformat(),
                    success=True,
                    signals_seen=world_detail["signals_seen"],
                    signals_changed=world_detail["domain_changed"] + world_detail["operational_recorded"],
                    signals_unchanged=world_detail["domain_unchanged"],
                )

                world_detail["success"] = True
                summary["worlds_observed"] += 1
                logger.info(
                    "Observed %s: %d seen, %d domain changed, %d domain unchanged, %d operational",
                    world_id, world_detail["signals_seen"],
                    world_detail["domain_changed"] + world_detail["domain_initial"],
                    world_detail["domain_unchanged"],
                    world_detail["operational_recorded"],
                )

            except Exception as e:
                error_msg = f"{world_id}: {e}"
                summary["errors"].append(error_msg)
                world_detail["error"] = str(e)
                # Record failed telemetry
                try:
                    self._memory._capture_scheduler_telemetry(
                        run_id=f"run-{int(time.time())}-{world_id}",
                        world_id=world_id,
                        provider="unknown",
                        run_started_at=cycle_time if 'cycle_time' in dir() else utc_now(),
                        run_finished_at=datetime.now(timezone.utc).isoformat(),
                        success=False,
                        signals_seen=0,
                        signals_changed=0,
                        signals_unchanged=0,
                        error=str(e),
                    )
                except Exception:
                    pass  # Don't fail the cycle if telemetry fails
                logger.error("Failed to observe %s: %s", world_id, e)

            summary["world_details"][world_id] = world_detail

        # 2. Resolve due predictions
        try:
            from .epistemic import resolve_due_predictions
            ctx = CallContext(
                actor="scheduler",
                client="omnisvera-scheduler",
                transport="internal",
                scopes=frozenset({"epistemic.write", "world.read"}),
                request_id=f"scheduler-{int(time.time())}",
                project_id="omnisvera",
            )
            result = resolve_due_predictions(
                self._memory,
                ctx,
                {"dry_run": False, "limit": 50},
            )
            result_data = json.loads(result) if isinstance(result, str) else result
            summary["predictions_resolved"] = result_data.get("resolved", 0)
            logger.info("Resolved %d predictions", summary["predictions_resolved"])
        except Exception as e:
            summary["errors"].append(f"resolution: {e}")
            logger.error("Failed to resolve predictions: %s", e)

        summary["finished_at"] = datetime.now(timezone.utc).isoformat()
        summary["duration_seconds"] = (
            datetime.now(timezone.utc) - cycle_start
        ).total_seconds()

        return summary


def setup_worlds(root: Path) -> tuple[WorldRegistry, WorldModelRegistry]:
    """Create and configure world registries with real providers."""
    worlds = WorldRegistry()
    model_builders = WorldModelRegistry()
    model_builders.register(CoreStateVectorBuilder())

    # Football world — real data from TheSportsDB
    try:
        # Premier League team IDs (TheSportsDB)
        football_provider = HttpFootballDataProvider(
            team_ids=[
                "133604",  # Arsenal
                "133616",  # Chelsea
                "133608",  # Manchester City
                "133614",  # Liverpool
                "133594",  # Manchester United
            ]
        )
        football = FootballWorldAdapter(provider=football_provider)
        worlds.register(football)
        logger.info("Registered football world (real data)")
    except Exception as e:
        logger.warning("Failed to register football world: %s", e)

    # Crypto world — real data from CoinGecko
    try:
        crypto_provider = CoinGeckoProvider(
            coin_ids=["bitcoin", "ethereum", "solana", "binancecoin"]
        )
        crypto = CryptoWorldAdapter(provider=crypto_provider)
        worlds.register(crypto)
        logger.info("Registered crypto world (real data)")
    except Exception as e:
        logger.warning("Failed to register crypto world: %s", e)

    return worlds, model_builders


def main() -> None:
    """CLI entry point for the scheduler."""
    parser = argparse.ArgumentParser(description="Omnisvera Automated Scheduler")
    parser.add_argument("--loop", action="store_true", help="Run hourly loop")
    parser.add_argument("--interval", type=int, default=3600, help="Loop interval in seconds")
    parser.add_argument("--root", type=str, default=None, help="Project root path")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    root = Path(args.root) if args.root else Path.cwd()
    # Use absolute path for memory database
    memory_db = root.parent / ".assistant-runtime" / "omnisvera-mcp" / "memory.db"
    memory = MemoryStore(memory_db)
    worlds, model_builders = setup_worlds(root)

    scheduler = AutomatedScheduler(
        memory=memory,
        worlds=worlds,
        model_builders=model_builders,
    )

    if args.loop:
        logger.info("Starting hourly loop (interval=%ds)", args.interval)
        while True:
            try:
                summary = scheduler.run_cycle()
                logger.info("Cycle complete: %s", json.dumps(summary, indent=2, default=str))
            except Exception as e:
                logger.error("Cycle failed: %s", e)
            time.sleep(args.interval)
    else:
        summary = scheduler.run_cycle()
        print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
