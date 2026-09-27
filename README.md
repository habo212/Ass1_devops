# Gym Log

A workout logger: record gym sessions (exercises, sets, reps, weight) and automatically track personal records (PRs) and progress per exercise.

## Run it

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://localhost:8000/health. It should return `{"status": "ok"}`.

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8000` | Port the server listens on (always binds `0.0.0.0`) |
| `DATA_DIR` | `./data` | Folder for the SQLite file. The DB lives at `$DATA_DIR/gymlog.db` |

## Tests

_Coming soon._
