# Gym Log diagrams

GitHub renders the Mermaid blocks below. Part 1 is the Assignment 1 monolith (the "before"),
as it was on 2026-10-03. Part 2 is the split system as deployed for Assignment 2 (the "after").

# Part 1: Assignment 1 monolith (before)

## Architecture

One Python process started by `python app.py`. `create_app()` loads config from environment
variables, runs `init_db` (creates all tables), and registers four blueprints, two per domain.
Each domain is split into routes/pages (HTTP), `service.py` (pure logic) and `repository.py` (SQL).
The records domain reaches workouts data **only** through the public interface in
`gymlog/workouts/__init__.py` (ADR-2).

```mermaid
flowchart TB
    user["Browser / curl"] -->|"HTTP on 0.0.0.0:$PORT"| app

    subgraph process["Single process: python app.py"]
        app["create_app()<br/>config.py: PORT, DATA_DIR<br/>db.py: init_db, get_db"]

        subgraph W["Domain 1: Workouts (gymlog/workouts)"]
            wroutes["routes.py<br/>/api/workouts (JSON)"]
            wpages["pages.py<br/>/ and /workouts/&lt;id&gt; (HTML)"]
            wservice["service.py<br/>validate_workout, parse_exercise_lines,<br/>normalize_exercise_name"]
            wrepo["repository.py<br/>create/get/update/delete_workout"]
            wpublic["__init__.py (public interface)<br/>get_sets_for_exercise, normalize_exercise_name"]
        end

        subgraph R["Domain 2: Records & Progress (gymlog/records)"]
            rroutes["routes.py<br/>/api/records/&lt;name&gt; (JSON)"]
            rpages["pages.py<br/>/records/&lt;name&gt; (HTML)"]
            rsummary["summary.py<br/>load_summary"]
            rservice["service.py<br/>epley_1rm, find_personal_records,<br/>progress_by_date, goal_percent"]
            rrepo["repository.py<br/>get/set/delete_goal"]
        end

        app --> wroutes & wpages & rroutes & rpages
        wroutes & wpages --> wservice
        wroutes & wpages --> wrepo
        wpublic --> wrepo & wservice
        rroutes & rpages --> rsummary
        rsummary --> rservice
        rsummary --> rrepo
        rsummary -->|"only allowed link<br/>between domains"| wpublic
    end

    wrepo --> db[("SQLite<br/>$DATA_DIR/gymlog.db")]
    rrepo --> db
```

## Database schema

Created on startup from `gymlog/workouts/schema.sql` and `gymlog/records/schema.sql` (ADR-3).
`goals` belongs to the records domain and has **no foreign key** into the workouts tables: it is
matched to exercises by the normalised name, so records could move to its own database later.

```mermaid
erDiagram
    workouts ||--o{ exercises : "has (ON DELETE CASCADE)"
    exercises ||--|{ sets : "has (ON DELETE CASCADE)"
    goals |o..o{ exercises : "exercise_name = name (no FK)"

    workouts {
        INTEGER id PK
        TEXT performed_on "ISO date"
        TEXT notes
    }
    exercises {
        INTEGER id PK
        INTEGER workout_id FK
        TEXT name "normalised, indexed"
    }
    sets {
        INTEGER id PK
        INTEGER exercise_id FK
        INTEGER reps "CHECK > 0"
        REAL weight_kg "CHECK >= 0"
    }
    goals {
        TEXT exercise_name PK
        REAL target_kg "CHECK > 0"
        TEXT set_on "ISO date"
    }
```

# Part 2: the split system (after, Assignment 2)

Matches the code and the Azure deployment as of 2026-11-22.

## Architecture after the split

Two services, each in its own container with its own database and its own login, which can't open
the other database. The only call across the seam is records asking workouts for one exercise's sets
over HTTP, with a timeout; if workouts doesn't answer, records returns 503 with the goal it owns
(ADR-6, ADR-10). The static UI calls both services from the browser; CORS lets only its origin in.

