"""Workouts SQL. The only file in this service that talks to the database.

SQL Server notes: placeholders are %s (pymssql), new ids come back with
OUTPUT INSERTED.id, and DATE columns are read with CONVERT(char(10), ..., 23)
so they leave as 'YYYY-MM-DD' text, the same as in Assignment 1.
"""
from .db import get_db, query, query_one


def _insert_exercises(cur, workout_id, exercises):
    """Insert each exercise and its sets for one workout."""
    for exercise in exercises:
        cur.execute(
            "INSERT INTO exercises (workout_id, name) OUTPUT INSERTED.id VALUES (%s, %s)",
            (workout_id, exercise["name"]),
        )
        exercise_id = cur.fetchone()["id"]
        for s in exercise["sets"]:
            cur.execute(
                "INSERT INTO sets (exercise_id, reps, weight_kg) VALUES (%s, %s, %s)",
                (exercise_id, s["reps"], s["weight_kg"]),
            )


def create_workout(workout):
    """Save a cleaned workout (from service.validate_workout) and return its id."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO workouts (performed_on, notes) OUTPUT INSERTED.id VALUES (%s, %s)",
        (workout["performed_on"], workout["notes"]),
    )
    workout_id = cur.fetchone()["id"]
    _insert_exercises(cur, workout_id, workout["exercises"])
    # Nothing is saved until commit, so a failure halfway saves nothing.
    db.commit()
    return workout_id


def list_workouts():
    """All workouts, newest first, without their exercises."""
    return query(
        "SELECT id, CONVERT(char(10), performed_on, 23) AS performed_on, notes "
        "FROM workouts ORDER BY performed_on DESC, id DESC"
    )


def list_exercise_names():
    """Every exercise name that has been logged, A to Z."""
    return [row["name"] for row in query("SELECT DISTINCT name FROM exercises ORDER BY name")]


def get_workout(workout_id):
    """One workout with its exercises and sets nested inside, or None if missing."""
    workout = query_one(
        "SELECT id, CONVERT(char(10), performed_on, 23) AS performed_on, notes "
        "FROM workouts WHERE id = %s",
        (workout_id,),
    )
    if workout is None:
        return None

    workout["exercises"] = query(
        "SELECT id, name FROM exercises WHERE workout_id = %s ORDER BY id", (workout_id,)
    )
    for exercise in workout["exercises"]:
        exercise["sets"] = query(
            "SELECT id, reps, weight_kg FROM sets WHERE exercise_id = %s ORDER BY id",
            (exercise["id"],),
        )
    return workout


def update_workout(workout_id, workout):
    """Replace a workout's date, notes and all its exercises. Returns False if missing."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE workouts SET performed_on = %s, notes = %s WHERE id = %s",
        (workout["performed_on"], workout["notes"], workout_id),
    )
    if cur.rowcount == 0:
        db.rollback()
        return False
    # ON DELETE CASCADE removes the old sets along with the old exercises.
    cur.execute("DELETE FROM exercises WHERE workout_id = %s", (workout_id,))
    _insert_exercises(cur, workout_id, workout["exercises"])
    db.commit()
    return True


def delete_workout(workout_id):
    """Delete a workout (its exercises and sets go with it). Returns False if missing."""
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM workouts WHERE id = %s", (workout_id,))
    deleted = cur.rowcount > 0
    db.commit()
    return deleted


def get_sets_for_exercise(name):
    """Every set ever done for one exercise, oldest first. Served to the records service over HTTP."""
    return query(
        """
        SELECT s.id AS set_id, CONVERT(char(10), w.performed_on, 23) AS performed_on,
               s.reps, s.weight_kg
        FROM sets s
        JOIN exercises e ON e.id = s.exercise_id
        JOIN workouts w ON w.id = e.workout_id
        WHERE e.name = %s
        ORDER BY w.performed_on, s.id
        """,
        (name,),
    )
