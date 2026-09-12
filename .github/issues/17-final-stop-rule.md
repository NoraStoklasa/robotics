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
- [ ] At mission end the logged Euclidean x-y distance from the robot centre to the target station's `observe` is under 0.20 m, for all three starts.
- [ ] Final heading is within 0.30 rad of the station's `observe_yaw`.
- [ ] Both wheel velocities are 0.0 for the last 20 consecutive timesteps of the run.
- [ ] No proximity reading exceeds the calibrated `STOP` threshold during the final approach.
- [ ] The final distance is computed from `get_pose()` and printed, so the margin is visible during the live demonstration.

## Evidence for the report
A results table of final distance to `observe` and final heading error, per mission — the direct evidence of meeting the success criterion.

## Course reference
Week 2 — distance and bearing between world-frame positions; Workshop 8, Part 2 — the safe stop behaviour.

## Out of scope
Enforcing the 4:00 budget — that is `[Sys] Log telemetry and enforce the 4:00 mission time budget`.
