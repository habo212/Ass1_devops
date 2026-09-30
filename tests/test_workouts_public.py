from gymlog.workouts import get_sets_for_exercise


def test_get_sets_for_exercise_joins_across_workouts(app, client):
    client.post("/api/workouts", json={"date": "2026-09-08", "exercises": [
        {"name": "Squat", "sets": [{"reps": 5, "weight_kg": 100}]},
        {"name": "Bench Press", "sets": [{"reps": 5, "weight_kg": 70}]},
    ]})
    client.post("/api/workouts", json={"date": "2026-09-01", "exercises": [
        {"name": "squat", "sets": [{"reps": 3, "weight_kg": 90}]},
    ]})

    with app.app_context():
        sets = get_sets_for_exercise("Squat")

    assert [(s["performed_on"], s["weight_kg"]) for s in sets] == [
        ("2026-09-01", 90.0),
        ("2026-09-08", 100.0),
    ]
