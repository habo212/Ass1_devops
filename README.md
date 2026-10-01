# Gym Log

A workout logger: record gym sessions (exercises, sets, reps, weight) and automatically track personal records (PRs) and progress per exercise.

## Run it

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://localhost:8000 to log workouts in the browser (http://localhost:8000/health returns `{"status": "ok"}`).

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8000` | Port the server listens on (always binds `0.0.0.0`) |
| `DATA_DIR` | `./data` | Folder for the SQLite file. The DB lives at `$DATA_DIR/gymlog.db` |

## API

| Method | Path | What it does |
|---|---|---|
| `POST` | `/api/workouts` | Log a workout (JSON: `date`, `notes`, `exercises[{name, sets[{reps, weight_kg}]}]`) |
| `GET` | `/api/workouts` | List workouts, newest first |
| `GET` / `PUT` / `DELETE` | `/api/workouts/<id>` | Get, replace or delete one workout |
| `GET` | `/api/records/<exercise>` | Personal records, estimated 1RM progress per day, and goal progress |
| `PUT` / `DELETE` | `/api/records/<exercise>/goal` | Set (`{"target_kg": 100}`) or remove a target weight |

Example:

```bash
curl -X POST localhost:8000/api/workouts -H 'content-type: application/json' \
  -d '{"date":"2026-10-01","exercises":[{"name":"Bench Press","sets":[{"reps":5,"weight_kg":80}]}]}'
curl localhost:8000/api/records/Bench%20Press
```

## Project structure

```
app.py                  # entry point: python app.py
gymlog/
  __init__.py           # create_app(): config, init_db, registers blueprints
  config.py             # reads PORT / DATA_DIR from the environment
  db.py                 # SQLite connection per request + schema init on startup
  workouts/             # Domain 1: sessions -> exercises -> sets
    __init__.py         #   public interface used by other domains (ADR-2)
    service.py repository.py routes.py schema.sql
  records/              # Domain 2: PRs, Epley 1RM progress, goals
    service.py repository.py routes.py schema.sql
tests/                  # pytest, each test gets a temporary DATA_DIR
```

## Tests

```bash
pytest --cov=gymlog --cov-report=term-missing
```

Result on 2026-10-01: **64 passed, 100% coverage** of `gymlog/` (322 statements, 0 missed).
