"""Issue #7: evaluate find_poster_region() and write docs/find_poster_region.md.

Runs the real detector (no synthetic data) against:
- All 103 real frames from Issues #5 and #6 -- the >=90%-detection-rate
  criterion, scored only on the unclipped subset it's meant to cover.
- The 20 required hand-labelled, unclipped frames
  (docs/data/poster_region_labels.json, labelled independently rather than
  generated from the detector) -- the IoU criterion.
- The 5 additional clipped stress-case labels
  (docs/data/poster_region_clipped_labels.json) -- reported separately so they
  cannot dilute or confuse the required IoU set.
- The 18 real "no poster visible" frames from the Issue #7 negative-capture
  sweep (docs/data/no_poster_captures/) -- the >=10-true-negatives criterion.

Also renders a figure strip (raw frame / mask / chosen box) for a handful of
frames, for the report. No Webots needed.
"""

from __future__ import annotations

import glob
import json
import os
import re
from pathlib import Path

import cv2
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "controllers" / "group_project_controller"))
import vision_utils as vu  # noqa: E402

WEBOTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = WEBOTS_ROOT.parent
DOC_PATH = REPO_ROOT / "docs" / "find_poster_region.md"
STRIP_PATH = REPO_ROOT / "docs" / "data" / "find_poster_region_strip.png"
CONSTRAINED = {"S4": 0.42, "S5": 0.57, "S7": 0.47}


def load_evaluated_frames() -> list[dict]:
    frames = []
    for f5 in glob.glob(str(REPO_ROOT / "docs/data/poster_captures/*/results.json")):
        for r in json.loads(Path(f5).read_text()):
            frames.append({"frame": r["frame"], "distance_m": r["distance_m"]})
    for f6 in glob.glob(str(REPO_ROOT / "docs/data/vision_eval_captures/*/manifest.json")):
        for r in json.loads(Path(f6).read_text()):
            frames.append({"frame": r["frame"], "distance_m": r["distance_m"]})
    for f in frames:
        m = re.search(r"_(S\d)_", f["frame"]) or re.search(r"/(S\d)/", f["frame"])
        f["station"] = m.group(1) if m else "?"
        max_clear = CONSTRAINED.get(f["station"], 1.3)
        f["unclipped"] = f["distance_m"] >= 0.8 and f["distance_m"] <= max_clear + 0.01
    return frames


def iou(a, b) -> float:
    if a is None or b is None:
        return 0.0
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x0, y0 = max(ax, bx), max(ay, by)
    x1, y1 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def evaluate_detection_rate(frames: list[dict]) -> dict:
    hit_u = miss_u = hit_c = miss_c = 0
    for f in frames:
        img = cv2.imread(str(REPO_ROOT / f["frame"]))
        box = vu.find_poster_region(img)
        if f["unclipped"]:
            hit_u, miss_u = (hit_u + 1, miss_u) if box else (hit_u, miss_u + 1)
        else:
            hit_c, miss_c = (hit_c + 1, miss_c) if box else (hit_c, miss_c + 1)
    return {
        "unclipped_hit": hit_u, "unclipped_total": hit_u + miss_u,
        "clipped_hit": hit_c, "clipped_total": hit_c + miss_c,
    }


def evaluate_label_file(labels_path: Path) -> list[dict]:
    labels = json.loads(labels_path.read_text())
    rows = []
    for row in labels:
        img = cv2.imread(str(REPO_ROOT / row["frame"]))
        pred = vu.find_poster_region(img)
        gt = tuple(row["box"]) if row["box"] else None
        m = re.search(r"_(S\d)_", row["frame"]) or re.search(r"/(S\d)/", row["frame"])
        station = m.group(1) if m else "?"
        dm = re.search(r"_d(\d)p(\d+)", row["frame"])
        dist = float(f"{dm.group(1)}.{dm.group(2)}") if dm else None
        max_clear = CONSTRAINED.get(station, 1.3)
        unclipped = dist is not None and dist >= 0.8 and dist <= max_clear + 0.01
        rows.append({"frame": row["frame"], "gt": gt, "pred": pred, "iou": iou(pred, gt), "unclipped": unclipped})
    return rows


def evaluate_iou() -> dict:
    labels_path = REPO_ROOT / "docs/data/poster_region_labels.json"
    return evaluate_label_file(labels_path)


def evaluate_clipped_stress() -> list[dict]:
    labels_path = REPO_ROOT / "docs/data/poster_region_clipped_labels.json"
    return evaluate_label_file(labels_path) if labels_path.exists() else []


def evaluate_negatives() -> list[dict]:
    rows = []
    for f in sorted(glob.glob(str(REPO_ROOT / "docs/data/no_poster_captures/*/*.png"))):
        img = cv2.imread(f)
        box = vu.find_poster_region(img)
        rows.append({"frame": str(Path(f).relative_to(REPO_ROOT)), "pred": box})
    return rows


