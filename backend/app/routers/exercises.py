from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, distinct
from app.database import get_db, SessionLocal
from app.models import Exercise, Progress, User, Course, Level, Attempt, CourseProgress
from app.schemas import SubmitRequest, SubmitResult, ExerciseOut
from typing import List
from datetime import datetime
import unicodedata
import re

router = APIRouter()


def _post_submit_side_effects(user_id: str, exercise_id: int, is_correct: bool) -> None:
	"""Run streak / challenges / achievements / SRS after the client already got feedback."""
	db = SessionLocal()
	try:
		from .gamification import (
			update_user_streak,
			check_and_award_achievements,
			update_daily_challenge_progress,
			create_srs_card_for_mistake,
		)

		update_user_streak(db, user_id, award_achievements=False)
		update_daily_challenge_progress(db, user_id, "complete_n_exercises", increment=1)
		if is_correct:
			update_daily_challenge_progress(db, user_id, "perfect_accuracy", increment=1)
		check_and_award_achievements(db, user_id)
		if not is_correct:
			create_srs_card_for_mistake(db, user_id, exercise_id)
	except Exception as e:
		print(f"[WARNING] Gamification error: {e}")
	finally:
		db.close()


@router.get("/public-stats")
def get_public_stats(db: Session = Depends(get_db)):
	"""Get public statistics (no auth required)"""
	total_classes = db.query(Course).filter(
		Course.parent_class_id == None,
		Course.name.like("Klasa%"),
	).count()
	total_courses = db.query(Course).filter(Course.parent_class_id != None).count()
	total_levels = db.query(Level).count()
	total_exercises = db.query(Exercise).count()
	# Count distinct categories
	total_categories = db.query(distinct(Exercise.category)).count()
	
	return {
		"total_classes": total_classes,
		"total_courses": total_courses,
		"total_levels": total_levels,
		"total_exercises": total_exercises,
		"total_categories": total_categories
	}

