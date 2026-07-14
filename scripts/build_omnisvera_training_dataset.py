"""Compatibilidade: prefira `python -m omnisvera_model build-dataset`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from omnisvera_model.dataset import build_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approved", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--seed", type=int, default=7331)
    parser.add_argument("--dataset-version", default="v0.1.0")
    parser.add_argument("--experimental-ack")
    args = parser.parse_args()
    report = build_dataset(args.approved, args.output_dir, args.dataset_version,
                           seed=args.seed, experimental_ack=args.experimental_ack)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not report["blocked_training"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
