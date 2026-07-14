from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .io import sha256_file, write_json
from .paths import MODEL_ROOT

QUANTIZATIONS = {"Q4_K_M", "Q5_K_M", "F16"}


def merge(base_model: str, adapter: Path, output: Path, execute: bool = False) -> dict[str, Any]:
    report = {"base_model": base_model, "adapter": str(adapter.resolve()), "output": str(output.resolve()), "executed": execute}
    if not adapter.exists():
        report["error"] = "adapter ausente"; return report
    if not execute:
        report["status"] = "simulation_ok"; return report
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("dependências de merge ausentes") from exc
    model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.float16, local_files_only=True, low_cpu_mem_usage=True)
    merged = PeftModel.from_pretrained(model, str(adapter.resolve())).merge_and_unload()
    output.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(output, safe_serialization=True)
    AutoTokenizer.from_pretrained(base_model, local_files_only=True).save_pretrained(output)
    report["status"] = "merged"; return report


def export_gguf(model_dir: Path, converter: Path, output: Path, execute: bool = False) -> dict[str, Any]:
    command = [str(converter), str(model_dir.resolve()), "--outfile", str(output.resolve()), "--outtype", "f16"]
    report = {"command": command, "executed": execute}
    if not model_dir.exists(): report["error"] = "modelo mesclado ausente"
    elif not converter.exists(): report["error"] = "conversor llama.cpp ausente"
    elif execute:
        subprocess.run(command, check=True); report["status"] = "exported"; report["sha256"] = sha256_file(output)
    else: report["status"] = "simulation_ok"
    return report


def quantize(source: Path, quantizer: Path, output: Path, quantization: str, execute: bool = False) -> dict[str, Any]:
    if quantization not in QUANTIZATIONS: raise ValueError("quantização não suportada")
    command = [str(quantizer), str(source.resolve()), str(output.resolve()), quantization]
    report = {"command": command, "executed": execute, "quantization": quantization}
    if not source.exists(): report["error"] = "GGUF fonte ausente"
    elif not quantizer.exists(): report["error"] = "llama-quantize ausente"
    elif execute:
        subprocess.run(command, check=True); report["status"] = "quantized"; report["sha256"] = sha256_file(output)
    else: report["status"] = "simulation_ok"
    return report


def ollama_command(action: str, model: str, modelfile: Path | None = None, execute: bool = False) -> dict[str, Any]:
    if action == "create": command = ["ollama", "create", model, "-f", str((modelfile or Path()).resolve())]
    elif action == "test": command = ["ollama", "run", model, "Responda apenas: Omnisvera pronto."]
    elif action == "remove": command = ["ollama", "rm", model]
    elif action == "list": command = ["ollama", "list"]
    else: raise ValueError("ação Ollama inválida")
    available = shutil.which("ollama") is not None
    report = {"command": command, "ollama_available": available, "executed": execute}
    if execute and available:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        report.update({"returncode": result.returncode, "stdout": result.stdout[-2000:], "stderr": result.stderr[-2000:]})
    return report

