# Full mission test matrix (Issue #20)

## Scope

**Rescoped 2026-09-17** (second rescope — see `docs/change_log.md`). The three official worlds
(`training_start_A/B/C.wbt`) crossed with **all eight mission targets, each run once** = 24 runs,
covering both boundary and interior stations in every world. The Week 8 brief's testing-strategy
section asks for a small matrix over start/target/station-type/repeated-run — the *repeated-run*
dimension is satisfied by `soda_can`/World A being run twice (rows 1-2 below), rather than doubling
every cell (the original 48-run scope, and an intermediate 21-run scope, are both superseded by this
version). Only `config/assessment_mission.json` is edited between runs — the controller is never
touched, and the controller file hash is recorded for every run to prove it.

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

A collision is a proximity reading above the calibrated `STOP` threshold (`STOP = 150`, see
`docs/proximity_calibration.md`), sustained beyond the avoidance response window — a single spike
below that duration is not counted.

## One-time classifier warm-up (not a hang)

The first station identified in every run triggers a lazy, one-off `_TargetIdentifier` build
(`vision_utils.py`): a ResNet18 is loaded and its final layer is actually trained for 60 steps on the
reference posters. This is CPU-bound and blocks Webots physics stepping for roughly 15-25 real
seconds, seen in the Webots clock as a stall followed by a jump. This is expected, happens once per
run (the identifier is cached afterwards), and does **not** count against sim-time or the 240 s
budget — only wall-clock time passes during it.

## Determinism note

The simulation is fully deterministic (fixed `IDENTIFIER_SEED`, no injected sensor noise, identical
start pose per world), so a genuine repeat of the same world/target pair reproduces the same result
bit-for-bit (verified: `soda_can`/World A rows 1-2 below are identical). This is expected and is not a
sign of a copy-pasted or faked result.

## Assessment conditions

Every run below must be started and left alone until it reaches `STOP` or `FAILED`/timeout: no menu
use, no keyboard input, no pausing, no reset, no restart. Any run that was touched is void and must be
repeated; log the touched run anyway with `void_reason` filled in, then add a fresh repeat row.

## Controller hash

Record once per matrix session, before the first run:

```
shasum -a 256 controllers/group_project_controller/group_project_controller.py
```

Hash for this matrix run: `c2757b9b045cccaa7e2ecad8823e52628d3428b7615fe34a1508385d7465e701` (verified
2026-09-17, matches the hash recorded before the earlier 48-run attempt — no controller edits have
happened in between).

If this changes mid-matrix, the matrix is invalid from that point on — stop and restart the whole
matrix under the new hash.

## Run log

Full per-run data lives in [`docs/data/results_matrix.csv`](data/results_matrix.csv) (25 rows: 24
required cells + 1 bonus repeat of `soda_can`/World A already run twice). Columns:

`run_id, world, start_pose, target, expected_station, station_type, repeat, run_timestamp, controller_hash, outcome, completion_time_s, over_budget_240s, final_distance_to_observe_m, station_chosen, station_match_expected, stations_inspected_count, collision_flag, max_proximity_reading, intervention_free, void_reason`

- `outcome`: `SUCCESS` / `FAILED` / `TIMEOUT`
- `over_budget_240s`: `YES`/`NO`, comparing `completion_time_s` to the 240 s budget
- `intervention_free`: `YES`/`NO` — `NO` means this row is void
- `void_reason`: blank unless `intervention_free = NO`, e.g. `"paused at 90s to check camera feed"`

## Progress

**All 25 runs complete (2026-09-17) — 25/25 SUCCESS, 0 collisions, 0 budget overruns, 0 void runs.**

