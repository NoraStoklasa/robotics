"""
3006ICT Group Project - Controller

Mission:
    Search the observation stations, identify the requested visual target,
    navigate safely, and stop at the correct target.
"""

import json
import math
from pathlib import Path

import cv2
import numpy as np
from controller import Robot

from project_utils import CONFIG, ROOT, world_to_grid, grid_to_world


# ------------------------------------------------------------------
# Webots setup
# ------------------------------------------------------------------
robot = Robot()
timestep = int(robot.getBasicTimeStep())

left_motor = robot.getDevice("left wheel motor")
right_motor = robot.getDevice("right wheel motor")
camera = robot.getDevice("camera")
ps = [robot.getDevice(f"ps{i}") for i in range(8)]
gps = robot.getDevice("gps")
imu = robot.getDevice("imu")

left_motor.setPosition(float("inf"))
right_motor.setPosition(float("inf"))
left_motor.setVelocity(0.0)
right_motor.setVelocity(0.0)

camera.enable(timestep)
gps.enable(timestep)
imu.enable(timestep)
for sensor in ps:
    sensor.enable(timestep)

MAX_SPEED = 6.28  # real e-puck wheel motor limit in Webots (was wrongly set to 10)

# Obstacle-sensor thresholds (Issue #4), measured from logged ps0-ps7 readings
# across wall/barrier/station approaches at many angles - not guessed from the
# workshop's example. STOP sits below the weakest verified near-contact
# reading (station S4's off-centre hit, 226) with real margin, and well below
# barrier B1's steady wedged reading (~350-380). See docs/proximity_calibration.md,
# including a self-correction after an early test-methodology bug.
WARN = 120   # reading above this: something's getting close, be cautious
STOP = 150   # reading above this: about to touch it, stop / avoid now

GRID = np.load(ROOT / "maps" / "occupancy_grid.npy")
MISSION = json.loads((ROOT / "config" / "assessment_mission.json").read_text())
target = MISSION["target"]

# ------------------------------------------------------------------
# Provided low-level helpers
# ------------------------------------------------------------------
def set_speed(left, right):
    left = np.clip(left, -MAX_SPEED, MAX_SPEED)
    right = np.clip(right, -MAX_SPEED, MAX_SPEED)
    left_motor.setVelocity(float(left))
    right_motor.setVelocity(float(right))


def get_pose():
    """Return provided ground-truth-like pose (x, y, yaw)."""
    x, y, _ = gps.getValues()
    yaw = imu.getRollPitchYaw()[2]
    return x, y, yaw


def camera_bgr():
    h, w = camera.getHeight(), camera.getWidth()
    image = np.frombuffer(camera.getImage(), np.uint8).reshape(h, w, 4)
    return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)


def proximity_values():
    return [sensor.getValue() for sensor in ps]


# ------------------------------------------------------------------
# Group implementation
# ------------------------------------------------------------------

# Simple movement commands, built on top of set_speed(). We always go
# through set_speed() so the max-speed limit only ever lives in one place.
def drive_forward(speed):
    # Both wheels the same speed = straight line.
    set_speed(speed, speed)


def turn_left(speed):
    """Curve to the left while still moving forward (left wheel goes slower)."""
    set_speed(speed * 0.3, speed)


def turn_right(speed):
    """Curve to the right while still moving forward (right wheel goes slower)."""
    set_speed(speed, speed * 0.3)


def rotate_in_place(speed):
    """Turn on the spot without moving forward (wheels spin opposite ways)."""
    set_speed(-speed, speed)


def stop():
    set_speed(0.0, 0.0)


# Helper functions for working out angles and distances, built on top of
# the provided get_pose().
def normalise_angle(angle):
    """Rewrite any angle so it falls in (-pi, pi] (in radians).

    atan2's own range includes -pi, which this function must not return:
    -pi and +pi are the same heading, and the acceptance range is half-open
    at the bottom. -pi only comes out of atan2(sin(angle), cos(angle)) when
    sin(angle) rounds to +/-0.0 with cos(angle) negative (e.g. angle == -pi
    exactly), so remap that one boundary case to +pi.
    """
    result = math.atan2(math.sin(angle), math.cos(angle))
    return math.pi if result == -math.pi else result


