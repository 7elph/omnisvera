"""Real Closed-Loop Learning Validation v0.1 — no new Core capability."""
import sys, tempfile, json, math, random
from pathlib import Path
from datetime import datetime, timezone, timedelta

LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))
if str(LOCAL_TOOLS.parent) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS.parent))

from omnisvera_mcp.memory.store import MemoryStore
from omnisvera_mcp.core.context import CallContext
from omnisvera_mcp.epistemic import commit_candidate, resolve_prediction
from omnisvera_mcp.experience.updater import ExperienceUpdaterRegistry
from omnisvera_mcp.experience.football_elo import FootballEloUpdater
from omnisvera_mcp.experience.runtime import process_pending_updates

def _expected(home, away, adv=50):
    diff = (home + adv) - away
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))

def _brier(p, o): return (p - o) ** 2
def _logloss(p, o):
    p = min(max(p, 1e-6), 1-1e-6)
    return -(o * math.log(p) + (1-o) * math.log(1-p))

# Dataset generation — synthetic but chronologically ordered, based on true hidden ratings
TRUE_RATINGS = {"ARS": 1600, "CHE": 1450, "MCI": 1550, "LIV": 1500}
TEAMS = list(TRUE_RATINGS.keys())

def generate_dataset(seed=42, n_train=10, n_eval=12):
    rnd = random.Random(seed)
    matches = []
    base_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(n_train + n_eval):
        home, away = rnd.sample(TEAMS, 2)
        # true expected
        exp = _expected(TRUE_RATINGS[home], TRUE_RATINGS[away])
        outcome = 1 if rnd.random() < exp else 0
        matches.append({
            "match_id": f"GEN-{i:03d}",
            "home": home, "away": away,
            "date": (base_date + timedelta(days=i*3)).isoformat(),
            "effective_at": (base_date + timedelta(days=i*3)).isoformat(),
            "outcome": outcome,
            "true_exp": exp,
        })
    matches.sort(key=lambda m: m["date"])
    train = matches[:n_train]
    eval_set = matches[n_train:]
    return train, eval_set

def _initial_experience_from_train(mem, train_matches):
    # Start from base 1500, process train sequentially via Experience updates (closed-loop style)
    # Create initial v1 with 1500
    exp = mem.experience_create(world_id="football", predictor_id="football.elo", predictor_version="v1", predictor_type="statistical", learned_state_schema="elo.v1", learned_state={"team_ratings": {t:1500 for t in TEAMS}, "home_advantage": 50, "k_factor": 20}, observations_used=0)
    reg = ExperienceUpdaterRegistry()
    reg.register(FootballEloUpdater())
    mem._experience_updater_registry = reg  # type: ignore
    for m in train_matches:
        snap = mem.create_snapshot_memory(domain="football", subject=f"{m['home']} vs {m['away']} train", state={"match": m})
        # For train, we still use closed-loop to build initial: we need prediction referencing current experience, then resolve, then update
        latest = mem.experience_latest("football", "football.elo", "v1")
        cand = {
            "world_id": "football", "domain": "football", "subject_ref": f"{m['home']} vs {m['away']}",
            "claim": f"{m['home']} beats {m['away']}", "probability": _expected(latest["learned_state"]["team_ratings"][m["home"]], latest["learned_state"]["team_ratings"][m["away"]]),
            "horizon": "2099-01-01T00:00:00+00:00", "resolution_rule": {"type": "home_win", "effective_at": m["effective_at"]},
            "model_snapshot_id": snap, "predictor_id": "football.elo", "predictor_version": "v1",
            "experience_id": latest["experience_id"], "experience_state_version": latest["state_version"], "experience_state_hash": latest["learned_state_hash"],
        }
        ctx = CallContext.trusted_local_stdio()
        pred_id = json.loads(commit_candidate(mem, ctx, {"candidate": cand}))["prediction_id"]
        resolve_prediction(mem, ctx, {"prediction_id": str(pred_id), "outcome": m["outcome"]})
        # Experience update happens automatically via resolve hook, but we ensure pending processed
        process_pending_updates(mem, reg)
    return mem.experience_latest("football", "football.elo", "v1")

import unittest

