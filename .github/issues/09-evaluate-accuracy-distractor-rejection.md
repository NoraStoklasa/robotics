---
title: "[Vision] Evaluate identification accuracy and distractor rejection"
labels: [stream:vision, type:test, priority:P0]
milestone: "M2 - Target identification"
stream: vision
depends_on: ["[Vision] Identify the target with confidence and a no-match outcome"]
estimate: "L"
---

## Why
The arena contains 20 distractor images on B1-B5 that must never be accepted, and the report needs a real accuracy table rather than a claim that the vision works.

## Rubric link
Experimental evaluation, results and discussion (8 marks); Project complexity and robustness (6 marks).

## Scope
- Build `tools/eval_vision.py`: given a directory of labelled crops, run `identify` and emit a confusion matrix, per-class precision and recall, and the `NO_MATCH` rate.
- Assemble the evaluation set from two sources: poster crops captured at all eight stations across all three training worlds, and crops of the 20 distractor images in `textures/distractors/`.
- Every distractor crop is a negative — the correct output is `NO_MATCH` for all of them, since B1-B5 images are never valid mission targets.
- Sweep `MIN_CONFIDENCE` over a range and plot the true-accept rate against the false-accept rate, then justify the operating point actually shipped.
- Record the outcome in `docs/vision_evaluation.md`.

## Acceptance criteria
- [x] `python tools/eval_vision.py` runs from a fresh clone using relative paths and writes the confusion matrix as both CSV and a figure.
- [x] At the shipped `MIN_CONFIDENCE`, the false-accept rate on all 20 distractor images is 0 — no distractor is ever returned as one of the eight target labels.
- [x] Top-1 accuracy on station crops is reported per world for A, B and C, with at least 7 of 8 stations correct in each.
- [x] The threshold sweep is plotted with at least 5 threshold values, and the shipped value is marked on the plot.
- [x] `docs/vision_evaluation.md` names at least one condition under which identification fails, with the frame that shows it.

## Evidence for the report
The confusion matrix figure, the threshold-sweep plot and the distractor-rejection table — the core of the vision results section.

## Course reference
Week 5 — precision, recall and confidence thresholds; Week 4 — domain-shift evaluation, applied here as the gap between clean reference images and camera crops.

## Out of scope
Whole-mission success rates and timing — that is `[Sys] Run the full mission test matrix`.
