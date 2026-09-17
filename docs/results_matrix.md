# Full mission test matrix (Issue #20)

## Scope

Three official worlds (`training_start_A/B/C.wbt`) crossed with all eight
mission targets, each configuration run **at least twice**, for
**48 runs minimum**. Only `config/assessment_mission.json` is edited between
runs — the controller is never touched, and the controller file hash is
recorded for every run to prove it.

| World | Start pose | Boundary stations | Interior stations |
|---|---|---|---|
| A | (-1.45, 0.0, 0.0) | S1, S3, S5, S7 | S2, S4, S6, S8 |
| B | (0.0, -1.45, 90°) | S1, S3, S5, S7 | S2, S4, S6, S8 |
| C | (1.45, 0.9, 180°) | S1, S3, S5, S7 | S2, S4, S6, S8 |

Target → expected station (identical across A/B/C in the official worlds):

| Target | Station | Type |
|---|---|---|
| soda_can | S1 | boundary |
| coffee_mug | S2 | interior |
| backpack | S3 | boundary |
| fire_extinguisher | S4 | interior |
| camera | S5 | boundary |
| running_shoe | S6 | interior |
| headphones | S7 | boundary |
| wall_clock | S8 | interior |

## Collision definition

A collision is a proximity reading above the calibrated `STOP` threshold
(see `docs/proximity_calibration.md`), sustained beyond the avoidance
response window — a single spike below that duration is not counted.

## Assessment conditions

Every run below must be started and left alone until it reaches `STOP` or
`FAILED`/timeout: no menu use, no keyboard input, no pausing, no reset, no
restart. Any run that was touched is void and must be repeated; log the
touched run anyway with `void_reason` filled in, then add a fresh repeat row.

## Controller hash

Record once per matrix session, before the first run:

```
shasum -a 256 controllers/group_project_controller/group_project_controller.py
```

Hash for this matrix run: `TODO`

If this changes mid-matrix, the matrix is invalid from that point on — stop
and restart the whole matrix under the new hash.

## Run log

Full per-run data lives in
[`docs/data/results_matrix.csv`](data/results_matrix.csv) (48 pre-populated
rows — fill in the result columns as each run completes; do not delete rows,
add a new row for any void-run repeat). Columns:

`run_id, world, start_pose, target, expected_station, station_type, repeat, run_timestamp, controller_hash, outcome, completion_time_s, over_budget_240s, final_distance_to_observe_m, station_chosen, station_match_expected, stations_inspected_count, collision_flag, max_proximity_reading, intervention_free, void_reason`

- `outcome`: `SUCCESS` / `FAILED` / `TIMEOUT`
- `over_budget_240s`: `YES`/`NO`, comparing `completion_time_s` to the 240 s budget
- `intervention_free`: `YES`/`NO` — `NO` means this row is void
- `void_reason`: blank unless `intervention_free = NO`, e.g. `"paused at 90s to check camera feed"`

## Summary — fill in once all 48 runs are logged

### By world

| World | Runs | Successes | Success rate | Mean completion time (s) | Runs over 240 s budget |
|---|---|---|---|---|---|
| A | 16 | | | | |
| B | 16 | | | | |
| C | 16 | | | | |
| **Overall** | **48** | | | | |

### By start pose

(identical to "by world" in this project, since each world = one fixed start
pose — kept as a separate table to satisfy the "read by dimension" requirement)

| Start pose | Runs | Successes | Success rate |
|---|---|---|---|
| A | 16 | | |
| B | 16 | | |
| C | 16 | | |

### By station type (boundary vs interior)

| Station type | Runs | Successes | Success rate |
|---|---|---|---|
| Boundary (S1,S3,S5,S7) | 24 | | |
| Interior (S2,S4,S6,S8) | 24 | | |

### By target label

| Target | Runs | Successes | Success rate | Mean completion time (s) |
|---|---|---|---|---|
| soda_can | 6 | | | |
| coffee_mug | 6 | | | |
| backpack | 6 | | | |
| fire_extinguisher | 6 | | | |
| camera | 6 | | | |
| running_shoe | 6 | | | |
| headphones | 6 | | | |
| wall_clock | 6 | | | |

### Budget overruns

List every run where `completion_time_s > 240`:

| run_id | world | target | completion_time_s |
|---|---|---|---|
| | | | |

### Void runs

List every run marked `intervention_free = NO` and the repeat row that replaced it:

| run_id | reason | replaced by run_id |
|---|---|---|

## Evidence for the report

This file plus `docs/data/results_matrix.csv` are the main results table of
the evaluation chapter. A completion-time bar chart per world (mean ± spread
across the 16 runs per world) should be generated from the CSV once
populated and embedded here.

## Out of scope

Analysis of *why* individual runs failed belongs in
`docs/failure_log.md` / Issue #21, not here.
