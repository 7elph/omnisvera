"""
World Learning Validation v0.1 — LEVEL 1 HARDENED
===================================================
Both predictors start well-informed (trained P0 from past seasons).
No arbitrary prior. Tests whether adaptive tracks a moving distribution.
Block bootstrap by season for CI.
"""

import csv
import os
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Match:
    match_id: str
    home_name: str
    away_name: str
    home_score: int
    away_score: int
    competition: str
    match_date: str
    season: str


@dataclass
class Prediction:
    predictor: str
    match_id: str
    probability: float
    outcome: int
    brier: float = 0.0
    season: str = ""

    def __post_init__(self):
        self.brier = round((self.probability - self.outcome) ** 2, 8)


class FrozenPredictor:
    def __init__(self, p0: float):
        self.p0 = p0

    def predict(self, match: Match) -> float:
        return self.p0

    def update(self, match: Match, outcome: int):
        pass


class AdaptivePredictor:
    def __init__(self, p0: float, confidence: int = 5):
        self.p0 = p0
        self.confidence = confidence
        self.total = 0
        self.home_wins = 0

    def predict(self, match: Match) -> float:
        if self.total == 0:
            return self.p0
        return (self.home_wins + self.p0 * self.confidence) / (
            self.total + self.confidence
        )

    def update(self, match: Match, outcome: int):
        self.total += 1
        self.home_wins += outcome


def load_all_seasons(data_dir: str) -> list[Match]:
    all_matches = []
    season_files = sorted(Path(data_dir).glob("EPL_*.csv"))

    for filepath in season_files:
        season = filepath.stem.replace("EPL_", "")
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if row.get("FTR") not in ("H", "D", "A"):
                    continue
                try:
                    hs = int(row.get("FTHG") or 0)
                    aws = int(row.get("FTAG") or 0)
                except (ValueError, TypeError):
                    continue

                all_matches.append(Match(
                    match_id=f"{season}_{i:03d}",
                    home_name=row.get("HomeTeam", ""),
                    away_name=row.get("AwayTeam", ""),
                    home_score=hs,
                    away_score=aws,
                    competition="Premier League",
                    match_date=row.get("Date", ""),
                    season=season,
                ))

    all_matches.sort(key=lambda m: m.match_date)
    return all_matches


def train_test_split_by_season(matches: list[Match], train_seasons: int = 6):
    """Split by season. First N seasons = train, rest = evaluation."""
    seasons = sorted(set(m.season for m in matches))
    train_set = set(seasons[:train_seasons])
    test_set = set(seasons[train_seasons:])

    train = [m for m in matches if m.season in train_set]
    test = [m for m in matches if m.season in test_set]

    return train, test, train_set, test_set


def estimate_home_win_rate(matches: list[Match]) -> float:
    """Estimate P(home win) from training data."""
    outcomes = [1 if m.home_score > m.away_score else 0 for m in matches]
    return sum(outcomes) / len(outcomes) if outcomes else 0.5


def run_experiment(train: list[Match], test: list[Match], p0: float) -> dict:
    """Both start at p0. Frozen never updates. Adaptive updates after each outcome."""
    frozen = FrozenPredictor(p0)
    adaptive = AdaptivePredictor(p0)

    frozen_preds = []
    adaptive_preds = []

    for match in test:
        fp = frozen.predict(match)
        ap = adaptive.predict(match)
        outcome = 1 if match.home_score > match.away_score else 0

        frozen_preds.append(Prediction("frozen", match.match_id, fp, outcome, season=match.season))
        adaptive_preds.append(Prediction("adaptive", match.match_id, ap, outcome, season=match.season))

        adaptive.update(match, outcome)

    return {
        "frozen": frozen_preds,
        "adaptive": adaptive_preds,
        "n": len(frozen_preds),
        "p0": p0,
        "adaptive_final_home_wins": adaptive.home_wins,
        "adaptive_final_total": adaptive.total,
    }


def block_bootstrap_by_season(frozen, adaptive, matches_by_season, n_boot=10000):
    """Block bootstrap: resample entire seasons, not individual matches."""
    seasons = list(matches_by_season.keys())
    rng = random.Random(42)

    # Group predictions by season
    fp_by_season = {}
    ap_by_season = {}
    for fp, ap in zip(frozen, adaptive):
        if fp.season not in fp_by_season:
            fp_by_season[fp.season] = []
            ap_by_season[ap.season] = []
        fp_by_season[fp.season].append(fp)
        ap_by_season[ap.season].append(ap)

    diffs_by_season = {}
    for s in seasons:
        diffs_by_season[s] = [
            fp.brier - ap.brier
            for fp, ap in zip(fp_by_season[s], ap_by_season[s])
        ]

    boot_diffs = []
    for _ in range(n_boot):
        # Resample seasons with replacement
        sampled_seasons = rng.choices(seasons, k=len(seasons))
        all_diffs = []
        for s in sampled_seasons:
            all_diffs.extend(diffs_by_season[s])
        boot_diffs.append(sum(all_diffs) / len(all_diffs))

    boot_diffs.sort()
    ci_low = boot_diffs[int(0.025 * len(boot_diffs))]
    ci_high = boot_diffs[int(0.975 * len(boot_diffs))]

    return ci_low, ci_high


