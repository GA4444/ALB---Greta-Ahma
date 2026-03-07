from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Enum, UniqueConstraint, DateTime, Float
from sqlalchemy.orm import relationship, backref
from .database import Base
import enum
from datetime import datetime


class CorpusGenre(str, enum.Enum):
	SHKENCOR = "shkencor"
	LETRAR = "letrar"
	JURIDIK = "juridik"
	PUBLICISTIK = "publicistik"
	ADMINISTRATIV = "administrativ"
	DIDAKTIK = "didaktik"
	TJETER = "tjeter"

class CorpusDialect(str, enum.Enum):
	GEGE = "gege"
	TOSKE = "toske"
	STANDARDE = "standarde"

class CorpusSource(str, enum.Enum):
	MEDIA = "media"
	LIBRA = "libra"
	DOKUMENTE_ZYRTARE = "dokumente_zyrtare"
	AKADEMIK = "akademik"
	PLATFORMA = "platforma"
	TJETER = "tjeter"

class CorpusProcessingStatus(str, enum.Enum):
	PENDING = "pending"
	TOKENIZED = "tokenized"
	LEMMATIZED = "lemmatized"
	ANNOTATED = "annotated"
	VALIDATED = "validated"
	ERROR = "error"


class CategoryEnum(str, enum.Enum):
	LISTEN_WRITE = "listen_write"  # Diktim (Audio → shkruaj)
	WORD_FROM_DESCRIPTION = "word_from_description"  # Fjala nga përshkrimi
	SYNONYMS_ANTONYMS = "synonyms_antonyms"  # Sinonime & Antonime
	ALBANIAN_OR_LOANWORD = "albanian_or_loanword"  # Shqipe apo Huazim?
	MISSING_LETTER = "missing_letter"  # Shkronja që mungon
	WRONG_LETTER = "wrong_letter"  # Shkronja e gabuar
	BUILD_WORD = "build_word"  # Ndërto fjalën
	NUMBER_TO_WORD = "number_to_word"  # Numri me fjalë
	PHRASES = "phrases"  # Shprehje (frazeologjike)
	SPELLING_PUNCTUATION = "spelling_punctuation"  # Drejtshkrim & Pikësim
	ABSTRACT_CONCRETE = "abstract_concrete"  # Abstrakte vs Konkrete
	BUILD_SENTENCE = "build_sentence"  # Ndërto fjalinë
	VOCABULARY = "vocabulary"  # Legacy category
	SPELLING = "spelling"  # Legacy category
	GRAMMAR = "grammar"  # Legacy category
	NUMBERS = "numbers"  # Legacy category
	PUNCTUATION = "punctuation"  # Legacy category


class Course(Base):
	__tablename__ = "courses"
	
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String(100), nullable=False)
	description = Column(Text, nullable=True)
	order_index = Column(Integer, default=0, nullable=False)
	category = Column(Enum(CategoryEnum), index=True, nullable=False)
	required_score = Column(Integer, default=80, nullable=False)  # percentage to unlock
	enabled = Column(Boolean, default=True)
	parent_class_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # For class hierarchy
	
	# Relationships
	levels = relationship("Level", back_populates="course", order_by="Level.order_index")
	exercises = relationship("Exercise", back_populates="course")
	sub_courses = relationship("Course", backref=backref("parent_class", remote_side=[id]))  # Courses within a class


class Level(Base):
	__tablename__ = "levels"
	
	id = Column(Integer, primary_key=True, index=True)
	course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
	name = Column(String(100), nullable=False)
	description = Column(Text, nullable=True)
	order_index = Column(Integer, default=0, nullable=False)
	required_score = Column(Integer, default=80, nullable=False)  # percentage to unlock
	enabled = Column(Boolean, default=True)
	
	# Relationships
	course = relationship("Course", back_populates="levels")
	exercises = relationship("Exercise", back_populates="level")


class Exercise(Base):
	__tablename__ = "exercises"

	id = Column(Integer, primary_key=True, index=True)
	category = Column(Enum(CategoryEnum), index=True, nullable=False)
	course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
	level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)
	prompt = Column(Text, nullable=False)
	# JSON-encoded string for choice lists or structured data when needed
	data = Column(Text, nullable=True)
	# expected answer text (or JSON-serialized for multi-answers)
	answer = Column(Text, nullable=False)
	points = Column(Integer, default=1, nullable=False)
	enabled = Column(Boolean, default=True)
	order_index = Column(Integer, default=0, nullable=False)

	# Rule-specific field (optional): e.g., pass threshold, max_errors
	rule = Column(String(50), nullable=True)

	# Relationships
	course = relationship("Course", back_populates="exercises")
	level = relationship("Level", back_populates="exercises")
	attempts = relationship("Attempt", back_populates="exercise")


