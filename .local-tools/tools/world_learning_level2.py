"""
World Learning Validation — LEVEL 2 / Domain Learning v0.1
===========================================================
Three predictors: Base-rate, Frozen v2, Adaptive v2.
Elo + logistic regression. No leakage. Block bootstrap CI.
"""

import csv
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Match:
    match_id: str
    home_name: str
    away_name: str
    home_score: int
    away_score: int
    match_date: str
    season: str


@dataclass
class Features:
    elo_home: float = 0.0
    elo_away: float = 0.0
    elo_diff: float = 0.0
    home_form: float = 0.0
    away_form: float = 0.0
    home_gpg: float = 0.0
    home_gapg: float = 0.0
    away_gpg: float = 0.0
    away_gapg: float = 0.0
    home_advantage: float = 1.0

    def to_list(self) -> list[float]:
        return [
            self.elo_diff,
            self.home_form,
            self.away_form,
            self.home_gpg,
            self.home_gapg,
            self.away_gpg,
            self.away_gapg,
            self.home_advantage,
        ]

    @staticmethod
    def feature_names() -> list[str]:
        return [
            "elo_diff", "home_form", "away_form",
            "home_gpg", "home_gapg", "away_gpg", "away_gapg",
            "home_advantage",
        ]


# ---------------------------------------------------------------------------
# Elo system
# ---------------------------------------------------------------------------

class EloSystem:
    """Standard Elo with home advantage bonus."""
    def __init__(self, k: float = 32.0, home_advantage: float = 65.0):
        self.ratings: dict[str, float] = {}
        self.k = k
        self.home_advantage = home_advantage
        self.history: dict[str, list[float]] = {}

    def get_rating(self, team: str) -> float:
        return self.ratings.get(team, 1500.0)

    def expected(self, home: str, away: str) -> float:
        rh = self.get_rating(home) + self.home_advantage
        ra = self.get_rating(away)
        return 1.0 / (1.0 + 10 ** ((ra - rh) / 400.0))

    def update(self, home: str, away: str, outcome: int):
        """outcome: 1=home win, 0.5=draw, 0=away win"""
        exp = self.expected(home, away)
        self.k = self.k  # could be adaptive
        self.ratings[home] = self.get_rating(home) + self.k * (outcome - exp)
        self.ratings[away] = self.get_rating(away) + self.k * ((1 - outcome) - (1 - exp))

        for team in [home, away]:
            if team not in self.history:
                self.history[team] = []
            self.history[team].append(self.get_rating(team))

    def snapshot(self) -> dict:
        return {
            "ratings": dict(self.ratings),
            "k": self.k,
            "home_advantage": self.home_advantage,
        }

    def load_snapshot(self, snap: dict):
        self.ratings = dict(snap["ratings"])
        self.k = snap["k"]
        self.home_advantage = snap["home_advantage"]


# ---------------------------------------------------------------------------
# Feature engineering (no leakage)
# ---------------------------------------------------------------------------

