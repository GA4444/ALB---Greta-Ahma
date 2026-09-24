"""
Period statistics from live Attempt rows (database = source of truth).

Used by:
- Admin weekly / monthly / yearly dashboards
- Weekly email aggregation (same formulas)
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional, Tuple

from sqlalchemy.orm import Session

from ..models import Attempt, Exercise, User
from .category_labels import category_label_sq

PeriodRange = Literal["weekly", "monthly", "yearly"]

DAY_NAMES_SQ = [
	"E hënë",
	"E martë",
	"E mërkurë",
	"E enjte",
	"E premte",
	"E shtunë",
	"E diel",
]
MONTH_NAMES_SQ = [
	"Janar",
	"Shkurt",
	"Mars",
	"Prill",
	"Maj",
	"Qershor",
	"Korrik",
	"Gusht",
	"Shtator",
	"Tetor",
	"Nëntor",
	"Dhjetor",
]


def utcnow() -> datetime:
	return datetime.utcnow()


def period_bounds(range_key: PeriodRange, now: Optional[datetime] = None) -> Tuple[datetime, datetime]:
	"""
	Inclusive window [start, end] in UTC, matching weekly email (rolling window).

	- weekly: last 7 days
	- monthly: last 30 days
	- yearly: last 365 days
	"""
	end = now or utcnow()
	if range_key == "weekly":
		start = end - timedelta(days=7)
	elif range_key == "monthly":
		start = end - timedelta(days=30)
	elif range_key == "yearly":
		start = end - timedelta(days=365)
	else:
		raise ValueError(f"Unsupported period range: {range_key}")
	return start, end


def _duration_seconds(attempt: Attempt) -> int:
	# Same fallback as weekly email / admin user report
	if attempt.duration_seconds is not None:
		return max(0, min(int(attempt.duration_seconds), 3600))
	return 60


def compute_user_period_stats(
	db: Session,
	user_id: int,
	range_key: PeriodRange = "weekly",
	now: Optional[datetime] = None,
) -> Dict[str, Any]:
	"""Personalized stats for one user in a period (email + optional user reports)."""
	start, end = period_bounds(range_key, now)
	user = db.query(User).filter(User.id == user_id).first()

	attempts = (
		db.query(Attempt, Exercise)
		.join(Exercise, Exercise.id == Attempt.exercise_id)
		.filter(
			Attempt.user_id == str(user_id),
			Attempt.created_at >= start,
			Attempt.created_at <= end,
		)
		.all()
	)

	total = len(attempts)
	correct = sum(1 for attempt, _ in attempts if attempt.is_correct)
	avg_score = round((correct / total) * 100) if total else 0
	total_seconds = sum(_duration_seconds(attempt) for attempt, _ in attempts)

	category_stats: Dict[str, List[int]] = {}
	for attempt, exercise in attempts:
		raw = exercise.category.value if hasattr(exercise.category, "value") else str(exercise.category)
		bucket = category_stats.setdefault(raw, [0, 0])
		bucket[0] += 1
		bucket[1] += int(bool(attempt.is_correct))

	ranked = sorted(
		(
			(category, round(correct_count / count * 100), count)
			for category, (count, correct_count) in category_stats.items()
		),
		key=lambda row: (row[1], row[2]),
		reverse=True,
	)
	strengths = [
		f"{category_label_sq(category)} — {accuracy}% saktësi"
		for category, accuracy, _ in ranked[:3]
		if accuracy >= 70
	]
	weaknesses = [
		f"{category_label_sq(category)} — {accuracy}% saktësi"
		for category, accuracy, _ in sorted(ranked, key=lambda row: row[1])[:2]
		if accuracy < 70
	]

	return {
		"range": range_key,
		"period_start": start.isoformat(),
		"period_end": end.isoformat(),
		"generated_at": (now or utcnow()).isoformat(),
		"data_source": "attempts",
		"exercises_completed": total,
		"avg_score": avg_score,
		"time_spent_minutes": round(total_seconds / 60),
		"current_streak": (user.current_streak if user else 0) or 0,
		"strengths": strengths,
		"weaknesses": weaknesses,
	}


def compute_platform_period_stats(
	db: Session,
	range_key: PeriodRange,
	now: Optional[datetime] = None,
) -> Dict[str, Any]:
	"""
	Platform-wide weekly/monthly/yearly analytics from Attempt + Exercise.
	Aggregation happens in Python over a filtered query (SQLite-friendly).
	"""
	start, end = period_bounds(range_key, now)
	generated = now or utcnow()

	rows = (
		db.query(Attempt, Exercise)
		.join(Exercise, Exercise.id == Attempt.exercise_id)
		.filter(
			Attempt.created_at >= start,
			Attempt.created_at <= end,
		)
		.all()
	)

	total_attempts = len(rows)
	correct_attempts = sum(1 for attempt, _ in rows if attempt.is_correct)
	active_users = len({attempt.user_id for attempt, _ in rows if attempt.user_id})
	total_seconds = sum(_duration_seconds(attempt) for attempt, _ in rows)
	avg_score = round((correct_attempts / total_attempts) * 100) if total_attempts else 0

	# Category performance
	category_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "correct": 0})
	for attempt, exercise in rows:
		raw = exercise.category.value if hasattr(exercise.category, "value") else str(exercise.category)
		label = category_label_sq(raw)
		category_stats[label]["total"] += 1
		category_stats[label]["correct"] += int(bool(attempt.is_correct))

	categories = []
	for label, values in category_stats.items():
		accuracy = round(values["correct"] / values["total"] * 100) if values["total"] else 0
		categories.append({
			"category": label,
			"kategori": label,
			"total": values["total"],
			"correct": values["correct"],
			"percentage": accuracy,
			"pikë": accuracy,
		})
	categories.sort(key=lambda row: (-row["percentage"], -row["total"]))

	# Hour-of-day activity (UTC)
	hour_buckets = defaultdict(int)
	for attempt, _ in rows:
		if attempt.created_at:
			hour_buckets[attempt.created_at.hour] += 1
	peak_hours = [
		{"orë": f"{hour:02d}:00", "aktivitet": hour_buckets.get(hour, 0)}
		for hour in range(0, 24, 2)
	]

	series = _build_series(range_key, start, end, rows)

	return {
		"range": range_key,
		"period_start": start.isoformat(),
		"period_end": end.isoformat(),
		"generated_at": generated.isoformat(),
		"data_source": "attempts",
		"realtime": True,
		"summary": {
			"active_users": active_users,
			"total_attempts": total_attempts,
			"correct_attempts": correct_attempts,
			"avg_score": avg_score,
			"time_spent_minutes": round(total_seconds / 60),
			"success_rate": avg_score,
		},
		"series": series,
		"peak_hours": peak_hours,
		"categories": categories,
	}


def _build_series(
	range_key: PeriodRange,
	start: datetime,
	end: datetime,
	rows: List[Tuple[Attempt, Exercise]],
) -> List[Dict[str, Any]]:
	if range_key == "weekly":
		return _daily_series(start, end, rows)
	if range_key == "monthly":
		return _weekly_buckets_series(start, end, rows)
	return _monthly_series(start, end, rows)


def _empty_bucket() -> Dict[str, Any]:
	return {
		"attempts": 0,
		"correct": 0,
		"users": set(),
		"seconds": 0,
	}


def _finalize_bucket(label: str, key_name: str, bucket: Dict[str, Any]) -> Dict[str, Any]:
	attempts = bucket["attempts"]
	correct = bucket["correct"]
	avg = round((correct / attempts) * 100) if attempts else 0
	return {
		key_name: label,
		"period": label,
		"përdorues": len(bucket["users"]),
		"users": len(bucket["users"]),
		"përpjekje": attempts,
		"attempts": attempts,
		"ushtrime": attempts,
		"exercises": attempts,
		"suksese": correct,
		"correct": correct,
		"sukseRate": avg,
		"avg_score": avg,
		"success_rate": avg,
		"time_minutes": round(bucket["seconds"] / 60),
		"time_hours": round(bucket["seconds"] / 3600, 1),
		"sessions": attempts,
	}


def _daily_series(start: datetime, end: datetime, rows: List[Tuple[Attempt, Exercise]]) -> List[Dict[str, Any]]:
	# Last 7 calendar days ending on end.date() (inclusive)
	end_day = end.date()
	days = [end_day - timedelta(days=offset) for offset in range(6, -1, -1)]
	buckets = {day: _empty_bucket() for day in days}

	for attempt, _ in rows:
		if not attempt.created_at:
			continue
		day = attempt.created_at.date()
		if day not in buckets:
			continue
		buckets[day]["attempts"] += 1
		buckets[day]["correct"] += int(bool(attempt.is_correct))
		buckets[day]["users"].add(attempt.user_id)
		buckets[day]["seconds"] += _duration_seconds(attempt)

	out = []
	for day in days:
		# Prefer weekday name for chart X axis (existing UI used ditë)
		label = DAY_NAMES_SQ[day.weekday()]
		item = _finalize_bucket(label, "ditë", buckets[day])
		item["date"] = day.isoformat()
		out.append(item)
	return out


def _weekly_buckets_series(start: datetime, end: datetime, rows: List[Tuple[Attempt, Exercise]]) -> List[Dict[str, Any]]:
	# 4–5 rolling week buckets covering the 30-day window
	end_day = end.date()
	week_starts = []
	cursor = end_day - timedelta(days=end_day.weekday())  # Monday of current week
	for _ in range(5):
		week_starts.append(cursor)
		cursor = cursor - timedelta(days=7)
	week_starts = list(reversed(week_starts))

	# Keep only weeks that overlap [start.date(), end.date()]
	start_day = start.date()
	week_starts = [ws for ws in week_starts if ws + timedelta(days=6) >= start_day and ws <= end_day]
	if not week_starts:
		week_starts = [end_day - timedelta(days=end_day.weekday())]

	buckets = {ws: _empty_bucket() for ws in week_starts}

	for attempt, _ in rows:
		if not attempt.created_at:
			continue
		day = attempt.created_at.date()
		monday = day - timedelta(days=day.weekday())
		if monday not in buckets:
			# Assign to nearest contained week start if edge
			continue
		buckets[monday]["attempts"] += 1
		buckets[monday]["correct"] += int(bool(attempt.is_correct))
		buckets[monday]["users"].add(attempt.user_id)
		buckets[monday]["seconds"] += _duration_seconds(attempt)

	out = []
	for index, ws in enumerate(week_starts, start=1):
		label = f"Java {index}"
		item = _finalize_bucket(label, "muaj", buckets[ws])
		item["week_start"] = ws.isoformat()
		out.append(item)
	return out


def _monthly_series(start: datetime, end: datetime, rows: List[Tuple[Attempt, Exercise]]) -> List[Dict[str, Any]]:
	# Last 12 calendar months ending at end's month
	year = end.year
	month = end.month
	keys: List[Tuple[int, int]] = []
	for offset in range(11, -1, -1):
		m_index = year * 12 + month - 1 - offset
		keys.append((m_index // 12, m_index % 12 + 1))

	buckets = {key: _empty_bucket() for key in keys}

	for attempt, _ in rows:
		if not attempt.created_at:
			continue
		key = (attempt.created_at.year, attempt.created_at.month)
		if key not in buckets:
			continue
		buckets[key]["attempts"] += 1
		buckets[key]["correct"] += int(bool(attempt.is_correct))
		buckets[key]["users"].add(attempt.user_id)
		buckets[key]["seconds"] += _duration_seconds(attempt)

	out = []
	for y, m in keys:
		label = f"{MONTH_NAMES_SQ[m - 1][:3]} {y}"
		item = _finalize_bucket(label, "muaj", buckets[(y, m)])
		item["vit"] = str(y)
		item["year"] = y
		item["month"] = m
		out.append(item)
	return out
