"""Regenerate the report figures that are not produced by any other tool.

Outputs (written to docs/data/):
  clearance_comparison.png   the effect of the clearance policy on reachability
  completion_times.png       completion time for every test matrix run
  architecture.png           the one page system architecture diagram
  state_machine.png          the mission state machine diagram

Run from anywhere:  python tools/build_report_figures.py
"""
import sys, json, csv, math
from pathlib import Path
from collections import deque

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, FancyBboxPatch, FancyArrowPatch

WEBOTS = Path(__file__).resolve().parents[1]      # 3006ICT_group_project_webots
REPO = WEBOTS.parent                              # repository root
OUT = REPO / "docs" / "data"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(WEBOTS / "controllers" / "group_project_controller"))
import project_utils as pu

GRID = np.load(WEBOTS / "maps" / "occupancy_grid.npy")
CONFIG = json.loads((WEBOTS / "config" / "project_config.json").read_text())
MATRIX_CSV = REPO / "docs" / "data" / "results_matrix.csv"

observe_cells = [pu.world_to_grid(*s["observe"]) for s in CONFIG["stations"]]
station_ids = [s["id"] for s in CONFIG["stations"]]
start_A = next(s for s in CONFIG["starts"] if s["id"] == "A")
start_cell = pu.world_to_grid(start_A["pose"][0], start_A["pose"][1])


def uniform_inflate(grid):
    """Inflate every obstacle by one cell in all 8 directions."""
    out = grid.copy()
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 1:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < rows and 0 <= cc < cols:
                            out[rr, cc] = 1
    return out


def reachable_from(grid, start):
    """4-connected flood fill, same connectivity as the A* search."""
    rows, cols = grid.shape
    seen = np.zeros_like(grid, dtype=bool)
    if grid[start] == 1:
        g = grid.copy(); g[start] = 0
    else:
        g = grid
    q = deque([start]); seen[start] = True
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols and not seen[rr, cc] and g[rr, cc] == 0:
                seen[rr, cc] = True
                q.append((rr, cc))
    return seen


policies = [
    ("Raw grid, no clearance", GRID),
    ("Uniform inflation, one cell", uniform_inflate(GRID)),
    ("Selective inflation, radius 4 (shipped)",
     pu.apply_clearance_policy(GRID, "selective", observe_cells, radius=4)),
]

OBST = "#8A8F98"
FREE = "#FFFFFF"
OK = "#1B7F4B"
BAD = "#C2352B"
START = "#1F4E79"

fig, axes = plt.subplots(1, 3, figsize=(13.5, 5.1))
summary = []
for ax, (title, g) in zip(axes, policies):
    seen = reachable_from(np.asarray(g), start_cell)
    ax.imshow(np.asarray(g), cmap=matplotlib.colors.ListedColormap([FREE, OBST]),
              vmin=0, vmax=1, interpolation="nearest")
    lost = []
    for (r, c), sid in zip(observe_cells, station_ids):
        good = bool(seen[r, c])
        if not good:
            lost.append(sid)
        ax.plot(c, r, "o", ms=9, mfc=OK if good else BAD, mec="black", mew=0.7, zorder=3)
        ax.annotate(sid, (c, r), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=8, fontweight="bold",
                    color="black", zorder=4)
    ax.plot(start_cell[1], start_cell[0], "*", ms=17, mfc=START, mec="black", mew=0.7, zorder=3)
    ax.annotate("Start A", (start_cell[1], start_cell[0]), textcoords="offset points",
                xytext=(0, -16), ha="center", fontsize=8, color=START, fontweight="bold")
    n_ok = 8 - len(lost)
    sub = f"{n_ok} of 8 stations reachable" + ("" if not lost else "\nlost: " + ", ".join(lost))
    ax.set_title(title, fontsize=10.5, fontweight="bold", pad=8)
    ax.text(0.5, -0.07, sub, transform=ax.transAxes, ha="center", va="top",
            fontsize=9.5, color=(BAD if lost else OK), fontweight="bold")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor("#CCCCCC")
    summary.append((title, n_ok, lost))

handles = [
    Patch(facecolor=OBST, edgecolor="none", label="Obstacle cell"),
    plt.Line2D([], [], marker="o", ls="", mfc=OK, mec="black", ms=8, label="Observation position reachable"),
    plt.Line2D([], [], marker="o", ls="", mfc=BAD, mec="black", ms=8, label="Observation position unreachable"),
    plt.Line2D([], [], marker="*", ls="", mfc=START, mec="black", ms=13, label="Start A"),
]
fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9.5,
           bbox_to_anchor=(0.5, -0.10))
fig.suptitle("Effect of the obstacle clearance policy on which stations can still be reached",
             fontsize=12.5, fontweight="bold", y=0.99)
