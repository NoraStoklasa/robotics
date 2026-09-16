---
title: "[Nav] Choose and validate an obstacle clearance strategy"
labels: [stream:navigation, type:research, priority:P0]
milestone: "M3 - Navigation"
stream: navigation
depends_on: ["[Nav] Load the occupancy grid and verify world-grid conversion"]
estimate: "M"
---

## Why
The textbook move — inflate obstacles by one cell for the robot radius — **disconnects all four interior stations on this map**, so the clearance policy has to be chosen deliberately and proved reachable.

## Rubric link
Problem understanding, project idea and design rationale (8 marks); Project complexity and robustness (6 marks).

## Scope
Verify this finding first, then decide. A breadth-first reachability check over the 4-connected grid gives:
- **Raw grid, no inflation** — all eight `observe` cells are reachable from all three starts.
- **Uniform inflation by one cell** — `S2`, `S4`, `S6` and `S8` become unreachable. The interior barriers sit one to two cells apart, and inflation seals every gap into the interior pocket. The `observe` cells themselves stay free; it is the corridors that close.
- **Selective inflation** — inflate by one cell, then restore the raw values within a Chebyshev radius of the eight `observe` cells: a radius of 4 cells or more restores reachability to all eight, while radius 2 or 3 does not.

Tasks:
- Write `tools/check_reachability.py` running the breadth-first check for a given clearance policy across all three starts and all eight stations.
- Reproduce the three results above, then choose a policy: raw grid, selective inflation, or a soft cost penalty near obstacles applied through the A* g-cost.
- Record the choice and the trade in `docs/decision_clearance.md`: the raw grid plans through gaps roughly one cell wide and leans on reactive avoidance to stay safe, while inflation buys margin at the cost of reachability.
- Cross-check the physical margin: cells are 0.10 m and the e-puck is far smaller, so a one-cell gap is physically passable but demands accurate heading control.

## Acceptance criteria
- [x] `python tools/check_reachability.py` prints a start-by-station reachability table for a chosen policy and exits non-zero if any of the 24 start/station pairs is unreachable.
- [x] The three findings above are reproduced and recorded, including which stations are lost under uniform inflation.
- [x] The chosen policy passes all 24 start/station pairs.
- [x] `docs/decision_clearance.md` states the policy, the evidence, and the accepted risk.
- [x] The policy is implemented as one function taking the raw grid and returning the planning grid, so it can be swapped without touching A*.

- [x] The chosen policy is recorded as a row in `docs/decision_log.md` with the reachability numbers that decided it.

## Evidence for the report
The reachability table under each policy and a figure of the inflated grid with the sealed interior pocket — a strong design-rationale exhibit showing a real constraint discovered by analysis.

## Course reference
Workshop 8, Part 6 — obstacle rejection on the 4-connected grid, and Part 5's point that local perception is still needed after a global path exists.

## Out of scope
The A* search itself — that is `[Nav] Implement A* on the 4-connected occupancy grid`.
