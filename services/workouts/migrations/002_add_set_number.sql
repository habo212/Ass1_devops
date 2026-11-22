-- 002: number the sets of each exercise (1, 2, 3...) instead of relying on id order.
-- Data-changing: every set that already exists is given its number from the order it was
-- logged in. The column has a default so the previous image, which doesn't know about it,
-- can still insert sets while a deploy rolls out (ADR-7).

ALTER TABLE sets ADD set_number INT NOT NULL CONSTRAINT df_sets_set_number DEFAULT 0;
GO

-- Backfill: the n-th set of an exercise (by id) gets number n.
WITH numbered AS (
    SELECT set_number, ROW_NUMBER() OVER (PARTITION BY exercise_id ORDER BY id) AS n
    FROM sets
)
UPDATE numbered SET set_number = n;
