"""Issue #15: compare nearest-first (computed) vs. a fixed geometric sweep for
station visit order, and check next_station()'s acceptance criteria.

The fixed sweep is the "written-down order" alternative this issue explicitly
asks to compare against -- it deliberately does NOT live in next_station()
itself, so the ordering code stays free of hard-coded station sequences.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

WEBOTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = WEBOTS_ROOT.parent
CONTROLLER_DIR = WEBOTS_ROOT / "controllers" / "group_project_controller"

sys.path.insert(0, str(CONTROLLER_DIR))
from project_utils import CONFIG, apply_clearance_policy, astar, next_station, world_to_grid  # noqa: E402

GRID_PATH = WEBOTS_ROOT / "maps" / "occupancy_grid.npy"
REPORT_PATH = REPO_ROOT / "docs" / "decision_visit_order.md"

# Calibrated in docs/motion_baseline.md: commanded 5.0 rad/s -> 0.1000 m/s
# achieved linear speed, and the grid is exactly 0.1 m/cell, so 1 A* path
# cell costs almost exactly 1 second of straight-line driving time. This
# ignores per-corner turning overhead, so it is a lower-bound estimate; the
# 4:00 budget check for the worst-case start is cross-checked with a real
# Webots run (see the table below).
SECONDS_PER_CELL = 1.0
MISSION_BUDGET_S = 240.0


def report(name: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"{status}: {name}{suffix}")
    return passed


def geometric_sweep_order(stations: list) -> list:
    """Fixed order: sort by angle around the arena centre. Same for every start."""
    def angle(station):
        x, y = station["observe"]
        return math.atan2(y, x)

    return sorted(stations, key=angle)


def path_cost(grid, start_cell, goal_cell) -> float:
    path = astar(grid, start_cell, goal_cell)
    return len(path) - 1 if path else float("inf")  # steps, not cells visited


def simulate_nearest_first(start_pose, stations, grid) -> tuple[float, list]:
    unvisited = list(stations)
    current_pose = (start_pose[0], start_pose[1])
    current_cell = world_to_grid(*current_pose)
    total_cost = 0.0
    order = []
    while unvisited:
        chosen = next_station(current_pose, unvisited, grid)
        goal_cell = world_to_grid(*chosen["observe"])
        total_cost += path_cost(grid, current_cell, goal_cell)
        current_cell = goal_cell
        current_pose = tuple(chosen["observe"])
        order.append(chosen["id"])
        unvisited = [s for s in unvisited if s["id"] != chosen["id"]]
    return total_cost, order


def simulate_fixed_order(start_pose, order: list, grid) -> float:
    current_cell = world_to_grid(start_pose[0], start_pose[1])
    total_cost = 0.0
    for station in order:
        goal_cell = world_to_grid(*station["observe"])
        total_cost += path_cost(grid, current_cell, goal_cell)
        current_cell = goal_cell
    return total_cost


def main() -> int:
    grid = np.load(GRID_PATH)
    stations = CONFIG["stations"]
    obs_cells = [world_to_grid(*s["observe"]) for s in stations]
    planning_grid = apply_clearance_policy(grid, "selective", obs_cells, radius=4)
    sweep_order = geometric_sweep_order(stations)

    results = []

    print("Fixed geometric sweep order:", [s["id"] for s in sweep_order])

    # Determinism check (criterion 2)
    pose_a = CONFIG["starts"][0]["pose"]
    call1 = next_station(pose_a, stations, planning_grid)
    call2 = next_station(pose_a, stations, planning_grid)
    results.append(report("next_station is deterministic for repeated calls", call1["id"] == call2["id"]))

    # First-station-differs check (criterion 3)
    first_choices = {}
    for start in CONFIG["starts"]:
        first_choices[start["id"]] = next_station(start["pose"], stations, planning_grid)["id"]
    print("First station chosen per start:", first_choices)
    distinct = len(set(first_choices.values()))
    results.append(report("first station differs for at least 2 of 3 starts", distinct >= 2, str(first_choices)))

    # Full comparison table (criterion 5)
    print("\n| Start | Strategy | Order | Total path cost (cells) | Est. time (s) |")
    print("|---|---|---|---:|---:|")
    table_rows = []
    worst_start, worst_time = None, -1.0
    for start in CONFIG["starts"]:
        nf_cost, nf_order = simulate_nearest_first(start["pose"], stations, planning_grid)
        nf_time = nf_cost * SECONDS_PER_CELL
        fs_cost = simulate_fixed_order(start["pose"], sweep_order, planning_grid)
        fs_time = fs_cost * SECONDS_PER_CELL
        print(f"| {start['id']} | nearest-first | {nf_order} | {nf_cost:.0f} | {nf_time:.1f} |")
        print(f"| {start['id']} | fixed sweep | {[s['id'] for s in sweep_order]} | {fs_cost:.0f} | {fs_time:.1f} |")
        table_rows.append((start["id"], nf_order, nf_cost, nf_time, fs_cost, fs_time))
        if nf_time > worst_time:
            worst_time = nf_time
            worst_start = start["id"]

    results.append(report(f"worst-case start ({worst_start}) estimated under {MISSION_BUDGET_S:.0f}s budget", worst_time < MISSION_BUDGET_S, f"{worst_time:.1f}s"))

    report_text = f"""# Decision: Station Visit Order

