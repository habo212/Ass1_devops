def test_home_page_shows_form(client):
    page = client.get("/")
    assert page.status_code == 200
    assert b"Log a workout" in page.data
    assert b"No workouts yet" in page.data


def test_submit_form_then_view_and_delete(client):
    response = client.post("/", data={
        "date": "2026-09-30", "notes": "push day", "exercises": "bench press: 8x60, 6x65",
    })
    assert response.status_code == 302  # redirect to the new workout
    detail = client.get(response.headers["Location"])
    assert b"Bench Press" in detail.data
    assert b"65.0" in detail.data
    assert b"2026-09-30" in client.get("/").data

    workout_url = response.headers["Location"]
    assert client.post(workout_url + "/delete").status_code == 302
    assert client.get(workout_url).status_code == 404
    assert client.post(workout_url + "/delete").status_code == 404


def test_bad_form_shows_error_and_keeps_input(client):
    page = client.post("/", data={"date": "2026-09-30", "exercises": "bench press 8x60"})
    assert page.status_code == 400
    assert b"line 1" in page.data
    assert b"bench press 8x60" in page.data  # what the user typed is still there
