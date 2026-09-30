"""Records SQL. Only touches the records domain's own `goals` table."""
from ..db import get_db


def get_goal(exercise_name):
    """The goal for one exercise as a dict, or None if none is set."""
    row = get_db().execute(
        "SELECT exercise_name, target_kg, set_on FROM goals WHERE exercise_name = ?",
        (exercise_name,),
    ).fetchone()
    return dict(row) if row else None


def set_goal(exercise_name, target_kg, set_on):
    """Create the goal, or replace it if the exercise already has one."""
    db = get_db()
    db.execute(
        """
        INSERT INTO goals (exercise_name, target_kg, set_on) VALUES (?, ?, ?)
        ON CONFLICT(exercise_name) DO UPDATE SET target_kg = excluded.target_kg,
                                                 set_on = excluded.set_on
        """,
        (exercise_name, target_kg, set_on),
    )
    db.commit()


def delete_goal(exercise_name):
    """Remove a goal. Returns False if there wasn't one."""
    db = get_db()
    cur = db.execute("DELETE FROM goals WHERE exercise_name = ?", (exercise_name,))
    db.commit()
    return cur.rowcount > 0