def save_strip(examples: list[tuple[str, tuple | None]]) -> None:
    """raw / mask / chosen-box strip for a handful of frames."""
    tiles = []
    for path, box in examples:
        img = cv2.imread(str(REPO_ROOT / path))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        val = hsv[:, :, 2].astype(int)
        w = img.shape[1]
        x0, x1 = int(w * vu._SIDE_MARGIN_FRAC), int(w * (1 - vu._SIDE_MARGIN_FRAC))
        vmin = int(val[:, x0:x1].min()) if val[:, x0:x1].min() <= vu._MAX_VMIN else vu._MAX_VMIN
        mask = ((val <= vmin + 45)).astype(np.uint8) * 255
        mask[:, :x0] = 0
        mask[:, x1:] = 0
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        annotated = img.copy()
        if box:
            x, y, bw, bh = box
            cv2.rectangle(annotated, (x, y), (x + bw, y + bh), (0, 0, 255), 1)
        row = np.hstack([
            cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
            cv2.resize(mask_bgr, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
            cv2.resize(annotated, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
        ])
        tiles.append(row)
    STRIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(STRIP_PATH), np.vstack(tiles))


def write_doc(det: dict, iou_rows: list[dict], clipped_rows: list[dict], neg_rows: list[dict]) -> None:
    required_iou = [r["iou"] for r in iou_rows]
    clipped_iou = [r["iou"] for r in clipped_rows]
    neg_none = sum(1 for r in neg_rows if r["pred"] is None)

    lines = [
        "# find_poster_region() Evaluation",
        "",
        "Recorded per [Issue #7](.github/issues/07-isolate-poster-region.md).",
        "",
        "## Method",
        "",
        "`find_poster_region()` (in `controllers/group_project_controller/vision_utils.py`) follows",
        "the Week 1 pipeline -- HSV threshold, contours, bounding boxes -- keyed off the barrier body",
        "rather than the poster panel directly (Issue #6 already found the poster's own brightness",
        "varies too much by target to threshold reliably; see the module's own docstring for the",
        "tested-and-rejected alternatives). The poster region is then the barrier's known geometric",
        "fraction (0.22/0.50 width, 0.22/0.28 height -- `protos/TexturedBarrier.proto`).",
        "",
        "Every design choice was tested against real frames, not reasoned about in the abstract --",
        "including guards added only after real false positives were found on frames with no poster",
        "at all (an absolute darkness ceiling, a solidity check, a check that the candidate actually",
        "contains printed content) and, after review, a search over overlapping left/right",
        "sub-windows in addition to the full frame (an unrelated dark object elsewhere in frame can",
        "sit close enough to the real target that no single threshold separates them within the full",
        "zone, but the half that excludes the other object isolates the real barrier cleanly). Full",
        "debugging history in `docs/find_poster_region_notes.md`.",
        "",
        "## Detection rate",
        "",
        f"| Set | Hit | Total | Rate |",
        f"|---|---:|---:|---:|",
        f"| Unclipped (required, >=90%) | {det['unclipped_hit']} | {det['unclipped_total']} | {100*det['unclipped_hit']/det['unclipped_total']:.1f}% |",
        f"| Clipped (not required) | {det['clipped_hit']} | {det['clipped_total']} | {100*det['clipped_hit']/det['clipped_total']:.1f}% |",
        "",
        "## IoU against hand-labelled ground truth",
        "",
        "20 required unclipped frames, labelled independently from the detector using raw-image",
        "inspection, the `cv2.selectROI` helper, and the spot-checked Issue #5 capture measurements --",
        "`docs/data/poster_region_labels.json`. Extra clipped stress cases are kept in a separate",
        "file and reported separately below so the required labelled set is unambiguous.",
        "",
        f"| Set | n | Mean IoU | >= 0.5 |",
        f"|---|---:|---:|---:|",
        f"| Required unclipped labelled set | {len(required_iou)} | {sum(required_iou)/len(required_iou):.3f} | {sum(1 for s in required_iou if s>=0.5)}/{len(required_iou)} |",
        "",
        "| Frame | GT | Predicted | IoU |",
        "|---|---|---|---:|",
    ]
    for r in sorted(iou_rows, key=lambda r: -r["iou"]):
        lines.append(f"| `{Path(r['frame']).name}` | {r['gt']} | {r['pred']} | {r['iou']:.2f} |")
    below_05 = [r for r in iou_rows if r["iou"] < 0.5]
    lines.append("")
    if below_05:
        lines.append(
            f"**{len(below_05)} of {len(required_iou)} required frames score below 0.5**, not"
            " hidden in the mean above:"
        )
        for r in below_05:
            lines.append(f"- `{Path(r['frame']).name}`: {r['iou']:.2f}")
    else:
        lines.append(
            f"**All {len(required_iou)}/{len(required_iou)} required unclipped frames clear"
            " IoU >= 0.5** -- see `docs/find_poster_region_notes.md` section 4 for how the frames that"
            " originally failed (all landing on the same degenerate fallback box) were fixed."
        )
    lines.append("")
    if clipped_rows:
        lines += [
            "## Additional Clipped Stress Cases",
            "",
            "These 5 hand-labelled clipped frames are kept outside the required IoU set because Issue #7's",
            "detection-rate criterion is explicitly scoped to visible, unclipped posters. They are useful",
            "diagnostics, but not the acceptance set.",
            "",
            f"| Set | n | Mean IoU | >= 0.5 |",
            f"|---|---:|---:|---:|",
            f"| Clipped stress cases | {len(clipped_iou)} | {sum(clipped_iou)/len(clipped_iou):.3f} | {sum(1 for s in clipped_iou if s>=0.5)}/{len(clipped_iou)} |",
            "",
            "| Frame | GT | Predicted | IoU |",
            "|---|---|---|---:|",
        ]
        for r in sorted(clipped_rows, key=lambda r: -r["iou"]):
            lines.append(f"| `{Path(r['frame']).name}` | {r['gt']} | {r['pred']} | {r['iou']:.2f} |")
        lines.append("")
    lines += [
        "## No-poster negative frames",
        "",
        f"{len(neg_rows)} real frames from a full rotation sweep (no route planning -- just rotate in place through",
        "20 deg steps from a start pose and photograph each heading; see the temporary capture block",
        "in `group_project_controller.py`'s `main()`, removed after this data was gathered).",
        f"**{neg_none}/{len(neg_rows)} correctly returned `None`** (required: >=10).",
        f"Of the {len(neg_rows)-neg_none} that did return a box, `rot05_100deg.png` and",
        "`rot06_120deg.png` genuinely have a station's poster visible at a distance/oblique angle",
        "during the sweep (true positives, not misses) and `rot14_280deg.png` is a confirmed false",
        "positive on an empty sky/water gradient -- a known, accepted trade-off (see",
        "`docs/find_poster_region_notes.md` section 4): fixing it required a stricter solidity",
        "cutoff that cost a real unclipped detection and an IoU pass, on a criterion that already",
        "has large headroom (>=10 required,",
        "15+ available either way).",
        "",
        "| Frame | Predicted |",
        "|---|---|",
    ]
    for r in neg_rows:
        lines.append(f"| `{Path(r['frame']).name}` | {r['pred']} |")
    lines += [
        "",
        "## Figure strip",
        "",
        "Raw frame / detection mask / chosen box, for a spread of cases (near-perfect match, a",
        "clipped frame, and a no-poster negative):",
        "",
        f"![poster region figure strip](data/{STRIP_PATH.name})",
        "",
        "## Compliance",
        "",
        "Uses only HSV thresholding, contours and bounding boxes on the camera frame plus the exact",
        "geometry in `protos/TexturedBarrier.proto` (a supplied project resource). No Webots Camera",
        "Recognition node, no simulator ground-truth object identity, no reading of `.wbt` files or",
        "texture filenames.",
        "",
    ]
    DOC_PATH.write_text("\n".join(lines))


def main() -> int:
    frames = load_evaluated_frames()
    print(f"Loaded {len(frames)} real frames ({sum(f['unclipped'] for f in frames)} unclipped)")
    det = evaluate_detection_rate(frames)
    print(f"Detection: unclipped {det['unclipped_hit']}/{det['unclipped_total']}, "
          f"clipped {det['clipped_hit']}/{det['clipped_total']}")

    iou_rows = evaluate_iou()
    required = [r["iou"] for r in iou_rows]
    print(f"IoU: required mean {sum(required)/len(required):.3f}, "
          f"{sum(1 for s in required if s>=0.5)}/{len(required)} >= 0.5")

    clipped_rows = evaluate_clipped_stress()
    if clipped_rows:
        clipped = [r["iou"] for r in clipped_rows]
        print(f"Clipped stress: mean {sum(clipped)/len(clipped):.3f}, "
              f"{sum(1 for s in clipped if s>=0.5)}/{len(clipped)} >= 0.5")

    neg_rows = evaluate_negatives()
    neg_none = sum(1 for r in neg_rows if r["pred"] is None)
    print(f"Negatives: {neg_none}/{len(neg_rows)} correctly None")

    examples = [
        (next(r["frame"] for r in iou_rows if r["iou"] > 0.9), next(r["pred"] for r in iou_rows if r["iou"] > 0.9)),
        (next(r["frame"] for r in clipped_rows if r["pred"]), next(r["pred"] for r in clipped_rows if r["pred"])),
        (neg_rows[0]["frame"], neg_rows[0]["pred"]),
    ]
    save_strip(examples)

    write_doc(det, iou_rows, clipped_rows, neg_rows)
    print(f"Wrote {DOC_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
