"""
3006ICT Group Project - Controller

Mission:
    Search the observation stations, identify the requested visual target,
    navigate safely, and stop at the correct target.
"""

import json
import math
import os
# (no Counter/deque -- plain dicts and lists are used instead)

import cv2
import numpy as np
from controller import Robot

import vision_utils
from project_utils import (
    CONFIG,
    ROOT,
    apply_clearance_policy,
    astar,
    grid_to_world,
    nearest_start_id,
    next_station,
    path_to_waypoints,
    simplify_path,
    world_to_grid,
)
from telemetry import TelemetryLogger


# ------------------------------------------------------------------
# Webots setup
# ------------------------------------------------------------------
robot = Robot()
timestep = int(robot.getBasicTimeStep())

left_motor = robot.getDevice("left wheel motor")
right_motor = robot.getDevice("right wheel motor")
camera = robot.getDevice("camera")
# The e-puck's 8 proximity sensors are called ps0 ... ps7, so collect them
# into one list we can loop over.
ps = []
for i in range(8):
    ps.append(robot.getDevice(f"ps{i}"))
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
# The grid cell each station is viewed from. Needed so selective inflation
# knows which cells to leave alone.
STATION_OBSERVE_CELLS = []
for station in CONFIG["stations"]:
    observe_x, observe_y = station["observe"]
    STATION_OBSERVE_CELLS.append(world_to_grid(observe_x, observe_y))
PLANNING_GRID = apply_clearance_policy(GRID, "selective", STATION_OBSERVE_CELLS, radius=4)

# Waypoint-following constants (Issue #13), tuned in docs/control_tuning.md.
KP_HEADING = 8.0
BASE_SPEED = 5.0            # commanded wheel speed (rad/s); MAX_SPEED clamps it
WAYPOINT_TOLERANCE = 0.05   # metres; well under half a grid cell (0.1 m)

# The station observe poses are the final stopping positions, but they are
# very close to the posters. That can make the target crop clipped or too
# distorted for the classifier, especially for targets like wall_clock. For
# the search/identify step, stand a little further back along the same viewing
# line, then move to the real observe pose only after the target is confirmed.
IDENTIFY_BACKOFF_DISTANCE = 0.5  # metres behind the supplied observe pose
IDENTIFY_BACKOFF_STEP = 0.1      # shrink by one grid cell if the full backoff is blocked

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
    # Every wheel command in the whole program goes through here, so the speed
    # limit only has to be applied in one place. np.clip keeps the value
    # between -MAX_SPEED and +MAX_SPEED.
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
    # Webots hands us the camera image as raw bytes in BGRA order. Reshape it
    # into a normal height x width x 4 image, then drop the alpha channel so
    # OpenCV can work with it as an ordinary BGR picture.
    h, w = camera.getHeight(), camera.getWidth()
    image = np.frombuffer(camera.getImage(), np.uint8).reshape(h, w, 4)
    return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)


def proximity_values():
    # Read all 8 proximity sensors and return them as a list, in ps0-ps7 order.
    readings = []
    for sensor in ps:
        readings.append(sensor.getValue())
    return readings


# True if ANY of the listed sensors is reading above the threshold, i.e. at
# least one of them can see something that close.
def any_sensor_above(readings, sensor_indexes, threshold):
    for i in sensor_indexes:
        if readings[i] > threshold:
            return True
    return False


# The biggest reading out of the listed sensors. Used to work out which side
# an obstacle is on, so we know which way to turn away from it.
def largest_reading(readings, sensor_indexes):
    biggest = readings[sensor_indexes[0]]
    for i in sensor_indexes:
        if readings[i] > biggest:
            biggest = readings[i]
    return biggest


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


# How far the robot still has to turn to be facing the way the station says
# it should. Positive means turn left, negative means turn right.
def yaw_error_to(station):
    _, _, yaw = get_pose()
    return normalise_angle(station["observe_yaw"] - yaw)


# Spin on the spot in whichever direction closes that error.
def rotate_towards_yaw(yaw_error):
    if yaw_error > 0:
        rotate_in_place(OBSERVE_TURN_SPEED)
    else:
        rotate_in_place(-OBSERVE_TURN_SPEED)


def pose_to_cell():
    # Which grid square the robot is standing in right now.
    px, py, _ = get_pose()
    return world_to_grid(px, py)


