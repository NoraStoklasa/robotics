# find_poster_region() Development Notes

Per [Issue #7](.github/issues/07-isolate-poster-region.md). Referenced from
`vision_utils.py`'s own docstring. Kept separately from `docs/find_poster_region.md`
(the evaluation results) because this is the debugging history -- what was tried,
what real data showed was wrong, and why the final design looks the way it does.
Every claim below was checked against real captured frames, not reasoned about.

## 1. The issue's own suggested method doesn't hold up

The issue suggests thresholding the *bright* poster panel apart from the dark
barrier body. Tried directly first:

- **Per-target brightness/saturation threshold.** Measured the poster region's
  own HSV value for a bright target (`soda_can`, ~49 median) and a dark one
  (`backpack`, ~35 median) -- the dark target's poster measured barely brighter
  than the plain barrier body itself (~35). No single brightness cutoff
  separates "poster" from "plain barrier" across all 8 targets.
- **Per-frame "distance from the modal barrier colour" mask.** Tried computing
  the frame's modal colour in a middle band and flagging pixels that deviate
  from it. Rendered masks on real frames showed this picks up the floor (which
  differs from the modal colour by a lot, being bright and warm) far more
  reliably than it picks up the poster.

Both rejected. Settled on the barrier-landmark approach instead (see the
module docstring for the full reasoning) -- still HSV threshold + contours +
bounding boxes, just keyed off the more reliable landmark.

## 2. Bugs found only once real hand-labelled ground truth existed

The detector looked finished after it hit 100% detection on all 103 real
frames. It wasn't -- IoU against 20 frames hand-labelled independently (by
Nora, not generated) came back at a failing 12/20 (>=0.5), mean 0.44.

