"""
Intelligent OCR Post-Processing Pipeline for Albanian Language

Pipeline Architecture:
1. Image Preprocessing (deskew, contrast, denoise, sharpen, threshold)
2. Multi-Engine OCR Extraction (Tesseract sqi + PaddleOCR fallback)
3. LLM-Based Post-Processing (GPT-4 for language refinement) [NEW]
4. Rule-Based Orthography Analysis (Albanian-specific heuristics)

The LLM post-processor:
- Detects and corrects OCR artifacts (Il→Il, rn→m, etc.)
- Restores missing Albanian diacritics (ë, ç)
- Improves syntactic and semantic consistency
- Provides confidence scoring

This architecture is suitable for academic research and production use.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple
from io import BytesIO
import re
import unicodedata
import time
import os
import json

try:
	from PIL import Image
	import pytesseract
except ImportError:
	Image = None
	pytesseract = None

# Optional PaddleOCR fallback (për shkrim dore). Kërkon instalim manual të paddleocr.
_PADDLE_OCR = None
np = None  # type: ignore

def _get_paddle_ocr():
	"""Lazy-initialize PaddleOCR on first use to avoid segfaults at import time."""
	global _PADDLE_OCR, np
	if _PADDLE_OCR is not None:
		return _PADDLE_OCR
	try:
		from paddleocr import PaddleOCR  # type: ignore
		import numpy as _np  # type: ignore
		np = _np
		_PADDLE_OCR = PaddleOCR(
			use_angle_cls=True,
			lang="latin",
			show_log=False,
		)
	except Exception:
		_PADDLE_OCR = None
	return _PADDLE_OCR

# LLM Integration for post-OCR refinement
try:
	import openai
	OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
	if OPENAI_API_KEY:
		openai.api_key = OPENAI_API_KEY
		LLM_AVAILABLE = True
	else:
		LLM_AVAILABLE = False
except ImportError:
	LLM_AVAILABLE = False

router = APIRouter()


# ============================================================================
# LLM POST-PROCESSING MODULE
# ============================================================================

def _llm_refine_ocr_text(raw_text: str, use_llm: bool = True) -> Dict[str, Any]:
	"""
	Use GPT-4 as a post-OCR language refinement module.
	
	Tasks:
	- Detect and correct OCR artifacts
	- Restore missing Albanian diacritics (ë, ç)
	- Improve syntactic and semantic consistency
	- Provide confidence score
	
	Returns:
		{
			"refined_text": str,
			"corrections": List[Dict],
			"confidence": float,
			"model_used": str,
			"processing_time_ms": int
		}
	"""
	if not use_llm or not LLM_AVAILABLE or not raw_text.strip():
		return {
			"refined_text": raw_text,
			"corrections": [],
			"confidence": 0.0,
			"model_used": "none",
			"processing_time_ms": 0
		}
	
	start_time = time.time()
	
	system_prompt = """Ti je një ekspert i gjuhës shqipe dhe OCR post-processing.

Detyra jote është të analizosh tekstin e nxjerrë nga OCR dhe:

1. KORRIGJO gabimet tipike të OCR-së:
   - "rn" → "m", "Il" → "Il", "l" → "i", "0" → "o", etj.
   - Shkronja të dyfishta të panevojshme
   - Karaktere të çuditshme ose simbole të gabuara

2. RESTAURO diacritics shqipe që mungojnë:
   - "e" → "ë" ku duhet (p.sh. "shtepi" → "shtëpi", "eshte" → "është")
   - "c" → "ç" ku duhet (p.sh. "caj" → "çaj", "rrufe" → "rrufe")

3. KORRIGJO gabime gramatikore dhe sintaksore të dukshme

4. RUAJ kuptimin origjinal - mos ndryshoni fjalë që janë të sakta

Përgjigju në formatin JSON:
{
  "refined_text": "Teksti i korrigjuar",
  "corrections": [
    {"original": "fjala origjinale", "corrected": "fjala e korrigjuar", "reason": "arsyeja"}
  ],
  "confidence": 0.85
}

