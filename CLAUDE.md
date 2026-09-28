# Context for Claude

## Who I am and how to help me
I'm Habib, a student at IE University, taking Software Development & DevOps (prof. Borja Serra). This repo is my Individual Assignment 1 (deadline 2026-10-04 23:59). AI use is allowed and expected, but I'm tested closed-book, on paper on my own code. That score multiplies my whole grade, so understanding matters more than speed.

How to work with me:

* Teach, don't just generate. Before writing code, tell me in 2–3 sentences what we're about to build and why. After writing it, explain it using my actual function and variable names.
* Keep code simple and readable: plain Flask + `sqlite3`, no clever tricks, and nothing I couldn't rewrite myself.
* Work in small steps that each make one meaningful commit. Suggest a descriptive commit message ("Add X so that Y"), never "update"/"fix"/"WIP".
* Claude may commit and push for me, but only real work done that day, after I've seen what's in it. Never backdate, batch-fake, or commit on a timer.
* At the end of each session: (1) quiz me with 3 questions like the in-class check and correct my answers, (2) remind me to add my `AI_USAGE.md` row. I write the "In my own words" column myself. You can check it for accuracy.
* If I ask for something that breaks the rules below, tell me.

## The app: Gym Log
Python 3 + Flask + SQLite, one process.

* Domain 1, Workouts (`gymlog/workouts/`): log sessions → exercises → sets (reps, weight). CRUD + validation.
* Domain 2, Records & Progress (`gymlog/records/`): detect personal records (heaviest weight, best estimated 1RM using the Epley formula `w * (1 + reps/30)`) per exercise, and show progress over time.
* The seam: `records` never imports workouts internals. It only uses one small function (e.g. `get_sets_for_exercise`) or its own tables, so it could become a separate service later. Keep this clean. It's graded.
* Structure: each domain has `service.py` (pure business logic, the thing we test), `repository.py` (SQL), and `routes.py` (a Flask blueprint registered in `create_app`).

## Hard rules from the brief (don't break these)

* Single process. SQLite only, at `$DATA_DIR/gymlog.db` (default `./data`). Create tables automatically on startup, with no manual migration step.
* One `requirements.txt` at the root. Keep it to about 12 third-party packages or fewer. About 15–50 files.
* No Dockerfile, docker-compose, GitHub Actions, IaC, Redis/Celery, or real deployment.
* Started by `python app.py`. Binds `0.0.0.0`, reads the port from `PORT`, and all config comes from environment variables. It must not need a `.env` file or any interactive setup.
* Tests: pytest, ≥70% coverage on core business logic of both domains. Command: `pytest --cov=gymlog --cov-report=term-missing`. Put the result in the README.
* `ADR.md`: exactly 5 entries in the given format (Date / Status / Context / Decision / Alternatives considered / Consequences), added across ≥3 different commit dates: 1) framework, 2) how the domains are separable, 3) SQLite schema/relationship (must match the DB diagram), 4) testing approach, 5) one thing I chose not to build.
* `AI_USAGE.md`: one row per meaningful AI interaction: Date/commit | Tool | Prompt | Accepted/Modified/Rejected | What changed & why | In my own words.
* Commits: ≥12 commits over ≥6 different days, no day >40% of commits, pushed to GitHub.
* Report (4–5 pages, separate): SDLC model + SMART goals, architecture diagram, DB schema diagram, README, AI disclosure statement.

## Plan and progress (update this as we go)

* ✅ Sun Sep 27: Flask skeleton (`app.py`, `gymlog/__init__.py` with `create_app`, `config.py`), README stub, ADR-1 (Flask), AI_USAGE.md. Idea sent to prof for approval.
* ✅ Mon Sep 28: `gymlog/db.py` (connection + schema init on startup), workouts schema, workouts `service.py` logic. ADR-3 (schema).
* Tue Sep 29: workouts `repository.py` + `routes.py` blueprint, first pytest tests (`tests/conftest.py` using a temp `DATA_DIR`).
* Wed Sep 30: records domain logic (PR detection, Epley 1RM, progress). ADR-2 (domain seam).
* Thu Oct 1: records routes + tests, reach ≥70% coverage. ADR-4 (testing).
* Fri Oct 2: simple HTML frontend (Jinja templates), check the §7 contract from a fresh clone. ADR-5 (what I didn't build, e.g. auth/login).
* Sat Oct 3: README final, architecture + DB diagrams, report draft, AI disclosure statement.
* Sun Oct 4: buffer, final review, submit.
