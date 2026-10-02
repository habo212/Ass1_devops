"""HTTP layer for records: PRs, progress and goals for one exercise."""
from datetime import date

from flask import Blueprint, request

from . import repository, service
from .summary import clean_name, load_summary

bp = Blueprint("records", __name__, url_prefix="/api/records")


@bp.get("/<name>")
def get_records(name):
    exercise_name = clean_name(name)
    summary = load_summary(exercise_name) if exercise_name else None
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