def identify_position_for(station):
    """Return the world point to use for taking the identification image.

    station["observe"] remains the official final stop. This helper only
    gives the camera more standoff before classification by moving backwards
    from observe_yaw, which points at the poster. Some stations have map
    obstacles behind the ideal viewing point, so try the largest clear backoff
    first and shrink toward observe if needed.
    """
    observe_x, observe_y = station["observe"]
    observe_yaw = station["observe_yaw"]

    # Work in 0.1 m steps because the occupancy grid resolution is 0.1 m/cell.
    # This keeps the check easy to explain: try 0.5 m, then 0.4 m, and so on.
    steps = round(IDENTIFY_BACKOFF_DISTANCE / IDENTIFY_BACKOFF_STEP)
    for step in range(steps, -1, -1):
        distance = step * IDENTIFY_BACKOFF_STEP
        identify_x = observe_x - distance * math.cos(observe_yaw)
        identify_y = observe_y - distance * math.sin(observe_yaw)
        identify_cell = world_to_grid(identify_x, identify_y)

        # Use only cells that are free in both the real occupancy grid and the
        # inflated planning grid. That avoids choosing a viewing point inside
        # an obstacle or too close to one.
        if GRID[identify_cell] == 0 and PLANNING_GRID[identify_cell] == 0:
            return identify_x, identify_y

    # The observe cell itself should be free, but keep a final fallback so this
    # helper never prevents the mission from trying a station.
    return observe_x, observe_y


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
    # If our own cell reads as blocked, A* would refuse to start. We're
    # physically standing there, so copy the grid and mark just that one cell
    # free for this plan only -- the real grid is left untouched.
    if grid[start_cell] == 1:
        grid = grid.copy()
        grid[start_cell] = 0
    raw_path = astar(grid, start_cell, goal_cell)
    simplified = simplify_path(raw_path)
    # [1:] drops the first waypoint, which is the cell we're already standing
    # in -- no point driving to where we already are.
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
        # Keep steering at this waypoint until we're close enough to it.
        while distance_to(wx, wy) > WAYPOINT_TOLERANCE:
            # P control: the further off we're pointing, the harder we turn.
            error = bearing_to(wx, wy)
            turn = kp * error
            # Slow down when the heading error is big, so the robot turns
            # roughly on the spot instead of driving off in a wide curve.
            # max(0.3, ...) stops it slowing all the way to a standstill.
            speed = base_speed * max(0.3, 1.0 - abs(error) / math.pi)
            # One wheel faster than the other = turn while driving.
            set_speed(speed - turn, speed + turn)
            yield (wx, wy)
    stop()


