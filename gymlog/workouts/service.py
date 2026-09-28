"""Workouts business logic: checking and cleaning input.

No Flask and no SQL in here, so every function can be tested with plain values.
"""
from datetime import date

MAX_NAME_LENGTH = 60
MAX_REPS = 100
MAX_WEIGHT_KG = 500


class ValidationError(ValueError):
    """Raised when user input is not a valid workout. Routes turn it into a 400."""


def normalize_exercise_name(name):
    """Clean an exercise name so '  bench   PRESS ' and 'Bench Press' match.

    The records domain matches exercises by name (see ADR-3), so this must be
    the only way names get cleaned.
    """
    if not isinstance(name, str):
        raise ValidationError("exercise name must be text")
    cleaned = " ".join(name.split()).title()
    if not cleaned:
        raise ValidationError("exercise name is required")
    if len(cleaned) > MAX_NAME_LENGTH:
        raise ValidationError(f"exercise name must be at most {MAX_NAME_LENGTH} characters")
    return cleaned


def parse_workout_date(value, today=None):
    """Turn 'YYYY-MM-DD' into a date. Workouts can't be in the future.

    `today` can be passed in by tests so they don't depend on the real date.
    """
    if today is None:
        today = date.today()
    try:
        performed_on = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError("date must look like YYYY-MM-DD")
    if performed_on > today:
        raise ValidationError("workout date can't be in the future")
    return performed_on


def validate_set(reps, weight_kg):
    """Check one set and return it as (int reps, float weight_kg).

    Form data arrives as strings, so we convert here.
    """
    try:
        reps = int(reps)
    except (TypeError, ValueError):
        raise ValidationError("reps must be a whole number")
    try:
        weight_kg = float(weight_kg)
    except (TypeError, ValueError):
        raise ValidationError("weight must be a number")

    if reps < 1 or reps > MAX_REPS:
        raise ValidationError(f"reps must be between 1 and {MAX_REPS}")
    if weight_kg < 0 or weight_kg > MAX_WEIGHT_KG:
        raise ValidationError(f"weight must be between 0 and {MAX_WEIGHT_KG} kg")
    return reps, weight_kg


def validate_workout(data, today=None):
    """Check a whole workout and return a cleaned copy ready to save.

    Expected shape:
        {"date": "2026-09-28", "notes": "...",
         "exercises": [{"name": "Bench Press",
                        "sets": [{"reps": 8, "weight_kg": 60}]}]}
    """
    if not isinstance(data, dict):
        raise ValidationError("workout must be an object")

    performed_on = parse_workout_date(data.get("date"), today)
    notes = str(data.get("notes") or "").strip()

    exercises = data.get("exercises")
    if not isinstance(exercises, list) or not exercises:
        raise ValidationError("a workout needs at least one exercise")

    clean_exercises = []
    for exercise in exercises:
        if not isinstance(exercise, dict):
            raise ValidationError("each exercise must be an object")
        name = normalize_exercise_name(exercise.get("name"))
        sets = exercise.get("sets")
        if not isinstance(sets, list) or not sets:
            raise ValidationError(f"{name} needs at least one set")

        clean_sets = []
        for s in sets:
            if not isinstance(s, dict):
                raise ValidationError("each set must be an object")
            reps, weight_kg = validate_set(s.get("reps"), s.get("weight_kg"))
            clean_sets.append({"reps": reps, "weight_kg": weight_kg})
        clean_exercises.append({"name": name, "sets": clean_sets})

    return {
        "performed_on": performed_on.isoformat(),
        "notes": notes,
        "exercises": clean_exercises,
    }
