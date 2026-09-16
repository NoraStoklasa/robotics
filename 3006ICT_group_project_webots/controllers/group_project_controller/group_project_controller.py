"""
3006ICT Group Project - Controller

Mission:
    Search the observation stations, identify the requested visual target,
    navigate safely, and stop at the correct target.
"""

import json
import math

import cv2
import numpy as np
from controller import Robot

from project_utils import (
    CONFIG,
    ROOT,
    apply_clearance_policy,
    astar,
    grid_to_world,
    path_to_waypoints,
    simplify_path,
    world_to_grid,
)


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

# Clearance policy (Issue #11): selective inflation, radius 4, so A* (Issue #12)
# plans a path that keeps a one-cell buffer everywhere except close to a
# station's observe cell, where the raw geometry is restored so all 8 stay
# reachable. Computed once here so every plan_path_to() call reuses it.
STATION_OBSERVE_CELLS = [world_to_grid(*s["observe"]) for s in CONFIG["stations"]]
PLANNING_GRID = apply_clearance_policy(GRID, "selective", STATION_OBSERVE_CELLS, radius=4)

# Waypoint-following constants (Issue #13), tuned in docs/control_tuning.md.
KP_HEADING = 8.0
BASE_SPEED = 5.0            # commanded wheel speed (rad/s); MAX_SPEED clamps it
WAYPOINT_TOLERANCE = 0.05   # metres; well under half a grid cell (0.1 m)

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
# Waypoint following (Issue #13)
# ------------------------------------------------------------------
def plan_path_to(x_goal, y_goal):
    """A* + simplify from the robot's current cell to (x_goal, y_goal).

    Returns (waypoints, raw_path): waypoints excludes the robot's own
    starting cell (it's already there), raw_path is kept for the
    simplification-ratio and collision checks in the report.
    """
    start_cell = pose_to_cell()
    goal_cell = world_to_grid(x_goal, y_goal)
    raw_path = astar(PLANNING_GRID, start_cell, goal_cell)
    simplified = simplify_path(raw_path)
    waypoints = path_to_waypoints(simplified)[1:]
    return waypoints, raw_path


def follow_path(waypoints, base_speed=BASE_SPEED, kp=KP_HEADING):
    """Generator: call next() once per control step until it raises StopIteration.

    Drives to each waypoint in turn with proportional heading control, then
    stops. Speed is cut when the heading error is large so the robot turns
    on the spot-ish before committing to driving forward, rather than
    swinging wide. Yields the (x, y) waypoint currently being driven to, so
    callers can log the true active target instead of assuming it never changes.
    """
    for wx, wy in waypoints:
        while distance_to(wx, wy) > WAYPOINT_TOLERANCE:
            error = bearing_to(wx, wy)
            turn = kp * error
            speed = base_speed * max(0.3, 1.0 - abs(error) / math.pi)
            set_speed(speed - turn, speed + turn)
            yield (wx, wy)
    stop()


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
        # TO DO

        stop()


if __name__ == "__main__":
    main()
