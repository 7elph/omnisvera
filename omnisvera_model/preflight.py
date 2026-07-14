from __future__ import annotations

import importlib.metadata
import json
import platform
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from .io import read_json, sha256_file
from .paths import MODEL_ROOT, ROOT


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def inspect_hardware() -> dict[str, Any]:
    cuda = False
    gpu_name = None
    vram_gb = 0.0
    try:
        import torch
        cuda = bool(torch.cuda.is_available())
        if cuda:
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = round(torch.cuda.get_device_properties(0).total_memory / 1024 ** 3, 2)
    except ImportError:
        pass
    memory_gb = None
    try:
        import psutil
        memory_gb = round(psutil.virtual_memory().total / 1024 ** 3, 2)
    except ImportError:
        pass
    return {
        "python": sys.version.split()[0], "platform": platform.platform(), "cuda": cuda,
        "gpu": gpu_name, "vram_gb": vram_gb, "ram_gb": memory_gb,
        "disk_free_gb": round(shutil.disk_usage(ROOT).free / 1024 ** 3, 2),
    }


def run_preflight(config_path: Path, dataset_manifest: Path | None = None) -> dict[str, Any]:
    config = read_json(config_path)
    mode = str(config.get("training_mode") or "lora")
    hardware = inspect_hardware()
    packages = {name: _package_version(name) for name in ("torch", "transformers", "datasets", "peft", "accelerate", "safetensors")}
    missing = [name for name, version in packages.items() if version is None]
    if mode == "qlora" and _package_version("bitsandbytes") is None:
        missing.append("bitsandbytes")
    manifest_path = dataset_manifest or MODEL_ROOT / "artifacts" / "dataset" / "manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    problems: list[str] = []
    if missing:
        problems.append("dependências ausentes: " + ", ".join(missing))
    if not manifest:
        problems.append("manifesto de dataset ausente")
    elif manifest.get("blocked_training") and not config.get("experimental_only"):
        problems.append("dataset bloqueado para treinamento real")
    if not hardware["cuda"]:
        problems.append("CUDA indisponível")
    required_vram = 10 if mode in {"lora", "qlora"} else 40
    if hardware["vram_gb"] < required_vram:
        problems.append(f"VRAM insuficiente: {hardware['vram_gb']} GB; referência {required_vram} GB")
    if hardware["disk_free_gb"] < 20:
        problems.append("menos de 20 GB livres")
    if not config.get("base_model"):
        problems.append("base_model ausente")
    if not config.get("license_acknowledged"):
        problems.append("licença/acesso do modelo-base ainda não confirmados")
    if sys.version_info >= (3, 13):
        problems.append("Python 3.13+ pode não ser suportado pela toolchain; use Python 3.10-3.12")
    try:
        probe_dir = MODEL_ROOT / "artifacts"
        probe_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=probe_dir, delete=True):
            pass
    except OSError:
        problems.append("diretório de artefatos sem permissão de escrita")
    report = {
        "ok": not problems, "config": str(config_path.resolve()), "training_mode": mode,
        "hardware": hardware, "dependencies": packages, "dataset_manifest": str(manifest_path.resolve()),
        "dataset_blocked": bool(manifest.get("blocked_training", True)), "problems": problems,
        "remote_command": f"python -m omnisvera_model train-lora --config {config_path.as_posix()}",
    }
    return report


def validate_training_config(config: dict[str, Any]) -> list[str]:
    required = {
        "experiment_name", "training_mode", "base_model", "seed", "epochs", "batch_size",
        "gradient_accumulation", "learning_rate", "sequence_length",
        "early_stopping_patience", "experimental_only",
    }
    errors = [f"campo ausente: {key}" for key in sorted(required - set(config))]
    if config.get("training_mode") not in {"lora", "qlora", "full"}:
        errors.append("training_mode inválido")
    if config.get("training_mode") in {"lora", "qlora"}:
        for key in ("lora_rank", "lora_alpha", "lora_dropout"):
            if key not in config:
                errors.append(f"campo LoRA ausente: {key}")
    if "warmup_steps" not in config and "warmup_ratio" not in config:
        errors.append("warmup_steps ou warmup_ratio é obrigatório")
    if config.get("save_strategy", "steps") == "steps" and "checkpoint_interval" not in config:
        errors.append("checkpoint_interval é obrigatório para save_strategy=steps")
    if config.get("evaluation_strategy", "steps") == "steps" and "eval_interval" not in config:
        errors.append("eval_interval é obrigatório para evaluation_strategy=steps")
    return errors
