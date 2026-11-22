# Evidence: data-changing migration 002 on Azure

Migration `services/workouts/migrations/002_add_set_number.sql` adds `sets.set_number` and
backfills it for every set that already exists (1, 2, 3… within each exercise, in the order
the sets were logged). Queries below were run against the live Azure database
`hrahal-ieu2024-workouts-db` on `hrahal-ieu2024-sql`, as the server admin, with `sqlcmd`.

## Before (2026-11-22 10:55 UTC, image d2de557…)

```
version       applied_at
001_init.sql  2026-11-22 01:59:53.0325062

COLUMN_NAME  DATA_TYPE        -- table sets
id           int
exercise_id  int
reps         int
weight_kg    float

workout_id  exercise        set_id  reps  weight_kg
1           Squat           1       5     100.0
1           Squat           2       3     110.0
2           Bench Press     3       8     60.0
2           Bench Press     4       6     65.0
2           Bench Press     5       5     70.0
2           Overhead Press  6       8     40.0
2           Overhead Press  7       8     40.0
```

## Deployment run

PR #8 merged to `main` as `0e67352`; CD run
https://github.com/habo212/Ass1_devops/actions/runs/45014960761 (all jobs green, health check on `0e67352`).

## Startup log line (Container App `hrahal-ieu2024-workouts`, `az containerapp logs show`)

```
2026-11-22 11:00:25,657 INFO workouts.migrate: applying migration 002_add_set_number.sql
2026-11-22 11:00:25,724 INFO workouts.migrate: migrations up to date: 1 applied now, 1 already applied
```

For comparison, a restart of the previous image earlier the same day applied nothing:

```
2026-11-22 10:55:32,660 INFO workouts.migrate: migrations up to date: 0 applied now, 1 already applied
```

## After (2026-11-22 11:02 UTC, image 0e67352…)

```
version                 applied_at
001_init.sql            2026-11-22 01:59:53.0325062
002_add_set_number.sql  2026-11-22 11:00:25.7866317

COLUMN_NAME  DATA_TYPE        -- table sets
id           int
exercise_id  int
reps         int
weight_kg    float
set_number   int

workout_id  exercise        set_id  set_number  reps  weight_kg
1           Squat           1       1           5     100.0
1           Squat           2       2           3     110.0
2           Bench Press     3       1           8     60.0
2           Bench Press     4       2           6     65.0
2           Bench Press     5       3           5     70.0
2           Overhead Press  6       1           8     40.0
2           Overhead Press  7       2           8     40.0
```

All 7 rows that existed before are still there with the same values, and each got its
position within its exercise. `GET /health` after the deploy:
`{"db":"ok","status":"ok","version":"0e67352af9232ab02d52c980a182f68e9faadf9b"}`.
