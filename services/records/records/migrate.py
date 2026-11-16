"""Our own migration runner: applies numbered .sql files once each, in order.

migrations/001_init.sql, 002_..., are never edited once applied; a fix is a new file.
Each applied file name is stored in schema_migrations, so a second start applies nothing.
"""
import logging
import os
import re

log = logging.getLogger(__name__)

FILE_NAME = re.compile(r"^\d{3}_[a-z0-9_]+\.sql$")
# Like sqlcmd: a line containing only GO ends a batch. Needed when one statement
# must run before the next is compiled, e.g. ADD a column, then UPDATE it.
BATCH_SEPARATOR = re.compile(r"^\s*GO\s*$", re.IGNORECASE | re.MULTILINE)

CREATE_TRACKING_TABLE = """
IF OBJECT_ID('schema_migrations') IS NULL
    CREATE TABLE schema_migrations (
        version NVARCHAR(255) NOT NULL PRIMARY KEY,
        applied_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    )
"""


def find_migrations(folder):
    """The migration file names in the order they must run."""
    names = sorted(name for name in os.listdir(folder) if name.endswith(".sql"))
    for name in names:
        if not FILE_NAME.match(name):
            raise ValueError(f"migration {name} must be named like 001_add_column.sql")
    numbers = [name[:3] for name in names]
    if len(set(numbers)) != len(numbers):
        raise ValueError("two migrations share the same number")
    return names


def split_batches(sql):
    """Split a migration file on GO lines into the batches to send one by one."""
    return [batch.strip() for batch in BATCH_SEPARATOR.split(sql) if batch.strip()]


def apply_migrations(conn, folder):
    """Apply every migration not yet recorded, each in its own transaction.

    Returns the names applied now. If a migration fails, its changes are rolled
    back, it is not recorded, and the error stops startup.
    """
    cur = conn.cursor()
    cur.execute(CREATE_TRACKING_TABLE)
    conn.commit()
    cur.execute("SELECT version FROM schema_migrations")
    already_applied = {row["version"] for row in cur.fetchall()}

    applied_now = []
    for name in find_migrations(folder):
        if name in already_applied:
            continue
        log.info("applying migration %s", name)
        with open(os.path.join(folder, name)) as f:
            batches = split_batches(f.read())
        try:
            for batch in batches:
                cur.execute(batch)
            cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (name,))
            conn.commit()  # the schema change and its record are saved together
        except Exception:
            conn.rollback()
            log.error("migration %s failed and was rolled back", name)
            raise
        applied_now.append(name)

    log.info("migrations up to date: %d applied now, %d already applied",
             len(applied_now), len(already_applied))
    return applied_now
