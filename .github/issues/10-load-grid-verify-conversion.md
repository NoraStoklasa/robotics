---
title: "[Nav] Load the occupancy grid and verify world-grid conversion"
labels: [stream:navigation, type:feature, priority:P0]
milestone: "M3 - Navigation"
stream: navigation
depends_on: ["[Nav] Implement motion primitives and pose utilities"]
estimate: "S"
---

## Why
Every planning decision rests on the grid and the coordinate conversion being right; a silent row/column swap here would be very hard to diagnose later.

## Rubric link
Technical approach, implementation and system integration (9 marks).

## Scope
- Load `maps/occupancy_grid.npy` — already loaded as `GRID` in the starter — and confirm its shape and encoding against `maps/occupancy_grid_info.json`: 40 rows, 40 columns, 0.1 m per cell, 0 free and 1 obstacle.
- Round-trip test the provided `world_to_grid` and `grid_to_world` helpers over a sweep of world coordinates and every grid cell.
- Render the grid with matplotlib, overlaying the three start poses and the eight `observe` positions from `CONFIG`.
- Verify each start and each `observe` position falls on a cell marked free, and record the cell indices in `docs/grid_check.md`.

## Acceptance criteria
- [ ] `GRID.shape` is `(40, 40)` and `numpy.unique(GRID)` is exactly `[0, 1]`.
- [ ] For every one of the 1600 cells, `world_to_grid(*grid_to_world(r, c))` returns `(r, c)`.
- [ ] All three start cells and all eight `observe` cells evaluate to 0 in the grid.
- [ ] The rendered overlay figure shows the eight observe markers sitting in free space, visually consistent with `maps/world_layout.png`.
- [ ] `docs/grid_check.md` lists the grid cell for each start and each station.

## Evidence for the report
The grid overlay figure showing starts, stations and obstacles — used to introduce the environment in the report.

## Course reference
Workshop 8, Part 6 — loading and displaying the occupancy grid, with 0 free and 1 obstacle.

## Out of scope
Clearance and inflation decisions — that is `[Nav] Choose and validate an obstacle clearance strategy`.
