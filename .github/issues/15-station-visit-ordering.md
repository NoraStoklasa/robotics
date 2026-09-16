---
title: "[Nav] Compute the station visit order from planned path cost"
labels: [stream:navigation, type:feature, priority:P0]
milestone: "M4 - Mission integration"
stream: navigation
depends_on: ["[Nav] Implement A* on the 4-connected occupancy grid"]
estimate: "M"
---

## Why
The robot may have to inspect several stations before it finds the target, and the order it does that in decides whether the mission fits inside 4:00.

## Rubric link
Project complexity and robustness (6 marks); Experimental evaluation, results and discussion (8 marks).

## Scope
- Implement `next_station(current_pose, unvisited)` choosing the next station to inspect by **computed A* path cost** from the current cell, never by a written-down order.
- Seed the candidate list from `CONFIG["stations"]`, so all eight are considered and nothing about the target identity influences the order.
- Recompute the order after each station is inspected, since the robot's position has changed.
- Keep a visited set so no station is inspected twice.
- Compare nearest-first against at least one alternative — for example, a fixed geometric sweep — by measuring total simulated time to reach every station from each start.
- Record the comparison in `docs/decision_visit_order.md`.

## Acceptance criteria
- [x] `next_station` derives its choice from `astar` path length; `grep -nE '"S[1-8]"' ` over the ordering code returns no hard-coded station sequence.
- [x] Given the same pose and unvisited set, the function is deterministic across repeated calls.
- [x] Starting from A, B and C, the computed first station differs for at least two of the three starts, confirming the order responds to pose.
- [x] Visiting all eight stations from the worst-case start completes within the 4:00 simulation budget, measured and recorded.
- [x] `docs/decision_visit_order.md` reports total time for both strategies from all three starts.

## Evidence for the report
The strategy comparison table — time to visit all stations, per start, per strategy. Direct evidence that the search order was designed rather than assumed.

## Course reference
Workshop 8, Part 6 — using A* path cost as the measure of distance, and comparing global planning against reactive navigation.

## Out of scope
The state machine that calls this — that is `[Sys] Implement the mission state machine`.
