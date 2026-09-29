import os

import pytest

from gymlog import create_app


@pytest.fixture
def app(tmp_path):
    """An app that uses a brand-new database in a temp folder for each test."""
    data_dir = str(tmp_path)
    return create_app({"DATA_DIR": data_dir, "DB_PATH": os.path.join(data_dir, "test.db")})


@pytest.fixture
def client(app):
    """Sends fake HTTP requests to the app without starting a server."""
    return app.test_client()
