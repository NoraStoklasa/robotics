"""Issue #7: find the poster region in a camera frame.

How it works: the barrier the poster is stuck on is the darkest solid thing
in view, so we find *that* first with an HSV brightness threshold plus
contours, then work out where the poster must be inside it -- the poster is
always the same known fraction of the barrier (0.22 m of a 0.50 m x 0.28 m
barrier face) and sits in the middle of it.

Why not just threshold the bright poster directly, as Issue #7 suggests? We
tried it on real frames and it fails on dark targets like the backpack and
headphones, which come out no brighter than the barrier itself. The barrier
is the reliable landmark instead.

All the measurements behind the constants and design choices below live in
docs/find_poster_region_notes.md -- check there before changing any number.
"""

from pathlib import Path

import cv2
import numpy as np

from project_utils import CONFIG, ROOT

# ---- How big/square a real poster looks in the camera, measured from real
# captures in docs/poster_visibility.md (not guessed). Full working: docs/find_poster_region_notes.md
MIN_POSTER_SIDE_PX = 25          # smallest side we'll believe (measured 31+)
MIN_POSTER_AREA_PX = MIN_POSTER_SIDE_PX ** 2   # 625
MAX_POSTER_AREA_PX = 4000        # bigger than this = two objects merged, reject
ASPECT_RATIO_TARGET = 1.0        # poster is 0.22 m x 0.22 m -- square head-on
ASPECT_RATIO_TOLERANCE = 0.7     # generous: small boxes are noisy
MIN_POSTER_INTERNAL_STD = 8.0    # a bare barrier is flat (std 0.0); a real
                                  # poster has detail (std >= 9.9)

# ---- Finding the barrier. No single brightness cut-off works at every
# distance, so we try four and pool whatever each one finds; the size and
# shape filters then pick the best. Full working: docs/find_poster_region_notes.md
_BARRIER_VALUE_BANDS = (25, 35, 45, 55)
_ROBUST_VMIN_PERCENTILE = 5       # backup anchor, used only as a last resort
_ROBUST_VMIN_GAP_MIN = 30         # ...and only if it's this far from the darkest pixel
_MIN_BARRIER_SIDE_PX = 8          # smallest believable barrier side
_BARRIER_ASPECT_MIN = 0.5         # reject tall thin slivers (e.g. a dark hose)
_SIDE_MARGIN_FRAC = 0.05          # ignore the outer 5% each side: we always
                                   # aim at the target first, so it's roughly
                                   # centred, and this stops a barrier at the
                                   # frame edge merging into our blob

# Poster geometry as a fraction of the barrier's own face
# (protos/TexturedBarrier.proto: barrier 0.50 x 0.28 m, poster 0.22 x 0.22 m).
_POSTER_WIDTH_FRAC = 0.22 / 0.50
_POSTER_HEIGHT_FRAC = 0.22 / 0.28

# ---- Guards for frames with no poster in view at all (just floor or sky).
# Without these the search latches onto whatever happens to be darkest, like
# a sky gradient, and calls it a barrier. Full working: docs/find_poster_region_notes.md
_MAX_VMIN = 45          # if even the darkest pixel is this bright, there is
                         # no real barrier in view -- don't bother looking
_MIN_SOLIDITY = 0.6      # contour area / box area: rejects hollow, straggly
                         # blobs. Tried 0.75, reverted -- it broke real ones
_SUBWINDOW_FRAC = 0.6    # we also search the left and right halves on their
                         # own, so a nearby dark object can't merge with the
                         # real barrier. Overlapping so nothing is split in two
_CLOSE_CROP_TOP_PX = 8   # very close, top-clipped crops get widened a little,
                         # or the target is too tightly boxed to recognise


# Used to sort the boxes below by their contour area, biggest first.
# sorted()/sort() needs a function saying which part of each box to compare.
def box_area(box):
    return box[4]


