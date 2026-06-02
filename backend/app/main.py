import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import exercises, progress, seed, auth, ai, audio, course_progression, database_viewer, leaderboard, admin, ocr, gamification, chatbot, chatbot_advanced, ai_advanced_practice, corpus_admin


def create_app() -> FastAPI:
	app = FastAPI(title="AlbLingo - Albanian Language Learning Platform", version="1.0.0")

	allowed_origins = [
		"http://localhost:5173",
		"http://127.0.0.1:5173",
		"http://localhost:5174",
		"http://127.0.0.1:5174",
		"https://alblingo.vercel.app",
	]
	extra = os.getenv("CORS_ORIGINS", "")
	if extra:
		allowed_origins.extend([o.strip() for o in extra.split(",") if o.strip()])

	app.add_middleware(
		CORSMiddleware,
		allow_origins=allowed_origins,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	# Create tables if not exist
	Base.metadata.create_all(bind=engine)

	# Routers
	app.include_router(exercises.router, prefix="/api", tags=["exercises"])
	app.include_router(progress.router, prefix="/api", tags=["progress"])
	app.include_router(seed.router, prefix="/api", tags=["seed"])
	app.include_router(auth.router, prefix="/api", tags=["auth"])
	app.include_router(ai.router, prefix="/api", tags=["ai"])
	app.include_router(audio.router, prefix="/api", tags=["audio"])
	app.include_router(course_progression.router, prefix="/api", tags=["course-progression"])
	app.include_router(ocr.router, prefix="/api", tags=["ocr"])
	app.include_router(gamification.router, prefix="/api", tags=["gamification"])
	app.include_router(chatbot.router, prefix="/api", tags=["chatbot"])
	app.include_router(chatbot_advanced.router, prefix="/api", tags=["chatbot-advanced"])
	app.include_router(ai_advanced_practice.router, prefix="/api", tags=["ai-advanced-practice"])
	app.include_router(database_viewer.router, tags=["database-viewer"])
	app.include_router(leaderboard.router, prefix="/api", tags=["leaderboard"])
	app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
	app.include_router(corpus_admin.router, prefix="/api/admin", tags=["corpus-admin"])

	return app


app = create_app()

# Start background email scheduler if enabled
@app.on_event("startup")
def startup_event():
	enabled = os.getenv("ENABLE_BACKGROUND_TASKS", "false").lower() in ("true", "1", "yes")
	if enabled:
		try:
			from .background_tasks import start_background_tasks
			start_background_tasks()
		except Exception as e:
			print(f"[WARNING] Background tasks not started: {e}")

# Root endpoint
@app.get("/")
def read_root():
	return {"message": "Welcome to Shqipto API", "status": "running"}

# Health check endpoint
@app.get("/health")
def health_check():
	return {"status": "healthy", "timestamp": "2024-08-21T15:44:00Z"}


# ─────────────────────────────────────────────────────────
# Email status & test endpoints
# ─────────────────────────────────────────────────────────

from pydantic import BaseModel as _BaseModel
from dotenv import dotenv_values as _dotenv_values
from pathlib import Path as _Path

_ENV_PATH = _Path(__file__).resolve().parent.parent / ".env"


def _live_cfg(key: str, default: str = "") -> str:
	vals = _dotenv_values(_ENV_PATH)
	return vals.get(key) or os.getenv(key, default)


@app.get("/api/email-status")
def email_status():
	"""Tregon nëse sistemi i email-it është i konfiguruar siç duhet."""
	smtp_user = _live_cfg("SMTP_USER")
	smtp_pass = _live_cfg("SMTP_PASSWORD")
	configured = bool(smtp_user and smtp_pass)
	scheduler_running = False
	try:
		from .background_tasks import scheduler
		scheduler_running = getattr(scheduler, "running", False)
	except Exception:
		pass
	return {
		"smtp_configured": configured,
		"smtp_user": smtp_user if configured else "(nuk është vendosur)",
		"env_file_found": _ENV_PATH.exists(),
		"env_file_path": str(_ENV_PATH),
		"welcome_email_on_register": True,
		"background_scheduler_running": scheduler_running,
		"instructions": (
			"Hapni backend/.env dhe vendosni SMTP_USER dhe SMTP_PASSWORD (Gmail App Password)."
			if not configured else
			"Konfigurimi SMTP duket i saktë. Provoni POST /api/email/test për të dërguar email testues."
		),
	}


class _TestEmailBody(_BaseModel):
	to_email: str
	type: str = "welcome"   # "welcome" | "streak" | "weekly"
	username: str = "TestUser"


@app.post("/api/email/test")
def test_email(body: _TestEmailBody):
	"""
	Dërgo email testues pa pasur nevojë të regjistrohesh.
	Body: { "to_email": "...", "type": "welcome"|"streak"|"weekly", "username": "..." }
	"""
	from .services.email_service import (
		send_welcome_email,
		send_streak_warning_email,
		send_weekly_report_email,
	)
	from datetime import datetime, timedelta

	if body.type == "welcome":
		ok = send_welcome_email(body.to_email, body.username, blocking=True)
	elif body.type == "streak":
		ok = send_streak_warning_email(
			body.to_email, body.username,
			current_streak=7,
			last_login=datetime.utcnow() - timedelta(hours=22),
			blocking=True,
		)
	elif body.type == "weekly":
		ok = send_weekly_report_email(
			body.to_email, body.username,
			stats={
				"exercises_completed": 25, "avg_score": 82,
				"time_spent_minutes": 140, "current_streak": 7,
				"strengths": ["Drejtshkrim — 88%", "Lexim — 84%"],
				"weaknesses": ["Gramatikë — 66%"],
			},
			blocking=True,
		)
	else:
		return {"success": False, "detail": "type duhet të jetë: welcome, streak, ose weekly"}

	return {
		"success": ok,
		"to": body.to_email,
		"type": body.type,
		"message": "Email u dërgua me sukses! Kontrollo Inbox/Spam." if ok else
		           "Dërgimi dështoi. Shiko terminalin e backend-it për detaje.",
	}


