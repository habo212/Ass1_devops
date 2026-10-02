def log(client, day, name, reps, weight):
    client.post("/api/workouts", json={
        "date": day, "exercises": [{"name": name, "sets": [{"reps": reps, "weight_kg": weight}]}],
    })


def test_records_page_shows_prs_and_progress(client):
    log(client, "2026-09-01", "Squat", 5, 90)
    log(client, "2026-09-08", "Squat", 3, 100)
    page = client.get("/records/squat")
    assert page.status_code == 200
    assert b"Squat" in page.data
    assert b"105.0 kg" in page.data  # best estimated 1RM: 90 * (1 + 5/30)
    assert b"2026-09-08" in page.data


def test_records_page_unknown_exercise(client):
    assert client.get("/records/Deadlift").status_code == 404
    assert client.get("/records/%20").status_code == 404


def test_goal_form_set_and_remove(client):
    log(client, "2026-09-01", "Squat", 5, 90)
    response = client.post("/records/Squat/goal", data={"target_kg": "140"})
    assert response.status_code == 302
    assert b"75% there" in client.get("/records/Squat").data

    client.post("/records/Squat/goal/delete")
    assert b"% there" not in client.get("/records/Squat").data


def test_goal_form_rejects_bad_value(client):
    log(client, "2026-09-01", "Squat", 5, 90)
    page = client.post("/records/Squat/goal", data={"target_kg": "-3"})
    assert page.status_code == 400
    assert b"target_kg must be" in page.data


def test_workout_page_links_to_records(client):
    log(client, "2026-09-01", "Bench Press", 5, 80)
    assert b"/records/Bench%20Press" in client.get("/workouts/1").data
