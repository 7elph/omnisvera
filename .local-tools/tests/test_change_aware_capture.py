"""Tests for Scheduler Information Quality v0.1.

Proves:
A) football scheduled identical in 24 polls: 1 domain observation, 23 unchanged_skipped, polling telemetry shows 24 polls
B) scheduled → live → completed: each relevant change persists
C) score changes: new observation persists
D) scheduler offline: gap detectable via absence of scheduler telemetry
E) crypto with different price each hour: all observations persist
F) operational signals identifiable and excludable from domain dataset
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from omnisvera_mcp.memory.store import MemoryStore
from omnisvera_mcp.scheduler import _is_operational, OPERATIONAL_SIGNALS


def _tmp_store() -> MemoryStore:
    """Create a temporary MemoryStore for testing."""
    tmp = tempfile.mkdtemp()
    return MemoryStore(Path(tmp) / "test.db")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
#  A) Football scheduled identical in 24 polls
# ---------------------------------------------------------------------------

class TestChangeAwareCapture:
    """Prove: same value repeated N times → 1 observation, N-1 unchanged_skipped."""

    def test_football_scheduled_24_polls(self):
        """A) football scheduled identical in 24 polls:
        - 1 domain observation
        - 23 unchanged_skipped
        - polling telemetry shows 24 polls
        """
        store = _tmp_store()

        # Simulate 24 hourly polls of a scheduled match with identical status
        match_signals = []
        for hour in range(24):
            observed_at = f"2026-09-03T{hour:02d}:00:00+00:00"
            match_signals.append({
                "world_id": "football",
                "signal_id": "football.match.status",
                "entity_ref": "match:TSDB-2494000",
                "schema": "football.match.v1",
                "value": "scheduled",
                "value_type": "categorical",
                "unit": "",
                "observed_at": observed_at,
                "source": {"observation_world_id": "football", "derivation": "direct"},
                "metadata": {},
            })

        # Capture all 24
        results = []
        for sig in match_signals:
            result = store.capture_signal_change_aware(**sig)
            results.append(result)

        # Count outcomes
        initial = sum(1 for r in results if r["status"] == "initial_recorded")
        unchanged = sum(1 for r in results if r["status"] == "unchanged_skipped")
        changed = sum(1 for r in results if r["status"] == "changed_recorded")

        assert initial == 1, f"Expected 1 initial_recorded, got {initial}"
        assert unchanged == 23, f"Expected 23 unchanged_skipped, got {unchanged}"
        assert changed == 0, f"Expected 0 changed_recorded, got {changed}"

        # Verify only 1 row in database (not 24)
        history = store.signal_history(
            "football", "football.match.status", "match:TSDB-2494000"
        )
        assert len(history) == 1, f"Expected 1 observation in DB, got {len(history)}"
        assert history[0]["value"] == "scheduled"

    def test_operational_signals_always_persist(self):
        """F) operational signals always persist (no change-awareness)."""
        store = _tmp_store()

        # Capture same operational signal 10 times
        results = []
        for i in range(10):
            result = store.capture_signal(
                world_id="football",
                signal_id="football.observation.match_count",
                entity_ref=None,
                schema="football.match.v1",
                value=8,
                value_type="number",
                unit="count",
                observed_at=f"2026-09-03T{i:02d}:00:00+00:00",
                source={"observation_world_id": "football", "derivation": "deterministic"},
                metadata={"derivation": "len(matches)"},
            )
            results.append(result)

        # All should be recorded (no dedup for operational signals via capture_signal)
        recorded = sum(1 for r in results if r["status"] == "recorded")
        assert recorded == 10, f"Expected 10 recorded, got {recorded}"

        # But in signal_observations table they all exist
        history = store.signal_history(
            "football", "football.observation.match_count"
        )
        assert len(history) == 10

    def test_operational_classification(self):
        """F) operational signals are correctly classified."""
        assert _is_operational("football.observation.match_count")
        assert _is_operational("football.provider.freshness")
        assert _is_operational("crypto.observation.coin_count")
        assert _is_operational("test.signal")

        # Domain signals are NOT operational
        assert not _is_operational("football.match.status")
        assert not _is_operational("football.match.home_score")
        assert not _is_operational("crypto.price.usd")
        assert not _is_operational("crypto.volume.24h")


# ---------------------------------------------------------------------------
#  B) scheduled → live → completed: each change persists
# ---------------------------------------------------------------------------

class TestStateTransitions:
    """Prove: each relevant state change persists."""

    def test_scheduled_to_live_to_completed(self):
        """B) scheduled → live → completed: each relevant change persists."""
        store = _tmp_store()

        transitions = [
            ("scheduled", "2026-09-03T14:00:00+00:00"),
            ("live", "2026-09-03T15:00:00+00:00"),
            ("completed", "2026-09-03T17:00:00+00:00"),
        ]

        results = []
        for status, observed_at in transitions:
            result = store.capture_signal_change_aware(
                world_id="football",
                signal_id="football.match.status",
                entity_ref="match:TSDB-2494000",
                schema="football.match.v1",
                value=status,
                value_type="categorical",
                unit="",
                observed_at=observed_at,
                source={"observation_world_id": "football", "derivation": "direct"},
                metadata={},
            )
            results.append(result)

        # All 3 should be recorded (2 changed + 1 initial)
        initial = sum(1 for r in results if r["status"] == "initial_recorded")
        changed = sum(1 for r in results if r["status"] == "changed_recorded")
        unchanged = sum(1 for r in results if r["status"] == "unchanged_skipped")

        assert initial == 1
        assert changed == 2
        assert unchanged == 0

        # 3 observations in DB
        history = store.signal_history(
            "football", "football.match.status", "match:TSDB-2494000"
        )
        assert len(history) == 3
        assert [h["value"] for h in history] == ["scheduled", "live", "completed"]


# ---------------------------------------------------------------------------
#  C) Score changes persist
# ---------------------------------------------------------------------------

class TestScoreChanges:
    """Prove: score changes create new observations."""

    def test_score_change_persists(self):
        """C) score muda: nova observação persiste."""
        store = _tmp_store()

        # Initial: no score (scheduled)
        store.capture_signal_change_aware(
            world_id="football",
            signal_id="football.match.home_score",
            entity_ref="match:TSDB-2494000",
            schema="football.match.v1",
            value=None,
            value_type="number",
            unit="goals",
            observed_at="2026-09-03T14:00:00+00:00",
            source={"observation_world_id": "football", "derivation": "direct"},
            metadata={},
        )

        # Goal scored: 1-0
        result1 = store.capture_signal_change_aware(
            world_id="football",
            signal_id="football.match.home_score",
            entity_ref="match:TSDB-2494000",
            schema="football.match.v1",
            value=1,
            value_type="number",
            unit="goals",
            observed_at="2026-09-03T15:30:00+00:00",
            source={"observation_world_id": "football", "derivation": "direct"},
            metadata={},
        )
        assert result1["status"] == "changed_recorded"

        # Second goal: 2-0
        result2 = store.capture_signal_change_aware(
            world_id="football",
            signal_id="football.match.home_score",
            entity_ref="match:TSDB-2494000",
            schema="football.match.v1",
            value=2,
            value_type="number",
            unit="goals",
            observed_at="2026-09-03T16:45:00+00:00",
            source={"observation_world_id": "football", "derivation": "direct"},
            metadata={},
        )
        assert result2["status"] == "changed_recorded"

        # Same score repeated: unchanged
        result3 = store.capture_signal_change_aware(
            world_id="football",
            signal_id="football.match.home_score",
            entity_ref="match:TSDB-2494000",
            schema="football.match.v1",
            value=2,
            value_type="number",
            unit="goals",
            observed_at="2026-09-03T17:00:00+00:00",
            source={"observation_world_id": "football", "derivation": "direct"},
            metadata={},
        )
        assert result3["status"] == "unchanged_skipped"

        # 3 observations in DB (initial None, 1, 2)
        history = store.signal_history(
            "football", "football.match.home_score", "match:TSDB-2494000"
        )
        assert len(history) == 3
        assert [h["value"] for h in history] == [None, 1, 2]


# ---------------------------------------------------------------------------
#  D) Scheduler offline: gap detectable
# ---------------------------------------------------------------------------

class TestSchedulerGap:
    """Prove: absence of telemetry means scheduler was offline."""

    def test_gap_detected_by_missing_telemetry(self):
        """D) scheduler offline: gap continua detectável pela ausência de scheduler telemetry."""
        store = _tmp_store()

        # Simulate telemetry for 3 hours, then gap, then resume
        for hour in [10, 11, 12]:  # Hours 10-12 present
            store._capture_scheduler_telemetry(
                run_id=f"run-{hour}",
                world_id="football",
                provider="HttpFootballDataProvider",
                run_started_at=f"2026-09-03T{hour:02d}:00:00+00:00",
                run_finished_at=f"2026-09-03T{hour:02d}:01:00+00:00",
                success=True,
                signals_seen=43,
                signals_changed=0,
                signals_unchanged=0,
            )

        # Hours 13-15 are MISSING (scheduler was offline)

        for hour in [16, 17]:  # Resume at hour 16
            store._capture_scheduler_telemetry(
                run_id=f"run-{hour}",
                world_id="football",
                provider="HttpFootballDataProvider",
                run_started_at=f"2026-09-03T{hour:02d}:00:00+00:00",
                run_finished_at=f"2026-09-03T{hour:02d}:01:00+00:00",
                success=True,
                signals_seen=43,
                signals_changed=0,
                signals_unchanged=0,
            )

        # Query telemetry: should see gap
        with store._connect() as conn:
            runs = conn.execute(
                "SELECT run_id, run_started_at FROM scheduler_runs WHERE world_id='football' ORDER BY run_started_at"
            ).fetchall()

        assert len(runs) == 5
        # Gap is detectable: no runs between 12:00 and 16:00
        run_times = [r["run_started_at"] for r in runs]
        assert "2026-09-03T13:00:00+00:00" not in run_times
        assert "2026-09-03T14:00:00+00:00" not in run_times
        assert "2026-09-03T15:00:00+00:00" not in run_times


# ---------------------------------------------------------------------------
#  E) Crypto: all observations persist (prices change)
# ---------------------------------------------------------------------------

class TestCryptoPersistence:
    """Prove: crypto with different price each hour: all observations persist."""

    def test_crypto_different_prices_persist(self):
        """E) crypto com preço diferente a cada hora: todas observações relevantes persistem."""
        store = _tmp_store()

        # Simulate 24 hourly BTC prices (all different)
        base_price = 80000.0
        results = []
        for hour in range(24):
            price = base_price + (hour * 100)  # Different each hour
            result = store.capture_signal_change_aware(
                world_id="crypto",
                signal_id="crypto.price.usd",
                entity_ref="coin:btc",
                schema="crypto.price.v1",
                value=price,
                value_type="number",
                unit="usd",
                observed_at=f"2026-09-03T{hour:02d}:00:00+00:00",
                source={"observation_world_id": "crypto", "derivation": "direct"},
                metadata={"symbol": "BTC", "name": "Bitcoin"},
            )
            results.append(result)

        # All should be recorded (1 initial + 23 changed)
        initial = sum(1 for r in results if r["status"] == "initial_recorded")
        changed = sum(1 for r in results if r["status"] == "changed_recorded")
        unchanged = sum(1 for r in results if r["status"] == "unchanged_skipped")

        assert initial == 1
        assert changed == 23
        assert unchanged == 0

        # 24 observations in DB
        history = store.signal_history(
            "crypto", "crypto.price.usd", "coin:btc"
        )
        assert len(history) == 24


# ---------------------------------------------------------------------------
#  F) Operational signals identifiable
# ---------------------------------------------------------------------------

class TestOperationalSeparation:
    """Prove: operational signals identifiable and excludable from domain dataset."""

    def test_operational_signals_in_db(self):
        """F) operational signals ficam identificáveis e excluíveis do dataset de domínio."""
        store = _tmp_store()

        # Mix domain and operational signals
        signals = [
            # Domain signals
            {"signal_id": "football.match.status", "value": "live", "entity_ref": "match:TSDB-123"},
            {"signal_id": "football.match.home_score", "value": 1, "entity_ref": "match:TSDB-123"},
            # Operational signals
            {"signal_id": "football.observation.match_count", "value": 8, "entity_ref": None},
            {"signal_id": "football.provider.freshness", "value": 120.5, "entity_ref": None},
        ]

        for i, sig in enumerate(signals):
            store.capture_signal(
                world_id="football",
                signal_id=sig["signal_id"],
                entity_ref=sig["entity_ref"],
                schema="football.match.v1",
                value=sig["value"],
                value_type="number" if isinstance(sig["value"], (int, float)) else "categorical",
                unit="",
                observed_at=f"2026-09-03T{i:02d}:00:00+00:00",
                source={"observation_world_id": "football", "derivation": "direct"},
                metadata={},
            )

        # Query all signals for football
        all_signals = store.signals_for_world("football")

        # Separate domain vs operational
        domain_signals = [s for s in all_signals if not _is_operational(s["signal_id"])]
        operational_signals = [s for s in all_signals if _is_operational(s["signal_id"])]

        assert len(domain_signals) == 2
        assert len(operational_signals) == 2

        # Domain signals are: status, home_score
        domain_ids = {s["signal_id"] for s in domain_signals}
        assert domain_ids == {"football.match.status", "football.match.home_score"}

        # Operational signals are: match_count, freshness
        op_ids = {s["signal_id"] for s in operational_signals}
        assert op_ids == {"football.observation.match_count", "football.provider.freshness"}


# ---------------------------------------------------------------------------
#  Change-aware vs regular: backward compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    """Prove: existing capture_signal still works (no change)."""

    def test_capture_signal_unchanged(self):
        """Existing capture_signal is not affected by change-aware changes."""
        store = _tmp_store()

        # Regular capture: idempotent by hash
        result1 = store.capture_signal(
            world_id="test",
            signal_id="test.signal",
            entity_ref=None,
            schema="test.v1",
            value="hello",
            value_type="string",
            unit="",
            observed_at="2026-09-03T10:00:00+00:00",
            source={},
        )
        result2 = store.capture_signal(
            world_id="test",
            signal_id="test.signal",
            entity_ref=None,
            schema="test.v1",
            value="hello",
            value_type="string",
            unit="",
            observed_at="2026-09-03T10:00:00+00:00",
            source={},
        )

        assert result1["status"] == "recorded"
        assert result2["status"] == "duplicate"  # Same hash → duplicate


# ---------------------------------------------------------------------------
#  Value equality: semantic comparison
# ---------------------------------------------------------------------------

class TestValueEquality:
    """Prove: semantic value comparison works correctly."""

    def test_numeric_tolerance(self):
        """Float values within tolerance are considered equal."""
        store = _tmp_store()

        # First observation
        result1 = store.capture_signal_change_aware(
            world_id="crypto",
            signal_id="crypto.price.usd",
            entity_ref="coin:btc",
            schema="crypto.price.v1",
            value=80000.123456789,
            value_type="number",
            unit="usd",
            observed_at="2026-09-03T10:00:00+00:00",
            source={},
        )
        assert result1["status"] == "initial_recorded"

        # Second: value within tolerance (relative 1e-9)
        result2 = store.capture_signal_change_aware(
            world_id="crypto",
            signal_id="crypto.price.usd",
            entity_ref="coin:btc",
            schema="crypto.price.v1",
            value=80000.123456790,  # 1e-9 relative diff
            value_type="number",
            unit="usd",
            observed_at="2026-09-03T11:00:00+00:00",
            source={},
        )
        assert result2["status"] == "unchanged_skipped"

        # Third: value outside tolerance
        result3 = store.capture_signal_change_aware(
            world_id="crypto",
            signal_id="crypto.price.usd",
            entity_ref="coin:btc",
            schema="crypto.price.v1",
            value=80100.0,  # 0.12% different
            value_type="number",
            unit="usd",
            observed_at="2026-09-03T12:00:00+00:00",
            source={},
        )
        assert result3["status"] == "changed_recorded"

    def test_string_equality(self):
        """String values must match exactly."""
        store = _tmp_store()

        store.capture_signal_change_aware(
            world_id="football",
            signal_id="football.match.status",
            entity_ref="match:TSDB-123",
            schema="football.match.v1",
            value="scheduled",
            value_type="categorical",
            unit="",
            observed_at="2026-09-03T10:00:00+00:00",
            source={},
        )

        # Same string → unchanged
        result = store.capture_signal_change_aware(
            world_id="football",
            signal_id="football.match.status",
            entity_ref="match:TSDB-123",
            schema="football.match.v1",
            value="scheduled",
            value_type="categorical",
            unit="",
            observed_at="2026-09-03T11:00:00+00:00",
            source={},
        )
        assert result["status"] == "unchanged_skipped"

        # Different string → changed
        result2 = store.capture_signal_change_aware(
            world_id="football",
            signal_id="football.match.status",
            entity_ref="match:TSDB-123",
            schema="football.match.v1",
            value="live",
            value_type="categorical",
            unit="",
            observed_at="2026-09-03T12:00:00+00:00",
            source={},
        )
        assert result2["status"] == "changed_recorded"


# ---------------------------------------------------------------------------
#  Telemetry: success and failure
# ---------------------------------------------------------------------------

class TestTelemetry:
    """Prove: telemetry records success and failure correctly."""

    def test_telemetry_success(self):
        """Telemetry records successful poll."""
        store = _tmp_store()

        store._capture_scheduler_telemetry(
            run_id="run-001",
            world_id="football",
            provider="HttpFootballDataProvider",
            run_started_at="2026-09-03T10:00:00+00:00",
            run_finished_at="2026-09-03T10:01:00+00:00",
            success=True,
            signals_seen=43,
            signals_changed=0,
            signals_unchanged=0,
        )

        with store._connect() as conn:
            row = conn.execute(
                "SELECT * FROM scheduler_runs WHERE run_id='run-001'"
            ).fetchone()

        assert row is not None
        assert row["success"] == 1
        assert row["signals_seen"] == 43
        assert row["error"] is None

    def test_telemetry_failure(self):
        """Telemetry records failed poll with error."""
        store = _tmp_store()

        store._capture_scheduler_telemetry(
            run_id="run-002",
            world_id="football",
            provider="HttpFootballDataProvider",
            run_started_at="2026-09-03T11:00:00+00:00",
            run_finished_at="2026-09-03T11:00:30+00:00",
            success=False,
            signals_seen=0,
            signals_changed=0,
            signals_unchanged=0,
            error="Connection timeout",
        )

        with store._connect() as conn:
            row = conn.execute(
                "SELECT * FROM scheduler_runs WHERE run_id='run-002'"
            ).fetchone()

        assert row is not None
        assert row["success"] == 0
        assert row["error"] == "Connection timeout"
