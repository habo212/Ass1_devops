# Architecture Decision Records

## 1. Backend framework: Python + Flask
Date: 2026-09-27
Status: Decided
Context: I need a small web backend that runs as one process, talks to SQLite and is easy to split into services later. Python is the language I'm most comfortable with, so I need to be able to explain every line.
Decision: Use Python with Flask and the built-in `sqlite3` module, organised with an app factory (`create_app`) so each feature domain can be registered separately.
Alternatives considered: Django: rejected because its admin, ORM and project structure are much more than a two-domain app needs, and it would add a lot of code I didn't write myself. FastAPI: a reasonable option, but async and Pydantic models don't buy me anything at this scale, and I know Flask better.
Consequences: Very little boilerplate, and the app starts in under a second. Flask doesn't give me validation or an ORM, so I have to write input checks and SQL myself.

## 2. Domain seam: records only talks to workouts through a two-function public interface
Date: 2026-09-30
Status: Decided
Context: The app has two domains, Workouts (logging sessions, exercises and sets) and Records & Progress (PRs, 1RM estimates, goals). Records needs workouts' sets to do anything, but it should be possible to move records into its own service later without rewriting it.
Decision: `gymlog/workouts/__init__.py` is the only thing other domains may import from workouts. It exposes `get_sets_for_exercise(name)` and `normalize_exercise_name(name)`, which return plain dicts and strings, never SQL rows or Flask objects. The dependency goes one way only: records imports workouts, never the other way round. Each domain has its own `service.py`, `repository.py`, `routes.py` and `schema.sql`.
Alternatives considered: Letting records write its own SQL joins over the workouts tables: less code, but then records depends on workouts' table layout and breaks on any schema change. Having workouts push new sets into records whenever a workout is saved: keeps PRs precomputed, but couples workouts to records in the other direction too, so neither could be split out alone.
Consequences: To split records out later, I only have to replace those two imported functions with HTTP calls to a workouts service (e.g. `GET /api/workouts/exercises/<name>/sets`). The cost is that records recomputes PRs from all sets on every request, which is fine for one person's log but would need caching at large scale.

## 3. SQLite schema: workouts → exercises → sets, records linked by exercise name
Date: 2026-09-28
Status: Decided
Context: A workout has several exercises and each exercise has several sets, and the records domain needs to find every set for one exercise to detect PRs. I also want the records domain to be splittable into its own service later, so its data can't be tightly tied to the workouts tables.
Decision: The workouts domain owns three tables, `workouts` 1→N `exercises` 1→N `sets`, joined by foreign keys with `ON DELETE CASCADE`. The records domain will own its own table and refer to exercises only by their name (plain text, no foreign key into the workouts tables).
Alternatives considered: One flat `sets` table with the date and exercise name on every row: simpler, but it repeats the date and notes on every set and can't represent "one visit" cleanly. A separate `exercise_types` lookup table with a foreign key from records: stricter, but it would chain the records tables to workouts tables, so they couldn't be moved into a different database later.
Consequences: Deleting a workout removes its exercises and sets automatically. Because records matches by name, the name must be normalised the same way everywhere ("bench press" = "Bench Press"), which the workouts service has to enforce.

## 4. Testing approach: pure service functions first, then routes on a temporary database
Date: 2026-10-01
Status: Decided
Context: The brief requires at least 70% coverage of the core business logic of both domains. Most of the real rules (input validation, name normalisation, PR detection, the Epley 1RM estimate) live in the two `service.py` files, while routes and repositories mostly pass data along.
Decision: Test every rule in `workouts/service.py` and `records/service.py` directly with plain Python values (using `pytest.mark.parametrize` for the bad inputs and a fixed `today` date), then add a smaller set of route tests through Flask's test client. A `conftest.py` fixture gives each test a fresh SQLite file in pytest's `tmp_path`, so the real SQL runs without touching `data/`.
Alternatives considered: Mocking the database in route tests: faster, but it would only prove the mocks work, not that my SQL and foreign keys do. Browser/end-to-end tests (e.g. Selenium): too heavy for the value they add here, and they would need extra packages.
Consequences: Coverage is 100%, and the SQLite schema (CHECK constraints, cascades) is exercised for real. The route tests are thinner: they cover the happy path plus 400/404 cases, not every combination, and there are no tests for concurrent writes because the app is single-user.

## 5. Not built: user accounts and login
Date: 2026-10-02
Status: Decided
Context: Gym Log is a personal training log, and the brief lets me decide whether to add authentication. Login would touch every table and every route, and the deadline is one week, so I had to decide early whether it was worth it.
Decision: No accounts or login. The app has one implicit user, and anyone who can reach the port can read and edit the log.
Alternatives considered: Flask-Login with hashed passwords and a `users` table: the standard approach, but it adds a `user_id` foreign key to `workouts` and `goals`, session handling, CSRF protection on every form and its own tests, roughly doubling the work for a feature that doesn't help the two domains I'm graded on. HTTP basic auth from an environment variable: much less code, but it would still be shared by everyone, so it protects the app without actually separating users.
Consequences: The app stays small and both domains could be finished and tested properly. Before the Azure deployment in Assignment 2, the app must not be left publicly reachable without at least network restrictions, and adding real users later means adding `user_id` to the `workouts` and `goals` tables.