fig.tight_layout(rect=[0, 0.10, 1, 0.95])
fig.savefig(OUT / "clearance_comparison.png", dpi=170, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("clearance:", summary)

# ---------------------------------------------------------------- completion time
rows = list(csv.DictReader(open(MATRIX_CSV)))
rows.sort(key=lambda r: (r["world"], float(r["completion_time_s"])))
worlds = ["A", "B", "C"]
WCOL = {"A": "#1F4E79", "B": "#2E8B8B", "C": "#B5762A"}

fig, ax = plt.subplots(figsize=(12.2, 5.2))
x = 0; ticks = []; labels = []; boundaries = []
for w in worlds:
    wr = [r for r in rows if r["world"] == w]
    for r in wr:
        t = float(r["completion_time_s"])
        ax.bar(x, t, width=0.76, color=WCOL[w],
               edgecolor="white", linewidth=0.6, zorder=2)
        ax.text(x, t + 4, f"{t:.0f}", ha="center", va="bottom", fontsize=7.4, color="#333333")
        ticks.append(x)
        lab = r["target"].replace("_", " ")
        if r["repeat"] != "1":
            lab += f" (repeat {r['repeat']})"
        labels.append(lab)
        x += 1
    boundaries.append(x - 0.5)
    x += 0.9

ax.axhline(240, color="#C2352B", ls="--", lw=1.6, zorder=3)
ax.text(len(ticks) * 0.5, 246, "240 s mission time limit", color="#C2352B",
        fontsize=10, fontweight="bold", ha="center")
slow = max(rows, key=lambda r: float(r["completion_time_s"]))
ax.axhline(float(slow["completion_time_s"]), color="#8A8F98", ls=":", lw=1.2, zorder=1)
ax.text(0.2, float(slow["completion_time_s"]) + 4,
        f"slowest run {float(slow['completion_time_s']):.2f} s",
        fontsize=8.8, color="#555555")

for b in boundaries[:-1]:
    ax.axvline(b + 0.45, color="#DDDDDD", lw=1)

ax.set_xticks(ticks)
ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=8)
ax.set_ylabel("Completion time (seconds of simulation time)", fontsize=10.5)
ax.set_ylim(0, 275)
ax.set_xlim(-0.9, x - 1.4)
ax.set_title("Completion time for all 25 test matrix runs, grouped by world\n"
             "Every run succeeded, and every run finished inside the limit",
             fontsize=12.5, fontweight="bold", pad=12)
ax.grid(axis="y", color="#EEEEEE", zorder=0)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
handles = [Patch(facecolor=WCOL[w], label=f"World {w}") for w in worlds]
ax.legend(handles=handles, frameon=False, ncol=3, loc="upper right", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "completion_times.png", dpi=170, bbox_inches="tight", facecolor="white")
plt.close(fig)

times = [float(r["completion_time_s"]) for r in rows]
print("runs:", len(rows), "mean:", round(sum(times) / len(times), 2),
      "max:", max(times), "over budget:", sum(1 for t in times if t > 240))
print("outcomes:", {r["outcome"] for r in rows}, "collisions:", {r["collision_flag"] for r in rows})


NAVY = "#1F4E79"
TEAL = "#2E8B8B"
OCHRE = "#B5762A"
GREEN = "#1B7F4B"
RED = "#C2352B"
GREY = "#5A6069"
LGREY = "#8A8F98"


def box(ax, x, y, w, h, title, sub=None, fc=NAVY, fs=9.6, subfs=7.5):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle="round,pad=0.008,rounding_size=0.03",
                                fc=fc, ec=fc, lw=1.4, zorder=2))
    if sub:
        ax.text(x, y + h * 0.22, title, ha="center", va="center", color="white",
                fontsize=fs, fontweight="bold", zorder=3)
        ax.text(x, y - h * 0.18, sub, ha="center", va="center", color="white",
                fontsize=subfs, zorder=3, linespacing=1.35)
    else:
        ax.text(x, y, title, ha="center", va="center", color="white", fontsize=fs,
                fontweight="bold", zorder=3, linespacing=1.4)


def arrow(ax, p0, p1, color=GREY, rad=0.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=13,
                                 lw=1.3, color=color,
                                 connectionstyle=f"arc3,rad={rad}", zorder=1,
                                 shrinkA=2, shrinkB=3))


def lbl(ax, x, y, text, color=GREY, fs=7.6):
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=color,
            bbox=dict(fc="white", ec="none", pad=1.4), zorder=4, linespacing=1.3)