def seasonal_metrics(frozen, adaptive):
    """Per-season Brier scores."""
    seasons = {}
    for fp, ap in zip(frozen, adaptive):
        s = fp.season
        if s not in seasons:
            seasons[s] = {"fb": 0, "ab": 0, "n": 0}
        seasons[s]["fb"] += fp.brier
        seasons[s]["ab"] += ap.brier
        seasons[s]["n"] += 1

    result = []
    for s in sorted(seasons.keys()):
        d = seasons[s]
        fb = d["fb"] / d["n"]
        ab = d["ab"] / d["n"]
        result.append({
            "season": s,
            "frozen_brier": round(fb, 4),
            "adaptive_brier": round(ab, 4),
            "advantage": round(fb - ab, 4),
            "n": d["n"],
        })
    return result


if __name__ == "__main__":
    print("=" * 65)
    print("LEVEL 1 HARDENED — Both start well-informed")
    print("=" * 65)

    # 1. Load data
    data_dir = r"C:\Users\delib\Desktop\OMNISVERA\.local-tools\tools\pl_data"
    matches = load_all_seasons(data_dir)
    seasons = sorted(set(m.season for m in matches))
    print(f"\nLoaded {len(matches)} matches across {len(seasons)} seasons")
    print(f"Seasons: {seasons}")

    # 2. Train/test split
    train_seasons_count = 6
    train, test, train_set, test_set = train_test_split_by_season(matches, train_seasons_count)

    print(f"\nTraining seasons ({train_seasons_count}): {sorted(train_set)}")
    print(f"Evaluation seasons ({len(test_set)}): {sorted(test_set)}")
    print(f"Training matches: {len(train)}")
    print(f"Evaluation matches: {len(test)}")

    # 3. Estimate P0 from training data
    p0 = estimate_home_win_rate(train)
    print(f"\nEstimated P(home win) from training: {p0:.4f}")

    # 4. Run experiment
    print(f"\nRunning experiment with trained P0 = {p0:.4f}...")
    result = run_experiment(train, test, p0)

    # 5. Basic metrics
    fp = result["frozen"]
    ap = result["adaptive"]
    n = result["n"]

    frozen_brier = sum(p.brier for p in fp) / n
    adaptive_brier = sum(p.brier for p in ap) / n
    mean_diff = frozen_brier - adaptive_brier

    print(f"\nMatches: {n}")
    print(f"Home win rate (eval): {sum(p.outcome for p in fp) / n:.4f}")

    print(f"\n--- FROZEN (P0={p0:.4f}, never updates) ---")
    print(f"Mean Brier: {frozen_brier:.6f}")

    print(f"\n--- ADAPTIVE (P0={p0:.4f}, Bayesian update) ---")
    print(f"Mean Brier: {adaptive_brier:.6f}")
    print(f"Home wins observed: {result['adaptive_final_home_wins']}/{result['adaptive_final_total']}")

    # 6. Block bootstrap CI
    print(f"\n--- BLOCK BOOTSTRAP CI (by season) ---")
    ci_low, ci_high = block_bootstrap_by_season(
        fp, ap, {s: [] for s in test_set}
    )
    print(f"Mean diff (frozen - adaptive): {mean_diff:+.6f}")
    print(f"95% CI (block bootstrap): [{ci_low:+.6f}, {ci_high:+.6f}]")
    print(f"CI compatible with zero: {ci_low <= 0 <= ci_high}")

    # 7. Verdict
    if ci_low <= 0 <= ci_high:
        verdict = "NO_LEARNING_ADVANTAGE"
    elif mean_diff > 0:
        verdict = "PRELIMINARY_LEARNING_ADVANTAGE"
    else:
        verdict = "FROZEN_ADVANTAGE"
    print(f"\nVerdict: {verdict}")

    # 8. Season breakdown
    print(f"\n--- SEASON BREAKDOWN ---")
    sm = seasonal_metrics(fp, ap)
    adaptive_wins = 0
    for s in sm:
        marker = "ADAPTIVE" if s["advantage"] > 0 else "FROZEN"
        if s["advantage"] > 0:
            adaptive_wins += 1
        print(f"  {s['season']}: f={s['frozen_brier']:.4f} a={s['adaptive_brier']:.4f} adv={s['advantage']:+.4f} -> {marker}")
    print(f"\nAdaptive wins: {adaptive_wins}/{len(sm)} seasons")

    # 9. Rolling learning curve
    print(f"\n--- LEARNING CURVE (rolling window=100) ---")
    window = 100
    for i in range(window, n + 1, 500):
        fb = sum(p.brier for p in fp[i-window:i]) / window
        ab = sum(p.brier for p in ap[i-window:i]) / window
        adv = fb - ab
        marker = "ADAPTIVE" if adv > 0 else "FROZEN"
        print(f"  Step {i:5d}: f={fb:.4f} a={ab:.4f} adv={adv:+.4f} -> {marker}")

    print("\n" + "=" * 65)
