"""One-time repairs for Progress.points inflated by daily-challenge bonuses."""

from __future__ import annotations

import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def repair_inflated_level_progress_points(db: Session) -> dict:
	"""Clamp each Progress.points to the max awardable for that level.

	Daily challenges used to dump +50/+75 into a random Progress row, which
	inflated totals and falsely completed levels.
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

	updated = 0
	excess_moved = 0
	rows = db.query(models.Progress).all()
	for progress in rows:
		# Levels with no exercises: any points are invalid leftover bonus.
		cap = caps.get(progress.level_id, 0)
		current = int(progress.points or 0)
		if current <= cap:
			continue
		extra = current - cap
		progress.points = cap
		updated += 1
		excess_moved += extra
		# Preserve earned bonus on the user account when possible.
		try:
			uid = int(progress.user_id)
		except (TypeError, ValueError):
			continue
		user = db.query(models.User).filter(models.User.id == uid).first()
		if user is not None:
			user.bonus_points = int(getattr(user, "bonus_points", 0) or 0) + extra

	if updated:
		db.commit()
	result = {"updated_rows": updated, "excess_moved_to_bonus": excess_moved}
	logger.info("Progress points repair: %s", result)
	return result
