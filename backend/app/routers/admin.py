from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from passlib.context import CryptContext
from datetime import datetime
from typing import List, Optional
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError
from ..services.category_labels import category_label_sq

router = APIRouter()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_admin(user_id: int, db: Session):
	"""Verify if user is admin"""
	user = db.query(models.User).filter(models.User.id == user_id).first()
	if not user or not user.is_admin:
		raise HTTPException(status_code=403, detail="Admin access required")
	return user


@router.post("/create-admin-user")
def create_admin_user(user_data: schemas.AdminUserCreate, db: Session = Depends(get_db)):
	"""Create admin user"""
	# Check if username already exists
	if db.query(models.User).filter(models.User.username == user_data.username).first():
		raise HTTPException(status_code=400, detail="Username already registered")
	
	# Check if email already exists
	if db.query(models.User).filter(models.User.email == user_data.email).first():
		raise HTTPException(status_code=400, detail="Email already registered")
	
	# Hash password
	hashed_password = pwd_context.hash(user_data.password)
	
	# Create admin user
	db_user = models.User(
		username=user_data.username,
		email=user_data.email,
		age=user_data.age,
		password_hash=hashed_password,
		is_admin=True,
		created_at=datetime.utcnow()
	)
	
	db.add(db_user)
	db.commit()
	db.refresh(db_user)
	
	return {"message": "Admin user created successfully", "user_id": db_user.id}


# ============ USERS MANAGEMENT ============

@router.get("/users", response_model=List[schemas.UserOut])
def get_all_users(user_id: int, db: Session = Depends(get_db)):
	"""Get all users (admin only)"""
	verify_admin(user_id, db)
	users = db.query(models.User).all()
	return users


