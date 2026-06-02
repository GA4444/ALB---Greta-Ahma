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

SQLite does not enforce foreign keys, so the local data contains some orphaned
references. PostgreSQL does enforce them, so during the copy:
  * an orphaned NULLABLE foreign key is set to NULL,
  * a row whose REQUIRED foreign key points at a missing parent is skipped.
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

# (column, parent table, nullable) for every foreign key we must validate.
# user_id columns that are plain strings (attempts, progress) are NOT real FKs.
FK_RULES = {
    models.Course: [("parent_class_id", "courses", True)],
    models.Level: [("course_id", "courses", False)],
    models.Exercise: [("course_id", "courses", False), ("level_id", "levels", False)],
    models.CorpusDocument: [("class_id", "courses", True)],
    models.DailyChallenge: [("level_id", "levels", True)],
    models.Attempt: [("exercise_id", "exercises", False)],
    models.Progress: [("course_id", "courses", False), ("level_id", "levels", False)],
    models.CourseProgress: [("user_id", "users", False), ("course_id", "courses", False)],
    models.UserAchievement: [("user_id", "users", False), ("achievement_id", "achievements", False)],
    models.UserDailyProgress: [("user_id", "users", False), ("challenge_id", "daily_challenges", False)],
    models.SpacedRepetitionCard: [("user_id", "users", False), ("exercise_id", "exercises", False)],
    models.ChatSession: [("user_id", "users", True)],
    models.ChatMessage: [("session_id", "chat_sessions", False)],
}


def _copy_table(model, src, tgt, inserted):
    table = model.__tablename__
    cols = [c.key for c in sa_inspect(model).mapper.column_attrs]
    rules = FK_RULES.get(model, [])
    rows = src.query(model).all()

    ids_ok = set()
    skipped = 0
    deferred_parent = {}  # course id -> parent_class_id (set after insert)

    for row in rows:
        data = {c: getattr(row, c) for c in cols}
        skip = False
        for col, parent, nullable in rules:
            val = data.get(col)
            if val is None:
                continue
            # Self-referential courses: insert without parent, link afterwards.
            if model is models.Course and col == "parent_class_id":
                deferred_parent[data.get("id")] = val
                data[col] = None
                continue
            if val not in inserted.get(parent, set()):
                if nullable:
                    data[col] = None
                else:
                    skip = True
                    break
        if skip:
            skipped += 1
            continue
        tgt.add(model(**data))
        ids_ok.add(data.get("id"))

    tgt.commit()
    inserted[table] = ids_ok

    if model is models.Course and deferred_parent:
        for child_id, parent_id in deferred_parent.items():
            if child_id in ids_ok and parent_id in ids_ok:
                tgt.query(model).filter(model.id == child_id).update(
                    {"parent_class_id": parent_id}
                )
        tgt.commit()

    return len(ids_ok), skipped


def main():
    src_engine = create_engine(SOURCE_URL)
    tgt_engine = create_engine(TARGET_URL)

    Base.metadata.create_all(bind=tgt_engine)

    SrcSession = sessionmaker(bind=src_engine)
    TgtSession = sessionmaker(bind=tgt_engine, autoflush=False)
    src = SrcSession()
    tgt = TgtSession()

    print("Clearing target tables...")
    for model in reversed(MIGRATION_ORDER):
        deleted = tgt.query(model).delete()
        print(f"  cleared {model.__tablename__}: {deleted}")
    tgt.commit()

    print("Copying data...")
    inserted = {}
    for model in MIGRATION_ORDER:
        count, skipped = _copy_table(model, src, tgt, inserted)
        note = f" (skipped {skipped} orphaned)" if skipped else ""
        print(f"  {model.__tablename__}: {count}{note}")

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
