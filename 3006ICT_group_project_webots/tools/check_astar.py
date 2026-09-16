"""Issue #12: run A* across all 24 start/station pairs and check the acceptance criteria.

Plans on the grid produced by the Issue #11 clearance policy (selective
inflation, radius 4), not the raw grid. Verifies path validity (no obstacle
cells, 4-connected steps, correct endpoints), timing, and the empty-goal
cases, then writes a figure and a report.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-check-astar")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

WEBOTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = WEBOTS_ROOT.parent
CONTROLLER_DIR = WEBOTS_ROOT / "controllers" / "group_project_controller"

sys.path.insert(0, str(CONTROLLER_DIR))
from project_utils import CONFIG, apply_clearance_policy, astar, world_to_grid  # noqa: E402

GRID_PATH = WEBOTS_ROOT / "maps" / "occupancy_grid.npy"
FIGURE_PATH = REPO_ROOT / "docs" / "data" / "astar_paths.png"
REPORT_PATH = REPO_ROOT / "docs" / "astar_planning.md"

CLEARANCE_POLICY = "selective"
CLEARANCE_RADIUS = 4


def report(name: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"{status}: {name}{suffix}")
    return passed


def start_cells() -> list[tuple[str, tuple[int, int]]]:
    return [(s["id"], world_to_grid(*s["pose"][:2])) for s in CONFIG["starts"]]


def station_cells() -> list[tuple[str, tuple[int, int]]]:
    return [(s["id"], world_to_grid(*s["observe"])) for s in CONFIG["stations"]]


def path_is_valid(grid: np.ndarray, path: list[tuple[int, int]], start: tuple[int, int], goal: tuple[int, int]) -> tuple[bool, str]:
    if not path:
        return False, "empty path"
    if path[0] != start:
        return False, f"first cell {path[0]} != start {start}"
    if path[-1] != goal:
        return False, f"last cell {path[-1]} != goal {goal}"
    for row, col in path:
        if grid[row, col] == 1:
            return False, f"path passes through obstacle cell ({row}, {col})"
    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        d_row, d_col = abs(r1 - r2), abs(c1 - c2)
        if (d_row, d_col) not in ((1, 0), (0, 1)):
            return False, f"non-4-connected step ({r1},{c1}) -> ({r2},{c2})"
    return True, ""


def synthetic_empty_goal_tests() -> list[bool]:
    """Issue #12: astar must return [] without raising for an obstacle or enclosed goal."""
    grid = np.zeros((5, 5), dtype=np.uint8)
    results = []

    obstacle_goal_grid = grid.copy()
    obstacle_goal_grid[4, 4] = 1
    path = astar(obstacle_goal_grid, (0, 0), (4, 4))
    results.append(report("astar([]) when goal cell is itself an obstacle", path == []))

    enclosed_grid = grid.copy()
    enclosed_grid[1, 2] = 1
    enclosed_grid[2, 1] = 1
    enclosed_grid[2, 3] = 1
    enclosed_grid[3, 2] = 1
    path = astar(enclosed_grid, (0, 0), (2, 2))
    results.append(report("astar([]) when goal is enclosed by obstacles", path == []))

    return results


def save_figure(grid: np.ndarray, starts: list, stations: list, paths: dict) -> None:
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.imshow(grid, cmap="gray_r", vmin=0, vmax=1, origin="upper")

    colors = plt.cm.tab10.colors
    for i, (s_id, _) in enumerate(starts):
        # Plot the path to this start's furthest station (longest path), to
        # keep the figure readable while showing a meaningful case per start.
        st_id, path = max(
            ((st_id, p) for (start_id, st_id), p in paths.items() if start_id == s_id),
            key=lambda item: len(item[1]),
        )
        rows, cols = zip(*path)
        ax.plot(cols, rows, "-o", markersize=2, color=colors[i % len(colors)], label=f"{s_id} -> {st_id} (furthest)")

    for s_id, (row, col) in starts:
        ax.scatter([col], [row], marker="s", s=90, color="black")
        ax.annotate(s_id, (col, row), xytext=(4, 4), textcoords="offset points")
    for st_id, (row, col) in stations:
        ax.scatter([col], [row], marker="*", s=110, color="tab:red")
        ax.annotate(st_id, (col, row), xytext=(4, 4), textcoords="offset points")

    ax.set_title("A* planned paths (selective-inflation grid, one representative path per start)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, linewidth=0.3, alpha=0.5)
    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=200)
    plt.close(fig)


