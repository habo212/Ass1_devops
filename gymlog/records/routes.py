"""HTTP layer for records: PRs, progress and goals for one exercise."""
from datetime import date

from flask import Blueprint, request

# Only the workouts public interface, never its internals (ADR-2).
from .. import workouts
from . import repository, service

bp = Blueprint("records", __name__, url_prefix="/api/records")


def _clean_name(name):
    try:
        return workouts.normalize_exercise_name(name)
    except ValueError:
        return None


@bp.get("/<name>")
def get_records(name):
    exercise_name = _clean_name(name)
    sets = workouts.get_sets_for_exercise(exercise_name) if exercise_name else []
    if not sets:
        return {"error": "no sets logged for this exercise"}, 404

    prs = service.find_personal_records(sets)
    goal = repository.get_goal(exercise_name)
    if goal:
        goal["percent"] = service.goal_percent(prs["best_1rm"]["estimated_1rm"], goal["target_kg"])

    return {
        "exercise": exercise_name,
        "personal_records": prs,
        "progress": service.progress_by_date(sets),
        "goal": goal,
    }


@bp.put("/<name>/goal")
def put_goal(name):
    exercise_name = _clean_name(name)
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
    exercise_name = _clean_name(name)
    if exercise_name is None or not repository.delete_goal(exercise_name):
        return {"error": "no goal for this exercise"}, 404
    return "", 204
