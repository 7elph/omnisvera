"""Compatibilidade: prefira `python -m omnisvera_model train-lora`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from omnisvera_model.training import train


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "omnisvera-model" / "config" / "lora-production.json")
    parser.add_argument("--dataset-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--resume")
    parser.add_argument("--acknowledgement")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    result = train(args.config, args.dataset_dir, args.output_dir, args.resume,
                   args.acknowledgement, args.preflight_only)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
