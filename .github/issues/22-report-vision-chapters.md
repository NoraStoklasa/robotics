---
title: "[Docs] Write the vision chapters of the report"
labels: [stream:vision, type:docs, priority:P0]
milestone: "M5 - Evaluation and deliverables"
stream: vision
depends_on: ["[Vision] Evaluate identification accuracy and distractor rejection", "[Vision] Build shuffled-assignment worlds to prove no fixed mapping"]
estimate: "L"
---

## Why
The report carries 35 of 60 marks, and the vision argument has to be written by the person who ran the experiments.

## Rubric link
Problem understanding, project idea and design rationale (8 marks); Experimental evaluation, results and discussion (8 marks); Overall writing quality (4 marks).

## Scope
- Write the perception sections: the identification problem and why the map and pose cannot solve it; the poster-visibility study and the standoff it justified; the approach decision and its evidence; poster isolation and matching; thresholds and the `NO_MATCH` outcome.
- Write the vision results: confusion matrix, distractor rejection over the 20 B1-B5 images, threshold sweep, and the shuffled-world results.
- State the compliance position explicitly: no Camera Recognition, no simulator ground truth, no reading of `.wbt` files or texture filenames, and explain how the eight reference images are used legitimately as supplied templates.
- Acknowledge any pretrained model or external library used, with its source, as the brief's academic-integrity section requires.
- Reuse the figures already produced; do not regenerate results at writing time.
- Do **not** write a success-only chapter. The Week 8 workshop states plainly that a report where everything worked first time is treated as a warning sign, and that markers probe exactly those gaps in the Q&A. Include at least one perception failure with its diagnosis and what the evidence showed, drawn from `docs/failure_log.md`.

## Acceptance criteria
- [ ] Every vision claim in the text cites a committed figure or table produced by an earlier issue.
- [ ] The compliance paragraph names each forbidden technique and states how the design avoids it.
- [ ] All external libraries and pretrained weights are acknowledged with a source.
- [ ] Figures are numbered, captioned and referenced by number in the body text.
- [ ] At least one documented perception failure appears with its diagnosis, evidence and outcome; the chapter does not read as a sequence of successes.
- [ ] The draft is reviewed by an owner of a different stream before merging, per the working agreement.

## Evidence for the report
This issue produces the report's perception chapters directly.

## Course reference
Weeks 3, 4 and 5 — the techniques being written up; Week 4's domain-shift discussion frames the reference-image-to-camera-crop gap.

## Out of scope
Navigation and integration chapters, and final assembly and formatting.
