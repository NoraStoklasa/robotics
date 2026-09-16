"""Coordinate helpers for the 3006ICT group-project world."""

import heapq
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


def heuristic(a, b):
    """Manhattan distance for 4-connected grid motion."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal):
    """A* on a 4-connected grid (Issue #12). Returns [(row, col), ...] or [] if unreachable.

    Plan on the grid returned by apply_clearance_policy, not the raw grid.
    """
    rows, cols = grid.shape

    if grid[start] == 1 or grid[goal] == 1:
        return []

    open_set = [(heuristic(start, goal), start)]
    g_cost = {start: 0}
    came_from = {}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        row, col = current
        neighbours = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]

        for neighbour in neighbours:
            n_row, n_col = neighbour

            if n_row < 0 or n_row >= rows or n_col < 0 or n_col >= cols:
                continue
            if grid[n_row, n_col] == 1:
                continue

            new_g = g_cost[current] + 1

            if neighbour not in g_cost or new_g < g_cost[neighbour]:
                g_cost[neighbour] = new_g
                f_cost = new_g + heuristic(neighbour, goal)
                heapq.heappush(open_set, (f_cost, neighbour))
                came_from[neighbour] = current

    return []


def simplify_path(path):
    """Collapse runs of collinear cells (Issue #13), keeping start, end and every corner.

    The direct line between two kept points retraces exactly the straight run
    of free cells the search already found, so this cannot introduce a
    collision the original path didn't already avoid.
    """
    if len(path) <= 2:
        return list(path)
    simplified = [path[0]]
    for i in range(1, len(path) - 1):
        prev_dir = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        next_dir = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        if prev_dir != next_dir:
            simplified.append(path[i])
    simplified.append(path[-1])
    return simplified


def path_to_waypoints(path):
    """Grid cell path -> list of world (x, y) waypoints, one per cell centre."""
    return [grid_to_world(row, col) for row, col in path]


def next_station(current_pose, unvisited, grid):
    """Choose the next station to inspect by computed A* path cost (Issue #15).

    current_pose: (x, y, ...) world pose. unvisited: station dicts (a subset
    of CONFIG["stations"]). grid: the planning grid (Issue #11 policy) to
    measure path cost on. Returns the station dict reached by the shortest
    A* path, or None if unvisited is empty. Deterministic: unvisited is
    sorted by id before comparing, so ties always resolve the same way.
    """
    current_cell = world_to_grid(current_pose[0], current_pose[1])
    best_station, best_cost = None, None
    for station in sorted(unvisited, key=lambda s: s["id"]):
        goal_cell = world_to_grid(*station["observe"])
        path = astar(grid, current_cell, goal_cell)
        cost = len(path) if path else float("inf")
        if best_cost is None or cost < best_cost:
            best_station, best_cost = station, cost
    return best_station
