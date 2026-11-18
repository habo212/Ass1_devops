"""One log line per request, written to stdout: method, path, status, duration."""
import logging
import time

from flask import g, request

log = logging.getLogger("requests")


def log_requests(app):
    @app.before_request
    def start_timer():
        g.started_at = time.perf_counter()

    @app.after_request
    def log_request(response):
        duration_ms = (time.perf_counter() - g.started_at) * 1000
        # e.g. "GET /api/workouts 200 12.3ms"
        log.info("%s %s %s %.1fms", request.method, request.path, response.status_code, duration_ms)
        return response