@router.post("/{exercise_id}/submit")
async def submit_answer(
	exercise_id: int,
	request: SubmitRequest,
	background_tasks: BackgroundTasks,
	db: Session = Depends(get_db),
):
    # Get the exercise
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # Get the user
    user = db.query(User).filter(User.id == int(request.user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if answer is correct (case-insensitive, normalize whitespace, normalize unicode)
    # Ensure we have string values (handle None cases)
    exercise_answer_str = str(exercise.answer) if exercise.answer else ""
    user_response_str = str(request.response) if request.response else ""
    
    # Normalize Unicode and convert to lowercase
    exercise_answer_normalized = unicodedata.normalize('NFKC', exercise_answer_str.lower().strip())
    user_response_normalized = unicodedata.normalize('NFKC', user_response_str.lower().strip())
    
    # Normalize whitespace: replace multiple spaces/tabs/newlines with single space
    exercise_answer_clean = re.sub(r'\s+', ' ', exercise_answer_normalized)
    user_response_clean = re.sub(r'\s+', ' ', user_response_normalized)
    
    # Remove any remaining leading/trailing whitespace after normalization
    exercise_answer_clean = exercise_answer_clean.strip()
    user_response_clean = user_response_clean.strip()
    
    # First try: exact match after normalization
    is_correct = exercise_answer_clean == user_response_clean
    
    # If not matching, try removing all spaces (for cases where user adds spaces or answer has spaces)
    if not is_correct:
        exercise_no_spaces = ''.join(exercise_answer_clean.split())
        user_no_spaces = ''.join(user_response_clean.split())
        # Accept if they match without spaces (handles both "e kuqe" vs "ekuqe" and "zogi" vs "z ogi")
        if exercise_no_spaces == user_no_spaces and exercise_no_spaces:
            is_correct = True
    
    # Calculate points (use exercise.points directly)
    points_earned = exercise.points if is_correct else 0
    
    # Create attempt record for course progress tracking
    attempt = Attempt(
        exercise_id=exercise_id,
        user_id=request.user_id,
        response=request.response,
        is_correct=is_correct,
        score_delta=points_earned,
        # Ignore impossible/client-manipulated values; reports fall back to an
        # estimate when older clients do not provide a duration.
        duration_seconds=(
            max(0, min(request.duration_seconds, 3600))
            if request.duration_seconds is not None
            else None
        ),
    )
    db.add(attempt)
    
    # Get or create progress record
    progress = db.query(Progress).filter(
        Progress.user_id == request.user_id,
        Progress.level_id == exercise.level_id
    ).first()
    
    if not progress:
        progress = Progress(
            user_id=request.user_id,
            category=exercise.category,
            level_id=exercise.level_id,
            course_id=exercise.course_id,
            points=0,
            errors=0,
            stars=0,
            completed=False
        )
        db.add(progress)
    
    # Update progress
    if is_correct:
        progress.points += points_earned
        # Calculate stars based on accuracy
        if progress.errors == 0:
            progress.stars = 3
        elif progress.errors < 3:
            progress.stars = 2
        else:
            progress.stars = 1
    else:
        progress.errors += 1
    
    # Level completion via aggregate points (no full exercise load)
    total_possible_points = (
        db.query(func.coalesce(func.sum(Exercise.points), 0))
        .filter(Exercise.level_id == exercise.level_id)
        .scalar()
        or 0
    )
    accuracy = (progress.points / total_possible_points) * 100 if total_possible_points > 0 else 0
    level_completed = accuracy >= 80
    if level_completed:
        progress.completed = True

    # Course completion: all levels completed
    total_levels = (
        db.query(func.count(Level.id))
        .filter(Level.course_id == exercise.course_id)
        .scalar()
        or 0
    )
    completed_levels = db.query(Progress).filter(
        Progress.user_id == request.user_id,
        Progress.course_id == exercise.course_id,
        Progress.completed == True
    ).count()
    course_completed = total_levels > 0 and completed_levels == total_levels
    
    db.commit()
    
    # Update course progress (SQL aggregates; needed for unlock / course_completed flag)
    from .course_progression import update_course_progress
    course_progress = update_course_progress(db, int(request.user_id), exercise.course_id)

    # Defer streak / achievements / SRS so the learner sees feedback immediately
    background_tasks.add_task(
        _post_submit_side_effects,
        str(request.user_id),
        exercise_id,
        is_correct,
    )
    
    # Prepare response message
    if is_correct:
        if course_progress.is_completed and not course_completed:
            message = f"🎉 Kurs i përfunduar! Saktësia: {course_progress.accuracy_percentage:.1f}% - Kursi i ardhshëm u hap! 🚀"
        elif level_completed:
            message = f"🎉 Nivel i përfunduar! Saktësia: {accuracy:.1f}%"
        else:
            message = f"✅ Përgjigje e saktë! +{points_earned} pikë"
    else:
        message = f"❌ Përgjigje e gabuar. Provoni sërish!"
    
    return SubmitResult(
        exercise_id=exercise_id,
        is_correct=is_correct,
        score_delta=points_earned,
        new_points=progress.points,
        new_errors=progress.errors,
        stars=progress.stars,
        level_completed=level_completed,
        course_completed=course_progress.is_completed,
        message=message,
        correct_answer=exercise.answer if not is_correct else None
    )

@router.get("/courses/{course_id}/levels")
async def get_course_levels(course_id: int, db: Session = Depends(get_db)):
    levels = db.query(Level).filter(Level.course_id == course_id).order_by(Level.order_index).all()
    return levels

@router.get("/levels/{level_id}/exercises", response_model=List[ExerciseOut])
async def get_level_exercises(level_id: int, shuffle_choices: bool = True, db: Session = Depends(get_db)):
    """
    Get exercises for a level with optional choice shuffling.
    
    Args:
        level_id: The level ID
        shuffle_choices: If True, randomize answer choices (default: True)
    
    Returns:
        List of exercises with shuffled choices (if applicable)
    """
    # Only return fields defined in ExerciseOut (answer is excluded)
    exercises = db.query(Exercise).filter(Exercise.level_id == level_id).order_by(Exercise.order_index).all()
    
    # Shuffle choices to prevent pattern recognition
    if shuffle_choices:
        import json
        import random
        from datetime import datetime
        
        # Use hour as seed for consistent shuffling within the same hour
        # This prevents excessive randomization while still rotating answers
        hour_seed = datetime.utcnow().hour
        
        shuffled_exercises = []
        for exercise in exercises:
            if exercise.data:
                try:
                    data = json.loads(exercise.data)
                    
                    # Shuffle choices if they exist
                    if 'choices' in data and isinstance(data['choices'], list) and len(data['choices']) > 1:
                        # Use exercise ID + hour seed for deterministic shuffling
                        random.seed(exercise.id + hour_seed)
                        shuffled_choices = data['choices'].copy()
                        random.shuffle(shuffled_choices)
                        data['choices'] = shuffled_choices
                        
                        # Update exercise data
                        exercise.data = json.dumps(data, ensure_ascii=False)
                
                except (json.JSONDecodeError, TypeError):
                    # If JSON is invalid, keep original data
                    pass
            
            shuffled_exercises.append(exercise)
        
        return shuffled_exercises
    
    return exercises

@router.get("/classes")
async def get_classes(user_id: str = None, db: Session = Depends(get_db)):
    # Top-level classes only: parent_class_id is None AND name starts with "Klasa"
    # (excludes orphaned "Niveli X" rows that lost their parent and wrongly appear as classes)
    classes = (
        db.query(Course)
        .filter(
            Course.parent_class_id == None,
            Course.enabled == True,
            Course.name.like("Klasa%"),
        )
        .order_by(Course.order_index)
        .all()
    )
    
    class_data = []
    user_id_int = int(user_id) if user_id and user_id.isdigit() else None
    
    for i, class_obj in enumerate(classes):
        unlocked = False
        progress_percent = 0.0
        
        if user_id_int:
            # Get all courses under this class
            class_courses = db.query(Course).filter(
                Course.parent_class_id == class_obj.id
            ).order_by(Course.order_index).all()
            
            if class_courses:
                course_ids = [c.id for c in class_courses]
                
                # Calculate progress percentage
                completed_count = db.query(CourseProgress).filter(
                    and_(
                        CourseProgress.user_id == user_id_int,
                        CourseProgress.course_id.in_(course_ids),
                        CourseProgress.is_completed == True
                    )
                ).count()
                
                progress_percent = (completed_count / len(course_ids)) * 100 if course_ids else 0.0
                
                # Check if class should be unlocked
                if i == 0:
                    # First class is always unlocked
                    unlocked = True
                else:
                    # Check if previous class has 80% completion
                    prev_class = classes[i - 1]
                    prev_class_courses = db.query(Course).filter(
                        Course.parent_class_id == prev_class.id
                    ).all()
                    
                    if prev_class_courses:
                        prev_course_ids = [c.id for c in prev_class_courses]
                        prev_completed_count = db.query(CourseProgress).filter(
                            and_(
                                CourseProgress.user_id == user_id_int,
                                CourseProgress.course_id.in_(prev_course_ids),
                                CourseProgress.is_completed == True
                            )
                        ).count()
                        
                        prev_completion_ratio = (prev_completed_count / len(prev_class_courses)) if prev_class_courses else 0.0
                        
                        # Unlock if previous class has 80%+ completion
                        unlocked = prev_completion_ratio >= 0.8
            else:
                # No courses in this class, unlock by default
                unlocked = i == 0
        else:
            # No user_id provided, only first class unlocked
            unlocked = i == 0
            progress_percent = 0.0
        
        class_data.append({
            "id": class_obj.id,
            "name": class_obj.name,
            "description": class_obj.description,
            "order_index": class_obj.order_index,
            "unlocked": unlocked,
            "progress_percent": progress_percent
        })
    
    return class_data

@router.get("/classes/{class_id}/courses")
async def get_class_courses(
    class_id: int,
    user_id: str = "1",
    include_levels: bool = False,
    db: Session = Depends(get_db),
):
    """Return courses for a class in one response.

    Progress is read from stored CourseProgress rows (updated on submit).
    Set include_levels=true to attach levels for every course in the same request
    instead of N follow-up /courses/{id}/levels calls.
    """
    courses = (
        db.query(Course)
        .filter(Course.parent_class_id == class_id)
        .order_by(Course.order_index)
        .all()
    )
    if not courses:
        return []

    user_id_int = int(user_id)
    course_ids = [course.id for course in courses]
    progress_rows = (
        db.query(CourseProgress)
        .filter(
            CourseProgress.user_id == user_id_int,
            CourseProgress.course_id.in_(course_ids),
        )
        .all()
    )
    progress_by_course = {row.course_id: row for row in progress_rows}

    created = False
    for course in courses:
        if course.id not in progress_by_course:
            progress = CourseProgress(
                user_id=user_id_int,
                course_id=course.id,
                is_unlocked=(course.order_index == 1),
            )
            db.add(progress)
            progress_by_course[course.id] = progress
            created = True
    if created:
        db.commit()

    levels_by_course = {}
    if include_levels:
        levels = (
            db.query(Level)
            .filter(Level.course_id.in_(course_ids))
            .order_by(Level.course_id, Level.order_index)
            .all()
        )
        for level in levels:
            levels_by_course.setdefault(level.course_id, []).append({
                "id": level.id,
                "course_id": level.course_id,
                "name": level.name,
                "description": level.description,
                "order_index": level.order_index,
                "required_score": level.required_score,
                "enabled": level.enabled,
            })

    course_data = []
    for course in courses:
        course_progress = progress_by_course.get(course.id)
        item = {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "order_index": course.order_index,
            "category": course.category.value if hasattr(course.category, "value") else course.category,
            "required_score": course.required_score,
            "enabled": course_progress.is_unlocked if course_progress else False,
            "parent_class_id": course.parent_class_id,
            "progress": {
                "accuracy_percentage": course_progress.accuracy_percentage if course_progress else 0.0,
                "is_completed": course_progress.is_completed if course_progress else False,
                "total_points": course_progress.total_points if course_progress else 0,
                "completed_exercises": course_progress.completed_exercises if course_progress else 0,
                "total_exercises": course_progress.total_exercises if course_progress else 0,
            },
        }
        if include_levels:
            item["levels"] = levels_by_course.get(course.id, [])
        course_data.append(item)

    return course_data


