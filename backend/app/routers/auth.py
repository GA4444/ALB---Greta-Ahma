from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from passlib.context import CryptContext
from datetime import datetime
from ..services.email_service import send_welcome_email

router = APIRouter()
# Use a modern, battle-tested password hashing scheme that doesn't have
# bcrypt's 72-byte limitation or platform-specific backend issues.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


@router.post("/register", response_model=schemas.AuthResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
	# Check if username already exists
	if db.query(models.User).filter(models.User.username == user_data.username).first():
		raise HTTPException(status_code=400, detail="Username already registered")
	
	# Check if email already exists
	if db.query(models.User).filter(models.User.email == user_data.email).first():
		raise HTTPException(status_code=400, detail="Email already registered")
	
	# Validate age
	if user_data.age and (user_data.age < 5 or user_data.age > 80):
		raise HTTPException(status_code=400, detail="Age must be between 5 and 80")
	
	# Hash password
	hashed_password = pwd_context.hash(user_data.password)
	
	# Create user
	db_user = models.User(
		username=user_data.username,
		email=user_data.email,
		age=user_data.age,
		password_hash=hashed_password,
		created_at=datetime.utcnow()
	)
	
	db.add(db_user)
	db.commit()
	db.refresh(db_user)
	
	# Dërgo welcome email në thread të veçantë (nuk bllokojë HTTP response-in)
	if user_data.email:
		send_welcome_email(user_data.email, user_data.username, blocking=False)
	
	return schemas.AuthResponse(
		user_id=db_user.id,
		username=db_user.username,
		message="Registration successful! Please log in to continue.",
		is_admin=db_user.is_admin
	)


@router.post("/login", response_model=schemas.AuthResponse)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
	# Find user by username
	user = db.query(models.User).filter(models.User.username == user_data.username).first()
	
	if not user:
		raise HTTPException(status_code=401, detail="Invalid username or password")
	
	if not user.is_active:
		raise HTTPException(status_code=401, detail="Account is deactivated")
	
	# Verify password
	if not pwd_context.verify(user_data.password, user.password_hash):
		raise HTTPException(status_code=401, detail="Invalid username or password")
	
	# Update last login
	user.last_login = datetime.utcnow()
	db.commit()
	
	return schemas.AuthResponse(
		user_id=user.id,
		username=user.username,
		message="Login successful!",
		is_admin=user.is_admin
	)


@router.get("/user/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
	user = db.query(models.User).filter(models.User.id == user_id).first()
	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	return user


@router.put("/user/{user_id}/profile", response_model=schemas.UserOut)
def update_user_profile(
	user_id: int,
	user_update: schemas.UserUpdate,
	db: Session = Depends(get_db)
):
	user = db.query(models.User).filter(models.User.id == user_id).first()
	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	
	# Update email if provided and not already taken
	if user_update.email is not None:
		existing_user = db.query(models.User).filter(
			models.User.email == user_update.email,
			models.User.id != user_id
		).first()
		if existing_user:
			raise HTTPException(status_code=400, detail="Email already registered")
		user.email = user_update.email
	
	# Update other fields
	if user_update.age is not None:
		if user_update.age < 5 or user_update.age > 80:
			raise HTTPException(status_code=400, detail="Age must be between 5 and 80")
		user.age = user_update.age
	
	if user_update.date_of_birth is not None:
		user.date_of_birth = user_update.date_of_birth
	
	if user_update.address is not None:
		user.address = user_update.address
	
	if user_update.phone_number is not None:
		user.phone_number = user_update.phone_number
	
	db.commit()
	db.refresh(user)
	return user


@router.put("/user/{user_id}/preferences")
def update_user_preferences(
	user_id: int, 
	preferences: dict, 
	db: Session = Depends(get_db)
):
	user = db.query(models.User).filter(models.User.id == user_id).first()
	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	
	# Update allowed preferences
	if "learning_style" in preferences:
		valid_styles = ["visual", "auditory", "kinesthetic", "reading", "mixed"]
		if preferences["learning_style"] in valid_styles:
			user.learning_style = preferences["learning_style"]
	
	if "preferred_difficulty" in preferences:
		valid_difficulties = ["easy", "normal", "hard"]
		if preferences["preferred_difficulty"] in valid_difficulties:
			user.preferred_difficulty = preferences["preferred_difficulty"]
	
	db.commit()
	return {"message": "Preferences updated successfully"}


