import os


def load_config():
    """Read all settings from environment variables, with defaults."""
    return {
        # Secret, so no default: mssql://user:password@host:1433/database
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
        # The commit this build came from, shown by /health. The CD pipeline sets it.
        "GIT_SHA": os.environ.get("GIT_SHA", "dev"),
    }
