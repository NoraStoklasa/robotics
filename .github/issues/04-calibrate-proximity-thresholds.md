---
title: "[Nav] Calibrate ps0-ps7 obstacle thresholds from logged readings"
labels: [stream:navigation, type:research, priority:P0]
milestone: "M1 - Sensing and motion baseline"
stream: navigation
depends_on: ["[Nav] Implement motion primitives and pose utilities"]
estimate: "M"
---

## Why
The collision requirement is absolute, and the avoidance threshold has to come from measured readings in this arena rather than from a value copied out of the workshop.

## Rubric link
Project complexity and robustness (6 marks) — a tuned, evidence-backed safety threshold.

## Scope
- Drive the robot toward each obstacle class in the arena — an arena wall, a `B1`-`B5` navigation barrier, and an observation-station barrier — logging all eight `proximity_values()` against `distance_to` the obstacle from `get_pose()`.
- Group the sensors as Workshop 8 does: `ps0`, `ps1`, `ps2` as right/front-right and `ps5`, `ps6`, `ps7` as left/front-left.
- Produce a reading-versus-distance plot for each obstacle class and choose a `WARN` threshold and a higher `STOP` threshold from it.
- Record the chosen thresholds and the reasoning in `docs/proximity_calibration.md`. Start from the workshop's value of about 80 but do not keep it unless the readings support it.

## Acceptance criteria
- [ ] Logged readings for all three obstacle classes are committed as CSV under `docs/data/`.
- [ ] A matplotlib figure plots proximity reading against measured distance for each obstacle class.
- [ ] The chosen `WARN` threshold fires at least 0.06 m before the robot contacts an obstacle in a repeated head-on approach test.
- [ ] `STOP` is strictly greater than `WARN`, and both are named constants in the controller, not literals scattered through the code.
- [ ] `docs/proximity_calibration.md` states each threshold and cites the figure it came from.

## Evidence for the report
The reading-versus-distance figure and the threshold table — the evidence that safety limits were measured rather than guessed.

## Course reference
Workshop 8, Part 5 — enabling ps0-ps7, printing real readings, and tuning the threshold experimentally instead of assuming it.

## Out of scope
The avoidance manoeuvre itself — that is `[Nav] Add reactive obstacle avoidance with recovery to the path`.
