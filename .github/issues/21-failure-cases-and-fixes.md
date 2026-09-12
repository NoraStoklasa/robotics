---
title: "[Sys] Document failure cases and robustness fixes"
labels: [stream:integration, type:docs, priority:P1]
milestone: "M5 - Evaluation and deliverables"
stream: integration
depends_on: ["[Sys] Run the full mission test matrix", "[Vision] Evaluate identification accuracy and distractor rejection", "[Sys] Keep a decision log and a failure log from day one"]
estimate: "M"
---

## Why
The brief asks for meaningful failure cases, and honest failure analysis earns more credit than an unsupported claim that everything works.

## Rubric link
Experimental evaluation, results and discussion (8 marks); Project complexity and robustness (6 marks).

## Scope
- Draw primarily from `docs/failure_log.md` (issue 27), which has been filling since M0. This issue curates and writes up an existing record; it is not the first time failures are collected. The Week 8 workshop is explicit that leaving this to the final week loses the insights permanently.
- For each case, follow the workshop's diagnostic question rather than jumping to a fix: *where did the first incorrect decision occur?* A robot that stops at the wrong station may have a perfectly correct navigator and a mistaken perception; naming the wrong layer and "fixing" it makes the system worse.
- Select at least two genuine failure cases from the test matrix and the vision evaluation. Likely candidates, to confirm rather than assume: a misidentification at an awkward viewing angle, a near-collision in a one-cell gap into the interior pocket, a run that approaches the time budget, and a `NO_MATCH` loop where no station is confidently identified.
- For each, write up: what happened, the telemetry excerpt showing it, the diagnosed cause, the fix applied or the reason it was left unfixed, and the re-test result.
- Where a failure is left unfixed, state the limitation plainly and propose the improvement that would address it.
- Add a limitations section covering what the system cannot do — for example, dependence on GPS and IMU pose rather than visual localisation.
- Record everything in `docs/failure_analysis.md`.

## Acceptance criteria
- [ ] At least two failure cases are documented, each with a telemetry excerpt or saved frame as evidence.
- [ ] Each case names a diagnosed cause, not just the symptom, and identifies which layer made the first incorrect decision.
- [ ] Each fix is re-tested and the before-and-after result is reported with numbers.
- [ ] The limitations section names at least three limitations with a proposed improvement for each.
- [ ] At least one failure case comes from vision and at least one from navigation.

## Evidence for the report
`docs/failure_analysis.md` — supplies the report's failure-cases, limitations and future-work sections directly.

## Course reference
Week 3 — track validation, knowing when the target is lost, and failure-case analysis; Week 5 — the miss-versus-false-alarm trade behind threshold choices.

## Out of scope
New features; this issue documents and repairs what the matrix already exposed.