# ------------------------------------------------------------------
# Reactive avoidance with recovery (Issue #14)
# ------------------------------------------------------------------
# Which way to turn to get away from an obstacle. If only one side can see
# it, turn away from that side. If both can, turn away from whichever side is
# reading closest. Used by both the WARN (AVOID) and STOP responses.
def turn_away_direction(readings, left_triggered, right_triggered):
    if left_triggered and not right_triggered:
        return "right"
    if right_triggered and not left_triggered:
        return "left"
    left_max = largest_reading(readings, FRONT_LEFT_PS)
    right_max = largest_reading(readings, FRONT_RIGHT_PS)
    if left_max >= right_max:
        return "right"
    return "left"


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
        # The last STUCK_WINDOW_STEPS positions, oldest first. Used to notice
        # the robot has stopped making progress.
        self.pos_history = []
        self.step_count = 0
        self.behaviour_log = []

    # True once the robot has arrived at its goal.
    def done(self):
        return self.state == "DONE"

    def _log(self, behaviour, detail=""):
        # Telemetry (Issue #14): log every behaviour *switch*, not every step.
        if behaviour != self.last_behaviour:
            entry = (self.step_count, behaviour, detail)
            self.behaviour_log.append(entry)
            print(f"BEHAVIOUR step={self.step_count} -> {behaviour} {detail}".rstrip())
            self.last_behaviour = behaviour

    # The point we're currently steering at: the next waypoint if there is
    # one, otherwise the final goal.
    def _current_target(self):
        if self.wp_index < len(self.waypoints):
            return self.waypoints[self.wp_index]
        return self.goal_x, self.goal_y

    # Ask A* for a fresh path from wherever we are now, and pick the state to
    # go into based on what came back.
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

    # One step of ordinary path following: same P control as follow_path,
    # but written so it can be called once per control step.
    def _drive_to_waypoint(self):
        wx, wy = self._current_target()
        # Close enough to this waypoint, so move on to the next one.
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

    # Called once per control step. Works through the states in priority
    # order: recovery first, then obstacle reactions, then path following.
    def step(self):
        self.step_count += 1
        x, y, _ = get_pose()
        # Remember where we are, and drop the oldest entry so the list only
        # ever holds the last STUCK_WINDOW_STEPS positions.
        self.pos_history.append((x, y))
        if len(self.pos_history) > STUCK_WINDOW_STEPS:
            self.pos_history.pop(0)

        if self.state == "DONE":
            stop()
            return

        if self.state == "PLAN":
            self._replan("initial plan")

        # Stuck detector: runs in every state except while a recovery is
        # already under way, so it can break an endless STOP/AVOID cycle too.
        if self.state not in ("RECOVER_BACKOFF", "RECOVER_ROTATE") and len(self.pos_history) == STUCK_WINDOW_STEPS:
            # Compare where we are now with where we were a full window ago.
            # Barely moved in all that time means we are stuck on something.
            x0, y0 = self.pos_history[0]
            if math.hypot(x - x0, y - y0) < STUCK_MIN_DISPLACEMENT:
                self._log("STUCK_RECOVERY", f"moved <{STUCK_MIN_DISPLACEMENT} m over {STUCK_WINDOW_STEPS} steps")
                self.state = "RECOVER_BACKOFF"
                self.sub_step = 0
                self.pos_history = []

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
                self.pos_history = []
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

        # Read the sensors and work out, for each side, whether something is
        # merely close (WARN) or about to be hit (STOP).
        ps_values = proximity_values()
        left_warn = any_sensor_above(ps_values, FRONT_LEFT_PS, WARN)
        right_warn = any_sensor_above(ps_values, FRONT_RIGHT_PS, WARN)
        left_stop = any_sensor_above(ps_values, FRONT_LEFT_PS, STOP)
        right_stop = any_sensor_above(ps_values, FRONT_RIGHT_PS, STOP)
        behaviour = select_behaviour(left_warn, right_warn, left_stop, right_stop, has_path=bool(self.waypoints))

        if behaviour == "STOP":
            self._log("STOP", f"left={left_stop} right={right_stop}")
            stop()
            # Remember which way to spin; STOP_ROTATE does the spinning.
            self.stop_turn_dir = turn_away_direction(ps_values, left_stop, right_stop)
            self.state = "STOP_ROTATE"
            self.sub_step = 0
            return

        if behaviour == "AVOID":
            self._log("AVOID", f"left={left_warn} right={right_warn}")
            # Steer away from the obstacle straight away, no separate state.
            if turn_away_direction(ps_values, left_warn, right_warn) == "right":
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
# Perception (Issue #29 stub, kept permanently -- not removed once verified,
# unlike the ephemeral test harnesses used to validate Issues #11-#15 -- so
# any component can be stubbed again later to isolate a failure). Default
# off, since the real identify() (Issue #8) is available. Documented in
# README.md.
# ------------------------------------------------------------------
STUB_PERCEPTION = os.environ.get("STUB_PERCEPTION", "0") == "1"
STUB_MATCH_STATION = os.environ.get("STUB_MATCH_STATION", "S1")
# Issue #16 testing only: make the stub disagree on exactly one frame at the
# matching station, to demonstrate a single bad frame being rejected by the
# consensus requirement without derailing the mission. 0 = never disagree.
STUB_NOISE_FRAME = int(os.environ.get("STUB_NOISE_FRAME", "0"))
_stub_call_count = {}


def stub_identify(current_station_id):
    """Perception stub (Issue #29): claims a match at STUB_MATCH_STATION with
    a fixed confidence, NO_MATCH everywhere else. Stands in for identify()'s
    (label, confidence) output without touching the camera, so the mission
    loop can be exercised independent of vision readiness.
    """
    if current_station_id != STUB_MATCH_STATION:
        return vision_utils.NO_MATCH, 0.0

    _stub_call_count[current_station_id] = _stub_call_count.get(current_station_id, 0) + 1
    if _stub_call_count[current_station_id] == STUB_NOISE_FRAME:
        return "headphones" if target != "headphones" else "camera", 0.80  # deliberate disagreeing frame
    return target, 0.95


_DEBUG_CAPTURE_DIR = os.environ.get("DEBUG_CAPTURE_DIR")
_debug_capture_count = {}


def identify_at_station(current_station_id):
    """Capture a frame and identify the target, or use the Issue #29 stub."""
    if STUB_PERCEPTION:
        return stub_identify(current_station_id)
    image = camera_bgr()
    if _DEBUG_CAPTURE_DIR:
        _debug_capture_count[current_station_id] = _debug_capture_count.get(current_station_id, 0) + 1
        cv2.imwrite(f"{_DEBUG_CAPTURE_DIR}/{current_station_id}_frame{_debug_capture_count[current_station_id]:02d}.png", image)
    return vision_utils.identify_frame(image)