# Threshold the brightness image at each of the value bands, find the dark
# blobs, and keep the ones that are actually barrier-shaped. `anchor` is the
# brightness we count "dark" from; `cap_height` trims a box that came out
# taller than it is wide (see _barrier_candidates for why).
def _boxes_for_anchor(val, x0, x1, anchor, cap_height):
    found = []
    for band in _BARRIER_VALUE_BANDS:
        # White (255) wherever the pixel is dark enough, black everywhere else.
        mask = (val <= anchor + band).astype(np.uint8) * 255
        # Blank out everything outside the columns we were asked to search.
        mask[:, :x0] = 0
        mask[:, x1:] = 0
        # Closing fills small holes so one barrier comes out as one blob.
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, bw, bh = cv2.boundingRect(c)
            # Too small to be a barrier at any distance we care about.
            if bw < _MIN_BARRIER_SIDE_PX or bh < _MIN_BARRIER_SIDE_PX:
                continue
            # Too tall and thin to be a barrier.
            if bw < _BARRIER_ASPECT_MIN * bh:
                continue
            area = cv2.contourArea(c)
            # Too "hollow": the blob doesn't fill enough of its own box.
            if area < _MIN_SOLIDITY * bw * bh:
                continue
            if cap_height and bh > bw:
                bh = bw
            found.append((x, y, bw, bh, area))
    return found


def _barrier_candidates(frame_bgr, x0, x1, allow_robust_anchor=True):
    """Find the dark barrier in one vertical strip of the picture.

    Returns every barrier-shaped box found at any of the brightness bands,
    biggest first, as (x, y, w, h, area). Returns nothing if even the darkest
    pixel in the strip is too bright to be a real barrier.

    Normally we measure "dark" from the darkest pixel in the strip. If that
    finds nothing at all, and `allow_robust_anchor` is on, we retry from a
    low percentile instead -- needed for the fire extinguisher, whose black
    hose is darker than the barrier behind it. Those retry boxes also get
    their height capped at their width, because the real barrier is never
    taller than it is wide and the wide bands bleed into the floor.
    Measurements and the frames that forced each rule: docs/find_poster_region_notes.md
    """
    # Convert to HSV and keep only the "value" (brightness) channel, because
    # the barrier is found by how dark it is, not by its colour.
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    val = hsv[:, :, 2].astype(int)
    zone = val[:, x0:x1]
    # Nothing dark enough in this strip of the image, so there is no barrier.
    if zone.size == 0 or int(zone.min()) > _MAX_VMIN:
        return []
    vmin = int(zone.min())

    # First try: anchor on the darkest pixel actually in the strip.
    boxes = _boxes_for_anchor(val, x0, x1, vmin, cap_height=False)
    # Nothing found, so try the backup anchor described in the docstring.
    if not boxes and allow_robust_anchor:
        vmin_robust = int(np.percentile(zone, _ROBUST_VMIN_PERCENTILE))
        # Only worth trying once it's far enough from the true min to be a
        # genuinely different region -- the fire_extinguisher hose-vs-panel
        # gap measured 54 on every affected frame.
        if vmin_robust - vmin >= _ROBUST_VMIN_GAP_MIN:
            boxes = _boxes_for_anchor(val, x0, x1, vmin_robust, cap_height=True)
    # Biggest box first, so the most likely barrier is looked at first.
    boxes.sort(key=box_area, reverse=True)
    return boxes