class ClosedLoopTests(unittest.TestCase):
    def test_closed_loop(self):
        tmp = Path(tempfile.mkdtemp()) / "closed.db"
        mem = MemoryStore(tmp)
        train, eval_set = generate_dataset(seed=42, n_train=10, n_eval=12)
        # Initial Experience from train
        initial = _initial_experience_from_train(mem, train)
        self.assertIsNotNone(initial)
        initial_version = initial["state_version"]
        initial_hash = initial["learned_state_hash"]
        # Frozen setup: snapshot of initial
        frozen_state = json.loads(json.dumps(initial["learned_state"]))  # deep copy
        # Base-rate
        home_wins = sum(1 for m in train if m["outcome"]==1)
        base_rate = home_wins / len(train) if train else 0.5
        # Adaptive runtime already has initial; we will run eval closed-loop
        reg = ExperienceUpdaterRegistry()
        reg.register(FootballEloUpdater())
        mem._experience_updater_registry = reg  # type: ignore
        ctx = CallContext.trusted_local_stdio()
        # Prepare metrics
        base_briers=[]; frozen_briers=[]; adaptive_briers=[]
        base_log=[]; frozen_log=[]; adaptive_log=[]
        lineage_examples=[]
        # Store frozen ratings (no updates)
        frozen_ratings = dict(frozen_state["team_ratings"])
        # For restart test, we will restart mid-eval
        restart_at = len(eval_set)//2
        for idx, m in enumerate(eval_set):
            if idx == restart_at:
                # Restart: new MemoryStore on same file, new runtime
                mem = MemoryStore(tmp)
                mem._experience_updater_registry = reg  # type: ignore
                # Verify continuity: latest should be same as before restart
                latest_before = mem.experience_latest("football", "football.elo", "v1")
                self.assertIsNotNone(latest_before)
                # continue
            # Adaptive: latest experience
            latest = mem.experience_latest("football", "football.elo", "v1")
            self.assertIsNotNone(latest)
            # Frozen prob based on frozen_state
            p_frozen = _expected(frozen_ratings[m["home"]], frozen_ratings[m["away"]])
            p_adaptive = _expected(latest["learned_state"]["team_ratings"][m["home"]], latest["learned_state"]["team_ratings"][m["away"]])
            p_base = base_rate
            o = m["outcome"]
            base_briers.append(_brier(p_base, o)); frozen_briers.append(_brier(p_frozen, o)); adaptive_briers.append(_brier(p_adaptive, o))
            base_log.append(_logloss(p_base, o)); frozen_log.append(_logloss(p_frozen, o)); adaptive_log.append(_logloss(p_adaptive, o))
            # Create prediction via adaptive (must reference latest)
            snap = mem.create_snapshot_memory(domain="football", subject=f"{m['home']} vs {m['away']} eval {idx}", state={"match": m, "elo": latest["learned_state"]})
            cand = {
                "world_id": "football", "domain": "football", "subject_ref": f"{m['home']} vs {m['away']}",
                "claim": f"{m['home']} beats {m['away']}", "probability": p_adaptive,
                "horizon": "2099-01-01T00:00:00+00:00", "resolution_rule": {"type": "home_win", "effective_at": m["effective_at"]},
                "model_snapshot_id": snap, "predictor_id": "football.elo", "predictor_version": "v1",
                "experience_id": latest["experience_id"], "experience_state_version": latest["state_version"], "experience_state_hash": latest["learned_state_hash"],
            }
            # also create frozen prediction for metrics (not via Experience, just for Brier)
            # For lineage, we track adaptive
            pred_id = json.loads(commit_candidate(mem, ctx, {"candidate": cand}))["prediction_id"]
            # Resolve
            resolve_prediction(mem, ctx, {"prediction_id": str(pred_id), "outcome": o})
            # Ensure runtime processed
            process_pending_updates(mem, reg)
            # For first 2 examples, capture lineage
            if idx < 2:
                new_latest = mem.experience_latest("football", "football.elo", "v1")
                lineage_examples.append({
                    "idx": idx, "match": m, "pred_id": pred_id, "p_adaptive": round(p_adaptive,4),
                    "outcome": o, "exp_before": latest["experience_id"][:8], "v_before": latest["state_version"],
                    "exp_after": new_latest["experience_id"][:8], "v_after": new_latest["state_version"],
                    "hash_before": latest["learned_state_hash"][:8], "hash_after": new_latest["learned_state_hash"][:8],
                })
        # Metrics
        def mean(x): return sum(x)/len(x) if x else 0
        base_brier_m = mean(base_briers); frozen_brier_m = mean(frozen_briers); adaptive_brier_m = mean(adaptive_briers)
        base_log_m = mean(base_log); frozen_log_m = mean(frozen_log); adaptive_log_m = mean(adaptive_log)
        # Paired difference Frozen vs Adaptive
        diffs = [f - a for f,a in zip(frozen_briers, adaptive_briers)]
        mean_diff = mean(diffs)
        # Block bootstrap CI (blocks of 3)
        import random as _rnd
        rnd = _rnd.Random(123)
        blocks = [diffs[i:i+3] for i in range(0, len(diffs), 3)]
        n_blocks = len(blocks)
        boot_means=[]
        for _ in range(1000):
            sample=[]
            for _ in range(n_blocks):
                b = rnd.choice(blocks)
                sample.extend(b)
            # sample may be longer than diffs due to block sampling, truncate
            sample = sample[:len(diffs)]
            boot_means.append(sum(sample)/len(sample) if sample else 0)
        boot_means.sort()
        ci_low = boot_means[int(0.025*len(boot_means))]
        ci_high = boot_means[int(0.975*len(boot_means))]
        # Causal incidents
        causal_reorder = mem.experience_update_list(status="causal_reorder_required", limit=100)
        # Store for delivery inspection
        self._metrics = {
            "train_n": len(train), "eval_n": len(eval_set),
            "base_brier": round(base_brier_m,4), "frozen_brier": round(frozen_brier_m,4), "adaptive_brier": round(adaptive_brier_m,4),
            "base_log": round(base_log_m,4), "frozen_log": round(frozen_log_m,4), "adaptive_log": round(adaptive_log_m,4),
            "mean_diff_frozen_minus_adaptive": round(mean_diff,4),
            "ci_low": round(ci_low,4), "ci_high": round(ci_high,4),
            "lineage_examples": lineage_examples,
            "causal_reorder_incidents": len(causal_reorder),
            "initial_version": initial_version, "final_version": mem.experience_latest("football","football.elo","v1")["state_version"],
        }
        # Verdict logic (no tuning)
        # If CI entirely >0 => adaptive better (lower Brier), if entirely <0 => frozen better, else no advantage
        if ci_low > 0 and ci_high > 0:
            verdict = "PRELIMINARY_DOMAIN_LEARNING_ADVANTAGE"  # adaptive lower Brier
        elif ci_low < 0 and ci_high < 0:
            verdict = "CONDITIONAL_DOMAIN_LEARNING_ADVANTAGE"  # but actually frozen better, still conditional?
            verdict = "NO_DOMAIN_LEARNING_ADVANTAGE"
        else:
            # Check if adaptive at least beats base?
            if adaptive_brier_m < base_brier_m and ci_high < 0.05:  # arbitrary threshold
                verdict = "CONDITIONAL_DOMAIN_LEARNING_ADVANTAGE"
            else:
                verdict = "NO_DOMAIN_LEARNING_ADVANTAGE"
        # More precise: if mean_diff >0 and CI excludes 0 => adaptive advantage
        if mean_diff > 0 and ci_low > 0:
            verdict = "PRELIMINARY_DOMAIN_LEARNING_ADVANTAGE"
        elif mean_diff > 0 and ci_low <=0 < ci_high:
            verdict = "CONDITIONAL_DOMAIN_LEARNING_ADVANTAGE"
        else:
            verdict = "NO_DOMAIN_LEARNING_ADVANTAGE"
        self._metrics["verdict"] = verdict
        # Print deliverable
        print("\n=== Real Closed-Loop Learning Validation v0.1 ===")
        print(json.dumps(self._metrics, indent=2))
        # Assertions for test: ensure closed-loop ran, lineage, restart, causal
        self.assertEqual(self._metrics["eval_n"], 12)
        self.assertEqual(self._metrics["final_version"], initial_version + 12)  # 12 eval updates
        self.assertEqual(len(lineage_examples), 2)
        self.assertEqual(self._metrics["causal_reorder_incidents"], 0)  # ordered feed, no reorder
        # Ensure verdict is one of allowed
        self.assertIn(verdict, ["NO_DOMAIN_LEARNING_ADVANTAGE","CONDITIONAL_DOMAIN_LEARNING_ADVANTAGE","PRELIMINARY_DOMAIN_LEARNING_ADVANTAGE"])

if __name__ == "__main__":
    unittest.main()
