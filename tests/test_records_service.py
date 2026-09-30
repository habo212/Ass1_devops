import pytest

from gymlog.records.service import (
    ValidationError,
    epley_1rm,
    find_personal_records,
    goal_percent,
    progress_by_date,
    validate_target,
)


def make_set(set_id, day, reps, weight):
    return {"set_id": set_id, "performed_on": day, "reps": reps, "weight_kg": weight}


SETS = [
    make_set(1, "2026-09-01", 5, 100.0),   # 1RM 116.7
    make_set(2, "2026-09-01", 1, 110.0),   # heaviest, 1RM 110
    make_set(3, "2026-09-08", 8, 100.0),   # 1RM 126.7, best
    make_set(4, "2026-09-15", 1, 110.0),   # ties heaviest, later
]


def test_epley_formula():
    assert epley_1rm(100, 5) == 116.7
    assert epley_1rm(60, 10) == 80.0


def test_epley_single_rep_is_the_weight():
    assert epley_1rm(110, 1) == 110


def test_find_prs():
    prs = find_personal_records(SETS)
    assert prs["heaviest"]["set_id"] == 2  # first time 110 was lifted, not the repeat
    assert prs["best_1rm"]["set_id"] == 3
    assert prs["best_1rm"]["estimated_1rm"] == 126.7


def test_find_prs_empty():
    assert find_personal_records([]) is None


def test_progress_keeps_best_per_day_in_date_order():
    assert progress_by_date(list(reversed(SETS))) == [
        {"date": "2026-09-01", "best_1rm": 116.7},
        {"date": "2026-09-08", "best_1rm": 126.7},
        {"date": "2026-09-15", "best_1rm": 110.0},
    ]


def test_progress_empty():
    assert progress_by_date([]) == []


def test_validate_target():
    assert validate_target("120") == 120.0


@pytest.mark.parametrize("bad", [0, -5, 501, "lots", None])
def test_validate_target_rejects(bad):
    with pytest.raises(ValidationError):
        validate_target(bad)


def test_goal_percent():
    assert goal_percent(90, 120) == 75
    assert goal_percent(130, 120) == 100
