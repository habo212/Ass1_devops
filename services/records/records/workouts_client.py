"""The only place records talks to the workouts service: one HTTP call.

This replaces the `from .. import workouts` import the monolith had (ADR-2, ADR-6).
"""
from urllib.parse import quote

import requests
from flask import current_app


class WorkoutsUnavailable(Exception):
    """Workouts didn't answer in time, couldn't be reached, or answered with an error."""


def get_sets_for_exercise(exercise_name):
    """Every set logged for one exercise, oldest first, fetched from workouts."""
    base_url = current_app.config["WORKOUTS_URL"]
    timeout_s = current_app.config["WORKOUTS_TIMEOUT_S"]
    # quote() so a name like "Bench Press" is safe inside a URL path.
    url = f"{base_url}/api/workouts/exercises/{quote(exercise_name, safe='')}/sets"
    try:
        # Without a timeout a stuck workouts service would hang this request forever.
        response = requests.get(url, timeout=timeout_s)
    except requests.RequestException as e:
        # Covers connection refused, DNS failure and timeouts.
        raise WorkoutsUnavailable(type(e).__name__)
    if response.status_code != 200:
        raise WorkoutsUnavailable(f"workouts answered {response.status_code}")
    return response.json()["sets"]
