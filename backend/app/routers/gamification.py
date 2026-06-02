from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, timedelta
from .. import models, schemas
from ..database import get_db
import random

router = APIRouter()


# ============================================================================
# ACHIEVEMENTS & BADGES
# ============================================================================

@router.get("/gamification/achievements")
def get_all_achievements(db: Session = Depends(get_db)):
	"""Get list of all possible achievements"""
	achievements = db.query(models.Achievement).all()
	return [
		{
			"id": a.id,
			"code": a.code,
			"name": a.name,
			"description": a.description,
			"icon": a.icon,
			"category": a.category,
			"requirement_value": a.requirement_value,
			"points_reward": a.points_reward,
		}
		for a in achievements
	]


@router.get("/gamification/achievements/{user_id}")
def get_user_achievements(user_id: str, db: Session = Depends(get_db)):
	"""Get achievements earned by a specific user"""
	user_achievements = (
		db.query(models.UserAchievement)
		.join(models.Achievement)
		.filter(models.UserAchievement.user_id == user_id)
		.all()
	)
	
	return {
		"total_achievements": len(user_achievements),
		"achievements": [
			{
				"id": ua.achievement.id,
				"code": ua.achievement.code,
				"name": ua.achievement.name,
				"description": ua.achievement.description,
				"icon": ua.achievement.icon,
				"category": ua.achievement.category,
				"earned_at": ua.earned_at.isoformat() if ua.earned_at else None,
				"points_reward": ua.achievement.points_reward,
			}
			for ua in user_achievements
		],
	}


def check_and_award_achievements(db: Session, user_id: str):
	"""
	Check if user has met criteria for any achievements and award them.
	This should be called after significant events (completing exercise, level, etc.)
	"""
	user = db.query(models.User).filter(models.User.id == user_id).first()
	if not user:
		return
	
	# Get all achievements the user hasn't earned yet
	earned_achievement_ids = {
		ua.achievement_id
		for ua in db.query(models.UserAchievement).filter(models.UserAchievement.user_id == user_id).all()
	}
	
	all_achievements = db.query(models.Achievement).all()
	newly_awarded = []
	
	for achievement in all_achievements:
		if achievement.id in earned_achievement_ids:
			continue  # Already earned
		
		# Check criteria based on achievement code
		should_award = False
		
		if achievement.code == "first_exercise":
			# Award for completing first exercise
			attempt_count = db.query(models.Attempt).filter(models.Attempt.user_id == user_id).count()
			should_award = attempt_count >= 1
		
		elif achievement.code == "perfect_level":
			# Award for completing a level with 100% accuracy
			attempts = (
				db.query(models.Attempt)
				.join(models.Exercise)
				.filter(models.Attempt.user_id == user_id)
				.all()
			)
			# Group by level and check if any level has 100% accuracy
			level_attempts = {}
			for att in attempts:
				exercise = db.get(models.Exercise, att.exercise_id)
				if exercise:
					level_id = exercise.level_id
					if level_id not in level_attempts:
						level_attempts[level_id] = {"correct": 0, "total": 0}
					level_attempts[level_id]["total"] += 1
					if att.is_correct:
						level_attempts[level_id]["correct"] += 1
			
			for level_stats in level_attempts.values():
				if level_stats["total"] >= 5 and level_stats["correct"] == level_stats["total"]:
					should_award = True
					break
		
		elif achievement.code.startswith("streak_"):
			# Streak achievements
			required_streak = achievement.requirement_value or 3
			should_award = user.current_streak >= required_streak
		
		elif achievement.code == "class_master":
			# Award for completing an entire class
			completed_courses = (
				db.query(models.CourseProgress)
				.filter(
					models.CourseProgress.user_id == user_id,
					models.CourseProgress.is_completed == True
				)
				.count()
			)
			should_award = completed_courses >= 10  # Assuming ~10 courses per class
		
		elif achievement.code == "speed_demon":
			# Award for completing 20+ exercises in one day
			today = datetime.utcnow().date()
			today_attempts = (
				db.query(models.Attempt)
				.filter(
					models.Attempt.user_id == user_id,
					func.date(models.Attempt.created_at) == today
				)
				.count()
			)
			should_award = today_attempts >= 20
		
		elif achievement.code == "accuracy_master":
			# Award for 95%+ overall accuracy with at least 50 attempts
			attempts = db.query(models.Attempt).filter(models.Attempt.user_id == user_id).all()
			if len(attempts) >= 50:
				correct = sum(1 for a in attempts if a.is_correct)
				accuracy = correct / len(attempts)
				should_award = accuracy >= 0.95
		
		# Award achievement if criteria met
		if should_award:
			user_achievement = models.UserAchievement(
				user_id=int(user_id),
				achievement_id=achievement.id
			)
			db.add(user_achievement)
			newly_awarded.append(achievement)
			
			# Update user total achievements
			user.total_achievements += 1
	
	if newly_awarded:
		db.commit()
	
	return newly_awarded


# ============================================================================
# STREAKS
# ============================================================================

