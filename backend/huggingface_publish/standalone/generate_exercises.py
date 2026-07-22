#!/usr/bin/env python3
"""Standalone Albanian spelling-exercise generator (outside the web app).

Usage:
  pip install torch transformers peft accelerate sentencepiece
  python generate_exercises.py --adapter ./albanian-spelling-lora --seed-word mirë --type missing_letter
  python generate_exercises.py --adapter USERNAME/albanian-spelling-lora --seed-word shkollë --type find_error
"""

from __future__ import annotations

import argparse
import json


def build_prompt(seed_word: str, grade: int, difficulty: str, exercise_type: str) -> str:
    payload = {
        "seed_word": seed_word,
        "grade": grade,
        "difficulty": difficulty,
        "exercise_type": exercise_type,
        "safety": "Kthe vetëm propozim; përgjigjja finale kontrollohet nga rregullat.",
    }
    return (
        "### Instruksion:\n"
        f"Gjenero një ushtrim të sigurt për drejtshkrimin shqip. Kategoria: {exercise_type}. "
        f"Klasa: {grade}. Vështirësia: {difficulty}. Fjala bazë: {seed_word}.\n\n"
        "### Input:\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\n\n### Përgjigje:\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Albanian spelling exercises with LoRA adapter.")
    parser.add_argument("--adapter", required=True, help="Local adapter folder or Hugging Face repo id")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--seed-word", default="mirë")
    parser.add_argument("--grade", type=int, default=3)
    parser.add_argument("--difficulty", default="easy", choices=["easy", "medium", "hard"])
    parser.add_argument(
        "--type",
        dest="exercise_type",
        default="missing_letter",
        choices=["missing_letter", "find_error", "explain_error"],
    )
    parser.add_argument("--max-new-tokens", type=int, default=120)
    parser.add_argument("--temperature", type=float, default=0.4)
    args = parser.parse_args()

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch

    tokenizer = AutoTokenizer.from_pretrained(args.adapter, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(args.base_model)
    model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()

    prompt = build_prompt(args.seed_word, args.grade, args.difficulty, args.exercise_type)
    inputs = tokenizer(prompt, return_tensors="pt")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    text = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
    print("=== PROMPT ===")
    print(prompt)
    print("=== MODEL OUTPUT ===")
    print(text.strip())
    print()
    print(
        "NOTE: Treat this as a proposal only. For children, keep the correct answer "
        "from deterministic Albanian rules / curated database."
    )


if __name__ == "__main__":
    main()
