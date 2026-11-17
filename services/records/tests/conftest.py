import pytest
import requests

from records import create_app

from .db_fixtures import database_url, empty_tables  # noqa: F401  (pytest fixture)


@pytest.fixture
def app(database_url):  # noqa: F811
    """The app on the test database. Migrations run here (only the first time do anything)."""
    app = create_app({
        "DATABASE_URL": database_url,
        "WORKOUTS_URL": "http://workouts.test",
        "WORKOUTS_TIMEOUT_S": 2,
    })
    yield app
    empty_tables(database_url, ["goals"])


@pytest.fixture
def client(app):
    """Sends fake HTTP requests to the app without starting a server."""
    return app.test_client()


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


class FakeWorkouts:
    """Stands in for the workouts service, so these tests need no second process.

    `sets` maps an exercise name to the sets workouts would return. Set `error`
    to an exception to simulate workouts being down, or `status_code` to 500.
    """

    def __init__(self):
        self.sets = {}
        self.error = None
        self.status_code = 200
        self.calls = []  # (url, timeout) of every request records made

    def get(self, url, timeout=None):
        self.calls.append((url, timeout))
        if self.error is not None:
            raise self.error
        if self.status_code != 200:
            return FakeResponse(self.status_code, {"error": "boom"})
        name = requests.utils.unquote(url.split("/exercises/")[1].removesuffix("/sets"))
        return FakeResponse(200, {"exercise": name, "sets": self.sets.get(name, [])})


@pytest.fixture
def workouts(monkeypatch):
    """Replace the real requests.get used by workouts_client with the fake above."""
    fake = FakeWorkouts()
    monkeypatch.setattr("records.workouts_client.requests.get", fake.get)
    return fake