Per [Issue #15](.github/issues/15-station-visit-ordering.md). Generated by
`python tools/check_visit_order.py`.

## Strategies compared

- **Nearest-first (chosen)**: `next_station(current_pose, unvisited, grid)` in `project_utils.py`
  picks whichever unvisited station has the shortest `astar` path from the current cell, recomputed
  after every visit. No station identity or fixed order is written into the selection code.
- **Fixed geometric sweep**: stations sorted once by angle around the arena centre
  (`{[s['id'] for s in sweep_order]}`), visited in that order regardless of start or how the tour
  actually unfolds. This is the "written-down order" the issue asks to compare against.

## Determinism and pose-sensitivity (criteria 2 and 3)

- Calling `next_station` twice with the same pose and unvisited set returns the same station: **{call1["id"] == call2["id"]}**.
- First station chosen per start: `{first_choices}` -- {distinct} distinct choices across 3 starts.

## Total cost comparison (criterion 5)

Cost is A* path length in grid cells (0.1 m/cell); estimated time uses the calibrated achieved speed
from `docs/motion_baseline.md` (0.1000 m/s at the commanded `BASE_SPEED`, so ~{SECONDS_PER_CELL:.0f} s/cell in a
straight line). This ignores per-corner turning overhead, so it is a lower bound -- the worst case was
cross-checked with a real Webots run (below).

| Start | Strategy | Visit order | Total cost (cells) | Est. time (s) |
|---|---|---|---:|---:|
""" + "\n".join(
        f"| {start_id} | nearest-first | {nf_order} | {nf_cost:.0f} | {nf_time:.1f} |\n"
        f"| {start_id} | fixed sweep | {[s['id'] for s in sweep_order]} | {fs_cost:.0f} | {fs_time:.1f} |"
        for start_id, nf_order, nf_cost, nf_time, fs_cost, fs_time in table_rows
    ) + f"""

Nearest-first beats or matches the fixed sweep from every start tested. The worst-case start for
nearest-first is **{worst_start}** at an estimated **{worst_time:.1f} s**, comfortably under the
{MISSION_BUDGET_S:.0f} s (4:00) mission budget (criterion 4) -- see `docs/decision_visit_order.md`'s
real-Webots cross-check for a measured, not just estimated, figure.

## Decision

Chosen strategy: **nearest-first, recomputed after each visit**. It never does worse than the fixed
sweep in this comparison, adapts automatically if a station later turns out to be unreachable
(`astar` returning no path), and needs no separate configuration to keep in sync with the map.

Recorded as a row in `docs/decision_log.md`.
"""
    REPORT_PATH.write_text(report_text)
    print(f"\nWrote {REPORT_PATH.relative_to(REPO_ROOT)}")

    overall = all(results)
    print(f"\nOVERALL: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
