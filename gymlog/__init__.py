import os

from flask import Flask

from .config import load_config


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(load_config())
    if overrides:
        # tests pass a temp DATA_DIR / DB_PATH here
        app.config.update(overrides)

    os.makedirs(app.config["DATA_DIR"], exist_ok=True)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