def write_report(rows: list[dict], all_valid: bool, max_time_s: float, empty_goal_ok: bool) -> None:
    table_header = "| Start | Station | Path length (cells) | Planning time (ms) | Valid |\n|---|---|---:|---:|---|"
    table_rows = "\n".join(
        f"| {r['start']} | {r['station']} | {r['length']} | {r['time_ms']:.3f} | {r['valid']} |" for r in rows
    )

    report_text = f"""# A* Path Planning

Per [Issue #12](.github/issues/12-implement-astar.md). Generated by `python tools/check_astar.py`.

`astar(grid, start, goal)` in `project_utils.py`, adapted from the Workshop 8 Part 6 starter
(`heapq` open set, 4-connected expansion, Manhattan heuristic, g-cost/parent tracking, path
reconstruction). Plans on the grid from the Issue #11 clearance policy
(`{CLEARANCE_POLICY}` inflation, radius {CLEARANCE_RADIUS}), not the raw grid.

## Results across all 24 start/station pairs

{table_header}
{table_rows}

- All 24 paths valid (correct endpoints, no obstacle cells, 4-connected steps): **{all_valid}**
- Slowest single-path planning time: **{max_time_s * 1000:.3f} ms** (budget: under 1000 ms)
- Empty-goal edge cases (obstacle goal, enclosed goal) return `[]` without raising: **{empty_goal_ok}**

## Figure

![A* planned paths](data/astar_paths.png)

One representative path per start is drawn (all 24 are computed and checked above; plotting all 24
would be unreadable in one figure).
"""
    REPORT_PATH.write_text(report_text)


def main() -> int:
    raw_grid = np.load(GRID_PATH)
    starts = start_cells()
    stations = station_cells()

    grid = apply_clearance_policy(raw_grid, CLEARANCE_POLICY, [c for _, c in stations], radius=CLEARANCE_RADIUS)

    rows = []
    paths: dict[tuple[str, str], list] = {}
    results = []
    max_time_s = 0.0

    for s_id, s_cell in starts:
        for st_id, st_cell in stations:
            t0 = time.perf_counter()
            path = astar(grid, s_cell, st_cell)
            elapsed = time.perf_counter() - t0
            max_time_s = max(max_time_s, elapsed)

            valid, detail = path_is_valid(grid, path, s_cell, st_cell)
            results.append(report(f"{s_id} -> {st_id}", valid, detail))
            paths[(s_id, st_id)] = path
            rows.append(
                {
                    "start": s_id,
                    "station": st_id,
                    "length": len(path),
                    "time_ms": elapsed * 1000,
                    "valid": valid,
                }
            )

    all_valid = all(r["valid"] for r in rows)
    results.append(report("all 24 pairs return a valid 4-connected path", all_valid))
    results.append(report("slowest path plans in under 1 second", max_time_s < 1.0, f"{max_time_s * 1000:.3f} ms"))

    edge_case_results = synthetic_empty_goal_tests()
    empty_goal_ok = all(edge_case_results)
    results.extend(edge_case_results)

    save_figure(grid, starts, stations, paths)
    write_report(rows, all_valid, max_time_s, empty_goal_ok)
    print(f"\nWrote {FIGURE_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)}")

    overall = all(results)
    print(f"\nOVERALL: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
