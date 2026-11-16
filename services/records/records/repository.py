"""Records SQL. Only touches this service's own `goals` table."""
from .db import get_db, query_one


def get_goal(exercise_name):
    """The goal for one exercise as a dict, or None if none is set."""
    return query_one(
        "SELECT exercise_name, target_kg, CONVERT(char(10), set_on, 23) AS set_on "
        "FROM goals WHERE exercise_name = %s",
        (exercise_name,),
    )


def set_goal(exercise_name, target_kg, set_on):
    """Create the goal, or replace it if the exercise already has one.

    SQL Server has no ON CONFLICT, so: try to update, and insert if nothing was there.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE goals SET target_kg = %s, set_on = %s WHERE exercise_name = %s",
        (target_kg, set_on, exercise_name),
    )
    if cur.rowcount == 0:
        cur.execute(
            "INSERT INTO goals (exercise_name, target_kg, set_on) VALUES (%s, %s, %s)",
            (exercise_name, target_kg, set_on),
        )
    db.commit()


def delete_goal(exercise_name):
    """Remove a goal. Returns False if there wasn't one."""
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM goals WHERE exercise_name = %s", (exercise_name,))
    deleted = cur.rowcount > 0
    db.commit()
    return deleted
