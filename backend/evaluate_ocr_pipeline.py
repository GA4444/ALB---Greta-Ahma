#!/usr/bin/env python3
"""
Evaluate the Albanian OCR pipeline with real project code and ground-truth text.

Input CSV columns:
- image_path
- expected_text
- category   (e.g. administrative, educational, literary)
- layout     (e.g. simple, complex)

Optional columns:
- id

Example:
python3 evaluate_ocr_pipeline.py \
  --dataset ocr_eval_dataset.csv \
  --output-json ocr_eval_results.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image

from app.database import SessionLocal
from app.routers import ocr as ocr_router


CONFIGS: Sequence[Tuple[str, str]] = (
    ("A", "Tesseract only"),
    ("B", "PaddleOCR only"),
    ("C", "Dual-engine fusion"),
    ("D", "Fusion + heuristics"),
    ("E", "Full pipeline"),
)


@dataclass
class Sample:
    sample_id: str
    image_path: str
    expected_text: str
    category: str
    layout: str


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or "").strip())


def _tokenize_words(text: str) -> List[str]:
    return ocr_router._tokenize_sq(_norm_text(text))


def _word_score(text: str) -> int:
    alpha = sum(ch.isalpha() for ch in text)
    return alpha + len(text)


def _load_samples(path: Path) -> List[Sample]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"image_path", "expected_text", "category", "layout"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Dataset CSV is missing columns: {', '.join(sorted(missing))}")

        samples: List[Sample] = []
        for index, row in enumerate(reader, start=1):
            sample_id = (row.get("id") or f"sample_{index}").strip()
            image_path = (row.get("image_path") or "").strip()
            expected_text = row.get("expected_text") or ""
            category = (row.get("category") or "").strip().lower()
            layout = (row.get("layout") or "").strip().lower()
            if not image_path or not expected_text or not category or not layout:
                raise ValueError(f"Row {index} has empty required fields")
            samples.append(
                Sample(
                    sample_id=sample_id,
                    image_path=image_path,
                    expected_text=expected_text,
                    category=category,
                    layout=layout,
                )
            )
    return samples


def _levenshtein_ops(a: Sequence[str], b: Sequence[str]) -> Tuple[int, int, int, int]:
    """
    Returns (distance, substitutions, deletions, insertions).
    """
    n = len(a)
    m = len(b)
    dp: List[List[Tuple[int, int, int, int]]] = [
        [(0, 0, 0, 0) for _ in range(m + 1)] for _ in range(n + 1)
    ]

    for i in range(1, n + 1):
        dist, s, d, ins = dp[i - 1][0]
        dp[i][0] = (dist + 1, s, d + 1, ins)
    for j in range(1, m + 1):
        dist, s, d, ins = dp[0][j - 1]
        dp[0][j] = (dist + 1, s, d, ins + 1)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                candidates = [dp[i - 1][j - 1]]
            else:
                dist, s, d, ins = dp[i - 1][j - 1]
                sub = (dist + 1, s + 1, d, ins)
                dist, s, d, ins = dp[i - 1][j]
                delete = (dist + 1, s, d + 1, ins)
                dist, s, d, ins = dp[i][j - 1]
                insert = (dist + 1, s, d, ins + 1)
                candidates = [sub, delete, insert]
            dp[i][j] = min(candidates, key=lambda item: (item[0], item[1], item[2], item[3]))
    return dp[n][m]


def _cer(expected: str, predicted: str) -> Tuple[float, Dict[str, int]]:
    exp_chars = list(_norm_text(expected))
    pred_chars = list(_norm_text(predicted))
    distance, subs, dels, ins = _levenshtein_ops(exp_chars, pred_chars)
    denom = max(1, len(exp_chars))
    return distance / denom, {"substitutions": subs, "deletions": dels, "insertions": ins, "n": len(exp_chars)}


def _wer(expected: str, predicted: str) -> Tuple[float, Dict[str, int]]:
    exp_words = _tokenize_words(expected)
    pred_words = _tokenize_words(predicted)
    distance, subs, dels, ins = _levenshtein_ops(exp_words, pred_words)
    denom = max(1, len(exp_words))
    return distance / denom, {"substitutions": subs, "deletions": dels, "insertions": ins, "n": len(exp_words)}


def _der(expected: str, predicted: str) -> Tuple[float, Dict[str, int]]:
    """
    Diacritical Error Rate for Albanian diacritics ë and ç.
    Counts expected diacritics that are not preserved in alignment.
    """
    exp_chars = list(_norm_text(expected))
    pred_chars = list(_norm_text(predicted))
    target = {"ë", "ç", "Ë", "Ç"}

    n = len(exp_chars)
    m = len(pred_chars)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    back: List[List[Tuple[int, int]]] = [[(0, 0)] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        dp[i][0] = i
        back[i][0] = (i - 1, 0)
    for j in range(1, m + 1):
        dp[0][j] = j
        back[0][j] = (0, j - 1)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if exp_chars[i - 1] == pred_chars[j - 1] else 1
            options = [
                (dp[i - 1][j - 1] + cost, (i - 1, j - 1)),
                (dp[i - 1][j] + 1, (i - 1, j)),
                (dp[i][j - 1] + 1, (i, j - 1)),
            ]
            best_cost, parent = min(options, key=lambda item: item[0])
            dp[i][j] = best_cost
            back[i][j] = parent

    total_diacritics = sum(1 for ch in exp_chars if ch in target)
    errors = 0
    i, j = n, m
    while i > 0 or j > 0:
        pi, pj = back[i][j]
        if pi == i - 1 and pj == j - 1:
            if exp_chars[i - 1] in target and exp_chars[i - 1] != pred_chars[j - 1]:
                errors += 1
        elif pi == i - 1 and pj == j:
            if exp_chars[i - 1] in target:
                errors += 1
        i, j = pi, pj

    denom = max(1, total_diacritics)
    return errors / denom, {"errors": errors, "n": total_diacritics}


def _run_tesseract_only(ocr_ready: Image.Image) -> str:
    if not ocr_router.pytesseract:
        return ""

    candidates: List[str] = []

    def try_cfg(cfg: str, use_lang: bool = True) -> None:
        try:
            text = ocr_router.pytesseract.image_to_string(
                ocr_ready,
                lang="sqi" if use_lang else None,
                config=cfg,
            ).strip()
            if text:
                candidates.append(text)
        except Exception:
            return

    common_cfg = '-c preserve_interword_spaces=1 -c tessedit_char_whitelist="A-Za-zËÇëç?.,\' -"'
    try_cfg(f"--oem 1 --psm 6 {common_cfg}", True)
    try_cfg(f"--oem 1 --psm 4 {common_cfg}", True)
    try_cfg(f"--oem 1 --psm 7 {common_cfg}", True)
    try_cfg(f"--oem 1 --psm 11 {common_cfg}", True)
    try_cfg(f"--oem 1 --psm 13 {common_cfg}", True)
    try_cfg(f"--oem 1 --psm 6 {common_cfg}", False)
    try_cfg(f"--oem 1 --psm 4 {common_cfg}", False)

    if not candidates:
        return ""
    return max(candidates, key=_word_score)


def _run_paddle_only(deskewed: Image.Image) -> str:
    return (ocr_router._run_paddle_fallback(deskewed) or "").strip()


def _run_fusion(tesseract_text: str, paddle_text: str) -> Tuple[str, str]:
    options = []
    if tesseract_text:
        options.append((tesseract_text, "tesseract"))
    if paddle_text:
        options.append((paddle_text, "paddleocr"))
    if not options:
        return "", "none"
    text, engine = max(options, key=lambda item: _word_score(item[0]))
    return text, engine


def _auto_apply_heuristics(
    text: str,
    lexicon: set,
    buckets: Dict[Tuple[str, int], List[str]],
    use_distance_suggestions: bool,
) -> str:
    tokens = _tokenize_words(text)
    if not tokens:
        return _norm_text(text)

    corrected: List[str] = []
    for token in tokens:
        lower = token.lower()
        if lower in lexicon or len(lower) < 2:
            corrected.append(token)
            continue

        suggestions = ocr_router._rule_based_candidates(lower, lexicon)
        if not suggestions and use_distance_suggestions:
            suggestions = ocr_router._suggest_from_lexicon(lower, buckets, max_suggestions=1)
        if suggestions:
            replacement = suggestions[0]
            if token[:1].isupper():
                replacement = replacement.capitalize()
            corrected.append(replacement)
        else:
            corrected.append(token)
    return " ".join(corrected)


def _run_full_pipeline(
    text: str,
    use_llm: bool,
    lexicon: set,
    buckets: Dict[Tuple[str, int], List[str]],
) -> Dict[str, str]:
    heuristic_text = _auto_apply_heuristics(
        text, lexicon, buckets, use_distance_suggestions=False
    )
    lexical_text = _auto_apply_heuristics(
        heuristic_text, lexicon, buckets, use_distance_suggestions=True
    )
    llm_result = ocr_router._llm_refine_ocr_text(lexical_text, use_llm=use_llm)
    full_text = lexical_text
    if llm_result.get("model_used") not in {"none", "fallback"}:
        full_text = llm_result["refined_text"]
    return {
        "D": _norm_text(heuristic_text),
        "E": _norm_text(full_text),
    }


def _summarize_metric(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0


def _format_percent(value: float) -> float:
    return round(value * 100.0, 2)


def _build_markdown_tables(results: Dict[str, Any]) -> str:
    overall = results["overall"]
    by_group = results["by_category_layout"]

    lines: List[str] = []
    lines.append("## Table I. Overall CER and WER by configuration across all document categories")
    lines.append("")
    lines.append("| Configuration | CER (%) | WER (%) | DER (%) |")
    lines.append("|---|---:|---:|---:|")
    for key, label in CONFIGS:
        row = overall[key]
        lines.append(
            f"| {key} - {label} | {row['cer_percent']:.2f} | {row['wer_percent']:.2f} | {row['der_percent']:.2f} |"
        )

    lines.append("")
    lines.append("## Table II. CER (%) by document category and layout complexity")
    lines.append("")
    lines.append("| Category | Layout | Config A | Config B | Config C | Config D | Config E |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")

    for category in sorted(by_group):
        for layout in sorted(by_group[category]):
            row = by_group[category][layout]
            lines.append(
                "| "
                + f"{category.capitalize()} | {layout.capitalize()} | "
                + " | ".join(f"{row[key]['cer_percent']:.2f}" for key, _ in CONFIGS)
                + " |"
            )

    lines.append("")
    lines.append("## Table III. Proposed row for comparison table")
    lines.append("")
    lines.append("| System | Language | CER (%) | WER (%) | Method |")
    lines.append("|---|---|---:|---:|---|")
    lines.append(
        f"| Proposed (Config E) | Albanian | {overall['E']['cer_percent']:.2f} | {overall['E']['wer_percent']:.2f} | Hybrid + Albanian-specific PP |"
    )
    return "\n".join(lines)


def evaluate(samples: List[Sample], use_llm: bool) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        lexicon, buckets = ocr_router._build_lexicon(db)
    finally:
        db.close()

    per_sample: List[Dict[str, Any]] = []
    aggregates: Dict[str, List[Dict[str, float]]] = {key: [] for key, _ in CONFIGS}
    grouped: Dict[str, Dict[str, Dict[str, List[Dict[str, float]]]]] = defaultdict(
        lambda: defaultdict(lambda: {key: [] for key, _ in CONFIGS})
    )

    paddle_available = ocr_router._get_paddle_ocr() is not None
    llm_available = bool(use_llm and getattr(ocr_router, "LLM_AVAILABLE", False))

    for sample in samples:
        image = Image.open(sample.image_path)
        deskewed = ocr_router._deskew_image(image)
        ocr_ready = ocr_router._preprocess_for_ocr(deskewed)

        config_texts: Dict[str, str] = {}
        config_texts["A"] = _norm_text(_run_tesseract_only(ocr_ready))
        config_texts["B"] = _norm_text(_run_paddle_only(deskewed))
        fusion_text, fusion_engine = _run_fusion(config_texts["A"], config_texts["B"])
        config_texts["C"] = _norm_text(fusion_text)
        downstream = _run_full_pipeline(config_texts["C"], use_llm=use_llm, lexicon=lexicon, buckets=buckets)
        config_texts.update(downstream)

        sample_metrics: Dict[str, Dict[str, float]] = {}
        for key, _label in CONFIGS:
            cer_value, cer_ops = _cer(sample.expected_text, config_texts[key])
            wer_value, wer_ops = _wer(sample.expected_text, config_texts[key])
            der_value, der_ops = _der(sample.expected_text, config_texts[key])
            metric_row = {
                "cer": cer_value,
                "wer": wer_value,
                "der": der_value,
                "cer_percent": _format_percent(cer_value),
                "wer_percent": _format_percent(wer_value),
                "der_percent": _format_percent(der_value),
                "cer_n": cer_ops["n"],
                "wer_n": wer_ops["n"],
                "der_n": der_ops["n"],
            }
            sample_metrics[key] = metric_row
            aggregates[key].append(metric_row)
            grouped[sample.category][sample.layout][key].append(metric_row)

        per_sample.append(
            {
                "id": sample.sample_id,
                "image_path": sample.image_path,
                "category": sample.category,
                "layout": sample.layout,
                "fusion_engine": fusion_engine,
                "texts": config_texts,
                "metrics": sample_metrics,
            }
        )

    overall = {
        key: {
            "cer_percent": round(_summarize_metric(item["cer"] for item in rows) * 100.0, 2),
            "wer_percent": round(_summarize_metric(item["wer"] for item in rows) * 100.0, 2),
            "der_percent": round(_summarize_metric(item["der"] for item in rows) * 100.0, 2),
            "samples": len(rows),
        }
        for key, rows in aggregates.items()
    }

    by_category_layout: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for category, layouts in grouped.items():
        by_category_layout[category] = {}
        for layout, config_rows in layouts.items():
            by_category_layout[category][layout] = {
                key: {
                    "cer_percent": round(_summarize_metric(item["cer"] for item in rows) * 100.0, 2),
                    "wer_percent": round(_summarize_metric(item["wer"] for item in rows) * 100.0, 2),
                    "der_percent": round(_summarize_metric(item["der"] for item in rows) * 100.0, 2),
                    "samples": len(rows),
                }
                for key, rows in config_rows.items()
            }

    results = {
        "dataset_size": len(samples),
        "paddle_available": paddle_available,
        "llm_requested": use_llm,
        "llm_available": llm_available,
        "overall": overall,
        "by_category_layout": by_category_layout,
        "per_sample": per_sample,
    }
    results["markdown_tables"] = _build_markdown_tables(results)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the Albanian OCR pipeline on a labeled dataset.")
    parser.add_argument("--dataset", required=True, help="Path to evaluation CSV dataset.")
    parser.add_argument("--output-json", help="Path to save full JSON results.")
    parser.add_argument("--output-md", help="Path to save paper-ready markdown tables.")
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Enable LLM refinement for Config E. Requires OPENAI_API_KEY.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset).expanduser().resolve()
    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}", file=sys.stderr)
        return 1

    samples = _load_samples(dataset_path)
    results = evaluate(samples, use_llm=args.use_llm)

    print(results["markdown_tables"])
    print("")
    print(
        json.dumps(
            {
                "dataset_size": results["dataset_size"],
                "paddle_available": results["paddle_available"],
                "llm_requested": results["llm_requested"],
                "llm_available": results["llm_available"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if args.output_json:
        output_json_path = Path(args.output_json).expanduser().resolve()
        output_json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.output_md:
        output_md_path = Path(args.output_md).expanduser().resolve()
        output_md_path.write_text(results["markdown_tables"] + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
