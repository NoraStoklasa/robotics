---
title: "[Nav] Follow a waypoint path with P-controlled heading"
labels: [stream:navigation, type:feature, priority:P0]
milestone: "M3 - Navigation"
stream: navigation
depends_on: ["[Nav] Implement A* on the 4-connected occupancy grid"]
estimate: "L"
---

## Why
An A* path is a list of cells, not a motor command; this is the layer that turns it into motion.

## Rubric link
Technical approach, implementation and system integration (9 marks).

## Scope
- Convert the cell path to world waypoints with the provided `grid_to_world`, taking each cell centre.
- Simplify the path by collapsing runs of collinear cells, so the robot steers at corners instead of at every 0.1 m cell. Keep the simplified path collision-free under the planning grid.
- Implement `follow_path(waypoints)` driving to each waypoint in turn: compute the heading error with `bearing_to`, apply proportional steering `turn = KP_HEADING * error`, and set `left = base + turn`, `right = base - turn` through `set_speed`.
- Treat a waypoint as reached when `distance_to` falls below `WAYPOINT_TOLERANCE`, then advance to the next.
- Reduce base speed when the heading error is large, so the robot turns before committing to driving forward.
- Tune `KP_HEADING` by testing at least two values and recording the behaviour, as Workshop 8 Part 4 asks.

- Issue wheel commands only through the motion layer from issue 03, so the single speed clamp stays the only place limits are applied.
- Match the navigation→control signature agreed in `docs/interfaces.md` (issue 26) — waypoint, heading or full path, whichever the team settled on.

## Acceptance criteria
- [x] From start A, the robot follows a planned path to at least three different stations and ends within 0.20 m of each `observe` position.
- [x] Cross-track deviation from the planned path stays under 0.15 m throughout, measured by logging `get_pose()` against the waypoint list.
- [x] Path simplification reduces the waypoint count by at least 50 percent on a path of 20 or more cells, and the simplified path still contains no obstacle cell.
- [x] Two `KP_HEADING` values are tested and the comparison, including any oscillation seen, is recorded in `docs/control_tuning.md`.
- [x] The robot completes a full path with no proximity reading exceeding the calibrated `STOP` threshold.

## Evidence for the report
A trajectory plot overlaying planned path and logged actual pose, plus the `KP_HEADING` comparison table.

## Course reference
Workshop 8, Part 4 — normalised error, proportional steering into differential wheel speeds, and comparing two `kp` values; Part 6, step 6 — converting grid cells into robot waypoints.

## Out of scope
Reacting to obstacles not in the map — that is `[Nav] Add reactive obstacle avoidance with recovery to the path`. Use a plain P controller only; no PID.
