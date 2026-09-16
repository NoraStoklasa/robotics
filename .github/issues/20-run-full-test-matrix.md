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
**Rescoped 2026-09-16** after checking the actual Week 8 brief (`notes_for_project/workshop8-p3-group-project.pdf`) against this issue's original wording. The brief's own testing-strategy section asks only for a **"small test matrix"** covering the dimensions start/target/station-type/repeated-run — it does not ask for every target crossed with every world crossed with two repeats each (the original 48-run scope below was this issue's own addition, not a brief requirement). Scaled down accordingly to keep the evidence real without multi-hour simulation time:

- Matrix: the three **official, unmodified** supplied worlds (`worlds/training_start_{A,B,C}.wbt`) crossed with **6 representative targets** — 3 at boundary stations and 3 at interior stations — chosen to span the confidence range already seen in issue 19's shuffled-world testing (e.g. include at least one target already known to be borderline, such as `wall_clock`, alongside targets already known to work cleanly, such as `soda_can`).
- For each cell, run the mission by editing only `config/assessment_mission.json` and opening the world — never the controller.
- Record per run: success or failure, completion time in simulation seconds, final distance to `observe`, station chosen against station expected, number of stations inspected, and the per-frame confidence trace at the correct station (used as the collision/robustness signal available from the controller's own telemetry).
- Repeat the borderline target across all three worlds a second time to check run-to-run consistency, rather than repeating every cell twice.
- Aggregate into `docs/results_matrix.md` with a success rate and a mean completion time per world.

- Run every matrix cell under **assessment conditions**, as the Week 8 workshop describes them: once the run starts, no menu use, no keyboard input, no pausing, no reset and no restart. Development-time interaction is fine; a matrix run with an intervention is void and must be re-run.
- Record the test dimensions separately so the results table can be read by dimension, not only as one success rate: start pose (world), target label, and station type (boundary versus interior pocket).

## Acceptance criteria
- [ ] The matrix covers all three official worlds and at least 6 target labels spanning both boundary and interior stations, with every run recorded in a committed CSV under `docs/data/`.
- [ ] The borderline target is run at least twice per world to check consistency, and both runs appear in the results.
- [ ] Success rate and mean completion time are reported per world and overall.
- [ ] Every run's completion time is compared against the 240 second budget, and any overrun is listed.
- [ ] No run required a controller edit.

- [ ] Every recorded run states that it completed without intervention; any run that was touched is marked void and repeated.
- [ ] Success rate is broken down by start pose (world) and by boundary-versus-interior station, not reported only as one aggregate.

## Evidence for the report
`docs/results_matrix.md` and its CSV — the main results table of the evaluation chapter, plus a completion-time bar chart per world.

## Course reference
Week 5 — evaluating a perception-driven system with quantitative success measures rather than single-run demonstrations.

## Out of scope
Analysing why individual runs failed — that is `[Sys] Document failure cases and robustness fixes`.