@router.get("/users/{target_user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, target_user_id: int, db: Session = Depends(get_db)):
	"""Get user by ID (admin only)"""
	verify_admin(user_id, db)
	user = db.query(models.User).filter(models.User.id == target_user_id).first()
	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	return user


@router.get("/users/{target_user_id}/report")
def get_user_report(user_id: int, target_user_id: int, db: Session = Depends(get_db)):
	"""Build an admin report exclusively from the selected user's stored activity."""
	verify_admin(user_id, db)
	user = db.query(models.User).filter(models.User.id == target_user_id).first()
	if not user:
		raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")

	attempt_rows = (
		db.query(models.Attempt, models.Exercise)
		.join(models.Exercise, models.Exercise.id == models.Attempt.exercise_id)
		.filter(models.Attempt.user_id == str(target_user_id))
		.order_by(models.Attempt.created_at.asc())
		.all()
	)

	def duration_minutes(attempt) -> float:
		seconds = attempt.duration_seconds if attempt.duration_seconds is not None else 60
		return max(0, min(seconds, 3600)) / 60

	total_attempts = len(attempt_rows)
	correct_attempts = sum(int(bool(attempt.is_correct)) for attempt, _ in attempt_rows)
	average_score = round(correct_attempts / total_attempts * 100) if total_attempts else 0
	total_minutes = round(sum(duration_minutes(attempt) for attempt, _ in attempt_rows))

	category_stats = defaultdict(lambda: {"total": 0, "correct": 0})
	day_stats = defaultdict(lambda: {"attempts": 0, "minutes": 0.0, "correct": 0})
	hour_stats = defaultdict(int)
	active_dates = set()
	period_stats = defaultdict(int)

	day_names = [
		"E hënë", "E martë", "E mërkurë", "E enjte",
		"E premte", "E shtunë", "E diel",
	]
	periods = [
		("Natën (00:00–05:59)", 0, 6),
		("Paradite (06:00–11:59)", 6, 12),
		("Pasdite (12:00–17:59)", 12, 18),
		("Mbrëmje (18:00–23:59)", 18, 24),
	]

	for attempt, exercise in attempt_rows:
		raw_category = (
			exercise.category.value
			if hasattr(exercise.category, "value")
			else str(exercise.category)
		)
		category = category_label_sq(raw_category)
		category_stats[category]["total"] += 1
		category_stats[category]["correct"] += int(bool(attempt.is_correct))

		if attempt.created_at:
			day_index = attempt.created_at.weekday()
			day_stats[day_index]["attempts"] += 1
			day_stats[day_index]["minutes"] += duration_minutes(attempt)
			day_stats[day_index]["correct"] += int(bool(attempt.is_correct))
			hour_stats[attempt.created_at.hour // 4] += 1
			active_dates.add(attempt.created_at.date())
			for period_name, start_hour, end_hour in periods:
				if start_hour <= attempt.created_at.hour < end_hour:
					period_stats[period_name] += 1
					break

	category_rows = []
	for category, values in category_stats.items():
		accuracy = round(values["correct"] / values["total"] * 100)
		category_rows.append({
			"area": category,
			"category": category,
			"score": accuracy,
			"exercises": values["total"],
			"completed": values["correct"],
			"total": values["total"],
			"percentage": accuracy,
		})
	category_rows.sort(key=lambda row: (row["score"], row["exercises"]), reverse=True)

	strengths = [row for row in category_rows if row["score"] >= 70][:3]
	weaknesses = sorted(
		(row for row in category_rows if row["score"] < 70),
		key=lambda row: (row["score"], -row["exercises"]),
	)[:3]

	activity_by_day = [
		{
			"day": day_names[index],
			"sessions": day_stats[index]["attempts"],
			"minutes": round(day_stats[index]["minutes"]),
		}
		for index in range(7)
	]
	peak_hours = [
		{"hour": f"{bucket * 4:02d}:00–{bucket * 4 + 3:02d}:59", "activity": hour_stats[bucket]}
		for bucket in range(6)
	]

	now = datetime.utcnow()
	month_names = [
		"Janar", "Shkurt", "Mars", "Prill", "Maj", "Qershor",
		"Korrik", "Gusht", "Shtator", "Tetor", "Nëntor", "Dhjetor",
	]
	month_keys = []
	for offset in range(5, -1, -1):
		month_number = now.year * 12 + now.month - 1 - offset
		month_keys.append((month_number // 12, month_number % 12 + 1))
	monthly_stats = defaultdict(lambda: {"total": 0, "correct": 0})
	for attempt, _ in attempt_rows:
		if attempt.created_at:
			key = (attempt.created_at.year, attempt.created_at.month)
			if key in month_keys:
				monthly_stats[key]["total"] += 1
				monthly_stats[key]["correct"] += int(bool(attempt.is_correct))
	progress_over_time = [
		{
			"month": month_names[month - 1],
			"avgScore": (
				round(monthly_stats[(year, month)]["correct"] / monthly_stats[(year, month)]["total"] * 100)
				if monthly_stats[(year, month)]["total"] else 0
			),
			"exercises": monthly_stats[(year, month)]["total"],
		}
		for year, month in month_keys
	]

	best_day = "Nuk ka ende të dhëna"
	days_with_activity = [
		(index, values)
		for index, values in day_stats.items()
		if values["attempts"] > 0
	]
	if days_with_activity:
		best_day_index, _ = max(
			days_with_activity,
			key=lambda item: (
				item[1]["correct"] / item[1]["attempts"],
				item[1]["attempts"],
			),
		)
		best_day = day_names[best_day_index]

	preferred_time = (
		max(period_stats.items(), key=lambda item: item[1])[0]
		if period_stats else "Nuk ka ende të dhëna"
	)
	if active_dates:
		span_days = max(1, (max(active_dates) - min(active_dates)).days + 1)
		active_days_per_week = min(7, len(active_dates) / max(1, span_days / 7))
		study_frequency = f"{active_days_per_week:.1f} ditë në javë"
	else:
		study_frequency = "Nuk ka ende aktivitet"

	recommendations = []
	if weaknesses:
		recommendations.append(
			f"Ushtroni më shumë te “{weaknesses[0]['area']}”; saktësia aktuale është {weaknesses[0]['score']}%."
		)
	if strengths:
		recommendations.append(
			f"Vazhdoni punën e mirë te “{strengths[0]['area']}”, ku saktësia është {strengths[0]['score']}%."
		)
	if total_attempts == 0:
		recommendations.append("Përdoruesi nuk ka përfunduar ende asnjë ushtrim.")
	elif total_attempts < 10:
		recommendations.append("Nevojiten më shumë ushtrime që analiza të bëhet më e qëndrueshme.")
	if user.current_streak:
		recommendations.append(
			f"Ruani ritmin aktual prej {user.current_streak} ditësh radhazi."
		)

	achievement_count = db.query(models.UserAchievement).filter(
		models.UserAchievement.user_id == target_user_id
	).count()
	level = "Fillestar" if average_score < 60 else "Mesatar" if average_score < 80 else "I avancuar"

	return {
		"generatedAt": now.isoformat(),
		"dataSource": "Të dhëna reale nga tentativat e përdoruesit",
		"strengths": strengths,
		"weaknesses": weaknesses,
		"activityByDay": activity_by_day,
		"peakHours": peak_hours,
		"progressOverTime": progress_over_time,
		"categoryPerformance": category_rows,
		"metrics": {
			"totalExercises": total_attempts,
			"completedExercises": correct_attempts,
			"averageScore": average_score,
			"totalTimeMinutes": total_minutes,
			"currentStreak": user.current_streak or 0,
			"longestStreak": user.longest_streak or 0,
			"achievements": achievement_count,
			"level": level,
		},
		"learningStyle": {
			"preferredTime": preferred_time,
			"averageSessionLength": (
				f"{round(total_minutes / total_attempts, 1)} minuta për ushtrim"
				if total_attempts else "Nuk ka ende të dhëna"
			),
			"studyFrequency": study_frequency,
			"bestPerformanceDay": best_day,
			"completionRate": average_score,
		},
		"recommendations": recommendations,
	}


@router.put("/users/{target_user_id}")
def update_user(
	user_id: int,
	target_user_id: int,
	user_update: dict,
	db: Session = Depends(get_db)
):
	"""Update user (admin only)"""
	verify_admin(user_id, db)
	user = db.query(models.User).filter(models.User.id == target_user_id).first()
	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	
	# Update allowed fields
	if "username" in user_update:
		# Check if username is already taken
		existing = db.query(models.User).filter(
			models.User.username == user_update["username"],
			models.User.id != target_user_id
		).first()
		if existing:
			raise HTTPException(status_code=400, detail="Username already taken")
		user.username = user_update["username"]
	
	if "email" in user_update:
		# Check if email is already taken
		existing = db.query(models.User).filter(
			models.User.email == user_update["email"],
			models.User.id != target_user_id
		).first()
		if existing:
			raise HTTPException(status_code=400, detail="Email already taken")
		user.email = user_update["email"]
	
	if "age" in user_update:
		user.age = user_update["age"]
	
	if "is_active" in user_update:
		user.is_active = user_update["is_active"]
	
	if "is_admin" in user_update:
		user.is_admin = user_update["is_admin"]
	
	if "password" in user_update:
		user.password_hash = pwd_context.hash(user_update["password"])
	
	db.commit()
	return {"message": "User updated successfully"}


@router.delete("/users/{target_user_id}")
def delete_user(user_id: int, target_user_id: int, db: Session = Depends(get_db)):
	"""Delete user (admin only)"""
	verify_admin(user_id, db)
	if user_id == target_user_id:
		raise HTTPException(status_code=400, detail="Nuk mund ta fshini llogarinë tuaj të administratorit")
	user = db.query(models.User).filter(models.User.id == target_user_id).first()
	if not user:
		raise HTTPException(status_code=404, detail="User not found")

	try:
		# Delete dependent learning/account data first so PostgreSQL foreign-key
		# constraints cannot leave the admin action half-completed.
		session_ids = [
			row[0] for row in db.query(models.ChatSession.id).filter(
				models.ChatSession.user_id == target_user_id
			).all()
		]
		if session_ids:
			db.query(models.ChatMessage).filter(
				models.ChatMessage.session_id.in_(session_ids)
			).delete(synchronize_session=False)
			db.query(models.ChatSession).filter(
				models.ChatSession.id.in_(session_ids)
			).delete(synchronize_session=False)

		db.query(models.EmailLog).filter(
			models.EmailLog.user_id == target_user_id
		).delete(synchronize_session=False)
		db.query(models.SpacedRepetitionCard).filter(
			models.SpacedRepetitionCard.user_id == target_user_id
		).delete(synchronize_session=False)
		db.query(models.UserDailyProgress).filter(
			models.UserDailyProgress.user_id == target_user_id
		).delete(synchronize_session=False)
		db.query(models.UserAchievement).filter(
			models.UserAchievement.user_id == target_user_id
		).delete(synchronize_session=False)
		db.query(models.CourseProgress).filter(
			models.CourseProgress.user_id == target_user_id
		).delete(synchronize_session=False)
		db.query(models.Attempt).filter(
			models.Attempt.user_id == str(target_user_id)
		).delete(synchronize_session=False)
		db.query(models.Progress).filter(
			models.Progress.user_id == str(target_user_id)
		).delete(synchronize_session=False)
		db.query(models.PedagogicalReview).filter(
			models.PedagogicalReview.reviewer_user_id == target_user_id
		).update(
			{models.PedagogicalReview.reviewer_user_id: None},
			synchronize_session=False,
		)

		db.delete(user)
		db.commit()
	except SQLAlchemyError:
		db.rollback()
		raise HTTPException(
			status_code=409,
			detail="Përdoruesi nuk mund të fshihet sepse ka të dhëna të lidhura",
		)
	return {"message": "User deleted successfully"}


# ============ CLASSES MANAGEMENT ============

@router.get("/classes", response_model=List[schemas.ClassOut])
def get_all_classes(user_id: int, db: Session = Depends(get_db)):
	"""Get all classes (admin only)"""
	verify_admin(user_id, db)
	classes = (
		db.query(models.Course)
		.filter(
			models.Course.parent_class_id == None,
			models.Course.name.like("Klasa%"),
		)
		.order_by(models.Course.order_index)
		.all()
	)
	result = []
	for cls in classes:
		courses = db.query(models.Course).filter(models.Course.parent_class_id == cls.id).order_by(models.Course.order_index).all()
		result.append(schemas.ClassOut(
			id=cls.id,
			name=cls.name,
			description=cls.description,
			order_index=cls.order_index,
			enabled=cls.enabled,
			courses=[schemas.CourseOut.model_validate(c) for c in courses],
			unlocked=True,
			completed=False
		))
	return result


@router.post("/classes", response_model=schemas.CourseOut)
def create_class(user_id: int, class_data: schemas.ClassCreate, db: Session = Depends(get_db)):
	"""Create new class (admin only)"""
	verify_admin(user_id, db)
	
	# Create class (which is a Course with parent_class_id = None)
	db_class = models.Course(
		name=class_data.name,
		description=class_data.description,
		order_index=class_data.order_index,
		category=models.CategoryEnum.VOCABULARY,  # Default category for classes
		enabled=class_data.enabled,
		parent_class_id=None
	)
	
	db.add(db_class)
	db.commit()
	db.refresh(db_class)
	
	return db_class


@router.put("/classes/{class_id}", response_model=schemas.CourseOut)
def update_class(
	user_id: int,
	class_id: int,
	class_update: schemas.ClassUpdate,
	db: Session = Depends(get_db)
):
	"""Update class (admin only)"""
	verify_admin(user_id, db)
	cls = db.query(models.Course).filter(
		models.Course.id == class_id,
		models.Course.parent_class_id == None
	).first()
	if not cls:
		raise HTTPException(status_code=404, detail="Class not found")
	
	if class_update.name is not None:
		cls.name = class_update.name
	if class_update.description is not None:
		cls.description = class_update.description
	if class_update.order_index is not None:
		cls.order_index = class_update.order_index
	if class_update.enabled is not None:
		cls.enabled = class_update.enabled
	
	db.commit()
	db.refresh(cls)
	return cls


@router.delete("/classes/{class_id}")
def delete_class(user_id: int, class_id: int, db: Session = Depends(get_db)):
	"""Delete class (admin only)"""
	verify_admin(user_id, db)
	cls = db.query(models.Course).filter(
		models.Course.id == class_id,
		models.Course.parent_class_id == None
	).first()
	if not cls:
		raise HTTPException(status_code=404, detail="Class not found")
	
	# Delete all courses in this class
	courses = db.query(models.Course).filter(models.Course.parent_class_id == class_id).all()
	for course in courses:
		# Delete all levels in this course
		levels = db.query(models.Level).filter(models.Level.course_id == course.id).all()
		for level in levels:
			# Delete all exercises in this level
			db.query(models.Exercise).filter(models.Exercise.level_id == level.id).delete()
		db.query(models.Level).filter(models.Level.course_id == course.id).delete()
		db.query(models.Course).filter(models.Course.id == course.id).delete()
	
	db.delete(cls)
	db.commit()
	return {"message": "Class deleted successfully"}


# ============ LEVELS MANAGEMENT ============

@router.get("/levels", response_model=List[schemas.LevelOut])
def get_all_levels(user_id: int, course_id: Optional[int] = None, db: Session = Depends(get_db)):
	"""Get all levels (admin only)"""
	verify_admin(user_id, db)
	query = db.query(models.Level)
	if course_id:
		query = query.filter(models.Level.course_id == course_id)
	levels = query.order_by(models.Level.order_index).all()
	return levels


@router.post("/levels", response_model=schemas.LevelOut)
def create_level(user_id: int, level_data: schemas.LevelCreate, db: Session = Depends(get_db)):
	"""Create new level (admin only)"""
	verify_admin(user_id, db)
	
	# Verify course exists
	course = db.query(models.Course).filter(models.Course.id == level_data.course_id).first()
	if not course:
		raise HTTPException(status_code=404, detail="Course not found")
	
	db_level = models.Level(
		course_id=level_data.course_id,
		name=level_data.name,
		description=level_data.description,
		order_index=level_data.order_index,
		required_score=level_data.required_score,
		enabled=level_data.enabled
	)
	
	db.add(db_level)
	db.commit()
	db.refresh(db_level)
	
	return db_level


@router.put("/levels/{level_id}", response_model=schemas.LevelOut)
def update_level(
	user_id: int,
	level_id: int,
	level_update: schemas.LevelUpdate,
	db: Session = Depends(get_db)
):
	"""Update level (admin only)"""
	verify_admin(user_id, db)
	level = db.query(models.Level).filter(models.Level.id == level_id).first()
	if not level:
		raise HTTPException(status_code=404, detail="Level not found")
	
	if level_update.course_id is not None:
		# Verify course exists
		course = db.query(models.Course).filter(models.Course.id == level_update.course_id).first()
		if not course:
			raise HTTPException(status_code=404, detail="Course not found")
		level.course_id = level_update.course_id
	if level_update.name is not None:
		level.name = level_update.name
	if level_update.description is not None:
		level.description = level_update.description
	if level_update.order_index is not None:
		level.order_index = level_update.order_index
	if level_update.required_score is not None:
		level.required_score = level_update.required_score
	if level_update.enabled is not None:
		level.enabled = level_update.enabled
	
	db.commit()
	db.refresh(level)
	return level


@router.delete("/levels/{level_id}")
def delete_level(user_id: int, level_id: int, db: Session = Depends(get_db)):
	"""Delete level (admin only)"""
	verify_admin(user_id, db)
	level = db.query(models.Level).filter(models.Level.id == level_id).first()
	if not level:
		raise HTTPException(status_code=404, detail="Level not found")
	
	# Delete all exercises in this level
	db.query(models.Exercise).filter(models.Exercise.level_id == level_id).delete()
	
	db.delete(level)
	db.commit()
	return {"message": "Level deleted successfully"}


# ============ EXERCISES MANAGEMENT ============

@router.get("/exercises", response_model=List[schemas.ExerciseOut])
def get_all_exercises(
	user_id: int,
	level_id: Optional[int] = None,
	course_id: Optional[int] = None,
	db: Session = Depends(get_db)
):
	"""Get all exercises (admin only)"""
	verify_admin(user_id, db)
	query = db.query(models.Exercise)
	if level_id:
		query = query.filter(models.Exercise.level_id == level_id)
	if course_id:
		query = query.filter(models.Exercise.course_id == course_id)
	exercises = query.order_by(models.Exercise.order_index).all()
	return exercises


@router.get("/exercises/{exercise_id}", response_model=schemas.ExerciseOut)
def get_exercise(user_id: int, exercise_id: int, db: Session = Depends(get_db)):
	"""Get exercise by ID (admin only)"""
	verify_admin(user_id, db)
	exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
	if not exercise:
		raise HTTPException(status_code=404, detail="Exercise not found")
	return exercise


@router.post("/exercises", response_model=schemas.ExerciseOut)
def create_exercise(user_id: int, exercise_data: schemas.ExerciseCreate, db: Session = Depends(get_db)):
	"""Create new exercise (admin only)"""
	verify_admin(user_id, db)
	
	# Verify level and course exist
	level = db.query(models.Level).filter(models.Level.id == exercise_data.level_id).first()
	if not level:
		raise HTTPException(status_code=404, detail="Level not found")
	
	course = db.query(models.Course).filter(models.Course.id == exercise_data.course_id).first()
	if not course:
		raise HTTPException(status_code=404, detail="Course not found")
	
	db_exercise = models.Exercise(
		category=exercise_data.category,
		course_id=exercise_data.course_id,
		level_id=exercise_data.level_id,
		prompt=exercise_data.prompt,
		data=exercise_data.data,
		answer=exercise_data.answer,
		points=exercise_data.points,
		rule=exercise_data.rule,
		order_index=exercise_data.order_index,
		enabled=exercise_data.enabled
	)
	
	db.add(db_exercise)
	db.commit()
	db.refresh(db_exercise)
	
	return db_exercise


@router.put("/exercises/{exercise_id}", response_model=schemas.ExerciseOut)
def update_exercise(
	user_id: int,
	exercise_id: int,
	exercise_update: schemas.ExerciseUpdate,
	db: Session = Depends(get_db)
):
	"""Update exercise (admin only)"""
	verify_admin(user_id, db)
	exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
	if not exercise:
		raise HTTPException(status_code=404, detail="Exercise not found")
	
	if exercise_update.category is not None:
		exercise.category = exercise_update.category
	if exercise_update.course_id is not None:
		# Verify course exists
		course = db.query(models.Course).filter(models.Course.id == exercise_update.course_id).first()
		if not course:
			raise HTTPException(status_code=404, detail="Course not found")
		exercise.course_id = exercise_update.course_id
	if exercise_update.level_id is not None:
		# Verify level exists
		level = db.query(models.Level).filter(models.Level.id == exercise_update.level_id).first()
		if not level:
			raise HTTPException(status_code=404, detail="Level not found")
		exercise.level_id = exercise_update.level_id
	if exercise_update.prompt is not None:
		exercise.prompt = exercise_update.prompt
	if exercise_update.data is not None:
		exercise.data = exercise_update.data
	if exercise_update.answer is not None:
		exercise.answer = exercise_update.answer
	if exercise_update.points is not None:
		exercise.points = exercise_update.points
	if exercise_update.rule is not None:
		exercise.rule = exercise_update.rule
	if exercise_update.order_index is not None:
		exercise.order_index = exercise_update.order_index
	if exercise_update.enabled is not None:
		exercise.enabled = exercise_update.enabled
	
	db.commit()
	db.refresh(exercise)
	return exercise


@router.delete("/exercises/{exercise_id}")
def delete_exercise(user_id: int, exercise_id: int, db: Session = Depends(get_db)):
	"""Delete exercise (admin only)"""
	verify_admin(user_id, db)
	exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
	if not exercise:
		raise HTTPException(status_code=404, detail="Exercise not found")
	
	db.delete(exercise)
	db.commit()
	return {"message": "Exercise deleted successfully"}


# ============ STATISTICS ============

@router.get("/stats")
def get_admin_stats(user_id: int, db: Session = Depends(get_db)):
	"""Get admin statistics (admin only)"""
	verify_admin(user_id, db)
	
	total_users = db.query(models.User).count()
	total_classes = db.query(models.Course).filter(
		models.Course.parent_class_id == None,
		models.Course.name.like("Klasa%"),
	).count()
	total_courses = db.query(models.Course).filter(models.Course.parent_class_id != None).count()
	total_levels = db.query(models.Level).count()
	total_exercises = db.query(models.Exercise).count()
	total_attempts = db.query(models.Attempt).count()
	
	return {
		"total_users": total_users,
		"total_classes": total_classes,
		"total_courses": total_courses,
		"total_levels": total_levels,
		"total_exercises": total_exercises,
		"total_attempts": total_attempts
	}

