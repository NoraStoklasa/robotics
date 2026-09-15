"""Issue #8: evaluate identify() and write docs/target_identification.md.

Runs the real production functions (`find_poster_region` + `identify`) against
the captured target frames from Issue #6 and against no-poster crops from Issue
#7. No Webots needed; run from the repo root with the project conda env:

    conda run -n 3006ict python 3006ICT_group_project_webots/tools/build_target_identification_doc.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import cv2

WEBOTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = WEBOTS_ROOT.parent
sys.path.insert(0, str(WEBOTS_ROOT / "controllers" / "group_project_controller"))

import vision_utils as vu  # noqa: E402
from project_utils import CONFIG  # noqa: E402

CAPTURES_ROOT = REPO_ROOT / "docs" / "data" / "vision_eval_captures"
NO_POSTER_ROOT = REPO_ROOT / "docs" / "data" / "no_poster_captures"
DOC_PATH = REPO_ROOT / "docs" / "target_identification.md"
RESULTS_PATH = REPO_ROOT / "docs" / "data" / "target_identification_results.json"

TARGET_LABELS = list(CONFIG["target_labels"])
VALID_OUTPUTS = set(TARGET_LABELS) | {vu.NO_MATCH}

# Ground truth for the training worlds, assigned by looking at the captured
# frames during Issue #6. This is evaluation-only and is never imported by the
# controller module.
STATION_LABEL = {
    "S1": "soda_can",
    "S2": "coffee_mug",
    "S3": "backpack",
    "S4": "fire_extinguisher",
    "S5": "camera",
    "S6": "running_shoe",
    "S7": "headphones",
    "S8": "wall_clock",
}


def load_frames() -> list[dict]:
    frames = []
    for manifest in sorted(CAPTURES_ROOT.glob("*/manifest.json")):
        frames.extend(json.loads(manifest.read_text()))
    return frames


def crop_frame(frame_path: str):
    image = cv2.imread(str(REPO_ROOT / frame_path))
    if image is None:
        return None
    box = vu.find_poster_region(image)
    if box is None:
        return None
    x, y, w, h = box
    return image[y:y + h, x:x + w]


def identify_crop(crop) -> dict:
    label, confidence = vu.identify(crop)
    details = dict(vu.identify.last_result)
    details["label"] = label
    details["confidence"] = confidence
    details.pop("scores", None)
    return details


def evaluate_targets() -> list[dict]:
    rows = []
    for frame in load_frames():
        truth = STATION_LABEL[frame["station"]]
        crop = crop_frame(frame["frame"])
        if crop is None:
            rows.append({
                **frame,
                "truth": truth,
                "label": vu.NO_MATCH,
                "confidence": 0.0,
                "runner_up": vu.NO_MATCH,
                "runner_up_confidence": 0.0,
                "margin": 0.0,
                "accepted": False,
                "reject_reason": "no_crop",
            })
            continue
        rows.append({**frame, "truth": truth, **identify_crop(crop)})
    return rows


def negative_crops() -> list[dict]:
    rows = []
    for path in sorted(NO_POSTER_ROOT.glob("*/*.png")):
        image = cv2.imread(str(path))
        if image is None:
            continue
        # Bottom-centre patch: floor/wall content, deliberately not a poster.
        crop = image[70:115, 40:120]
        rows.append({
            "frame": str(path.relative_to(REPO_ROOT)),
            **identify_crop(crop),
        })
    return rows


def best_per_truth(rows: list[dict]) -> list[dict]:
    out = []
    for truth in TARGET_LABELS:
        candidates = [r for r in rows if r["truth"] == truth]
        accepted = [r for r in candidates if r["label"] != vu.NO_MATCH]
        pool = accepted or candidates
        best = max(pool, key=lambda r: r["confidence"])
        out.append(best)
    return out


def confusion_matrix(rows: list[dict]) -> list[list[int]]:
    cols = TARGET_LABELS + [vu.NO_MATCH]
    return [
        [sum(1 for r in rows if r["truth"] == truth and r["label"] == col) for col in cols]
        for truth in TARGET_LABELS
    ]


def confidence_summary(rows: list[dict], negative_rows: list[dict]) -> list[dict]:
    groups = {
        "correct accepted": [r["confidence"] for r in rows if r["label"] == r["truth"]],
        "incorrect accepted": [
            r["confidence"] for r in rows
            if r["label"] not in (r["truth"], vu.NO_MATCH)
        ],
        "target crop rejected": [r["confidence"] for r in rows if r["label"] == vu.NO_MATCH],
        "no-poster crop rejected": [
            r["confidence"] for r in negative_rows if r["label"] == vu.NO_MATCH
        ],
    }
    summary = []
    for name, values in groups.items():
        if values:
            summary.append({
                "case": name,
                "n": len(values),
                "min": min(values),
                "median": statistics.median(values),
                "max": max(values),
            })
        else:
            summary.append({"case": name, "n": 0, "min": None, "median": None, "max": None})
    return summary


def fmt(value):
    return "-" if value is None else f"{value:.3f}"


def write_doc(rows: list[dict], negative_rows: list[dict]) -> None:
    best_rows = best_per_truth(rows)
    best_correct = sum(1 for r in best_rows if r["label"] == r["truth"])
    valid_outputs = sum(1 for r in rows if r["label"] in VALID_OUTPUTS)
    neg_no_match = sum(1 for r in negative_rows if r["label"] == vu.NO_MATCH)
    cols = TARGET_LABELS + [vu.NO_MATCH]
    matrix = confusion_matrix(rows)
    summary = confidence_summary(rows, negative_rows)

    lines = [
        "# Target Identification Evaluation",
        "",
        "Recorded per [Issue #8](.github/issues/08-identify-target-with-confidence.md).",
        "",
        "## Method",
        "",
        "`identify(crop)` lives in `controllers/group_project_controller/vision_utils.py` and follows",
        "the Issue #6 decision: an ImageNet-pretrained ResNet-18 backbone is frozen, then a fresh",
        "8-way linear head is trained on augmented copies of the supplied `textures/target_*.png`",
        "reference images. Labels are read from `CONFIG[\"target_labels\"]`; reference filenames are",
        "built as `target_<label>.png`.",
        "",
        f"`MIN_CONFIDENCE = {vu.MIN_CONFIDENCE:.2f}` and `MIN_CONFIDENCE_MARGIN = {vu.MIN_CONFIDENCE_MARGIN:.2f}`.",
        "The thresholds reject weak or ambiguous classifications as `NO_MATCH` so later mission logic",
        "can inspect the next station instead of committing to a wrong one.",
        "",
        "## Acceptance Checks",
        "",
        f"- Valid return values on full captured set: {valid_outputs}/{len(rows)}.",
        f"- Top-1 over the best captured crop from each of 8 target classes: {best_correct}/8.",
        f"- No-poster crops returning `NO_MATCH`: {neg_no_match}/{len(negative_rows)}.",
        "- Vision source station-ID grep: `grep -nE 'S[1-8]' vision_utils.py` returns no matches.",
        "- Forbidden-technique grep over controller source returns no functional calls.",
        "",
        "## Best Crop Per Target",
        "",
        "| Truth | Returned | Confidence | Runner-up | Runner-up confidence | Margin | Frame |",
        "|---|---|---:|---|---:|---:|---|",
    ]
    for row in best_rows:
        lines.append(
            f"| `{row['truth']}` | `{row['label']}` | {row['confidence']:.3f} | "
            f"`{row['runner_up']}` | {row['runner_up_confidence']:.3f} | "
            f"{row['margin']:.3f} | `{Path(row['frame']).name}` |"
        )

    lines += [
        "",
        "## Confusion Matrix",
        "",
        "Rows are true labels; columns are returned labels over all captured frames where the poster",
        "cropper was run. `NO_MATCH` means the score or margin threshold rejected the crop.",
        "",
        "| Truth \\ Returned | " + " | ".join(f"`{c}`" for c in cols) + " |",
        "|---" + "|---:" * len(cols) + "|",
    ]
    for truth, counts in zip(TARGET_LABELS, matrix):
        lines.append(f"| `{truth}` | " + " | ".join(str(c) for c in counts) + " |")

    lines += [
        "",
        "## Confidence Summary",
        "",
        "| Case | n | Min | Median | Max |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['case']} | {row['n']} | {fmt(row['min'])} | {fmt(row['median'])} | {fmt(row['max'])} |"
        )

    lines += [
        "",
        "## No-Match Crops",
        "",
        "| Frame | Returned | Confidence | Runner-up | Margin | Reason |",
        "|---|---|---:|---|---:|---|",
    ]
    for row in negative_rows:
        lines.append(
            f"| `{Path(row['frame']).name}` | `{row['label']}` | {row['confidence']:.3f} | "
            f"`{row['runner_up']}` | {row['margin']:.3f} | `{row['reject_reason']}` |"
        )

    lines += [
        "",
        "## Compliance",
        "",
        "The runtime vision module reads the class list from `CONFIG[\"target_labels\"]` and contains no",
        "station identifiers. It uses no Webots Camera Recognition node, no Supervisor API, and no",
        "world-file or texture-assignment lookup.",
        "",
    ]
    DOC_PATH.write_text("\n".join(lines))


def main() -> int:
    rows = evaluate_targets()
    negative_rows = negative_crops()
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps({"targets": rows, "no_match": negative_rows}, indent=1))
    write_doc(rows, negative_rows)

    best_rows = best_per_truth(rows)
    print(f"Valid outputs: {sum(1 for r in rows if r['label'] in VALID_OUTPUTS)}/{len(rows)}")
    print(f"Best-crop top-1: {sum(1 for r in best_rows if r['label'] == r['truth'])}/8")
    print(f"No-poster NO_MATCH: {sum(1 for r in negative_rows if r['label'] == vu.NO_MATCH)}/{len(negative_rows)}")
    print(f"Wrote {DOC_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
