"""Coordinate helpers for the 3006ICT group-project world."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "config" / "project_config.json").read_text())

X_MIN = CONFIG["arena"]["x_min"]
Y_MAX = CONFIG["arena"]["y_max"]
RES = CONFIG["arena"]["resolution"]


def world_to_grid(x, y):
    """World (x, y) -> occupancy-grid (row, col)."""
    col = int((x - X_MIN) / RES)
    row = int((Y_MAX - y) / RES)
    return row, col


def grid_to_world(row, col):
    """Occupancy-grid cell -> world coordinate at the cell centre."""
    x = X_MIN + (col + 0.5) * RES
    y = Y_MAX - (row + 0.5) * RES
    return x, y


def station_by_id(station_id):
    return next(s for s in CONFIG["stations"] if s["id"] == station_id)


def start_by_id(start_id):
    return next(s for s in CONFIG["starts"] if s["id"] == start_id)


def inflate_grid(grid):
    """Return a copy of grid with every obstacle's 4-connected free neighbours also marked obstacle."""
    inflated = grid.copy()
    rows, cols = grid.shape
    for row in range(rows):
        for col in range(cols):
            if grid[row, col] != 1:
                continue
            for d_row, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                n_row, n_col = row + d_row, col + d_col
                if 0 <= n_row < rows and 0 <= n_col < cols:
                    inflated[n_row, n_col] = 1
    return inflated


def selective_inflation(grid, observe_cells, radius):
    """Inflate by one cell, then restore raw values within a Chebyshev radius of each observe cell."""
    inflated = inflate_grid(grid)
    rows, cols = grid.shape
    for obs_row, obs_col in observe_cells:
        row_lo, row_hi = max(0, obs_row - radius), min(rows - 1, obs_row + radius)
        col_lo, col_hi = max(0, obs_col - radius), min(cols - 1, obs_col + radius)
        for row in range(row_lo, row_hi + 1):
            for col in range(col_lo, col_hi + 1):
                if max(abs(row - obs_row), abs(col - obs_col)) <= radius:
                    inflated[row, col] = grid[row, col]
    return inflated


def apply_clearance_policy(grid, policy, observe_cells=None, radius=4):
    """Return the planning grid for a named clearance policy (Issue #11).

    Swap the policy here without touching the A* search: it always plans on
    whatever grid this function returns.
    """
    if policy == "raw":
        return grid.copy()
    if policy == "uniform":
        return inflate_grid(grid)
    if policy == "selective":
        if observe_cells is None:
            raise ValueError("selective policy requires observe_cells")
        return selective_inflation(grid, observe_cells, radius)
    raise ValueError(f"unknown clearance policy: {policy}")
