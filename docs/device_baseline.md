# Device Baseline

Recorded per [Issue #2](.github/issues/02-verify-worlds-device-baseline.md), from an unmodified
run of the three supplied training worlds. `left wheel motor` / `right wheel motor`, `camera`,
`ps0`-`ps7`, `gps` and `imu` all resolved via `getDevice` with no errors — those are the exact
device-name strings the controller uses.

## Common to all three worlds

| Property | Value |
|---|---|
| `robot.getBasicTimeStep()` | 32 ms |
| Camera resolution | 160 x 120 |
| Stations | S1-S8 |
| Console warnings on load | None observed |

## Start pose vs `CONFIG["starts"]`

| World | Logged `get_pose()` (x, y, yaw) | Config pose (x, y, yaw) | Within tolerance? |
|---|---|---|---|
| A | (-1.4595, ~0.0, 0.0) | (-1.45, 0.0, 0.0) | Yes |
| B | (~0.0, -1.4595, 1.5708) | (0.0, -1.45, 1.5708) | Yes |
| C | (1.4595, 0.9000, -3.14159) | (1.45, 0.9, 3.14159) | Yes — yaw wraps to the same orientation (-pi = pi) |

Tolerance required by Issue #2: 0.05 m on x/y, 0.05 rad on yaw. All three starts pass.

## Notes

- No device-name errors in the console on any of the three worlds.
- All three worlds ran with the mission target `soda_can` (`config/assessment_mission.json`);
  target-to-station assignment is not read from this baseline check.
- Basic timestep and start pose were captured with two temporary print statements added to
  `main()` in `group_project_controller.py` (kept in place — harmless, and will be superseded
  once real navigation logic replaces the `# TO DO` sections).
