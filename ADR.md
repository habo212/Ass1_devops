# Architecture Decision Records

## 1. Backend framework: Python + Flask
Date: 2026-09-27
Status: Decided
Context: I need a small web backend that runs as one process, talks to SQLite and is easy to split into services later. Python is the language I'm most comfortable with, so I need to be able to explain every line.
Decision: Use Python with Flask and the built-in `sqlite3` module, organised with an app factory (`create_app`) so each feature domain can be registered separately.
Alternatives considered: Django: rejected because its admin, ORM and project structure are much more than a two-domain app needs, and it would add a lot of code I didn't write myself. FastAPI: a reasonable option, but async and Pydantic models don't buy me anything at this scale, and I know Flask better.
Consequences: Very little boilerplate, and the app starts in under a second. Flask doesn't give me validation or an ORM, so I have to write input checks and SQL myself.