def _all_barrier_candidates(frame_bgr):
    """Run the barrier search three times and pool the results: once over the
    whole middle of the picture, then over its left half and its right half.
    Searching the halves helps when another dark object sits next to the real
    barrier and the two merge into one blob.

    Each result carries the width of the window it came from, except the two
    halves, which report -1. That width is only used to spot a box that fills
    its whole window (see find_poster_region) -- which means "everything here
    was dark", not "I found something". For a half-window, filling it is the
    correct outcome, so the check is disabled there.

    The percentile fallback is decided once, across all three windows, rather
    than per window -- per window let an empty half produce a bogus square
    blob that beat a correct candidate. Full working: docs/find_poster_region_notes.md
    """
    # Cut a small margin off each side of the picture first, then work out
    # the three column ranges we are going to search in.
    w = frame_bgr.shape[1]
    x0 = int(w * _SIDE_MARGIN_FRAC)
    x1 = int(w * (1 - _SIDE_MARGIN_FRAC))
    half = int((x1 - x0) * _SUBWINDOW_FRAC)
    # Each entry is (first column, last column, width used for the "too vague"
    # check). The two half-windows use -1 so they never count as too vague.
    windows = [(x0, x1, x1 - x0), (x0, x0 + half, -1), (x1 - half, x1, -1)]

    # First pass: the normal search, in all three windows.
    out = []
    for wx0, wx1, degenerate_zone_w in windows:
        boxes = _barrier_candidates(frame_bgr, wx0, wx1, allow_robust_anchor=False)
        for bx, by, bw, bh, area in boxes:
            out.append((bx, by, bw, bh, area, degenerate_zone_w))

    # Only if that found nothing anywhere do we allow the backup anchor -- see
    # the docstring above for why it is a last resort and not a per-window one.
    if not out:
        for wx0, wx1, degenerate_zone_w in windows:
            boxes = _barrier_candidates(frame_bgr, wx0, wx1, allow_robust_anchor=True)
            for bx, by, bw, bh, area in boxes:
                out.append((bx, by, bw, bh, area, degenerate_zone_w))
    return out


