import pytest

from workouts import create_app

from .db_fixtures import database_url, empty_tables  # noqa: F401  (pytest fixture)


@pytest.fixture
def app(database_url):  # noqa: F811
    """The app on the test database. Migrations run here (only the first time do anything)."""
    app = create_app({"DATABASE_URL": database_url})
    yield app
    empty_tables(database_url, ["workouts"])  # cascades to exercises and sets


@pytest.fixture
def client(app):
    """Sends fake HTTP requests to the app without starting a server."""
    return app.test_client()
