"""Builds the records view for one exercise. Shared by the JSON API and the HTML page."""
# Only the workouts public interface, never its internals (ADR-2).
from .. import workouts
from . import repository, service


def clean_name(name):
    """The normalised exercise name, or None if the name is invalid."""
    try:
        return workouts.normalize_exercise_name(name)
    except ValueError:
        return None


def load_summary(exercise_name):
    """PRs, progress and goal for an already-cleaned name, or None if nothing is logged."""
    sets = workouts.get_sets_for_exercise(exercise_name)
    if not sets:
        return None

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