**Bug: a "found nothing more specific than the whole search window" candidate
was winning by raw size.** Many predictions across completely unrelated
frames were landing on the exact same generic box. Traced to a barrier
candidate that filled (almost) the entire detection zone -- not a located
object, just "everything in the window was dark enough" -- beating a smaller,
correct candidate on area. Fixed by deprioritising (not rejecting outright:
Station S6's own lighting sometimes leaves it as the only candidate at all)
rather than always preferring the largest candidate. Result: mean IoU 0.44 ->
0.58 (8/20 -> 12/20 >=0.5).

## 3. Bugs found only once real "no poster visible" frames existed

A second required test -- >=10 real frames with no poster visible should
return `None` -- exposed the detector was wrong on 13 of 18 real negative
frames (a full rotation sweep from a start pose, most headings facing no
poster at all):

- **Sky/floor gradients mistaken for a barrier.** The per-frame adaptive
  darkest-pixel threshold assumes a real barrier is always present to anchor
  on; when none is in view it just latches onto whatever's darkest -- a sky
  gradient, a horizon band. Fixed with an absolute darkness ceiling (every
  real barrier frame measured vmin<=43 across all 3 worlds; false positives
  measured 55-76) and a solidity check (a false match stitched from scattered
  pixels via morphological closing leaves most of its bounding box empty;
  real barriers measured 0.79-0.98 solidity vs 0.33 on one false positive).
- **A genuinely plain, posterless navigation barrier**, structurally
  identical to a real one but with no printed content, still passed both
  guards above (it's a real, solid, dark rectangle -- just not a *poster*).
  Fixed with an internal-texture check on the final candidate region: a flat
  barrier measured std=0.0, every real poster region measured std>=9.9.

Result: 4/18 -> 17/18 correctly `None`, with zero regression on detection
rate or IoU (reran both suites after every change).

## 4. The IoU number itself was still a fail on a strict reading (12/20, 12/15 unclipped)

Flagged on review: a strict reading of "boxes overlap ... with IoU >= 0.5"
means the labelled set should pass, not that the mean clears 0.5. The three
specific unclipped failures (`A_S2_d0p800_hp10`, `B_S6_d0p800_hm10`,
`B_S6_d0p800_hp10`) all had predictions landing on the *same* generic box
again (`x~49, w~63`) -- tracing it showed the degenerate full-window
candidate (see #2) was, for these three frames specifically, the *only*
candidate available at all.

Looked at the raw frames: in each case, an unrelated dark object elsewhere in
the same frame (a wall decoration in one, another station's barrier in
others) sits close enough to the real target that even the narrowest value
band still merges them into one blob across the whole search zone -- no
per-pixel threshold separates them, since the gap between the two objects is
itself dark enough to bridge.

**Fix: search overlapping left-half and right-half sub-windows, in addition
to the full zone, and pool every candidate.** In each of the three failing
frames, the half that excludes the unrelated object isolates the real
barrier cleanly. Confirmed on real frames before implementing broadly (all
three predicted IoU jumped to ~0.65 in a standalone check before touching the
module). Required one non-obvious fix: a sub-window candidate that fills
its *own* (deliberately narrow) window is the *expected, correct* outcome of
a working search, not a sign of a vague one -- applying the same
"fills-the-window-is-suspicious" penalty used for the full zone to sub-window
candidates too defeated the entire purpose (first implementation showed zero
improvement despite finding the right candidates, because they tied with the
old degenerate one and lost on raw area).

Introduced one new negative-frame false positive as a side effect (a
sub-window's own local darkest-pixel threshold, with no real barrier in that
half to anchor on, admitted a patch of empty sky at solidity 0.60). Tried
raising `_MIN_SOLIDITY` from 0.6 to 0.75 to reject it -- reverted: the true
minimum solidity among all 36 real unclipped winning candidates is 0.42,
*below* that false positive's own 0.60, so no fixed cutoff separates them
without also losing real detections. The tightened threshold cost a real
unclipped detection and an IoU pass (35/36, 14/15) to fix one frame in a
test that already has large headroom (>=15/18 against a >=10 requirement).
Kept `_MIN_SOLIDITY` at 0.6, prioritising the primary, tightly-specified
criteria over a secondary one with slack.

**Final result: 20/20 (100%) of the required unclipped labelled frames clear
IoU >= 0.5**, mean 0.787. The 5 clipped diagnostic labels are kept in
`docs/data/poster_region_clipped_labels.json` and reported separately, outside
the required IoU set. See `docs/find_poster_region.md` for the full numbers.

---

# Constant-by-constant rationale (moved out of `vision_utils.py`)

Moved here on 2026-09-17 so `vision_utils.py` reads as ordinary lab code. **Nothing was deleted** — the
measurements below were previously inline comments in that file, and each constant there now carries a
one-line summary plus a pointer to this section. If you are defending a number in the oral or the
report, this is the place to look.

## Why the barrier is the landmark, not the poster

`find_poster_region(image)` follows the Week 1 pipeline (HSV threshold, contours, bounding boxes) with
one deliberate adaptation, made after testing the literal approach against real data rather than
assuming it.

Issue #7's suggested method is to threshold the *bright* poster panel directly, apart from the dark
barrier body and the floor. Tested on real captures first: the panel's actual brightness varies hugely
by target — dark-photographed targets (the backpack, headphones) render barely brighter than the plain
barrier body itself (measured ~35 vs ~35 on the HSV value channel in a real dark-target capture), so a
direct brightness threshold on the poster is not reliable across all 8 targets. Two direct-segmentation
attempts (a per-target brightness/saturation threshold, and a per-frame "distance from the modal barrier
colour" mask) were tried on real frames and both failed on dark targets before this design was settled on.

Instead the barrier body is the landmark: it renders as the frame's darkest coherent region regardless of
which target is on it (verified target-agnostic in Issue #6, 76/84 real frames), and the poster's own
size is a *known, exact* fraction of it (0.22 m poster / 0.50 m barrel length = 0.44; 0.22 m / 0.28 m
height = 0.79, centred — `protos/TexturedBarrier.proto`). So: HSV-threshold to find the barrier, take its
contour and bounding box, then project the poster's known fraction of it. Still HSV threshold + contours
+ bounding boxes throughout, just keyed off the more reliable landmark for this dataset.

Every design choice was tested against all 103 real frames from Issues #5 and #6 (all 8 stations, all 3
worlds, clipped and unclipped), not just reasoned about — several earlier versions looked reasonable and
were wrong in ways only real data exposed. Sections 1–4 above record the specific failures and fixes.

## Poster plausibility filters

Derived from `docs/poster_visibility.md`'s UNCLIPPED rows (two measured stations, 0.80–1.30 m standoff,
offset 0 — the only rows with `clipped_top=False` and `clipped_bottom=False`): width 31–52 px, height
32–52 px, aspect ratio (w/h) 0.97–1.02. Not magic numbers.

| Constant | Value | Rationale |
|---|---|---|
| `MIN_POSTER_SIDE_PX` | 25 | A margin below the smallest observed side (31 px). |
| `MIN_POSTER_AREA_PX` | 625 | `MIN_POSTER_SIDE_PX ** 2`. |
| `MAX_POSTER_AREA_PX` | 4000 | Generous headroom above the largest observed unclipped area (52×52 = 2704). Rejects a candidate this large outright rather than let a bad merge (two unrelated dark objects mistaken for one barrier) win by raw size — returning `None` on an implausible candidate is more correct than returning a wrong box. |
| `ASPECT_RATIO_TARGET` | 1.0 | The poster is 0.22 m × 0.22 m, so square head-on. |
| `ASPECT_RATIO_TOLERANCE` | 0.7 | Generous: a few px of noise on a ~30 px box moves the ratio far more than on a big one. |
| `MIN_POSTER_INTERNAL_STD` | 8.0 | Grey-value std dev inside the candidate. A plain, posterless barrier is flat (measured std = 0.0 on one, real data); every real poster region across 20 labelled frames measured std ≥ 9.9. This is the one check that looks at the poster's own printed content rather than the barrier landmark around it. |

## Barrier landmark detection

Adapted from Issue #6's detector, verified on 76/84 real frames there.

**`_BARRIER_VALUE_BANDS = (25, 35, 45, 55)`** — no single fixed value band works across the whole
distance range. A narrow band (25) correctly isolates a small, far barrier (≥1.0 m) but only finds the
darkest *core* of a barrier rendered under lighter local lighting, understating its size. A wide band
(55) recovers that whole barrier but, at long range, starts merging the (now small) barrier with adjacent
background pixels. Rather than pick one value and accept whichever failure mode it causes, try every band
and pool all the candidates — the aspect-ratio and area filters then pick the best one from whichever
band happened to isolate it cleanly.

| Constant | Value | Rationale |
|---|---|---|
| `_ROBUST_VMIN_PERCENTILE` | 5 | Second band anchor alongside the zone's true darkest pixel — see the robust-anchor section below. |
| `_ROBUST_VMIN_GAP_MIN` | 30 | Only use that second anchor once it is this far from the true min. The `fire_extinguisher` hose-vs-panel gap measured 54 on every affected frame. |
| `_MIN_BARRIER_SIDE_PX` | 8 | Smallest plausible barrier side in px. |
| `_BARRIER_ASPECT_MIN` | 0.5 | Rejects thin slivers — e.g. a target's own dark accent, like a hose, being darker than the barrier itself (Issue #6). |
| `_POSTER_WIDTH_FRAC` | 0.22/0.50 | Poster geometry as a fraction of the barrier's own face (`protos/TexturedBarrier.proto`: barrier 0.50 × 0.28 m, poster 0.22 × 0.22 m). |
| `_POSTER_HEIGHT_FRAC` | 0.22/0.28 | As above. |
| `_CLOSE_CROP_TOP_PX` | 8 | Close-range/top-clipped crops can leave the printed target too tightly boxed for identification even though the poster is visibly present. Expand only this narrow case after candidate ranking; larger, normally-framed crops are left unchanged for IoU. |

**`_SIDE_MARGIN_FRAC = 0.05`** — exclude the outer 5% on each side before detection. The capture protocol
always aims the camera at the target first (`bearing_to`), so the true target is roughly centred; a stray
obstacle at the frame edge (e.g. a nearby B1–B5 navigation barrier, seen from one pose) was otherwise
merging with the real barrier into one bogus wide blob. Kept small: a real barrier at 0.8 m is itself
~110–120 px wide (most of the frame), so a wider margin clips genuine barriers, not just stray objects.
An off-centre capture heading (±10°) naturally shifts the barrier towards one side, so even "touches the
margin" is not a reliable clipped/not-clipped signal; the min/max area and aspect-ratio filters do that
job instead, applied uniformly.

**`_SUBWINDOW_FRAC = 0.6`** — width of each half-window as a fraction of the full search zone. Found
testing real frames: an unrelated dark object elsewhere in frame (a wall decoration, or another station's
barrier) can sit close enough to the true target that even the narrowest value band still merges them
into one blob across the *whole* zone. Searching the left and right halves separately, in addition to the
full zone, recovers the true barrier alone in the half that excludes the other object. Overlapping (0.6,
not 0.5) so a barrier straddling the middle isn't itself split in half.

## Guards against "no poster in view at all"

Found testing against real frames with NO poster visible (floor, wall, sky, distant barrier only): the
per-frame adaptive vmin assumes there is always a genuinely dark barrier to anchor on, and when there
isn't one it latches onto whatever is darkest in frame — a sky gradient, a horizon band — and the wide
value bands then admit most of that gradient as "barrier". Two independent, real-data-backed guards:

**`_MAX_VMIN = 45`** — every one of 36 real unclipped barrier frames across all 3 worlds had vmin ≤ 43
(the worst lighting case); most sky/floor-only false positives had vmin 55–76. If the frame's own darkest
pixel in the search zone is already this bright, there is almost certainly no real barrier in view, so
detection is skipped entirely.

**`_MIN_SOLIDITY = 0.6`** — contour area / bounding-box area. Tried raising this to 0.75 to reject a
borderline (0.60) sub-window false positive on empty sky — **reverted**: the true minimum solidity among
all 36 real unclipped winning candidates is 0.42, *below* that false positive's own 0.60, so no fixed
cutoff separates them cleanly. 0.75 cost a real unclipped detection and an IoU pass (35/36, 14/15) to fix
one frame in a negative-only test that already has large headroom (≥15/18 either way against a ≥10
requirement). Kept at 0.6, prioritising the primary, tightly-specified criteria (detection rate, IoU) over
a secondary one with slack.

## The robust (percentile) anchor in `_barrier_candidates`

A second anchor is tried at `_ROBUST_VMIN_PERCENTILE` rather than the zone's true darkest pixel, but only
when `allow_robust_anchor` is set. Found on real `fire_extinguisher` frames (S4): the target's own black
hose renders darker (HSV value ~33–46) than the barrier panel behind it (~88), and is a thin sliver too
narrow to pass `_BARRIER_ASPECT_MIN` on its own, so the true-min anchor finds zero valid candidates
anywhere in the frame. Anchoring instead at the percentile lands on the panel directly (measured 88 on all
three affected frames), because a thin accessory occupies too little of the search zone to move a low
percentile.

Robust-anchor boxes are also height-capped at their own width. Pixel inspection of the same three frames
showed why: the real barrel panel sits directly above a floor of similar HSV value, with no brightness gap
between them at this close range, so the wide bands this anchor needs (to bridge the panel's own
fragmented dark pixels via the morphological close) also bridge straight through into the floor — the
contour's bbox comes back ~30 px taller than the real barrel (106 vs the ~78 every other same-distance
station's barrel measures at this width). The real proto (0.50 × 0.28 m) is never taller than it is wide,
so trimming excess height from the bottom (keeping the top, which measured correctly in every case)
removes the floor without needing to distinguish it from the barrel by colour.

**Why the rescue is decided globally, not per window.** Tried per-window first and it regressed a real
`running_shoe` frame (S6) where the *full-zone* window already found the correct candidate at the true
min, but one of the *half*-windows didn't (an ordinary case of a half excluding part of the real object).
That empty half then invoked the robust anchor on its own and turned up a small, unrelated, almost
perfectly square blob elsewhere in the half, which won `find_poster_region`'s aspect-ratio tie-break purely
by shape over the correct, larger candidate the full-zone window had already found. Trying the true min
everywhere first, and only falling back to the robust anchor if that leaves every single window empty,
makes the fallback unable to outrank a real candidate found anywhere in the frame.

## Why half-windows are never treated as "degenerate"

Each pooled result carries its own window's width, EXCEPT the two half-windows, which report a width of
-1 (meaning: never treat as degenerate). "Fills (almost) the whole window" is only a bad sign for the
full-zone search — that means nothing more specific than a big chunk of the *whole frame* was found. For a
half-window, deliberately narrowed precisely to exclude an unrelated object elsewhere in frame, filling it
is the expected, correct outcome of a working search, not a sign of a vague, unlocalised one. Treating it
the same way defeated the entire purpose of searching sub-windows (tested: without this distinction, the
half-window candidates still lost to the full-window one on raw area, unchanged result).

A degenerate candidate is **deprioritised, not rejected**: on a few frames (one hard lighting case
fragments its true barrier into pieces too small to individually clear `MIN_POSTER_AREA_PX`) a degenerate
box is the only candidate available at all, so it is only used if nothing more specific survives.

## Why the poster fraction is applied unconditionally

No separate "clipped, so use the raw box" case. That special case was tried and, combined with any margin
narrow enough not to clip genuine barrier width, could not reliably tell a truly-clipped barrier apart
from one merely shifted toward one side by an off-centre capture heading (±10°). Applying the same
fraction unconditionally underestimates the poster at very close range (where the detected barrier is
itself already an underestimate, being clipped) rather than overestimating it — and the size/aspect-ratio
filters reject the frames that would be underestimated too far to be plausible, which is exactly the
intended behaviour for a case outside where this method is meant to work (see Issue #5's close-range
clipping notes).

## Candidate ranking tie-break

When two plausible boxes are close in size, prefer the one closer to the poster's known square shape over
the merely larger one. Issue #9 exposed this with S2 captures where an unrelated left-wall picture was a
little taller/larger than the true mug poster and therefore won on area alone.

## `identify_frame()`: why more than one candidate is tried

Found on real live `headphones` (S7) frames: the precise projection
(`_POSTER_WIDTH_FRAC`/`_POSTER_HEIGHT_FRAC` of the detected barrier) can land squarely in the
low-information gap between the two earcups, while that same barrier's own full extent — before the
fraction narrows it — reliably shows both earcups plus the headband. On the exact frames that failed live,
confidence rose from 0.36–0.44 (rejected) to 0.43–0.77 (mostly accepted), and one frame that had been
confidently *wrong* (`running_shoe`/`backpack` at 0.38–0.41 on the narrow crop) came back correctly as
`headphones` at 0.77 on the full barrier box.

Also found on a real `soda_can` frame (`C_S1_d1p000_hp10.png`, long range + off-axis):
`find_poster_region`'s own top-ranked candidate can itself be the wrong one. There, a half-window search
merged a strip of sky above the barrier into its "barrier" at a wide value band, and the resulting poster
projection — centred on empty plain panel, not the can — happened to score very slightly *more* square
than the correct candidate (still present, ranked second) and won the aspect-closeness tie-break by a
hair. Several geometric signals were tried to catch this at detection time (internal value range of the
barrier region, top-row brightness) — none separated it from legitimate candidates on real data, the same
dead end hit while chasing the `headphones` case. Trying the top `_IDENTIFY_MAX_RANKED_CANDIDATES` ranked
candidates (not just the first) and keeping whichever `identify()` actually accepts covers both cases: the
sky-merged candidate has no real poster content so the classifier does not confidently accept it, and the
correct, second-ranked candidate wins instead.

Tried replacing the narrow projection outright: **rejected** — it is what `docs/find_poster_region.md`'s
hand-labelled IoU test verifies against real ground truth, and the other targets rely on it staying tight
for a clean square crop. If nothing is accepted, the top-ranked candidate's own (rejected) result is kept,
unchanged from calling `identify()` directly on it.

## Identification thresholds

| Constant | Value | Rationale |
|---|---|---|
| `MIN_CONFIDENCE` | 0.50 | Tuned on the real Issue #6/#7 captures: with the frozen-ResNet head, the best usable crop for seven of eight target classes clears both thresholds, while central floor/no-poster patches stayed below 0.50. |
| `MIN_CONFIDENCE_MARGIN` | 0.20 | Prevents weak "coin flip" classifications being accepted even when the top softmax score alone is moderately high. |
| `MIN_REFERENCE_SIMILARITY` | -0.05 | Issue #9 added open-set distractor testing. A closed 8-way classifier always picks the "nearest" target class for an unrelated image, so a few distractors can look high-confidence even though they are not target posters. This lightweight same-reference check compares the crop to the reference image for the predicted class and rejects the known false-accept patterns without changing the classifier's public interface. |

**Per-label floors (`MIN_REFERENCE_SIMILARITY_BY_LABEL`).** Only labels whose real in-game renders score
clearly positive get one; see `docs/decision_log.md` for each decision.

- `wall_clock: 0.00` — original entry.
- `camera: 0.00` — added 2026-09-17 after `test_worlds/test_start_B.wbt` failed. The real `headphones`
  poster at S2 read as `camera` on 3 of 5 frames and won the consensus vote. The cases separate cleanly:
  false `camera` = -0.029, genuine `camera` (S4, same run) = +0.123/+0.176/+0.175.
- **`fire_extinguisher` and `coffee_mug` deliberately have none.** `fire_extinguisher` (2026-09-16): even a
  manually traced, pixel-perfect crop of the real in-game poster — no shadow/floor contamination at all —
  only scores ~0.11 against the studio reference photo, despite the classifier itself being 97% confident
  on that same crop; the known false-accept distractors (`books_a.png`/`books_b.png`, ~0.17) score *higher*
  than that, so no floor keeps both. `coffee_mug` (2026-09-17): a real, live `S2` capture (world C) scored
  `raw_label=coffee_mug` at 0.86–0.90 confidence with an 0.82+ margin on 5 of 5 frames from the retry
  viewpoint, but only 0.014–0.018 reference similarity — again below its own distractors (`keyboard_b.png`
  0.092, `soccer_ball_a.png` 0.058) that the 0.10 floor was protecting against. Both labels' in-game
  renders simply don't resemble their studio reference photos at this metric's pixel/colour-histogram
  level, regardless of crop quality. The full confusion matrix was checked before dropping either floor:
  both labels have zero false positives against every real in-game frame from any other station, so the
  only cost of removing them is those distractor images, which never appear inside the Webots simulation.