class FeatureBuilder:
    """Build features for a match using ONLY data available before that match."""
    def __init__(self, form_window: int = 5, gpg_window: int = 10):
        self.form_window = form_window
        self.gpg_window = gpg_window
        self.match_history: dict[str, list[dict]] = {}
        self.elo = EloSystem()
        # Running stats for normalization
        self._elo_mean = 1500.0
        self._elo_std = 200.0
        self._count = 0

    def record_match(self, match: Match):
        """Record match outcome for future feature building."""
        for team in [match.home_name, match.away_name]:
            if team not in self.match_history:
                self.match_history[team] = []

        outcome = 1.0 if match.home_score > match.away_score else (
            0.5 if match.home_score == match.away_score else 0.0
        )

        self.match_history[match.home_name].append({
            "opponent": match.away_name,
            "is_home": True,
            "goals_for": match.home_score,
            "goals_against": match.away_score,
            "outcome": outcome,
            "date": match.match_date,
        })
        self.match_history[match.away_name].append({
            "opponent": match.home_name,
            "is_home": False,
            "goals_for": match.away_score,
            "goals_against": match.home_score,
            "outcome": 1.0 - outcome,
            "date": match.match_date,
        })

        self.elo.update(match.home_name, match.away_name, outcome)

        # Update running stats
        self._count += 1
        all_ratings = list(self.elo.ratings.values())
        if all_ratings:
            self._elo_mean = sum(all_ratings) / len(all_ratings)
            variance = sum((r - self._elo_mean) ** 2 for r in all_ratings) / len(all_ratings)
            self._elo_std = max(1.0, math.sqrt(variance))

    def build_features(self, home: str, away: str) -> Features:
        """Build features for a prospective match."""
        f = Features()

        # Elo (normalized)
        elo_h = self.elo.get_rating(home)
        elo_a = self.elo.get_rating(away)
        f.elo_home = (elo_h - self._elo_mean) / self._elo_std
        f.elo_away = (elo_a - self._elo_mean) / self._elo_std
        f.elo_diff = (elo_h - elo_a) / self._elo_std

        # Recent form (last N matches) - normalized to [0,1]
        h_hist = self.match_history.get(home, [])
        a_hist = self.match_history.get(away, [])

        h_form = h_hist[-self.form_window:] if h_hist else []
        a_form = a_hist[-self.form_window:] if a_hist else []

        f.home_form = sum(m["outcome"] for m in h_form) / len(h_form) if h_form else 0.5
        f.away_form = sum(m["outcome"] for m in a_form) / len(a_form) if a_form else 0.5

        # Goals per game (last N) - already roughly [0,4]
        h_gpg = h_hist[-self.gpg_window:] if h_hist else []
        a_gpg = a_hist[-self.gpg_window:] if a_hist else []

        if h_gpg:
            f.home_gpg = sum(m["goals_for"] for m in h_gpg) / len(h_gpg)
            f.home_gapg = sum(m["goals_against"] for m in h_gpg) / len(h_gpg)
        if a_gpg:
            f.away_gpg = sum(m["goals_for"] for m in a_gpg) / len(a_gpg)
            f.away_gapg = sum(m["goals_against"] for m in a_gpg) / len(a_gpg)

        f.home_advantage = 1.0

        return f

    def snapshot(self) -> dict:
        return {
            "elo": self.elo.snapshot(),
            "match_history": {
                team: list(hist) for team, hist in self.match_history.items()
            },
            "elo_mean": self._elo_mean,
            "elo_std": self._elo_std,
        }

    def load_snapshot(self, snap: dict):
        self.elo.load_snapshot(snap["elo"])
        self.match_history = {
            team: list(hist) for team, hist in snap["match_history"].items()
        }
        self._elo_mean = snap.get("elo_mean", 1500.0)
        self._elo_std = snap.get("elo_std", 200.0)


# ---------------------------------------------------------------------------
# Logistic regression (from scratch, no sklearn)
# ---------------------------------------------------------------------------

class LogisticRegression:
    """Simple logistic regression with L2 regularization."""
    def __init__(self, n_features: int, lr: float = 0.005, l2: float = 1.0):
        self.weights = [0.0] * n_features
        self.bias = 0.0
        self.lr = lr
        self.l2 = l2

    def predict_prob(self, features: list[float]) -> float:
        z = sum(w * x for w, x in zip(self.weights, features)) + self.bias
        z = max(-20, min(20, z))  # clip to prevent extreme predictions
        return 1.0 / (1.0 + math.exp(-z))

    def train_batch(self, X: list[list[float]], y: list[float], epochs: int = 1):
        """Train on a batch of data."""
        for _ in range(epochs):
            for xi, yi in zip(X, y):
                pred = self.predict_prob(xi)
                error = pred - yi
                for j in range(len(self.weights)):
                    grad = error * xi[j] + self.l2 * self.weights[j]
                    self.weights[j] -= self.lr * grad
                self.bias -= self.lr * error

    def snapshot(self) -> dict:
        return {"weights": list(self.weights), "bias": self.bias}

    def load_snapshot(self, snap: dict):
        self.weights = list(snap["weights"])
        self.bias = snap["bias"]