@router.get("/gamification/streak/{user_id}")
def get_user_streak(user_id: str, db: Session = Depends(get_db)):
	"""Get user's current and longest streak"""
	user = db.query(models.User).filter(models.User.id == user_id).first()
	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	
	return {
		"current_streak": user.current_streak,
		"longest_streak": user.longest_streak,
		"last_activity_date": user.last_activity_date.isoformat() if user.last_activity_date else None,
	}


def update_user_streak(db: Session, user_id: str):
	"""Update user's streak after an activity. Call this after submitting an exercise."""
	user = db.query(models.User).filter(models.User.id == user_id).first()
	if not user:
		return
	
	today = datetime.utcnow().date()
	last_activity = user.last_activity_date.date() if user.last_activity_date else None
	
	if last_activity is None:
		# First activity ever
		user.current_streak = 1
		user.longest_streak = 1
	elif last_activity == today:
		# Already active today, no change
		pass
	elif last_activity == today - timedelta(days=1):
		# Active yesterday, increment streak
		user.current_streak += 1
		if user.current_streak > user.longest_streak:
			user.longest_streak = user.current_streak
	else:
		# Streak broken (missed one or more days)
		user.current_streak = 1
	
	user.last_activity_date = datetime.utcnow()
	db.commit()
	
	# Check for streak achievements
	check_and_award_achievements(db, user_id)


# ============================================================================
# DAILY CHALLENGES
# ============================================================================

@router.get("/gamification/daily-challenge")
def get_daily_challenge(user_id: Optional[str] = None, db: Session = Depends(get_db)):
	"""Get today's daily challenge"""
	today = datetime.utcnow().strftime("%Y-%m-%d")
	
	# Get or create today's challenge
	challenge = (
		db.query(models.DailyChallenge)
		.filter(models.DailyChallenge.date == today)
		.first()
	)
	
	if not challenge:
		# Generate a new daily challenge
		challenge = _generate_daily_challenge(db, today)
	
	result = {
		"id": challenge.id,
		"date": challenge.date,
		"challenge_type": challenge.challenge_type,
		"target_value": challenge.target_value,
		"description": challenge.description,
		"points_reward": challenge.points_reward,
		"level_id": challenge.level_id,
	}
	
	# If user_id provided, include their progress
	if user_id:
		progress = (
			db.query(models.UserDailyProgress)
			.filter(
				models.UserDailyProgress.user_id == user_id,
				models.UserDailyProgress.challenge_id == challenge.id
			)
			.first()
		)
		
		if progress:
			result["user_progress"] = {
				"current_value": progress.current_value,
				"completed": progress.completed,
				"completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
			}
		else:
			result["user_progress"] = {
				"current_value": 0,
				"completed": False,
				"completed_at": None,
			}
	
	return result


def _generate_daily_challenge(db: Session, date_str: str) -> models.DailyChallenge:
	"""Generate a new daily challenge for the given date"""
	challenge_types = [
		{
			"type": "complete_n_exercises",
			"target": 10,
			"description": "Përfundo 10 ushtrime sot për të fituar pikë bonus!",
			"points": 50,
		},
		{
			"type": "perfect_accuracy",
			"target": 5,
			"description": "Bëj 5 ushtrime pa asnjë gabim!",
			"points": 75,
		},
		{
			"type": "complete_n_exercises",
			"target": 20,
			"description": "Sfidë e madhe: përfundo 20 ushtrime sot!",
			"points": 100,
		},
	]
	
	# Randomly select a challenge type (can be made more sophisticated)
	selected = random.choice(challenge_types)
	
	challenge = models.DailyChallenge(
		date=date_str,
		challenge_type=selected["type"],
		target_value=selected["target"],
		description=selected["description"],
		points_reward=selected["points"],
	)
	
	db.add(challenge)
	db.commit()
	db.refresh(challenge)
	
	return challenge


def update_daily_challenge_progress(db: Session, user_id: str, challenge_type: str, increment: int = 1):
	"""Update user's progress on today's daily challenge"""
	today = datetime.utcnow().strftime("%Y-%m-%d")
	
	challenge = (
		db.query(models.DailyChallenge)
		.filter(
			models.DailyChallenge.date == today,
			models.DailyChallenge.challenge_type == challenge_type
		)
		.first()
	)
	
	if not challenge:
		return
	
	# Get or create user progress
	progress = (
		db.query(models.UserDailyProgress)
		.filter(
			models.UserDailyProgress.user_id == user_id,
			models.UserDailyProgress.challenge_id == challenge.id
		)
		.first()
	)
	
	if not progress:
		progress = models.UserDailyProgress(
			user_id=int(user_id),
			challenge_id=challenge.id,
			current_value=0
		)
		db.add(progress)
	
	if not progress.completed:
		progress.current_value += increment
		
		# Check if challenge is completed
		if progress.current_value >= challenge.target_value:
			progress.completed = True
			progress.completed_at = datetime.utcnow()
			
			# Award points to user (add to Progress)
			user_progress = (
				db.query(models.Progress)
				.filter(models.Progress.user_id == user_id)
				.first()
			)
			if user_progress:
				user_progress.points += challenge.points_reward
		
		db.commit()


