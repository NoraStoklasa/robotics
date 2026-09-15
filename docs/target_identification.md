# Target Identification Evaluation

Recorded per [Issue #8](.github/issues/08-identify-target-with-confidence.md).

## Method

`identify(crop)` lives in `controllers/group_project_controller/vision_utils.py` and follows
the Issue #6 decision: an ImageNet-pretrained ResNet-18 backbone is frozen, then a fresh
8-way linear head is trained on augmented copies of the supplied `textures/target_*.png`
reference images. Labels are read from `CONFIG["target_labels"]`; reference filenames are
built as `target_<label>.png`.

`MIN_CONFIDENCE = 0.50` and `MIN_CONFIDENCE_MARGIN = 0.20`.
The thresholds reject weak or ambiguous classifications as `NO_MATCH` so later mission logic
can inspect the next station instead of committing to a wrong one.

## Acceptance Checks

- Valid return values on full captured set: 84/84.
- Top-1 over the best captured crop from each of 8 target classes: 7/8.
- No-poster crops returning `NO_MATCH`: 18/18.
- Vision source station-ID grep: `grep -nE 'S[1-8]' vision_utils.py` returns no matches.
- Forbidden-technique grep over controller source returns no functional calls.

## Best Crop Per Target

| Truth | Returned | Confidence | Runner-up | Runner-up confidence | Margin | Frame |
|---|---|---:|---|---:|---:|---|
| `soda_can` | `soda_can` | 0.843 | `camera` | 0.044 | 0.800 | `C_S1_d0p800_hp00.png` |
| `coffee_mug` | `coffee_mug` | 0.958 | `headphones` | 0.016 | 0.943 | `A_S2_d0p800_hp10.png` |
| `backpack` | `backpack` | 0.595 | `headphones` | 0.127 | 0.468 | `C_S3_d0p800_hm10.png` |
| `fire_extinguisher` | `NO_MATCH` | 0.257 | `coffee_mug` | 0.196 | 0.061 | `B_S4_d0p420_hm10.png` |
| `camera` | `camera` | 0.932 | `wall_clock` | 0.017 | 0.914 | `B_S5_d0p570_hp00.png` |
| `running_shoe` | `running_shoe` | 0.988 | `camera` | 0.003 | 0.985 | `B_S6_d0p800_hm10.png` |
| `headphones` | `headphones` | 0.506 | `running_shoe` | 0.156 | 0.350 | `A_S7_d0p295_hp00.png` |
| `wall_clock` | `wall_clock` | 0.992 | `fire_extinguisher` | 0.003 | 0.989 | `A_S8_d0p800_hp00.png` |

## Confusion Matrix

Rows are true labels; columns are returned labels over all captured frames where the poster
cropper was run. `NO_MATCH` means the score or margin threshold rejected the crop.

| Truth \ Returned | `soda_can` | `coffee_mug` | `backpack` | `fire_extinguisher` | `camera` | `running_shoe` | `headphones` | `wall_clock` | `NO_MATCH` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `soda_can` | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| `coffee_mug` | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| `backpack` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 10 |
| `fire_extinguisher` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| `camera` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 3 |
| `running_shoe` | 0 | 0 | 0 | 0 | 0 | 5 | 1 | 0 | 6 |
| `headphones` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 8 |
| `wall_clock` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 9 | 2 |

## Confidence Summary

| Case | n | Min | Median | Max |
|---|---:|---:|---:|---:|
| correct accepted | 35 | 0.502 | 0.843 | 0.992 |
| incorrect accepted | 2 | 0.510 | 0.534 | 0.558 |
| target crop rejected | 47 | 0.000 | 0.276 | 0.489 |
| no-poster crop rejected | 18 | 0.174 | 0.275 | 0.486 |

## No-Match Crops

| Frame | Returned | Confidence | Runner-up | Margin | Reason |
|---|---|---:|---|---:|---|
| `rot00_000deg.png` | `NO_MATCH` | 0.311 | `coffee_mug` | 0.119 | `below_min_confidence` |
| `rot01_020deg.png` | `NO_MATCH` | 0.228 | `backpack` | 0.008 | `below_min_confidence` |
| `rot02_040deg.png` | `NO_MATCH` | 0.210 | `backpack` | 0.008 | `below_min_confidence` |
| `rot03_060deg.png` | `NO_MATCH` | 0.336 | `coffee_mug` | 0.186 | `below_min_confidence` |
| `rot04_080deg.png` | `NO_MATCH` | 0.259 | `coffee_mug` | 0.036 | `below_min_confidence` |
| `rot05_100deg.png` | `NO_MATCH` | 0.402 | `coffee_mug` | 0.228 | `below_min_confidence` |
| `rot06_120deg.png` | `NO_MATCH` | 0.337 | `backpack` | 0.084 | `below_min_confidence` |
| `rot07_140deg.png` | `NO_MATCH` | 0.286 | `backpack` | 0.062 | `below_min_confidence` |
| `rot08_160deg.png` | `NO_MATCH` | 0.222 | `coffee_mug` | 0.039 | `below_min_confidence` |
| `rot09_180deg.png` | `NO_MATCH` | 0.260 | `wall_clock` | 0.088 | `below_min_confidence` |
| `rot10_200deg.png` | `NO_MATCH` | 0.312 | `soda_can` | 0.139 | `below_min_confidence` |
| `rot11_220deg.png` | `NO_MATCH` | 0.174 | `backpack` | 0.015 | `below_min_confidence` |
| `rot12_240deg.png` | `NO_MATCH` | 0.262 | `backpack` | 0.029 | `below_min_confidence` |
| `rot13_260deg.png` | `NO_MATCH` | 0.467 | `coffee_mug` | 0.253 | `below_min_confidence` |
| `rot14_280deg.png` | `NO_MATCH` | 0.389 | `coffee_mug` | 0.149 | `below_min_confidence` |
| `rot15_300deg.png` | `NO_MATCH` | 0.264 | `soda_can` | 0.092 | `below_min_confidence` |
| `rot16_320deg.png` | `NO_MATCH` | 0.486 | `running_shoe` | 0.313 | `below_min_confidence` |
| `rot17_340deg.png` | `NO_MATCH` | 0.240 | `backpack` | 0.080 | `below_min_confidence` |

## Compliance

The runtime vision module reads the class list from `CONFIG["target_labels"]` and contains no
station identifiers. It uses no Webots Camera Recognition node, no Supervisor API, and no
world-file or texture-assignment lookup.
