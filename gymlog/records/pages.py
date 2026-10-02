"""HTML page for one exercise's records, progress and goal."""
from datetime import date

from flask import Blueprint, abort, redirect, render_template, request, url_for

from . import repository, service
from .summary import clean_name, load_summary

bp = Blueprint("record_pages", __name__, url_prefix="/records")


def _summary_or_404(name):
    exercise_name = clean_name(name)
    summary = load_summary(exercise_name) if exercise_name else None
    if summary is None:
        abort(404)
    return summary


@bp.get("/<name>")
def detail(name):
    return render_template("records/detail.html", summary=_summary_or_404(name), error=None)


@bp.post("/<name>/goal")
def set_goal(name):
    summary = _summary_or_404(name)
    try:
        target_kg = service.validate_target(request.form.get("target_kg"))
    except service.ValidationError as e:
        return render_template("records/detail.html", summary=summary, error=str(e)), 400
    repository.set_goal(summary["exercise"], target_kg, date.today().isoformat())
    return redirect(url_for("record_pages.detail", name=summary["exercise"]))


@bp.post("/<name>/goal/delete")
def delete_goal(name):
    summary = _summary_or_404(name)
    repository.delete_goal(summary["exercise"])
    return redirect(url_for("record_pages.detail", name=summary["exercise"]))
