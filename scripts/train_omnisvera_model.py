from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "omnisvera-model" / "artifacts" / "dataset"
DEFAULT_OUTPUT = ROOT / "omnisvera-model" / "artifacts" / "training"


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Treina o Llama-3.2-Omnisvera-3B")
    parser.add_argument("--model-id", default="meta-llama/Llama-3.2-3B-Instruct")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mode", choices=("full", "lora"), default="full")
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--max-length", type=int, default=1536)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation", type=int, default=16)
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--allow-cpu", action="store_true")
    args = parser.parse_args()

    try:
        import torch
        from datasets import Dataset
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:
        raise SystemExit("Instale omnisvera-model/requirements-train.txt antes do treino") from exc

    if not torch.cuda.is_available() and not args.allow_cpu:
        raise SystemExit(
            "GPU CUDA não encontrada. O notebook atual deve preparar/testar o dataset, não treinar 3B. "
            "Use uma máquina de treinamento ou --allow-cpu por sua conta e risco."
        )

    dataset_dir = args.dataset_dir.resolve()
    train_rows = load_rows(dataset_dir / "train.jsonl")
    eval_rows = load_rows(dataset_dir / "eval.jsonl")
    manifest_path = dataset_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not manifest.get("production_ready"):
            raise SystemExit("Dataset marcado como não pronto para produção; aumente e revise os exemplos curados")

    tokenizer = AutoTokenizer.from_pretrained(args.model_id, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    def prepare(rows: list[dict]) -> Dataset:
        texts = [
            tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=False)
            for row in rows
        ]
        dataset = Dataset.from_dict({"text": texts})

        def tokenize(batch: dict) -> dict:
            encoded = tokenizer(batch["text"], truncation=True, max_length=args.max_length)
            encoded["labels"] = [list(ids) for ids in encoded["input_ids"]]
            return encoded

        return dataset.map(tokenize, batched=True, remove_columns=["text"])

    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=dtype if torch.cuda.is_available() else torch.float32,
        low_cpu_mem_usage=True,
    )
    if args.mode == "lora":
        try:
            from peft import LoraConfig, get_peft_model
        except ImportError as exc:
            raise SystemExit("PEFT não está instalado") from exc
        model = get_peft_model(
            model,
            LoraConfig(
                r=32,
                lora_alpha=64,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"),
            ),
        )

    learning_rate = args.learning_rate or (5e-6 if args.mode == "full" else 1e-4)
    output_dir = args.output_dir.resolve() / args.mode
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=learning_rate,
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch",
        report_to="none",
        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        fp16=torch.cuda.is_available() and not torch.cuda.is_bf16_supported(),
        gradient_checkpointing=True,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=prepare(train_rows),
        eval_dataset=prepare(eval_rows),
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    trainer.save_model(str(output_dir / "final"))
    tokenizer.save_pretrained(str(output_dir / "final"))
    print(f"Modelo salvo em {output_dir / 'final'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
