# External Resources and AI-Usage Register

Per [Issue #28](.github/issues/28-ai-usage-and-external-resources.md). Every pretrained model,
third-party snippet, non-standard library, and use of AI assistance in the final controller and
supporting tools appears here with its source. The report's acknowledgement section should be
generated from this file, not written from memory.

**Status note (2026-09-15):** this file was created late -- during Issue #6, which needed it for
its own compliance section -- rather than from M0 as the issue asks. Issues #3, #4, #5, #10 were
already closed with substantial AI assistance before this file existed; that work is recorded in
`docs/change_log.md` (which has been kept from day one) but not yet broken out into individual
rows here. Backfilling that is still needed before submission -- see the AI-assistance row below.

## Pretrained models

| Date | Resource | Source | Used in | Why permitted |
|---|---|---|---|---|
| 2026-09-15 | ResNet-18, ImageNet-pretrained weights | `torchvision.models.ResNet18_Weights.IMAGENET1K_V1` (torchvision, BSD-3) | Issue #6, Option B backbone (frozen; only a new linear head is trained) | Week 4 workshop explicitly covers a pretrained ResNet-18 with a frozen backbone and a retrained head |

## Third-party libraries (beyond the supplied starter environment)

| Date | Library | Source | Used in | Notes |
|---|---|---|---|---|
| 2026-09-14 | OpenCV (`cv2`) | opencv-python | All controller/tools code from Issue #2 onward | Supplied by the project's `camera_bgr()` helper and Workshop 8's own use of OpenCV; standard course toolkit, not an external addition |
| 2026-09-15 | PyTorch / torchvision | pytorch.org | Issue #6, Option B | Pre-installed in the project's conda environment; standard toolkit for Week 4's transfer-learning content |

## Supplied project resources used as permitted

| Date | Resource | Used in | Why permitted |
|---|---|---|---|
| 2026-09-15 | `textures/target_*.png` (the 8 reference images) | Issue #6, as ORB matching templates and ResNet-18 training data | Issue #6 explicitly permits this: "the eight reference images in `textures/` are a supplied project resource and may be used as templates or training data" |

## AI assistance

| Date | Tool | Used in | What it did | Reviewed by |
|---|---|---|---|---|
| 2026-09-14 to 2026-09-15 | Claude Code (Anthropic) | Issues #3, #4, #5, #6, #10, plus various doc/process fixes | Substantial assistance across all of these: test/calibration scripts, the grid-conversion checker, the poster-visibility capture sweep and bbox heuristic, the A* multi-station capture-route planner, the ORB-vs-ResNet-18 comparison pipeline and decision-doc generation, and a number of bug fixes (e.g. `normalise_angle`'s `-pi` edge case). Every Webots simulation run was driven live and watched by Nora, not run unattended; generated code and generated findings were reviewed (and in several cases re-tested against real captured data, or corrected) before being kept -- see `docs/change_log.md` for the complete chronological record of every individual change, which predates and is more granular than this register | Nora |

**Still to do:** break the AI-assistance row above out into one row per issue (matching
`docs/change_log.md`'s entries), so each can be spot-checked in the Issue #24 Q&A rehearsal without
needing to cross-reference the change log.