def distance_to(x, y):
    # Straight-line distance from where the robot is now to point (x, y).
    px, py, _ = get_pose()
    return math.hypot(x - px, y - py)


def bearing_to(x, y):
    """How far the robot needs to turn to face point (x, y). 0 = already
    facing it, positive = turn left, negative = turn right."""
    px, py, yaw = get_pose()
    target_heading = math.atan2(y - py, x - px)
    return normalise_angle(target_heading - yaw)


def pose_to_cell():
    px, py, _ = get_pose()
    return world_to_grid(px, py)


# ------------------------------------------------------------------
# TEMPORARY: Issue #5 poster-visibility capture sweep. Remove this whole
# block once docs/data/poster_captures/ has results for both stations --
# the report itself is built afterwards by
# tools/build_poster_visibility_doc.py, which needs no Webots.
#
# Run ONCE PER STATION, each from that station's own world start (do not
# chain stations in one run -- see the Issue #4 chaining lesson in
# docs/failure_log.md):
#   STATION_ID = "S1"  ->  open worlds/training_start_A.wbt
#   STATION_ID = "S3"  ->  open worlds/training_start_C.wbt
# Both are straight-line reachable from their start and have a clear
# capture pocket -- checked against maps/occupancy_grid.npy before writing
# this. S2/S4/S6/S8 are NOT reachable by a straight line (they need real
# obstacle avoidance, Issue #14), so they are out of scope for this
# crude point-and-shoot mover.
# ------------------------------------------------------------------
STATION_ID = "S1"

# Cross-checked against the exact barrier translation/rotation in the
# world file plus the poster's local offset in TexturedBarrier.proto
# (0, -0.035, 0.145) -- matches this figure to well under 1 mm for both
# S1 and S3, so Issue #5's "verify, don't just trust" is satisfied.
STANDOFF_TO_POSTER = 0.295

DISTANCES_M = [0.295, 0.45, 0.60, 0.80, 1.00, 1.30]
OFFSET_DEG_AT = {0.295: (-15, 15), 0.60: (-15, 15)}
# (0.60, +15) is blocked by an obstacle for S3's geometry specifically --
# confirmed against the occupancy grid, not a bug in the mover.
SKIP_COMBOS = {"S3": {(0.60, 15)}}

REPO_ROOT = ROOT.parent  # ROOT is the Webots project dir; docs/ lives one level up
CAPTURE_DIR = REPO_ROOT / "docs" / "data" / "poster_captures" / STATION_ID


def _poster_centre(station):
    ox, oy = station["observe"]
    yaw = station["observe_yaw"]
    return ox + STANDOFF_TO_POSTER * math.cos(yaw), oy + STANDOFF_TO_POSTER * math.sin(yaw)


def _waypoint(px, py, yaw, distance, offset_deg):
    # A point 'distance' metres back from the poster along its own facing
    # axis, shifted sideways so the poster subtends 'offset_deg' off-centre.
    lateral = distance * math.tan(math.radians(offset_deg))
    wx = px - distance * math.cos(yaw) - lateral * math.sin(yaw)
    wy = py - distance * math.sin(yaw) + lateral * math.cos(yaw)
    return wx, wy


def _turn_to_face(x, y, tol=0.02, max_steps=300):
    """Crude point-and-shoot rotation -- enough to aim the camera for this
    one-off measurement. Not Issue #13's P-controller."""
    steps = 0
    while steps < max_steps:
        b = bearing_to(x, y)
        if abs(b) < tol:
            stop()
            return True
        rotate_in_place(1.5 if b > 0 else -1.5)
        if robot.step(timestep) == -1:
            return False
        steps += 1
    stop()
    return abs(bearing_to(x, y)) < tol


def _drive_to(x, y, tol=0.02, max_steps=3000):
    """Crude point-and-shoot drive: aim, then a short forward burst,
    re-aiming often. Only used for the short, pre-checked hops in this
    capture sweep -- not a general navigator."""
    steps = 0
    while distance_to(x, y) > tol and steps < max_steps:
        if not _turn_to_face(x, y, tol=0.05):
            return False
        burst = 0
        while distance_to(x, y) > tol and burst < 15 and steps < max_steps:
            drive_forward(2.5)
            if robot.step(timestep) == -1:
                return False
            steps += 1
            burst += 1
    stop()
    return distance_to(x, y) <= tol


