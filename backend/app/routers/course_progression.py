from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from ..database import get_db
from .. import models, schemas
from datetime import datetime
from typing import List

router = APIRouter()

def calculate_course_progress(db: Session, user_id: int, course_id: int) -> dict:
    """Calculate progress for a specific course"""
    # Get all exercises for this course
    total_exercises = db.query(models.Exercise).filter(
        models.Exercise.course_id == course_id
    ).count()
    
    # Get user's attempts for this course
    attempts = db.query(models.Attempt).join(models.Exercise).filter(
        and_(
            models.Attempt.user_id == str(user_id),
            models.Exercise.course_id == course_id
        )
    ).all()
    
    # Calculate stats
    completed_exercises = len(set(attempt.exercise_id for attempt in attempts))
    correct_answers = sum(1 for attempt in attempts if attempt.is_correct)
    total_points = sum(attempt.score_delta for attempt in attempts if attempt.score_delta > 0)
    
    # Calculate accuracy
    accuracy_percentage = (correct_answers / len(attempts)) * 100 if attempts else 0.0
    
    # Check if course is completed (80%+ accuracy and all exercises attempted)
    is_completed = (
        completed_exercises >= total_exercises and 
        accuracy_percentage >= 80.0 and
        total_exercises > 0
    )
    
    return {
        'total_exercises': total_exercises,
        'completed_exercises': completed_exercises,
        'correct_answers': correct_answers,
        'total_points': total_points,
        'accuracy_percentage': accuracy_percentage,
        'is_completed': is_completed
    }

def update_course_progress(db: Session, user_id: int, course_id: int) -> models.CourseProgress:
    """Update or create course progress record"""
    # Calculate current progress
    progress_data = calculate_course_progress(db, user_id, course_id)
    
    # Get or create progress record
    progress = db.query(models.CourseProgress).filter(
        and_(
            models.CourseProgress.user_id == user_id,
            models.CourseProgress.course_id == course_id
        )
    ).first()
    
    if not progress:
        progress = models.CourseProgress(
            user_id=user_id,
            course_id=course_id,
            is_unlocked=True  # First course is always unlocked
        )
        db.add(progress)
    
    # Update progress data
    progress.total_exercises = progress_data['total_exercises']
    progress.completed_exercises = progress_data['completed_exercises']
    progress.correct_answers = progress_data['correct_answers']
    progress.total_points = progress_data['total_points']
    progress.accuracy_percentage = progress_data['accuracy_percentage']
    
    # Mark as completed if criteria met
    if progress_data['is_completed'] and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = datetime.utcnow()
        
        # Unlock next course in sequence
        unlock_next_course(db, user_id, course_id)
        
        # Check if 80% of courses (nivele) in this class are completed (to unlock next class)
        # This check happens every time a course is completed, not just the last one
        course = db.query(models.Course).filter(models.Course.id == course_id).first()
        if course and course.parent_class_id:
            unlock_next_class_if_eligible(db, user_id, course.parent_class_id)
    
    progress.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(progress)
    
    return progress

def unlock_next_course(db: Session, user_id: int, completed_course_id: int):
	"""Unlock the next course in sequence after completing current course"""
	# Get the completed course
	completed_course = db.query(models.Course).filter(
		models.Course.id == completed_course_id
	).first()
	
	if not completed_course:
		return
	
	# Find next course in the same class (same parent_class_id) with higher order_index
	next_course = db.query(models.Course).filter(
		and_(
			models.Course.parent_class_id == completed_course.parent_class_id,
			models.Course.order_index > completed_course.order_index
		)
	).order_by(models.Course.order_index).first()
	
	if next_course:
		# Get or create progress record for next course
		next_progress = db.query(models.CourseProgress).filter(
			and_(
				models.CourseProgress.user_id == user_id,
				models.CourseProgress.course_id == next_course.id
			)
		).first()
		
		if not next_progress:
			next_progress = models.CourseProgress(
				user_id=user_id,
				course_id=next_course.id,
				is_unlocked=True
			)
			db.add(next_progress)
		else:
			next_progress.is_unlocked = True
		
		db.commit()
	else:
		# If there is no next course in this class, check unlocking the next class
		unlock_next_class_if_eligible(db, user_id, completed_course.parent_class_id)


