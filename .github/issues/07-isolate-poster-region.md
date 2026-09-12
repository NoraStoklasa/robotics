---
title: "[Vision] Isolate the poster region in the camera frame"
labels: [stream:vision, type:feature, priority:P0]
milestone: "M2 - Target identification"
stream: vision
depends_on: ["[Vision] Measure poster appearance against standoff distance"]
estimate: "M"
---

## Why
Matching works far better on a tight poster crop than on a whole 160 x 120 frame that is mostly floor, wall and background.

## Rubric link
Technical approach, implementation and system integration (9 marks).

## Scope
- Implement `find_poster_region(image)` returning a bounding box, or `None` when no plausible poster is present.
- Use the Week 1 pipeline: convert BGR to HSV, threshold to separate the bright poster panel from the dark grey barrier body (`baseColor 0.29 0.30 0.32` in `protos/TexturedBarrier.proto`) and from the arena floor, then take contours and their bounding boxes.
- Reject implausible candidates by area, by aspect ratio (the poster is square, so a ratio near 1.0 seen head-on), and by minimum pixel size taken from the poster-visibility table.
- When several candidates survive, return the largest, and expose the full ranked list for debugging.
- Save an annotated debug image, with the chosen box drawn, behind a `DEBUG` flag.

## Acceptance criteria
- [ ] On the captured frames from the poster-visibility study, a box is returned for at least 90 percent of frames where a poster is visible and unclipped.
- [ ] Returned boxes overlap the hand-marked poster region with IoU of at least 0.5 on a labelled set of at least 20 frames.
- [ ] `find_poster_region` returns `None` on at least 10 frames containing only floor, wall or barrier body with no poster.
- [ ] Aspect-ratio and area rejection limits are named constants derived from the poster-visibility table, not magic numbers.
- [ ] Running with `DEBUG` enabled writes annotated frames and does not change the returned boxes.

## Evidence for the report
A figure strip of annotated frames — raw frame, mask, chosen box — for the implementation chapter, plus the IoU number on the labelled set.

## Course reference
Week 1 — BGR to HSV conversion, `cv2.inRange` thresholding, masks, contours and bounding boxes; Week 5 — IoU as the overlap measure.

## Out of scope
Deciding which target the crop shows; this issue only locates the crop.
