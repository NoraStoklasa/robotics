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
- [ ] Each run writes a telemetry CSV and appends one summary row, with `robot.getTime()` as the time source rather than wall-clock time.
- [ ] Budget warnings appear in the log at the 50, 75 and 90 percent marks in a run that reaches them.
- [ ] A run started with an artificially reduced `TIME_BUDGET` triggers degraded mode and still stops at the identified station.
- [ ] Enabling telemetry changes total mission completion time by under 5 percent, compared against runs with it disabled.
- [ ] `.gitignore` excludes `runs/`, and the committed summary CSVs live under `docs/data/`.

## Evidence for the report
The per-run summary CSV — the source table for every completion-time figure in the evaluation chapter.

## Course reference
Workshop 8, Part 1 — reading the simulation timestep, and Part 5's practice of printing real sensor readings to drive tuning decisions.

## Out of scope
Running the test matrix itself — that is `[Sys] Run the full mission test matrix`.
