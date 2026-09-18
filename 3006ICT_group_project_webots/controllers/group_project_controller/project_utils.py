"""Coordinate helpers for the 3006ICT group-project world."""

import heapq
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "config" / "project_config.json").read_text())

X_MIN = CONFIG["arena"]["x_min"]
X_MAX = CONFIG["arena"]["x_max"]
Y_MIN = CONFIG["arena"]["y_min"]
Y_MAX = CONFIG["arena"]["y_max"]
RES = CONFIG["arena"]["resolution"]
GRID_ROWS = round((Y_MAX - Y_MIN) / RES)
GRID_COLS = round((X_MAX - X_MIN) / RES)


# Report Section 5.1 -- The map and the grid (world <-> grid conversion, verified round-trip)
def world_to_grid(x, y):
    """World (x, y) -> occupancy-grid (row, col).

    Clamped to the grid's valid index range: a coordinate exactly on the
    arena boundary (x == x_max or y == y_min) would otherwise divide out to
    GRID_COLS/GRID_ROWS, one past the last valid index.
    """
    col = min(max(int((x - X_MIN) / RES), 0), GRID_COLS - 1)
    row = min(max(int((Y_MAX - y) / RES), 0), GRID_ROWS - 1)
    return row, col


# Report Section 5.1 -- The map and the grid (grid -> world conversion)
def grid_to_world(row, col):
    """Occupancy-grid cell -> world coordinate at the cell centre."""
    x = X_MIN + (col + 0.5) * RES
    y = Y_MAX - (row + 0.5) * RES
    return x, y


# Report Section 3 -- System architecture (config lookup helpers behind
# the station/start data flowing into Figure 7's Mission state machine)

# Look through the stations in the config file and hand back the one with
# this id (e.g. "S3"). Raises if the id isn't in the config at all.
def station_by_id(station_id):
    for station in CONFIG["stations"]:
        if station["id"] == station_id:
            return station
    raise ValueError(f"no station with id {station_id}")


# Same idea, but for the three start poses ("A", "B", "C").
def start_by_id(start_id):
    for start in CONFIG["starts"]:
        if start["id"] == start_id:
            return start
    raise ValueError(f"no start with id {start_id}")


# Report Section 7.1/9.1 -- How we tested (labels each run by start pose A/B/C
# for the mission_summary.csv row that Table 14's breakdown is built from)
def nearest_start_id(pose):
    """Which configured start (x, y) the robot's first real pose is closest to.

    The controller itself never gets told which world/start it's running in --
    this is only for labelling the Issue #18 telemetry summary row, matched
    against CONFIG["starts"] the same way Issue #2's device baseline did.
    """
    x, y, _ = pose
    # Go through every start and keep the one with the smallest distance.
    # We compare squared distances so there's no need for a square root --
    # whichever is closest is closest either way.
    best_id = None
    best_distance = None
    for start in CONFIG["starts"]:
        dx = start["pose"][0] - x
        dy = start["pose"][1] - y
        distance = dx * dx + dy * dy
        if best_distance is None or distance < best_distance:
            best_id = start["id"]
            best_distance = distance
    return best_id


# Report Section 2.4 -- How much clearance to leave around obstacles
# (uniform one-cell inflation: the option that sealed off S2/S4/S6/S8, Table 4)
def inflate_grid(grid):
    """Return a copy of grid with every obstacle's 4-connected free neighbours also marked obstacle."""
    # Make the obstacles one cell "fatter" in every direction so the planned
    # path keeps a gap from walls -- the robot has a body, not zero width.
    inflated = grid.copy()
    rows, cols = grid.shape
    for row in range(rows):
        for col in range(cols):
            # Only obstacle cells (value 1) spread out into their neighbours.
            if grid[row, col] != 1:
                continue
            # Up, down, left, right.
            for d_row, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                n_row, n_col = row + d_row, col + d_col
                if 0 <= n_row < rows and 0 <= n_col < cols:
                    inflated[n_row, n_col] = 1
    return inflated


# Report Section 2.4 -- How much clearance to leave around obstacles
# (the shipped policy: selective inflation, radius 4 -- Table 4, Figure 6)
def selective_inflation(grid, observe_cells, radius):
    """Inflate by one cell, then restore raw values within a Chebyshev radius of each observe cell."""
    # Fatten everything first, then undo it in a square around each station's
    # viewing cell. Without this the stations end up walled off and A* can't
    # reach them at all.
    inflated = inflate_grid(grid)
    rows, cols = grid.shape
    for obs_row, obs_col in observe_cells:
        # Work out the square of cells to restore, clipped to the grid edges.
        row_lo, row_hi = max(0, obs_row - radius), min(rows - 1, obs_row + radius)
        col_lo, col_hi = max(0, obs_col - radius), min(cols - 1, obs_col + radius)
        for row in range(row_lo, row_hi + 1):
            for col in range(col_lo, col_hi + 1):
                # Only restore cells inside the square radius of the station.
                if max(abs(row - obs_row), abs(col - obs_col)) <= radius:
                    inflated[row, col] = grid[row, col]
    return inflated


# Report Section 2.4 -- How much clearance to leave around obstacles
# (single switch point for the policy; Figure 6 was generated by calling this
# function directly, so the figure shows the real planning grid)
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