class Attempt(Base):
	__tablename__ = "attempts"

	id = Column(Integer, primary_key=True, index=True)
	exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
	user_id = Column(String(64), index=True, nullable=False)
	response = Column(Text, nullable=False)
	is_correct = Column(Boolean, default=False)
	score_delta = Column(Integer, default=0)

	exercise = relationship("Exercise", back_populates="attempts")


class Progress(Base):
	__tablename__ = "progress"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(String(64), index=True, nullable=False)
	category = Column(Enum(CategoryEnum), index=True, nullable=False)
	course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
	level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)
	# aggregate points and error counts
	points = Column(Integer, default=0)
	errors = Column(Integer, default=0)
	stars = Column(Integer, default=0)
	completed = Column(Boolean, default=False)
	
	# Relationships
	course = relationship("Course")
	level = relationship("Level")


class CourseProgress(Base):
	__tablename__ = "course_progress"
	
	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
	course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
	total_exercises = Column(Integer, default=0)
	completed_exercises = Column(Integer, default=0)
	correct_answers = Column(Integer, default=0)
	total_points = Column(Integer, default=0)
	accuracy_percentage = Column(Float, default=0.0)
	is_completed = Column(Boolean, default=False)
	is_unlocked = Column(Boolean, default=False)
	completed_at = Column(DateTime, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	
	# Relationships
	user = relationship("User")
	course = relationship("Course")
	
	# Unique constraint to prevent duplicate progress records
	__table_args__ = (UniqueConstraint('user_id', 'course_id', name='unique_user_course_progress'),)


class User(Base):
	__tablename__ = "users"
	id = Column(Integer, primary_key=True, index=True)
	username = Column(String(50), unique=True, index=True, nullable=False)
	email = Column(String(100), unique=True, index=True, nullable=False)
	age = Column(Integer, nullable=True)
	date_of_birth = Column(DateTime, nullable=True)
	address = Column(String(255), nullable=True)
	phone_number = Column(String(20), nullable=True)
	# grade_level = Column(String(20), nullable=True)  # e.g., "Class 1", "Class 2" - REMOVED
	# learning_style = Column(String(50), nullable=True)  # e.g., "visual", "auditory", "kinesthetic" - REMOVED
	# preferred_difficulty = Column(String(20), default="normal")  # "easy", "normal", "hard" - REMOVED
	created_at = Column(DateTime, default=datetime.utcnow)
	last_login = Column(DateTime, nullable=True)
	is_active = Column(Boolean, default=True)
	is_admin = Column(Boolean, default=False, nullable=False)
	password_hash = Column(String(255), nullable=False)

	# Gamification fields
	current_streak = Column(Integer, default=0, nullable=False)
	longest_streak = Column(Integer, default=0, nullable=False)
	last_activity_date = Column(DateTime, nullable=True)
	total_achievements = Column(Integer, default=0, nullable=False)


class Achievement(Base):
	"""Achievements/Badges that users can earn"""
	__tablename__ = "achievements"
	
	id = Column(Integer, primary_key=True, index=True)
	code = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "first_perfect_score", "week_streak"
	name = Column(String(100), nullable=False)
	description = Column(Text, nullable=True)
	icon = Column(String(10), nullable=True)  # Emoji icon
	category = Column(String(50), nullable=True)  # "streak", "accuracy", "progress", "special"
	requirement_value = Column(Integer, nullable=True)  # e.g., 7 for "7-day streak"
	points_reward = Column(Integer, default=0, nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)


class UserAchievement(Base):
	"""Track which achievements users have earned"""
	__tablename__ = "user_achievements"
	
	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
	achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
	earned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	
	# Relationships
	user = relationship("User")
	achievement = relationship("Achievement")
	
	__table_args__ = (UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),)


class DailyChallenge(Base):
	"""Daily challenges for users"""
	__tablename__ = "daily_challenges"
	
	id = Column(Integer, primary_key=True, index=True)
	date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
	challenge_type = Column(String(50), nullable=False)  # "complete_n_exercises", "perfect_accuracy", "specific_level"
	target_value = Column(Integer, nullable=True)  # e.g., 10 for "complete 10 exercises"
	level_id = Column(Integer, ForeignKey("levels.id"), nullable=True)  # For level-specific challenges
	points_reward = Column(Integer, default=50, nullable=False)
	description = Column(Text, nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)
	
	# Relationships
	level = relationship("Level")


