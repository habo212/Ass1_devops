"""Records business logic: personal records, 1RM estimates and progress.

Works on plain lists of sets like
    {"set_id": 1, "performed_on": "2026-09-30", "reps": 5, "weight_kg": 100.0}
so it needs no database and no Flask.
"""
MAX_TARGET_KG = 500


class ValidationError(ValueError):
    """Raised when a goal is not valid. Routes turn it into a 400."""


def epley_1rm(weight_kg, reps):
    """Estimate the one-rep max with the Epley formula: w * (1 + reps / 30).

    A single rep already is a 1RM, so it's returned as-is (the formula would
    add 3.3% for no reason).
    """
    if reps == 1:
        return round(weight_kg, 1)
    return round(weight_kg * (1 + reps / 30), 1)


def find_personal_records(sets):
    """Return the heaviest set and the set with the best estimated 1RM.

    Sets come oldest first, and max() keeps the first of equal values, so a
    tie counts from the first day it was achieved. Returns None if no sets.
    """
    if not sets:
        return None
    heaviest = max(sets, key=lambda s: s["weight_kg"])
    best = max(sets, key=lambda s: epley_1rm(s["weight_kg"], s["reps"]))
    return {
        "heaviest": heaviest,
        "best_1rm": {**best, "estimated_1rm": epley_1rm(best["weight_kg"], best["reps"])},
    }


def progress_by_date(sets):
    """Best estimated 1RM for each workout date, oldest first, to draw progress."""
    best_per_date = {}
    for s in sets:
        estimate = epley_1rm(s["weight_kg"], s["reps"])
        day = s["performed_on"]
        if day not in best_per_date or estimate > best_per_date[day]:
            best_per_date[day] = estimate
    return [{"date": day, "best_1rm": best_per_date[day]} for day in sorted(best_per_date)]


def validate_target(target_kg):
    """Check a goal weight and return it as a float."""
    try:
        target_kg = float(target_kg)
    except (TypeError, ValueError):
        raise ValidationError("target_kg must be a number")
    if target_kg <= 0 or target_kg > MAX_TARGET_KG:
        raise ValidationError(f"target_kg must be above 0 and at most {MAX_TARGET_KG}")
    return target_kg


def goal_percent(best_1rm, target_kg):
    """How far the best estimated 1RM is towards the goal, capped at 100%."""
    return min(100, round(best_1rm / target_kg * 100))
