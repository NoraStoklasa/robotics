---
title: "[Vision] Choose and record the target-identification approach"
labels: [stream:vision, type:research, priority:P0]
milestone: "M2 - Target identification"
stream: vision
depends_on: ["[Vision] Measure poster appearance against standoff distance"]
estimate: "M"
---

## Why
Locks in one identification method with written justification, so the report can defend the choice and the team stops re-litigating it mid-build.

## Rubric link
Problem understanding, project idea and design rationale (8 marks).

## Scope
- Evaluate both candidates offline, on the frames captured in the poster-visibility study, against the eight reference images in `textures/target_*.png`:
  - **Option A — ORB keypoints and descriptor matching** (Weeks 3 and 7): detect ORB features on the poster crop and on each reference image, match descriptors, score by good-match count with a ratio test.
  - **Option B — ResNet-18 transfer learning** (Week 4): pretrained backbone with a frozen body and a retrained head over the eight classes, trained on augmented crops of the eight reference images.
- Score both on the same held-out captured frames and record top-1 accuracy, plus runtime per frame measured on a team laptop.
- Write `docs/decision_vision_approach.md` as a short decision record: the options, the measured numbers, the choice, and the reason.
- Note explicitly which provided resources are used and why that is permitted: the eight reference images in `textures/` are a supplied project resource and may be used as templates or training data. Reading which texture is attached to which station in a `.wbt` file is forbidden, and this design must not do it.
- If Option B is chosen, record the pretrained weights used and their source for the acknowledgements section, and add a row to `docs/external_resources.md` (issue 28).
- Open the record with the argument the Week 8 workshop makes explicitly: the Workshop 8 Part 3 red-mask colour threshold is **not** sufficient here. It fails under illumination change, shadows, reflections, confusing backgrounds and similarly coloured objects, and the project requires deciding *which station shows a named target* rather than finding one known colour. Say so, with a captured frame demonstrating it, rather than asserting it.
- Treat the runtime figure as a real engineering trade-off, not a footnote: the workshop expects a stated balance between identification accuracy and per-frame processing cost, justified against the control-loop timestep.
- Record the choice as a row in `docs/decision_log.md` (issue 27) with its deciding criterion, not only in this document.

## Acceptance criteria
- [ ] Both options are implemented well enough to produce a top-1 accuracy figure on the same set of at least 30 captured frames.
- [ ] `docs/decision_vision_approach.md` records accuracy and per-frame runtime for both options in one table.
- [ ] The record states the chosen option and at least two reasons referencing the measured numbers.
- [ ] The record contains a compliance paragraph confirming no use of Webots Camera Recognition, no simulator ground-truth identity, and no reading of `.wbt` files or texture filenames at runtime.
- [ ] Per-frame runtime of the chosen option leaves the control loop able to run within the simulation timestep recorded in the device baseline, and the accuracy-versus-runtime trade-off is stated in one sentence with both numbers.
- [ ] The record includes a captured frame or measurement showing why a Workshop-8-style colour threshold is inadequate for this task.
- [ ] The decision appears as a row in `docs/decision_log.md`.

## Evidence for the report
`docs/decision_vision_approach.md` — the comparison table and decision rationale, quoted directly in the design-rationale chapter.

## Course reference
Week 8 workshop — "do not rely on the Part 3 red-mask method for the project; it is a totally different level", and the tutor's confirmation that the group project method is fully free within the course toolbox. Week 3 — ORB keypoint detection and descriptor matching; Week 4 — pretrained ResNet-18 with a frozen backbone and limited fine-tuning.

## Out of scope
Production implementation of the chosen matcher — that is `[Vision] Identify the target with confidence and a no-match outcome`.
