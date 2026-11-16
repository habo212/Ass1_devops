# Gym Log

A workout logger: record gym sessions (exercises, sets, reps, weight) and automatically track personal records (PRs) and progress per exercise.

## Run it

Assignment 2 is in progress: the app is now two services, `services/workouts` and `services/records`.
Docker, SQL Server and the static UI are added in later steps. For now each service runs on its own:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r services/workouts/requirements-dev.txt -r services/records/requirements-dev.txt

# terminal 1
cd services/workouts && PORT=8001 python app.py
# terminal 2
cd services/records && PORT=8002 WORKOUTS_URL=http://localhost:8001 python app.py
```

## Configuration (environment variables)

| Service | Variable | Default | Purpose |
|---|---|---|---|
| both | `PORT` | `8000` | Port the service listens on (always binds `0.0.0.0`) |
| both | `DATA_DIR` | `./data` | Folder for the service's own SQLite file |
| records | `WORKOUTS_URL` | `http://workouts:8000` | Base URL of the workouts service |
| records | `WORKOUTS_TIMEOUT_S` | `2` | Seconds to wait for workouts before answering 503 |

## API

| Method | Path | What it does |
|---|---|---|
| `POST` | `/api/workouts` | Log a workout (JSON: `date`, `notes`, `exercises[{name, sets[{reps, weight_kg}]}]`) |
| `GET` | `/api/workouts` | List workouts, newest first |
| `GET` / `PUT` / `DELETE` | `/api/workouts/<id>` | Get, replace or delete one workout |
| `GET` | `/api/workouts/exercises` | Every exercise name logged (workouts) |
| `GET` | `/api/workouts/exercises/<exercise>/sets` | Every set for one exercise, oldest first. Records calls this (workouts) |
| `GET` | `/api/records/<exercise>` | Personal records, estimated 1RM progress per day, and goal progress. `503` if workouts is unavailable (records) |
| `PUT` / `DELETE` | `/api/records/<exercise>/goal` | Set (`{"target_kg": 100}`) or remove a target weight |

Example:

```bash
curl -X POST localhost:8001/api/workouts -H 'content-type: application/json' \
  -d '{"date":"2026-10-01","exercises":[{"name":"Bench Press","sets":[{"reps":5,"weight_kg":80}]}]}'
curl localhost:8002/api/records/Bench%20Press
```

## Project structure

Design decisions: [ADR.md](ADR.md). The diagrams in [docs/diagrams.md](docs/diagrams.md) still show the Assignment 1 monolith.

```
services/
  workouts/               # Service 1: sessions -> exercises -> sets
    app.py                #   entry point: python app.py
    requirements.txt      #   its own pinned dependencies
    workouts/             #   create_app, config, db, service, repository, routes, schema.sql
    tests/
  records/                # Service 2: PRs, Epley 1RM progress, goals
    app.py
    requirements.txt
    records/              #   same layout, plus workouts_client.py (the HTTP call to workouts)
    tests/                #   workouts is replaced by a fake, so no second process is needed
```

## Tests

Each service is tested from its own folder:

```bash
cd services/workouts && pytest --cov=workouts --cov-report=term-missing
cd services/records && pytest --cov=records --cov-report=term-missing
```

Result on 2026-11-16: workouts **46 passed, 100%**; records **30 passed, 100%**.
