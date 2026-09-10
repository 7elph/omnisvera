"""
Baseline Predictor v1 — Deterministic, auditable, version-locked.

predictor_id = "baseline.mission_completion.v1"
predictor_version = "1.0.0"

Rules (all read-only, no outcome knowledge):
  1. mission_exists:       snapshot has at least one active mission → 0.85
  2. participants_active:  snapshot has >= 2 named participants → 0.90
  3. session_continuity:   session has prior completed session → 0.80
  4. compound:             geometric mean of triggered rules

The probability is a PURE FUNCTION of snapshot content + predictor version.
The outcome NEVER participates in the calculation.

Each call returns:
  - probability: float
  - signals_used: list[str]   — which rules fired
  - signal_values: dict       — raw rule outputs before geometric mean
  - explanation: str          — human-readable audit trail
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


PREDICTOR_ID = "baseline.mission_completion.v1"
PREDICTOR_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class PredictionResult:
    probability: float
    signals_used: list[str]
    signal_values: dict[str, float]
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "predictor_id": PREDICTOR_ID,
            "predictor_version": PREDICTOR_VERSION,
            "probability": self.probability,
            "signals_used": self.signals_used,
            "signal_values": self.signal_values,
            "explanation": self.explanation,
        }


def _rule_mission_exists(state: dict[str, Any]) -> tuple[float, str]:
    """Check if snapshot contains at least one active/declared mission.

    Reads: state["missions"] — list of dicts with "status" key.
    Active statuses: "active", "declared", "in_progress".
    """
    missions = state.get("missions", [])
    if not isinstance(missions, list) or not missions:
        return 0.0, "no missions found in snapshot"
    active_statuses = {"active", "declared", "in_progress", "open"}
    active = [m for m in missions if isinstance(m, dict) and m.get("status") in active_statuses]
    if active:
        return 0.85, f"{len(active)} active mission(s): {[m.get('title', '?') for m in active]}"
    return 0.0, f"{len(missions)} mission(s) found but none active"


def _rule_participants_active(state: dict[str, Any]) -> tuple[float, str]:
    """Check if snapshot has >= 2 named participants.

    Reads: state["participants"] — list of dicts with "public_label" or "name".
    """
    participants = state.get("participants", [])
    if not isinstance(participants, list):
        return 0.0, "participants not a list"
    named = [p for p in participants if isinstance(p, dict) and (p.get("public_label") or p.get("name"))]
    if len(named) >= 2:
        labels = [p.get("public_label") or p.get("name", "?") for p in named]
        return 0.90, f"{len(named)} named participants: {labels}"
    return 0.0, f"only {len(named)} named participant(s)"


def _rule_session_continuity(state: dict[str, Any]) -> tuple[float, str]:
    """Check if session has evidence of prior continuity (completed prior session).

    Reads: state["session_status"], state["session_number"], state["prior_sessions"].
    """
    session_number = state.get("session_number")
    if session_number is not None and isinstance(session_number, (int, float)) and session_number > 1:
        return 0.80, f"session_number={session_number} (>1, implies prior session)"
    prior = state.get("prior_sessions", [])
    if isinstance(prior, list) and len(prior) > 0:
        return 0.80, f"{len(prior)} prior session(s) recorded"
    status = state.get("session_status", "")
    if status == "completed":
        return 0.80, "session_status=completed (implies continuity)"
    return 0.0, "no continuity evidence"


# Ordered list of rules — each produces (score, explanation)
RULES = [
    ("mission_exists", _rule_mission_exists),
    ("participants_active", _rule_participants_active),
    ("session_continuity", _rule_session_continuity),
]


def predict(state: dict[str, Any]) -> PredictionResult:
    """Produce a deterministic probability from snapshot state.

    The probability is the geometric mean of all triggered rules' scores.
    If no rules trigger, probability = 0.05 (minimal baseline).
    """
    signals_used: list[str] = []
    signal_values: dict[str, float] = {}
    explanations: list[str] = []

    for rule_name, rule_fn in RULES:
        score, explanation = rule_fn(state)
        if score > 0:
            signals_used.append(rule_name)
            signal_values[rule_name] = score
            explanations.append(f"{rule_name}={score:.2f}: {explanation}")

    if not signals_used:
        probability = 0.05
        explanation = "No signals triggered → minimal baseline p=0.05"
    else:
        # Geometric mean of triggered signals
        product = 1.0
        for s in signals_used:
            product *= signal_values[s]
        probability = round(product ** (1.0 / len(signals_used)), 8)
        explanation = " | ".join(explanations) + f" → geometric_mean={probability:.8f}"

    return PredictionResult(
        probability=probability,
        signals_used=signals_used,
        signal_values=signal_values,
        explanation=explanation,
    )