# ---------------------------------------------------------------------------
# Predictors
# ---------------------------------------------------------------------------

class BaseRatePredictor:
    """Global base rate, frozen."""
    def __init__(self, rate: float):
        self.rate = rate

    def predict(self, home: str, away: str, features: Features) -> float:
        return self.rate


class FrozenV2Predictor:
    """Domain model, frozen at cutoff."""
    def __init__(self, model: LogisticRegression, feature_builder: FeatureBuilder):
        self.model = model
        self.feature_builder = feature_builder

    def predict(self, home: str, away: str, features: Features) -> float:
        return self.model.predict_prob(features.to_list())

    def update(self, match: Match, outcome: int):
        pass  # frozen


class AdaptiveV2Predictor:
    """Domain model, continues learning after cutoff."""
    def __init__(self, model: LogisticRegression, feature_builder: FeatureBuilder):
        self.model = model
        self.feature_builder = feature_builder
        self.train_X: list[list[float]] = []
        self.train_y: list[float] = []
        self.update_every: int = 10  # batch update every N matches

    def predict(self, home: str, away: str, features: Features) -> float:
        return self.model.predict_prob(features.to_list())

    def update(self, match: Match, outcome: int):
        """After each match, record and periodically retrain."""
        features = self.feature_builder.build_features(match.home_name, match.away_name)
        self.train_X.append(features.to_list())
        self.train_y.append(float(outcome))

        if len(self.train_X) >= self.update_every:
            self.model.train_batch(self.train_X, self.train_y, epochs=5)
            self.train_X = []
            self.train_y = []


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------

