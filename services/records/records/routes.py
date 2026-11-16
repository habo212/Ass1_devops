"""HTTP layer for records: PRs, progress and goals for one exercise."""
from datetime import date

from flask import Blueprint, request

from . import repository, service
from .summary import clean_name, load_summary
from .workouts_client import WorkoutsUnavailable

bp = Blueprint("records", __name__, url_prefix="/api/records")


@bp.get("/<name>")
def get_records(name):
    exercise_name = clean_name(name)
    if exercise_name is None:
        return {"error": "no sets logged for this exercise"}, 404
    try:
        summary = load_summary(exercise_name)
    except WorkoutsUnavailable:
        # Designed failure: say clearly what is wrong, and still return the part
        # we own (the goal), instead of a stack trace or a hung request.
        return {
            "error": "the workouts service is unavailable, so records can't be calculated right now",
            "exercise": exercise_name,
            "goal": repository.get_goal(exercise_name),
        }, 503
    if summary is None:
        return {"error": "no sets logged for this exercise"}, 404
    return summary


@bp.put("/<name>/goal")
def put_goal(name):
    exercise_name = clean_name(name)
    if exercise_name is None:
        return {"error": "invalid exercise name"}, 400
    body = request.get_json(silent=True) or {}
    try:
        target_kg = service.validate_target(body.get("target_kg"))
    except service.ValidationError as e:
        return {"error": str(e)}, 400
    repository.set_goal(exercise_name, target_kg, date.today().isoformat())
    return repository.get_goal(exercise_name)


@bp.delete("/<name>/goal")
def delete_goal(name):
    exercise_name = clean_name(name)
    if exercise_name is None or not repository.delete_goal(exercise_name):
        return {"error": "no goal for this exercise"}, 404
    return "", 204
