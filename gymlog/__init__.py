import os

from flask import Flask

from .config import load_config
from .db import init_db
from .records.routes import bp as records_bp
from .workouts.routes import bp as workouts_bp


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(load_config())
    if overrides:
        # tests pass a temp DATA_DIR / DB_PATH here
        app.config.update(overrides)

    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    init_db(app)

    app.register_blueprint(workouts_bp)
    app.register_blueprint(records_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
