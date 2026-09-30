"""Public interface of the workouts domain.

Other domains (records) may only use what is listed here, never repository,
service or routes directly. If workouts became its own service, these two
functions would become its HTTP API. See ADR-2.
"""
from .repository import get_sets_for_exercise
from .service import normalize_exercise_name

__all__ = ["get_sets_for_exercise", "normalize_exercise_name"]
