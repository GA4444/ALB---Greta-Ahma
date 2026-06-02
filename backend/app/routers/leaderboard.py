from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, String, case
from typing import List
from ..database import get_db
from .. import models
from pydantic import BaseModel

router = APIRouter()

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    total_points: int
    total_correct: int
    total_attempts: int
    accuracy: float
    completed_courses: int
    level: int

    class Config:
        from_attributes = True

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db), limit: int = 0):
    """
    Get leaderboard with top users ranked by total points.
    OPTIMIZED: Uses a single query with subqueries instead of N+1 queries.
    limit=0 (default) -> returns all users; set a positive number to limit.
    """
    
    # Subquery for user statistics from attempts (total points, attempts, correct)
    attempts_stats = (
        db.query(
            models.Attempt.user_id,
            func.sum(case((models.Attempt.score_delta > 0, models.Attempt.score_delta), else_=0)).label('total_points'),
            func.count(models.Attempt.id).label('total_attempts'),
            func.sum(case((models.Attempt.is_correct == True, 1), else_=0)).label('total_correct')
        )
        .group_by(models.Attempt.user_id)
        .subquery()
    )
    
    # Subquery for completed courses
    completed_courses_subq = (
        db.query(
            models.CourseProgress.user_id,
            func.count(models.CourseProgress.id).label('completed_courses')
        )
        .filter(models.CourseProgress.is_completed == True)
        .group_by(models.CourseProgress.user_id)
        .subquery()
    )
    
    # Main query: Join users with their stats
    leaderboard_query = (
        db.query(
            models.User.id.label('user_id'),
            models.User.username,
            func.coalesce(attempts_stats.c.total_points, 0).label('total_points'),
            func.coalesce(attempts_stats.c.total_attempts, 0).label('total_attempts'),
            func.coalesce(attempts_stats.c.total_correct, 0).label('total_correct'),
            func.coalesce(completed_courses_subq.c.completed_courses, 0).label('completed_courses')
        )
        # Attempt.user_id is a String column, so cast User.id to string for that join.
        .outerjoin(attempts_stats, cast(models.User.id, String) == attempts_stats.c.user_id)
        # CourseProgress.user_id is an Integer column, so join on integers directly
        # (casting to String breaks on PostgreSQL with an "operator does not exist" error).
        .outerjoin(completed_courses_subq, models.User.id == completed_courses_subq.c.user_id)
        .order_by(
            func.coalesce(attempts_stats.c.total_points, 0).desc(),
            (func.coalesce(attempts_stats.c.total_correct, 0) * 100.0 / func.nullif(func.coalesce(attempts_stats.c.total_attempts, 1), 0)).desc(),
            func.coalesce(completed_courses_subq.c.completed_courses, 0).desc()
        )
    )

    if limit and limit > 0:
        leaderboard_query = leaderboard_query.limit(limit)

    leaderboard_rows = leaderboard_query.all()
    
    # Build results
    result = []
    for idx, row in enumerate(leaderboard_rows, start=1):
        total_points = int(row.total_points)
        total_attempts = int(row.total_attempts)
        total_correct = int(row.total_correct)
        completed_courses = int(row.completed_courses)
        
        accuracy = (total_correct / total_attempts * 100) if total_attempts > 0 else 0.0
        level = (total_points // 100) + 1
        
        result.append(LeaderboardEntry(
            rank=idx,
            user_id=row.user_id,
            username=row.username,
            total_points=total_points,
            total_correct=total_correct,
            total_attempts=total_attempts,
            accuracy=round(accuracy, 1),
            completed_courses=completed_courses,
            level=level
        ))
    
    return result

@router.get("/leaderboard/{user_id}/rank")
def get_user_rank(user_id: int, db: Session = Depends(get_db)):
    """Get current user's rank in the leaderboard"""
    leaderboard = get_leaderboard(db=db, limit=1000)
    
    for entry in leaderboard:
        if entry.user_id == user_id:
            return {
                "rank": entry.rank,
                "total_users": len(leaderboard),
                "percentile": round((1 - (entry.rank - 1) / len(leaderboard)) * 100, 1) if leaderboard else 0
            }
    
    return {
        "rank": len(leaderboard) + 1,
        "total_users": len(leaderboard),
        "percentile": 0
    }

