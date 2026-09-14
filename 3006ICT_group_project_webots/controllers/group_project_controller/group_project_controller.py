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

MAX_SPEED = 10
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
    """Rewrite any angle so it's between -180 and 180 degrees (in radians)."""
    return math.atan2(math.sin(angle), math.cos(angle))


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