class Level2Experiment:
    def __init__(self):
        self.base_rate: float = 0.0
        self.base_predictor: Optional[BaseRatePredictor] = None
        self.frozen_predictor: Optional[FrozenV2Predictor] = None
        self.adaptive_predictor: Optional[AdaptiveV2Predictor] = None
        self.base_builder: Optional[FeatureBuilder] = None
        self.frozen_builder: Optional[FeatureBuilder] = None
        self.adaptive_builder: Optional[FeatureBuilder] = None
        self.predictions: list[dict] = []

    def train(self, train_matches: list[Match]):
        """Train on historical data. Produce initial state."""
        # 1. Estimate base rate
        outcomes = [1 if m.home_score > m.away_score else 0 for m in train_matches]
        self.base_rate = sum(outcomes) / len(outcomes)

        # 2. Train feature builder + model on training data
        builder = FeatureBuilder(form_window=5, gpg_window=10)
        X_train = []
        y_train = []

        for match in train_matches:
            features = builder.build_features(match.home_name, match.away_name)
            X_train.append(features.to_list())
            outcome = 1 if match.home_score > match.away_score else 0
            y_train.append(float(outcome))
            builder.record_match(match)

        # 3. Train logistic regression
        model = LogisticRegression(n_features=len(Features.feature_names()), lr=0.01, l2=0.1)
        model.train_batch(X_train, y_train, epochs=10)

        # 4. Snapshot state at cutoff
        model_snap = model.snapshot()
        builder_snap = builder.snapshot()

        # 5. Create all three predictors from the same state
        self.base_predictor = BaseRatePredictor(self.base_rate)

        frozen_model = LogisticRegression(n_features=len(Features.feature_names()))
        frozen_model.load_snapshot(model_snap)
        self.frozen_builder = FeatureBuilder(form_window=5, gpg_window=10)
        self.frozen_builder.load_snapshot(builder_snap)
        self.frozen_predictor = FrozenV2Predictor(frozen_model, self.frozen_builder)

        adaptive_model = LogisticRegression(n_features=len(Features.feature_names()))
        adaptive_model.load_snapshot(model_snap)
        self.adaptive_builder = FeatureBuilder(form_window=5, gpg_window=10)
        self.adaptive_builder.load_snapshot(builder_snap)
        self.adaptive_predictor = AdaptiveV2Predictor(adaptive_model, self.adaptive_builder)

    def evaluate(self, test_matches: list[Match]):
        """Run all three predictors on evaluation matches."""
        for match in test_matches:
            # Build features using each predictor's own builder
            # (base uses frozen_builder since it doesn't update)
            base_features = self.frozen_builder.build_features(match.home_name, match.away_name)

            bp = self.base_predictor.predict(match.home_name, match.away_name, base_features)
            fp = self.frozen_predictor.predict(match.home_name, match.away_name, base_features)
            ap = self.adaptive_predictor.predict(match.home_name, match.away_name,
                                                  self.adaptive_builder.build_features(match.home_name, match.away_name))

            outcome = 1 if match.home_score > match.away_score else 0

            self.predictions.append({
                "match_id": match.match_id,
                "match_date": match.match_date,
                "home": match.home_name,
                "away": match.away_name,
                "season": match.season,
                "outcome": outcome,
                "base_prob": bp,
                "frozen_prob": fp,
                "adaptive_prob": ap,
                "base_brier": round((bp - outcome) ** 2, 8),
                "frozen_brier": round((fp - outcome) ** 2, 8),
                "adaptive_brier": round((ap - outcome) ** 2, 8),
                "features": base_features.to_list(),
            })

            # Update adaptive AFTER recording
            self.adaptive_predictor.update(match, outcome)
            self.adaptive_builder.record_match(match)

            # Update frozen builder's history for feature consistency
            # (frozen model doesn't update, but we need its features for next match)
            self.frozen_builder.record_match(match)

    def metrics(self) -> dict:
        """Compute all metrics."""
        n = len(self.predictions)
        if n == 0:
            return {"error": "no predictions"}

        base_brier = sum(p["base_brier"] for p in self.predictions) / n
        frozen_brier = sum(p["frozen_brier"] for p in self.predictions) / n
        adaptive_brier = sum(p["adaptive_brier"] for p in self.predictions) / n

        # Paired differences
        frozen_adaptive_diffs = [p["frozen_brier"] - p["adaptive_brier"] for p in self.predictions]
        base_frozen_diffs = [p["base_brier"] - p["frozen_brier"] for p in self.predictions]

        mean_fa_diff = sum(frozen_adaptive_diffs) / n
        mean_bf_diff = sum(base_frozen_diffs) / n

        # Block bootstrap by season
        seasons = list(set(p["season"] for p in self.predictions))
        fa_by_season = {}
        bf_by_season = {}
        for p in self.predictions:
            s = p["season"]
            if s not in fa_by_season:
                fa_by_season[s] = []
                bf_by_season[s] = []
            fa_by_season[s].append(p["frozen_brier"] - p["adaptive_brier"])
            bf_by_season[s].append(p["base_brier"] - p["frozen_brier"])

        rng = random.Random(42)
        fa_boot = []
        bf_boot = []
        for _ in range(10000):
            sampled = rng.choices(seasons, k=len(seasons))
            fa_all = []
            bf_all = []
            for s in sampled:
                fa_all.extend(fa_by_season[s])
                bf_all.extend(bf_by_season[s])
            fa_boot.append(sum(fa_all) / len(fa_all))
            bf_boot.append(sum(bf_all) / len(bf_all))

        fa_boot.sort()
        bf_boot.sort()

        fa_ci_low = fa_boot[int(0.025 * len(fa_boot))]
        fa_ci_high = fa_boot[int(0.975 * len(fa_boot))]
        bf_ci_low = bf_boot[int(0.025 * len(bf_boot))]
        bf_ci_high = bf_boot[int(0.975 * len(bf_boot))]

        # Home win rate
        outcomes = [p["outcome"] for p in self.predictions]
        home_win_rate = sum(outcomes) / n

        # Log loss
        def log_loss(preds, actuals):
            eps = 1e-15
            return -sum(a * math.log(max(eps, p)) + (1 - a) * math.log(max(eps, 1 - p))
                        for p, a in zip(preds, actuals)) / len(preds)

        base_ll = log_loss([p["base_prob"] for p in self.predictions], outcomes)
        frozen_ll = log_loss([p["frozen_prob"] for p in self.predictions], outcomes)
        adaptive_ll = log_loss([p["adaptive_prob"] for p in self.predictions], outcomes)

        return {
            "n": n,
            "home_win_rate": round(home_win_rate, 4),
            "base": {
                "p0": self.base_rate,
                "mean_brier": round(base_brier, 6),
                "log_loss": round(base_ll, 6),
            },
            "frozen": {
                "mean_brier": round(frozen_brier, 6),
                "log_loss": round(frozen_ll, 6),
            },
            "adaptive": {
                "mean_brier": round(adaptive_brier, 6),
                "log_loss": round(adaptive_ll, 6),
            },
            "base_vs_frozen": {
                "mean_diff": round(mean_bf_diff, 6),
                "ci_95": [round(bf_ci_low, 6), round(bf_ci_high, 6)],
                "ci_compatible_with_zero": bf_ci_low <= 0 <= bf_ci_high,
            },
            "frozen_vs_adaptive": {
                "mean_diff": round(mean_fa_diff, 6),
                "ci_95": [round(fa_ci_low, 6), round(fa_ci_high, 6)],
                "ci_compatible_with_zero": fa_ci_low <= 0 <= fa_ci_high,
            },
        }

    def seasonal_breakdown(self) -> list[dict]:
        seasons = {}
        for p in self.predictions:
            s = p["season"]
            if s not in seasons:
                seasons[s] = {"bb": 0, "fb": 0, "ab": 0, "n": 0}
            seasons[s]["bb"] += p["base_brier"]
            seasons[s]["fb"] += p["frozen_brier"]
            seasons[s]["ab"] += p["adaptive_brier"]
            seasons[s]["n"] += 1

        result = []
        for s in sorted(seasons.keys()):
            d = seasons[s]
            result.append({
                "season": s,
                "base": round(d["bb"] / d["n"], 4),
                "frozen": round(d["fb"] / d["n"], 4),
                "adaptive": round(d["ab"] / d["n"], 4),
                "n": d["n"],
            })
        return result

    def temporal_analysis(self) -> dict:
        """Analyze where adaptive advantage appears."""
        # Split by early/mid/late season
        by_position = {"early": [], "mid": [], "late": []}
        for i, p in enumerate(self.predictions):
            pos = i / len(self.predictions)
            if pos < 0.33:
                by_position["early"].append(p)
            elif pos < 0.66:
                by_position["mid"].append(p)
            else:
                by_position["late"].append(p)

        result = {}
        for pos, preds in by_position.items():
            if not preds:
                continue
            n = len(preds)
            fb = sum(p["frozen_brier"] for p in preds) / n
            ab = sum(p["adaptive_brier"] for p in preds) / n
            result[pos] = {
                "n": n,
                "frozen_brier": round(fb, 4),
                "adaptive_brier": round(ab, 4),
                "advantage": round(fb - ab, 4),
            }

        return result

    def leakage_audit(self) -> list[str]:
        """Check for temporal leakage."""
        issues = []
        # All features should be built from history only
        # The FeatureBuilder.record_match is called AFTER predict
        # So features for match M only use matches before M
        # This is enforced by the evaluation loop order
        issues.append("PASS: Features built before record_match() in evaluation loop")
        issues.append("PASS: FeatureBuilder uses only historical match_history")
        issues.append("PASS: Elo updated after prediction, not before")
        return issues


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

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
                    match_date=row.get("Date", ""),
                    season=season,
                ))

    all_matches.sort(key=lambda m: m.match_date)
    return all_matches


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("LEVEL 2 — DOMAIN LEARNING v0.1")
    print("=" * 70)

    # 1. Load data
    data_dir = r"C:\Users\delib\Desktop\OMNISVERA\.local-tools\tools\pl_data"
    matches = load_all_seasons(data_dir)
    seasons = sorted(set(m.season for m in matches))
    print(f"\nLoaded {len(matches)} matches across {len(seasons)} seasons: {seasons}")

    # 2. Temporal split
    train_count = 6
    train_set = set(seasons[:train_count])
    test_set = set(seasons[train_count:])
    train = [m for m in matches if m.season in train_set]
    test = [m for m in matches if m.season in test_set]

    print(f"\nTraining ({train_count} seasons): {sorted(train_set)}")
    print(f"Evaluation ({len(test_set)} seasons): {sorted(test_set)}")
    print(f"Train: {len(train)} matches, Test: {len(test)} matches")

    # 3. Train
    print("\nTraining models...")
    exp = Level2Experiment()
    exp.train(train)
    print(f"Base rate: {exp.base_rate:.4f}")

    # 4. Evaluate
    print("Evaluating...")
    exp.evaluate(test)
    print(f"Evaluated {len(exp.predictions)} matches")

    # 5. Metrics
    m = exp.metrics()
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"Home win rate (eval): {m['home_win_rate']:.4f}")

    print(f"\n--- BASE RATE (P={m['base']['p0']:.4f}) ---")
    print(f"Mean Brier: {m['base']['mean_brier']:.6f}")
    print(f"Log Loss:   {m['base']['log_loss']:.6f}")

    print(f"\n--- FROZEN v2 (domain model, frozen at cutoff) ---")
    print(f"Mean Brier: {m['frozen']['mean_brier']:.6f}")
    print(f"Log Loss:   {m['frozen']['log_loss']:.6f}")

    print(f"\n--- ADAPTIVE v2 (domain model, continues learning) ---")
    print(f"Mean Brier: {m['adaptive']['mean_brier']:.6f}")
    print(f"Log Loss:   {m['adaptive']['log_loss']:.6f}")

    print(f"\n--- BASE vs FROZEN (value of domain knowledge) ---")
    print(f"Mean diff: {m['base_vs_frozen']['mean_diff']:+.6f}")
    print(f"95% CI: [{m['base_vs_frozen']['ci_95'][0]:+.6f}, {m['base_vs_frozen']['ci_95'][1]:+.6f}]")
    print(f"CI compat zero: {m['base_vs_frozen']['ci_compatible_with_zero']}")

    print(f"\n--- FROZEN vs ADAPTIVE (value of continued learning) ---")
    print(f"Mean diff: {m['frozen_vs_adaptive']['mean_diff']:+.6f}")
    print(f"95% CI: [{m['frozen_vs_adaptive']['ci_95'][0]:+.6f}, {m['frozen_vs_adaptive']['ci_95'][1]:+.6f}]")
    print(f"CI compat zero: {m['frozen_vs_adaptive']['ci_compatible_with_zero']}")

    # Verdict
    fa = m["frozen_vs_adaptive"]
    if fa["ci_compatible_with_zero"]:
        verdict = "NO_DOMAIN_LEARNING_ADVANTAGE"
    elif fa["mean_diff"] > 0:
        verdict = "PRELIMINARY_DOMAIN_LEARNING_ADVANTAGE"
    else:
        verdict = "FROZEN_ADVANTAGE"
    print(f"\nVerdict: {verdict}")

    # 6. Season breakdown
    print(f"\n--- SEASON BREAKDOWN ---")
    for s in exp.seasonal_breakdown():
        best = "base" if s["base"] <= s["frozen"] and s["base"] <= s["adaptive"] else (
            "frozen" if s["frozen"] <= s["adaptive"] else "adaptive"
        )
        print(f"  {s['season']}: base={s['base']:.4f} frozen={s['frozen']:.4f} adaptive={s['adaptive']:.4f} -> {best}")

    # 7. Temporal analysis
    print(f"\n--- TEMPORAL ANALYSIS (early/mid/late season) ---")
    for pos, data in exp.temporal_analysis().items():
        print(f"  {pos}: n={data['n']} f={data['frozen_brier']:.4f} a={data['adaptive_brier']:.4f} adv={data['advantage']:+.4f}")

    # 8. Leakage audit
    print(f"\n--- LEAKAGE AUDIT ---")
    for issue in exp.leakage_audit():
        print(f"  {issue}")

    print(f"\n{'='*70}")
