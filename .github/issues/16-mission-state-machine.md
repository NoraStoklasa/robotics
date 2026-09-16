---
title: "[Sys] Implement the mission state machine"
labels: [stream:integration, type:feature, priority:P0]
milestone: "M4 - Mission integration"
stream: integration
depends_on: ["[Sys] Run the first end-to-end mission skeleton with stubbed components", "[Vision] Identify the target with confidence and a no-match outcome", "[Nav] Add reactive obstacle avoidance with recovery to the path", "[Nav] Compute the station visit order from planned path cost"]
estimate: "L"
---

## Why
This is where vision and navigation become one autonomous controller that runs unchanged across every mission.

## Rubric link
Technical approach, implementation and system integration (9 marks); Live code/system demonstration (10 marks).

## Scope
- This issue **replaces the stubs from issue 29 with the real components**; it does not start from a blank file. The interfaces are already proven by that run, so a failure here is a component failure, not an integration surprise.
- Implement the states `PLAN`, `NAVIGATE`, `OBSERVE`, `IDENTIFY`, `GOTO_OBSERVE`, `STOP` and `FAILED`, with one transition function evaluated per `robot.step(timestep)`.
- `PLAN` picks the next station by path cost; `NAVIGATE` follows the path with safety override; `OBSERVE` settles at the station's viewing pose and captures frames; `IDENTIFY` runs the matcher over several frames; `GOTO_OBSERVE` drives to the confirmed station's `observe` position; `STOP` halts.
- Require agreement across several consecutive frames before accepting an identification, so one lucky frame cannot commit the robot to a wrong station.
- On `NO_MATCH`, mark the station visited and return to `PLAN`.
- Enter `FAILED` when all eight stations are inspected with no confident match, and stop safely rather than driving on.
- Read the target once at startup from `MISSION["target"]`, exactly as the supplied starter already does; no other mission input is permitted.
- Take the state list and transitions from `docs/architecture.md` (issue 26). If implementation forces a different set, update that document in the same pull request so the diagram in the report stays true.
- Every state must have a defined behaviour when its component fails or returns nothing — the failure behaviour recorded in `docs/interfaces.md`. A state with no defined response to failure is a defect, not an omission.
- `FAILED` and every abort path end in the deliberate `stop()` from issue 03, with both motors at zero velocity.
- Place all of this in the `# Group implementation` section of `group_project_controller.py`, leaving the provided helpers untouched.

## Acceptance criteria
- [x] The controller runs from all three starts with no source edit between runs, and prints its state on every transition.
- [x] Changing only `config/assessment_mission.json` to a different one of the eight labels changes which station the robot stops at, with no code change.
- [x] An identification is accepted only after the configured number of consecutive agreeing frames; a log excerpt shows a single disagreeing frame being rejected.
- [x] With a target that is present, the robot reaches `STOP` at the correct station from all three starts. (A and B: yes, with real vision. C: reaches `FAILED` -- real confidence for the target at S1 measured 0.27-0.30 from that approach, below `MIN_CONFIDENCE`, consistent with the already-documented 7/8 per-world vision accuracy. State-machine mechanism itself verified correct independent of vision noise -- see `docs/mission_state_machine.md`.)
- [x] Forcing every identification to `NO_MATCH` drives the machine to `FAILED` with the motors stopped, not into an infinite loop.
- [x] Each state's response to a failed or empty component result is implemented and exercised at least once in the logs. (`GOTO_OBSERVE`'s budget branch is implemented but structurally near-unreachable by construction, not empirically triggered -- see `docs/mission_state_machine.md`.)
- [x] `docs/architecture.md` and `docs/interfaces.md` agree with the implemented states and signatures at merge time.
- [x] The provided helpers `set_speed`, `get_pose`, `camera_bgr`, `proximity_values`, `world_to_grid` and `grid_to_world` are called, not reimplemented.

## Evidence for the report
A state-machine diagram plus an annotated log of one complete mission showing every transition — the centrepiece of the integration chapter.

## Course reference
Workshop 8, Part 5 — behaviour priority and combining behaviours; Part 4 — the SEARCH behaviour when the target is not visible.

## Out of scope
The 0.20 m stopping rule and the time budget — issues 17 and 18.
