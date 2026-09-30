"""Task instruction tips for all exercise categories (shown as 💡 before the task).

Also cleans legacy prompt suffixes such as trailing «Saktë:» and «Fjala:».
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional, Union

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Legacy Level 10 prompts appended "\nSaktë:" as an answer blank label.
_SAKTE_SUFFIX_RE = re.compile(r"(?:\r?\n|\s)+Saktë:\s*$", re.IGNORECASE)
# Legacy Level 9 (phrases) prompts appended "\nFjala:" as an answer blank label.
_FJALA_SUFFIX_RE = re.compile(r"(?:\r?\n|\s)+Fjala:\s*$", re.IGNORECASE)
# Optional "Përshkrimi:" label left in front of phrase prompts.
_PERSHKRIMI_PREFIX_RE = re.compile(r"^Përshkrimi:\s*", re.IGNORECASE)

HINT_LISTEN_WRITE = "Dëgjo me kujdes dhe shkruaj atë që dëgjon."
HINT_WORD_FROM_DESCRIPTION = "Lexo përshkrimin dhe zgjidh fjalën e duhur."
HINT_SYNONYMS = "Gjej fjalën që ka kuptim të njëjtë ose të ngjashëm."
HINT_ANTONYMS = "Gjej fjalën që ka kuptim të kundërt."
HINT_SYNONYMS_ANTONYMS = "Gjej sinonimin ose antonimin e fjalës."
HINT_ALBANIAN_OR_LOANWORD = "Vendos nëse fjala është shqipe apo huazim."
HINT_MISSING_LETTER = "Plotëso shkronjën që mungon në fjalë."
HINT_WRONG_LETTER = "Gjej fjalën e gabuar dhe shkruaj formën e saktë."
HINT_BUILD_WORD = "Rendit shkronjat dhe formo fjalën e saktë."
HINT_NUMBER_TO_WORD = "Shkruaj numrin me fjalë."
HINT_PHRASES = "Lexo përshkrimin dhe shkruaj fjalën që i përgjigjet."
HINT_SPELLING_PUNCTUATION = "Rishkruaj fjalinë saktë."
HINT_CONCRETE = "Zgjidh fjalën konkrete — diçka që mund ta shohësh ose ta prekësh."
HINT_ABSTRACT = "Zgjidh fjalën abstrakte — ndjenjë ose ide, jo objekt."
HINT_ABSTRACT_CONCRETE_GENERIC = "Zgjidh fjalën e duhur: konkrete (objekt) ose abstrakte (ndjenjë/ide)."
HINT_BUILD_SENTENCE = "Rendit fjalët e dhëna dhe formo një fjali të saktë."


def _category_value(category: Any) -> str:
	if category is None:
		return ""
	if hasattr(category, "value"):
		return str(category.value)
	return str(category)


def hint_for_exercise(category: Any, data: Optional[Union[dict, str]] = None) -> Optional[str]:
	"""Return the instructional tip for an exercise category."""
	cat = _category_value(category)
	payload: dict = {}
	if isinstance(data, dict):
		payload = data
	elif isinstance(data, str) and data.strip():
		try:
			parsed = json.loads(data)
			if isinstance(parsed, dict):
				payload = parsed
		except Exception:
			payload = {}

	kind = str(payload.get("type") or "").lower()

	if cat == "listen_write":
		return HINT_LISTEN_WRITE
	if cat == "word_from_description":
		return HINT_WORD_FROM_DESCRIPTION
	if cat == "synonyms_antonyms":
		if kind == "synonym":
			return HINT_SYNONYMS
		if kind == "antonym":
			return HINT_ANTONYMS
		return HINT_SYNONYMS_ANTONYMS
	if cat == "albanian_or_loanword":
		return HINT_ALBANIAN_OR_LOANWORD
	if cat == "missing_letter":
		return HINT_MISSING_LETTER
	if cat == "wrong_letter":
		return HINT_WRONG_LETTER
	if cat == "build_word":
		return HINT_BUILD_WORD
	if cat == "number_to_word":
		return HINT_NUMBER_TO_WORD
	if cat == "phrases":
		return HINT_PHRASES
	if cat == "spelling_punctuation":
		return HINT_SPELLING_PUNCTUATION
	if cat == "build_sentence":
		return HINT_BUILD_SENTENCE
	if cat == "abstract_concrete":
		if kind == "concrete":
			return HINT_CONCRETE
		if kind == "abstract":
			return HINT_ABSTRACT
		return HINT_ABSTRACT_CONCRETE_GENERIC
	return None


def migrate_exercise_rule_column(engine: Engine) -> None:
	"""Widen exercises.rule so full Albanian hints fit (was VARCHAR(50))."""
	from sqlalchemy import inspect, text

	inspector = inspect(engine)
	if "exercises" not in set(inspector.get_table_names()):
		return

	columns = {col["name"]: col for col in inspector.get_columns("exercises")}
	if "rule" not in columns:
		return

	dialect = engine.dialect.name
	with engine.begin() as connection:
		if dialect == "postgresql":
			connection.execute(text("ALTER TABLE exercises ALTER COLUMN rule TYPE VARCHAR(255)"))
			logger.info("Widened exercises.rule to VARCHAR(255) on PostgreSQL")
		elif dialect == "sqlite":
			# SQLite stores type affinity loosely; recreate is unnecessary for length.
			logger.info("SQLite exercises.rule length is not strictly enforced; model updated to 255")


def clean_sakte_suffix(prompt: Optional[str]) -> Optional[str]:
	"""Remove trailing «Saktë:» label from spelling/punctuation prompts."""
	if prompt is None:
		return None
	return _SAKTE_SUFFIX_RE.sub("", str(prompt)).rstrip()


def clean_phrase_prompt(prompt: Optional[str]) -> Optional[str]:
	"""Remove trailing «Fjala:» and optional «Përshkrimi:» label from phrase prompts."""
	if prompt is None:
		return None
	cleaned = _FJALA_SUFFIX_RE.sub("", str(prompt)).rstrip()
	cleaned = _PERSHKRIMI_PREFIX_RE.sub("", cleaned).strip()
	return cleaned


def strip_sakte_from_spelling_prompts(db: Session) -> dict:
	"""One-time cleanup: remove «Saktë:» from stored spelling_punctuation prompts."""
	from . import models

	updated = 0
	skipped = 0
	exercises = (
		db.query(models.Exercise)
		.filter(models.Exercise.category == models.CategoryEnum.SPELLING_PUNCTUATION)
		.all()
	)
	for exercise in exercises:
		original = exercise.prompt or ""
		cleaned = clean_sakte_suffix(original) or ""
		if cleaned == original:
			skipped += 1
			continue
		exercise.prompt = cleaned
		updated += 1

	if updated:
		db.commit()
	return {"updated": updated, "skipped": skipped, "total": len(exercises)}


def strip_fjala_from_phrase_prompts(db: Session) -> dict:
	"""Remove «Fjala:» / «Përshkrimi:» labels from stored phrases prompts."""
	from . import models

	updated = 0
	skipped = 0
	exercises = (
		db.query(models.Exercise)
		.filter(models.Exercise.category == models.CategoryEnum.PHRASES)
		.all()
	)
	for exercise in exercises:
		original = exercise.prompt or ""
		cleaned = clean_phrase_prompt(original) or ""
		if cleaned == original:
			skipped += 1
			continue
		exercise.prompt = cleaned
		updated += 1

	if updated:
		db.commit()
	return {"updated": updated, "skipped": skipped, "total": len(exercises)}


def backfill_exercise_hints(db: Session) -> dict:
	"""Set missing/outdated instructional tips for all exercise categories."""
	from . import models

	updated = 0
	skipped = 0
	exercises = db.query(models.Exercise).all()
	for exercise in exercises:
		desired = hint_for_exercise(exercise.category, exercise.data)
		if not desired:
			skipped += 1
			continue
		if (exercise.rule or "").strip() == desired:
			skipped += 1
			continue
		exercise.rule = desired
		updated += 1

	if updated:
		db.commit()
	return {"updated": updated, "skipped": skipped, "total": len(exercises)}


# Backwards-compatible alias used by older call sites / migrations.
def backfill_level_10_12_exercise_hints(db: Session) -> dict:
	return backfill_exercise_hints(db)
