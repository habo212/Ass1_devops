"""Workouts SQL. The only file in this domain that talks to the database."""
from ..db import get_db


def _insert_exercises(db, workout_id, exercises):
    """Insert each exercise and its sets for one workout."""
    for exercise in exercises:
        cur = db.execute(
            "INSERT INTO exercises (workout_id, name) VALUES (?, ?)",
            (workout_id, exercise["name"]),
        )
        exercise_id = cur.lastrowid
        for s in exercise["sets"]:
            db.execute(
                "INSERT INTO sets (exercise_id, reps, weight_kg) VALUES (?, ?, ?)",
                (exercise_id, s["reps"], s["weight_kg"]),
            )


def create_workout(workout):
    """Save a cleaned workout (from service.validate_workout) and return its id."""
    db = get_db()
    cur = db.execute(
        "INSERT INTO workouts (performed_on, notes) VALUES (?, ?)",
        (workout["performed_on"], workout["notes"]),
    )
    workout_id = cur.lastrowid
    _insert_exercises(db, workout_id, workout["exercises"])
    # Nothing is saved until commit, so a failure halfway saves nothing.
    db.commit()
    return workout_id


def list_workouts():
    """All workouts, newest first, without their exercises."""
    rows = get_db().execute(
        "SELECT id, performed_on, notes FROM workouts ORDER BY performed_on DESC, id DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def get_workout(workout_id):
    """One workout with its exercises and sets nested inside, or None if missing."""
    db = get_db()
    row = db.execute(
        "SELECT id, performed_on, notes FROM workouts WHERE id = ?", (workout_id,)
    ).fetchone()
    if row is None:
        return None

    workout = dict(row)
    workout["exercises"] = []
    exercise_rows = db.execute(
        "SELECT id, name FROM exercises WHERE workout_id = ? ORDER BY id", (workout_id,)
    ).fetchall()
    for exercise_row in exercise_rows:
        set_rows = db.execute(
            "SELECT id, reps, weight_kg FROM sets WHERE exercise_id = ? ORDER BY id",
            (exercise_row["id"],),
        ).fetchall()
        exercise = dict(exercise_row)
        exercise["sets"] = [dict(s) for s in set_rows]
        workout["exercises"].append(exercise)
    return workout


def update_workout(workout_id, workout):
    """Replace a workout's date, notes and all its exercises. Returns False if missing."""
    db = get_db()
    cur = db.execute(
        "UPDATE workouts SET performed_on = ?, notes = ? WHERE id = ?",
        (workout["performed_on"], workout["notes"], workout_id),
    )
    if cur.rowcount == 0:
        return False
    # ON DELETE CASCADE removes the old sets along with the old exercises.
    db.execute("DELETE FROM exercises WHERE workout_id = ?", (workout_id,))
    _insert_exercises(db, workout_id, workout["exercises"])
    db.commit()
    return True


def delete_workout(workout_id):
    """Delete a workout (its exercises and sets go with it). Returns False if missing."""
    db = get_db()
    cur = db.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
    db.commit()
    return cur.rowcount > 0


def get_sets_for_exercise(name):
    """Every set ever done for one exercise, oldest first. Used by the records domain."""
    rows = get_db().execute(
        """
        SELECT s.id AS set_id, w.performed_on, s.reps, s.weight_kg
        FROM sets s
        JOIN exercises e ON e.id = s.exercise_id
        JOIN workouts w ON w.id = e.workout_id
        WHERE e.name = ?
        ORDER BY w.performed_on, s.id
        """,
        (name,),
    ).fetchall()
    return [dict(row) for row in rows]
