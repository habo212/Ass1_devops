-- 001: the records table, ported from the Assignment 1 SQLite schema.
-- No foreign key into workouts: those tables live in another database (ADR-6).

-- One target weight per exercise, e.g. Bench Press -> 100 kg.
CREATE TABLE goals (
    exercise_name NVARCHAR(60) NOT NULL PRIMARY KEY,  -- same normalised name workouts uses
    target_kg FLOAT NOT NULL CHECK (target_kg > 0),
    set_on DATE NOT NULL
);
