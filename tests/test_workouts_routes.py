WORKOUT = {
    "date": "2026-09-30",
    "exercises": [{"name": "Squat", "sets": [{"reps": 5, "weight_kg": 100}]}],
}


def test_create_then_get(client):
    created = client.post("/api/workouts", json=WORKOUT)
    assert created.status_code == 201
    workout_id = created.json["id"]

    fetched = client.get(f"/api/workouts/{workout_id}")
    assert fetched.status_code == 200
    assert fetched.json["exercises"][0]["sets"][0]["weight_kg"] == 100.0


def test_create_rejects_invalid(client):
    response = client.post("/api/workouts", json={"date": "nope"})
    assert response.status_code == 400
    assert "error" in response.json


def test_list_is_newest_first(client):
    client.post("/api/workouts", json={**WORKOUT, "date": "2026-09-01"})
    client.post("/api/workouts", json=WORKOUT)
    dates = [w["performed_on"] for w in client.get("/api/workouts").json["workouts"]]
    assert dates == ["2026-09-30", "2026-09-01"]


def test_update_replaces_sets(client):
    workout_id = client.post("/api/workouts", json=WORKOUT).json["id"]
    new = {**WORKOUT, "exercises": [{"name": "Squat", "sets": [{"reps": 3, "weight_kg": 110}]}]}
    updated = client.put(f"/api/workouts/{workout_id}", json=new)
    assert updated.status_code == 200
    sets = updated.json["exercises"][0]["sets"]
    assert len(sets) == 1
    assert sets[0]["reps"] == 3


def test_update_invalid_and_missing(client):
    assert client.put("/api/workouts/1", json={}).status_code == 400
    assert client.put("/api/workouts/999", json=WORKOUT).status_code == 404


def test_delete_then_gone(client):
    workout_id = client.post("/api/workouts", json=WORKOUT).json["id"]
    assert client.delete(f"/api/workouts/{workout_id}").status_code == 204
    assert client.get(f"/api/workouts/{workout_id}").status_code == 404
    assert client.delete(f"/api/workouts/{workout_id}").status_code == 404


def test_health(client):
    assert client.get("/health").json == {"status": "ok"}
