"""SQL Server access for this service: connection string, retries, one connection per request."""
import logging
import os
import time
from urllib.parse import unquote, urlparse

import pymssql
from flask import current_app, g

from .migrate import apply_migrations

log = logging.getLogger(__name__)

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations")


def parse_database_url(url):
    """Split mssql://user:password@host:port/database into pymssql.connect() arguments."""
    parts = urlparse(url or "")
    if parts.scheme != "mssql" or not parts.hostname or not parts.path.strip("/"):
        raise ValueError("DATABASE_URL must look like mssql://user:password@host:1433/database")
    return {
        "server": parts.hostname,
        "port": parts.port or 1433,
        # unquote so a password containing @ or / can be written as %40 or %2F
        "user": unquote(parts.username or ""),
        "password": unquote(parts.password or ""),
        "database": parts.path.strip("/"),
    }


def connect(url, attempts=10, first_delay_s=1.0, max_delay_s=10.0, sleep=time.sleep):
    """Open a connection, retrying with exponential backoff.

    Azure SQL serverless pauses when idle, and while it resumes every connection
    fails (error 40613) for up to about a minute. Waiting 1, 2, 4, 8, then 10 s
    between tries covers about 65 s before giving up.
    """
    args = parse_database_url(url)
    delay = first_delay_s
    for attempt in range(1, attempts + 1):
        try:
            # as_dict: rows come back as dicts, like sqlite3.Row did in Assignment 1
            return pymssql.connect(**args, as_dict=True, login_timeout=15, timeout=30)
        except pymssql.OperationalError as e:
            if attempt == attempts:
                raise
            log.warning("database not reachable (try %d of %d), retrying in %.0f s: %s",
                        attempt, attempts, delay, e)
            sleep(delay)
            delay = min(delay * 2, max_delay_s)


def get_db():
    """Return the connection for the current request, opening it if needed."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_URL"])
    return g.db


def close_db(exception=None):
    """Close the connection at the end of the request (Flask calls this for us)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=()):
    """Run a SELECT and return every row as a dict."""
    cur = get_db().cursor()
    cur.execute(sql, params)
    return cur.fetchall()


def query_one(sql, params=()):
    """Run a SELECT and return the first row as a dict, or None."""
    cur = get_db().cursor()
    cur.execute(sql, params)
    return cur.fetchone()


def database_is_usable(url):
    """True if this service's login can read and write its own database right now.

    Used by /health. Only one try, no retries: /health must answer quickly, and the
    caller (the CD pipeline, Azure) asks again by itself.
    """
    try:
        conn = connect(url, attempts=1)
    except pymssql.Error as e:
        log.warning("health: can't connect to the database: %s", e)
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM schema_migrations")  # read
        cur.execute("INSERT INTO schema_migrations (version) VALUES ('health-check')")  # write
        conn.rollback()  # undo the write, so the check leaves nothing behind
        return True
    except pymssql.Error as e:
        log.warning("health: can't read and write the database: %s", e)
        return False
    finally:
        conn.close()


def init_db(app):
    """Bring the schema up to date on startup by applying any new migrations."""
    conn = connect(app.config["DATABASE_URL"])
    try:
        apply_migrations(conn, MIGRATIONS_DIR)
    finally:
        conn.close()
    app.teardown_appcontext(close_db)
