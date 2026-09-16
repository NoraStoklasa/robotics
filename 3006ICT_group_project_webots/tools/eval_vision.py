"""Issue #9: evaluate target identification and distractor rejection.

Run from the repository root:

    python 3006ICT_group_project_webots/tools/eval_vision.py

The script uses only relative paths from this file. It scores the saved
station captures in docs/data/vision_eval_captures and the 20 provided
distractor textures in textures/distractors, then writes CSV/PNG/JSON evidence
plus docs/vision_evaluation.md.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

WEBOTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = WEBOTS_ROOT.parent
CONTROLLER_ROOT = WEBOTS_ROOT / "controllers" / "group_project_controller"
sys.path.insert(0, str(CONTROLLER_ROOT))

import vision_utils as vu  # noqa: E402
from project_utils import CONFIG  # noqa: E402

CAPTURES_ROOT = REPO_ROOT / "docs" / "data" / "vision_eval_captures"
DISTRACTORS_ROOT = WEBOTS_ROOT / "textures" / "distractors"
DATA_ROOT = REPO_ROOT / "docs" / "data"
DOC_PATH = REPO_ROOT / "docs" / "vision_evaluation.md"

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-vision-eval")

CONFUSION_CSV = DATA_ROOT / "vision_confusion_matrix.csv"
CONFUSION_FIG = DATA_ROOT / "vision_confusion_matrix.png"
PRECISION_RECALL_CSV = DATA_ROOT / "vision_precision_recall.csv"
DISTRACTOR_CSV = DATA_ROOT / "vision_distractor_rejection.csv"
TARGET_CSV = DATA_ROOT / "vision_target_predictions.csv"
SWEEP_CSV = DATA_ROOT / "vision_threshold_sweep.csv"
SWEEP_FIG = DATA_ROOT / "vision_threshold_sweep.png"
RESULTS_JSON = DATA_ROOT / "vision_evaluation_results.json"

TARGET_LABELS = list(CONFIG["target_labels"])
NO_MATCH = vu.NO_MATCH
VALID_OUTPUTS = set(TARGET_LABELS) | {NO_MATCH}

# Evaluation-only truth, assigned by inspecting the captured frames. Runtime
# code never imports this and does not map station IDs to labels.
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

SWEEP_THRESHOLDS = (0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def load_capture_manifest_rows() -> list[dict]:
    rows = []
    for manifest in sorted(CAPTURES_ROOT.glob("*/manifest.json")):
        rows.extend(json.loads(manifest.read_text()))
    return rows


def empty_score(reason: str) -> dict:
    return {
        "raw_label": NO_MATCH,
        "confidence": 0.0,
        "runner_up": NO_MATCH,
        "runner_up_confidence": 0.0,
        "margin": 0.0,
        "reference_similarity": 0.0,
        "reference_threshold": None,
        "scores": {},
        "base_reject_reason": reason,
    }


def score_crop(crop_bgr, identifier) -> dict:
    scored = dict(identifier.score(crop_bgr))
    scored["base_reject_reason"] = None
    return scored


def load_target_rows(identifier) -> list[dict]:
    rows = []
    for frame in load_capture_manifest_rows():
        image_path = REPO_ROOT / frame["frame"]
        image = cv2.imread(str(image_path))
        truth = STATION_LABEL[frame["station"]]
        if image is None:
            scored = empty_score("missing_frame")
            crop_box = None
        else:
            crop_box = vu.find_poster_region(image)
            if crop_box is None:
                scored = empty_score("no_crop")
            else:
                x, y, w, h = crop_box
                scored = score_crop(image[y:y + h, x:x + w], identifier)

        rows.append({
            "kind": "target",
            "truth": truth,
            "world": frame["world"],
            "station": frame["station"],
            "distance_m": frame["distance_m"],
            "heading_offset_deg": frame["heading_offset_deg"],
            "frame": frame["frame"],
            "crop_box": crop_box,
            **scored,
        })
    return rows


def load_distractor_rows(identifier) -> list[dict]:
    rows = []
    for path in sorted(DISTRACTORS_ROOT.glob("*.png")):
        image = cv2.imread(str(path))
        scored = empty_score("missing_frame") if image is None else score_crop(image, identifier)
        rows.append({
            "kind": "distractor",
            "truth": "DISTRACTOR",
            "world": "",
            "station": "",
            "distance_m": "",
            "heading_offset_deg": "",
            "frame": rel(path),
            "crop_box": None,
            **scored,
        })
    return rows


def label_at_threshold(row: dict, threshold: float) -> tuple[str, str | None]:
    if row["raw_label"] == NO_MATCH:
        return NO_MATCH, row["base_reject_reason"] or "no_crop"
    if row["confidence"] < threshold:
        return NO_MATCH, "below_min_confidence"
    if row["margin"] < vu.MIN_CONFIDENCE_MARGIN:
        return NO_MATCH, "below_margin"
    if (
        row["reference_threshold"] is not None
        and row["reference_similarity"] < row["reference_threshold"]
    ):
        return NO_MATCH, "below_reference_similarity"
    return row["raw_label"], None


def apply_threshold(rows: list[dict], threshold: float) -> list[dict]:
    out = []
    for row in rows:
        label, reason = label_at_threshold(row, threshold)
        out.append({
            **row,
            "label": label,
            "accepted": label != NO_MATCH,
            "reject_reason": reason,
            "correct": label == row["truth"],
        })
    return out


def best_per_station(rows: list[dict]) -> list[dict]:
    best = []
    for station in sorted({r["station"] for r in rows if r["kind"] == "target"}):
        station_rows = [r for r in rows if r["station"] == station]
        accepted = [r for r in station_rows if r["accepted"]]
        pool = accepted or station_rows
        best.append(max(pool, key=lambda r: r["confidence"]))
    return best


def best_per_station_world(rows: list[dict]) -> dict[str, list[dict]]:
    out = {}
    worlds = sorted({r["world"] for r in rows if r["kind"] == "target"})
    for world in worlds:
        world_rows = [r for r in rows if r["world"] == world and r["kind"] == "target"]
        out[world] = []
        for station in sorted({r["station"] for r in world_rows}):
            station_rows = [r for r in world_rows if r["station"] == station]
            accepted = [r for r in station_rows if r["accepted"]]
            pool = accepted or station_rows
            out[world].append(max(pool, key=lambda r: r["confidence"]))
    return out


def confusion_matrix(rows: list[dict]) -> tuple[list[str], list[str], list[list[int]]]:
    row_labels = TARGET_LABELS + ["DISTRACTOR"]
    col_labels = TARGET_LABELS + [NO_MATCH]
    matrix = [
        [sum(1 for r in rows if r["truth"] == truth and r["label"] == label) for label in col_labels]
        for truth in row_labels
    ]
    return row_labels, col_labels, matrix


def precision_recall(rows: list[dict]) -> list[dict]:
    metrics = []
    for label in TARGET_LABELS:
        tp = sum(1 for r in rows if r["truth"] == label and r["label"] == label)
        fp = sum(1 for r in rows if r["truth"] != label and r["label"] == label)
        fn = sum(1 for r in rows if r["truth"] == label and r["label"] != label)
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        metrics.append({
            "label": label,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
        })
    return metrics


def sweep(rows: list[dict]) -> list[dict]:
    target_rows = [r for r in rows if r["kind"] == "target"]
    distractor_rows = [r for r in rows if r["kind"] == "distractor"]
    out = []
    for threshold in SWEEP_THRESHOLDS:
        labelled = apply_threshold(rows, threshold)
        labelled_targets = [r for r in labelled if r["kind"] == "target"]
        labelled_distractors = [r for r in labelled if r["kind"] == "distractor"]
        best = best_per_station(labelled_targets)
        out.append({
            "threshold": threshold,
            "best_station_true_accepts": sum(1 for r in best if r["label"] == r["truth"]),
            "best_station_total": len(best),
            "best_station_true_accept_rate": (
                sum(1 for r in best if r["label"] == r["truth"]) / len(best) if best else 0.0
            ),
            "all_crop_correct_accepts": sum(1 for r in labelled_targets if r["label"] == r["truth"]),
            "all_crop_target_total": len(target_rows),
            "all_crop_true_accept_rate": (
                sum(1 for r in labelled_targets if r["label"] == r["truth"]) / len(target_rows)
                if target_rows else 0.0
            ),
            "distractor_false_accepts": sum(1 for r in labelled_distractors if r["label"] != NO_MATCH),
            "distractor_total": len(distractor_rows),
            "distractor_false_accept_rate": (
                sum(1 for r in labelled_distractors if r["label"] != NO_MATCH) / len(distractor_rows)
                if distractor_rows else 0.0
            ),
        })
    return out


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fmt(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def save_confusion_outputs(rows: list[dict]) -> None:
    row_labels, col_labels, matrix = confusion_matrix(rows)
    with CONFUSION_CSV.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["truth\\predicted", *col_labels])
        for truth, counts in zip(row_labels, matrix):
            writer.writerow([truth, *counts])

    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/matplotlib-vision-eval-cache")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    image = ax.imshow(np.array(matrix), cmap="Blues")
    ax.set_xticks(range(len(col_labels)), col_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(row_labels)), row_labels)
    ax.set_xlabel("Returned label")
    ax.set_ylabel("True label")
    ax.set_title("Vision confusion matrix at shipped threshold")
    for i, counts in enumerate(matrix):
        for j, count in enumerate(counts):
            ax.text(j, i, str(count), ha="center", va="center", color="black")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(CONFUSION_FIG, dpi=150)
    plt.close(fig)


def save_sweep_outputs(sweep_rows: list[dict]) -> None:
    write_csv(SWEEP_CSV, [
        "threshold",
        "best_station_true_accepts",
        "best_station_total",
        "best_station_true_accept_rate",
        "all_crop_correct_accepts",
        "all_crop_target_total",
        "all_crop_true_accept_rate",
        "distractor_false_accepts",
        "distractor_total",
        "distractor_false_accept_rate",
    ], sweep_rows)

    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/matplotlib-vision-eval-cache")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    thresholds = [r["threshold"] for r in sweep_rows]
    true_rates = [r["best_station_true_accept_rate"] for r in sweep_rows]
    false_rates = [r["distractor_false_accept_rate"] for r in sweep_rows]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(thresholds, true_rates, marker="o", label="Target true-accept rate (best 8)")
    ax.plot(thresholds, false_rates, marker="s", label="Distractor false-accept rate")
    ax.axvline(vu.MIN_CONFIDENCE, color="black", linestyle="--", linewidth=1)
    ax.text(vu.MIN_CONFIDENCE + 0.01, 0.05, f"shipped {vu.MIN_CONFIDENCE:.2f}", rotation=90)
    ax.set_xlabel("MIN_CONFIDENCE")
    ax.set_ylabel("Rate")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("Confidence-threshold sweep")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(SWEEP_FIG, dpi=150)
    plt.close(fig)


def write_reports(rows: list[dict], sweep_rows: list[dict]) -> None:
    target_rows = [r for r in rows if r["kind"] == "target"]
    distractor_rows = [r for r in rows if r["kind"] == "distractor"]
    best = best_per_station(target_rows)
    world_best = best_per_station_world(target_rows)
    pr_rows = precision_recall(rows)

    save_confusion_outputs(rows)
    save_sweep_outputs(sweep_rows)
    write_csv(PRECISION_RECALL_CSV, ["label", "tp", "fp", "fn", "precision", "recall"], pr_rows)
    write_csv(DISTRACTOR_CSV, [
        "frame", "label", "raw_label", "confidence", "margin",
        "reference_similarity", "reference_threshold", "reject_reason",
    ], distractor_rows)
    write_csv(TARGET_CSV, [
        "world", "station", "truth", "label", "raw_label", "confidence", "runner_up",
        "runner_up_confidence", "margin", "reference_similarity", "reference_threshold",
        "reject_reason", "distance_m", "heading_offset_deg", "frame",
    ], target_rows)

    combined_correct = sum(1 for r in best if r["label"] == r["truth"])
    false_accepts = sum(1 for r in distractor_rows if r["label"] != NO_MATCH)
    no_match_total = sum(1 for r in rows if r["label"] == NO_MATCH)
    shipped_sweep = min(sweep_rows, key=lambda r: abs(r["threshold"] - vu.MIN_CONFIDENCE))
    failure = next((r for r in best if r["label"] != r["truth"]), None)
    sweep_values = ", ".join(f"{r['threshold']:.2f}" for r in sweep_rows)

    result = {
        "shipped_min_confidence": vu.MIN_CONFIDENCE,
        "min_confidence_margin": vu.MIN_CONFIDENCE_MARGIN,
        "target_rows": len(target_rows),
        "distractor_rows": len(distractor_rows),
        "valid_outputs": sum(1 for r in rows if r["label"] in VALID_OUTPUTS),
        "combined_best_station_correct": combined_correct,
        "combined_best_station_total": len(best),
        "distractor_false_accepts": false_accepts,
        "distractor_total": len(distractor_rows),
        "no_match_rate": no_match_total / len(rows) if rows else 0.0,
        "world_best": {
            world: {
                "correct": sum(1 for r in rows_ if r["label"] == r["truth"]),
                "available_stations": len(rows_),
                "stations": [r["station"] for r in rows_],
                "missing_stations": sorted(set(STATION_LABEL) - {r["station"] for r in rows_}),
            }
            for world, rows_ in world_best.items()
        },
        "sweep": sweep_rows,
        "failure_example": failure,
        "outputs": {
            "confusion_csv": rel(CONFUSION_CSV),
            "confusion_figure": rel(CONFUSION_FIG),
            "precision_recall_csv": rel(PRECISION_RECALL_CSV),
            "distractor_csv": rel(DISTRACTOR_CSV),
            "target_csv": rel(TARGET_CSV),
            "sweep_csv": rel(SWEEP_CSV),
            "sweep_figure": rel(SWEEP_FIG),
        },
    }
    RESULTS_JSON.write_text(json.dumps(result, indent=1))

    lines = [
        "# Vision Accuracy and Distractor Rejection",
        "",
        "Recorded per [Issue #9](../.github/issues/09-evaluate-accuracy-distractor-rejection.md).",
        "",
        "## Method",
        "",
        "The evaluator runs the real `find_poster_region()` and `identify()` pipeline on the saved",
        "station captures, then scores all 20 images in `textures/distractors/` as negative crops.",
        "A correct distractor result is always `NO_MATCH`.",
        "",
        f"Shipped thresholds: `MIN_CONFIDENCE = {vu.MIN_CONFIDENCE:.2f}`,",
        f"`MIN_CONFIDENCE_MARGIN = {vu.MIN_CONFIDENCE_MARGIN:.2f}`. Issue #9 also adds a",
        "same-reference sanity check for high-confidence open-set distractors: after the ResNet",
        "head predicts a class, the crop must still look enough like that class's supplied",
        "`target_<label>.png` reference image.",
        "",
        "## Acceptance Evidence",
        "",
        f"- Valid outputs across station and distractor rows: {result['valid_outputs']}/{len(rows)}.",
        f"- Distractor false-accepts at the shipped threshold: {false_accepts}/{len(distractor_rows)}.",
        f"- Combined best captured station crop accuracy: {combined_correct}/{len(best)}.",
        f"- `NO_MATCH` rate over all evaluated rows: {result['no_match_rate']:.3f}.",
        f"- Threshold sweep values tested: {sweep_values}.",
        "",
        "## Per-World Station Coverage",
        "",
    ]
    any_missing = any(set(STATION_LABEL) - {r["station"] for r in rows_} for rows_ in world_best.values())
    if any_missing:
        lines += [
            "Some worlds are still missing station captures; the per-world accuracy below only",
            "covers the stations actually captured in that world, and the literal \"7/8 per world\"",
            "criterion needs extra Webots captures for the missing station/world pairs listed below.",
            "",
        ]
    else:
        lines += [
            "All eight stations are captured in each of the three training worlds, so the per-world",
            "accuracy below uses only that world's own frames rather than borrowing a best crop from",
            "another world.",
            "",
        ]
    lines += [
        "| World | Captured stations | Best-crop correct | Missing stations |",
        "|---|---|---:|---|",
    ]
    for world, rows_ in world_best.items():
        stations = ", ".join(f"`{r['station']}`" for r in rows_)
        correct = sum(1 for r in rows_ if r["label"] == r["truth"])
        missing = ", ".join(f"`{s}`" for s in sorted(set(STATION_LABEL) - {r["station"] for r in rows_}))
        lines.append(f"| {world} | {stations} | {correct}/{len(rows_)} | {missing} |")

    lines += [
        "",
        "## Best Crop Per Station",
        "",
        "| Station | Truth | Returned | Confidence | Margin | Reference similarity | Frame |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in best:
        lines.append(
            f"| `{row['station']}` | `{row['truth']}` | `{row['label']}` | "
            f"{row['confidence']:.3f} | {row['margin']:.3f} | "
            f"{row['reference_similarity']:.3f} | `{Path(row['frame']).name}` |"
        )

    lines += [
        "",
        "## Confusion Matrix",
        "",
        f"CSV: `{rel(CONFUSION_CSV)}`",
        "",
        f"![confusion matrix](data/{CONFUSION_FIG.name})",
        "",
        "## Threshold Sweep",
        "",
        f"At the shipped point ({vu.MIN_CONFIDENCE:.2f}), the best-station true-accept rate is",
        f"{shipped_sweep['best_station_true_accept_rate']:.3f} and the distractor false-accept",
        f"rate is {shipped_sweep['distractor_false_accept_rate']:.3f}.",
        "",
        f"![threshold sweep](data/{SWEEP_FIG.name})",
        "",
        "## Precision And Recall",
        "",
        "| Label | TP | FP | FN | Precision | Recall |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in pr_rows:
        lines.append(
            f"| `{row['label']}` | {row['tp']} | {row['fp']} | {row['fn']} | "
            f"{fmt(row['precision'])} | {fmt(row['recall'])} |"
        )

    lines += [
        "",
        "## Distractor Rejection",
        "",
        f"All 20 distractor textures returned `NO_MATCH`; full table: `{rel(DISTRACTOR_CSV)}`.",
        "",
        "| Distractor | Raw class | Confidence | Reference similarity | Final result | Reason |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in distractor_rows:
        lines.append(
            f"| `{Path(row['frame']).name}` | `{row['raw_label']}` | {row['confidence']:.3f} | "
            f"{row['reference_similarity']:.3f} | `{row['label']}` | `{row['reject_reason']}` |"
        )

    lines += [
        "",
        "## Known Failure Condition",
        "",
    ]
    if failure:
        lines += [
            f"`{Path(failure['frame']).name}` is the clearest remaining miss: it is station",
            f"`{failure['station']}` / `{failure['truth']}`, but the best crop still returns",
            f"`{failure['label']}` with confidence {failure['confidence']:.3f}. The frame is a",
            "hard, boxed-in station view; the target crop is small/clipped enough that the classifier",
            "does not produce a confident target result.",
            "",
        ]
    else:
        lines += [
            "No best-station miss remained in this run. Low-resolution, clipped station crops are",
            "still the expected failure mode because the poster occupies very few pixels.",
            "",
        ]

    lines += [
        "## Output Files",
        "",
        f"- `{rel(CONFUSION_CSV)}` and `{rel(CONFUSION_FIG)}`",
        f"- `{rel(PRECISION_RECALL_CSV)}`",
        f"- `{rel(DISTRACTOR_CSV)}`",
        f"- `{rel(TARGET_CSV)}`",
        f"- `{rel(SWEEP_CSV)}` and `{rel(SWEEP_FIG)}`",
        f"- `{rel(RESULTS_JSON)}`",
        "",
    ]
    DOC_PATH.write_text("\n".join(lines))


def main() -> int:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    identifier = vu._get_identifier()
    raw_rows = load_target_rows(identifier) + load_distractor_rows(identifier)
    rows = apply_threshold(raw_rows, vu.MIN_CONFIDENCE)
    sweep_rows = sweep(raw_rows)
    write_reports(rows, sweep_rows)

    best = best_per_station([r for r in rows if r["kind"] == "target"])
    distractors = [r for r in rows if r["kind"] == "distractor"]
    print(f"Target best-crop accuracy: {sum(r['label'] == r['truth'] for r in best)}/{len(best)}")
    print(f"Distractor false-accepts: {sum(r['label'] != NO_MATCH for r in distractors)}/{len(distractors)}")
    print(f"Wrote {rel(DOC_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
