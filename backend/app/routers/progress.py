from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from ..database import get_db
from .. import models, schemas


router = APIRouter()


@router.get("/progress/{user_id}", response_model=List[schemas.ProgressOut])
def get_user_progress(user_id: str, db: Session = Depends(get_db)):
	"""Get progress for all categories for a user"""
	progress = (
		db.query(models.Progress)
		.filter(models.Progress.user_id == user_id)
		.all()
	)
	return progress


@router.get("/progress/{user_id}/status", response_model=List[schemas.CategoryStatusOut])
def get_category_status(user_id: str, db: Session = Depends(get_db)):
	"""Get status for all categories for a user"""
	# Get user's attempts grouped by category
	status_data = []
	
	for category in models.CategoryEnum:
		# Count total attempts for this category
		total_attempts = (
			db.query(func.count(models.Attempt.id))
			.join(models.Exercise, models.Attempt.exercise_id == models.Exercise.id)
			.filter(
				models.Attempt.user_id == user_id,
				models.Exercise.category == category
			)
			.scalar()
		)
		
		# Count correct attempts for this category
		correct_attempts = (
			db.query(func.count(models.Attempt.id))
			.join(models.Exercise, models.Attempt.exercise_id == models.Exercise.id)
			.filter(
				models.Attempt.user_id == user_id,
				models.Exercise.category == category,
				models.Attempt.is_correct == True
			)
			.scalar()
		)
		
		# Calculate accuracy
		accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
		
		# Determine if user can advance (80% accuracy required)
		can_advance = accuracy >= 80
		
		status_data.append(schemas.CategoryStatusOut(
			category=category,
			total_attempts=total_attempts or 0,
			correct_attempts=correct_attempts or 0,
			accuracy=accuracy,
			can_advance=can_advance
		))
	
	return status_data


@router.get("/progress/{user_id}/totals")
def get_user_totals(user_id: str, db: Session = Depends(get_db)):
	"""Lightweight totals for header/stats — avoids the heavy full overview query."""
	total_points, total_stars = (
		db.query(
			func.coalesce(func.sum(models.Progress.points), 0),
			func.coalesce(func.sum(models.Progress.stars), 0),
		)
		.filter(models.Progress.user_id == user_id)
		.one()
	)
	return {
		"user_id": user_id,
		"total_points": int(total_points or 0),
		"total_stars": int(total_stars or 0),
	}


@router.get("/progress/{user_id}/overview", response_model=schemas.UserProgressOut)
def get_user_overview(user_id: str, db: Session = Depends(get_db)):
	"""Get comprehensive overview of user progress across all courses"""
	# Aggregate totals in SQL (fast path for header stats too)
	total_points, total_stars = (
		db.query(
			func.coalesce(func.sum(models.Progress.points), 0),
			func.coalesce(func.sum(models.Progress.stars), 0),
		)
		.filter(models.Progress.user_id == user_id)
		.one()
	)
	total_points = int(total_points or 0)
	total_stars = int(total_stars or 0)

	# Get all courses
	courses = db.query(models.Course).order_by(models.Course.order_index).all()
	
	# Get user's progress
	user_progress = (
		db.query(models.Progress)
		.filter(models.Progress.user_id == user_id)
		.all()
	)
	
	course_progress_list = []
	
	for course in courses:
		# Get levels for this course
		levels = (
			db.query(models.Level)
			.filter(models.Level.course_id == course.id)
			.order_by(models.Level.order_index)
			.all()
		)
		
		# Get progress for this course
		course_progress = [
			p for p in user_progress 
			if p.course_id == course.id
		]
		
		# Calculate overall score for this course
		if course_progress:
			total_exercises = len(course_progress)
			completed_exercises = sum(1 for p in course_progress if p.completed)
			overall_score = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
		else:
			overall_score = 0
		
		# Determine if course is unlocked
		unlocked = course.order_index == 1 or any(p.completed for p in course_progress)
		
		# Determine if course is completed
		completed = all(p.completed for p in course_progress) if course_progress else False
		
		course_progress_list.append(schemas.CourseProgressOut(
			course=course,
			levels=levels,
			progress=course_progress,
			unlocked=unlocked,
			completed=completed,
			overall_score=overall_score
		))
	
	return schemas.UserProgressOut(
		user_id=user_id,
		total_points=total_points,
		total_stars=total_stars,
		courses=course_progress_list
	)


@router.get("/courses/{course_id}/levels/{level_id}/progress/{user_id}", response_model=schemas.ProgressOut)
def get_level_progress(course_id: int, level_id: int, user_id: str, db: Session = Depends(get_db)):
	"""Get progress for a specific level for a user"""
	progress = (
		db.query(models.Progress)
		.filter(
			models.Progress.user_id == user_id,
			models.Progress.course_id == course_id,
			models.Progress.level_id == level_id
		)
		.first()
	)
	
	if not progress:
		raise HTTPException(status_code=404, detail="Progress not found")
	
	return progress


