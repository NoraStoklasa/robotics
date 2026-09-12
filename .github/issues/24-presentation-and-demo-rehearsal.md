---
title: "[Docs] Build the presentation and rehearse the live demo"
labels: [stream:integration, type:docs, priority:P0]
milestone: "M5 - Evaluation and deliverables"
stream: integration
depends_on: ["[Sys] Run the full mission test matrix", "[Vision] Build shuffled-assignment worlds to prove no fixed mapping"]
estimate: "M"
---

## Why
The presentation is 25 of 60 marks, 10 of which are the live demonstration — which is run on a mission the instructor chooses on the day.

## Rubric link
Clarity and technical explanation (7 marks); Live code/system demonstration (10 marks); Q&A and individual understanding (8 marks).

## Scope
- Build a 10-minute deck: task, solution architecture, the design decisions and their evidence, main results.
- Rehearse the live demo end to end under assessment conditions: another member picks the world and edits `config/assessment_mission.json`, the presenter opens the world and presses Run, and nobody touches anything else. No pausing, restarting or editing.
- Rehearse from all three starts and with several targets, including at least one interior station, and time each run against the 4:00 limit.
- Prepare a Q&A sheet covering the whole system, and rotate practice questions so **every member can answer on vision, navigation and integration** — the rubric examines individual understanding of the complete system.
- Build the Q&A bank around the question types the workshop says will be asked, and ask them of **individuals**, not the group: how does your robot identify the target; how does your navigation work; why did you choose this approach over the alternative; what does this component assume; what happens when it fails; what evidence supports that claim. The workshop states examiners will "dive deep into more challenging technical details, especially what we learned this semester" — so include questions tying the design back to Weeks 1-8 material.
- Rehearse the assessment interaction rules until they are automatic: after Run, no menu use, no keyboard input, no pausing, no reset, no restart, no editing. The workshop notes the assessment rules are stricter than normal development, where reset and restart are used freely.
- Agree the honest answer to "why did you not do X": name the constraint or the measurement, not a vague preference.
- Write a one-page demo-day runbook: which files to open, the Webots Python-command setting, and what to do if the simulation misbehaves.
- Agree what to say if a run fails on the day: describe the failure honestly and refer to the documented failure analysis.

## Acceptance criteria
- [ ] The deck runs to 10 minutes or less in a timed rehearsal.
- [ ] At least 5 rehearsal runs are completed under assessment conditions, from all three starts, and each completion time is recorded against the 4:00 limit.
- [ ] Every member answers at least three practice questions from a stream that is not their own, **and** justifies at least one design decision with the number that settled it.
- [ ] Every member can state the input, output, assumptions and failure behaviour of all three main components from `docs/interfaces.md`.
- [ ] Every rehearsal run is completed with zero interaction after Run; any rehearsal where someone intervened is repeated.
- [ ] The runbook fits on one page and names the exact files opened during the demo.
- [ ] At least one rehearsal uses a shuffled-assignment world, so the demo is not tuned to the training mapping.

## Evidence for the report
The rehearsal timing log doubles as extra evidence of repeated successful runs in the evaluation chapter.

## Course reference
Workshop 8, Part 1 — the Webots Python-command configuration that must be correct on the demo machine before anything runs.

## Out of scope
Report writing and submission packaging.
