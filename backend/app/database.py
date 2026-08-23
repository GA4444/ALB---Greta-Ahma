import logging
import os
from typing import Optional, Tuple
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base


load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Render.com provides postgres:// but SQLAlchemy 2.x requires postgresql://
if DATABASE_URL.startswith("postgres://"):
	DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def _engine_kwargs(url: str) -> dict:
	kwargs = {
		"echo": False,
		"future": True,
		"pool_pre_ping": True,
	}
	if url.startswith("sqlite"):
		kwargs["connect_args"] = {"check_same_thread": False}
		return kwargs

	kwargs["pool_recycle"] = 300
	kwargs["pool_timeout"] = 10
	connect_args = {"connect_timeout": 10}
	if "sslmode=" not in url:
		connect_args["sslmode"] = "require"
	kwargs["connect_args"] = connect_args
	return kwargs


engine = create_engine(DATABASE_URL, **_engine_kwargs(DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def database_dialect() -> str:
	if DATABASE_URL.startswith("sqlite"):
		return "sqlite"
	if DATABASE_URL.startswith("postgresql"):
		return "postgresql"
	return "other"


def database_host() -> str:
	parsed = urlparse(DATABASE_URL)
	return parsed.hostname or "local"


def check_database() -> Tuple[bool, Optional[str]]:
	try:
		with engine.connect() as connection:
			connection.execute(text("SELECT 1"))
		return True, None
	except Exception as exc:
		logger.warning("Database readiness check failed: %s", exc)
		return False, str(exc)[:240]


def init_database() -> None:
	"""Create missing tables and apply lightweight migrations.

	Must stay off the import path so Gunicorn can bind and serve /health
	even when Render Postgres is asleep or unreachable.
	"""
	ok, error = check_database()
	if not ok:
		raise RuntimeError(error or "Database is not reachable")

	from . import models  # noqa: F401  — register metadata
	from .email_migrations import migrate_email_notification_schema

	try:
		Base.metadata.create_all(bind=engine)
	except Exception:
		logger.exception("create_all failed; continuing if the database already answers queries")

	try:
		migrate_email_notification_schema(engine)
	except Exception:
		logger.exception("Email schema migration failed")

	ok, error = check_database()
	if not ok:
		raise RuntimeError(error or "Database became unreachable after schema setup")


def get_db():
	from sqlalchemy.orm import Session
	db: Session = SessionLocal()
	try:
		yield db
	finally:
		db.close()