# ===================================================== architecture
fig, ax = plt.subplots(figsize=(13.2, 8.4))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
ax.text(50, 97.5, "System architecture: what each part does and what passes between them",
        ha="center", fontsize=13, fontweight="bold")

box(ax, 16, 88, 27, 7.4, "assessment_mission.json", "the target name for this mission",
    OCHRE, fs=9.2)
box(ax, 50, 88, 27, 7.4, "project_config.json", "station and observe positions", LGREY, fs=9.2)
box(ax, 84, 88, 27, 7.4, "occupancy_grid.npy", "40 x 40 cells, 0.1 m each", LGREY, fs=9.2)

box(ax, 84, 75, 27, 7.0, "apply_clearance_policy()", "selective, radius 4", GREY, fs=9.2)
arrow(ax, (84, 84.2), (84, 78.6))
lbl(ax, 90.5, 81.4, "raw grid")

box(ax, 50, 62, 48, 9.2, "Mission state machine",
    "PLAN   NAVIGATE   OBSERVE   IDENTIFY   GOTO_OBSERVE\nFINAL_ALIGN   FINAL_HOLD   STOP   FAILED",
    NAVY, fs=10.4, subfs=8.2)
arrow(ax, (16, 84.2), (32, 66.8))
lbl(ax, 20.5, 74.5, "target")
arrow(ax, (50, 84.2), (50, 66.8))
lbl(ax, 55.5, 75.5, "stations")
arrow(ax, (76, 71.4), (68, 66.8))
lbl(ax, 78.5, 68.4, "planning grid")

box(ax, 15, 41, 26, 11.0, "Perception",
    "identify_at_station()\nfind_poster_region() then identify()", TEAL, fs=9.6, subfs=7.8)
box(ax, 47, 41, 26, 11.0, "Station search and planning",
    "next_station(), astar(),\nsimplify_path()", TEAL, fs=9.6, subfs=7.8)
box(ax, 79, 41, 26, 11.0, "Navigator",
    "follow_path() plus\nselect_behaviour() safety override", TEAL, fs=9.6, subfs=7.8)

arrow(ax, (33, 57.4), (18, 46.5))
lbl(ax, 22.0, 53.5, "station id")
arrow(ax, (22, 46.5), (38, 57.4), GREEN)
lbl(ax, 33.5, 50.2, "(label, confidence)\nor NO_MATCH", GREEN)
arrow(ax, (47, 57.4), (47, 46.5))
lbl(ax, 54.5, 52.0, "pose, unvisited")
arrow(ax, (66, 57.4), (76, 46.5))
lbl(ax, 68.0, 50.5, "goal (x, y)")
arrow(ax, (83, 46.5), (71, 57.4), GREEN)
lbl(ax, 88.0, 52.5, "arrived, or\nbudget spent", GREEN)
arrow(ax, (60.5, 41), (65.5, 41))
lbl(ax, 63, 44.6, "waypoints")

box(ax, 42, 17, 74, 9.4, "Webots e-puck interface (supplied helpers)",
    "set_speed()      get_pose() from GPS and InertialUnit      camera_bgr()      proximity_values() ps0 to ps7",
    GREY, fs=9.6, subfs=8.0)
arrow(ax, (15, 35.4), (24, 21.8))
lbl(ax, 15.0, 27.5, "camera frame")
arrow(ax, (47, 35.4), (47, 21.8))
lbl(ax, 51.5, 28.0, "pose")
arrow(ax, (76, 35.4), (68, 21.8))
lbl(ax, 79.5, 28.0, "wheel speeds,\nps readings")

box(ax, 90, 17, 16, 9.4, "Telemetry", "run CSV plus one\nsummary row", OCHRE, fs=9.2, subfs=7.6)
arrow(ax, (74, 58.0), (90, 22.0), OCHRE, rad=-0.22)
lbl(ax, 95.0, 29.5, "state, pose,\nlabel, time", OCHRE)

ax.text(50, 6.5,
        "Every arrow is a real call in the shipped controller. The two interfaces agreed before any code was written are\n"
        "identify(crop) returning (label, confidence), and follow_path(waypoints) taking the full simplified waypoint list.",
        ha="center", fontsize=9, color="#444444", style="italic", linespacing=1.6)