Confidence duhet të jetë 0.0-1.0 bazuar në sa i sigurt je për korrigjimet."""

	user_prompt = f"""Analizo dhe korrigjo këtë tekst të nxjerrë nga OCR:

---
{raw_text}
---

Kthe rezultatin në formatin JSON të specifikuar."""

	try:
		response = openai.ChatCompletion.create(
			model="gpt-4-turbo-preview",
			messages=[
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt}
			],
			temperature=0.3,  # Low temperature for more consistent corrections
			max_tokens=1500
		)
		
		content = response.choices[0].message.content.strip()
		
		# Extract JSON from response
		json_match = re.search(r'\{[\s\S]*\}', content)
		if json_match:
			result = json.loads(json_match.group())
			processing_time = int((time.time() - start_time) * 1000)
			
			return {
				"refined_text": result.get("refined_text", raw_text),
				"corrections": result.get("corrections", []),
				"confidence": float(result.get("confidence", 0.5)),
				"model_used": "gpt-4-turbo",
				"processing_time_ms": processing_time
			}
	except Exception as e:
		print(f"[OCR LLM] Error: {e}")
	
	# Fallback if LLM fails
	return {
		"refined_text": raw_text,
		"corrections": [],
		"confidence": 0.0,
		"model_used": "fallback",
		"processing_time_ms": int((time.time() - start_time) * 1000)
	}

# In-process cache for lexicon (keeps OCR fast). Safe for a single-process dev server.
_LEXICON_CACHE: Optional[set] = None
_BUCKETS_CACHE: Optional[Dict[Tuple[str, int], List[str]]] = None
_LEXICON_CACHE_AT: float = 0.0
_LEXICON_TTL_SECONDS: float = 300.0


class OCRAnalysisOut(BaseModel):
	extracted_text: str
	refined_text: Optional[str] = None  # LLM-refined version
	errors: List[Dict[str, Any]]
	suggestions: List[str]
	issues: List[Dict[str, Any]] = []
	llm_corrections: List[Dict[str, Any]] = []  # Corrections made by LLM
	meta: Dict[str, Any] = {}


def _norm_text(s: str) -> str:
	return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s or "").strip())


def _tokenize_sq(text: str) -> List[str]:
	# Albanian letters are covered by Unicode alpha + explicit ë/ç cases
	return re.findall(r"[A-Za-zËÇëç]+", text, flags=re.UNICODE)


def _preprocess_for_ocr(img: "Image.Image") -> "Image.Image":
	"""
	Upscale + denoise + sharpen + adaptive threshold për të rritur besueshmërinë e OCR.
	"""
	gray = img.convert("L")
	try:
		from PIL import ImageOps, ImageFilter, ImageEnhance

		# 1) Upscale (1.5x) për të rritur lexueshmërinë e shkronjave
		w, h = gray.size
		scale = 1.5
		gray = gray.resize((int(w * scale), int(h * scale)))

		# 2) Rritje kontrasti + autocontrast
		gray = ImageEnhance.Contrast(gray).enhance(2.0)
		gray = ImageOps.autocontrast(gray)

		# 3) Denoise i lehtë + Sharpen
		gray = gray.filter(ImageFilter.MedianFilter(size=3))
		gray = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

		# 4) Adaptive-like threshold (pak më i ulët se më parë)
		bw = gray.point(lambda x: 255 if x > 135 else 0, mode="1")
		return bw.convert("L")
	except Exception:
		# Fallback minimal në rast mungese bibliotekash
		bw = gray.point(lambda x: 255 if x > 140 else 0, mode="1")
		return bw.convert("L")


def _deskew_image(img: "Image.Image") -> "Image.Image":
	"""
	Përdor Tesseract OSD për të zbuluar këndin dhe e rrotullon imazhin nëse është e nevojshme.
	"""
	if not pytesseract or not hasattr(pytesseract, "image_to_osd"):
		return img
	try:
		osd = pytesseract.image_to_osd(img)
		angle_match = re.search(r"Rotate: (\d+)", osd)
		if angle_match:
			angle = int(angle_match.group(1)) % 360
			# rrotullim minimal, 0/90/180/270
			if angle in (90, 180, 270):
				return img.rotate(-angle, expand=True, fillcolor=255)
	except Exception:
		pass
	return img


def _run_paddle_fallback(img: "Image.Image") -> str:
	"""
	Fallback OCR me PaddleOCR (opsionale, nëse është instaluar). E përshtatshme për shkrim dore.
	"""
	paddle = _get_paddle_ocr()
	if not paddle or np is None:
		return ""
	try:
		np_img = np.array(img.convert("RGB"))
		res = paddle.ocr(np_img, cls=True)
		lines = []
		for line in res:
			if line and len(line) > 0:
				text = line[1][0]
				if text:
					lines.append(text)
		return "\n".join(lines).strip()
	except Exception:
		return ""


def _levenshtein(a: str, b: str, max_dist: int = 2) -> int:
	# Bounded Levenshtein to keep it fast
	if a == b:
		return 0
	if abs(len(a) - len(b)) > max_dist:
		return max_dist + 1
	previous = list(range(len(b) + 1))
	for i, ca in enumerate(a, start=1):
		current = [i]
		min_row = current[0]
		for j, cb in enumerate(b, start=1):
			ins = current[j - 1] + 1
			delete = previous[j] + 1
			sub = previous[j - 1] + (0 if ca == cb else 1)
			val = min(ins, delete, sub)
			current.append(val)
			if val < min_row:
				min_row = val
		previous = current
		if min_row > max_dist:
			return max_dist + 1
	return previous[-1]


def _build_lexicon(db: Session) -> Tuple[set, Dict[Tuple[str, int], List[str]]]:
	# Use existing corpus (exercise prompts + answers) as an in-project "dictionary"
	global _LEXICON_CACHE, _BUCKETS_CACHE, _LEXICON_CACHE_AT
	now = time.time()
	if _LEXICON_CACHE is not None and _BUCKETS_CACHE is not None and (now - _LEXICON_CACHE_AT) < _LEXICON_TTL_SECONDS:
		return _LEXICON_CACHE, _BUCKETS_CACHE

	lex = set()
	buckets: Dict[Tuple[str, int], List[str]] = {}

	rows = db.query(models.Exercise.prompt, models.Exercise.answer).filter(models.Exercise.enabled == True).all()
	for prompt, answer in rows:
		for src in [prompt or "", answer or ""]:
			for tok in _tokenize_sq(_norm_text(src).lower()):
				w = tok.lower()
				if len(w) < 2:
					continue
				lex.add(w)

	for w in lex:
		key = (w[0], len(w))
		buckets.setdefault(key, []).append(w)

	_LEXICON_CACHE = lex
	_BUCKETS_CACHE = buckets
	_LEXICON_CACHE_AT = now
	return lex, buckets


def _issue_meta(issue_type: str, conf: Optional[float], has_suggestions: bool) -> Dict[str, Any]:
	"""
	Attach professional metadata:
	- source: 'ocr' or 'orthography'
	- severity: info/warning/error
	- likelihood: probability-like score that it's truly a spelling issue
	"""
	if issue_type == "low_confidence":
		return {"source": "ocr", "severity": "warning", "likelihood": 0.2}
	if issue_type == "mismatch_expected":
		return {"source": "orthography", "severity": "error", "likelihood": 0.95}
	if issue_type in ("diacritics_suspected", "double_consonant_suspected"):
		return {"source": "orthography", "severity": "warning", "likelihood": 0.8}
	if issue_type in ("ending_ë_suspected", "ç_suspected"):
		return {"source": "orthography", "severity": "warning", "likelihood": 0.85}
	if issue_type in (
		"missing_letter",
		"extra_letter",
		"letter_substitution",
		"letter_transposition",
		"digraph_suspected",
		"vowel_confusion",
		"capitalization",
	):
		return {"source": "orthography", "severity": "warning", "likelihood": 0.82 if has_suggestions else 0.7}
	if issue_type in ("missing_word", "extra_word"):
		return {"source": "orthography", "severity": "error", "likelihood": 0.9}
	if issue_type == "unknown_word":
		return {"source": "orthography", "severity": "warning" if has_suggestions else "info", "likelihood": 0.6 if has_suggestions else 0.35}
	return {"source": "orthography", "severity": "info", "likelihood": 0.5}


def _rule_based_candidates(token: str, lexicon: set) -> List[str]:
	"""
	Albanian-aware, conservative candidates based on frequent orthography/OCR patterns.
	Returns candidates that exist in lexicon.
	"""
	w = token.lower().strip()
	if not w:
		return []

	cands = []

	# 1) ë at the end is often missed (e.g., "shtepi" -> "shtëpi" not possible without dictionary,
	# but "e" -> "ë" at ending can still help in many cases)
	if w.endswith("e"):
		cands.append(w[:-1] + "ë")
	if not w.endswith("ë"):
		cands.append(w + "ë")

	# 2) ç vs c confusion (single replacement positions)
	for i, ch in enumerate(w):
		if ch == "c":
			cands.append(w[:i] + "ç" + w[i + 1 :])
		if ch == "e":
			cands.append(w[:i] + "ë" + w[i + 1 :])
		if ch == "ë":
			cands.append(w[:i] + "e" + w[i + 1 :])

	# 3) collapse double consonants (OCR repeats letters)
	cands.append(_collapse_double_consonants(w))

	# 4) Albanian digraphs often lose one letter in handwriting/OCR.
	cands.extend(_digraph_expansion_candidates(w))

	# 5) Single missing / extra letter hypotheses, filtered by lexicon below.
	cands.extend(_single_letter_insertion_candidates(w, lexicon))
	cands.extend(_single_letter_deletion_candidates(w))

	# 6) Nearby transposition, useful for dictation mistakes and OCR swaps.
	cands.extend(_adjacent_transposition_candidates(w))

	# Dedupe, keep only present in lexicon
	out = []
	seen = set()
	for c in cands:
		if not c or c == w:
			continue
		if c in lexicon and c not in seen:
			seen.add(c)
			out.append(c)
	return out[:5]


def _suggest_from_lexicon(token: str, buckets: Dict[Tuple[str, int], List[str]], max_suggestions: int = 5) -> List[str]:
	t = token.lower()
	if not t:
		return []
	first = t[0]
	candidates: List[str] = []
	for ln in range(max(2, len(t) - 2), len(t) + 3):
		candidates.extend(buckets.get((first, ln), []))

	scored = []
	for c in candidates:
		d = _levenshtein(t, c, max_dist=2)
		if d <= 2:
			scored.append((d, c))
	scored.sort(key=lambda x: (x[0], x[1]))
	out = []
	for _, c in scored:
		if c not in out:
			out.append(c)
		if len(out) >= max_suggestions:
			break
	return out


def _collapse_double_consonants(word: str) -> str:
	# Reduce any double letters (e.g., tt -> t). Conservative but helpful for OCR noise.
	return re.sub(r"([A-Za-zËÇëç])\1+", r"\1", word, flags=re.UNICODE)


def _diacritics_normalize(word: str) -> str:
	return word.replace("ë", "e").replace("ç", "c")


def _is_diacritics_variant(a: str, b: str) -> bool:
	return _diacritics_normalize(a) == _diacritics_normalize(b) and a != b


ALBANIAN_DIGRAPHS = ("dh", "gj", "ll", "nj", "rr", "sh", "th", "xh", "zh")
ALBANIAN_VOWELS = set("aeëiouy")
ALBANIAN_LETTERS = "abcçdeëfghijklmnopqrstuvxyz"


def _digraph_expansion_candidates(word: str) -> List[str]:
	"""
	Generate conservative candidates for Albanian digraph loss:
	d -> dh, g -> gj, l -> ll, n -> nj, r -> rr, s -> sh, t -> th, x -> xh, z -> zh.
	"""
	cands: List[str] = []
	for digraph in ALBANIAN_DIGRAPHS:
		first = digraph[0]
		for idx, ch in enumerate(word):
			if ch == first:
				cands.append(word[:idx] + digraph + word[idx + 1 :])
	return cands


def _single_letter_insertion_candidates(word: str, lexicon: set) -> List[str]:
	cands: List[str] = []
	lengths = {len(candidate) for candidate in lexicon}
	if len(word) + 1 not in lengths:
		return cands
	for idx in range(len(word) + 1):
		for letter in ALBANIAN_LETTERS:
			cands.append(word[:idx] + letter + word[idx:])
	return cands


def _single_letter_deletion_candidates(word: str) -> List[str]:
	return [word[:idx] + word[idx + 1 :] for idx in range(len(word))]


def _adjacent_transposition_candidates(word: str) -> List[str]:
	cands: List[str] = []
	for idx in range(len(word) - 1):
		if word[idx] != word[idx + 1]:
			cands.append(word[:idx] + word[idx + 1] + word[idx] + word[idx + 2 :])
	return cands


def _is_adjacent_transposition(a: str, b: str) -> bool:
	if len(a) != len(b) or a == b:
		return False
	diffs = [idx for idx, (ca, cb) in enumerate(zip(a, b)) if ca != cb]
	return len(diffs) == 2 and diffs[1] == diffs[0] + 1 and a[diffs[0]] == b[diffs[1]] and a[diffs[1]] == b[diffs[0]]


def _single_substitution(a: str, b: str) -> Optional[Tuple[str, str]]:
	if len(a) != len(b):
		return None
	diffs = [(ca, cb) for ca, cb in zip(a, b) if ca != cb]
	if len(diffs) == 1:
		return diffs[0]
	return None


def _classify_expected_mismatch(expected: str, recognized: str) -> Dict[str, Any]:
	exp = (expected or "").strip()
	rec = (recognized or "").strip()
	exp_l = exp.lower()
	rec_l = rec.lower()

	if exp and not rec:
		return {
			"type": "missing_word",
			"message": "Fjala mungon në tekstin e lexuar nga OCR ose në diktim.",
			"suggestions": [exp],
		}
	if rec and not exp:
		return {
			"type": "extra_word",
			"message": "U gjet një fjalë shtesë që nuk është në tekstin e pritur.",
			"suggestions": [],
		}
	if exp_l == rec_l and exp != rec:
		return {
			"type": "capitalization",
			"message": "Fjala është e njëjtë, por ka ndryshim në shkronjë të madhe/të vogël.",
			"suggestions": [exp],
		}
	if _is_diacritics_variant(rec_l, exp_l):
		return {
			"type": "diacritics_suspected",
			"message": "Gabim diakritik: kontrollo përdorimin e ë/e ose ç/c.",
			"suggestions": [exp],
		}
	if _collapse_double_consonants(rec_l) == exp_l:
		return {
			"type": "double_consonant_suspected",
			"message": "Dyshohet shkronjë e dyfishtë e tepërt.",
			"suggestions": [exp],
		}
	for digraph in ALBANIAN_DIGRAPHS:
		if digraph in exp_l and digraph not in rec_l:
			return {
				"type": "digraph_suspected",
				"message": f"Dyshohet gabim te grupi karakteristik shqip '{digraph}'.",
				"suggestions": [exp],
			}
	if len(exp_l) == len(rec_l) + 1 and _levenshtein(rec_l, exp_l, max_dist=1) == 1:
		return {
			"type": "missing_letter",
			"message": "Mungon një shkronjë në fjalë.",
			"suggestions": [exp],
		}
	if len(rec_l) == len(exp_l) + 1 and _levenshtein(rec_l, exp_l, max_dist=1) == 1:
		return {
			"type": "extra_letter",
			"message": "Ka një shkronjë të tepërt në fjalë.",
			"suggestions": [exp],
		}
	if _is_adjacent_transposition(rec_l, exp_l):
		return {
			"type": "letter_transposition",
			"message": "Dy shkronja janë ndërruar vendesh.",
			"suggestions": [exp],
		}

	substitution = _single_substitution(rec_l, exp_l)
	if substitution:
		found, needed = substitution
		if found in ALBANIAN_VOWELS and needed in ALBANIAN_VOWELS:
			return {
				"type": "vowel_confusion",
				"message": f"Dyshohet ngatërrim zanor: '{found}' duhet të jetë '{needed}'.",
				"suggestions": [exp],
			}
		return {
			"type": "letter_substitution",
			"message": f"Dyshohet zëvendësim shkronje: '{found}' duhet të jetë '{needed}'.",
			"suggestions": [exp],
		}

	return {
		"type": "mismatch_expected",
		"message": "Fjala nuk përputhet me tekstin e pritur.",
		"suggestions": [exp] if exp else [],
	}


def _classify_lexicon_issue(token: str, suggestions: List[str], collapsed: str, lexicon: set) -> Tuple[str, str]:
	w = token.lower()
	if not suggestions:
		return "unknown_word", "Fjalë e panjohur në korpus; mund të jetë gabim drejtshkrimi ose emër i përveçëm."

	best = suggestions[0]
	if any(s.endswith("ë") and not w.endswith("ë") for s in suggestions):
		return "ending_ë_suspected", "Dyshohet mungesë e 'ë' (shpesh në fund të fjalës). Shiko sugjerimet."
	if any("ç" in s and "c" in w for s in suggestions):
		return "ç_suspected", "Dyshohet gabim te 'ç' / 'c'. Shiko sugjerimet."
	if collapsed != w and collapsed in lexicon:
		return "double_consonant_suspected", "Dyshohet shkronjë e dyfishtë (shpesh gabim OCR ose gabim drejtshkrimi)."
	if _is_diacritics_variant(w, best):
		return "diacritics_suspected", "Dyshohet gabim te ë/e ose ç/c. Shiko sugjerimet."
	if any(digraph in best and digraph not in w for digraph in ALBANIAN_DIGRAPHS):
		return "digraph_suspected", "Dyshohet gabim te një grup shkronjash karakteristik i shqipes (dh, gj, ll, nj, rr, sh, th, xh, zh)."
	if len(best) == len(w) + 1:
		return "missing_letter", "Mund të mungojë një shkronjë. Shiko sugjerimet."
	if len(w) == len(best) + 1:
		return "extra_letter", "Mund të ketë një shkronjë të tepërt. Shiko sugjerimet."
	if _is_adjacent_transposition(w, best):
		return "letter_transposition", "Dyshohet ndërrim vendesh i dy shkronjave."
	substitution = _single_substitution(w, best)
	if substitution:
		found, needed = substitution
		if found in ALBANIAN_VOWELS and needed in ALBANIAN_VOWELS:
			return "vowel_confusion", "Dyshohet ngatërrim zanor. Shiko sugjerimet."
		return "letter_substitution", "Dyshohet zëvendësim shkronje. Shiko sugjerimet."
	return "unknown_word", "Mund të ketë gabim drejtshkrimi. Shiko sugjerimet."


def _extract_tokens_with_confidence(img: "Image.Image") -> Tuple[List[Dict[str, Any]], float]:
	"""
	Extract tokens with OCR confidence using Tesseract's image_to_data.
	Returns (tokens, avg_confidence).
	"""
	if not pytesseract:
		return [], 0.0
	try:
		output_type = getattr(pytesseract, "Output", None)
		data = pytesseract.image_to_data(
			img,
			lang="sqi",
			config="--oem 1 --psm 6 -c preserve_interword_spaces=1",
			output_type=(output_type.DICT if output_type else None),
		)
	except Exception:
		return [], 0.0

	texts = data.get("text", []) if isinstance(data, dict) else []
	confs = data.get("conf", []) if isinstance(data, dict) else []
	tokens: List[Dict[str, Any]] = []
	conf_values: List[float] = []

	for raw, conf in zip(texts, confs):
		raw = (raw or "").strip()
		if not raw:
			continue
		m = re.search(r"[A-Za-zËÇëç]+", raw, flags=re.UNICODE)
		if not m:
			continue
		token = m.group(0)
		try:
			c = float(conf)
		except Exception:
			c = -1.0
		if c >= 0:
			conf_values.append(c)
		tokens.append({"token": token, "raw": raw, "confidence": c})

	avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0.0
	return tokens, avg_conf


@router.post("/ocr/analyze", response_model=OCRAnalysisOut)
async def analyze_dictation(
	image: UploadFile = File(...),
	expected_text: Optional[str] = Form(None),
	use_llm: bool = Form(True),  # Enable LLM post-processing by default
	db: Session = Depends(get_db)
):
	"""
	Intelligent OCR Pipeline for Albanian Language Documents.
	
	Pipeline stages:
	1. Image preprocessing (deskew, contrast, denoise, threshold)
	2. Multi-engine OCR (Tesseract sqi + PaddleOCR)
	3. LLM post-processing (GPT-4 for language refinement) [optional]
	4. Rule-based orthography analysis
	
	Parameters:
	- image: Scanned image or photo of Albanian text
	- expected_text: Optional reference text for comparison
	- use_llm: Enable GPT-4 post-processing (default: True)
	
	Returns:
	- extracted_text: Raw OCR output
	- refined_text: LLM-corrected text (if use_llm=True)
	- llm_corrections: List of corrections made by LLM
	- issues: Orthography issues detected
	"""

	if not pytesseract or not Image:
		raise HTTPException(
			status_code=501,
			detail="OCR libraries not installed. Install pillow and pytesseract with system-level tesseract."
		)

	content = await image.read()
	try:
		ocr_image = Image.open(BytesIO(content))
	except Exception as exc:
		raise HTTPException(status_code=400, detail="Invalid image file") from exc

	# Deskew + preprocess
	deskewed = _deskew_image(ocr_image)
	ocr_ready = _preprocess_for_ocr(deskewed)
	token_objs, avg_conf = _extract_tokens_with_confidence(ocr_ready)

	# Multi-pass OCR: provo disa konfigurime për të rritur saktësinë në shkrim dore
	ocr_candidates: List[Tuple[str, str]] = []  # (text, engine)

	def _try_ocr(cfg: str, use_lang: bool = True) -> None:
		try:
			txt = pytesseract.image_to_string(
				ocr_ready,
				lang="sqi" if use_lang else None,
				config=cfg,
			).strip()
			if txt:
				ocr_candidates.append((txt, "tesseract"))
		except Exception:
			pass

	# Konfigurime të ndryshme psm/oem + whitelist për alfabetin shqip
	common_cfg = "-c preserve_interword_spaces=1 -c tessedit_char_whitelist=\"A-Za-zËÇëç?.,' -\""
	_try_ocr(f"--oem 1 --psm 6 {common_cfg}", True)
	_try_ocr(f"--oem 1 --psm 4 {common_cfg}", True)
	_try_ocr(f"--oem 1 --psm 7 {common_cfg}", True)  # single line
	_try_ocr(f"--oem 1 --psm 11 {common_cfg}", True)  # sparse text
	_try_ocr(f"--oem 1 --psm 13 {common_cfg}", True)  # raw line

	# Fallback pa lang nëse sqi mungon
	_try_ocr(f"--oem 1 --psm 6 {common_cfg}", False)
	_try_ocr(f"--oem 1 --psm 4 {common_cfg}", False)

	# PaddleOCR fallback (nëse është instaluar) për shkrim dore
	paddle_text = _run_paddle_fallback(deskewed)
	if paddle_text:
		ocr_candidates.append((paddle_text, "paddleocr"))

	def _score(text: str) -> int:
		# Shkronja alfabetike + gjatësi: zgjedhim më të “lexueshmen”
		alpha = sum(ch.isalpha() for ch in text)
		return alpha + len(text)

	if not ocr_candidates:
		raise HTTPException(status_code=500, detail="OCR processing failed")

	best_text, engine_used = max(ocr_candidates, key=lambda x: _score(x[0]))
	extracted = best_text

	# ========================================================================
	# STAGE 3: LLM POST-PROCESSING (GPT-4 Language Refinement)
	# ========================================================================
	llm_result = _llm_refine_ocr_text(extracted, use_llm=use_llm)
	refined_text = llm_result["refined_text"]
	llm_corrections = llm_result["corrections"]
	llm_confidence = llm_result["confidence"]
	llm_model = llm_result["model_used"]
	llm_time = llm_result["processing_time_ms"]

	errors: List[Dict[str, Any]] = []
	suggestions: List[str] = []
	issues: List[Dict[str, Any]] = []

	# Use refined text for analysis if LLM was used
	text_for_analysis = refined_text if use_llm and llm_model != "none" else extracted
	extracted_norm = _norm_text(text_for_analysis)
	extracted_tokens = [t["token"] for t in token_objs] if token_objs else _tokenize_sq(extracted_norm)
	expected_norm = _norm_text(expected_text) if expected_text else ""
	expected_tokens = _tokenize_sq(expected_norm) if expected_text else []

	lexicon, buckets = _build_lexicon(db)

	if expected_text:
		# Compare token-by-token against expected reference text (orthography check)
		max_len = max(len(extracted_tokens), len(expected_tokens))
		for idx in range(max_len):
			rec_word = extracted_tokens[idx] if idx < len(extracted_tokens) else ""
			exp_word = expected_tokens[idx] if idx < len(expected_tokens) else ""
			if rec_word != exp_word:
				classification = _classify_expected_mismatch(exp_word, rec_word)
				issue_type = classification["type"]
				errors.append({"position": idx + 1, "expected": exp_word, "recognized": rec_word})
				issues.append({
					"position": idx + 1,
					"token": rec_word or exp_word,
					"type": issue_type,
					"message": classification["message"],
					"expected": exp_word,
					"recognized": rec_word,
					"suggestions": classification["suggestions"],
					"ocr_confidence": (token_objs[idx]["confidence"] if token_objs and idx < len(token_objs) else None),
					**_issue_meta(issue_type, None, bool(classification["suggestions"])),
				})
				if exp_word:
					suggestions.append(exp_word)
	else:
		# No reference text: run Albanian spelling heuristics using corpus lexicon
		for idx, tok in enumerate(extracted_tokens, start=1):
			w = tok.lower()
			if len(w) < 2:
				continue

			conf = None
			if token_objs and (idx - 1) < len(token_objs):
				conf = token_objs[idx - 1].get("confidence")

			# Flag low OCR-confidence tokens separately (often OCR noise, not orthography)
			if conf is not None and conf >= 0 and conf < 60:
				issues.append({
					"position": idx,
					"token": tok,
					"type": "low_confidence",
					"message": "Besueshmëri e ulët nga OCR — kontrollo manualisht këtë fjalë (mund të jetë gabim i nxjerrjes, jo i drejtshkrimit).",
					"expected": None,
					"recognized": tok,
					"suggestions": [],
					"ocr_confidence": conf,
					**_issue_meta("low_confidence", conf, False),
				})

			if w in lexicon:
				continue
			# Albanian-aware checks
			collapsed = _collapse_double_consonants(w)
			sugs: List[str] = []
			issue_type = "unknown_word"
			msg = "Fjalë e panjohur në korpus; mund të jetë gabim drejtshkrimi ose emër i përveçëm."

			# First: rule-based corrections (fast + Albanian-specific)
			rule_sugs = _rule_based_candidates(w, lexicon)
			if rule_sugs:
				sugs = rule_sugs
				issue_type, msg = _classify_lexicon_issue(w, sugs, collapsed, lexicon)
			else:
				# Second: distance-based suggestions from corpus
				sugs = _suggest_from_lexicon(w, buckets, max_suggestions=5)
				if sugs:
					issue_type, msg = _classify_lexicon_issue(w, sugs, collapsed, lexicon)
			issues.append({
				"position": idx,
				"token": tok,
				"type": issue_type,
				"message": msg,
				"expected": None,
				"recognized": tok,
				"suggestions": sugs,
				"ocr_confidence": conf,
				**_issue_meta(issue_type, conf, bool(sugs)),
			})

	return OCRAnalysisOut(
		extracted_text=_norm_text(extracted),  # Raw OCR output
		refined_text=refined_text if use_llm and llm_model != "none" else None,
		errors=errors,
		suggestions=suggestions,
		issues=issues,
		llm_corrections=llm_corrections,
		meta={
			"language": "sqi",
			"expected_provided": bool(expected_text),
			"tokens_extracted": len(extracted_tokens),
			"issues_found": len(issues),
			"ocr_confidence_avg": avg_conf,
			"ocr_engine": engine_used,
			"llm_enabled": use_llm,
			"llm_model": llm_model,
			"llm_confidence": llm_confidence,
			"llm_processing_time_ms": llm_time,
			"pipeline_version": "2.0-llm",
		},
	)
