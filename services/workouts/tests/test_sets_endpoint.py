"""The two endpoints the records service reads across the seam."""


def log_two_workouts(client):
    client.post("/api/workouts", json={"date": "2026-09-08", "exercises": [
        {"name": "Squat", "sets": [{"reps": 5, "weight_kg": 100}]},
        {"name": "Bench Press", "sets": [{"reps": 5, "weight_kg": 70}]},
    ]})
    client.post("/api/workouts", json={"date": "2026-09-01", "exercises": [
        {"name": "squat", "sets": [{"reps": 3, "weight_kg": 90}]},
    ]})


def test_sets_for_exercise_are_joined_across_workouts_oldest_first(client):
    log_two_workouts(client)

    body = client.get("/api/workouts/exercises/squat/sets").json

    assert body["exercise"] == "Squat"  # the name comes back normalised
    assert [(s["performed_on"], s["reps"], s["weight_kg"]) for s in body["sets"]] == [
        ("2026-09-01", 3, 90.0),
        ("2026-09-08", 5, 100.0),
    ]
    assert "set_id" in body["sets"][0]


def test_sets_for_unlogged_exercise_is_an_empty_list(client):
    response = client.get("/api/workouts/exercises/Deadlift/sets")
    assert response.status_code == 200
    assert response.json == {"exercise": "Deadlift", "sets": []}


def test_sets_rejects_invalid_name(client):
    response = client.get("/api/workouts/exercises/%20/sets")
    assert response.status_code == 400
    assert "error" in response.json


def test_list_exercise_names(client):
    assert client.get("/api/workouts/exercises").json == {"exercises": []}
    log_two_workouts(client)
    assert client.get("/api/workouts/exercises").json == {"exercises": ["Bench Press", "Squat"]}
