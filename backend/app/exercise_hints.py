"""Task hints for Levels 10–12 across all classes (shown like other exercise tips).

Also cleans legacy prompt suffixes such as trailing «Saktë:».
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

HINT_SPELLING_PUNCTUATION = (
	"Rishkruaj fjalinë saktë."
)
HINT_CONCRETE = (
	"Zgjidh fjalën konkrete — diçka që mund ta shohësh ose ta prekësh."
)
HINT_ABSTRACT = (
	"Zgjidh fjalën abstrakte — ndjenjë ose ide, jo objekt."
)
HINT_ABSTRACT_CONCRETE_GENERIC = (
	"Zgjidh fjalën e duhur: konkrete (objekt) ose abstrakte (ndjenjë/ide)."
)
HINT_BUILD_SENTENCE = (
	"Rendit fjalët e dhëna dhe formo një fjali të saktë."
)


def _category_value(category: Any) -> str:
	if category is None:
		return ""
	if hasattr(category, "value"):
		return str(category.value)
	return str(category)


def hint_for_exercise(category: Any, data: Optional[Union[dict, str]] = None) -> Optional[str]:
	"""Return the instructional hint for a Level 10/11/12 style exercise."""
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

	if cat == "spelling_punctuation":
		return HINT_SPELLING_PUNCTUATION
	if cat == "build_sentence":
		return HINT_BUILD_SENTENCE
	if cat == "abstract_concrete":
		kind = str(payload.get("type") or "").lower()
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
	cleaned = _SAKTE_SUFFIX_RE.sub("", str(prompt)).rstrip()
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


def backfill_level_10_12_exercise_hints(db: Session) -> dict:
	"""Set missing/outdated hints for spelling_punctuation, abstract_concrete, build_sentence."""
	from . import models

	updated = 0
	skipped = 0
	exercises = (
		db.query(models.Exercise)
		.filter(models.Exercise.category.in_([
			models.CategoryEnum.SPELLING_PUNCTUATION,
			models.CategoryEnum.ABSTRACT_CONCRETE,
			models.CategoryEnum.BUILD_SENTENCE,
		]))
		.all()
	)
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