fig.savefig(OUT / "architecture.png", dpi=170, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ===================================================== state machine
fig, ax = plt.subplots(figsize=(13.4, 7.8))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
ax.text(50, 98, "Mission state machine: the normal path, and what happens when a component cannot answer",
        ha="center", fontsize=12.6, fontweight="bold")
ax.text(50, 93.6,
        "Green is the normal path.   Orange returns to PLAN with that station marked visited, so the search continues.   Red ends the mission.",
        ha="center", fontsize=8.8, color="#444444", style="italic")

W, H = 17.0, 8.6
row1, row2 = 66.0, 33.0
TOP1 = row1 + H / 2

s1 = [(12.5, "PLAN", "pick the nearest\nunvisited station"),
      (33.5, "NAVIGATE", "drive to the\nobserve position"),
      (55.5, "OBSERVE", "stop and turn to\nobserve_yaw"),
      (78.0, "IDENTIFY", "read frames until\n3 of the last 5 agree")]
for x, n, s in s1:
    box(ax, x, row1, W, H, n, s, NAVY, fs=10.2, subfs=7.5)

s2 = [(24.0, "GOTO_OBSERVE", "close to within\n0.10 m", NAVY),
      (46.0, "FINAL_ALIGN", "turn to the graded\nfinal heading", NAVY),
      (68.0, "FINAL_HOLD", "hold still for\n20 steps", NAVY),
      (89.0, "STOP", "motors at zero,\nmission complete", GREEN)]
for x, n, s, c in s2:
    box(ax, x, row2, W, H, n, s, c, fs=9.8, subfs=7.5)

box(ax, 12.5, 12.0, 17.0, 7.6, "FAILED", "motors at zero", RED, fs=9.8, subfs=7.5)

for (a, _, _), (b, _, _), lab in zip(s1[:-1], s1[1:],
                                     ["station\nchosen", "arrived", "settled and\naligned"]):
    arrow(ax, (a + W / 2, row1), (b - W / 2, row1), GREEN)
    lbl(ax, (a + b) / 2, row1 + 5.9, lab, GREEN, fs=7.3)

for (a, _, _, _), (b, _, _, _), lab in zip(s2[:-1], s2[1:],
                                           ["within 0.10 m", "aligned", "hold complete"]):
    arrow(ax, (a + W / 2, row2), (b - W / 2, row2), GREEN)
    lbl(ax, (a + b) / 2, row2 + 5.9, lab, GREEN, fs=7.3)

# IDENTIFY -> GOTO_OBSERVE
arrow(ax, (78.0, row1 - H / 2), (24.0, row2 + H / 2), GREEN, rad=0.14)
lbl(ax, 52, 50.5, "consensus reached on the mission target", GREEN, fs=8.2)


def elbow_back(ax, x_from, lane, label, color=OCHRE):
    """Route a skip-back from a box top up to a lane, left, then down into PLAN."""
    x_to = 12.5
    ax.plot([x_from, x_from], [TOP1, lane], color=color, lw=1.25, zorder=1)
    ax.plot([x_from, x_to], [lane, lane], color=color, lw=1.25, zorder=1)
    ax.add_patch(FancyArrowPatch((x_to, lane), (x_to, TOP1), arrowstyle="-|>",
                                 mutation_scale=13, lw=1.25, color=color, zorder=1,
                                 shrinkA=0, shrinkB=2))
    lbl(ax, (x_from + x_to) / 2, lane, label, color, fs=7.3)


elbow_back(ax, 33.5, 75.5, "step budget spent")
elbow_back(ax, 55.5, 81.0, "yaw budget spent")
elbow_back(ax, 78.0, 86.5, "wrong label, or 20 frames with no consensus")

arrow(ax, (12.5, row1 - H / 2), (12.5, 15.8), RED)
lbl(ax, 12.5, 42.0, "no unvisited\nstations left", RED, fs=7.4)
arrow(ax, (24.0, row2 - H / 2), (17.0, 15.8), RED)
lbl(ax, 25.5, 23.0, "cannot close\nto 0.10 m", RED, fs=7.4)
arrow(ax, (46.0, row2 - H / 2), (21.0, 14.5), RED, rad=0.16)
lbl(ax, 42.0, 20.0, "cannot align", RED, fs=7.4)

ax.add_patch(FancyBboxPatch((50, 3.5), 47, 18.5,
                            boxstyle="round,pad=0.01,rounding_size=0.02",
                            fc="#F4F6F8", ec=LGREY, lw=1.1, zorder=1))
ax.text(73.5, 19.0, "Checked every step, in every state", ha="center", fontsize=9.2,
        fontweight="bold", color=GREY, zorder=3)
ax.text(73.5, 10.8,
        "240 s budget: a warning is printed at 50, 75 and 90 per cent, then the mission\n"
        "ends FAILED with outcome TIMEOUT.  Degraded mode past 90 per cent: commit to the\n"
        "best sighting so far instead of inspecting more stations.  Stuck detector: no real\n"
        "movement over 200 steps triggers back off, rotate and replan.",
        ha="center", va="center", fontsize=7.9, color="#444444", linespacing=1.7, zorder=3)

fig.savefig(OUT / "state_machine.png", dpi=170, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("diagrams written")
