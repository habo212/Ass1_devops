# Gym Log diagrams

Both diagrams match the code as of 2026-10-03. GitHub renders the Mermaid blocks below.

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