# ============================================================================
# SPACED REPETITION SYSTEM (SRS)
# ============================================================================

@router.get("/gamification/srs/due/{user_id}")
def get_due_srs_cards(user_id: str, limit: int = 10, db: Session = Depends(get_db)):
	"""Get SRS cards due for review"""
	now = datetime.utcnow()
	
	due_cards = (
		db.query(models.SpacedRepetitionCard)
		.filter(
			models.SpacedRepetitionCard.user_id == user_id,
			models.SpacedRepetitionCard.next_review_date <= now
		)
		.order_by(models.SpacedRepetitionCard.next_review_date.asc())
		.limit(limit)
		.all()
	)
	
	return {
		"due_count": len(due_cards),
		"cards": [
			{
				"id": card.id,
				"exercise_id": card.exercise_id,
				"word": card.word,
				"next_review_date": card.next_review_date.isoformat(),
				"ease_factor": card.ease_factor,
				"interval_days": card.interval_days,
				"total_reviews": card.total_reviews,
				"correct_reviews": card.correct_reviews,
			}
			for card in due_cards
		],
	}


@router.post("/gamification/srs/review")
def review_srs_card(
	card_id: int,
	quality: int,  # 0-5 rating (0=total blackout, 5=perfect)
	db: Session = Depends(get_db)
):
	"""
	Review an SRS card and update scheduling using SM-2 algorithm.
	Quality scale: 0=complete fail, 1=incorrect but recognized, 2=incorrect easy recall,
	               3=correct with difficulty, 4=correct after hesitation, 5=perfect recall
	"""
	card = db.get(models.SpacedRepetitionCard, card_id)
	if not card:
		raise HTTPException(status_code=404, detail="SRS card not found")
	
	# Update stats
	card.total_reviews += 1
	card.last_reviewed_at = datetime.utcnow()
	
	if quality >= 3:
		card.correct_reviews += 1
	
	# SM-2 Algorithm
	if quality >= 3:
		# Correct response
		if card.repetitions == 0:
			card.interval_days = 1
		elif card.repetitions == 1:
			card.interval_days = 6
		else:
			card.interval_days = int(card.interval_days * card.ease_factor)
		
		card.repetitions += 1
	else:
		# Incorrect response - reset repetitions
		card.repetitions = 0
		card.interval_days = 1
	
	# Update ease factor
	card.ease_factor = max(
		1.3,
		card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
	)
	
	# Schedule next review
	card.next_review_date = datetime.utcnow() + timedelta(days=card.interval_days)
	
	db.commit()
	db.refresh(card)
	
	return {
		"card_id": card.id,
		"next_review_date": card.next_review_date.isoformat(),
		"interval_days": card.interval_days,
		"ease_factor": card.ease_factor,
		"repetitions": card.repetitions,
	}


def create_srs_card_for_mistake(db: Session, user_id: str, exercise_id: int):
	"""Create an SRS card when user makes a mistake on an exercise"""
	exercise = db.get(models.Exercise, exercise_id)
	if not exercise:
		return
	
	# Check if card already exists
	existing = (
		db.query(models.SpacedRepetitionCard)
		.filter(
			models.SpacedRepetitionCard.user_id == user_id,
			models.SpacedRepetitionCard.exercise_id == exercise_id
		)
		.first()
	)
	
	if existing:
		return existing
	
	# Create new card
	card = models.SpacedRepetitionCard(
		user_id=int(user_id),
		exercise_id=exercise_id,
		word=exercise.answer or exercise.prompt[:50],
		next_review_date=datetime.utcnow() + timedelta(hours=4),  # Review in 4 hours
	)
	
	db.add(card)
	db.commit()
	db.refresh(card)
	
	return card


@router.get("/gamification/srs/stats/{user_id}")
def get_srs_stats(user_id: str, db: Session = Depends(get_db)):
	"""Get SRS statistics for a user"""
	total_cards = (
		db.query(models.SpacedRepetitionCard)
		.filter(models.SpacedRepetitionCard.user_id == user_id)
		.count()
	)
	
	due_cards = (
		db.query(models.SpacedRepetitionCard)
		.filter(
			models.SpacedRepetitionCard.user_id == user_id,
			models.SpacedRepetitionCard.next_review_date <= datetime.utcnow()
		)
		.count()
	)
	
	cards = (
		db.query(models.SpacedRepetitionCard)
		.filter(models.SpacedRepetitionCard.user_id == user_id)
		.all()
	)
	
	total_reviews = sum(c.total_reviews for c in cards)
	correct_reviews = sum(c.correct_reviews for c in cards)
	
	return {
		"total_cards": total_cards,
		"due_cards": due_cards,
		"total_reviews": total_reviews,
		"correct_reviews": correct_reviews,
		"accuracy": (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0,
	}
