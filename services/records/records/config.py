import os


def load_config():
    """Read all settings from environment variables, with defaults."""
    data_dir = os.environ.get("DATA_DIR", os.path.join(os.getcwd(), "data"))
    return {
        "DATA_DIR": data_dir,
        "DB_PATH": os.path.join(data_dir, "records.db"),
        # Where the workouts service lives. No trailing slash.
        "WORKOUTS_URL": os.environ.get("WORKOUTS_URL", "http://workouts:8000").rstrip("/"),
        # How long to wait for workouts before giving up, in seconds.
        "WORKOUTS_TIMEOUT_S": float(os.environ.get("WORKOUTS_TIMEOUT_S", "2")),
    }
