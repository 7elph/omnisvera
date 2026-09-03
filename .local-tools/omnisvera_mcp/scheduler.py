"""Automated Scheduler — hourly observation → signal capture cycle.

Runs as a standalone process or via cron. Performs:
1. Observe all connected worlds
2. Capture signals to memory
3. Check for due predictions and resolve them
4. Log all activity

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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AutomatedScheduler:
    """Hourly scheduler for the Omnisvera observation → signal capture cycle.

    Coordinates:
    - World observation (all registered worlds)
    - Signal capture (persist to memory)
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

    def run_cycle(self) -> dict[str, Any]:
        """Run one complete observation → capture cycle.

        Returns summary of actions taken.
        """
        cycle_start = datetime.now(timezone.utc)
        summary: dict[str, Any] = {
            "started_at": cycle_start.isoformat(),
            "worlds_observed": 0,
            "signals_captured": 0,
            "predictions_resolved": 0,
            "errors": [],
        }

        # 1. Observe all worlds
        for descriptor in self._worlds.list():
            world_id = descriptor.world_id
            try:
                adapter = self._worlds.get(world_id)
                observation = adapter.observe()
                signals = adapter.signals(observation)

                # Capture signals with unique observed_at for this cycle
                cycle_time = datetime.now(timezone.utc).isoformat()
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
                    result = self._memory.capture_signal(**sig_dict)
                    if result.get("status") == "recorded":
                        summary["signals_captured"] += 1

                summary["worlds_observed"] += 1
                logger.info("Observed %s: %d signals", world_id, len(signals))

            except Exception as e:
                error_msg = f"{world_id}: {e}"
                summary["errors"].append(error_msg)
                logger.error("Failed to observe %s: %s", world_id, e)

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
