"""HTTP layer for workouts: read the request, call service + repository, return JSON."""
from flask import Blueprint, request

from . import repository, service

bp = Blueprint("workouts", __name__, url_prefix="/api/workouts")


@bp.post("")
def create_workout():
    try:
        workout = service.validate_workout(request.get_json(silent=True))
    except service.ValidationError as e:
        return {"error": str(e)}, 400
    workout_id = repository.create_workout(workout)
    return repository.get_workout(workout_id), 201


@bp.get("")
def list_workouts():
    return {"workouts": repository.list_workouts()}


@bp.get("/<int:workout_id>")
def get_workout(workout_id):
    workout = repository.get_workout(workout_id)
    if workout is None:
        return {"error": "workout not found"}, 404
    return workout


@bp.put("/<int:workout_id>")
def update_workout(workout_id):
    try:
        workout = service.validate_workout(request.get_json(silent=True))
    except service.ValidationError as e:
        return {"error": str(e)}, 400
    if not repository.update_workout(workout_id, workout):
        return {"error": "workout not found"}, 404
    return repository.get_workout(workout_id)


@bp.delete("/<int:workout_id>")
def delete_workout(workout_id):
    if not repository.delete_workout(workout_id):
        return {"error": "workout not found"}, 404
    return "", 204
