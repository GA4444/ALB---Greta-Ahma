#!/usr/bin/env python3
"""
Generate a reproducible synthetic OCR benchmark from real corpus text.

The benchmark is transparent by design:
- text content comes from real `corpus_documents`
- document categories are synthetic visual templates
- resulting images can be evaluated with `evaluate_ocr_pipeline.py`
"""

from __future__ import annotations

import csv
import random
import re
import sqlite3
from pathlib import Path
from typing import Iterable, List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path("/Users/Apple/Desktop/Phd 08:02:2026")
DB_PATH = ROOT / "backend" / "dev.db"
OUT_DIR = ROOT / "backend" / "ocr_eval_synthetic"
CSV_PATH = ROOT / "backend" / "ocr_eval_dataset.csv"

FONT_SANS = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
FONT_SERIF = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"

CATEGORIES = ("administrative", "educational", "literary")
LAYOUTS = ("simple", "complex")
SAMPLES_PER_CELL = 6


def _clean_text(raw: str) -> str:
    parts: List[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if "—" in line:
            line = line.split("—")[-1].strip()
        line = re.sub(r"Fjalë:\s*\[[^\]]*\]", "", line)
        line = re.sub(r"_+", " ", line)
        line = re.sub(r"\s+", " ", line).strip(" -")
        if line:
            parts.append(line)
    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _load_texts(limit: int) -> List[str]:
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT content FROM corpus_documents WHERE LENGTH(content) > 80 ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    texts: List[str] = []
    for (content,) in rows:
        cleaned = _clean_text(content or "")
        if len(cleaned) >= 60:
            texts.append(cleaned)
        if len(texts) >= limit:
            break
    return texts


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if draw.textlength(candidate, font=font) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_paragraph(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: Tuple[int, int],
    width: int,
    font: ImageFont.FreeTypeFont,
    line_spacing: int = 10,
) -> int:
    x, y = xy
    lines = _wrap(draw, text, font, width)
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_height = (bbox[3] - bbox[1]) + line_spacing
    for line in lines:
        draw.text((x, y), line, fill="black", font=font)
        y += line_height
    return y


def _render_sample(text: str, category: str, layout: str, sample_index: int) -> Image.Image:
    random.seed(1000 + sample_index)
    width, height = 1700, 2200
    img = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.truetype(FONT_SANS if category != "literary" else FONT_SERIF, 58)
    body_font = ImageFont.truetype(FONT_SANS if category != "literary" else FONT_SERIF, 38)
    small_font = ImageFont.truetype(FONT_SANS, 28)

    if category == "administrative":
        draw.text((520, 120), "REPUBLIKA E SHQIPERISE", font=title_font, fill="black")
        draw.text((1100, 220), "Date: 12.03.2026", font=small_font, fill="black")
        draw.text((150, 320), "Lenda: Dokument administrativ i gjeneruar per benchmark OCR", font=small_font, fill="black")
        y = _draw_paragraph(draw, text, (180, 470), 1320, body_font, line_spacing=16)
        draw.text((180, y + 120), "Drejtori", font=small_font, fill="black")
        draw.rectangle((1260, 280, 1500, 520), outline="black", width=5)
        draw.text((1295, 370), "VULE", font=body_font, fill="black")
    elif category == "educational":
        draw.text((560, 120), "FLETE PUNE", font=title_font, fill="black")
        draw.text((180, 230), "Klasa: VIII", font=small_font, fill="black")
        draw.text((480, 230), "Lenda: Gjuhe Shqipe", font=small_font, fill="black")
        draw.text((180, 320), "Udhezim: Lexo me kujdes dhe ploteso ushtrimin.", font=small_font, fill="black")
        y = _draw_paragraph(draw, text, (200, 470), 1280, body_font, line_spacing=20)
        draw.line((180, y + 100, 1480, y + 100), fill="black", width=3)
        draw.text((200, y + 130), "Pergjigjja: ____________________________", font=small_font, fill="black")
    else:
        draw.text((520, 140), "KAPITULL I", font=title_font, fill="black")
        draw.text((620, 230), "Tekst letrar", font=small_font, fill="black")
        if layout == "simple":
            _draw_paragraph(draw, text, (180, 420), 1340, body_font, line_spacing=18)
        else:
            left = text[: len(text) // 2]
            right = text[len(text) // 2 :]
            _draw_paragraph(draw, left, (150, 420), 610, body_font, line_spacing=16)
            _draw_paragraph(draw, right, (920, 420), 610, body_font, line_spacing=16)
            draw.line((840, 380, 840, 1900), fill="black", width=2)

    if layout == "complex":
        # Mild rotation, blur, and noise to emulate harder OCR conditions.
        img = img.rotate(random.choice([-1.8, -1.2, 1.1, 1.7]), expand=False, fillcolor=255)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
        overlay = ImageDraw.Draw(img)
        for _ in range(8):
            x1 = random.randint(100, width - 100)
            y1 = random.randint(150, height - 150)
            x2 = x1 + random.randint(-180, 180)
            y2 = y1 + random.randint(-40, 40)
            overlay.line((x1, y1, x2, y2), fill=210, width=2)
        overlay.ellipse((1260, 280, 1500, 520), outline=180, width=6)

    return img


def main() -> None:
    total_needed = len(CATEGORIES) * len(LAYOUTS) * SAMPLES_PER_CELL
    texts = _load_texts(total_needed)
    if len(texts) < total_needed:
        raise RuntimeError(f"Not enough corpus texts. Needed {total_needed}, found {len(texts)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    idx = 0
    for category in CATEGORIES:
        for layout in LAYOUTS:
            for local_idx in range(SAMPLES_PER_CELL):
                text = texts[idx]
                sample_id = f"{category[:3]}_{layout[:3]}_{local_idx + 1:02d}"
                img = _render_sample(text, category, layout, idx)
                img_path = OUT_DIR / f"{sample_id}.png"
                img.save(img_path)
                rows.append(
                    {
                        "id": sample_id,
                        "image_path": str(img_path),
                        "expected_text": text,
                        "category": category,
                        "layout": layout,
                    }
                )
                idx += 1

    with CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["id", "image_path", "expected_text", "category", "layout"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} synthetic OCR samples")
    print(f"Dataset CSV: {CSV_PATH}")


if __name__ == "__main__":
    main()
