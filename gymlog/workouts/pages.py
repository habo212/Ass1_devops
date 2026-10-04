"""HTML pages for workouts. Same service + repository as the JSON API, but renders templates."""
from datetime import date

from flask import Blueprint, abort, redirect, render_template, request, url_for

from . import repository, service

bp = Blueprint("workout_pages", __name__)


@bp.get("/")
def index():
    return render_template(
        "workouts/index.html",
        workouts=repository.list_workouts(),
        exercises=repository.list_exercise_names(),
        form={"date": date.today().isoformat()},
        error=None,
    )


@bp.post("/")
def create():
    form = request.form
    try:
        workout = service.validate_workout({
            "date": form.get("date"),
            "notes": form.get("notes"),
            "exercises": service.parse_exercise_lines(form.get("exercises")),
        })
    except service.ValidationError as e:
        # Show the form again with what the user typed, plus the error.
        page = render_template(
            "workouts/index.html",
            workouts=repository.list_workouts(),
            exercises=repository.list_exercise_names(),
            form=form,
            error=str(e),
        )
        return page, 400
    workout_id = repository.create_workout(workout)
    # Redirect after POST so refreshing the page doesn't log the workout twice.
    return redirect(url_for("workout_pages.detail", workout_id=workout_id))


@bp.get("/workouts/<int:workout_id>")
def detail(workout_id):
    workout = repository.get_workout(workout_id)
    if workout is None:
        abort(404)
    return render_template("workouts/detail.html", workout=workout)


@bp.post("/workouts/<int:workout_id>/delete")
def delete(workout_id):
    if not repository.delete_workout(workout_id):
        abort(404)
    return redirect(url_for("workout_pages.index"))