class UserDailyProgress(Base):
	"""Track user progress on daily challenges"""
	__tablename__ = "user_daily_progress"
	
	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
	challenge_id = Column(Integer, ForeignKey("daily_challenges.id"), nullable=False)
	current_value = Column(Integer, default=0, nullable=False)  # Current progress toward target
	completed = Column(Boolean, default=False, nullable=False)
	completed_at = Column(DateTime, nullable=True)
	
	# Relationships
	user = relationship("User")
	challenge = relationship("DailyChallenge")
	
	__table_args__ = (UniqueConstraint('user_id', 'challenge_id', name='unique_user_daily_challenge'),)


class SpacedRepetitionCard(Base):
	"""SRS cards for words/exercises the user struggles with"""
	__tablename__ = "srs_cards"
	
	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
	exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
	word = Column(String(200), nullable=False)  # The word being practiced
	
	# SRS algorithm fields (SM-2 inspired)
	ease_factor = Column(Float, default=2.5, nullable=False)  # How "easy" the card is (2.5 is default)
	interval_days = Column(Integer, default=1, nullable=False)  # Days until next review
	repetitions = Column(Integer, default=0, nullable=False)  # Number of successful repetitions
	
	# Scheduling
	next_review_date = Column(DateTime, nullable=False, index=True)
	last_reviewed_at = Column(DateTime, nullable=True)
	
	# Stats
	total_reviews = Column(Integer, default=0, nullable=False)
	correct_reviews = Column(Integer, default=0, nullable=False)
	
	created_at = Column(DateTime, default=datetime.utcnow)
	
	# Relationships
	user = relationship("User")
	exercise = relationship("Exercise")
	
	__table_args__ = (UniqueConstraint('user_id', 'exercise_id', name='unique_user_srs_card'),)


class ChatSession(Base):
	"""Chat sessions for AI Chatbot"""
	__tablename__ = "chat_sessions"
	
	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(String(50), ForeignKey("users.id"), nullable=True, index=True)  # Null for anonymous
	session_token = Column(String(100), unique=True, nullable=False, index=True)
	started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
	ended_at = Column(DateTime, nullable=True)
	is_active = Column(Boolean, default=True, nullable=False)
	
	# Session metadata
	total_messages = Column(Integer, default=0, nullable=False)
	user_satisfaction = Column(Integer, nullable=True)  # 1-5 rating
	
	# Relationships
	user = relationship("User")
	messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")


class ChatMessage(Base):
	"""Individual messages in chat sessions"""
	__tablename__ = "chat_messages"
	
	id = Column(Integer, primary_key=True, index=True)
	session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
	role = Column(String(20), nullable=False)  # 'user' or 'assistant'
	content = Column(Text, nullable=False)
	
	# LLM metadata
	model_used = Column(String(50), nullable=True)  # e.g., "gpt-4", "claude-3", "local"
	tokens_used = Column(Integer, nullable=True)
	response_time_ms = Column(Integer, nullable=True)
	
	# Context
	context_data = Column(Text, nullable=True)  # JSON-encoded context
	
	# Generated content
	suggested_questions = Column(Text, nullable=True)  # JSON array
	generated_exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=True)
	
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
	
	# Relationships
	session = relationship("ChatSession", back_populates="messages")
	generated_exercise = relationship("Exercise")


class CorpusDocument(Base):
	__tablename__ = "corpus_documents"

	id = Column(Integer, primary_key=True, index=True)
	title = Column(String(300), nullable=False, index=True)
	content = Column(Text, nullable=False)
	author = Column(String(200), nullable=True, index=True)
	year = Column(Integer, nullable=True, index=True)

	class_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)

	genre = Column(Enum(CorpusGenre), nullable=True, index=True)
	dialect = Column(Enum(CorpusDialect), nullable=True, index=True)
	source = Column(Enum(CorpusSource), nullable=True, index=True)
	fuse_class_code = Column(String(50), nullable=True, index=True)

	token_count = Column(Integer, default=0, nullable=False)
	lemma_count = Column(Integer, default=0, nullable=False)
	sentence_count = Column(Integer, default=0, nullable=False)
	avg_word_length = Column(Float, default=0.0, nullable=False)
	type_token_ratio = Column(Float, default=0.0, nullable=False)
	word_frequencies = Column(Text, nullable=True)  # JSON {word: count}

	processing_status = Column(Enum(CorpusProcessingStatus), default=CorpusProcessingStatus.PENDING, nullable=False, index=True)
	is_validated = Column(Boolean, default=False, nullable=False)
	validation_notes = Column(Text, nullable=True)
	content_hash = Column(String(64), nullable=True, index=True)

	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

	linked_class = relationship("Course", foreign_keys=[class_id])



