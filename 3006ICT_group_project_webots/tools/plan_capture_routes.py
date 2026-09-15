"""Issue #6: plan the evaluation-frame capture routes, one per training world.

Writes tools/issue6_capture_routes.json, which the temporary capture block in
group_project_controller.py's main() follows. Needs no Webots.

Why multi-leg routes: Issue #5's one-leg point-and-shoot mover could only
reach S1/S3 in a straight line, but an 8-class accuracy test needs frames of
all eight posters. Every leg here is planned with A* on a 0.05 m grid (the
0.1 m grid with 1-cell inflation seals the interior stations off -- see the
project notes) and then verified clear with a 0.045 m body margin against
maps/occupancy_grid.npy before being written out.

Capture spots per station: on the poster's own facing axis at 0.295 m (the
real observe distance), 0.45 m, 0.80 m and 1.00 m, each capped at the
furthest clear standoff for that station -- S4, S5 and S7 are boxed in and
cannot back off past ~0.42-0.56 m, so their frames are all top-clipped
(Issue #5), which is exactly what the robot will see there in the mission.

Uses only CONFIG (observe positions and yaws) and the occupancy grid -- no
world-file or texture information.
"""

from __future__ import annotations

import heapq
import itertools
import json
import math
from pathlib import Path

import numpy as np

WEBOTS_ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((WEBOTS_ROOT / "config" / "project_config.json").read_text())
GRID = np.load(WEBOTS_ROOT / "maps" / "occupancy_grid.npy")
OUT_PATH = WEBOTS_ROOT / "tools" / "issue6_capture_routes.json"

X_MIN, Y_MAX, RES = CONFIG["arena"]["x_min"], CONFIG["arena"]["y_max"], CONFIG["arena"]["resolution"]
MARGIN = 0.045       # e-puck radius ~0.037 m plus a small pad
FINE = 0.05          # planning grid resolution
STANDOFF = 0.295     # observe position to poster face (verified in Issue #5)
TARGET_STANDOFFS = (0.295, 0.45, 0.80, 1.00)
STARTS = {s["id"]: tuple(s["pose"][:2]) for s in CONFIG["starts"]}
STATIONS = {s["id"]: s for s in CONFIG["stations"]}


def free(x: float, y: float) -> bool:
    r, c = int((Y_MAX - y) / RES), int((x - X_MIN) / RES)
    return 0 <= r < GRID.shape[0] and 0 <= c < GRID.shape[1] and GRID[r, c] == 0


def free_m(x: float, y: float) -> bool:
    return all(free(x + dx, y + dy) for dx in (-MARGIN, 0, MARGIN) for dy in (-MARGIN, 0, MARGIN))


def line_clear(a, b) -> bool:
    (x0, y0), (x1, y1) = a, b
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.01))
    return all(free_m(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1))


N = int((CONFIG["arena"]["x_max"] - X_MIN) / FINE)


def cell_xy(i: int, j: int):
    return (X_MIN + (j + 0.5) * FINE, Y_MAX - (i + 0.5) * FINE)


OK = np.array([[free_m(*cell_xy(i, j)) for j in range(N)] for i in range(N)])


def nearest_ok_cell(p):
    """The fine cell containing p may not itself be free with margin even when
    p is (its centre can sit up to 0.035 m away) -- snap to the closest free
    cell that has a verified straight line to the real point."""
    i0, j0 = int((Y_MAX - p[1]) / FINE), int((p[0] - X_MIN) / FINE)
    for r in range(0, 4):
        cands = [(i0 + di, j0 + dj) for di in range(-r, r + 1) for dj in range(-r, r + 1)
                 if 0 <= i0 + di < N and 0 <= j0 + dj < N and OK[i0 + di, j0 + dj]]
        cands.sort(key=lambda c: math.dist(cell_xy(*c), p))
        for c in cands:
            if line_clear(p, cell_xy(*c)):
                return c
    return None


def astar(a, b):
    s, g = nearest_ok_cell(a), nearest_ok_cell(b)
    if s is None or g is None:
        return None
    pq = [(0.0, s)]
    came = {s: None}
    cost = {s: 0.0}
    while pq:
        _, u = heapq.heappop(pq)
        if u == g:
            break
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            v = (u[0] + di, u[1] + dj)
            if not (0 <= v[0] < N and 0 <= v[1] < N) or not OK[v]:
                continue
            c = cost[u] + math.hypot(di, dj)
            if c < cost.get(v, math.inf):
                cost[v] = c
                came[v] = u
                heapq.heappush(pq, (c + math.hypot(v[0] - g[0], v[1] - g[1]), v))
    if g not in came:
        return None
    cells = []
    u = g
    while u is not None:
        cells.append(cell_xy(*u))
        u = came[u]
    path = [a] + cells[::-1] + [b]
    # shortcut to as few straight legs as possible, each one verified clear
    out = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and not line_clear(path[i], path[j]):
            j -= 1
        if not line_clear(path[i], path[j]):
            return None
        out.append(path[j])
        i = j
    return out


