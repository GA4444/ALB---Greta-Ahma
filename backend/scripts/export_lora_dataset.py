import argparse
import json
import os
import sys
from datetime import datetime

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database import SessionLocal  # noqa: E402
from app.models import Exercise  # noqa: E402
from app.services.albanian_research_ai import instruction_pair_from_exercise  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Export instruction-tuning JSONL for LoRA/QLoRA.")
    parser.add_argument("--out", default="model_artifacts/lora_qlora/instruction_dataset.jsonl")
    parser.add_argument("--limit", type=int, default=0, help="0 = all enabled exercises")
    args = parser.parse_args()

    out_path = os.path.abspath(os.path.join(BACKEND_DIR, args.out))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    db = SessionLocal()
    try:
        query = db.query(Exercise).filter(Exercise.enabled == True).order_by(Exercise.id.asc())
        if args.limit > 0:
            query = query.limit(args.limit)
        exercises = query.all()

        count = 0
        with open(out_path, "w", encoding="utf-8") as f:
            for exercise in exercises:
                pair = instruction_pair_from_exercise(exercise)
                record = {
                    "instruction": pair["instruction"],
                    "input": pair["input"],
                    "output": pair["output"],
                    "text": (
                        "### Instruksion:\n"
                        + pair["instruction"]
                        + "\n\n### Input:\n"
                        + json.dumps(pair["input"], ensure_ascii=False)
                        + "\n\n### Përgjigje:\n"
                        + json.dumps(pair["output"], ensure_ascii=False)
                    ),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1

        manifest = {
            "created_at_utc": datetime.utcnow().isoformat() + "Z",
            "records": count,
            "format": "instruction_tuning_jsonl",
            "output": out_path,
            "next_step": "Run train_lora_qlora.py on a GPU/Colab machine.",
        }
        with open(os.path.join(os.path.dirname(out_path), "dataset_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
