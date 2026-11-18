"""CORS: let the browser call this service from the UI's origin, and from nowhere else.

The UI is served from another origin (nginx on :8080 locally, the Static Web App on
Azure), so the browser only lets its JavaScript read our answers if we send
Access-Control-Allow-Origin with exactly that origin.
"""
from flask import request


def allow_ui_origin(app):
    @app.after_request
    def add_cors_headers(response):
        if request.headers.get("Origin") == app.config["UI_ORIGIN"]:
            response.headers["Access-Control-Allow-Origin"] = app.config["UI_ORIGIN"]
            # Before a PUT, DELETE or JSON POST the browser first sends an OPTIONS
            # "preflight" request; Flask answers it, and these headers approve it.
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        # The answer depends on the Origin header, so caches must not mix them up.
        response.headers["Vary"] = "Origin"
        return response
