-- Workouts domain tables. Run on every startup; IF NOT EXISTS makes that safe.

-- One gym visit.
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY,
    performed_on TEXT NOT NULL,          -- ISO date, e.g. '2026-09-28'
    notes TEXT NOT NULL DEFAULT ''
);

-- An exercise done during a workout, e.g. 'Bench Press'.
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY,
    workout_id INTEGER NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
    name TEXT NOT NULL
);

-- One set of an exercise: how many reps at what weight.
CREATE TABLE IF NOT EXISTS sets (
    id INTEGER PRIMARY KEY,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    reps INTEGER NOT NULL CHECK (reps > 0),
    weight_kg REAL NOT NULL CHECK (weight_kg >= 0)
);

-- The records domain looks up all sets for one exercise name, so index it.
CREATE INDEX IF NOT EXISTS idx_exercises_name ON exercises(name);
