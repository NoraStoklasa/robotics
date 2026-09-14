# Motion Baseline

Recorded per [Issue #3](.github/issues/03-motion-primitives-pose-utilities.md), measured with
`drive_forward(5.0)` and `rotate_in_place(5.0)` (commanded wheel speed 5.0 rad/s, below the
`MAX_SPEED = 10` clamp), each held for 60 timesteps (1.92 s at the 32 ms basic timestep).

## Achieved speed vs commanded

| Test | Commanded | Achieved |
|---|---|---|
| Forward drive | 5.0 rad/s (wheels) | 0.1000 m/s (linear) |
| Rotate in place | 5.0 rad/s (wheels) | 0.9971 rad/s (body) |

The commanded value is a wheel angular speed; the achieved value is the robot's actual linear or
angular speed, which is smaller because of the wheel radius and axle length — this is why the
project measures achieved speed directly rather than assuming the commanded number is delivered.

## Straight-line accuracy

Over the 0.192 m forward-drive test: forward distance 0.1919 m, lateral drift 0.0000 m.
Well within the 0.05 m tolerance required by Issue #3 — `drive_forward` with equal wheel speeds
tracks a straight line.

## How this was measured

Two temporary blocks were added to `main()` in `group_project_controller.py`: one drove forward
for 60 steps and compared the start/end `get_pose()` (split into forward and lateral components
using the starting heading), the other rotated in place for 60 steps, summing the per-step yaw
change (rather than a single start/end difference) so the number stays correct even past a full
rotation. Both blocks have been removed now that this doc is filled in — see `docs/change_log.md`.
