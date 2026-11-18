import pathlib

import requests


def make_set(set_id, day, reps, weight):
    return {"set_id": set_id, "performed_on": day, "reps": reps, "weight_kg": weight}


def test_records_for_logged_exercise(client, workouts):
    workouts.sets["Bench Press"] = [
        make_set(1, "2026-09-01", 5, 80.0),
        make_set(2, "2026-09-08", 3, 90.0),
    ]

    body = client.get("/api/records/bench%20press").json  # different spelling, same exercise

    assert body["exercise"] == "Bench Press"
    assert body["personal_records"]["heaviest"]["weight_kg"] == 90.0
    assert body["personal_records"]["best_1rm"]["estimated_1rm"] == 99.0
    assert [p["date"] for p in body["progress"]] == ["2026-09-01", "2026-09-08"]
    assert body["goal"] is None


def test_records_asks_workouts_with_the_configured_url_and_timeout(client, workouts):
    client.get("/api/records/bench%20press")

    assert workouts.calls == [
        ("http://workouts.test/api/workouts/exercises/Bench%20Press/sets", 2),
    ]


def test_records_unknown_exercise(client, workouts):
    assert client.get("/api/records/Deadlift").status_code == 404
    assert client.get("/api/records/%20").status_code == 404


def test_goal_lifecycle(client, workouts):
    workouts.sets["Squat"] = [make_set(1, "2026-09-01", 5, 90.0)]  # estimated 1RM 105

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


# --- Partial failure: what records does when workouts can't be asked ---

def test_workouts_down_gives_503_with_a_clear_error_and_our_own_goal(client, workouts):
    client.put("/api/records/Squat/goal", json={"target_kg": 140})
    workouts.error = requests.ConnectionError("connection refused")

    response = client.get("/api/records/Squat")

    assert response.status_code == 503
    assert "workouts service is unavailable" in response.json["error"]
    assert response.json["exercise"] == "Squat"
    assert response.json["goal"]["target_kg"] == 140.0  # records' own data still served


def test_workouts_timeout_gives_503(client, workouts):
    workouts.error = requests.Timeout("too slow")
    assert client.get("/api/records/Squat").status_code == 503


def test_workouts_error_status_gives_503(client, workouts):
    workouts.status_code = 500
    assert client.get("/api/records/Squat").status_code == 503


def test_goals_still_work_while_workouts_is_down(client, workouts):
    workouts.error = requests.ConnectionError("connection refused")

    assert client.put("/api/records/Squat/goal", json={"target_kg": 120}).status_code == 200
    assert client.delete("/api/records/Squat/goal").status_code == 204
    assert workouts.calls == []  # goals never needed workouts at all


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


def test_records_shares_no_code_with_workouts():
    """Guards the seam: records reaches workouts over HTTP only, never by import."""
    records_dir = pathlib.Path(__file__).parent.parent / "records"
    for path in records_dir.glob("*.py"):
        for line in path.read_text().splitlines():
            code = line.strip()
            assert not code.startswith(("import workouts", "from workouts")), (
                f"{path.name} imports the workouts package: {code}"
            )
