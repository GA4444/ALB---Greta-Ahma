#!/usr/bin/env python3
"""
One-shot data migration: local SQLite (dev.db) -> production PostgreSQL.

Usage:
    cd backend
    TARGET_DATABASE_URL="postgresql://USER:PASS@HOST:PORT/DBNAME" \
        venv/bin/python migrate_to_production.py

Get TARGET_DATABASE_URL from Render:
    Dashboard -> alblingo-db -> "Connections" -> "External Database URL".

The script wipes the target tables it manages and re-inserts every row from
dev.db, preserving primary keys, then fixes the PostgreSQL id sequences.
"""
import os
import sys

from sqlalchemy import create_engine, inspect as sa_inspect, text
from sqlalchemy.orm import sessionmaker

SOURCE_URL = os.environ.get("SOURCE_DATABASE_URL", "sqlite:///./dev.db")
TARGET_URL = os.environ.get("TARGET_DATABASE_URL")

if not TARGET_URL:
    print("ERROR: set TARGET_DATABASE_URL to the Render External Database URL.")
    sys.exit(1)

if TARGET_URL.startswith("postgres://"):
    TARGET_URL = TARGET_URL.replace("postgres://", "postgresql://", 1)

# Importing models registers them on Base.metadata.
from app import models  # noqa: E402
from app.database import Base  # noqa: E402

# Parents first; children reference earlier entries.
MIGRATION_ORDER = [
    models.Achievement,
    models.User,
    models.Course,
    models.Level,
    models.Exercise,
    models.CorpusDocument,
    models.DailyChallenge,
    models.Attempt,
    models.Progress,
    models.CourseProgress,
    models.UserAchievement,
    models.UserDailyProgress,
    models.SpacedRepetitionCard,
    models.ChatSession,
    models.ChatMessage,
]


def _row_order(model, rows):
    """Insert self-referential courses with parents before children."""
    if model is models.Course:
        return sorted(rows, key=lambda r: (r.parent_class_id is not None, r.id or 0))
    return rows


def main():
    src_engine = create_engine(SOURCE_URL)
    tgt_engine = create_engine(TARGET_URL)

    # Ensure the target schema exists (matches the deployed app).
    Base.metadata.create_all(bind=tgt_engine)

    SrcSession = sessionmaker(bind=src_engine)
    TgtSession = sessionmaker(bind=tgt_engine, autoflush=False)
    src = SrcSession()
    tgt = TgtSession()

    # Wipe managed tables (children first) so we can re-insert with real PKs.
    print("Clearing target tables...")
    for model in reversed(MIGRATION_ORDER):
        deleted = tgt.query(model).delete()
        print(f"  cleared {model.__tablename__}: {deleted}")
    tgt.commit()

    print("Copying data...")
    for model in MIGRATION_ORDER:
        cols = [c.key for c in sa_inspect(model).mapper.column_attrs]
        rows = src.query(model).all()
        for row in _row_order(model, rows):
            data = {c: getattr(row, c) for c in cols}
            tgt.add(model(**data))
        tgt.commit()
        print(f"  {model.__tablename__}: {len(rows)}")

    # Fix PostgreSQL id sequences after inserting explicit primary keys.
    if tgt_engine.dialect.name == "postgresql":
        print("Resetting id sequences...")
        with tgt_engine.connect() as conn:
            for model in MIGRATION_ORDER:
                table = model.__tablename__
                conn.execute(text(
                    "SELECT setval(pg_get_serial_sequence(:t, 'id'), "
                    "COALESCE((SELECT MAX(id) FROM " + table + "), 1))"
                ), {"t": table})
            conn.commit()

    src.close()
    tgt.close()
    print("Migration complete.")


if __name__ == "__main__":
    main()
