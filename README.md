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

## Live system

| | URL |
|---|---|
| UI (Static Web App `hrahal-ieu2024-ui`) | not deployed yet: Static Web Apps are blocked by the Azure for Students region policy (ADR-8) |
| workouts | https://hrahal-ieu2024-workouts.thankfulhill-5d393d7d.germanywestcentral.azurecontainerapps.io/health |
| records | https://hrahal-ieu2024-records.thankfulhill-5d393d7d.germanywestcentral.azurecontainerapps.io/health |

Both services scale to zero, so the first request after a quiet period can take up to about a
minute while the container starts and the database resumes.

## Deployment (Azure)

### How a deploy works

Every push to `main` (always through a pull request) runs `.github/workflows/ci.yml`. If `lint`,
`validate`, both `test` jobs, `integration` and both `build` jobs pass, the `deploy` job:

1. pushes both images to GHCR as `ghcr.io/habo212/gymlog-<service>:<commit sha>`;
2. signs in to Azure as the managed identity `hrahal-ieu2024-github` through GitHub OIDC
   (no password: Azure only trusts tokens for `main` of this repository);
3. updates both Container Apps: new image, 0–1 replicas, and all their configuration
   (`GIT_SHA`, `UI_ORIGIN`, `WORKOUTS_URL`, `WORKOUTS_TIMEOUT_S`, and `DATABASE_URL` read from the
   Container App secret `db-url`, which is set from the GitHub secret);
4. calls `GET /health` on both until each reports the new SHA (30 tries, 10 s apart), else fails;
5. writes `ui/config.js` with the services' URLs and uploads `ui/` to the Static Web App (skipped
   with a warning while the Static Web App doesn't exist).

### Initial setup (once), step by step

Everything is created by `infra/azure-setup.sh`, which is safe to run again: each step skips or
updates what already exists.

1. Install the Azure CLI, the GitHub CLI and Docker Desktop.
2. Sign in to the Azure for Students subscription and to GitHub:
   ```bash
   az login
   az account set --subscription "Azure for Students"
   gh auth login
   ```
3. From the repository root, run the setup:
   ```bash
   ./infra/azure-setup.sh
   ```
   It registers the resource providers, then creates in `rg-sdd-3a` (Germany West Central, an
   allowed region): the SQL server and both databases, a contained user per database
   (`db/azure-user.sql`, run with `sqlcmd` from the SQL Server image), the Static Web App, the
   Container Apps environment and both Container Apps (with a placeholder image), and the managed
   identity with its federated credential and the Contributor role on the resource group. It
   generates the database passwords into `~/.config/gymlog-azure/` (never into the repo), saves the
   GitHub secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`,
   `WORKOUTS_DATABASE_URL` and `RECORDS_DATABASE_URL`, and finally removes the temporary firewall
   rule for your own IP.
4. Merge a pull request to `main` (or re-run the latest `main` workflow). The pipeline deploys the
   real images and configuration; nothing is changed by hand in the portal after this.

| Resource | What it is |
|---|---|
| `hrahal-ieu2024-workouts`, `hrahal-ieu2024-records` | Container Apps in `hrahal-ieu2024-env`, Consumption plan, 0–1 replicas |
| `hrahal-ieu2024-sql` with `hrahal-ieu2024-workouts-db`, `hrahal-ieu2024-records-db` | Azure SQL, General Purpose serverless Gen5, 0.5–1 vCore, free offer, one contained user per database |
| `hrahal-ieu2024-ui` | Static Web App for `ui/` (blocked by region policy, see above) |
| `hrahal-ieu2024-github` | Managed identity the pipeline signs in as (GitHub OIDC, `main` only) |

See ADR-8 for the choices and costs, and `docs/diagrams.md` for the deployment diagram.

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

Design decisions: [ADR.md](ADR.md). Diagrams (Assignment 1 monolith, the split system, deployment and one database diagram per service): [docs/diagrams.md](docs/diagrams.md). Evidence for the report: [docs/evidence/](docs/evidence/).

```
services/
  workouts/               # Service 1: sessions -> exercises -> sets
    app.py                #   entry point: python app.py
    openapi.yaml          #   OpenAPI 3 description of every endpoint
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
ui/                       # static UI (index.html, app.js, style.css, config.js)
db/init.sql               # creates both databases and logins (local)
db/azure-user.sql         # creates one service's contained user on Azure SQL
infra/azure-setup.sh      # one-time Azure setup (see Deployment)
tests/integration/        # cross-seam test against the running stack
.github/workflows/ci.yml  # CI on every push/PR, CD on main
system.yaml               # machine-readable system description (system.schema.json)
ruff.toml                 # lint rules
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

Result on 2026-11-22: workouts **76 passed, 99%**; records **57 passed, 99%** (the 3 uncovered lines in each `db.py` are the database error paths of `/health`). CI fails if either is below 70%.

Lint: `ruff check .` (rules in `ruff.toml`). OpenAPI: `openapi-spec-validator services/*/openapi.yaml`.

### Cross-seam integration test

`tests/integration/` runs against the real running stack, with nothing faked: it logs a workout
through the workouts API and checks that records computes the PRs from it over HTTP, and that
deleting the workout makes records forget it too. CI runs it on every push after the unit tests.

```bash
docker compose up -d --build
pip install -r tests/integration/requirements.txt
pytest tests/integration -v
```
