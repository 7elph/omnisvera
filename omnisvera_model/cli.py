from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .curation import capture, review
from .dataset import build_dataset, coverage_report, migrate_legacy_dataset, validate_rows
from .exporting import export_gguf, merge, ollama_command, quantize
from .evaluation import evaluate_models
from .io import read_json, read_jsonl, sha256_file, write_json
from .paths import DATA_ROOT, LEGACY_DATASET, MODEL_ROOT, REGISTRY_PATH, ensure_runtime_dirs
from .preflight import run_preflight
from .registry import promote, register, rollback
from .training import train


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m omnisvera_model", description="Ciclo de vida do Llama-3.2-Omnisvera-3B")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("validate-data"); p.add_argument("--source", type=_path, default=LEGACY_DATASET); p.add_argument("--legacy", action="store_true")
    p = sub.add_parser("migrate-legacy"); p.add_argument("--source", type=_path, default=LEGACY_DATASET); p.add_argument("--output", type=_path)
    p = sub.add_parser("capture-example"); p.add_argument("--input", type=_path, required=True); p.add_argument("--output", type=_path)
    p = sub.add_parser("review-example"); p.add_argument("--source", type=_path, required=True); p.add_argument("--id", required=True); p.add_argument("--action", choices=["approve","reject","edit"], required=True); p.add_argument("--reviewer", required=True); p.add_argument("--ideal-response"); p.add_argument("--category"); p.add_argument("--persona-id"); p.add_argument("--quality-score", type=int); p.add_argument("--contains-secret", choices=["true","false"]); p.add_argument("--mark-leak",action="store_true"); p.add_argument("--mark-invention",action="store_true")
    p = sub.add_parser("approve-example"); p.add_argument("--source", type=_path, required=True); p.add_argument("--id", required=True); p.add_argument("--reviewer", required=True); p.add_argument("--quality-score", type=int, default=2); p.add_argument("--ideal-response")
    p = sub.add_parser("build-dataset"); p.add_argument("--approved", type=_path); p.add_argument("--output", type=_path); p.add_argument("--version", default="v0.1.0"); p.add_argument("--seed", type=int, default=7331); p.add_argument("--experimental-ack")
    p = sub.add_parser("coverage-report"); p.add_argument("--approved", type=_path); p.add_argument("--output", type=_path)
    p = sub.add_parser("freeze-eval"); p.add_argument("--source", type=_path, default=MODEL_ROOT / "evaluation" / "frozen_eval_v1.json"); p.add_argument("--manifest", type=_path, default=MODEL_ROOT / "evaluation" / "frozen_eval_v1.manifest.json")
    p = sub.add_parser("preflight"); p.add_argument("--config", type=_path, required=True); p.add_argument("--output", type=_path)
    for name in ("train-lora", "train-full", "resume"):
        p = sub.add_parser(name); p.add_argument("--config", type=_path, required=True); p.add_argument("--dataset-dir", type=_path); p.add_argument("--output-dir", type=_path); p.add_argument("--checkpoint"); p.add_argument("--acknowledgement"); p.add_argument("--preflight-only", action="store_true")
    p = sub.add_parser("merge"); p.add_argument("--base-model", required=True); p.add_argument("--adapter", type=_path, required=True); p.add_argument("--output", type=_path, required=True); p.add_argument("--execute", action="store_true")
    p = sub.add_parser("export-gguf"); p.add_argument("--model-dir", type=_path, required=True); p.add_argument("--converter", type=_path, required=True); p.add_argument("--output", type=_path, required=True); p.add_argument("--execute", action="store_true")
    p = sub.add_parser("quantize"); p.add_argument("--source", type=_path, required=True); p.add_argument("--quantizer", type=_path, required=True); p.add_argument("--output", type=_path, required=True); p.add_argument("--type", choices=["Q4_K_M","Q5_K_M","F16"], default="Q4_K_M"); p.add_argument("--execute", action="store_true")
    p = sub.add_parser("evaluate"); p.add_argument("--models", nargs="+", required=True); p.add_argument("--base-url", default="http://localhost:11434"); p.add_argument("--cases", type=_path); p.add_argument("--output", type=_path); p.add_argument("--timeout", type=int, default=120); p.add_argument("--limit",type=int); p.add_argument("--validate-only", action="store_true")
    p = sub.add_parser("ollama-create"); p.add_argument("--model", default="llama-3.2-omnisvera-3b"); p.add_argument("--modelfile", type=_path, required=True); p.add_argument("--execute", action="store_true")
    p = sub.add_parser("ollama-test"); p.add_argument("--model", default="llama-3.2-omnisvera-3b"); p.add_argument("--execute", action="store_true")
    p = sub.add_parser("ollama-remove"); p.add_argument("--model", default="llama-3.2-omnisvera-3b"); p.add_argument("--execute", action="store_true")
    p = sub.add_parser("ollama-list"); p.add_argument("--execute", action="store_true")
    p = sub.add_parser("register"); p.add_argument("--model-id", required=True); p.add_argument("--metadata", type=_path, required=True)
    p = sub.add_parser("promote"); p.add_argument("--model-id", required=True); p.add_argument("--gates", type=_path, required=True)
    sub.add_parser("rollback")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ensure_runtime_dirs(); command = args.command
    if command == "validate-data":
        rows = read_jsonl(args.source)
        if args.legacy: rows = [__import__("omnisvera_model.schema", fromlist=["migrate_legacy"]).migrate_legacy(row) for row in rows]
        errors = validate_rows(rows, strict_approval=not args.legacy); _print({"rows":len(rows),"errors":errors,"valid":not errors}); return 0 if not errors else 1
    if command == "migrate-legacy": _print({"migrated":len(migrate_legacy_dataset(args.source,args.output))}); return 0
    if command == "capture-example": _print(capture(read_json(args.input),args.output)); return 0
    if command in {"review-example","approve-example"}:
        action = "approve" if command == "approve-example" else args.action
        secret = None if not hasattr(args,"contains_secret") or args.contains_secret is None else args.contains_secret == "true"
        _print(review(args.source,args.id,action,args.reviewer,args.ideal_response,getattr(args,"category",None),getattr(args,"persona_id",None),secret,args.quality_score,getattr(args,"mark_leak",False),getattr(args,"mark_invention",False))); return 0
    if command == "build-dataset": _print(build_dataset(args.approved,args.output,args.version,seed=args.seed,experimental_ack=args.experimental_ack)); return 0
    if command == "coverage-report":
        report=coverage_report(args.approved); _print(report); 
        if args.output: write_json(args.output,report)
        return 0
    if command == "freeze-eval":
        payload=read_json(args.source); manifest={"version":payload.get("version"),"cases":len(payload.get("cases") or []),"sha256":sha256_file(args.source),"immutable":True}; write_json(args.manifest,manifest); _print(manifest); return 0
    if command == "preflight":
        report=run_preflight(args.config); _print(report); 
        if args.output: write_json(args.output,report)
        return 0 if report["ok"] else 2
    if command in {"train-lora","train-full","resume"}:
        mode=read_json(args.config).get("training_mode")
        if command == "train-lora" and mode not in {"lora","qlora"}: raise ValueError("train-lora exige config lora/qlora")
        if command == "train-full" and mode != "full": raise ValueError("train-full exige config full")
        result=train(args.config,args.dataset_dir,args.output_dir,args.checkpoint,args.acknowledgement,args.preflight_only); _print(result); return 0
    if command == "merge": _print(merge(args.base_model,args.adapter,args.output,args.execute)); return 0
    if command == "export-gguf": _print(export_gguf(args.model_dir,args.converter,args.output,args.execute)); return 0
    if command == "quantize": _print(quantize(args.source,args.quantizer,args.output,args.type,args.execute)); return 0
    if command == "evaluate": _print(evaluate_models(args.models,args.base_url,args.cases,args.output,args.timeout,args.validate_only,args.limit)); return 0
    if command == "ollama-create": _print(ollama_command("create",args.model,args.modelfile,args.execute)); return 0
    if command == "ollama-test": _print(ollama_command("test",args.model,None,args.execute)); return 0
    if command == "ollama-remove": _print(ollama_command("remove",args.model,None,args.execute)); return 0
    if command == "ollama-list": _print(ollama_command("list","",None,args.execute)); return 0
    if command == "register": _print(register(args.model_id,read_json(args.metadata))); return 0
    if command == "promote": _print(promote(args.model_id,read_json(args.gates))); return 0
    if command == "rollback": _print({"production_model":rollback()}); return 0
    return 2