def _poster_from_barrier(bx, by, bw, bh):
    """Work out where the poster is, given where the barrier is.

    The poster is always the same fraction of the barrier and sits in the
    middle of it, so scale the barrier box down and keep its centre.

    We apply this the same way to every frame, including close-up ones where
    the barrier is clipped. We tried special-casing clipped barriers and
    couldn't tell them apart from ones merely shifted by an off-centre
    heading, so the plausibility filters reject those instead. See docs/find_poster_region_notes.md
    """
    # Shrink the barrier box down to poster size...
    pw = int(round(bw * _POSTER_WIDTH_FRAC))
    ph = int(round(bh * _POSTER_HEIGHT_FRAC))
    # ...then put it back centred on the middle of the barrier. max(0, ...)
    # stops the box starting off the left/top edge of the picture.
    cx = bx + bw // 2
    cy = by + bh // 2
    px = max(0, cx - pw // 2)
    py = max(0, cy - ph // 2)
    return px, py, pw, ph


def _expanded_close_crop(box, frame_w, frame_h):
    """Widen very close, top-clipped crops a little before identification.

    At close range the exact projection can cut off so much of the target
    that the classifier rejects it. The guard is deliberately tight so
    normally-framed boxes keep their original geometry (the IoU test checks
    those against hand-labelled ground truth). See docs/find_poster_region_notes.md
    """
    x, y, w, h = box
    if y > _CLOSE_CROP_TOP_PX or h >= 50:
        return box

    nx = max(0, x - int(round(0.15 * w)))
    ny = 0
    nw = min(frame_w - nx, int(round(1.60 * w)))
    nh = min(frame_h - ny, int(round(1.50 * h)))
    if nw * nh <= MAX_POSTER_AREA_PX:
        return nx, ny, nw, nh
    return box


# Decides the order the candidate poster boxes get ranked in. sort() puts the
# smallest of these three values first, so this reads as: put the vague
# "whole window was dark" boxes last; of the rest prefer the one closest to a
# square (the poster really is square); and if two are equally square, prefer
# the bigger one. The minus sign flips area so that bigger counts as smaller
# here, i.e. comes first.
def candidate_rank(candidate):
    x, y, box_w, box_h = candidate["box"]
    squareness = abs(box_w / box_h - ASPECT_RATIO_TARGET)
    return (candidate["degenerate"], squareness, -candidate["area"])


def find_poster_region(image, debug=False, debug_path=None):
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

    # Turn every barrier we found into a poster box, then throw away the ones
    # that can't be a real poster.
    candidates = []
    for bx, by, bw, bh, _area, zone_w in _all_barrier_candidates(image):
        px, py, pw, ph = _poster_from_barrier(bx, by, bw, bh)
        # Reject anything with no size, or that falls off the picture.
        if pw <= 0 or ph <= 0 or py + ph > h or px + pw > w:
            continue
        # Reject anything far too small or far too big to be a poster.
        if not (MIN_POSTER_AREA_PX <= pw * ph <= MAX_POSTER_AREA_PX):
            continue
        # Reject anything that isn't roughly square -- the poster is 0.22 m
        # by 0.22 m, so head-on it should look square.
        ratio = pw / ph
        if abs(ratio - ASPECT_RATIO_TARGET) > ASPECT_RATIO_TOLERANCE:
            continue
        # A barrier with no poster on it is a flat, even colour, so if the
        # region has almost no variation there's no poster there. This is the
        # one check that looks at the poster's own printed content rather
        # than the barrier around it.
        gray = cv2.cvtColor(image[py:py + ph, px:px + pw], cv2.COLOR_BGR2GRAY)
        if gray.std() < MIN_POSTER_INTERNAL_STD:
            continue
        # A box filling almost the whole search window hasn't really found
        # anything -- it just means everything in there was dark. We push
        # these to the back rather than binning them, because occasionally
        # one is the only candidate we have. See docs/find_poster_region_notes.md
        degenerate = zone_w > 0 and bw >= 0.9 * zone_w
        candidates.append({
            "box": (px, py, pw, ph), "area": pw * ph,
            "from_barrier": (bx, by, bw, bh), "degenerate": degenerate,
        })
    # When two boxes are close in size, prefer the squarer one over the
    # merely bigger one -- a wall picture once beat the real poster on size.
    candidates.sort(key=candidate_rank)
    if candidates:
        # Only the winning box can get the close-range widening; the rest are
        # left exactly as they were.
        best = candidates[0]
        expanded = _expanded_close_crop(best["box"], w, h)
        best["box"] = expanded
        best["area"] = expanded[2] * expanded[3]
    find_poster_region.last_candidates = candidates

    chosen = candidates[0]["box"] if candidates else None

    # Debug drawing only. This writes a picture to disk for us to look at and
    # never changes the box we return.
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

# How sure the model has to be before we believe it. Tuned on real captures:
# 7 of 8 targets clear both, while floor/no-poster patches stay under 0.50.
# The margin stops us accepting a near coin-flip between two labels. See docs/find_poster_region_notes.md
MIN_CONFIDENCE = 0.50            # top score must be at least this
MIN_CONFIDENCE_MARGIN = 0.20     # ...and this far ahead of the runner-up

# The model only knows 8 labels, so shown something else it still picks the
# closest one, sometimes confidently. As a sanity check we also compare the
# crop against the reference photo of whatever label it picked. See docs/find_poster_region_notes.md
MIN_REFERENCE_SIMILARITY = -0.05
# Some labels get a stricter floor of their own. Only labels whose real
# in-game posters actually score positively against their reference photo can
# have one -- fire_extinguisher and coffee_mug deliberately don't, because
# their real renders score BELOW their own distractors. Measurements for every
# label, and why each was added or dropped: docs/find_poster_region_notes.md
MIN_REFERENCE_SIMILARITY_BY_LABEL = {
    "wall_clock": 0.00,
    "camera": 0.00,      # added 2026-09-17: a real headphones poster was
                          # being read as camera (-0.029) while the genuine
                          # camera scores +0.123..+0.176 -- docs/decision_log.md
}
_REFERENCE_SIMILARITY_SIZE = 64
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
        ref_arrays = []
        for label in self.labels:
            path = ROOT / "textures" / f"target_{label}.png"
            image = cv2.imread(str(path))
            if image is None:
                raise RuntimeError(f"Missing reference image: {path}")
            ref_arrays.append(image)
            ref_images.append(T.functional.to_pil_image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))
        # Work out the comparison features for each reference photo once, up
        # front, and store them in a dict keyed by the label name.
        self.reference_features = {}
        for i in range(len(self.labels)):
            label = self.labels[i]
            self.reference_features[label] = self._reference_features(ref_arrays[i])

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

    @staticmethod
    def _reference_features(image_bgr):
        resized = cv2.resize(
            image_bgr,
            (_REFERENCE_SIMILARITY_SIZE, _REFERENCE_SIMILARITY_SIZE),
            interpolation=cv2.INTER_AREA,
        )

        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY).astype(np.float32)
        gray = (gray - gray.mean()) / (gray.std() + 1e-6)

        lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB).astype(np.float32)
        lab = (lab - lab.mean(axis=(0, 1), keepdims=True)) / (
            lab.std(axis=(0, 1), keepdims=True) + 1e-6
        )

        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [24, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        return gray, lab.reshape(-1), hist

    def _reference_similarity(self, crop_bgr, label):
        gray, lab, hist = self._reference_features(crop_bgr)
        ref_gray, ref_lab, ref_hist = self.reference_features[label]

        gray_score = float((gray * ref_gray).mean())
        lab_score = float(
            np.dot(lab, ref_lab) / (np.linalg.norm(lab) * np.linalg.norm(ref_lab) + 1e-6)
        )
        hist_score = float(cv2.compareHist(hist, ref_hist, cv2.HISTCMP_CORREL))
        return 0.55 * gray_score + 0.35 * lab_score + 0.10 * hist_score

    def score(self, crop_bgr):
        rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        with self.torch.no_grad():
            probs = self.model(self.inference_transform(rgb).unsqueeze(0)).softmax(1)[0]
        values, indices = self.torch.sort(probs, descending=True)
        best_index = int(indices[0])
        runner_index = int(indices[1])
        best_confidence = float(values[0])
        runner_confidence = float(values[1])
        raw_label = self.labels[best_index]
        # A couple of labels have their own similarity floor; everything else
        # uses the shared default.
        if raw_label in MIN_REFERENCE_SIMILARITY_BY_LABEL:
            reference_threshold = MIN_REFERENCE_SIMILARITY_BY_LABEL[raw_label]
        else:
            reference_threshold = MIN_REFERENCE_SIMILARITY

        # The model's score for every label, so a failed match can be explained.
        all_scores = {}
        for i in range(len(self.labels)):
            all_scores[self.labels[i]] = float(probs[i])

        return {
            "raw_label": raw_label,
            "confidence": best_confidence,
            "runner_up": self.labels[runner_index],
            "runner_up_confidence": runner_confidence,
            "margin": best_confidence - runner_confidence,
            "reference_similarity": self._reference_similarity(crop_bgr, raw_label),
            "reference_threshold": reference_threshold,
            "scores": all_scores,
        }


def _get_identifier():
    global _IDENTIFIER
    if _IDENTIFIER is None:
        _IDENTIFIER = _TargetIdentifier()
    return _IDENTIFIER


# Every "couldn't identify it" answer is the same apart from the reason, so
# build it in one place instead of writing the same dict out three times.
# `reason` records which check failed, which is handy when debugging.
def no_match_result(reason):
    return {
        "label": NO_MATCH,
        "raw_label": NO_MATCH,
        "confidence": 0.0,
        "runner_up": NO_MATCH,
        "runner_up_confidence": 0.0,
        "margin": 0.0,
        "reference_similarity": 0.0,
        "reference_threshold": None,
        "accepted": False,
        "reject_reason": reason,
        "scores": {},
    }


def identify(crop):
    """Input: BGR poster crop from `find_poster_region()`.

    Output: `(label, confidence)`, where `label` is one of
    `CONFIG["target_labels"]` or the exact sentinel `NO_MATCH`.

    Assumptions: `crop` is a non-empty BGR image of a plausible poster region;
    reference images live under `textures/target_<label>.png`, with labels read
    only from `CONFIG["target_labels"]`.

    Failure behaviour: returns `(NO_MATCH, confidence)` when the classifier is
    unavailable, the crop is invalid, the best class is below `MIN_CONFIDENCE`,
    the best-vs-runner-up gap is below `MIN_CONFIDENCE_MARGIN`, or the crop
    does not look enough like the reference image for the predicted class;
    callers must inspect the next station rather than commit to a target on
    `NO_MATCH`.
    """
    if crop is None or getattr(crop, "size", 0) == 0:
        identify.last_result = no_match_result("empty_crop")
        identify.last_scores = {}
        return NO_MATCH, 0.0

    try:
        scored = _get_identifier().score(crop)
    except Exception as exc:  # pragma: no cover - depends on active Python env
        identify.last_result = no_match_result(f"classifier_unavailable:{type(exc).__name__}")
        identify.last_scores = {}
        return NO_MATCH, 0.0

    reject_reason = None
    if scored["confidence"] < MIN_CONFIDENCE:
        reject_reason = "below_min_confidence"
    elif scored["margin"] < MIN_CONFIDENCE_MARGIN:
        reject_reason = "below_margin"
    elif scored["reference_similarity"] < scored["reference_threshold"]:
        reject_reason = "below_reference_similarity"

    # Any rejection reason at all means we refuse to commit to a label.
    if reject_reason:
        label = NO_MATCH
    else:
        label = scored["raw_label"]

    # Start from everything score() worked out, then add our own verdict.
    result = dict(scored)
    result["label"] = label
    result["accepted"] = (label != NO_MATCH)
    result["reject_reason"] = reject_reason
    identify.last_result = result
    identify.last_scores = scored["scores"]
    return label, scored["confidence"]


# Starting value, in case anything reads this before identify() has ever run.
identify.last_result = no_match_result("not_run")
identify.last_scores = {}


_IDENTIFY_MAX_RANKED_CANDIDATES = 3  # see identify_frame


def identify_frame(image):
    """Find the poster, then identify it -- trying a few different ideas of
    where the poster is, rather than trusting the single best-ranked box.

    For each of the top few candidates we try both the narrow poster box and
    the whole barrier box it came from, and keep whichever answer the
    classifier actually accepts. This matters because the narrow box can land
    in the gap between a pair of headphones, and because the top-ranked
    candidate is occasionally the wrong one. If nothing is accepted we keep
    the top candidate's own rejected result. Full working, including the
    approaches that didn't work: docs/find_poster_region_notes.md
    """
    crop_box = find_poster_region(image)
    # No poster found at all, so there is nothing to identify.
    if crop_box is None:
        return identify(None)

    # Build the list of crops to try. For each of the top few candidates we
    # try both the narrow poster box and the whole barrier box it came from.
    # seen_poster_boxes stops us counting the same poster box twice when it
    # turned up at more than one brightness band.
    boxes = []
    seen_poster_boxes = []
    for c in find_poster_region.last_candidates:
        if c["box"] in seen_poster_boxes:
            continue
        seen_poster_boxes.append(c["box"])
        # Stop once we have looked at enough candidates.
        if len(seen_poster_boxes) > _IDENTIFY_MAX_RANKED_CANDIDATES:
            break
        for box in (c["box"], c["from_barrier"]):
            if box not in boxes:
                boxes.append(box)
    # Try identifying each candidate crop, then keep the best answer. "Best"
    # means: an accepted result always beats a rejected one, and between two
    # results of the same kind the higher confidence wins. We only swap on a
    # strictly better score, so if two tie the earlier (higher-ranked) crop
    # keeps the win.
    best_label = None
    best_confidence = None
    best_result = None
    best_score = None
    for bx, by, bw, bh in boxes:
        label, confidence = identify(image[by:by + bh, bx:bx + bw])
        result = dict(identify.last_result)
        score = (result["accepted"], confidence)
        if best_score is None or score > best_score:
            best_label = label
            best_confidence = confidence
            best_result = result
            best_score = score

    identify.last_result = best_result
    identify.last_scores = best_result["scores"]
    return best_label, best_confidence
