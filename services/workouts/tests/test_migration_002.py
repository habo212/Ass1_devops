"""Migration 002 (set_number): new sets are numbered, and existing sets are backfilled."""
import os
import shutil

import pymssql
import pytest

from workouts.db import MIGRATIONS_DIR, parse_database_url
from workouts.migrate import apply_migrations

from .db_fixtures import SERVER_URL

BACKFILL_DB = "workouts_backfill_test"


def test_new_sets_are_numbered_in_the_order_they_were_sent(client):
    body = {
        "date": "2026-11-20",
        "exercises": [{"name": "Squat", "sets": [
            {"reps": 5, "weight_kg": 100}, {"reps": 5, "weight_kg": 105}, {"reps": 3, "weight_kg": 110},
        ]}],
    }
    workout_id = client.post("/api/workouts", json=body).json["id"]
    sets = client.get(f"/api/workouts/{workout_id}").json["exercises"][0]["sets"]
    assert [(s["set_number"], s["weight_kg"]) for s in sets] == [(1, 100.0), (2, 105.0), (3, 110.0)]


@pytest.fixture
def db_with_only_001(tmp_path):
    """A fresh database where only migration 001 ran, like production before this change."""
    admin = pymssql.connect(**parse_database_url(SERVER_URL), autocommit=True)
    admin.cursor().execute(f"""
        IF DB_ID('{BACKFILL_DB}') IS NOT NULL
        BEGIN
            ALTER DATABASE {BACKFILL_DB} SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
            DROP DATABASE {BACKFILL_DB};
        END
        CREATE DATABASE {BACKFILL_DB};
    """)
    admin.close()
    shutil.copy(os.path.join(MIGRATIONS_DIR, "001_init.sql"), tmp_path)
    conn = pymssql.connect(**parse_database_url(SERVER_URL.rsplit("/", 1)[0] + "/" + BACKFILL_DB), as_dict=True)
    apply_migrations(conn, tmp_path)
    yield conn
    conn.close()


def test_002_backfills_existing_sets_per_exercise(db_with_only_001):
    conn = db_with_only_001
    cur = conn.cursor()
    cur.execute("INSERT INTO workouts (performed_on) VALUES ('2026-11-01')")
    cur.execute("INSERT INTO exercises (workout_id, name) VALUES (1, 'Squat'), (1, 'Bench Press')")
    # Interleaved on purpose: numbering must restart for each exercise, not follow the global id.
    cur.execute("""
        INSERT INTO sets (exercise_id, reps, weight_kg)
        VALUES (1, 5, 100), (2, 8, 60), (1, 5, 105), (2, 8, 62.5), (1, 3, 110)
    """)
    conn.commit()

    apply_migrations(conn, MIGRATIONS_DIR)  # 001 is skipped, 002 runs on existing data

    cur.execute("SELECT exercise_id, set_number, weight_kg FROM sets ORDER BY id")
    rows = [(r["exercise_id"], r["set_number"], r["weight_kg"]) for r in cur.fetchall()]
    assert rows == [(1, 1, 100.0), (2, 1, 60.0), (1, 2, 105.0), (2, 2, 62.5), (1, 3, 110.0)]
