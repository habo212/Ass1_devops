# Gym Log

A workout logger: record gym sessions (exercises, sets, reps, weight) and automatically track personal records (PRs) and progress per exercise.

## Run it

The app is two services, `services/workouts` and `services/records`, each with its own SQL Server
database. Needs Docker Desktop (on Apple Silicon, turn on Rosetta emulation in its settings).

```bash
docker compose up --build
```

This starts SQL Server, runs `db/init.sql` once (databases and logins), then builds and starts both
services: workouts on http://localhost:8001 and records on http://localhost:8002. Open the UI at
**http://localhost:8080**: a stock `nginx` container serving the static files in `ui/`, which call
both services from the browser. Data is kept in the `sqlserver-data` volume between runs.

The services' URLs used by the UI are in `ui/config.js` (local defaults); the deploy pipeline
replaces that file with the Azure URLs.

### Run a single service without Docker

Start only the database, then run the service with Python:

```bash
docker compose up -d sqlserver db-init

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r services/workouts/requirements-dev.txt -r services/records/requirements-dev.txt

# terminal 1
cd services/workouts
PORT=8001 DATABASE_URL='mssql://workouts_user:Workouts_LocalDev1!@localhost:1433/workouts' python app.py
# terminal 2
cd services/records
PORT=8002 WORKOUTS_URL=http://localhost:8001 \
  DATABASE_URL='mssql://records_user:Records_LocalDev1!@localhost:1433/records' python app.py
```

The passwords above are local-only defaults from `docker-compose.yml` (SQL Server is bound to
127.0.0.1). Override them with environment variables or a git-ignored `.env` file.

## Configuration (environment variables)

| Service | Variable | Default | Purpose |
|---|---|---|---|
| both | `PORT` | `8000` | Port the service listens on (always binds `0.0.0.0`) |
| both | `DATABASE_URL` | none (secret) | `mssql://user:password@host:1433/database` of the service's own database |
| records | `WORKOUTS_URL` | `http://workouts:8000` | Base URL of the workouts service |
| records | `WORKOUTS_TIMEOUT_S` | `2` | Seconds to wait for workouts before answering 503 |
| both | `UI_ORIGIN` | `http://localhost:8080` | The only origin allowed to call the service from a browser (CORS) |
| both | `GIT_SHA` | `dev` | Commit the running build came from, shown by `/health`; set by the pipeline |

## Logs

Each service logs to stdout, one line per request with method, path, status and duration,
e.g. `INFO requests: GET /api/workouts 200 12.3ms`. See them with `docker compose logs -f workouts`.

## Database and migrations

- `db/init.sql` creates the `workouts` and `records` databases and one login per service, each
  able to open only its own database. It is safe to run again.
- Each service creates and changes its own tables with numbered files in `services/<name>/migrations/`
  (`001_init.sql`, ...). On startup the service applies the files not yet listed in its
  `schema_migrations` table, each in one transaction, so a second start applies nothing.
- Applied migrations are never edited; a change is a new file. A line with only `GO` splits a
  file into batches.
- Connecting retries with backoff (1, 2, 4, 8, then 10 s, about 65 s in total) so a paused
  Azure SQL database has time to resume.

## API

| Method | Path | What it does |
|---|---|---|
| `GET` | `/health` | `200 {"status": "ok", "db": "ok", "version": "<git sha>"}` if the service can read and write its own database, else `503` (both) |
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
    migrations/           #   001_init.sql, ... applied in order on startup
    Dockerfile            #   python:3.13.5-slim, non-root, gunicorn with 1 worker
    workouts/             #   create_app, config, db, migrate, service, repository, routes
    tests/
  records/                # Service 2: PRs, Epley 1RM progress, goals
    app.py
    requirements.txt
    records/              #   same layout, plus workouts_client.py (the HTTP call to workouts)
    migrations/
    tests/                #   workouts is replaced by a fake, so no second process is needed
db/init.sql             # creates both databases and logins (local)
docker-compose.yml
```

## Tests

Tests run against the compose SQL Server in a throwaway `workouts_test` / `records_test` database
(set `TEST_SQLSERVER_URL` to use another server). Start it first, then test each service from its folder:

```bash
docker compose up -d sqlserver
cd services/workouts && pytest --cov=workouts --cov-report=term-missing
cd services/records && pytest --cov=records --cov-report=term-missing
```

Result on 2026-11-17: workouts **65 passed, 100%**; records **48 passed, 100%**.
