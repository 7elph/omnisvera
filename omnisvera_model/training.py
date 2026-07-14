from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .io import read_json, read_jsonl, write_json
from .manifest import create_manifest
from .paths import MODEL_ROOT
from .preflight import run_preflight, validate_training_config

SMOKE_ACK = "I_UNDERSTAND_THIS_IS_EXPERIMENTAL_NOT_FOR_PRODUCTION"
FULL_ACK = "I_UNDERSTAND_FULL_TRAINING_REQUIRES_PRODUCTION_HARDWARE"


def train(config_path: Path, dataset_dir: Path | None = None, output_dir: Path | None = None,
          resume: str | None = None, acknowledgement: str | None = None,
          preflight_only: bool = False) -> dict[str, Any]:
    config = read_json(config_path)
    errors = validate_training_config(config)
    if errors:
        raise ValueError("; ".join(errors))
    dataset = dataset_dir or MODEL_ROOT / "artifacts" / "dataset"
    dataset_manifest = dataset / "manifest.json"
    report = run_preflight(config_path, dataset_manifest)
    experiment = str(config["experiment_name"])
    output = output_dir or MODEL_ROOT / "artifacts" / "training" / experiment
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "preflight.json", report)
    if preflight_only:
        return {"status": "preflight_only", "preflight": report}
    experimental = bool(config.get("experimental_only"))
    if experimental and acknowledgement != SMOKE_ACK:
        raise RuntimeError(f"smoke test exige --acknowledgement {SMOKE_ACK}")
    if config["training_mode"] == "full" and acknowledgement != FULL_ACK:
        raise RuntimeError(f"full training exige --acknowledgement {FULL_ACK}")
    if not report["ok"]:
        raise RuntimeError("preflight falhou: " + "; ".join(report["problems"]))
    manifest_data = read_json(dataset_manifest)
    if manifest_data.get("blocked_training") and not experimental:
        raise RuntimeError("treinamento real bloqueado pelo manifesto do dataset")
    if experimental and not manifest_data.get("experimental_export"):
        raise RuntimeError("dataset experimental não foi construído com reconhecimento explícito")

    try:
        import torch
        from datasets import Dataset
        from transformers import (AutoModelForCausalLM, AutoTokenizer,
            DataCollatorForLanguageModeling, EarlyStoppingCallback, Trainer, TrainingArguments)
    except ImportError as exc:
        raise RuntimeError("dependências de treinamento ausentes") from exc

    local_only = not bool(config.get("allow_model_download", False))
    revision = str(config.get("base_model_revision") or "main")
    tokenizer = AutoTokenizer.from_pretrained(config["base_model"], revision=revision, use_fast=True, local_files_only=local_only)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    def prepare(path: Path) -> Any:
        rows = read_jsonl(path)
        texts = [tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=False) for row in rows]
        ds = Dataset.from_dict({"text": texts})
        def tokenize(batch: dict[str, list[str]]) -> dict[str, Any]:
            encoded = tokenizer(batch["text"], truncation=True, max_length=int(config["sequence_length"]))
            encoded["labels"] = [list(ids) for ids in encoded["input_ids"]]
            return encoded
        return ds.map(tokenize, batched=True, remove_columns=["text"])

    mode = config["training_mode"]
    model_kwargs: dict[str, Any] = {"local_files_only": local_only, "low_cpu_mem_usage": True, "revision": revision}
    precision = str(config.get("precision") or "bf16")
    model_kwargs["dtype"] = torch.bfloat16 if precision == "bf16" else torch.float16
    if mode == "qlora":
        try:
            from transformers import BitsAndBytesConfig
            model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")
        except ImportError as exc:
            raise RuntimeError("QLoRA exige bitsandbytes") from exc
    model = AutoModelForCausalLM.from_pretrained(config["base_model"], **model_kwargs)
    if mode in {"lora", "qlora"}:
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        if mode == "qlora":
            model = prepare_model_for_kbit_training(model)
        model = get_peft_model(model, LoraConfig(
            r=int(config["lora_rank"]), lora_alpha=int(config["lora_alpha"]),
            lora_dropout=float(config["lora_dropout"]), bias="none", task_type="CAUSAL_LM",
            target_modules=config.get("target_modules") or ["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
        ))
    save_strategy = str(config.get("save_strategy") or "steps")
    evaluation_strategy = str(config.get("evaluation_strategy") or "steps")
    load_best = bool(config.get("load_best_model_at_end", True))
    argument_values: dict[str, Any] = dict(
        output_dir=str(output / "checkpoints"), seed=int(config["seed"]),
        num_train_epochs=float(config["epochs"]), per_device_train_batch_size=int(config["batch_size"]),
        per_device_eval_batch_size=int(config.get("per_device_eval_batch_size", 1)),
        gradient_accumulation_steps=int(config["gradient_accumulation"]),
        learning_rate=float(config["learning_rate"]),
        logging_steps=max(1, int(config.get("logging_interval", 10))),
        logging_strategy=str(config.get("logging_strategy") or "steps"),
        save_strategy=save_strategy, eval_strategy=evaluation_strategy, load_best_model_at_end=load_best,
        report_to="none", bf16=precision == "bf16", fp16=precision == "fp16",
        gradient_checkpointing=bool(config.get("gradient_checkpointing", True)),
        save_total_limit=int(config.get("save_total_limit", 3)),
        metric_for_best_model="eval_loss", greater_is_better=False,
    )
    if "warmup_steps" in config:
        argument_values["warmup_steps"] = int(config["warmup_steps"])
    else:
        argument_values["warmup_ratio"] = float(config.get("warmup_ratio", 0.0))
    if save_strategy == "steps":
        argument_values["save_steps"] = int(config["checkpoint_interval"])
    if evaluation_strategy == "steps":
        argument_values["eval_steps"] = int(config["eval_interval"])
    args = TrainingArguments(**argument_values)
    callbacks = []
    if load_best and evaluation_strategy != "no" and int(config.get("early_stopping_patience", 0)) > 0:
        callbacks.append(EarlyStoppingCallback(early_stopping_patience=int(config["early_stopping_patience"])))
    trainer = Trainer(
        model=model, args=args, train_dataset=prepare(dataset / "train.jsonl"),
        eval_dataset=prepare(dataset / "eval.jsonl"),
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
        callbacks=callbacks,
    )
    started = time.monotonic()
    result = trainer.train(resume_from_checkpoint=resume or None)
    final = output / "final"
    trainer.save_model(str(final)); tokenizer.save_pretrained(str(final))
    history = list(trainer.state.log_history)
    loss_by_epoch: list[dict[str, Any]] = []
    epochs = sorted({float(item["epoch"]) for item in history if item.get("epoch") is not None})
    for epoch in epochs:
        entries = [item for item in history if item.get("epoch") is not None and float(item["epoch"]) == epoch]
        train_losses = [float(item["loss"]) for item in entries if item.get("loss") is not None]
        eval_losses = [float(item["eval_loss"]) for item in entries if item.get("eval_loss") is not None]
        loss_by_epoch.append({
            "epoch": epoch,
            "train_loss": train_losses[-1] if train_losses else None,
            "eval_loss": eval_losses[-1] if eval_losses else None,
        })
    metrics = dict(result.metrics)
    metrics.update({
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "global_step": int(trainer.state.global_step),
        "expected_optimizer_updates": int(config.get("expected_optimizer_updates") or 0),
        "loss_by_epoch": loss_by_epoch,
        "log_history": history,
    })
    write_json(output / "metrics.json", metrics)
    manifest = create_manifest(config_path, dataset_manifest,
        str(config.get("package_classification") or "EXPERIMENTAL_NOT_FOR_PRODUCTION") if experimental else "trained",
        output / "training_manifest.json", checkpoints=[str(final)], metrics=metrics)
    return {"status": manifest["status"], "output": str(final), "metrics": metrics}
