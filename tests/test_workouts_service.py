from datetime import date

import pytest

from gymlog.workouts.service import (
    ValidationError,
    normalize_exercise_name,
    parse_exercise_lines,
    parse_workout_date,
    validate_set,
    validate_workout,
)

TODAY = date(2026, 9, 30)


def valid_workout():
    return {
        "date": "2026-09-30",
        "notes": "  push day ",
        "exercises": [{"name": "bench press", "sets": [{"reps": "8", "weight_kg": "60"}]}],
    }


# normalize_exercise_name

def test_normalize_fixes_spaces_and_capitals():
    assert normalize_exercise_name("  bench   PRESS ") == "Bench Press"


@pytest.mark.parametrize("bad", ["", "   ", None, 42, "x" * 61])
def test_normalize_rejects_bad_names(bad):
    with pytest.raises(ValidationError):
        normalize_exercise_name(bad)


# parse_workout_date

def test_parse_date_accepts_today():
    assert parse_workout_date("2026-09-30", today=TODAY) == TODAY


def test_parse_date_rejects_future():
    with pytest.raises(ValidationError, match="future"):
        parse_workout_date("2026-10-01", today=TODAY)


@pytest.mark.parametrize("bad", ["30/09/2026", "yesterday", None])
def test_parse_date_rejects_bad_format(bad):
    with pytest.raises(ValidationError):
        parse_workout_date(bad, today=TODAY)


def test_parse_date_defaults_to_real_today():
    assert parse_workout_date("2000-01-01") == date(2000, 1, 1)


# validate_set

def test_validate_set_converts_strings():
    assert validate_set("5", "102.5") == (5, 102.5)


def test_validate_set_allows_bodyweight():
    assert validate_set(10, 0) == (10, 0.0)


@pytest.mark.parametrize(
    "reps, weight",
    [(0, 50), (101, 50), ("five", 50), (None, 50), (5, -1), (5, 501), (5, "heavy")],
)
def test_validate_set_rejects_bad_values(reps, weight):
    with pytest.raises(ValidationError):
        validate_set(reps, weight)


# validate_workout

def test_validate_workout_returns_clean_copy():
    assert validate_workout(valid_workout(), today=TODAY) == {
        "performed_on": "2026-09-30",
        "notes": "push day",
        "exercises": [{"name": "Bench Press", "sets": [{"reps": 8, "weight_kg": 60.0}]}],
    }


def test_validate_workout_missing_notes_becomes_empty():
    data = valid_workout()
    del data["notes"]
    assert validate_workout(data, today=TODAY)["notes"] == ""


@pytest.mark.parametrize(
    "change",
    [
        lambda w: w.update(exercises=[]),
        lambda w: w.update(exercises="bench"),
        lambda w: w.update(exercises=["bench"]),
        lambda w: w["exercises"][0].update(sets=[]),
        lambda w: w["exercises"][0].update(sets=[5]),
    ],
)
def test_validate_workout_rejects_bad_structure(change):
    data = valid_workout()
    change(data)
    with pytest.raises(ValidationError):
        validate_workout(data, today=TODAY)


def test_validate_workout_rejects_non_dict():
    with pytest.raises(ValidationError):
        validate_workout(None, today=TODAY)


# parse_exercise_lines

def test_parse_lines_splits_exercises_and_sets():
    text = "Bench Press: 8x60, 6X65\n\n  squat : 5 x 100 \n"
    assert parse_exercise_lines(text) == [
        {"name": "Bench Press", "sets": [{"reps": "8", "weight_kg": "60"}, {"reps": "6", "weight_kg": "65"}]},
        {"name": "  squat ", "sets": [{"reps": "5", "weight_kg": "100"}]},
    ]


def test_parse_lines_then_validate_cleans_everything():
    data = {"date": "2026-09-30", "exercises": parse_exercise_lines("squat : 5 x 100")}
    assert validate_workout(data, today=TODAY)["exercises"] == [
        {"name": "Squat", "sets": [{"reps": 5, "weight_kg": 100.0}]}
    ]


@pytest.mark.parametrize("bad", ["Bench Press 8x60", "Bench Press: 8-60", "Bench Press: 8x60,"])
def test_parse_lines_rejects_bad_lines(bad):
    with pytest.raises(ValidationError, match="line 1"):
        parse_exercise_lines(bad)


def test_parse_lines_empty_input():
    assert parse_exercise_lines(None) == []
