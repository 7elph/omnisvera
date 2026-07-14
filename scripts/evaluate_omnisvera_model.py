"""Compatibilidade: prefira `python -m omnisvera_model evaluate`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from omnisvera_model.evaluation import evaluate_models


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--models",nargs="+",default=["qwen2:1.5b"])
    parser.add_argument("--base-url",default="http://localhost:11434")
    parser.add_argument("--cases",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--timeout",type=int,default=120)
    parser.add_argument("--limit",type=int)
    parser.add_argument("--validate-only",action="store_true")
    args=parser.parse_args()
    report=evaluate_models(args.models,args.base_url,args.cases,args.output,args.timeout,args.validate_only,args.limit)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
