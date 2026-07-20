from typing import Optional, List, Literal
from pydantic import BaseModel
from .models import CategoryEnum
from datetime import datetime


class CourseOut(BaseModel):
	id: int
	name: str
	description: Optional[str]
	order_index: int
	category: CategoryEnum
	required_score: int
	enabled: bool
	parent_class_id: Optional[int]
	sub_courses: Optional[List['CourseOut']] = []

	class Config:
		from_attributes = True


class ClassOut(BaseModel):
	id: int
	name: str
	description: Optional[str]
	order_index: int
	enabled: bool
	courses: List[CourseOut]
	unlocked: bool
	completed: bool

	class Config:
		from_attributes = True


class LevelOut(BaseModel):
	id: int
	course_id: int
	name: str
	description: Optional[str] = None
	order_index: int
	required_score: int
	enabled: bool

	class Config:
		from_attributes = True


class ExerciseOut(BaseModel):
	id: int
	category: CategoryEnum
	course_id: int
	level_id: int
	prompt: str
	data: Optional[str] = None
	points: int
	rule: Optional[str] = None
	order_index: int

	class Config:
		from_attributes = True


class SubmitRequest(BaseModel):
	user_id: str
	response: str


class SubmitResult(BaseModel):
	exercise_id: int
	is_correct: bool
	score_delta: int
	new_points: int
	new_errors: int
	stars: int
	level_completed: bool
	course_completed: bool
	message: str
	correct_answer: Optional[str] = None


class PersonalizedPracticeExerciseOut(BaseModel):
	id: str
	prompt: str
	answer: str
	category: str
	hint: Optional[str] = None
	order_index: int


class PersonalizedPracticeRequest(BaseModel):
	user_id: str
	class_id: Optional[int]
	level_id: int


class PersonalizedPracticeResponse(BaseModel):
	exercises: List[PersonalizedPracticeExerciseOut]
	message: str


class AICoachRequest(BaseModel):
	user_id: str
	level_id: Optional[int] = None


class AICoachMistakePattern(BaseModel):
	type: str
	count: int
	examples: List[str] = []


class AICoachResponse(BaseModel):
	user_id: str
	level_id: Optional[int] = None
	total_attempts_analyzed: int
	incorrect_attempts_analyzed: int
	patterns: List[AICoachMistakePattern]
	micro_lessons: List[str]
	drill_plan: List[str]

class ProgressOut(BaseModel):
	category: CategoryEnum
	course_id: int
	level_id: int
	points: int
	errors: int
	stars: int
	completed: bool

	class Config:
		from_attributes = True


class CategoryStatusOut(BaseModel):
	category: CategoryEnum
	total_attempts: int
	correct_attempts: int
	accuracy: float
	can_advance: bool


class CourseProgressOut(BaseModel):
	course: CourseOut
	levels: List[LevelOut]
	progress: List[ProgressOut]
	unlocked: bool
	completed: bool
	overall_score: float

	class Config:
		from_attributes = True


class UserProgressOut(BaseModel):
	user_id: str
	total_points: int
	total_stars: int
	courses: List[CourseProgressOut]

	class Config:
		from_attributes = True


class UserCreate(BaseModel):
	username: str
	email: str
	age: Optional[int] = None
	password: str

class UserOut(BaseModel):
	id: int
	username: str
	email: str
	age: Optional[int]
	date_of_birth: Optional[datetime] = None
	address: Optional[str] = None
	phone_number: Optional[str] = None
	created_at: datetime
	last_login: Optional[datetime]
	is_active: bool
	is_admin: bool

class UserUpdate(BaseModel):
	email: Optional[str] = None
	age: Optional[int] = None
	date_of_birth: Optional[datetime] = None
	address: Optional[str] = None
	phone_number: Optional[str] = None

class UserLogin(BaseModel):
	username: str
	password: str

class AuthResponse(BaseModel):
	user_id: int
	username: str
	message: str
	is_admin: bool = False

class AdminUserCreate(BaseModel):
	username: str
	email: str
	password: str
	age: Optional[int] = None

class ExerciseCreate(BaseModel):
	category: CategoryEnum
	course_id: int
	level_id: int
	prompt: str
	data: Optional[str] = None
	answer: str
	points: int = 1
	rule: Optional[str] = None
	order_index: int = 0
	enabled: bool = True

class ExerciseUpdate(BaseModel):
	category: Optional[CategoryEnum] = None
	course_id: Optional[int] = None
	level_id: Optional[int] = None
	prompt: Optional[str] = None
	data: Optional[str] = None
	answer: Optional[str] = None
	points: Optional[int] = None
	rule: Optional[str] = None
	order_index: Optional[int] = None
	enabled: Optional[bool] = None

class LevelCreate(BaseModel):
	course_id: int
	name: str
	description: Optional[str] = None
	order_index: int = 0
	required_score: int = 80
	enabled: bool = True

class LevelUpdate(BaseModel):
	course_id: Optional[int] = None
	name: Optional[str] = None
	description: Optional[str] = None
	order_index: Optional[int] = None
	required_score: Optional[int] = None
	enabled: Optional[bool] = None

class ClassCreate(BaseModel):
	name: str
	description: Optional[str] = None
	order_index: int = 0
	enabled: bool = True

class ClassUpdate(BaseModel):
	name: Optional[str] = None
	description: Optional[str] = None
	order_index: Optional[int] = None
	enabled: Optional[bool] = None


class CourseProgressDetail(BaseModel):
	id: int
	user_id: int
	course_id: int
	total_exercises: int
	completed_exercises: int
	correct_answers: int
	total_points: int
	accuracy_percentage: float
	is_completed: bool
	is_unlocked: bool
	completed_at: Optional[datetime]
	course: CourseOut
	
	class Config:
		from_attributes = True