def path_len(p) -> float:
    return sum(math.dist(a, b) for a, b in zip(p, p[1:]))


def poster_centre(sid):
    s = STATIONS[sid]
    ox, oy = s["observe"]
    yaw = s["observe_yaw"]
    return (ox + STANDOFF * math.cos(yaw), oy + STANDOFF * math.sin(yaw))


def axis_point(sid, d):
    px, py = poster_centre(sid)
    yaw = STATIONS[sid]["observe_yaw"]
    return (round(px - d * math.cos(yaw), 4), round(py - d * math.sin(yaw), 4))


def max_clear_standoff(sid) -> float:
    obs = tuple(STATIONS[sid]["observe"])
    best = STANDOFF
    for d in np.arange(0.30, 1.305, 0.01):
        w = axis_point(sid, float(d))
        if free_m(*w) and line_clear(obs, w):
            best = float(d)
        else:
            break
    return round(best, 2)


def main() -> int:
    dmax = {sid: max_clear_standoff(sid) for sid in STATIONS}
    standoffs = {sid: sorted({round(min(d, dmax[sid]), 3) for d in TARGET_STANDOFFS}) for sid in STATIONS}
    far = {sid: axis_point(sid, max(standoffs[sid])) for sid in STATIONS}
    near = {sid: axis_point(sid, STANDOFF) for sid in STATIONS}

    sources = dict(STARTS, **{f"near_{sid}": near[sid] for sid in STATIONS})
    cache = {}
    for key, a in sources.items():
        for sid in STATIONS:
            p = astar(a, far[sid])
            cache[(key, sid)] = (p, path_len(p) if p else math.inf)

    # Split the 8 stations over the 3 worlds (<=3 each), best visiting order per
    # world, penalising lopsided splits so no single Webots run is much longer.
    best = None
    ids = list(STATIONS)
    for assign in itertools.product(STARTS, repeat=len(ids)):
        groups = {w: [s for s, a in zip(ids, assign) if a == w] for w in STARTS}
        if any(not g or len(g) > 3 for g in groups.values()):
            continue
        total, plan = 0.0, {}
        for w, g in groups.items():
            best_w = min(
                ((sum(cache[(frm, s)][1] for frm, s in zip([w] + [f"near_{x}" for x in order[:-1]], order)), order)
                 for order in itertools.permutations(g)),
                key=lambda t: t[0],
            )
            total += best_w[0]
            plan[w] = best_w[1]
        counts = [sum(len(standoffs[s]) for s in plan[w]) for w in STARTS]
        score = total + 0.5 * (max(counts) - min(counts))
        if best is None or score < best[0]:
            best = (score, total, plan)
    if best is None or math.isinf(best[1]):
        print("FAIL: no split of the stations has a planned path for every leg")
        return 1
    _, total, plan = best

    routes = {}
    for w in STARTS:
        frm = w
        steps = []
        for sid in plan[w]:
            p, _ = cache[(frm, sid)]
            steps.append({"kind": "travel", "to_station": sid, "waypoints": [list(map(float, q)) for q in p[1:]]})
            for d in sorted(standoffs[sid], reverse=True):   # arrive furthest out, then step in
                steps.append({"kind": "capture", "station": sid, "distance_m": d,
                              "at": list(axis_point(sid, d)), "poster": list(map(lambda v: round(v, 4), poster_centre(sid)))})
            frm = f"near_{sid}"
        routes[w] = {"start": list(STARTS[w]), "stations": list(plan[w]), "steps": steps}

    unsafe = 0
    for w, r in routes.items():
        pos = tuple(r["start"])
        for st in r["steps"]:
            for q in (st["waypoints"] if st["kind"] == "travel" else [st["at"]]):
                if not line_clear(pos, tuple(q)):
                    unsafe += 1
                    print(f"UNSAFE LEG in world {w}: {pos} -> {q}")
                pos = tuple(q)
        n_cap = sum(1 for s in r["steps"] if s["kind"] == "capture")
        n_leg = sum(len(s["waypoints"]) for s in r["steps"] if s["kind"] == "travel")
        print(f"World {w}: {r['stations']}  {n_leg} travel legs, {n_cap} capture spots x 3 headings = {n_cap * 3} frames")
    print("Max clear standoff per station:", dmax)
    print(f"Total travel {total:.2f} m; every leg verified clear: {unsafe == 0}")
    if unsafe:
        return 1
    OUT_PATH.write_text(json.dumps(routes, indent=1))
    print(f"Wrote {OUT_PATH.relative_to(WEBOTS_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
