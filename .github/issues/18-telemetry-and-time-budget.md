---
title: "[Sys] Log telemetry and enforce the 4:00 mission time budget"
labels: [stream:integration, type:feature, priority:P0]
milestone: "M4 - Mission integration"
stream: integration
depends_on: ["[Sys] Implement the mission state machine"]
estimate: "M"
---

## Why
A mission that has not succeeded by 4:00 is recorded as incomplete, and the report's timing results have to come from logs rather than a stopwatch.

## Rubric link
Experimental evaluation, results and discussion (8 marks); Live code/system demonstration (10 marks).

## Scope
- Add a telemetry module writing one CSV row per logging interval: simulation time from `robot.getTime()`, state, pose, current station, identification label and confidence, active behaviour, and maximum proximity reading.
- Write one summary line per run: start id, mission target, station chosen, final distance to `observe`, completion time, and success or failure.
- Track elapsed simulation time against a `TIME_BUDGET` of 240 seconds, and log a warning at 50, 75 and 90 percent consumed.
- Add a degraded mode: when the budget is nearly spent and a confident identification exists, go straight to that station's `observe` rather than continuing to inspect others.
- Write logs under `runs/` with a timestamped filename, and keep `runs/` out of version control while committing the summary CSVs used in the report.
- Keep logging cheap enough not to slow the control loop; log at an interval, not every timestep.

## Acceptance criteria
- [x] Each run writes a telemetry CSV and appends one summary row, with `robot.getTime()` as the time source rather than wall-clock time.
- [x] Budget warnings appear in the log at the 50, 75 and 90 percent marks in a run that reaches them.
- [x] A run started with an artificially reduced `TIME_BUDGET` triggers degraded mode and still stops at the identified station.
- [x] Enabling telemetry changes total mission completion time by under 5 percent, compared against runs with it disabled.
- [x] `.gitignore` excludes `runs/`, and the committed summary CSVs live under `docs/data/`.

## Evidence for the report
The per-run summary CSV — the source table for every completion-time figure in the evaluation chapter.

Real Webots runs, world A (start A), target `soda_can` at S1:

| Test | `TIME_BUDGET` | Result |
|---|---|---|
| Normal run | 240s (default) | Summary row written correctly: `start_id=A, station=S1, final_distance=0.043, completion_time=144.58, outcome=SUCCESS`. Interval CSV appeared under `runs/`. |
| Budget warnings | 100s | `TIME BUDGET 50%/75%/90% consumed` printed at 50.0s/75.0s/90.0s exactly. |
| Timeout | 100s | No target sighting occurred before the budget elapsed (only confirmed non-target labels); mission correctly reached `FAILED` with outcome `TIMEOUT` at 100.0s, not stuck looping. |
| Degraded mode | 100s, with a debug-seeded unconfirmed sighting (temporary test-only hook, since real vision reaches 3-frame consensus almost instantly once a poster is in view, leaving no natural window where a sighting exists but isn't confirmed) | At the 90% mark (90.0s), `PLAN`/mid-`NAVIGATE` toward a different station was interrupted; mission switched straight to `GOTO_OBSERVE` for the candidate station and completed `FINAL_ALIGN`/`FINAL_HOLD` within the remaining budget: distance 0.088 m, heading error 0.011 rad. |

Bug found and fixed during this verification: `_check_degraded_mode` was originally only evaluated inside `PLAN`, so a station already being visited when the 90% mark hit (mid-`NAVIGATE`/`OBSERVE`/`IDENTIFY`) wasn't interrupted, risking `TIMEOUT` before ever redirecting. Fixed by making it a cross-cutting check evaluated every step (like the budget check itself) instead of only at `PLAN` decision points -- see `docs/change_log.md`.

**Telemetry overhead:** ran world A with `TELEMETRY_ENABLED=0` and compared against the earlier telemetry-on run. Both reached `FINAL STOP` at the identical final pose and simulated completion time (144.58s) -- a 0% difference. Webots advances simulated time by a fixed timestep regardless of how much real CPU time the controller spends per step, so logging every 10th step (small CSV row, no blocking I/O of consequence) cannot shift `robot.getTime()` at all; the two runs being pose-identical to 15+ decimal places confirms the simulation is otherwise fully deterministic between them.

All 5 acceptance criteria met.

## Course reference
Workshop 8, Part 1 — reading the simulation timestep, and Part 5's practice of printing real sensor readings to drive tuning decisions.

## Out of scope
Running the test matrix itself — that is `[Sys] Run the full mission test matrix`.