```mermaid
flowchart LR
    browser["Browser<br/>static UI (ui/: index.html, app.js, config.js)"]

    subgraph W["workouts service (services/workouts)"]
        wapi["Flask + gunicorn :8000<br/>/api/workouts, /health"]
    end
    subgraph R["records service (services/records)"]
        rapi["Flask + gunicorn :8000<br/>/api/records, /health"]
    end

    browser -->|"HTTPS, CORS = UI origin"| wapi
    browser -->|"HTTPS, CORS = UI origin"| rapi
    rapi -->|"GET /api/workouts/exercises/{name}/sets<br/>WORKOUTS_URL, timeout WORKOUTS_TIMEOUT_S<br/>(the seam)"| wapi

    wapi -->|"workouts_user<br/>DATABASE_URL"| wdb[("workouts DB<br/>workouts, exercises, sets")]
    rapi -->|"records_user<br/>DATABASE_URL"| rdb[("records DB<br/>goals")]
```

Locally, `docker compose up --build` runs the same picture: `ui` (nginx:1.27-alpine serving `ui/`,
port 8080), `workouts` (8001), `records` (8002), one `sqlserver` container holding both databases,
and the one-off `db-init` job that creates the databases and logins (`db/init.sql`).

## Deployment

```mermaid
flowchart LR
    dev["git push / pull request"] --> gh["GitHub<br/>habo212/Ass1_devops"]
    gh --> ci["GitHub Actions: ci.yml<br/>lint, validate, test x2 (SQL Server container),<br/>integration (compose), build x2"]
    ci -->|"push to main only,<br/>all jobs green"| cd["deploy job<br/>OIDC sign-in as hrahal-ieu2024-github"]
    ci -->|"docker push :&lt;sha&gt; (main only)"| ghcr[("GHCR<br/>ghcr.io/habo212/gymlog-workouts<br/>ghcr.io/habo212/gymlog-records")]

    subgraph AZ["Azure for Students: resource group rg-sdd-3a, Germany West Central"]
        subgraph ENV["Container Apps environment hrahal-ieu2024-env (Consumption)"]
            caw["hrahal-ieu2024-workouts<br/>0-1 replicas"]
            car["hrahal-ieu2024-records<br/>0-1 replicas"]
        end
        subgraph SQL["Azure SQL server hrahal-ieu2024-sql"]
            dbw[("hrahal-ieu2024-workouts-db<br/>serverless, 0.5-1 vCore")]
            dbr[("hrahal-ieu2024-records-db<br/>serverless, 0.5-1 vCore")]
        end
        swa["Storage static website hrahalieu2024ui<br/>ui/ files + config.js (ADR-8)"]
        mi["Managed identity hrahal-ieu2024-github<br/>Contributor on rg-sdd-3a"]
    end

    cd -->|"az containerapp update --image :&lt;sha&gt;"| caw & car
    ghcr -->|"image pull"| caw & car
    cd -.->|"upload ui/ + generated config.js"| swa
    cd -->|"GET /health until version = sha"| caw & car
    caw --> dbw
    car --> dbr
    car -->|"HTTPS, the seam"| caw
```

## Database per service (matches the migrations)

`workouts` database, from `services/workouts/migrations/001_init.sql` and `002_add_set_number.sql`:

```mermaid
erDiagram
    workouts ||--o{ exercises : "has (ON DELETE CASCADE)"
    exercises ||--|{ sets : "has (ON DELETE CASCADE)"

    workouts {
        INT id PK "IDENTITY"
        DATE performed_on
        NVARCHAR notes "max 1000, default ''"
    }
    exercises {
        INT id PK "IDENTITY"
        INT workout_id FK
        NVARCHAR name "max 60, normalised, indexed"
    }
    sets {
        INT id PK "IDENTITY"
        INT exercise_id FK
        INT reps "CHECK > 0"
        FLOAT weight_kg "CHECK >= 0"
        INT set_number "002: 1, 2, 3... per exercise, default 0"
    }
    schema_migrations {
        NVARCHAR version PK "e.g. 002_add_set_number.sql"
        DATETIME2 applied_at
    }
```

`records` database, from `services/records/migrations/001_init.sql`. `goals.exercise_name` matches
`exercises.name` in the other database by value only: no foreign key can cross databases, so the
link is kept in code (ADR-7).

```mermaid
erDiagram
    goals {
        NVARCHAR exercise_name PK "max 60, same normalised name as workouts"
        FLOAT target_kg "CHECK > 0"
        DATE set_on
    }
    schema_migrations {
        NVARCHAR version PK
        DATETIME2 applied_at
    }
```
