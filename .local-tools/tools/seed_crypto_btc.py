"""Explicit real historical seed; never invokes an AI or creates predictions."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from omnisvera_mcp.adapters.crypto_btc import candles, iso, SOURCE
from omnisvera_mcp.experience.crypto_btc import direction_state, PREDICTOR_ID, SCHEMA
from omnisvera_mcp.memory.store import MemoryStore


def seed(store, artifact_dir, *, fetch=candles, now=None):
    existing = store.experience_latest("crypto", PREDICTOR_ID, "v1")
    if existing:
        if not existing.get("integrity_ok") or existing["learned_state_schema"] != SCHEMA:
            raise ValueError("existing crypto experience invalid; refusing overwrite")
        return existing
    end = int(now or datetime.now(timezone.utc).timestamp()) // 3600 * 3600
    start = end - 240 * 3600
    rows = fetch(start, end, 3600)
    if len(rows) != 240 or [r[0] for r in rows] != list(range(start, end, 3600)):
        raise ValueError("expected 240 consecutive closed hourly candles")
    up = sum(b[4] > a[4] for a, b in zip(rows, rows[1:]))
    state = direction_state(up, len(rows) - 1 - up)
    raw = json.dumps(rows, separators=(",", ":"))
    digest = hashlib.sha256(raw.encode()).hexdigest()
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = artifact_dir / f"btc-usd-hourly-{digest}.json"
    if artifact.exists() and artifact.read_text(encoding="utf-8") != raw:
        raise ValueError("dataset artifact conflict")
    artifact.write_text(raw, encoding="utf-8")
    return store.experience_create(world_id="crypto", predictor_id=PREDICTOR_ID,
        predictor_version="v1", predictor_type="statistical", learned_state_schema=SCHEMA,
        learned_state=state, observations_used=state["observations_used"],
        metadata=dict(source=SOURCE, dataset_path=str(artifact.resolve()), dataset_sha256=digest,
                      start=iso(start), end_exclusive=iso(end), granularity_seconds=3600,
                      candles=len(rows), retrieved_at=iso(datetime.now(timezone.utc).timestamp()),
                      method="consecutive closed hourly closes; ties count as down; Beta(1,1)"),
        created_by="seed_crypto_btc")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--artifacts", required=True)
    args = parser.parse_args()
    print(json.dumps(seed(MemoryStore(Path(args.db)), args.artifacts), indent=2))