def unlock_next_class_if_eligible(db: Session, user_id: int, class_course_id: int) -> None:
	"""Unlock the first course of the next class when 80% of courses in current class are completed."""
	if class_course_id is None:
		return
	# Get all courses under this class
	class_courses = db.query(models.Course).filter(
		models.Course.parent_class_id == class_course_id
	).order_by(models.Course.order_index).all()
	if not class_courses:
		return
	course_ids = [c.id for c in class_courses]
	# Count completed courses for this user in this class
	completed_count = db.query(models.CourseProgress).filter(
		and_(
			models.CourseProgress.user_id == user_id,
			models.CourseProgress.course_id.in_(course_ids),
			models.CourseProgress.is_completed == True
		)
	).count()
	completion_ratio = (completed_count / len(course_ids)) if course_ids else 0.0
	if completion_ratio >= 0.8:
		# Find the next class by order_index of the class container
		current_class = db.query(models.Course).filter(models.Course.id == class_course_id).first()
		if not current_class:
			return
		next_class = db.query(models.Course).filter(
			and_(
				models.Course.parent_class_id.is_(None),
				models.Course.order_index > current_class.order_index
			)
		).order_by(models.Course.order_index).first()
		if not next_class:
			return
		# Unlock first course in next class
		first_course_next_class = db.query(models.Course).filter(
			models.Course.parent_class_id == next_class.id
		).order_by(models.Course.order_index).first()
		if not first_course_next_class:
			return
		next_progress = db.query(models.CourseProgress).filter(
			and_(
				models.CourseProgress.user_id == user_id,
				models.CourseProgress.course_id == first_course_next_class.id
			)
		).first()
		if not next_progress:
			next_progress = models.CourseProgress(
				user_id=user_id,
				course_id=first_course_next_class.id,
				is_unlocked=True
			)
			db.add(next_progress)
		else:
			next_progress.is_unlocked = True
		db.commit()

@router.post("/update-course-progress/{user_id}/{course_id}")
def update_user_course_progress(
    user_id: int,
    course_id: int,
    db: Session = Depends(get_db)
):
    """Update course progress after exercise completion"""
    try:
        progress = update_course_progress(db, user_id, course_id)
        return {
            "message": "Course progress updated successfully",
            "progress": {
                "course_id": progress.course_id,
                "accuracy_percentage": progress.accuracy_percentage,
                "is_completed": progress.is_completed,
                "total_points": progress.total_points,
                "completed_exercises": progress.completed_exercises,
                "total_exercises": progress.total_exercises
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update course progress: {str(e)}")

@router.get("/course-progress/{user_id}", response_model=List[schemas.CourseProgressDetail])
def get_user_course_progress(user_id: int, db: Session = Depends(get_db)):
    """Get all course progress for a user"""
    progress_records = db.query(models.CourseProgress).filter(
        models.CourseProgress.user_id == user_id
    ).all()
    
    return progress_records

@router.get("/course-progress/{user_id}/{course_id}")
def get_specific_course_progress(user_id: int, course_id: int, db: Session = Depends(get_db)):
    """Get progress for a specific course"""
    progress = db.query(models.CourseProgress).filter(
        and_(
            models.CourseProgress.user_id == user_id,
            models.CourseProgress.course_id == course_id
        )
    ).first()
    
    if not progress:
        # Create initial progress record
        progress = update_course_progress(db, user_id, course_id)
    
    return {
        "course_id": progress.course_id,
        "accuracy_percentage": progress.accuracy_percentage,
        "is_completed": progress.is_completed,
        "is_unlocked": progress.is_unlocked,
        "total_points": progress.total_points,
        "completed_exercises": progress.completed_exercises,
        "total_exercises": progress.total_exercises,
        "completed_at": progress.completed_at
    }

@router.post("/initialize-course-progress/{user_id}")
def initialize_user_course_progress(user_id: int, db: Session = Depends(get_db)):
    """Initialize course progress for a new user - unlock first course in each class"""
    try:
        # Get all main classes (top-level "Klasa ..." only)
        main_classes = db.query(models.Course).filter(
            models.Course.parent_class_id.is_(None),
            models.Course.enabled == True,
            models.Course.name.like("Klasa%"),
        ).order_by(models.Course.order_index).all()
        
        for main_class in main_classes:
            # Get first course in this class
            first_course = db.query(models.Course).filter(
                models.Course.parent_class_id == main_class.id
            ).order_by(models.Course.order_index).first()
            
            if first_course:
                # Check if progress already exists
                existing_progress = db.query(models.CourseProgress).filter(
                    and_(
                        models.CourseProgress.user_id == user_id,
                        models.CourseProgress.course_id == first_course.id
                    )
                ).first()
                
                if not existing_progress:
                    # Create progress record with first course unlocked
                    progress = models.CourseProgress(
                        user_id=user_id,
                        course_id=first_course.id,
                        is_unlocked=True
                    )
                    db.add(progress)
        
        db.commit()
        return {"message": "Course progress initialized successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize course progress: {str(e)}")
