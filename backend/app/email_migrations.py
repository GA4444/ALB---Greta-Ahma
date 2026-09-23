"""Small idempotent schema migration for email notification data and user columns.

The project does not use Alembic yet, so this keeps existing SQLite and
PostgreSQL deployments compatible while ``create_all`` handles new tables.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def migrate_email_notification_schema(engine: Engine) -> None:
	inspector = inspect(engine)
	table_names = set(inspector.get_table_names())
	datetime_type = "TIMESTAMP" if engine.dialect.name == "postgresql" else "DATETIME"

	with engine.begin() as connection:
		if "users" in table_names:
			user_columns = {column["name"] for column in inspector.get_columns("users")}

			for name in ("last_streak_warning_at", "last_weekly_report_at"):
				if name not in user_columns:
					connection.execute(text(
						f"ALTER TABLE users ADD COLUMN {name} {datetime_type}"
					))
					logger.info("Added users.%s", name)
					user_columns.add(name)

			for name in ("first_name", "last_name"):
				if name not in user_columns:
					connection.execute(text(
						f"ALTER TABLE users ADD COLUMN {name} VARCHAR(80)"
					))
					logger.info("Added users.%s", name)
					user_columns.add(name)

			# Ensure streak columns exist (older DBs may predate gamification)
			for name, sql_type, default in (
				("current_streak", "INTEGER", "0"),
				("longest_streak", "INTEGER", "0"),
				("total_achievements", "INTEGER", "0"),
			):
				if name not in user_columns:
					connection.execute(text(
						f"ALTER TABLE users ADD COLUMN {name} {sql_type} DEFAULT {default}"
					))
					logger.info("Added users.%s", name)
					user_columns.add(name)

			if "last_activity_date" not in user_columns:
				connection.execute(text(
					f"ALTER TABLE users ADD COLUMN last_activity_date {datetime_type}"
				))
				logger.info("Added users.last_activity_date")
				user_columns.add("last_activity_date")

		if "attempts" in table_names:
			attempt_columns = {column["name"] for column in inspector.get_columns("attempts")}
			if "created_at" not in attempt_columns:
				connection.execute(text(
					f"ALTER TABLE attempts ADD COLUMN created_at {datetime_type}"
				))
				connection.execute(text(
					"UPDATE attempts SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
				))
				logger.info("Added attempts.created_at")
			if "duration_seconds" not in attempt_columns:
				connection.execute(text("ALTER TABLE attempts ADD COLUMN duration_seconds INTEGER"))
				logger.info("Added attempts.duration_seconds")
			connection.execute(text(
				"CREATE INDEX IF NOT EXISTS ix_attempts_created_at ON attempts (created_at)"
			))
