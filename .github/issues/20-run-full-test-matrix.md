---
title: "[Sys] Run the full mission test matrix"
labels: [stream:integration, type:test, priority:P0]
milestone: "M5 - Evaluation and deliverables"
stream: integration
depends_on: ["[Sys] Implement the final stop rule at the observation position", "[Sys] Log telemetry and enforce the 4:00 mission time budget"]
estimate: "L"
---

## Why
The brief requires evaluation across the three supplied missions with success, failure and completion time — and a single successful run is explicitly not sufficient evidence.

## Rubric link
Experimental evaluation, results and discussion (8 marks); Project complexity and robustness (6 marks).

## Scope
- Define the matrix: three supplied worlds (starts A, B, C) crossed with a set of mission targets covering all eight labels, including targets at boundary stations and at interior stations.
- For each cell, run the mission by editing only `config/assessment_mission.json` and opening the world — never the controller.
- Record per run: success or failure, completion time in simulation seconds, final distance to `observe`, station chosen against station expected, number of stations inspected, collision flag, and maximum proximity reading.
- Repeat each configuration at least twice to expose run-to-run variation.
- Aggregate into `docs/results_matrix.md` with a success rate and a mean completion time per world.
- Define collision precisely and state the definition: a proximity reading above the calibrated `STOP` threshold sustained beyond the avoidance response window.

- Run every matrix cell under **assessment conditions**, as the Week 8 workshop describes them: once the run starts, no menu use, no keyboard input, no pausing, no reset and no restart. Development-time interaction is fine; a matrix run with an intervention is void and must be re-run.
- Record the test dimensions separately so the results table can be read by dimension, not only as one success rate: start pose, target label, station type (boundary versus interior pocket), and world.

## Acceptance criteria
- [ ] The matrix covers all three worlds and all eight target labels, with every run recorded in a committed CSV under `docs/data/`.
- [ ] Each configuration is run at least twice, and both runs appear in the results.
- [ ] Success rate and mean completion time are reported per world and overall.
- [ ] Every run's completion time is compared against the 240 second budget, and any overrun is listed.
- [ ] No run required a controller edit; the log records the same controller file hash across every run in the matrix.

- [ ] Every recorded run states that it completed without intervention; any run that was touched is marked void and repeated.
- [ ] Success rate is broken down by start pose and by boundary-versus-interior station, not reported only as one aggregate.

## Evidence for the report
`docs/results_matrix.md` and its CSV — the main results table of the evaluation chapter, plus a completion-time bar chart per world.

## Course reference
Week 5 — evaluating a perception-driven system with quantitative success measures rather than single-run demonstrations.

## Out of scope
Analysing why individual runs failed — that is `[Sys] Document failure cases and robustness fixes`.
