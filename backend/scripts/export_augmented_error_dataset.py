#!/usr/bin/env python3
"""Export controlled Albanian error-augmentation pairs for Hugging Face.

Creates (incorrect -> correct) pairs with labeled error types:
  missing_diacritic, c_q_confusion, digraph_reduction, case_ending_error,
  letter_transposition, missing_letter, extra_letter, drop_final_vowel.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import Counter
from datetime import datetime

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.albanian_research_ai import (  # noqa: E402
    ALBANIAN_DIGRAPHS,
    corrupt_word,
    normalize_sq,
)


SEED_WORDS = [
    "mirë", "fëmijë", "shkollë", "libër", "mësues", "nxënës", "gjuha", "shqipe",
    "çanta", "çaj", "qeni", "qielli", "dhoma", "thjeshtë", "gjumi", "njeri",
    "llampa", "rruga", "zhvillim", "xhaxha", "mbrëmje", "vjeshtë", "pranverë",
    "verë", "dimër", "familje", "shtëpi", "dritare", "tavolinë", "karrige",
    "laps", "fletore", "detyrë", "ushtrim", "gabim", "rregull", "drejtshkrim",
    "shkronjë", "fjali", "fjalë", "kuptim", "tingull", "digraf", "mbaresë",
    "emër", "mbiemër", "folje", "ndajfolje", "përemër", "lidhëz", "parafjalë",
    "numër", "gjinia", "rasa", "emërore", "gjinore", "dhanore", "kallëzore",
    "rrjedhore", "vendore", "shumës", "njëjës", "shkruaj", "lexoj", "dëgjoj",
    "flas", "mësoj", "kuptoj", "përdor", "korrigjoj", "plotësoj", "krahasoj",
]


ERROR_TYPES = [
    "missing_diacritic",
    "c_q_confusion",
    "digraph_reduction",
    "case_ending_error",
    "letter_transposition",
    "missing_letter",
    "extra_letter",
    "drop_final_vowel",
]


def words_from_instruction_dataset(path: str) -> list[str]:
    words: list[str] = []
    if not os.path.exists(path):
        return words
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            answer = normalize_sq(str((row.get("output") or {}).get("answer") or ""))
            if answer and re.fullmatch(r"[a-zëç]+", answer) and 2 <= len(answer) <= 24:
                words.append(answer)
            prompt = str((row.get("output") or {}).get("prompt") or "")
            for token in re.findall(r"[A-Za-zËÇëç]+", prompt):
                token_n = normalize_sq(token)
                if 3 <= len(token_n) <= 20 and re.fullmatch(r"[a-zëç]+", token_n):
                    words.append(token_n)
    return words


def generate_pairs(words: list[str], per_word: int, seed: int) -> list[dict]:
    random.seed(seed)
    unique_words = sorted(set(words))
    rows: list[dict] = []
    seen = set()
    for word in unique_words:
        produced = 0
        attempts = 0
        while produced < per_word and attempts < per_word * 12:
            attempts += 1
            preferred = ERROR_TYPES[attempts % len(ERROR_TYPES)]
            corrupted, e_type = corrupt_word(word, preferred)
            if e_type == "none" or corrupted == word:
                corrupted, e_type = corrupt_word(word)
            if e_type == "none" or corrupted == word:
                continue
            key = (corrupted, word, e_type)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "incorrect": corrupted,
                    "correct": word,
                    "error_type": e_type,
                    "language": "sq",
                    "task": "albanian_spelling_correction",
                    "instruction": (
                        "Korrigjo fjalën e gabuar në shqip. "
                        "Kthe vetëm formën e saktë."
                    ),
                    "input": corrupted,
                    "output": word,
                    "text": (
                        f"### Instruksion:\nKorrigjo fjalën e gabuar në shqip.\n\n"
                        f"### Input:\n{corrupted}\n\n"
                        f"### Përgjigje:\n{word}"
                    ),
                }
            )
            produced += 1
    return rows


def main():
    parser = argparse.ArgumentParser(description="Export Albanian controlled-error augmentation dataset.")
    parser.add_argument(
        "--instruction-dataset",
        default="model_artifacts/lora_qlora/instruction_dataset.jsonl",
    )
    parser.add_argument(
        "--out-dir",
        default="huggingface_publish/dataset_albanian_error_augmentation",
    )
    parser.add_argument("--per-word", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    instruction_path = os.path.abspath(os.path.join(BACKEND_DIR, args.instruction_dataset))
    out_dir = os.path.abspath(os.path.join(BACKEND_DIR, args.out_dir))
    os.makedirs(out_dir, exist_ok=True)

    words = SEED_WORDS + words_from_instruction_dataset(instruction_path)
    pairs = generate_pairs(words, per_word=args.per_word, seed=args.seed)
    random.Random(args.seed).shuffle(pairs)

    jsonl_path = os.path.join(out_dir, "train.jsonl")
    csv_path = os.path.join(out_dir, "train.csv")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for row in pairs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("incorrect,correct,error_type,language,task\n")
        for row in pairs:
            f.write(
                f"\"{row['incorrect']}\",\"{row['correct']}\",\"{row['error_type']}\","
                f"\"{row['language']}\",\"{row['task']}\"\n"
            )

    counts = Counter(row["error_type"] for row in pairs)
    digraph_coverage = sorted({d for d in ALBANIAN_DIGRAPHS if any(d in w for w in words)})
    manifest = {
        "created_at_utc": datetime.utcnow().isoformat() + "Z",
        "records": len(pairs),
        "unique_source_words": len(set(words)),
        "error_type_counts": dict(counts),
        "covered_digraphs": digraph_coverage,
        "format": "jsonl_and_csv",
        "files": {
            "jsonl": jsonl_path,
            "csv": csv_path,
        },
        "description": (
            "Controlled Albanian orthographic error augmentation pairs "
            "(incorrect -> correct) for spelling correction and GEC research."
        ),
    }
    with open(os.path.join(out_dir, "dataset_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
