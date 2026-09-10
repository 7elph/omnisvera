"""
World Learning Validation v0.1 — FULL EXPERIMENT
=================================================
10 seasons of real Premier League data (2014-2024).
3,800+ matches. Both predictors start identical.
No synthetic data. No tampering.
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
    status: str
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
    """Load all Premier League seasons, sorted chronologically."""
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
                    status="completed",
                    competition="Premier League",
                    match_date=row.get("Date", ""),
                    season=season,
                ))

    all_matches.sort(key=lambda m: m.match_date)
    return all_matches


def run_experiment(matches: list[Match], p0: float = 0.55) -> dict:
    """Run frozen vs adaptive on same sequence. Both start at p0."""
    frozen = FrozenPredictor(p0)
    adaptive = AdaptivePredictor(p0)

    frozen_preds = []
    adaptive_preds = []

    for match in matches:
        fp = frozen.predict(match)
        ap = adaptive.predict(match)
        outcome = 1 if match.home_score > match.away_score else 0

        frozen_preds.append(Prediction("frozen", match.match_id, fp, outcome))
        adaptive_preds.append(Prediction("adaptive", match.match_id, ap, outcome))

        adaptive.update(match, outcome)

    return {
        "frozen": frozen_preds,
        "adaptive": adaptive_preds,
        "n": len(frozen_preds),
        "adaptive_home_wins": adaptive.home_wins,
        "adaptive_total": adaptive.total,
    }


def paired_metrics(result: dict) -> dict:
    """Paired comparison with bootstrap CI."""
    fp = result["frozen"]
    ap = result["adaptive"]
    n = result["n"]

    diffs = [f.brier - a.brier for f, a in zip(fp, ap)]

    frozen_brier = sum(p.brier for p in fp) / n
    adaptive_brier = sum(p.brier for p in ap) / n
    mean_diff = sum(diffs) / n

    # Bootstrap 95% CI
    rng = random.Random(42)
    boot = []
    for _ in range(10000):
        sample = rng.choices(diffs, k=n)
        boot.append(sum(sample) / n)
    boot.sort()
    ci_low = boot[int(0.025 * len(boot))]
    ci_high = boot[int(0.975 * len(boot))]

    # Rolling Brier (window=50)
    window = min(50, n)
    frozen_rolling = sum(p.brier for p in fp[-window:]) / window
    adaptive_rolling = sum(p.brier for p in ap[-window:]) / window

    # Home win rate
    outcomes = [p.outcome for p in fp]
    home_win_rate = sum(outcomes) / n

    return {
        "n": n,
        "home_win_rate": round(home_win_rate, 4),
        "frozen": {
            "p0": fp[0].probability,
            "mean_brier": round(frozen_brier, 6),
            "rolling_brier_last50": round(frozen_rolling, 6),
        },
        "adaptive": {
            "p0": ap[0].probability,
            "mean_brier": round(adaptive_brier, 6),
            "rolling_brier_last50": round(adaptive_rolling, 6),
            "total_observations": result["adaptive_total"],
            "home_wins_observed": result["adaptive_home_wins"],
        },
        "paired": {
            "mean_diff": round(mean_diff, 6),
            "ci_95_low": round(ci_low, 6),
            "ci_95_high": round(ci_high, 6),
            "ci_compatible_with_zero": (ci_low <= 0 <= ci_high),
        },
        "verdict": classify(mean_diff, ci_low, ci_high),
    }


def classify(mean_diff, ci_low, ci_high):
    if ci_low <= 0 <= ci_high:
        return "NO_LEARNING_ADVANTAGE"
    elif mean_diff > 0:
        return "PRELIMINARY_LEARNING_ADVANTAGE"
    else:
        return "FROZEN_ADVANTAGE"


def calibration_buckets(predictions, n_buckets=5):
    bucket_size = 1.0 / n_buckets
    buckets = {}
    for p in predictions:
        idx = min(int(p.probability / bucket_size), n_buckets - 1)
        if idx not in buckets:
            buckets[idx] = {"pred": [], "out": []}
        buckets[idx]["pred"].append(p.probability)
        buckets[idx]["out"].append(p.outcome)

    result = []
    for idx in sorted(buckets.keys()):
        b = buckets[idx]
        mean_p = sum(b["pred"]) / len(b["pred"])
        obs_f = sum(b["out"]) / len(b["out"])
        result.append({
            "bucket": f"{idx * bucket_size:.2f}-{(idx+1) * bucket_size:.2f}",
            "n": len(b["pred"]),
            "predicted": round(mean_p, 4),
            "observed": round(obs_f, 4),
            "gap": round(abs(mean_p - obs_f), 4),
        })
    return result


def learning_curve(predictions, window=100):
    """Rolling Brier difference over time."""
    n = len(predictions) // 2
    fp = [p for p in predictions if p.predictor == "frozen"]
    ap = [p for p in predictions if p.predictor == "adaptive"]

    curve = []
    for i in range(window, n + 1):
        fb = sum(p.brier for p in fp[i-window:i]) / window
        ab = sum(p.brier for p in ap[i-window:i]) / window
        curve.append({
            "step": i,
            "frozen": round(fb, 4),
            "adaptive": round(ab, 4),
            "advantage": round(fb - ab, 4),
        })
    return curve


if __name__ == "__main__":
    print("=" * 65)
    print("WORLD LEARNING VALIDATION v0.1 — FULL EXPERIMENT")
    print("=" * 65)

    # 1. Load data
    data_dir = r"C:\Users\delib\Desktop\OMNISVERA\.local-tools\tools\pl_data"
    matches = load_all_seasons(data_dir)
    print(f"\nLoaded {len(matches)} Premier League matches")
    print(f"Seasons: {matches[0].season} to {matches[-1].season}")
    print(f"Date range: {matches[0].match_date} to {matches[-1].match_date}")

    # 2. Run experiment
    p0 = 0.55
    print(f"\nRunning experiment with P0 = {p0}...")
    result = run_experiment(matches, p0)

    # 3. Metrics
    m = paired_metrics(result)
    m["adaptive"]["total_observations"] = result["n"]

    # 4. Report
    print(f"\nMatches: {m['n']}")
    print(f"Home win rate: {m['home_win_rate']:.1%}")

    print(f"\n--- FROZEN (P0={p0}) ---")
    print(f"Mean Brier: {m['frozen']['mean_brier']:.6f}")
    print(f"Rolling (last 50): {m['frozen']['rolling_brier_last50']:.6f}")

    print(f"\n--- ADAPTIVE (P0={p0}) ---")
    print(f"Mean Brier: {m['adaptive']['mean_brier']:.6f}")
    print(f"Rolling (last 50): {m['adaptive']['rolling_brier_last50']:.6f}")

    print(f"\n--- PAIRED COMPARISON ---")
    print(f"Mean diff (frozen - adaptive): {m['paired']['mean_diff']:+.6f}")
    print(f"95% CI: [{m['paired']['ci_95_low']:+.6f}, {m['paired']['ci_95_high']:+.6f}]")
    print(f"CI compatible with zero: {m['paired']['ci_compatible_with_zero']}")

    print(f"\n--- VERDICT ---")
    print(m["verdict"])

    # 5. Calibration
    print(f"\n--- CALIBRATION (Adaptive) ---")
    for b in calibration_buckets(result["adaptive"]):
        print(f"  {b['bucket']}: pred={b['predicted']:.3f} obs={b['observed']:.3f} gap={b['gap']:.3f} n={b['n']}")

    # 6. Learning curve summary
    curve = learning_curve(result["frozen"] + result["adaptive"])
    print(f"\n--- LEARNING CURVE (rolling window=100) ---")
    checkpoints = [100, 500, 1000, 1500, 2000, 2500, 3000, 3500]
    for cp in checkpoints:
        if cp <= len(curve):
            c = curve[cp - 1]
            marker = "ADAPTIVE" if c["advantage"] > 0 else "FROZEN"
            print(f"  Step {cp:5d}: f={c['frozen']:.4f} a={c['adaptive']:.4f} adv={c['advantage']:+.4f} -> {marker}")

    # 7. Season breakdown
    print(f"\n--- SEASON BREAKDOWN ---")
    seasons = {}
    for fp, ap in zip(result["frozen"], result["adaptive"]):
        # Find match season
        for m in matches:
            if m.match_id == fp.match_id:
                s = m.season
                break
        else:
            continue
        if s not in seasons:
            seasons[s] = {"fb": 0, "ab": 0, "n": 0}
        seasons[s]["fb"] += fp.brier
        seasons[s]["ab"] += ap.brier
        seasons[s]["n"] += 1

    for s in sorted(seasons.keys()):
        d = seasons[s]
        fb = d["fb"] / d["n"]
        ab = d["ab"] / d["n"]
        marker = "ADAPTIVE" if ab < fb else "FROZEN"
        print(f"  {s}: f={fb:.4f} a={ab:.4f} -> {marker}")

    print("\n" + "=" * 65)
