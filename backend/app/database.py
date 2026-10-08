import logging
import os
import socket
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

_ORIGINAL_DATABASE_URL = DATABASE_URL

_RENDER_PG_SUFFIXES = (
	".oregon-postgres.render.com",
	".ohio-postgres.render.com",
	".frankfurt-postgres.render.com",
	".singapore-postgres.render.com",
	".virginia-postgres.render.com",
)


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


def _candidate_database_urls(url: str) -> list[str]:
	candidates = [url]
	host = urlparse(url).hostname or ""
	if host.startswith("dpg-") and "." not in host:
		for suffix in _RENDER_PG_SUFFIXES:
			candidates.append(url.replace(host, host + suffix, 1))
	# Preserve order while dropping duplicates.
	return list(dict.fromkeys(candidates))


def _host_resolves(host: str) -> bool:
	try:
		socket.getaddrinfo(host, 5432)
		return True
	except OSError:
		return False


def _bind_engine(url: str) -> None:
	global DATABASE_URL, engine
	DATABASE_URL = url
	engine = create_engine(url, **_engine_kwargs(url))
	SessionLocal.configure(bind=engine)


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
	last_error = None
	for url in _candidate_database_urls(_ORIGINAL_DATABASE_URL):
		host = urlparse(url).hostname or ""
		if host and not _host_resolves(host):
			last_error = f'could not resolve database host "{host}"'
			continue
		_bind_engine(url)
		ok, error = check_database()
		if ok:
			last_error = None
			break
		last_error = error
	if last_error:
		raise RuntimeError(last_error)

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

	try:
		from .exercise_hints import (
			backfill_exercise_hints,
			migrate_exercise_rule_column,
			replace_i_i_ri_with_i_ri,
			replace_i_trim_with_trim,
			strip_fjala_from_phrase_prompts,
			strip_sakte_from_spelling_prompts,
		)
		migrate_exercise_rule_column(engine)
		db = SessionLocal()
		try:
			# Keep startup migrations cheap — avoid long locks that cause proxy 503s.
			prompt_result = strip_sakte_from_spelling_prompts(db)
			logger.info("Spelling prompt «Saktë:» cleanup: %s", prompt_result)
			phrase_result = strip_fjala_from_phrase_prompts(db)
			logger.info("Phrase prompt «Fjala:» cleanup: %s", phrase_result)
			trim_result = replace_i_trim_with_trim(db)
			logger.info("Exercise wording «i trim» cleanup: %s", trim_result)
			ri_result = replace_i_i_ri_with_i_ri(db)
			logger.info("Exercise typo «i i ri» cleanup: %s", ri_result)
			result = backfill_exercise_hints(db)
			logger.info("Exercise hints backfill: %s", result)
			from .progress_repairs import repair_inflated_level_progress_points
			repair_result = repair_inflated_level_progress_points(db)
			logger.info("Progress points repair: %s", repair_result)
		finally:
			db.close()
	except Exception:
		logger.exception("Exercise hint migration/backfill failed")

	# Seed Klasa 9 in a separate short transaction after core migrations.
	try:
		from . import models
		db = SessionLocal()
		try:
			has_class_9 = (
				db.query(models.Course.id)
				.filter(
					models.Course.name == "Klasa 9",
					models.Course.parent_class_id.is_(None),
				)
				.first()
			)
			if not has_class_9:
				from .routers.seed_albanian_corpus import seed_ninth_class_exercises
				seed_ninth_class_exercises(db)
				logger.info("Seeded missing Klasa 9")
				from .exercise_hints import backfill_exercise_hints, strip_fjala_from_phrase_prompts
				strip_fjala_from_phrase_prompts(db)
				backfill_exercise_hints(db)
		finally:
			db.close()
	except Exception:
		logger.exception("Klasa 9 ensure/seed failed")

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


