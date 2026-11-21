"""Cross-seam integration test: the two real services, talking over HTTP.

Unlike the unit tests, nothing is faked here. A workout is written through the
workouts API, and the records API must compute PRs from it, which only works
if records really calls workouts (ADR-6). Run it against a running stack:

    docker compose up -d --build
    pytest tests/integration
"""
import os
import random
import string
import time

import pytest
import requests

WORKOUTS_URL = os.environ.get("WORKOUTS_URL", "http://localhost:8001")
RECORDS_URL = os.environ.get("RECORDS_URL", "http://localhost:8002")


def wait_until_healthy(base_url, timeout_s=120):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            if requests.get(f"{base_url}/health", timeout=2).status_code == 200:
                return
        except requests.ConnectionError:
            pass
        time.sleep(2)
    pytest.fail(f"{base_url}/health never returned 200")


@pytest.fixture(scope="module", autouse=True)
def stack_is_up():
    wait_until_healthy(WORKOUTS_URL)
    wait_until_healthy(RECORDS_URL)


@pytest.fixture
def exercise():
    # A fresh, letters-only name so earlier runs or real data can't change the result.
    return "Seam " + "".join(random.choices(string.ascii_lowercase, k=8)).title()


def log_workout(exercise, sets, date="2026-11-01"):
    body = {"date": date, "exercises": [{"name": exercise, "sets": sets}]}
    response = requests.post(f"{WORKOUTS_URL}/api/workouts", json=body, timeout=5)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_records_computes_prs_from_sets_logged_in_workouts(exercise):
    workout_id = log_workout(exercise, [{"reps": 5, "weight_kg": 100}, {"reps": 1, "weight_kg": 110}])
    try:
        response = requests.get(f"{RECORDS_URL}/api/records/{exercise}", timeout=5)
        assert response.status_code == 200, response.text
        prs = response.json()["personal_records"]
        assert prs["heaviest"]["weight_kg"] == 110.0
        assert prs["best_1rm"]["estimated_1rm"] == 116.7  # 100 * (1 + 5/30) beats 110 x 1
    finally:
        requests.delete(f"{WORKOUTS_URL}/api/workouts/{workout_id}", timeout=5)


def test_deleting_the_workout_removes_it_from_records(exercise):
    workout_id = log_workout(exercise, [{"reps": 3, "weight_kg": 80}])
    assert requests.get(f"{RECORDS_URL}/api/records/{exercise}", timeout=5).status_code == 200

    assert requests.delete(f"{WORKOUTS_URL}/api/workouts/{workout_id}", timeout=5).status_code == 204

    # Records keeps no copy of the sets, so once workouts forgets them, so does records.
    assert requests.get(f"{RECORDS_URL}/api/records/{exercise}", timeout=5).status_code == 404
