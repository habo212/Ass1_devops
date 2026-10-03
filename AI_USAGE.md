# AI Usage Log

| Date/commit | Tool | Prompt | Disposition (Accepted/Modified/Rejected) | What changed & why (if modified) | In my own words, how this works |
|---|---|---|---|---|---|
| 2026-09-27 / skeleton commit | Claude | "Help me pick an app idea and plan the assignment day by day; set up a Flask skeleton that satisfies the §7 deployment contract" | Accepted | | TODO (Habib) |
| 2026-09-28 / 99a758b, 67a81e2 | Claude Code | "Can we do day 2 now" (db.py with schema init on startup, workouts schema, workouts service.py, ADR-3) | Accepted |  | TODO (Habib) |
| 2026-09-29 / ff68d21 | Claude Code | "Can you commit [today's work]" (workouts repository.py + routes.py blueprint) | Accepted |  | TODO (Habib) |
| 2026-09-30 / f1b7f9d | Claude Code | "Commit 2" (pytest suite for workouts: conftest with temp DATA_DIR, service and route tests) | Modified | pytest couldn't import `gymlog`, so a `pytest.ini` with `pythonpath = .` was added. One sloppy assertion with an `or` fallback was rewritten to check the set directly. | TODO (Habib) |
| 2026-09-30 / 2b29551, 008f46c | Claude Code | "Do the 2 commits for today" (records domain: PR detection, Epley 1RM, progress, ADR-2) | Modified | Chose a `goals` table so records owns its own SQLite data. The seam test failed on a comment in `records/routes.py` that mentioned `workouts.repository`; the comment was reworded. Asked to remove the Claude trailer from earlier commits: rejected, because force-pushing would reset push timestamps and break the 6-day requirement. | TODO (Habib) |
| 2026-10-01 / 319ebf4 | Claude Code | "Can you do the commits please" (ADR-4, README tests/coverage section, this log) | Accepted |  | TODO (Habib) |
| 2026-10-01 / e933208 | Claude Code | "Can you do the commits please" (workouts HTML pages) | Accepted | | TODO (Habib) |
| 2026-10-02 / 41e486c, 2c691a8 | Claude Code | "Can you commit for today pls" (records HTML page, ADR-5, fresh-clone check) | Modified | The PR/progress/goal code was duplicated between the API and the new page, so it was moved into `records/summary.py` and both use it. Fresh clone from GitHub installed, started with `python app.py` and passed all 69 tests with no fixes needed. | TODO (Habib) |
| 2026-10-03 / diagrams commit | Claude Code | "Can you do the commit for today pls" (architecture + DB schema diagrams) | Accepted | | TODO (Habib) |
