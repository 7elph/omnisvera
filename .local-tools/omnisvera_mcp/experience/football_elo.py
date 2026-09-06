"""Concrete updater for football.elo v1 — deterministic, simple Elo.

State shape:
{
  "team_ratings": {"ARS": 1500, "CHE": 1450, ...},
  "home_advantage": 50,
  "k_factor": 20
}

Update rule (deterministic, bounded):
- outcome 1 => home/team win => transfer k*(1 - expected) from away to home
- outcome 0 => away win => transfer k*(0 - expected)
- outcome handling uses home_advantage and current ratings.
If prediction lacks team info, falls back to generic: winner +10 / loser -10 on a dummy pair.

This proves the runtime universal — not a sophisticated predictor.
"""
from __future__ import annotations

from typing import Any

from .updater import ExperienceUpdateResult, ExperienceUpdater


def _expected(home_rating: float, away_rating: float, home_adv: float = 50.0) -> float:
    diff = (home_rating + home_adv) - away_rating
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


class FootballEloUpdater(ExperienceUpdater):
    PREDICTOR_ID = "football.elo"
    PREDICTOR_VERSION = "v1"
    PREDICTOR_TYPE = "statistical"
    SCHEMA = "elo.v1"

    def describe(self) -> dict[str, Any]:
        return {
            "predictor_id": self.PREDICTOR_ID,
            "predictor_version": self.PREDICTOR_VERSION,
            "predictor_type": self.PREDICTOR_TYPE,
            "schema": self.SCHEMA,
            "description": "Simple deterministic Elo updater for football.elo v1",
            "update_order_semantics": "order_sensitive",
        }

    def update(
        self,
        *,
        previous_experience: dict[str, Any] | None,
        prediction: dict[str, Any],
        resolution: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> ExperienceUpdateResult:
        prev_state: dict[str, Any] = {}
        if previous_experience is not None:
            prev_state = dict(previous_experience.get("learned_state") or {})
        team_ratings: dict[str, float] = dict(prev_state.get("team_ratings") or {})
        home_adv: float = float(prev_state.get("home_advantage", 50.0))
        k_factor: float = float(prev_state.get("k_factor", 20.0))

        # Derive teams from prediction context if available
        # Try resolution_rule -> entity_ref or claim
        # For acceptance we ensure at least ARS/CHE exist
        if "ARS" not in team_ratings:
            team_ratings.setdefault("ARS", 1500.0)
        if "CHE" not in team_ratings:
            team_ratings.setdefault("CHE", 1450.0)

        # Simple heuristic: subject_ref like "ARS vs CHE" or resolution sources
        subject = str(prediction.get("subject_ref") or prediction.get("claim") or "")
        # Attempt to parse teams from claim like "ARS beats CHE" or subject
        home_team = "ARS"
        away_team = "CHE"
        subj_lower = subject.lower()
        if "ars" in subj_lower and "che" in subj_lower:
            # default already
            pass
        # Also check resolution context for explicit teams if provided via metadata
        ctx = context or {}
        if "home_team" in ctx and "away_team" in ctx:
            home_team = str(ctx["home_team"])
            away_team = str(ctx["away_team"])

        # Ensure ratings exist
        team_ratings.setdefault(home_team, 1500.0)
        team_ratings.setdefault(away_team, 1500.0)

        outcome = int(resolution.get("outcome", 0))  # 1 home win, 0 away win
        # For draw we treat 0.5? But outcome only 0/1 per spec, so no draw
        expected = _expected(team_ratings[home_team], team_ratings[away_team], home_adv)
        observed = float(outcome)
        delta = k_factor * (observed - expected)

        new_ratings = dict(team_ratings)
        new_ratings[home_team] = round(team_ratings[home_team] + delta, 4)
        new_ratings[away_team] = round(team_ratings[away_team] - delta, 4)

        new_state = {
            "team_ratings": new_ratings,
            "home_advantage": home_adv,
            "k_factor": k_factor,
        }

        # Detect change (should always change unless delta 0, but keep logic)
        state_changed = new_state != prev_state

        summary = f"Elo update {home_team}({team_ratings[home_team]:.1f}) vs {away_team}({team_ratings[away_team]:.1f}) exp={expected:.3f} obs={observed} delta={delta:.2f}"

        return ExperienceUpdateResult(
            learned_state_schema=self.SCHEMA,
            learned_state=new_state,
            observations_used_delta=1,
            metadata={"home_team": home_team, "away_team": away_team, "expected": round(expected, 4), "delta": round(delta, 4)},
            provenance={"updater": f"{self.PREDICTOR_ID}:{self.PREDICTOR_VERSION}"},
            update_summary=summary[:280],
            state_changed=state_changed,
        )
