---
title: "[Nav] Add reactive obstacle avoidance with recovery to the path"
labels: [stream:navigation, type:feature, priority:P0]
milestone: "M3 - Navigation"
stream: navigation
depends_on: ["[Nav] Follow a waypoint path with P-controlled heading", "[Nav] Calibrate ps0-ps7 obstacle thresholds from logged readings"]
estimate: "L"
---

## Why
The mission fails outright on any collision, and the grid is a 0.1 m approximation — the planned path can pass closer to a barrier than the map suggests.

## Rubric link
Project complexity and robustness (6 marks); Live code/system demonstration (10 marks).

## Scope
- Implement the Workshop 8 behaviour priority explicitly: **Safety > Path following > Search**, with one function selecting the active behaviour each control step.
- Use the calibrated thresholds: when the front-left group `ps5`-`ps7` or the front-right group `ps0`-`ps2` exceeds `WARN`, turn away from the triggering side; when either exceeds `STOP`, stop and rotate in place before continuing.
- After an avoidance manoeuvre, return to the path rather than abandoning it: either re-acquire the nearest remaining waypoint, or replan with A* from the current cell when displacement exceeds a set distance.
- Add a stuck detector: if the robot's pose moves less than a set distance over a set number of timesteps, trigger a recovery — back off, rotate, replan.
- Log every behaviour switch through the telemetry logger.

## Acceptance criteria
- [ ] In a run deliberately started facing a barrier, the robot avoids contact and still reaches the goal within 0.20 m.
- [ ] Across all 24 start/station pairs, no run records a proximity reading above the calibrated `STOP` threshold for more than 3 consecutive timesteps.
- [ ] After each avoidance manoeuvre the robot returns to within `WAYPOINT_TOLERANCE` of a waypoint on the planned path, or a replan is logged.
- [ ] The stuck detector fires and recovers in a test where the robot is placed against a barrier corner, with recovery visible in the log.
- [ ] Safety demonstrably overrides path following: a log excerpt shows an avoidance behaviour active while a waypoint was still pending.

## Evidence for the report
An annotated trajectory showing an avoidance event and the return to path, plus a table of behaviour-switch counts per run.

## Course reference
Workshop 8, Part 5 — left and right obstacle checks, turn-away avoidance, and giving avoidance higher priority than target following.

## Out of scope
Deciding which station to visit next — that is `[Nav] Compute the station visit order from planned path cost`.
