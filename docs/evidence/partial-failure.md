# Evidence: partial failure (workouts stopped)

Local compose stack, 2026-11-22 11:08 (CET). Records needs workouts' sets for every records view
(the cross-seam flow); its goal is its own data.

## Both services up

```
$ curl localhost:8002/api/records/Deadlift
{"exercise":"Deadlift","goal":{"exercise_name":"Deadlift","percent":91,"set_on":"2026-11-22","target_kg":180.0},
 "personal_records":{"best_1rm":{"estimated_1rm":163.3,...},"heaviest":{...,"weight_kg":140.0}},"progress":[...]}
HTTP 200 in 0.068s
```

## `docker compose stop workouts`

```
$ curl localhost:8002/api/records/Deadlift
{"error":"the workouts service is unavailable, so records can't be calculated right now",
 "exercise":"Deadlift","goal":{"exercise_name":"Deadlift","set_on":"2026-11-22","target_kg":180.0}}
HTTP 503 in 0.063s

$ curl localhost:8002/health
{"db":"ok","status":"ok","version":"dev"}
HTTP 200
```

Records log lines (one per request):

```
records-1  | 2026-11-22 11:08:30,056 INFO requests: GET /api/records/Deadlift 200 64.7ms
records-1  | 2026-11-22 11:08:31,137 INFO requests: GET /api/records/Deadlift 503 60.8ms
records-1  | 2026-11-22 11:08:31,160 INFO requests: GET /health 200 10.1ms
```

What this shows: the cross-seam flow fails in a designed way: a clear JSON error plus the goal records
owns, in 63 ms, with no stack trace and no hang. Here the connection is refused at once; a workouts
service that is slow instead of down is cut off by `WORKOUTS_TIMEOUT_S`. Records' own `/health`
stays 200, because health reports the service's own state, not the other service's.