# Report Section 5.2 -- Planning a route (A* heuristic: Manhattan distance,
# matching the 4-connected grid)
def heuristic(a, b):
    """Manhattan distance for 4-connected grid motion."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# Report Section 5.2 -- Planning a route (the A* search itself, adapted from
# the Workshop 8 starter code; all 24 start/station pairs produce a valid
# path, slowest plan 0.390 ms, unreachable goals return [] without raising)
def astar(grid, start, goal):
    """A* on a 4-connected grid (Issue #12). Returns [(row, col), ...] or [] if unreachable.

    Plan on the grid returned by apply_clearance_policy, not the raw grid.
    """
    rows, cols = grid.shape

    # If we're starting inside a wall, or asked to reach one, there's no path.
    if grid[start] == 1 or grid[goal] == 1:
        return []

    # open_set is the "to visit" list, kept sorted cheapest-first by heapq.
    # g_cost[cell] = steps taken to reach that cell so far.
    # came_from[cell] = which cell we arrived from, used to rebuild the path.
    open_set = [(heuristic(start, goal), start)]
    g_cost = {start: 0}
    came_from = {}

    while open_set:
        # Take the cell with the smallest f_cost (steps so far + guess to go).
        _, current = heapq.heappop(open_set)

        # Reached the goal: walk the came_from chain backwards to the start,
        # then flip it so the path reads start -> goal.
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

            # Skip anything off the edge of the map or inside an obstacle.
            if n_row < 0 or n_row >= rows or n_col < 0 or n_col >= cols:
                continue
            if grid[n_row, n_col] == 1:
                continue

            # Every move to a neighbouring cell costs 1 step.
            new_g = g_cost[current] + 1

            # Only keep this route if the neighbour is new, or we just found a
            # cheaper way of getting to it than we had before.
            if neighbour not in g_cost or new_g < g_cost[neighbour]:
                g_cost[neighbour] = new_g
                f_cost = new_g + heuristic(neighbour, goal)
                heapq.heappush(open_set, (f_cost, neighbour))
                came_from[neighbour] = current

    return []


# Report Section 5.2 -- Planning a route (waypoint simplification: keeps only
# direction-change cells, cutting waypoint count by ~82% on average, 76-93%
# across the full 24-pair set)
def simplify_path(path):
    """Collapse runs of collinear cells (Issue #13), keeping start, end and every corner.

    The direct line between two kept points retraces exactly the straight run
    of free cells the search already found, so this cannot introduce a
    collision the original path didn't already avoid.
    """
    if len(path) <= 2:
        return list(path)
    # Always keep the first cell, then only keep a cell if the direction of
    # travel changes there (a corner). Straight runs in between get dropped.
    simplified = [path[0]]
    for i in range(1, len(path) - 1):
        prev_dir = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        next_dir = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        # Direction changed, so this cell is a corner and has to stay.
        if prev_dir != next_dir:
            simplified.append(path[i])
    # Always keep the last cell too -- that's the goal.
    simplified.append(path[-1])
    return simplified


# Report Section 5.2/5.3 -- turns the simplified grid-cell plan into the
# world-coordinate waypoint list that follow_path()/Navigator drive along
def path_to_waypoints(path):
    """Grid cell path -> list of world (x, y) waypoints, one per cell centre."""
    # Turn each grid cell of the plan back into a real-world point the robot
    # can actually drive to.
    waypoints = []
    for row, col in path:
        waypoints.append(grid_to_world(row, col))
    return waypoints


# Small helper used to sort stations by their id. sorted() needs a function
# that says which part of each station to compare; this returns the id text.
def station_id_of(station):
    return station["id"]


# Report Section 2.5/5.5 -- Which order to visit the stations (nearest-first
# by real A* path cost, recomputed after each visit -- Table 5's 155/138/141
# cells beat the fixed-sweep alternative from every start)
def next_station(current_pose, unvisited, grid):
    """Choose the next station to inspect by computed A* path cost (Issue #15).

    current_pose: (x, y, ...) world pose. unvisited: station dicts (a subset
    of CONFIG["stations"]). grid: the planning grid (Issue #11 policy) to
    measure path cost on. Returns the station dict reached by the shortest
    A* path, or None if unvisited is empty. Deterministic: unvisited is
    sorted by id before comparing, so ties always resolve the same way.
    """
    current_cell = world_to_grid(current_pose[0], current_pose[1])

    # Sort by station id first so the loop always looks at them in the same
    # order. That way, if two stations tie on path length, we always pick the
    # same one and the robot behaves the same way every run.
    stations_in_order = sorted(unvisited, key=station_id_of)

    best_station = None
    best_cost = None
    for station in stations_in_order:
        observe_x, observe_y = station["observe"]
        goal_cell = world_to_grid(observe_x, observe_y)
        path = astar(grid, current_cell, goal_cell)
        # No path at all counts as infinitely expensive, so a station we can
        # actually reach always wins over one we can't.
        if path:
            cost = len(path)
        else:
            cost = float("inf")
        if best_cost is None or cost < best_cost:
            best_station = station
            best_cost = cost
    return best_station
