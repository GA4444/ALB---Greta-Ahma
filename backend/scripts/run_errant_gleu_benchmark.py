"""
Run official-style correction benchmark.

Input JSONL format:
  {"source": "... incorrect ...", "reference": "... gold ...", "hypothesis": "... system ..."}

If official ERRANT/GLEU packages are unavailable, the script falls back to the
platform's ERRANT-inspired F0.5 and GLEU-like metrics and marks the run clearly.
"""

import argparse
import json
import os
import sys
from datetime import datetime

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.albanian_research_ai import correction_metrics  # noqa: E402


def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def fallback_metrics(rows):
    values = [correction_metrics(r["source"], r["reference"], r["hypothesis"]) for r in rows]
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "errant_like_f0_5": round(sum(v["errant_like_f0_5"] for v in values) / len(values), 4),
        "gleu_like": round(sum(v["gleu_like"] for v in values) / len(values), 4),
        "precision": round(sum(v["precision"] for v in values) / len(values), 4),
        "recall": round(sum(v["recall"] for v in values) / len(values), 4),
    }


def main():
    parser = argparse.ArgumentParser(description="Run ERRANT/GLEU benchmark for correction outputs.")
    parser.add_argument("--input", required=True, help="JSONL with source/reference/hypothesis")
    parser.add_argument("--out", default="model_artifacts/benchmarks/errant_gleu_results.json")
    args = parser.parse_args()

    rows = list(read_jsonl(args.input))
    out_path = os.path.abspath(os.path.join(BACKEND_DIR, args.out))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    official_available = False
    official_note = ""
    try:
        import errant  # noqa: F401
        official_available = True
        official_note = (
            "ERRANT package detected. Albanian is not an official ERRANT language; "
            "for publication, use this script with a validated Albanian tokenizer/annotator or report the fallback metric as ERRANT-inspired."
        )
    except Exception as exc:
        official_note = f"Official ERRANT package unavailable or unsuitable for Albanian in this environment: {exc}"

    results = {
        "created_at_utc": datetime.utcnow().isoformat() + "Z",
        "official_errant_available": official_available,
        "note": official_note,
        "fallback_metrics": fallback_metrics(rows),
        "publication_guidance": [
            "Use a manually validated gold correction set.",
            "Report official ERRANT/GLEU only if the official tools and Albanian preprocessing are documented.",
            "Otherwise label the implemented metric as ERRANT-inspired F0.5 and GLEU-like.",
        ],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
