import os
import sqlite3

from flask import current_app, g

# This service owns exactly one schema: the workouts tables.
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_db():
    """Return the SQLite connection for the current request, opening it if needed."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row  # rows behave like dicts: row["name"]
        g.db.execute("PRAGMA foreign_keys = ON")  # SQLite has them off by default
    return g.db


def close_db(exception=None):
    """Close the connection at the end of the request (Flask calls this for us)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create this service's tables on startup."""
    conn = sqlite3.connect(app.config["DB_PATH"])
    with open(SCHEMA_FILE) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

    app.teardown_appcontext(close_db)
