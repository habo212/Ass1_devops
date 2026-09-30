import pathlib


def log(client, day, name, reps, weight):
    client.post("/api/workouts", json={
        "date": day, "exercises": [{"name": name, "sets": [{"reps": reps, "weight_kg": weight}]}],
    })


def test_records_for_logged_exercise(client):
    log(client, "2026-09-01", "Bench Press", 5, 80)
    log(client, "2026-09-08", "bench press", 3, 90)  # different spelling, same exercise

    body = client.get("/api/records/bench%20press").json
    assert body["exercise"] == "Bench Press"
    assert body["personal_records"]["heaviest"]["weight_kg"] == 90.0
    assert body["personal_records"]["best_1rm"]["estimated_1rm"] == 99.0
    assert [p["date"] for p in body["progress"]] == ["2026-09-01", "2026-09-08"]
    assert body["goal"] is None


def test_records_unknown_exercise(client):
    assert client.get("/api/records/Deadlift").status_code == 404
    assert client.get("/api/records/%20").status_code == 404


def test_goal_lifecycle(client):
    log(client, "2026-09-01", "Squat", 5, 90)  # estimated 1RM 105

    assert client.put("/api/records/squat/goal", json={"target_kg": 140}).json["target_kg"] == 140.0
    assert client.get("/api/records/Squat").json["goal"]["percent"] == 75

    client.put("/api/records/Squat/goal", json={"target_kg": 100})  # replaces, doesn't duplicate
    assert client.get("/api/records/Squat").json["goal"]["percent"] == 100

    assert client.delete("/api/records/Squat/goal").status_code == 204
    assert client.delete("/api/records/Squat/goal").status_code == 404


def test_goal_rejects_bad_input(client):
    assert client.put("/api/records/Squat/goal", json={"target_kg": -1}).status_code == 400
    assert client.put("/api/records/Squat/goal", data="x").status_code == 400
    assert client.put("/api/records/%20/goal", json={"target_kg": 100}).status_code == 400


def test_records_only_imports_workouts_public_interface():
    """Guards the ADR-2 seam: records must not reach into workouts internals."""
    records_dir = pathlib.Path(__file__).parent.parent / "gymlog" / "records"
    for path in records_dir.glob("*.py"):
        source = path.read_text()
        for internal in ("workouts.repository", "workouts.service", "workouts.routes"):
            assert internal not in source, f"{path.name} imports {internal}"
