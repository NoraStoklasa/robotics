---
title: "[Nav] Implement motion primitives and pose utilities"
labels: [stream:navigation, type:feature, priority:P0]
milestone: "M1 - Sensing and motion baseline"
stream: navigation
depends_on: ["[Sys] Verify all three worlds run and record the device baseline"]
estimate: "M"
---

## Why
Every later behaviour issues its commands through a small, tested motion and geometry layer instead of writing raw wheel speeds inline.

## Rubric link
Technical approach, implementation and system integration (9 marks).

## Scope
- On top of the provided `set_speed(left, right)`, add: `drive_forward(speed)`, `turn_left(speed)`, `turn_right(speed)`, `rotate_in_place(speed)` and `stop()`.
- On top of the provided `get_pose()`, add: `normalise_angle(a)` folding any angle to `(-pi, pi]`; `distance_to(x, y)`; `bearing_to(x, y)` returning the heading error to a world point in the robot frame; and `pose_to_cell()` wrapping the provided `world_to_grid`.
- Measure the actual straight-line speed and the in-place rotation rate by logging `get_pose()` over a fixed number of timesteps, and record both in `docs/motion_baseline.md`.
- Enforce the Week 8 engineering pattern: **one place** where wheel commands are clamped. Every motion primitive routes through a single `clamp_speed` before `set_speed`, so a later tuning change cannot leave two layers with inconsistent limits.
- Implement `stop()` as a deliberate, always-available behaviour, not an afterthought — the workshop calls it out as needed for normal operation, target loss, obstacle emergencies and debugging alike.
- Note the commanded-vs-achieved wheel speed: the starter clamps to `MAX_SPEED = 10`, so record the speed the robot actually reaches rather than assuming the commanded value is delivered.

## Acceptance criteria
- [ ] `normalise_angle` returns a value in `(-pi, pi]` for the inputs `0`, `pi`, `-pi`, `3*pi`, `-3*pi` and `7.5`.
- [ ] `bearing_to` returns a value whose magnitude is under 0.05 rad when the robot faces a point directly ahead, and within 0.05 rad of `+pi/2` for a point directly to its left.
- [ ] `pose_to_cell()` at each of starts A, B and C returns the same cell as `world_to_grid` applied to the matching `CONFIG["starts"]` pose.
- [ ] Driving forward for a fixed number of timesteps moves the robot along its own heading with a lateral drift under 0.05 m, measured from logged `get_pose()` values.
- [ ] `docs/motion_baseline.md` records the achieved forward speed in m/s and the rotation rate in rad/s.
- [ ] `grep -n 'set_speed' ` over the group code shows every call originating from the motion layer, with the clamp applied in exactly one function.

## Evidence for the report
`docs/motion_baseline.md` — the measured speed and rotation-rate table, cited when justifying controller gains and the 4:00 time budget.

## Course reference
Workshop 8, Part 2 — differential-drive control through `set_speed`, including forward, left, right, in-place rotation and a safe stop.

## Out of scope
Closed-loop heading control toward a waypoint — that is `[Nav] Follow a waypoint path with P-controlled heading`.
