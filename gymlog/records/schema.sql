-- Records domain tables. No foreign keys into workouts tables (see ADR-2, ADR-3).

-- One target weight per exercise, e.g. Bench Press -> 100 kg.
CREATE TABLE IF NOT EXISTS goals (
    exercise_name TEXT PRIMARY KEY,      -- same normalised name workouts uses
    target_kg REAL NOT NULL CHECK (target_kg > 0),
    set_on TEXT NOT NULL                 -- ISO date the goal was set
);