def _measure_poster_bbox(frame_bgr):
    """Heuristic bounding box for the poster panel: the barrier body is a
    flat grey (PBRAppearance baseColor ~0.29/0.30/0.32), the poster is a
    printed image, so flag pixels that are clearly more saturated or a
    different brightness from the frame's modal (background) value, then
    take the largest connected blob. Approximate, for this measurement
    only -- final target identification is Issue #8."""
    h = frame_bgr.shape[0]
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(int)
    val = hsv[:, :, 2].astype(int)
    bg_val = int(np.median(val))
    mask = ((sat > 40) | (np.abs(val - bg_val) > 35)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    x, y, bw, bh = cv2.boundingRect(c)
    return {
        "x": x, "y": y, "w": bw, "h": bh,
        "clipped_top": bool(y <= 0),
        "clipped_bottom": bool((y + bh) >= h - 1),
    }


def _capture(distance, offset_deg):
    frame = camera_bgr()
    bbox = _measure_poster_bbox(frame)
    tag = f"d{distance:.3f}_o{offset_deg:+03d}".replace(".", "p").replace("+", "p").replace("-", "m")
    frame_path = CAPTURE_DIR / f"{STATION_ID}_{tag}.png"
    cv2.imwrite(str(frame_path), frame)
    debug_path = None
    if bbox is not None:
        debug = frame.copy()
        cv2.rectangle(debug, (bbox["x"], bbox["y"]), (bbox["x"] + bbox["w"], bbox["y"] + bbox["h"]), (0, 0, 255), 1)
        debug_path = CAPTURE_DIR / f"{STATION_ID}_{tag}_bbox.png"
        cv2.imwrite(str(debug_path), debug)
    result = {
        "station": STATION_ID,
        "distance_m": distance,
        "offset_deg": offset_deg,
        "frame": str(frame_path.relative_to(REPO_ROOT)),
        "debug": str(debug_path.relative_to(REPO_ROOT)) if debug_path else None,
        "bbox": bbox,
        "pose": list(get_pose()),
    }
    print(f"[{STATION_ID}] d={distance:.3f} off={offset_deg:+d}  bbox={bbox}")
    return result


def _run_poster_sweep():
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    station = next(s for s in CONFIG["stations"] if s["id"] == STATION_ID)
    px, py = _poster_centre(station)
    yaw = station["observe_yaw"]

    combos = [(d, 0) for d in DISTANCES_M]
    for d, offs in OFFSET_DEG_AT.items():
        combos += [(d, off) for off in offs]
    skip = SKIP_COMBOS.get(STATION_ID, set())
    combos = sorted((d, off) for d, off in combos if (d, off) not in skip)

    results = []
    for d, off in combos:
        wx, wy = _waypoint(px, py, yaw, d, off)
        if not _drive_to(wx, wy):
            print(f"FAILED to reach d={d} off={off} -- stopping sweep, check the world / log to failure_log.md")
            break
        if not _turn_to_face(px, py):
            print(f"WARNING: could not aim exactly at the poster for d={d} off={off}, capturing anyway")
        results.append(_capture(d, off))

    results_path = CAPTURE_DIR / "results.json"
    results_path.write_text(json.dumps(results, indent=2))
    print(f"Saved {len(results)}/{len(combos)} captures for {STATION_ID}. Results: {results_path}")
    print("Now run: python3 tools/build_poster_visibility_doc.py")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    print("Group-project controller started.")
    print("Mission:", MISSION)
    print("target:", target)
    print("Stations:", [s["id"] for s in CONFIG["stations"]])
    print("Camera:", camera.getWidth(), "x", camera.getHeight())
    print("Basic timestep:", timestep)

    printed_pose = False
    while robot.step(timestep) != -1:
        pose = get_pose()
        if not printed_pose:
            print("Start pose (x, y, yaw):", pose)
            printed_pose = True
            _run_poster_sweep()  # TEMPORARY: Issue #5, remove after both stations are captured
        # TO DO

        stop()


if __name__ == "__main__":
    main()
