# 3006ICT Group Project — Vision-Guided Navigation

Webots R2025a e-puck controller that identifies a named target among 8 observation stations
using the RGB camera, then navigates to that station's observation position.

## Setup

### 1. Install Webots

Install **Webots R2025a**, the version specified for this course. Launch it once and confirm it
opens before changing anything.

### 2. Conda Python environment

Use the same Conda environment as the earlier labs. From a terminal:

```
conda activate <environment_name>
python -c "import cv2, numpy, matplotlib; print('Python environment OK')"
python -c "import sys; print(sys.executable)"
```

Copy the complete path printed by `sys.executable`.

### 3. Point Webots at that Python

In Webots, set the Python command under **Preferences → General → Python command**
(on macOS: **Webots → Preferences → General → Python command**). Paste the path from step 2 —
if it contains spaces, enclose it in double quotes. Restart Webots afterwards.

Alternatively, run `3006ICT_group_project_webots/tools/check_python_environment.py` in your
Conda environment; it prints the same path and confirms `numpy`/`cv2` import correctly.

If you see a Python/package error in Webots: don't change the code first. Check which Python
executable Webots is using — a controller that works in a terminal but fails in Webots usually
means an environment mismatch, not a code bug.

### 4. Run the project

Open one of `3006ICT_group_project_webots/worlds/training_start_A.wbt`, `training_start_B.wbt`
or `training_start_C.wbt` and press **Run**. The controller is `group_project_controller`,
already named in every supplied world — no extra wiring needed.

Do not continue to implementation work until a baseline world runs cleanly: the first goal is a
known-good Webots setup, not solving navigation.

### Stubbing perception (Issue #29)

To isolate a failure to navigation vs. vision, set an environment variable before launching Webots
to force the identification step to a known answer instead of running the camera pipeline:

```
STUB_PERCEPTION=1 STUB_MATCH_STATION=S4   # claims a match at S4, NO_MATCH everywhere else
```

Leave `STUB_PERCEPTION` unset (or `0`) to use the real vision pipeline (Issue #8). This is a
diagnostic flag, not a permanent mode — the controller runs the real components by default.

### Telemetry and the mission time budget (Issue #18)

Every run writes an interval-sampled CSV under `runs/` (gitignored) and appends one summary row
(start, target, station, final distance, completion time, outcome) to the committed
`docs/data/mission_summary.csv`. Useful environment variables:

```
TELEMETRY_ENABLED=0   # skip both CSVs, e.g. to measure logging overhead against a normal run
TIME_BUDGET=60         # seconds; lower the 4:00 (240 s) budget to test warnings/timeout/degraded mode
```

Past `TIME_BUDGET`, the mission fails with outcome `TIMEOUT`. Past 90% of the budget, if a
target sighting was seen but never confirmed (station skipped after `IDENTIFY_MAX_FRAMES` with no
3-frame consensus), the mission commits straight to that station's `observe` instead of continuing
to inspect the remaining stations.

## Repository layout

- `3006ICT_group_project_webots/` — supplied Webots project (worlds, controller, maps, config,
  protos, targets, textures, tools). Kept exactly as supplied; only the controller code inside
  `controllers/group_project_controller/` is group work.
- `docs/` — architecture, interfaces, decision log, failure log, team agreement, contribution log.
- `.github/issues/` — local source of truth for the project backlog (mirrors GitHub issues in
  `NoraStoklasa/robotics`).

## Rules

- `worlds/`, `maps/`, `protos/`, `targets/` and `textures/` are never modified.
- The target-to-station assignment may differ between worlds — do not hard-code it.
- No Webots Camera Recognition or Supervisor ground-truth object identity for target ID.
- See `.github/issues/BACKLOG.md` §5 for the full allowed-toolbox and forbidden list.
