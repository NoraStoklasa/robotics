---
title: "[Docs] Write the navigation and integration chapters"
labels: [stream:navigation, type:docs, priority:P0]
milestone: "M5 - Evaluation and deliverables"
stream: navigation
depends_on: ["[Sys] Run the full mission test matrix"]
estimate: "L"
---

## Why
The navigation design contains the project's most interesting constraint, and the person who found it should be the one to write it up.

## Rubric link
Technical approach, implementation and system integration (9 marks); Problem understanding and design rationale (8 marks); Overall writing quality (4 marks).

## Scope
- Write the navigation sections: occupancy grid and coordinate conversion; the clearance investigation and why uniform inflation was rejected or adapted; A* with the Manhattan heuristic; waypoint conversion and path simplification; P-controlled heading with the gain comparison; reactive avoidance and behaviour priority; visit ordering by path cost.
- Give the clearance finding the space it deserves: uniform one-cell inflation seals the interior pocket and makes `S2`, `S4`, `S6` and `S8` unreachable, so the policy had to be designed around a measured reachability check.
- Write the integration sections: the state machine and its diagram, the stopping rule against the 0.20 m criterion, telemetry, and the time budget with degraded mode.
- Explain what was deliberately not built and why — in particular that visual SLAM is unnecessary because GPS and InertialUnit pose are provided, which the brief confirms.
- Open the integration section with the **one-page architecture figure and the component contract table** from issue 26, and describe the interfaces as designed decisions — the workshop treats agreeing these early as the single most important engineering idea in the project.
- Include the first end-to-end skeleton run (issue 29) and what it exposed: describe the build → test → integrate → improve cycle with dates, rather than presenting the final controller as if it arrived whole.
- Source the design-rationale passages from `docs/decision_log.md`, quoting the criterion and the number that settled each choice.
- Do not write a success-only chapter; include at least one navigation or integration failure with its diagnosis, per the workshop's warning.
- State the contribution of each stream to integration, feeding the contribution table.

## Acceptance criteria
- [ ] The clearance investigation is presented with its reachability table and the sealed-pocket figure.
- [ ] Every controller constant that was tuned — heading gain, proximity thresholds, tolerances, confidence threshold — appears in one table with its value and how it was chosen.
- [ ] The state-machine diagram is included and every state in the implementation appears in it.
- [ ] The section on visual SLAM explains why it is not required, referencing the provided pose.
- [ ] The architecture figure and the interface contract table are both included, and match the shipped controller.
- [ ] The integration narrative gives dates for the first end-to-end run and at least one subsequent iteration.
- [ ] At least one navigation or integration failure is written up with its diagnosis and outcome.
- [ ] The draft is reviewed by an owner of a different stream before merging.

## Evidence for the report
This issue produces the report's navigation and integration chapters directly.

## Course reference
Workshop 8, Parts 2, 4, 5 and 6; Week 7 — visual odometry and SLAM, cited as the alternative that the provided pose makes unnecessary.

## Out of scope
Perception chapters, and final assembly and formatting.
