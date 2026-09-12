---
title: "[Vision] Measure poster appearance against standoff distance"
labels: [stream:vision, type:research, priority:P0]
milestone: "M2 - Target identification"
stream: vision
depends_on: ["[Nav] Implement motion primitives and pose utilities"]
estimate: "M"
---

## Why
Fixes the single number the whole vision design depends on — how many pixels of poster the robot actually gets, and from where — before any matcher is chosen.

## Rubric link
Problem understanding, project idea and design rationale (8 marks); Experimental evaluation, results and discussion (8 marks).

## Scope
Known geometry, from `protos/TexturedBarrier.proto` and `config/project_config.json` — verify each of these rather than trusting this list:
- Each station barrier is a box of 0.50 m x 0.06 m x 0.28 m; the poster is a 0.22 m x 0.22 m panel mounted on one vertical face, centred about 0.145 m above the floor.
- Every `observe` position sits about 0.295 m from the poster face, and every `observe_yaw` points at the poster centre.
- The camera is 160 x 120 and is mounted low on the e-puck, so the poster centre sits well above the optical axis at close range.

Tasks:
- Drive to a known station's `observe` pose, capture `camera_bgr()`, and save the frame.
- Repeat the capture at a range of standoff distances along the `observe_yaw` axis — for example 0.30, 0.45, 0.60, 0.80, 1.00 and 1.30 m — and at lateral offsets of 0 and about +/-15 degrees.
- For every capture, record the poster's bounding box in pixels (width, height, and whether the top or bottom edge is clipped by the frame).
- Produce `docs/poster_visibility.md` with a table of distance against poster pixel size and clipping, and a recommendation for the standoff band to identify from.

## Acceptance criteria
- [ ] Captured frames for at least 6 distances and 3 lateral offsets are committed under `docs/data/poster_captures/`.
- [ ] The table records poster bounding-box width and height in pixels, and a clipped yes/no flag, for every capture.
- [ ] The report states explicitly whether the full poster fits in the 160 x 120 frame at the 0.295 m `observe` distance, backed by a saved frame.
- [ ] A recommended identification standoff band is stated as two distances in metres, justified by the measured pixel size and clipping.
- [ ] The measurement is repeated at a second station and the pixel sizes agree to within 15 percent.

## Evidence for the report
`docs/poster_visibility.md` — the distance-against-pixel-size table plus annotated example frames. This is the measurement that justifies the identification range in the design chapter.

## Course reference
Week 2 — pinhole camera model and the relationship between object size, distance and pixel extent; Workshop 8, Part 3 — converting the camera buffer to an OpenCV image with `camera_bgr()`.

## Out of scope
Deciding between ORB matching and a CNN classifier; this issue only measures what the camera can see and feeds that decision.
