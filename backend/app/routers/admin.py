from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from passlib.context import CryptContext
from datetime import datetime
from typing import List, Optional

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
	user = db.query(models.User).filter(models.User.id == target_user_id).first()
	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	
	db.delete(user)
	db.commit()
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

