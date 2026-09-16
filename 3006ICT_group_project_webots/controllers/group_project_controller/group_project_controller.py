"""
3006ICT Group Project - Controller

Mission:
    Search the observation stations, identify the requested visual target,
    navigate safely, and stop at the correct target.
"""

import json
import math
from collections import deque

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

# Reactive avoidance and recovery (Issue #14). Sensor groups per Workshop 8 /
# Issue #4: ps0-ps2 front-right, ps5-ps7 front-left.
FRONT_RIGHT_PS = (0, 1, 2)
FRONT_LEFT_PS = (5, 6, 7)
AVOID_TURN_SPEED = 3.0          # differential applied while steering away during WARN
STOP_ROTATE_SPEED = 3.0
STOP_ROTATE_STEPS = 20          # ~0.64 s rotating away before re-checking, after a STOP
RECOVERY_SPEED = 3.0
RECOVERY_BACKOFF_STEPS = 15     # ~0.48 s reversing
RECOVERY_ROTATE_STEPS = 25      # ~0.8 s rotating, then a full replan
SEARCH_RETRY_STEPS = 30         # how often to retry planning when no path exists
STUCK_WINDOW_STEPS = 200        # ~6.4 s -- longer than the worst-case legitimate turn-in
STUCK_MIN_DISPLACEMENT = 0.02   # metres; well below normal progress over that window
REPLAN_DISPLACEMENT = 0.15      # metres off the next waypoint that forces a full replan

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

    Plans on PLANNING_GRID (the Issue #11 clearance policy) as usual, unless
    the robot's own current cell is marked blocked there -- either the Issue
    #11 inflation margin, or the 0.1 m grid quantizing a near-wall position
    onto the wrong side of a cell boundary (found via Issue #14 testing: a
    real, collision-free pose can round into a cell the *raw* grid also
    calls an obstacle). Either way the robot is physically standing there
    right now, so that one cell is patched free for this call only -- the
    rest of the route keeps the clearance margin.
    """
    start_cell = pose_to_cell()
    goal_cell = world_to_grid(x_goal, y_goal)
    grid = PLANNING_GRID
    if grid[start_cell] == 1:
        grid = grid.copy()
        grid[start_cell] = 0
    raw_path = astar(grid, start_cell, goal_cell)
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
# Reactive avoidance with recovery (Issue #14)
# ------------------------------------------------------------------
def select_behaviour(left_warn, right_warn, left_stop, right_stop, has_path):
    """Workshop 8 priority, one function: Safety > Path following > Search."""
    if left_stop or right_stop:
        return "STOP"
    if left_warn or right_warn:
        return "AVOID"
    if has_path:
        return "FOLLOW"
    return "SEARCH"


class Navigator:
    """Drives to (goal_x, goal_y), handling obstacles the map didn't capture.

    step() is called once per control step. Path following (Issue #13) stays
    the normal case; STOP/WARN readings interrupt it, and a stuck detector
    forces a back-off-rotate-replan recovery if pose stops changing.
    """

    def __init__(self, goal_x, goal_y):
        self.goal_x = goal_x
        self.goal_y = goal_y
        self.waypoints = []
        self.wp_index = 0
        self.state = "PLAN"
        self.sub_step = 0
        self.stop_turn_dir = None
        self.last_behaviour = None
        self.pos_history = deque(maxlen=STUCK_WINDOW_STEPS)
        self.step_count = 0
        self.behaviour_log = []

    def done(self):
        return self.state == "DONE"

    def _log(self, behaviour, detail=""):
        # Telemetry (Issue #14): log every behaviour *switch*, not every step.
        if behaviour != self.last_behaviour:
            entry = (self.step_count, behaviour, detail)
            self.behaviour_log.append(entry)
            print(f"BEHAVIOUR step={self.step_count} -> {behaviour} {detail}".rstrip())
            self.last_behaviour = behaviour

    def _current_target(self):
        if self.wp_index < len(self.waypoints):
            return self.waypoints[self.wp_index]
        return self.goal_x, self.goal_y

    def _replan(self, reason):
        self.waypoints, raw_path = plan_path_to(self.goal_x, self.goal_y)
        self.wp_index = 0
        if not raw_path:
            self._log("SEARCH", f"{reason} (no path found)")
            self.state = "SEARCH"
        elif not self.waypoints:
            self._log("DONE", f"{reason} (already at goal)")
            self.state = "DONE"
            stop()
        else:
            self._log("REPLAN", reason)
            self.state = "FOLLOW"

    def _drive_to_waypoint(self):
        wx, wy = self._current_target()
        if distance_to(wx, wy) <= WAYPOINT_TOLERANCE:
            self.wp_index += 1
            if self.wp_index >= len(self.waypoints):
                self.state = "DONE"
                stop()
                return
            wx, wy = self._current_target()
        error = bearing_to(wx, wy)
        turn = KP_HEADING * error
        speed = BASE_SPEED * max(0.3, 1.0 - abs(error) / math.pi)
        set_speed(speed - turn, speed + turn)

    def step(self):
        self.step_count += 1
        x, y, _ = get_pose()
        self.pos_history.append((x, y))

        if self.state == "DONE":
            stop()
            return

        if self.state == "PLAN":
            self._replan("initial plan")

        # Stuck detector: runs in every state except while a recovery is
        # already under way, so it can break an endless STOP/AVOID cycle too.
        if self.state not in ("RECOVER_BACKOFF", "RECOVER_ROTATE") and len(self.pos_history) == self.pos_history.maxlen:
            x0, y0 = self.pos_history[0]
            if math.hypot(x - x0, y - y0) < STUCK_MIN_DISPLACEMENT:
                self._log("STUCK_RECOVERY", f"moved <{STUCK_MIN_DISPLACEMENT} m over {STUCK_WINDOW_STEPS} steps")
                self.state = "RECOVER_BACKOFF"
                self.sub_step = 0
                self.pos_history.clear()

        if self.state == "RECOVER_BACKOFF":
            self._log("RECOVER_BACKOFF")
            set_speed(-RECOVERY_SPEED, -RECOVERY_SPEED)
            self.sub_step += 1
            if self.sub_step >= RECOVERY_BACKOFF_STEPS:
                self.state = "RECOVER_ROTATE"
                self.sub_step = 0
            return

        if self.state == "RECOVER_ROTATE":
            self._log("RECOVER_ROTATE")
            set_speed(-RECOVERY_SPEED, RECOVERY_SPEED)
            self.sub_step += 1
            if self.sub_step >= RECOVERY_ROTATE_STEPS:
                self.pos_history.clear()
                self._replan("post-recovery replan")
            return

        if self.state == "STOP_ROTATE":
            self._log("STOP_ROTATE", self.stop_turn_dir)
            if self.stop_turn_dir == "right":
                set_speed(STOP_ROTATE_SPEED, -STOP_ROTATE_SPEED)
            else:
                set_speed(-STOP_ROTATE_SPEED, STOP_ROTATE_SPEED)
            self.sub_step += 1
            if self.sub_step >= STOP_ROTATE_STEPS:
                wx, wy = self._current_target()
                if distance_to(wx, wy) > REPLAN_DISPLACEMENT:
                    self._replan("displaced from path after a STOP avoidance")
                else:
                    self._log("RESUME", "re-acquiring nearest waypoint")
                    self.state = "FOLLOW"
            return

        if self.state == "SEARCH":
            self._log("SEARCH", "no path found, rotating and retrying")
            set_speed(-AVOID_TURN_SPEED * 0.5, AVOID_TURN_SPEED * 0.5)
            self.sub_step += 1
            if self.sub_step >= SEARCH_RETRY_STEPS:
                self.sub_step = 0
                self._replan("search retry")
            return

        ps_values = proximity_values()
        left_warn = any(ps_values[i] > WARN for i in FRONT_LEFT_PS)
        right_warn = any(ps_values[i] > WARN for i in FRONT_RIGHT_PS)
        left_stop = any(ps_values[i] > STOP for i in FRONT_LEFT_PS)
        right_stop = any(ps_values[i] > STOP for i in FRONT_RIGHT_PS)
        behaviour = select_behaviour(left_warn, right_warn, left_stop, right_stop, has_path=bool(self.waypoints))

        if behaviour == "STOP":
            self._log("STOP", f"left={left_stop} right={right_stop}")
            stop()
            if left_stop and not right_stop:
                self.stop_turn_dir = "right"    # turn away from the left obstacle
            elif right_stop and not left_stop:
                self.stop_turn_dir = "left"     # turn away from the right obstacle
            else:
                left_max = max(ps_values[i] for i in FRONT_LEFT_PS)
                right_max = max(ps_values[i] for i in FRONT_RIGHT_PS)
                self.stop_turn_dir = "right" if left_max >= right_max else "left"
            self.state = "STOP_ROTATE"
            self.sub_step = 0
            return

        if behaviour == "AVOID":
            self._log("AVOID", f"left={left_warn} right={right_warn}")
            if left_warn and not right_warn:
                set_speed(AVOID_TURN_SPEED, -AVOID_TURN_SPEED)     # turn away from the left obstacle
            elif right_warn and not left_warn:
                set_speed(-AVOID_TURN_SPEED, AVOID_TURN_SPEED)     # turn away from the right obstacle
            else:
                left_max = max(ps_values[i] for i in FRONT_LEFT_PS)
                right_max = max(ps_values[i] for i in FRONT_RIGHT_PS)
                if left_max >= right_max:
                    set_speed(AVOID_TURN_SPEED, -AVOID_TURN_SPEED)
                else:
                    set_speed(-AVOID_TURN_SPEED, AVOID_TURN_SPEED)
            return

        if behaviour == "SEARCH":
            self._replan("no path available")
            return

        self._log("FOLLOW")
        self._drive_to_waypoint()


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
