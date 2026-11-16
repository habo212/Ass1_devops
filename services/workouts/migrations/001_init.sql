-- 001: the workouts tables, ported from the Assignment 1 SQLite schema.
-- INTEGER PRIMARY KEY -> INT IDENTITY, TEXT -> NVARCHAR / DATE, REAL -> FLOAT.

-- One gym visit.
CREATE TABLE workouts (
    id INT IDENTITY(1, 1) PRIMARY KEY,
    performed_on DATE NOT NULL,
    notes NVARCHAR(1000) NOT NULL DEFAULT ''
);

-- An exercise done during a workout, e.g. 'Bench Press'.
CREATE TABLE exercises (
    id INT IDENTITY(1, 1) PRIMARY KEY,
    workout_id INT NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
    name NVARCHAR(60) NOT NULL
);

-- One set of an exercise: how many reps at what weight.
CREATE TABLE sets (
    id INT IDENTITY(1, 1) PRIMARY KEY,
    exercise_id INT NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    reps INT NOT NULL CHECK (reps > 0),
    weight_kg FLOAT NOT NULL CHECK (weight_kg >= 0)
);

-- The records service asks for all sets of one exercise name, so index it.
CREATE INDEX idx_exercises_name ON exercises(name);
