---
title: "[Nav] Implement A* on the 4-connected occupancy grid"
labels: [stream:navigation, type:feature, priority:P0]
milestone: "M3 - Navigation"
stream: navigation
depends_on: ["[Nav] Choose and validate an obstacle clearance strategy"]
estimate: "M"
---

## Why
Gives the robot a global, collision-free route between any two cells, which reactive steering alone cannot produce in an arena with interior pockets.

## Rubric link
Technical approach, implementation and system integration (9 marks).

## Scope
- Implement `astar(grid, start, goal)` returning a list of `(row, col)` cells from start to goal, or an empty list when no path exists.
- Follow the Workshop 8 Part 6 structure: `heapq` open set, four-connected neighbour expansion, rejection of out-of-bounds and obstacle cells, g-cost update with parent recording, and path reconstruction.
- Use the Manhattan heuristic `abs(a[0] - b[0]) + abs(a[1] - b[1])`, as given in the workshop starter.
- Plan on the grid produced by the chosen clearance policy, not on the raw grid directly.
- Add a matplotlib visualisation of grid plus path, reusing the plotting shape of `astar_starter.py`.

## Acceptance criteria
- [x] For all 24 start/station pairs, `astar` returns a non-empty path whose first cell is the start and last cell is the goal.
- [x] No cell in any returned path has value 1 in the planning grid.
- [x] Consecutive cells in every returned path differ by exactly one step in exactly one axis, confirming 4-connectivity.
- [x] `astar` returns an empty list, without raising, when the goal is an obstacle cell or is enclosed by obstacles.
- [x] Planning one path from start A to the furthest station completes in under 1 second on a team laptop.

## Evidence for the report
A figure showing planned paths from each start to a representative station, and a table of path length and planning time per start/station pair.

## Course reference
Workshop 8, Part 6 — A* with `f(n) = g(n) + h(n)`, 4-connected expansion and the Manhattan heuristic.

## Out of scope
Turning cells into motion — that is `[Nav] Follow a waypoint path with P-controlled heading`. Do not use RRT, PRM or D*; A* only.
