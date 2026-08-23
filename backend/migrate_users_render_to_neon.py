#!/usr/bin/env python3
"""
Migrate users (+ optional learning progress) from old Render Postgres -> Neon.

Does NOT wipe Neon curriculum (courses/levels/exercises).
Merges users by username/email; remaps IDs for progress tables.

Usage:
  cd backend
  SOURCE_DATABASE_URL="postgresql://...@...render.com/..." \\
  TARGET_DATABASE_URL="postgresql://...@...neon.tech/..." \\
  .venv/bin/python migrate_users_render_to_neon.py

Optional:
  MIGRATE_PROGRESS=1   # also copy attempts / progress / course_progress / achievements / srs
  DRY_RUN=1            # print what would happen, no writes
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import create_engine, inspect as sa_inspect, text
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import Base


def _normalize_url(url: str) -> str:
	url = url.strip().strip('"').strip("'")
	if url.startswith("postgres://"):
		url = "postgresql://" + url[len("postgres://") :]
	if url.startswith("postgresql://") and "sslmode=" not in url:
		url += ("&" if "?" in url else "?") + "sslmode=require"
	return url


def _engine(url: str):
	return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 20})


def _row_dict(obj) -> Dict[str, Any]:
	return {c.key: getattr(obj, c.key) for c in sa_inspect(obj.__class__).mapper.column_attrs}


def _build_exercise_map(src, tgt) -> Dict[int, int]:
	"""Map old exercise_id -> new exercise_id via course name + level order + exercise order/prompt."""
	src_rows = (
		src.query(
			models.Exercise.id,
			models.Exercise.prompt,
			models.Exercise.order_index,
			models.Level.order_index.label("level_order"),
			models.Course.name.label("course_name"),
			models.Course.order_index.label("course_order"),
			models.Course.parent_class_id,
		)
		.join(models.Level, models.Level.id == models.Exercise.level_id)
		.join(models.Course, models.Course.id == models.Exercise.course_id)
		.all()
	)
	tgt_rows = (
		tgt.query(
			models.Exercise.id,
			models.Exercise.prompt,
			models.Exercise.order_index,
			models.Level.order_index.label("level_order"),
			models.Course.name.label("course_name"),
			models.Course.order_index.label("course_order"),
			models.Course.parent_class_id,
		)
		.join(models.Level, models.Level.id == models.Exercise.level_id)
		.join(models.Course, models.Course.id == models.Exercise.course_id)
		.all()
	)

	def key(r) -> Tuple:
		return (
			(r.course_name or "").strip().lower(),
			int(r.course_order or 0),
			int(r.level_order or 0),
			int(r.order_index or 0),
			(r.prompt or "").strip().lower()[:180],
		)

	tgt_by_key = {}
	for r in tgt_rows:
		tgt_by_key.setdefault(key(r), r.id)

	mapping: Dict[int, int] = {}
	for r in src_rows:
		new_id = tgt_by_key.get(key(r))
		if new_id:
			mapping[r.id] = new_id
	return mapping


def _build_course_map(src, tgt) -> Dict[int, int]:
	src_courses = src.query(models.Course).all()
	tgt_courses = tgt.query(models.Course).all()
	tgt_by = {
		((c.name or "").strip().lower(), int(c.order_index or 0), c.parent_class_id is None): c.id
		for c in tgt_courses
	}
	# Also index children by parent name + child name
	tgt_parent_name = {c.id: (c.name or "").strip().lower() for c in tgt_courses}
	tgt_child = {}
	for c in tgt_courses:
		if c.parent_class_id:
			parent = next((p for p in tgt_courses if p.id == c.parent_class_id), None)
			pname = (parent.name if parent else "").strip().lower()
			tgt_child[((pname), (c.name or "").strip().lower(), int(c.order_index or 0))] = c.id

	src_parent_name = {c.id: (c.name or "").strip().lower() for c in src_courses}
	mapping: Dict[int, int] = {}
	for c in src_courses:
		if c.parent_class_id is None:
			k = ((c.name or "").strip().lower(), int(c.order_index or 0), True)
			if k in tgt_by:
				mapping[c.id] = tgt_by[k]
				continue
		else:
			pname = src_parent_name.get(c.parent_class_id, "")
			ck = (pname, (c.name or "").strip().lower(), int(c.order_index or 0))
			if ck in tgt_child:
				mapping[c.id] = tgt_child[ck]
	return mapping


def _build_level_map(src, tgt, course_map: Dict[int, int]) -> Dict[int, int]:
	src_levels = src.query(models.Level).all()
	tgt_levels = tgt.query(models.Level).all()
	tgt_by = {
		(l.course_id, int(l.order_index or 0), (l.name or "").strip().lower()): l.id
		for l in tgt_levels
	}
	mapping: Dict[int, int] = {}
	for l in src_levels:
		new_course = course_map.get(l.course_id)
		if not new_course:
			continue
		k = (new_course, int(l.order_index or 0), (l.name or "").strip().lower())
		if k in tgt_by:
			mapping[l.id] = tgt_by[k]
			continue
		# Fallback: same course + order only
		for (cid, order, _name), lid in tgt_by.items():
			if cid == new_course and order == int(l.order_index or 0):
				mapping[l.id] = lid
				break
	return mapping


def _reset_seq(tgt_engine, table: str, id_col: str = "id") -> None:
	with tgt_engine.begin() as conn:
		conn.execute(
			text(
				f"SELECT setval(pg_get_serial_sequence('{table}', '{id_col}'), "
				f"COALESCE((SELECT MAX({id_col}) FROM {table}), 1), true)"
			)
		)


def main() -> int:
	source = os.environ.get("SOURCE_DATABASE_URL")
	target = os.environ.get("TARGET_DATABASE_URL")
	migrate_progress = os.environ.get("MIGRATE_PROGRESS", "1").strip() not in {"0", "false", "no"}
	dry_run = os.environ.get("DRY_RUN", "0").strip() in {"1", "true", "yes"}

	if not source or not target:
		print("ERROR: set SOURCE_DATABASE_URL (old Render) and TARGET_DATABASE_URL (Neon).")
		return 1

	source = _normalize_url(source)
	target = _normalize_url(target)

	src_engine = _engine(source)
	tgt_engine = _engine(target)
	Base.metadata.create_all(bind=tgt_engine)

	Src = sessionmaker(bind=src_engine)
	Tgt = sessionmaker(bind=tgt_engine, autoflush=False)
	src = Src()
	tgt = Tgt()

	try:
		src_users = src.query(models.User).order_by(models.User.id).all()
		tgt_by_username = {u.username.lower(): u for u in tgt.query(models.User).all()}
		tgt_by_email = {u.email.lower(): u for u in tgt.query(models.User).all()}

		print(f"Source users: {len(src_users)}")
		print(f"Target users before: {len(tgt_by_username)}")
		print(f"Migrate progress: {migrate_progress} | dry_run: {dry_run}")

		user_id_map: Dict[int, int] = {}
		created = 0
		reused = 0
		skipped = 0

		for u in src_users:
			existing = tgt_by_username.get(u.username.lower()) or tgt_by_email.get(u.email.lower())
			if existing:
				user_id_map[u.id] = existing.id
				# Refresh password/profile from old DB so old logins still work
				if not dry_run:
					existing.password_hash = u.password_hash
					existing.email = u.email
					existing.age = u.age
					existing.date_of_birth = u.date_of_birth
					existing.address = u.address
					existing.phone_number = u.phone_number
					existing.is_active = u.is_active
					# Keep target admin flag if already admin; else copy
					existing.is_admin = bool(existing.is_admin or u.is_admin)
					existing.current_streak = u.current_streak or 0
					existing.longest_streak = u.longest_streak or 0
					existing.last_activity_date = u.last_activity_date
					existing.total_achievements = u.total_achievements or 0
					existing.last_login = u.last_login
					existing.created_at = u.created_at or existing.created_at
				reused += 1
				print(f"  reuse  old_id={u.id} -> new_id={existing.id} @{u.username}")
				continue

			data = _row_dict(u)
			data.pop("id", None)
			if dry_run:
				created += 1
				print(f"  create @{u.username} (dry-run)")
				continue

			nu = models.User(**data)
			tgt.add(nu)
			tgt.flush()
			user_id_map[u.id] = nu.id
			tgt_by_username[nu.username.lower()] = nu
			tgt_by_email[nu.email.lower()] = nu
			created += 1
			print(f"  create old_id={u.id} -> new_id={nu.id} @{u.username}")

		if not dry_run:
			tgt.commit()
			_reset_seq(tgt_engine, "users")

		print(f"Users: created={created} reused={reused} skipped={skipped}")

		if not migrate_progress:
			print("Done (users only).")
			return 0

		course_map = _build_course_map(src, tgt)
		level_map = _build_level_map(src, tgt, course_map)
		exercise_map = _build_exercise_map(src, tgt)
		print(
			f"Maps: courses={len(course_map)} levels={len(level_map)} exercises={len(exercise_map)}"
		)

		# --- CourseProgress ---
		cp_ok = cp_skip = 0
		for row in src.query(models.CourseProgress).all():
			new_uid = user_id_map.get(row.user_id)
			new_cid = course_map.get(row.course_id)
			if not new_uid or not new_cid:
				cp_skip += 1
				continue
			exists = (
				tgt.query(models.CourseProgress)
				.filter_by(user_id=new_uid, course_id=new_cid)
				.first()
			)
			if exists:
				if not dry_run:
					exists.total_exercises = row.total_exercises
					exists.completed_exercises = row.completed_exercises
					exists.correct_answers = row.correct_answers
					exists.total_points = row.total_points
					exists.accuracy_percentage = row.accuracy_percentage
					exists.is_completed = row.is_completed
					exists.is_unlocked = row.is_unlocked
					exists.completed_at = row.completed_at
					exists.updated_at = row.updated_at
				cp_ok += 1
				continue
			if dry_run:
				cp_ok += 1
				continue
			data = _row_dict(row)
			data.pop("id", None)
			data["user_id"] = new_uid
			data["course_id"] = new_cid
			tgt.add(models.CourseProgress(**data))
			cp_ok += 1
		print(f"course_progress: upserted~{cp_ok} skipped={cp_skip}")

		# --- Progress ---
		pr_ok = pr_skip = 0
		for row in src.query(models.Progress).all():
			# progress.user_id is string in schema
			try:
				old_uid = int(row.user_id)
			except (TypeError, ValueError):
				pr_skip += 1
				continue
			new_uid = user_id_map.get(old_uid)
			new_cid = course_map.get(row.course_id)
			new_lid = level_map.get(row.level_id)
			if not new_uid or not new_cid or not new_lid:
				pr_skip += 1
				continue
			exists = (
				tgt.query(models.Progress)
				.filter_by(user_id=str(new_uid), level_id=new_lid)
				.first()
			)
			if exists:
				if not dry_run:
					exists.points = row.points
					exists.errors = row.errors
					exists.stars = row.stars
					exists.completed = row.completed
					exists.course_id = new_cid
					exists.category = row.category
				pr_ok += 1
				continue
			if dry_run:
				pr_ok += 1
				continue
			data = _row_dict(row)
			data.pop("id", None)
			data["user_id"] = str(new_uid)
			data["course_id"] = new_cid
			data["level_id"] = new_lid
			tgt.add(models.Progress(**data))
			pr_ok += 1
		print(f"progress: upserted~{pr_ok} skipped={pr_skip}")

		# --- Attempts (append missing; avoid full duplicates by user+exercise+response+correct) ---
		at_ok = at_skip = 0
		for row in src.query(models.Attempt).all():
			try:
				old_uid = int(row.user_id)
			except (TypeError, ValueError):
				at_skip += 1
				continue
			new_uid = user_id_map.get(old_uid)
			new_eid = exercise_map.get(row.exercise_id)
			if not new_uid or not new_eid:
				at_skip += 1
				continue
			if dry_run:
				at_ok += 1
				continue
			dup = (
				tgt.query(models.Attempt)
				.filter_by(
					user_id=str(new_uid),
					exercise_id=new_eid,
					response=row.response,
					is_correct=row.is_correct,
				)
				.first()
			)
			if dup:
				at_skip += 1
				continue
			data = _row_dict(row)
			data.pop("id", None)
			data["user_id"] = str(new_uid)
			data["exercise_id"] = new_eid
			tgt.add(models.Attempt(**data))
			at_ok += 1
		print(f"attempts: inserted~{at_ok} skipped={at_skip}")

		# --- User achievements ---
		ach_by_code = {a.code: a.id for a in tgt.query(models.Achievement).all()}
		src_ach = {a.id: a.code for a in src.query(models.Achievement).all()}
		ua_ok = ua_skip = 0
		for row in src.query(models.UserAchievement).all():
			new_uid = user_id_map.get(row.user_id)
			code = src_ach.get(row.achievement_id)
			new_aid = ach_by_code.get(code) if code else None
			if not new_uid or not new_aid:
				ua_skip += 1
				continue
			exists = (
				tgt.query(models.UserAchievement)
				.filter_by(user_id=new_uid, achievement_id=new_aid)
				.first()
			)
			if exists or dry_run:
				ua_ok += 1
				continue
			tgt.add(
				models.UserAchievement(
					user_id=new_uid,
					achievement_id=new_aid,
					earned_at=row.earned_at,
				)
			)
			ua_ok += 1
		print(f"user_achievements: upserted~{ua_ok} skipped={ua_skip}")

		# --- SRS cards ---
		srs_ok = srs_skip = 0
		for row in src.query(models.SpacedRepetitionCard).all():
			new_uid = user_id_map.get(row.user_id)
			new_eid = exercise_map.get(row.exercise_id)
			if not new_uid or not new_eid:
				srs_skip += 1
				continue
			exists = (
				tgt.query(models.SpacedRepetitionCard)
				.filter_by(user_id=new_uid, exercise_id=new_eid)
				.first()
			)
			if exists or dry_run:
				srs_ok += 1
				continue
			data = _row_dict(row)
			data.pop("id", None)
			data["user_id"] = new_uid
			data["exercise_id"] = new_eid
			tgt.add(models.SpacedRepetitionCard(**data))
			srs_ok += 1
		print(f"srs_cards: upserted~{srs_ok} skipped={srs_skip}")

		if dry_run:
			tgt.rollback()
			print("Dry-run complete (no writes).")
		else:
			tgt.commit()
			for table in ("course_progress", "progress", "attempts", "user_achievements", "srs_cards"):
				try:
					_reset_seq(tgt_engine, table)
				except Exception as exc:
					print(f"  seq warn {table}: {exc}")
			print("Migration complete.")
		return 0
	except Exception as exc:
		tgt.rollback()
		print(f"ERROR: {type(exc).__name__}: {exc}")
		return 1
	finally:
		src.close()
		tgt.close()


if __name__ == "__main__":
	sys.exit(main())