- [x] Row 1: A / soda_can (1) — SUCCESS, 140.32 s, S1, 0.097 m
- [x] Row 2: A / soda_can (2) — SUCCESS, 140.32 s, S1, 0.097 m (identical repeat, confirms determinism)
- [x] Row 3: A / coffee_mug — SUCCESS, 32.42 s, S2, 0.099 m
- [x] Row 4: A / backpack — SUCCESS, 111.10 s, S3, 0.098 m
- [x] Row 5: A / fire_extinguisher — SUCCESS, 69.18 s, S4, 0.092 m
- [x] Row 6: A / camera — SUCCESS, 92.54 s, S5, 0.099 m
- [x] Row 7: A / running_shoe — SUCCESS, 55.55 s, S6, 0.098 m
- [x] Row 8: A / headphones — SUCCESS, 180.93 s, S7, 0.098 m (all 8 stations checked)
- [x] Row 9: A / wall_clock — SUCCESS, 21.73 s, S8, 0.097 m
- [x] Row 10: B / soda_can — SUCCESS, 172.74 s, S1, 0.097 m
- [x] Row 11: B / coffee_mug — SUCCESS, 64.90 s, S2, 0.099 m
- [x] Row 12: B / backpack — SUCCESS, 143.52 s, S3, 0.098 m
- [x] Row 13: B / fire_extinguisher — SUCCESS, 101.60 s, S4, 0.092 m
- [x] Row 14: B / camera — SUCCESS, 124.96 s, S5, 0.099 m
- [x] Row 15: B / running_shoe — SUCCESS, 87.97 s, S6, 0.098 m
- [x] Row 16: B / headphones — SUCCESS, 19.52 s, S7, 0.020 m
- [x] Row 17: B / wall_clock — SUCCESS, 53.25 s, S8, 0.099 m
- [x] Row 18: C / soda_can — SUCCESS, 167.04 s, S1, 0.097 m
- [x] Row 19: C / coffee_mug — SUCCESS, 91.84 s, S2, 0.098 m (borderline confidence 0.50-0.54, still passed consensus)
- [x] Row 20: C / backpack — SUCCESS, 8.58 s, S3, 0.098 m
- [x] Row 21: C / fire_extinguisher — SUCCESS, 59.84 s, S4, 0.090 m
- [x] Row 22: C / camera — SUCCESS, 26.50 s, S5, 0.097 m
- [x] Row 23: C / running_shoe — SUCCESS, 47.01 s, S6, 0.098 m
- [x] Row 24: C / headphones — SUCCESS, 122.72 s, S7, 0.099 m
- [x] Row 25: C / wall_clock — SUCCESS, 103.71 s, S8, 0.098 m

Note: in Worlds B and C, station S7 (`headphones`) consistently produces a first-pass
`NO_MATCH`/low-confidence read (~0.31-0.37) when a non-`headphones` target is being searched for and
S7 is visited early in the search order, resolving on the automatic retry-from-observe-pose path
(confidence then 0.67-0.71). When `headphones` is the actual target, it reads correctly and quickly.
This is a real, reproducible pattern worth noting in the failure/robustness discussion (Issue #21) even
though it never caused a matrix failure here.

## Summary

### By world

| World | Runs | Successes | Success rate | Mean completion time (s) | Runs over 240 s budget |
|---|---|---|---|---|---|
| A | 9 | 9 | 100% | 93.79 | 0 |
| B | 8 | 8 | 100% | 96.06 | 0 |
| C | 8 | 8 | 100% | 78.41 | 0 |
| **Overall** | **25** | **25** | **100%** | **89.59** | **0** |

### By start pose

(identical to "by world" in this project, since each world = one fixed start pose — kept as a
separate table to satisfy the "read by dimension" requirement)

| Start pose | Runs | Successes | Success rate |
|---|---|---|---|
| A | 9 | 9 | 100% |
| B | 8 | 8 | 100% |
| C | 8 | 8 | 100% |

### By station type (boundary vs interior)

| Station type | Runs | Successes | Success rate |
|---|---|---|---|
| Boundary (S1,S3,S5,S7) | 13 (4 targets x 3 worlds, +1 bonus soda_can repeat) | 13 | 100% |
| Interior (S2,S4,S6,S8) | 12 (4 targets x 3 worlds) | 12 | 100% |

### By target label

| Target | Runs | Successes | Success rate | Mean completion time (s) |
|---|---|---|---|---|
| soda_can | 4 (incl. 1 repeat) | 4 | 100% | 155.11 |
| coffee_mug | 3 | 3 | 100% | 63.05 |
| backpack | 3 | 3 | 100% | 87.73 |
| fire_extinguisher | 3 | 3 | 100% | 76.87 |
| camera | 3 | 3 | 100% | 81.33 |
| running_shoe | 3 | 3 | 100% | 63.51 |
| headphones | 3 | 3 | 100% | 107.72 |
| wall_clock | 3 | 3 | 100% | 59.56 |

`soda_can` and `headphones` have the highest mean completion times because their expected stations
(S1, S7) are furthest along the search order from most start poses, so more stations get checked (and
rejected) before the mission reaches them — not because those two labels are harder to identify.

### Budget overruns

None. Every run finished well inside the 240 s budget; the slowest was Row 8 (A / headphones,
180.93 s, 8/8 stations checked) — still 59.07 s under budget.

| run_id | world | target | completion_time_s |
|---|---|---|---|
| — none — | | | |

### Void runs

None. Every run completed without pausing, resetting or restarting mid-mission.

| run_id | reason | replaced by run_id |
|---|---|---|
| — none — | | |

## Evidence for the report

This file plus `docs/data/results_matrix.csv` are the main results table of the evaluation chapter.
A completion-time bar chart per world should be generated from the CSV once populated and embedded
here.

## Out of scope

Analysis of *why* individual runs failed belongs in `docs/failure_log.md` / Issue #21, not here.
