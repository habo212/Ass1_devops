"""The records service: personal records, 1RM progress and goals."""
import logging

from flask import Flask

from .config import load_config
from .db import init_db
from .routes import bp as records_bp


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(load_config())
    if overrides:
        # tests pass the test database's DATABASE_URL here
        app.config.update(overrides)
    if not app.config["DATABASE_URL"]:
        raise RuntimeError("DATABASE_URL is not set")

    # Log to stdout, where docker compose and Azure Container Apps collect it.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    init_db(app)

    app.register_blueprint(records_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
