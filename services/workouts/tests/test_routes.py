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
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "db": "ok", "version": "dev"}


def test_health_check_leaves_nothing_behind(client):
    client.get("/health")
    client.get("/health")  # would fail on the duplicate key if the first write had stayed
    assert client.get("/health").status_code == 200


def test_health_is_503_when_the_database_is_unreachable(app):
    # Nothing listens on port 1, so the connection is refused straight away.
    app.config["DATABASE_URL"] = "mssql://u:p@127.0.0.1:1/nothing"
    response = app.test_client().get("/health")
    assert response.status_code == 503
    assert response.json["db"] == "error"


def test_health_shows_the_git_sha(app):
    app.config["GIT_SHA"] = "abc1234"
    assert app.test_client().get("/health").json["version"] == "abc1234"


def test_every_request_is_logged(client, caplog):
    caplog.set_level("INFO", logger="requests")
    client.get("/no-such-page")
    line = caplog.records[-1].getMessage()
    assert line.startswith("GET /no-such-page 404 ")
    assert line.endswith("ms")
