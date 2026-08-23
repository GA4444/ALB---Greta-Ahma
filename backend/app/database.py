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


