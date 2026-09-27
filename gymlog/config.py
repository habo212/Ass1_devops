import os


def load_config():
    """Read all settings from environment variables, with defaults."""
    data_dir = os.environ.get("DATA_DIR", os.path.join(os.getcwd(), "data"))
    return {
        "DATA_DIR": data_dir,
        "DB_PATH": os.path.join(data_dir, "gymlog.db"),
    }
