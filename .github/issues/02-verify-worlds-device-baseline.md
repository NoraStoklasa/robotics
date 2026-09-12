---
title: "[Sys] Verify all three worlds run and record the device baseline"
labels: [stream:integration, type:test, priority:P0]
milestone: "M1 - Sensing and motion baseline"
stream: integration
depends_on: ["[Sys] Set up the repo, Python environment and working agreement"]
estimate: "S"
---

## Why
Confirms every member can run all three supplied starts before any implementation begins, and pins down the sensor numbers every later issue depends on.

## Rubric link
Live code/system demonstration (10 marks) — the demo depends on the world opening cleanly on the machine used on the day.

## Scope
- Open each of `worlds/training_start_A.wbt`, `training_start_B.wbt`, `training_start_C.wbt` and run the simulation.
- Confirm the supplied controller's own startup prints appear: mission, target, station list and camera size (the starter already prints these in `main()`).
- Record, in `docs/device_baseline.md`: `robot.getBasicTimeStep()`, camera width and height, the eight proximity-sensor names, and the `get_pose()` reading at each start.
- Compare the logged start pose against `CONFIG["starts"]` for A, B and C.

- Confirm the group-project e-puck's additional devices by name — the Week 8 workshop states the project robot carries a **GPS and an InertialUnit** beyond the workshop e-puck — and record the exact device-name strings, since `getDevice` fails silently against a wrong name.
- Record which warnings Webots prints on load. The workshop notes that version and texture warnings can be safely ignored for this project; list the ones seen so a teammate does not chase them as bugs.
- Record the rule in the README: `worlds/`, `maps/`, `protos/`, `targets/` and `textures/` are never modified. Only the controller is group work, and issue 19 works on *copies* of worlds.

## Acceptance criteria
- [ ] All three worlds run for at least 10 simulated seconds with no device-name error in the Webots console.
- [ ] `docs/device_baseline.md` records the basic timestep and the camera resolution as printed by the controller.
- [ ] For each start, the logged `get_pose()` x and y agree with the matching `CONFIG["starts"]` pose to within 0.05 m, and yaw to within 0.05 rad.
- [ ] The device baseline is recorded from an unmodified copy of the supplied worlds.

## Evidence for the report
`docs/device_baseline.md` plus one Webots console screenshot per world, for the experimental-setup section.

## Course reference
Workshop 8, Part 1 — steps 3 to 6: run the world, locate the camera, wheel motors and ps0-ps7, and record the camera resolution and basic timestep.

- [ ] The GPS and InertialUnit device names are recorded verbatim and shown returning a valid reading in the baseline log.
- [ ] The warnings printed on load are listed, each marked ignorable or needing action.

## Out of scope
Any motion or perception behaviour; this issue only observes and records.