# ------------------------------------------------------------------
# Mission state machine (Issue #16)
#
# PLAN -> NAVIGATE -> OBSERVE -> IDENTIFY -> GOTO_OBSERVE -> FINAL_ALIGN -> FINAL_HOLD -> STOP
#                         ^          |
#                         '----------+---> PLAN (NO_MATCH, or component
#                                           failure -- station marked visited)
#
# GOTO_OBSERVE/FINAL_ALIGN can also fall to FAILED if the final approach (Issue
# #17) can't close within ARRIVAL_TOLERANCE or align to observe_yaw within its
# step budget -- there's no other station to retry once the target is confirmed.
#
# Issue #18 adds two things that cut across every state rather than living in
# one: TIME_BUDGET forces FAILED (outcome "TIMEOUT") from any non-terminal
# state once exceeded, and PLAN short-circuits straight to GOTO_OBSERVE with
# the best unconfirmed target sighting so far once DEGRADED_MODE_FRACTION of
# the budget is spent, instead of continuing PLAN -> NAVIGATE -> OBSERVE ->
# IDENTIFY over the remaining unvisited stations.
#
# See docs/architecture.md's state table for the full transition list and
# every state's defined failure behaviour, and docs/interfaces.md for the
# component signatures this drives. Replaces Issue #29's simpler skeleton
# with the real components against an interface that skeleton already proved.
# ------------------------------------------------------------------
IDENTIFY_CONSENSUS_FRAMES = 3   # agreeing frames required, within the trailing window, to accept an identification
IDENTIFY_WINDOW_FRAMES = 5      # trailing window IDENTIFY_CONSENSUS_FRAMES is counted over, so one bad frame doesn't reset progress
IDENTIFY_MAX_FRAMES = 20        # give up on this station (treat as NO_MATCH) past this many frames
OBSERVE_SETTLE_STEPS = 5        # ~0.16 s to stop drifting before the camera is trusted
OBSERVE_YAW_TOLERANCE = 0.05    # rad; Navigator only reaches (x, y), so OBSERVE must align heading itself
OBSERVE_TURN_SPEED = 2.0        # rad/s wheel speed while aligning to observe_yaw
OBSERVE_YAW_STEP_BUDGET = int(os.environ.get("OBSERVE_YAW_STEP_BUDGET", "3000"))  # lower via env var to test the failure path
NAVIGATE_STEP_BUDGET = int(os.environ.get("NAVIGATE_STEP_BUDGET", "3000"))  # ~96 s; lower via env var to test the failure path

# Final stop rule (Issue #17): the literal success criterion is centre-within-
# 0.20 m, stopped, no collision -- so ARRIVAL_TOLERANCE sits well inside that
# with margin for pose noise and the settle, and the mission's own accept/
# reject decision is this distance check, never a step-budget timeout.
ARRIVAL_TOLERANCE = 0.10        # metres; half the 0.20 m requirement
FINAL_HOLD_STEPS = 20           # consecutive zero-velocity steps required before the mission ends
FINAL_ALIGN_STEP_BUDGET = int(os.environ.get("FINAL_ALIGN_STEP_BUDGET", "3000"))  # lower via env var to test the failure path

# Telemetry and the 4:00 time budget (Issue #18).
TELEMETRY_ENABLED = os.environ.get("TELEMETRY_ENABLED", "1") == "1"       # off to measure logging overhead
TELEMETRY_LOG_INTERVAL_STEPS = 10   # ~0.32 s; log at an interval, not every timestep, to keep the loop cheap
TIME_BUDGET = float(os.environ.get("TIME_BUDGET", "240"))                 # seconds; the assessment's 4:00 mission budget
BUDGET_WARN_FRACTIONS = (0.50, 0.75, 0.90)
# Degraded mode: past this much of the budget, stop inspecting further stations
# and commit to the best target-matching evidence seen so far, if any exists.
# DEGRADED_MIN_CONFIDENCE sits above the ~0.0-0.5 confidence real NO_MATCH/wrong-
# label frames produce (see docs/target_identification.md), so only a real,
# if unconfirmed, sighting of the target counts as a candidate worth acting on.
DEGRADED_MODE_FRACTION = 0.90
DEGRADED_MIN_CONFIDENCE = 0.60
RUNS_DIR = ROOT / "runs"
MISSION_SUMMARY_PATH = ROOT.parent / "docs" / "data" / "mission_summary.csv"


