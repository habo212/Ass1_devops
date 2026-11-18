"""Only the UI's origin may read this service's answers from a browser."""
UI = "http://localhost:8080"


def test_the_ui_origin_is_allowed(client):
    response = client.get("/health", headers={"Origin": UI})
    assert response.headers["Access-Control-Allow-Origin"] == UI


def test_other_origins_are_not_allowed(client):
    response = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in response.headers


def test_preflight_allows_put_with_json(client):
    response = client.options("/health", headers={
        "Origin": UI,
        "Access-Control-Request-Method": "PUT",
        "Access-Control-Request-Headers": "Content-Type",
    })
    assert response.status_code == 200
    assert "PUT" in response.headers["Access-Control-Allow-Methods"]
    assert response.headers["Access-Control-Allow-Headers"] == "Content-Type"


def test_ui_origin_comes_from_the_environment(app):
    app.config["UI_ORIGIN"] = "https://gymlog.example"
    response = app.test_client().get("/health", headers={"Origin": "https://gymlog.example"})
    assert response.headers["Access-Control-Allow-Origin"] == "https://gymlog.example"
