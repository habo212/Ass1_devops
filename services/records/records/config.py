import os


def load_config():
    """Read all settings from environment variables, with defaults."""
    return {
        # Secret, so no default: mssql://user:password@host:1433/database
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
        # The commit this build came from, shown by /health. The CD pipeline sets it.
        "GIT_SHA": os.environ.get("GIT_SHA", "dev"),
        # Where the workouts service lives. No trailing slash.
        "WORKOUTS_URL": os.environ.get("WORKOUTS_URL", "http://workouts:8000").rstrip("/"),
        # How long to wait for workouts before giving up, in seconds.
        "WORKOUTS_TIMEOUT_S": float(os.environ.get("WORKOUTS_TIMEOUT_S", "2")),
    }