class Mission:
    """Drives the whole mission. Call step() once per robot.step(timestep)."""

    def __init__(self, telemetry=None):
        self.state = "PLAN"
        self.unvisited = list(CONFIG["stations"])
        self.station = None
        self.nav = None
        self.nav_steps = 0
        self.settle_steps = 0
        self.yaw_align_steps = 0
        self.identify_frames = 0
        self.last_label = None
        self.last_confidence = 0.0
        self.consensus_count = 0
        # The labels from the last few camera frames, oldest first.
        self.label_window = []
        self.identify_from_observe = False
        self.final_align_steps = 0
        self.final_hold_steps = 0
        self.final_distance = None
        self.final_heading_error = None
        self._last_logged_state = None

        # Issue #18: telemetry, the 4:00 budget, and the degraded-mode fallback.
        self.telemetry = telemetry
        self.start_id = nearest_start_id(get_pose())
        self.mission_start_time = robot.getTime()
        self.telemetry_step_count = 0
        self.budget_fractions_warned = set()
        self.best_candidate = None  # {"station": station_dict, "confidence": float}
        self.outcome = None         # set to "TIMEOUT" only; otherwise inferred from self.state
        self._finished = False

        # Issue #20 matrix runs: a clear terminal banner at start and end, plus
        # running max-proximity and stations-inspected counters for the
        # results-matrix CSV so a run's outcome is obvious without opening a log file.
        self.max_proximity_seen = 0.0
        self.stations_inspected = 0
        print(
            f"\n===== MISSION START: start_pose={self.start_id} target='{target}' "
            f"budget={TIME_BUDGET:.0f}s =====\n"
        )

    # True once the mission has finished, either way.
    def done(self):
        return self.state in ("STOP", "FAILED")

    def _log(self, detail=""):
        # Print on every state transition (not every step), per Issue #16's
        # "prints its state on every transition" acceptance criterion.
        if self.state != self._last_logged_state:
            print(f"MISSION: state={self.state} {detail}".rstrip())
            self._last_logged_state = self.state

    # Give up on this station and go back to PLAN to choose another one.
    def _skip_current_station(self, reason):
        print(f"MISSION: {reason}, marking {self.station['id']} visited")
        self.stations_inspected += 1
        # Rebuild the unvisited list without this station, so PLAN doesn't
        # send us straight back to it.
        still_unvisited = []
        for s in self.unvisited:
            if s["id"] != self.station["id"]:
                still_unvisited.append(s)
        self.unvisited = still_unvisited
        self.state = "PLAN"

    # How many simulated seconds the mission has been running for.
    def _elapsed_time(self):
        return robot.getTime() - self.mission_start_time

    # Print a warning as we pass 50%, 75% and 90% of the time budget, and
    # fail the mission outright once the whole budget is gone.
    def _check_time_budget(self):
        fraction = self._elapsed_time() / TIME_BUDGET
        for warn_fraction in BUDGET_WARN_FRACTIONS:
            if fraction >= warn_fraction and warn_fraction not in self.budget_fractions_warned:
                self.budget_fractions_warned.add(warn_fraction)
                print(
                    f"MISSION: TIME BUDGET {warn_fraction * 100:.0f}% consumed "
                    f"({self._elapsed_time():.1f}s / {TIME_BUDGET:.0f}s)"
                )
        if fraction >= 1.0 and not self.done():
            self.outcome = "TIMEOUT"
            self.state = "FAILED"
            self._log(f"TIME_BUDGET of {TIME_BUDGET:.0f}s exceeded")
            stop()

    def _check_degraded_mode(self):
        # Issue #18 degraded mode: cross-cutting like the budget check above,
        # not just a PLAN-time decision -- a station chosen before the 90%
        # mark can still be mid-NAVIGATE/OBSERVE/IDENTIFY when the mark is
        # crossed, and waiting for that visit to finish naturally could burn
        # the rest of the budget on the wrong station. GOTO_OBSERVE onward is
        # excluded because that means the real target is already confirmed
        # and committed to -- nothing left to preempt.
        if self.state in ("GOTO_OBSERVE", "FINAL_ALIGN", "FINAL_HOLD", "STOP", "FAILED"):
            return
        if self.best_candidate is None:
            return
        if self._elapsed_time() / TIME_BUDGET < DEGRADED_MODE_FRACTION:
            return
        self.station = self.best_candidate["station"]
        self._log(
            f"DEGRADED MODE: budget {self._elapsed_time():.0f}s/{TIME_BUDGET:.0f}s consumed, "
            f"committing to {self.station['id']} (confidence={self.best_candidate['confidence']:.2f}) "
            "instead of continuing the current station visit or inspecting others"
        )
        observe_x, observe_y = self.station["observe"]
        self.nav = Navigator(observe_x, observe_y)
        self.nav_steps = 0
        self.state = "GOTO_OBSERVE"

    def _note_candidate(self, label, confidence):
        # Issue #18 degraded mode's evidence: any real (non-consensus-confirmed)
        # sighting of the target, kept even after the station is marked visited.
        if label != target or confidence < DEGRADED_MIN_CONFIDENCE:
            return
        if self.best_candidate is None or confidence > self.best_candidate["confidence"]:
            self.best_candidate = {"station": self.station, "confidence": confidence}

    def _log_telemetry_row(self):
        if self.telemetry is None or not self.telemetry.enabled:
            return
        self.telemetry_step_count += 1
        if self.telemetry_step_count % TELEMETRY_LOG_INTERVAL_STEPS != 0:
            return
        x, y, yaw = get_pose()
        # There is no Navigator yet during the very first PLAN step.
        if self.nav is not None:
            behaviour = self.nav.last_behaviour
        else:
            behaviour = ""
        if self.station:
            station_id = self.station["id"]
        else:
            station_id = ""
        self.telemetry.log_step(
            sim_time=round(self._elapsed_time(), 3),
            state=self.state,
            x=round(x, 3),
            y=round(y, 3),
            yaw=round(yaw, 3),
            station=station_id,
            label=self.last_label or "",
            confidence=round(self.last_confidence, 3),
            behaviour=behaviour or "",
            max_proximity=round(largest_reading(proximity_values(), (0, 1, 2, 3, 4, 5, 6, 7)), 1),
        )

    def _finish(self):
        if self._finished:
            return
        self._finished = True
        # self.outcome is only ever set for a timeout. Otherwise the mission
        # succeeded if it ended in the STOP state, and failed if it didn't.
        if self.outcome:
            outcome = self.outcome
        else:
            if self.state == "STOP":
                outcome = "SUCCESS"
            else:
                outcome = "FAILED"
        elapsed = self._elapsed_time()
        collision_flag = self.max_proximity_seen > STOP
        over_budget = elapsed > TIME_BUDGET
        # Work these out first so the printing below stays readable.
        if self.station:
            station_id = self.station["id"]
        else:
            station_id = ""
        if self.final_distance is not None:
            distance_text = f"{self.final_distance:.3f}"
        else:
            distance_text = ""

        if self.telemetry is not None:
            self.telemetry.log_summary(
                start_id=self.start_id,
                target=target,
                station=station_id,
                final_distance=distance_text,
                completion_time=f"{elapsed:.2f}",
                outcome=outcome,
            )

        # Issue #20 matrix runs: everything a run row in results_matrix.csv
        # needs, printed as one unmissable block so a failed/void run is
        # obvious at a glance in the Webots console without opening the CSVs.
        # Build each bit of text separately, then print it all at the end.
        if outcome == "SUCCESS":
            result_icon = "PASS"
        else:
            result_icon = "FAIL"

        if self.station:
            station_text = self.station["id"]
        else:
            station_text = "none"

        if self.final_distance is not None:
            distance_line = f"{self.final_distance:.3f}"
        else:
            distance_line = "n/a"

        if over_budget:
            budget_warning = "  *** OVER 240s BUDGET ***"
        else:
            budget_warning = ""

        if collision_flag:
            collision_warning = "  *** COLLISION (above STOP threshold) ***"
        else:
            collision_warning = ""

        print(
            "\n===== MISSION RESULT: "
            f"{result_icon} =====\n"
            f"  outcome:              {outcome}\n"
            f"  start_pose:           {self.start_id}\n"
            f"  target:               {target}\n"
            f"  station_reached:      {station_text}\n"
            f"  final_distance_m:     {distance_line}\n"
            f"  completion_time_s:    {elapsed:.2f}"
            f"{budget_warning}\n"
            f"  stations_inspected:   {self.stations_inspected}\n"
            f"  max_proximity:        {self.max_proximity_seen:.1f}"
            f"{collision_warning}\n"
            "===========================================\n"
        )

    def step(self):
        self._check_time_budget()
        self._check_degraded_mode()
        self._log_telemetry_row()
        # Keep track of the closest we ever got to anything, for the report's
        # "did this run collide?" column.
        closest_now = largest_reading(proximity_values(), (0, 1, 2, 3, 4, 5, 6, 7))
        if closest_now > self.max_proximity_seen:
            self.max_proximity_seen = closest_now
        if self.state == "PLAN":
            self._plan()
        elif self.state == "NAVIGATE":
            self._navigate()
        elif self.state == "OBSERVE":
            self._observe()
        elif self.state == "IDENTIFY":
            self._identify()
        elif self.state == "GOTO_OBSERVE":
            self._goto_observe()
        elif self.state == "FINAL_ALIGN":
            self._final_align()
        elif self.state == "FINAL_HOLD":
            self._final_hold()
        else:  # STOP or FAILED: terminal, both end in the deliberate stop()
            stop()
        if self.done():
            self._finish()

    # PLAN: pick the cheapest unvisited station to go and look at next.
    def _plan(self):
        if not self.unvisited:
            self.state = "FAILED"
            self._log("no unvisited stations left")
            stop()
            return
        pose = get_pose()
        self.station = next_station(pose, self.unvisited, PLANNING_GRID)
        identify_x, identify_y = identify_position_for(self.station)
        observe_x, observe_y = self.station["observe"]
        self.identify_from_observe = math.isclose(identify_x, observe_x) and math.isclose(identify_y, observe_y)
        self._log(
            f"chosen={self.station['id']} from pose=({pose[0]:.2f}, {pose[1]:.2f}) "
            f"identify_pose=({identify_x:.2f}, {identify_y:.2f})"
        )
        self.nav = Navigator(identify_x, identify_y)
        self.nav_steps = 0
        self.state = "NAVIGATE"

    # NAVIGATE: let the Navigator drive us to the identify pose.
    def _navigate(self):
        self._log(f"station={self.station['id']} final_observe={self.station['observe']}")
        self.nav.step()
        self.nav_steps += 1
        if self.nav.done():
            self.settle_steps = 0
            self.yaw_align_steps = 0
            self.state = "OBSERVE"
        elif self.nav_steps >= NAVIGATE_STEP_BUDGET:
            self._skip_current_station(f"NAVIGATE failed to reach {self.station['id']} within the step budget")

    # OBSERVE: turn on the spot to face the poster, then sit still for a
    # moment so the camera image isn't blurred by movement.
    def _observe(self):
        self._log(f"station={self.station['id']}")
        # Reaching the observe (x, y) says nothing about which way the robot
        # is facing -- Navigator only cares about position. Rotate to the
        # station's observe_yaw before the camera can be trusted; only start
        # the settle countdown once heading is actually aligned.
        yaw_error = yaw_error_to(self.station)
        if abs(yaw_error) > OBSERVE_YAW_TOLERANCE:
            self.yaw_align_steps += 1
            if self.yaw_align_steps >= OBSERVE_YAW_STEP_BUDGET:
                self._skip_current_station(f"OBSERVE failed to align heading at {self.station['id']} within the step budget")
                return
            rotate_towards_yaw(yaw_error)
            self.settle_steps = 0
            return

        stop()
        self.settle_steps += 1
        if self.settle_steps >= OBSERVE_SETTLE_STEPS:
            self.identify_frames = 0
            self.last_label = None
            self.consensus_count = 0
            self.label_window = []
            self.state = "IDENTIFY"

    # IDENTIFY: take camera frames and only believe the answer once the same
    # label comes back on enough frames in a row.
    def _identify(self):
        self._log(f"station={self.station['id']}")
        label, confidence = identify_at_station(self.station["id"])
        self.identify_frames += 1
        self.last_confidence = confidence
        self._note_candidate(label, confidence)

        # Add this frame's answer to the rolling window, keeping only the
        # last IDENTIFY_WINDOW_FRAMES frames.
        self.label_window.append(label)
        if len(self.label_window) > IDENTIFY_WINDOW_FRAMES:
            self.label_window.pop(0)

        # Count how many times each real label appears in that window
        # (NO_MATCH doesn't count as a vote for anything).
        label_counts = {}
        for seen in self.label_window:
            if seen == vision_utils.NO_MATCH:
                continue
            if seen in label_counts:
                label_counts[seen] = label_counts[seen] + 1
            else:
                label_counts[seen] = 1

        # The label with the most votes wins. We only swap on a strictly
        # bigger count, so on a tie the label we saw first keeps the lead.
        self.last_label = None
        self.consensus_count = 0
        for seen in label_counts:
            if label_counts[seen] > self.consensus_count:
                self.last_label = seen
                self.consensus_count = label_counts[seen]

        print(
            f"MISSION: state=IDENTIFY station={self.station['id']} frame={self.identify_frames} "
            f"label={label} confidence={confidence:.2f} "
            f"consensus={self.consensus_count}/{IDENTIFY_CONSENSUS_FRAMES} (of last {len(self.label_window)} frames)"
        )

        if self.consensus_count >= IDENTIFY_CONSENSUS_FRAMES:
            if self.last_label == target:
                print(f"MISSION: IDENTIFY confirmed '{target}' at {self.station['id']} after {IDENTIFY_CONSENSUS_FRAMES} of the last {IDENTIFY_WINDOW_FRAMES} frames")
                self.stations_inspected += 1
                observe_x, observe_y = self.station["observe"]
                self.nav = Navigator(observe_x, observe_y)
                self.nav_steps = 0
                self.state = "GOTO_OBSERVE"
            else:
                self._skip_current_station(f"IDENTIFY confirmed non-target label '{self.last_label}' at {self.station['id']}")
        elif self.identify_frames >= IDENTIFY_MAX_FRAMES:
            if not self.identify_from_observe:
                print(
                    f"MISSION: IDENTIFY reached {IDENTIFY_MAX_FRAMES} frames with no consensus at "
                    f"{self.station['id']}, retrying from observe pose"
                )
                self.identify_from_observe = True
                observe_x, observe_y = self.station["observe"]
                self.nav = Navigator(observe_x, observe_y)
                self.nav_steps = 0
                self.state = "NAVIGATE"
                return
            self._skip_current_station(f"IDENTIFY reached {IDENTIFY_MAX_FRAMES} frames with no consensus at {self.station['id']}")

    # GOTO_OBSERVE: the target is confirmed, so drive the last bit up to the
    # station's official stopping point.
    def _goto_observe(self):
        self._log(f"station={self.station['id']}")
        # Close in on position, not on a timer: Navigator's own
        # WAYPOINT_TOLERANCE (0.05 m) is already tighter than ARRIVAL_TOLERANCE,
        # but the arrival decision here is the explicit distance check below,
        # not nav.done() -- the step budget is only a stuck-robot safety net,
        # never grounds for declaring the final position acceptable.
        self.nav.step()
        self.nav_steps += 1
        ox, oy = self.station["observe"]
        if distance_to(ox, oy) <= ARRIVAL_TOLERANCE:
            stop()  # position accepted -- FINAL_ALIGN only ever rotates from here, never translates
            self._log(f"within {ARRIVAL_TOLERANCE} m of {self.station['id']} observe, aligning heading")
            self.final_align_steps = 0
            self.state = "FINAL_ALIGN"
        elif self.nav_steps >= NAVIGATE_STEP_BUDGET:
            self.state = "FAILED"
            self._log(f"GOTO_OBSERVE failed to close within {ARRIVAL_TOLERANCE} m of {self.station['id']} within the step budget")
            stop()

    # FINAL_ALIGN: we're in the right place, now turn to face the right way.
    def _final_align(self):
        self._log(f"station={self.station['id']}")
        yaw_error = yaw_error_to(self.station)
        if abs(yaw_error) > OBSERVE_YAW_TOLERANCE:
            self.final_align_steps += 1
            if self.final_align_steps >= FINAL_ALIGN_STEP_BUDGET:
                self.state = "FAILED"
                self._log(f"FINAL_ALIGN failed to align heading at {self.station['id']} within the step budget")
                stop()
                return
            rotate_towards_yaw(yaw_error)
            return
        stop()  # heading accepted -- FINAL_HOLD takes over zeroing velocity from here
        self.final_hold_steps = 0
        self.state = "FINAL_HOLD"

    # FINAL_HOLD: sit completely still for a while, so the marker can see the
    # robot really has stopped, then record the final numbers.
    def _final_hold(self):
        self._log(f"station={self.station['id']}")
        stop()
        self.final_hold_steps += 1
        if self.final_hold_steps < FINAL_HOLD_STEPS:
            return
        ox, oy = self.station["observe"]
        self.final_distance = distance_to(ox, oy)
        _, _, yaw = get_pose()
        self.final_heading_error = normalise_angle(self.station["observe_yaw"] - yaw)
        print(
            f"MISSION: FINAL STOP at {self.station['id']} pose={get_pose()} "
            f"distance_to_observe={self.final_distance:.3f} m heading_error={self.final_heading_error:.3f} rad"
        )
        self.state = "STOP"
        self._log(f"stopped at {self.station['id']}")
        stop()


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
# Sets everything up, then runs the mission one control step at a time until
# it finishes or Webots shuts the controller down.
def main():
    print("Group-project controller started.")
    print("Mission:", MISSION)
    print("target:", target)
    print("Stations:", [s["id"] for s in CONFIG["stations"]])
    print("Camera:", camera.getWidth(), "x", camera.getHeight())
    print("Basic timestep:", timestep)

    robot.step(timestep)  # GPS/IMU need one step before they report real values
    if STUB_PERCEPTION:
        print(f"MISSION: STUB_PERCEPTION on, claiming a match at {STUB_MATCH_STATION}")

    telemetry = TelemetryLogger(RUNS_DIR, MISSION_SUMMARY_PATH, enabled=TELEMETRY_ENABLED)
    mission = Mission(telemetry=telemetry)
    # The main control loop. robot.step() advances the simulation by one
    # timestep and returns -1 when Webots wants us to quit.
    while robot.step(timestep) != -1:
        mission.step()
        if mission.done():
            break


if __name__ == "__main__":
    main()
