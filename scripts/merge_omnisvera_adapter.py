from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Mescla um adapter LoRA Omnisvera ao Llama-base")
    parser.add_argument("--base-model", default="meta-llama/Llama-3.2-3B-Instruct")
    parser.add_argument(
        "--adapter",
        type=Path,
        default=ROOT / "omnisvera-model" / "artifacts" / "training" / "lora" / "final",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "omnisvera-model" / "artifacts" / "merged",
    )
    args = parser.parse_args()
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise SystemExit("Instale omnisvera-model/requirements-train.txt") from exc

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
    )
    merged = PeftModel.from_pretrained(model, str(args.adapter.resolve())).merge_and_unload()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(output, safe_serialization=True)
    AutoTokenizer.from_pretrained(args.base_model).save_pretrained(output)
    print(f"Modelo mesclado salvo em {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
