# Image for the records service. Build context: services/records (only this folder).
FROM python:3.13.5-slim

# Print logs straight away (no buffering) and don't write .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencies first: this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only what the service needs to run: no tests, no secrets, no .env.
COPY app.py .
COPY records/ records/
COPY migrations/ migrations/

# Run as an unprivileged user, not root.
RUN useradd --uid 10001 --no-create-home appuser
USER appuser

EXPOSE 8000

# One worker process, so migrations run once per container; 4 threads serve requests.
# --timeout 120 leaves time for the database to resume and migrations to run at startup.
# sh -c so $PORT is read when the container starts; exec so gunicorn gets stop signals.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 120 app:app"]
