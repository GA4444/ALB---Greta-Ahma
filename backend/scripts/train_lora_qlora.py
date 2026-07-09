"""
LoRA/QLoRA training entrypoint for the Albanian educational exercise generator.

Run on a GPU/Colab machine:
  pip install -r backend/requirements-training.txt
  cd backend
  python scripts/export_lora_dataset.py
  python scripts/train_lora_qlora.py --model Qwen/Qwen2.5-0.5B-Instruct

The Render production service should load artifacts only; do not train there.
"""

import argparse
import inspect
import json
import os
import sys
from datetime import datetime

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def require_training_deps():
    try:
        import torch  # noqa: F401
        from datasets import load_dataset  # noqa: F401
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training  # noqa: F401
        from transformers import (  # noqa: F401
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
    except Exception as exc:
        raise SystemExit(
            "Missing training dependencies. Install on GPU/Colab with:\n"
            "  pip install -r backend/requirements-training.txt\n"
            f"Original error: {exc}"
        )


def main():
    parser = argparse.ArgumentParser(description="Train LoRA/QLoRA exercise generator.")
    parser.add_argument("--dataset", default="model_artifacts/lora_qlora/instruction_dataset.jsonl")
    parser.add_argument("--out", default="model_artifacts/lora_qlora/adapter")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--epochs", type=float, default=3)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--qlora", action="store_true")
    args = parser.parse_args()

    require_training_deps()
    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )

    dataset_path = os.path.abspath(os.path.join(BACKEND_DIR, args.dataset))
    out_dir = os.path.abspath(os.path.join(BACKEND_DIR, args.out))
    if not os.path.exists(dataset_path):
        raise SystemExit(f"Dataset missing: {dataset_path}. Run export_lora_dataset.py first.")
    os.makedirs(out_dir, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quant_config = None
    if args.qlora:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=quant_config,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    if args.qlora:
        model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    )
    model = get_peft_model(model, lora_config)

    ds = load_dataset("json", data_files=dataset_path, split="train")
    split = ds.train_test_split(test_size=0.1, seed=42) if len(ds) > 10 else {"train": ds, "test": ds}

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=args.max_length, padding=False)

    train_ds = split["train"].map(tokenize, batched=True, remove_columns=split["train"].column_names)
    eval_ds = split["test"].map(tokenize, batched=True, remove_columns=split["test"].column_names)

    training_kwargs = {
        "output_dir": out_dir,
        "num_train_epochs": args.epochs,
        "per_device_train_batch_size": args.batch_size,
        "per_device_eval_batch_size": args.batch_size,
        "gradient_accumulation_steps": args.grad_accum,
        "learning_rate": args.lr,
        "logging_steps": 10,
        "save_strategy": "epoch",
        "fp16": torch.cuda.is_available(),
        "report_to": [],
    }
    strategy_arg = "evaluation_strategy"
    if "eval_strategy" in inspect.signature(TrainingArguments.__init__).parameters:
        strategy_arg = "eval_strategy"
    training_kwargs[strategy_arg] = "epoch"
    training_args = TrainingArguments(**training_kwargs)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)

    manifest = {
        "trained_at_utc": datetime.utcnow().isoformat() + "Z",
        "base_model": args.model,
        "method": "QLoRA" if args.qlora else "LoRA",
        "dataset": dataset_path,
        "artifact_dir": out_dir,
        "records": len(ds),
    }
    with open(os.path.join(out_dir, "training_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
