"""Issue #7: locate the poster region in a captured frame.

`find_poster_region(image)` follows the Week 1 pipeline (HSV threshold,
contours, bounding boxes) with one deliberate adaptation, made after testing
the literal approach against real data rather than assuming it:

The issue's suggested method is to threshold the *bright* poster panel
directly, apart from the dark barrier body and the floor. Tested on real
captures first: the panel's actual brightness varies hugely by target --
dark-photographed targets (the backpack, headphones) render barely brighter
than the plain barrier body itself (measured ~35 vs ~35 on the HSV value
channel in a real dark-target capture), so a direct brightness threshold on the
poster is not reliable across all 8 targets. Two direct-segmentation
attempts (a per-target brightness/saturation threshold, and a per-frame
"distance from the modal barrier colour" mask) were tried on real frames and
both failed on dark targets before this design was settled on -- see
docs/find_poster_region_notes.md.

Instead, the barrier body is the landmark: it renders as the frame's
darkest coherent region regardless of which target is on it (verified
target-agnostic in Issue #6, 76/84 real frames), and the poster's own size
is a *known, exact* fraction of it (0.22 m poster / 0.50 m barrel length =
0.44, 0.22 m / 0.28 m height = 0.79, centred -- protos/TexturedBarrier.proto).
So: HSV-threshold to find the barrier, take its contour and bounding box,
then project the poster's known fraction of it. Still HSV threshold +
contours + bounding boxes throughout, just keyed off the more reliable
landmark for this dataset.

Every design choice below was tested against all 103 real frames from
Issues #5 and #6 (all 8 stations, all 3 worlds, both clipped and unclipped),
not just reasoned about -- several earlier versions looked reasonable and
were wrong in ways only real data exposed (see docs/find_poster_region_notes.md
for the specific failures and what fixed each one).
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from project_utils import CONFIG, ROOT

# ---- Constants, derived from docs/poster_visibility.md's UNCLIPPED rows
# (two measured stations, 0.80-1.30 m standoff, offset 0 -- the only rows with
# clipped_top=False and clipped_bottom=False): width 31-52 px, height
# 32-52 px, aspect ratio (w/h) 0.97-1.02. Not magic numbers.
MIN_POSTER_SIDE_PX = 25          # a margin below the smallest observed side (31 px)
MIN_POSTER_AREA_PX = MIN_POSTER_SIDE_PX ** 2   # 625
MAX_POSTER_AREA_PX = 4000        # generous headroom above the largest observed
                                  # unclipped area (52*52 = 2704) -- rejects a
                                  # candidate this large outright rather than
                                  # let a bad merge (two unrelated dark objects
                                  # mistaken for one barrier) win by raw size;
                                  # returning None on an implausible candidate
                                  # is more correct than returning a wrong box
ASPECT_RATIO_TARGET = 1.0        # poster is 0.22 m x 0.22 m -- square head-on
ASPECT_RATIO_TOLERANCE = 0.7     # generous: a few px of noise on a ~30 px box
                                  # moves the ratio far more than on a big one
MIN_POSTER_INTERNAL_STD = 8.0    # grey-value std dev inside the candidate --
                                  # a plain, posterless barrier is flat (measured
                                  # std=0.0 on one, real data); every real poster
                                  # region across 20 labelled frames measured
                                  # std>=9.9

# Barrier landmark detection (adapted from Issue #6's detector, verified on
# 76/84 real frames there).
#
# No single fixed value band works across the whole distance range: a narrow
# band (25) correctly isolates a small, far barrier (>=1.0 m) but only finds
# the darkest *core* of a barrier rendered under lighter local lighting,
# understating its size; a wide band (55) recovers that whole
# barrier but, at long range, starts merging the (now small) barrier with
# adjacent background pixels. Rather than pick one value and accept whichever
# failure mode it causes, try every band and pool all the candidates -- the
# aspect-ratio and area filters below then pick the best one from whichever
# band happened to isolate it cleanly.
_BARRIER_VALUE_BANDS = (25, 35, 45, 55)
_MIN_BARRIER_SIDE_PX = 8
_BARRIER_ASPECT_MIN = 0.5         # reject thin slivers (e.g. a target's own
                                   # dark accent, like a hose, being darker
                                   # than the barrier itself -- Issue #6)
_SIDE_MARGIN_FRAC = 0.05          # exclude the outer 5% on each side before
                                   # detection: the capture protocol always
                                   # aims the camera at the target first
                                   # (bearing_to), so the true target is
                                   # roughly centred -- a stray obstacle at
                                   # the frame edge (e.g. a nearby B1-B5
                                   # navigation barrier, seen from one pose)
                                   # was otherwise merging with the real
                                   # barrier into one bogus wide blob. Kept
                                   # small: a real barrier at 0.8 m is itself
                                   # ~110-120 px wide (most of the frame), so
                                   # a wider margin clips genuine barriers,
                                   # not just stray objects -- and an
                                   # off-centre capture heading (+/-10 deg)
                                   # naturally shifts the barrier towards one
                                   # side, so even "touches the margin" is
                                   # not a reliable clipped/not-clipped
                                   # signal; the min/max area and
                                   # aspect-ratio filters below do that job
                                   # instead, applied uniformly

# Poster geometry as a fraction of the barrier's own face
# (protos/TexturedBarrier.proto: barrier 0.50 x 0.28 m, poster 0.22 x 0.22 m).
_POSTER_WIDTH_FRAC = 0.22 / 0.50
_POSTER_HEIGHT_FRAC = 0.22 / 0.28

# Found testing against real frames with NO poster visible at all (floor,
# wall, sky, distant barrier only): the per-frame adaptive vmin assumes
# there's always a genuinely dark barrier to anchor on, and when there
# isn't one, it just latches onto whatever's darkest in frame -- a sky
# gradient, a horizon band -- and the wide value bands then admit most of
# that gradient as "barrier". Two independent, real-data-backed guards
# against this:
_MAX_VMIN = 45          # every one of 36 real unclipped barrier frames across
                         # all 3 worlds had vmin <= 43 (the worst lighting
                         # case); most sky/floor-only false
                         # positives had vmin 55-76. If the frame's own
                         # darkest pixel in the search zone is already this
                         # bright, there is almost certainly no real barrier
                         # in view, so detection is skipped entirely.
_MIN_SOLIDITY = 0.6      # contour area / bounding-box area. Tried raising this
                         # to 0.75 to reject a borderline (0.60) sub-window
                         # false positive on empty sky -- reverted: the true
                         # minimum solidity among all 36 real unclipped
                         # winning candidates is 0.42, *below* that false
                         # positive's own 0.60, so no fixed cutoff separates
                         # them cleanly, and 0.75 cost a real unclipped
                         # detection and an IoU pass (35/36, 14/15) to fix
                         # one frame in a negative-only test that already has
                         # large headroom (>=15/18 either way against a
                         # >=10 requirement). Kept at 0.6, prioritising the
                         # primary, tightly-specified criteria (detection
                         # rate, IoU) over a secondary one with slack.

_SUBWINDOW_FRAC = 0.6    # width of each half-window, as a fraction of the
                         # full search zone. Found testing real frames: an
                         # unrelated dark object elsewhere in frame (a wall
                         # decoration, or another station's barrier) can sit
                         # close enough to the true target that even the
                         # narrowest value band still merges them into one
                         # blob across the *whole* zone -- searching the left
                         # and right halves separately, in addition to the
                         # full zone, recovers the true barrier alone in the
                         # half that excludes the other object. Overlapping
                         # (0.6, not 0.5) so a barrier straddling the middle
                         # isn't itself split in half.


def _barrier_candidates(frame_bgr: np.ndarray, x0: int, x1: int) -> list[tuple[int, int, int, int, float]]:
    """Every plausible barrier-shaped contour's bbox (x, y, w, h, area)
    found within columns [x0, x1) at any of _BARRIER_VALUE_BANDS, largest
    first. Near-duplicate boxes (same barrier found at more than one band)
    are kept -- downstream dedup happens naturally since they produce the
    same poster candidate. Empty if this window's own darkest pixel already
    looks too bright to be a real barrier (see _MAX_VMIN)."""
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    val = hsv[:, :, 2].astype(int)
    zone = val[:, x0:x1]
    if zone.size == 0 or int(zone.min()) > _MAX_VMIN:
        return []
    vmin = int(zone.min())
    boxes = []
    for band in _BARRIER_VALUE_BANDS:
        mask = (val <= vmin + band).astype(np.uint8) * 255
        mask[:, :x0] = 0
        mask[:, x1:] = 0
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, bw, bh = cv2.boundingRect(c)
            if bw < _MIN_BARRIER_SIDE_PX or bh < _MIN_BARRIER_SIDE_PX:
                continue
            if bw < _BARRIER_ASPECT_MIN * bh:
                continue
            area = cv2.contourArea(c)
            if area < _MIN_SOLIDITY * bw * bh:
                continue
            boxes.append((x, y, bw, bh, area))
    boxes.sort(key=lambda b: b[4], reverse=True)
    return boxes


def _all_barrier_candidates(frame_bgr: np.ndarray) -> list[tuple[int, int, int, int, float, int]]:
    """_barrier_candidates run over the full search zone plus overlapping
    left and right half-windows (see _SUBWINDOW_FRAC), pooled together.
    Each result also carries its own window's width, EXCEPT for the two
    half-windows, which report a width of -1 (meaning: never treat as
    degenerate). "Fills (almost) the whole window" is only a bad sign for
    the full-zone search -- that means nothing more specific than a big
    chunk of the *whole frame* was found. For a half-window, deliberately
    narrowed precisely to try to exclude an unrelated object elsewhere in
    frame, filling it is the expected, correct outcome of a working search,
    not a sign of a vague, unlocalised one -- treating it the same way
    defeated the entire purpose of searching sub-windows in the first
    place (tested: without this distinction, the half-window candidates
    still lost to the full-window one on raw area, unchanged result)."""
    w = frame_bgr.shape[1]
    x0, x1 = int(w * _SIDE_MARGIN_FRAC), int(w * (1 - _SIDE_MARGIN_FRAC))
    half = int((x1 - x0) * _SUBWINDOW_FRAC)
    windows = [(x0, x1, x1 - x0), (x0, x0 + half, -1), (x1 - half, x1, -1)]
    out = []
    for wx0, wx1, degenerate_zone_w in windows:
        for bx, by, bw, bh, area in _barrier_candidates(frame_bgr, wx0, wx1):
            out.append((bx, by, bw, bh, area, degenerate_zone_w))
    return out


def _poster_from_barrier(bx: int, by: int, bw: int, bh: int) -> tuple[int, int, int, int]:
    """Project the poster's known size fraction onto a detected barrier box,
    centred on it. Applied uniformly -- no separate "clipped, use the raw
    box" case: that special case was tried and, combined with any margin
    narrow enough not to clip genuine barrier width, could not reliably
    tell a truly-clipped barrier apart from one merely shifted toward one
    side by an off-centre capture heading (+/-10 deg). Applying the same
    fraction unconditionally underestimates the poster at very close range
    (where the detected barrier itself is already an underestimate, being
    clipped) rather than overestimating it -- and the size/aspect-ratio
    filters below reject the frames that would be underestimated too far
    to be plausible, which is exactly the intended behaviour for a case
    outside where this method is meant to work (see Issue #5's own
    close-range clipping notes)."""
    pw = int(round(bw * _POSTER_WIDTH_FRAC))
    ph = int(round(bh * _POSTER_HEIGHT_FRAC))
    cx, cy = bx + bw // 2, by + bh // 2
    return max(0, cx - pw // 2), max(0, cy - ph // 2), pw, ph


def find_poster_region(image: np.ndarray, debug: bool = False, debug_path: str | Path | None = None):
    """Return (x, y, w, h) for the most plausible poster region in `image`
    (BGR, as from camera_bgr()), or None if no plausible candidate survives.

    The full ranked candidate list (largest first, each a dict with "box",
    "area" and the "from_barrier" box it was derived from) is left on
    `find_poster_region.last_candidates` after every call, for debugging.

    With `debug=True`, writes an annotated frame (chosen box in red, other
    candidates in orange) to `debug_path` (default a fixed path under /tmp)
    -- this only affects what gets written to disk, never the returned box.
    """
    h, w = image.shape[:2]
    candidates = []
    for bx, by, bw, bh, _area, zone_w in _all_barrier_candidates(image):
        px, py, pw, ph = _poster_from_barrier(bx, by, bw, bh)
        if pw <= 0 or ph <= 0 or py + ph > h or px + pw > w:
            continue
        if not (MIN_POSTER_AREA_PX <= pw * ph <= MAX_POSTER_AREA_PX):
            continue
        ratio = pw / ph
        if abs(ratio - ASPECT_RATIO_TARGET) > ASPECT_RATIO_TOLERANCE:
            continue
        # A barrier with no poster on it is a flat, uniform colour -- found
        # testing against real frames with a plain (posterless) navigation
        # barrier in view: the candidate region measured std=0.0 there vs
        # std>=9.9 on every real poster region tested (20 labelled frames).
        # This is the one check that actually looks at the poster's own
        # printed content, not just the barrier landmark around it.
        gray = cv2.cvtColor(image[py:py + ph, px:px + pw], cv2.COLOR_BGR2GRAY)
        if gray.std() < MIN_POSTER_INTERNAL_STD:
            continue
        # A barrier candidate spanning (almost) the whole detection zone
        # hasn't found anything specific -- it's "everything in the window
        # was dark enough", not a located object. Tested on real frames:
        # this degenerate case sometimes still beats a real, smaller, more
        # accurate candidate on raw area and was winning wrongly, but for a
        # few frames (one hard lighting case fragments its true barrier
        # into pieces too small to individually clear MIN_POSTER_AREA_PX) a
        # degenerate box is the only candidate available at all -- so it's
        # deprioritised, not rejected outright: only used if nothing more
        # specific survives.
        degenerate = zone_w > 0 and bw >= 0.9 * zone_w
        candidates.append({
            "box": (px, py, pw, ph), "area": pw * ph,
            "from_barrier": (bx, by, bw, bh), "degenerate": degenerate,
        })
    candidates.sort(key=lambda c: (c["degenerate"], -c["area"]))
    find_poster_region.last_candidates = candidates

    chosen = candidates[0]["box"] if candidates else None

    if debug:
        vis = image.copy()
        for i, c in enumerate(candidates):
            x, y, cw, ch = c["box"]
            color = (0, 0, 255) if i == 0 else (0, 165, 255)
            cv2.rectangle(vis, (x, y), (x + cw, y + ch), color, 1)
        out_path = Path(debug_path) if debug_path else Path("/tmp/find_poster_region_debug.png")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), vis)

    return chosen


find_poster_region.last_candidates = []


# ---------------------------------------------------------------------------
# Issue #8: target identification on an already-isolated poster crop
# ---------------------------------------------------------------------------

NO_MATCH = "NO_MATCH"
TARGET_LABELS = tuple(CONFIG["target_labels"])

# Tuned on the real Issue #6/Issue #7 captures: with the frozen-ResNet head
# below, the best usable crop for seven of eight target classes clears both
# thresholds, while central floor/no-poster patches stayed below 0.50. The
# margin prevents weak "coin flip" classifications from being accepted even
# when the top softmax score alone is moderately high.
MIN_CONFIDENCE = 0.50
MIN_CONFIDENCE_MARGIN = 0.20
IDENTIFIER_TRAINING_STEPS = 60
IDENTIFIER_SEED = 0

_IDENTIFIER = None


class _TargetIdentifier:
    def __init__(self):
        try:
            import torch
            import torch.nn as nn
            import torchvision
            from torchvision import transforms as T
        except Exception as exc:  # pragma: no cover - depends on local Webots env
            raise RuntimeError(
                "identify() needs torch and torchvision in the active Python environment"
            ) from exc

        self.torch = torch
        self.transforms = T
        self.labels = list(TARGET_LABELS)

        torch.manual_seed(IDENTIFIER_SEED)
        ref_images = []
        for label in self.labels:
            path = ROOT / "textures" / f"target_{label}.png"
            image = cv2.imread(str(path))
            if image is None:
                raise RuntimeError(f"Missing reference image: {path}")
            ref_images.append(T.functional.to_pil_image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))

        self.model = torchvision.models.resnet18(
            weights=torchvision.models.ResNet18_Weights.IMAGENET1K_V1
        )
        for param in self.model.parameters():
            param.requires_grad = False
        self.model.fc = nn.Linear(512, len(self.labels))

        augment = T.Compose([
            T.RandomResizedCrop(112, scale=(0.35, 1.0), ratio=(0.6, 1.4)),
            T.RandomApply([T.Resize(24), T.Resize(112)], p=0.5),
            T.ColorJitter(brightness=(0.25, 0.9), contrast=0.4, saturation=0.4, hue=0.03),
            T.RandomApply([T.GaussianBlur(5, sigma=(0.3, 1.5))], p=0.5),
            T.RandomRotation(8),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        optimiser = torch.optim.Adam(self.model.fc.parameters(), lr=1e-3)
        self.model.train()
        for _ in range(IDENTIFIER_TRAINING_STEPS):
            xs, ys = [], []
            for class_index, image in enumerate(ref_images):
                for _ in range(16):
                    xs.append(augment(image))
                    ys.append(class_index)
            loss = torch.nn.functional.cross_entropy(
                self.model(torch.stack(xs)),
                torch.tensor(ys),
            )
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()

        self.model.eval()
        self.inference_transform = T.Compose([
            T.ToTensor(),
            T.Resize((112, 112)),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    def score(self, crop_bgr: np.ndarray) -> dict:
        rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        with self.torch.no_grad():
            probs = self.model(self.inference_transform(rgb).unsqueeze(0)).softmax(1)[0]
        values, indices = self.torch.sort(probs, descending=True)
        best_index = int(indices[0])
        runner_index = int(indices[1])
        best_confidence = float(values[0])
        runner_confidence = float(values[1])
        return {
            "raw_label": self.labels[best_index],
            "confidence": best_confidence,
            "runner_up": self.labels[runner_index],
            "runner_up_confidence": runner_confidence,
            "margin": best_confidence - runner_confidence,
            "scores": {
                self.labels[int(i)]: float(probs[int(i)])
                for i in range(len(self.labels))
            },
        }


def _get_identifier():
    global _IDENTIFIER
    if _IDENTIFIER is None:
        _IDENTIFIER = _TargetIdentifier()
    return _IDENTIFIER


def identify(crop: np.ndarray) -> tuple[str, float]:
    """Input: BGR poster crop from `find_poster_region()`.

    Output: `(label, confidence)`, where `label` is one of
    `CONFIG["target_labels"]` or the exact sentinel `NO_MATCH`.

    Assumptions: `crop` is a non-empty BGR image of a plausible poster region;
    reference images live under `textures/target_<label>.png`, with labels read
    only from `CONFIG["target_labels"]`.

    Failure behaviour: returns `(NO_MATCH, confidence)` when the classifier is
    unavailable, the crop is invalid, the best class is below `MIN_CONFIDENCE`,
    or the best-vs-runner-up gap is below `MIN_CONFIDENCE_MARGIN`; callers must
    inspect the next station rather than commit to a target on `NO_MATCH`.
    """
    if crop is None or getattr(crop, "size", 0) == 0:
        result = {
            "label": NO_MATCH,
            "raw_label": NO_MATCH,
            "confidence": 0.0,
            "runner_up": NO_MATCH,
            "runner_up_confidence": 0.0,
            "margin": 0.0,
            "accepted": False,
            "reject_reason": "empty_crop",
            "scores": {},
        }
        identify.last_result = result
        identify.last_scores = {}
        return NO_MATCH, 0.0

    try:
        scored = _get_identifier().score(crop)
    except Exception as exc:  # pragma: no cover - depends on active Python env
        result = {
            "label": NO_MATCH,
            "raw_label": NO_MATCH,
            "confidence": 0.0,
            "runner_up": NO_MATCH,
            "runner_up_confidence": 0.0,
            "margin": 0.0,
            "accepted": False,
            "reject_reason": f"classifier_unavailable:{type(exc).__name__}",
            "scores": {},
        }
        identify.last_result = result
        identify.last_scores = {}
        return NO_MATCH, 0.0

    reject_reason = None
    if scored["confidence"] < MIN_CONFIDENCE:
        reject_reason = "below_min_confidence"
    elif scored["margin"] < MIN_CONFIDENCE_MARGIN:
        reject_reason = "below_margin"

    label = NO_MATCH if reject_reason else scored["raw_label"]
    result = {
        **scored,
        "label": label,
        "accepted": label != NO_MATCH,
        "reject_reason": reject_reason,
    }
    identify.last_result = result
    identify.last_scores = scored["scores"]
    return label, scored["confidence"]


identify.last_result = {
    "label": NO_MATCH,
    "raw_label": NO_MATCH,
    "confidence": 0.0,
    "runner_up": NO_MATCH,
    "runner_up_confidence": 0.0,
    "margin": 0.0,
    "accepted": False,
    "reject_reason": "not_run",
    "scores": {},
}
identify.last_scores = {}
