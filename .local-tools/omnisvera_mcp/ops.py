"""Shared operational signal classification.

Single source of truth for scheduler + world.context.
Changing this set changes both persistence semantics and view semantics,
so it must live in one place.
"""
from __future__ import annotations

OPERATIONAL_SIGNAL_IDS: frozenset[str] = frozenset({
    "football.observation.match_count",
    "football.provider.freshness",
    "crypto.observation.coin_count",
    "test.signal",
})
