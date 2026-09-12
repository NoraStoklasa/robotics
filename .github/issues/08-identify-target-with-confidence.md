---
title: "[Vision] Identify the target with confidence and a no-match outcome"
labels: [stream:vision, type:feature, priority:P0]
milestone: "M2 - Target identification"
stream: vision
depends_on: ["[Vision] Choose and record the target-identification approach", "[Vision] Isolate the poster region in the camera frame"]
estimate: "L"
---

## Why
This is the one thing the brief insists must be solved visually — deciding whether the poster in front of the robot is the requested target.

## Rubric link
Technical approach, implementation and system integration (9 marks); Project complexity and robustness (6 marks).

## Scope
- Implement `identify(crop)` returning `(label, confidence)` where `label` is one of the eight entries in `CONFIG["target_labels"]` or the sentinel `NO_MATCH`.
- Load the eight reference templates from `textures/target_*.png` by iterating `CONFIG["target_labels"]` and building the filename from the label. The mission target comes from `MISSION["target"]`, which the starter already reads.
- Implement the approach chosen in the decision record, scoring the crop against all eight references and returning the best label with a comparable confidence score.
- Add a `MIN_CONFIDENCE` threshold and a margin rule: reject when the best score is below the threshold, or when the best and second-best scores are too close to separate. Both are named constants.
- Return `NO_MATCH` rather than guessing, so the mission logic can move to the next station instead of committing to a wrong one.
- Log every identification attempt — station, frame, label, confidence, runner-up — through the telemetry logger.

- Match the signature agreed in `docs/interfaces.md` (issue 26) exactly — this is the vision→navigation contract, and issues 16 and 29 are written against it. If the implementation forces a change, change the contract document in the same pull request.
- Document the module's four contract lines in the docstring: input, output, assumptions, failure behaviour. `NO_MATCH` is the failure behaviour; state what the caller must do with it.

## Acceptance criteria
- [ ] `identify` returns a label from `CONFIG["target_labels"]` or the exact sentinel `NO_MATCH`, and never any other value, across the full captured-frame set.
- [ ] On poster crops captured at the eight stations, top-1 accuracy is at least 87.5 percent, that is at least 7 of 8 correct.
- [ ] Feeding a crop of arena floor or bare barrier body returns `NO_MATCH` for at least 10 such crops.
- [ ] The label set is read from `CONFIG["target_labels"]`; no station identifier appears anywhere in the vision module, verified by `grep -nE 'S[1-8]' ` over the vision source returning no matches.
- [ ] No forbidden technique is used: `grep -rniE 'recognition|supervisor|\.wbt' ` over the controller source returns no functional call, only comments.
- [ ] `MIN_CONFIDENCE` and the margin rule are named constants with the tuning rationale in a comment or the decision record.

- [ ] The function signature matches `docs/interfaces.md`, and the docstring states input, output, assumptions and failure behaviour.

## Evidence for the report
A confusion matrix over the eight targets and a table of confidence scores for correct, incorrect and `NO_MATCH` cases.

## Course reference
Week 3 — ORB descriptor matching with a ratio test; Week 4 — ResNet-18 transfer learning; Week 5 — confidence thresholds and the miss-versus-false-alarm trade.

## Out of scope
Rejecting the B1-B5 distractor images specifically, and the accuracy sweep across worlds — both are `[Vision] Evaluate identification accuracy and distractor rejection`.
