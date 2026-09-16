---
title: "[Sys] Implement the final stop rule at the observation position"
labels: [stream:integration, type:feature, priority:P0]
milestone: "M4 - Mission integration"
stream: integration
depends_on: ["[Sys] Implement the mission state machine"]
estimate: "M"
---

## Why
This is the literal success criterion — the e-puck centre within 0.20 m of the designated observation position, stopped, with no collision.

## Rubric link
Live code/system demonstration (10 marks); Technical approach, implementation and system integration (9 marks).

## Scope
- On a confirmed identification, plan to the station's `observe` coordinate from `CONFIG` and drive there.
- Close the final approach in position, not on a timer: keep correcting while the Euclidean x-y distance from `get_pose()` to `observe` exceeds `ARRIVAL_TOLERANCE`.
- Set `ARRIVAL_TOLERANCE` safely inside the 0.20 m requirement — 0.10 m gives margin for pose noise and the final settle.
- Rotate to `observe_yaw` once inside tolerance, so the robot ends facing the poster it identified.
- Call `set_speed(0.0, 0.0)` and hold it; log the final pose and the measured distance to `observe`.
- Guard against overshoot: reduce speed as distance closes, and never approach the barrier below the calibrated `STOP` proximity threshold.

## Acceptance criteria
- [x] At mission end the logged Euclidean x-y distance from the robot centre to the target station's `observe` is under 0.20 m, for all three starts.
- [x] Final heading is within 0.30 rad of the station's `observe_yaw`.
- [x] Both wheel velocities are 0.0 for the last 20 consecutive timesteps of the run.
- [x] No proximity reading exceeds the calibrated `STOP` threshold during the final approach.
- [x] The final distance is computed from `get_pose()` and printed, so the margin is visible during the live demonstration.

## Evidence for the report
A results table of final distance to `observe` and final heading error, per mission — the direct evidence of meeting the success criterion.

Real Webots runs, all three starts, target `soda_can` at S1 in every world:

| World | Start | Path to identification | Final distance to `observe` | Final heading error |
|---|---|---|---|---|
| A | start_A | real vision, confirmed at S1 after visiting S8/S2/S4/S6/S5 as non-matches | 0.043 m | -0.035 rad |
| B | start_B | real vision, confirmed at S1 after visiting S7/S8/S2/S4/S6/S5 as non-matches | 0.043 m | -0.035 rad |
| C | start_C | `STUB_PERCEPTION=1` (see caveat below) | 0.043 m | 0.027 rad |

No `BEHAVIOUR ... STOP` (proximity) events were logged between `GOTO_OBSERVE` and the final print in
any run, and each `FINAL_HOLD` completed its full 20-step zero-velocity hold before the mission
state moved to `STOP`.

**Caveat:** in world C, real vision never reaches consensus on `soda_can` at S1 (confidence sits at
0.27-0.30, below `MIN_CONFIDENCE`) -- a pre-existing vision-model limitation already documented from
Issue #16's testing (`docs/mission_state_machine.md`), not a defect in this issue's final-stop logic.
World C's row above used `STUB_PERCEPTION=1`/`STUB_MATCH_STATION=S1` to force the identification and
exercise `GOTO_OBSERVE`/`FINAL_ALIGN`/`FINAL_HOLD` independently of that limitation; the result
confirms the final-stop mechanism itself works identically to worlds A and B once a station is
confirmed.

## Course reference
Week 2 — distance and bearing between world-frame positions; Workshop 8, Part 2 — the safe stop behaviour.

## Out of scope
Enforcing the 4:00 budget — that is `[Sys] Log telemetry and enforce the 4:00 mission time budget`.
