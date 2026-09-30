"""Repairs for Progress.points / completion using distinct-correct logic."""

from __future__ import annotations

import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def repair_inflated_level_progress_points(db: Session) -> dict:
	"""Recompute Progress.points from distinct correct exercises and fix completion.

	Also moves any leftover over-cap bonus mass into users.bonus_points when
	legacy daily-challenge rewards had been dumped into Progress.
	"""
	from . import models

	caps = {
		row.level_id: int(row.total or 0)
		for row in (
			db.query(
				models.Exercise.level_id,
				func.coalesce(func.sum(models.Exercise.points), 0).label("total"),
			)
			.group_by(models.Exercise.level_id)
			.all()
		)
	}
	counts = {
		row.level_id: int(row.total or 0)
		for row in (
			db.query(
				models.Exercise.level_id,
				func.count(models.Exercise.id).label("total"),
			)
			.group_by(models.Exercise.level_id)
			.all()
		)
	}

	updated = 0
	excess_moved = 0
	completion_fixed = 0
	rows = db.query(models.Progress).all()
	for progress in rows:
		level_id = progress.level_id
		cap = caps.get(level_id, 0)
		total_exercises = counts.get(level_id, 0)
		level_exercise_ids = [
			row[0]
			for row in db.query(models.Exercise.id).filter(models.Exercise.level_id == level_id).all()
		]
		if level_exercise_ids:
			correct_ids = [
				row[0]
				for row in (
					db.query(models.Attempt.exercise_id)
					.filter(
						models.Attempt.user_id == progress.user_id,
						models.Attempt.is_correct == True,  # noqa: E712
						models.Attempt.exercise_id.in_(level_exercise_ids),
					)
					.distinct()
					.all()
				)
			]
		else:
			correct_ids = []

		if correct_ids:
			unique_points = int(
				db.query(func.coalesce(func.sum(models.Exercise.points), 0))
				.filter(models.Exercise.id.in_(correct_ids))
				.scalar()
				or 0
			)
		else:
			unique_points = 0

		current = int(progress.points or 0)
		if current > unique_points:
			extra = current - unique_points
			excess_moved += extra
			try:
				uid = int(progress.user_id)
			except (TypeError, ValueError):
				uid = None
			if uid is not None:
				user = db.query(models.User).filter(models.User.id == uid).first()
				if user is not None:
					user.bonus_points = int(getattr(user, "bonus_points", 0) or 0) + extra

		if progress.points != unique_points:
			progress.points = unique_points
			updated += 1

		# Never keep points above the one-pass level cap.
		if cap and progress.points > cap:
			progress.points = cap
			updated += 1

		accuracy = (len(correct_ids) / total_exercises * 100) if total_exercises else 0
		should_complete = accuracy >= 80
		if bool(progress.completed) != should_complete:
			progress.completed = should_complete
			completion_fixed += 1

	if updated or excess_moved or completion_fixed:
		db.commit()
	result = {
		"updated_rows": updated,
		"excess_moved_to_bonus": excess_moved,
		"completion_fixed": completion_fixed,
	}
	logger.info("Progress points repair: %s", result)
	return result
