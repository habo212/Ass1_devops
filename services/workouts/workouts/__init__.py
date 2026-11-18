"""The workouts service: gym sessions, their exercises and sets."""
import logging
import sys

from flask import Flask

from .config import load_config
from .cors import allow_ui_origin
from .db import database_is_usable, init_db
from .observability import log_requests
from .routes import bp as workouts_bp


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(load_config())
    if overrides:
        # tests pass the test database's DATABASE_URL here
        app.config.update(overrides)
    if not app.config["DATABASE_URL"]:
        raise RuntimeError("DATABASE_URL is not set")

    # Log to stdout, where docker compose and Azure Container Apps collect it.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    init_db(app)

    log_requests(app)
    allow_ui_origin(app)
    app.register_blueprint(workouts_bp)

    @app.get("/health")
    def health():
        # Only this service's own state: its database, never the other service.
        if database_is_usable(app.config["DATABASE_URL"]):
            return {"status": "ok", "db": "ok", "version": app.config["GIT_SHA"]}
        return {"status": "error", "db": "error", "version": app.config["GIT_SHA"]}, 503

    return app
