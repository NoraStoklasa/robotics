# Prompt for Claude Code — build the GitHub issue backlog for 3006ICT Group Project

> Copy everything below the line into Claude Code, running inside the repo clone of
> `https://github.com/NoraStoklasa/robotics`.

---

You are helping a 3-person university team plan a robotics + computer vision group project. Your job in this session is **planning only**: produce a complete, high-quality GitHub issue backlog. Do not implement any project code.

## 0. Read these first (do not skip, do not guess)

Read these files before writing anything. They are the ground truth for scope:

- `~/Desktop/GRIFFITH/Robotics and computer vision/3006ICT_Group_Project/3006ICT_Group_Project.pdf` — the assessment brief (requirements, rubric, deliverables)
- `~/Desktop/GRIFFITH/Robotics and computer vision/3006ICT_Group_Project/3006ICT_group_project_webots/README.txt`
- `~/Desktop/GRIFFITH/Robotics and computer vision/3006ICT_Group_Project/3006ICT_group_project_webots/controllers/group_project_controller/group_project_controller.py` — the provided starter controller
- `~/Desktop/GRIFFITH/Robotics and computer vision/3006ICT_Group_Project/3006ICT_group_project_webots/controllers/group_project_controller/project_utils.py`
- `~/Desktop/GRIFFITH/Robotics and computer vision/3006ICT_Group_Project/3006ICT_group_project_webots/config/project_config.json`
- `~/Desktop/GRIFFITH/Robotics and computer vision/3006ICT_Group_Project/3006ICT_group_project_webots/maps/occupancy_grid_info.json`
- `~/Desktop/GRIFFITH/Robotics and computer vision/week8/week8_lab/` — Workshop 8 (the closest lab to this project)

If any file is missing, stop and say so rather than inventing its contents.

## 1. The project in one paragraph

A Webots R2025a simulation gives us a Cyberbotics e-puck in a 4 m × 4 m arena with 8 observation stations (4 boundary: S1, S3, S5, S7; 4 interior: S2, S4, S6, S8) and 5 barriers B1–B5 that carry **non-target distractor images**. `config/assessment_mission.json` names one target identity from: `soda_can, coffee_mug, backpack, fire_extinguisher, camera, running_shoe, headphones, wall_clock`. The robot is **not** told which station shows it. One controller must, unchanged across missions and from starts A/B/C: use the RGB camera to work out which station displays the requested target, then drive itself to that station's designated observation position (`observe` in `project_config.json`), stop within **0.20 m**, with **no collisions**, **no manual steering**, inside **4:00 of simulation time**. Marks: Final Report 35 + Oral Presentation 25 = 60.

## 2. What is already provided (never write issues to rebuild these)

From the starter controller and `project_utils.py`:

- `set_speed(left, right)` — clamped wheel velocity command (`MAX_SPEED = 10`)
- `get_pose()` — returns `(x, y, yaw)` from GPS + InertialUnit
- `camera_bgr()` — camera buffer converted BGRA → BGR OpenCV image
- `proximity_values()` — list of `ps0`–`ps7` readings
- `world_to_grid(x, y)` / `grid_to_world(row, col)`, `station_by_id`, `start_by_id`
- `CONFIG` (arena bounds, resolution 0.1 m, starts A/B/C, all 8 stations with `observe` and `observe_yaw`, target labels), `GRID` (40×40 occupancy grid, 0 = free, 1 = obstacle), `MISSION["target"]`

The group's work goes in the `# Group implementation` / `# TO DO` sections. Issues must build **on top of** these helpers.

## 3. HARD CONSTRAINT — the allowed toolbox (this is the most important rule)

The team may only use techniques taught in this course, Weeks 1–8 lectures and workshops. **Every issue you write must be solvable with the list below.** If a task would need anything outside it, redesign the task.

**Allowed — taught in the course:**

| Week | Techniques you may require |
|---|---|
| W1 | OpenCV basics, BGR/HSV conversion, `cv2.inRange` colour thresholding, masks, contours, bounding boxes, centroid/moments, rule-based action from image position |
| W2 | Pinhole camera model, intrinsic matrix K, 3D→pixel projection, back-projection with known depth, image/camera/robot/world coordinate frames |
| W3 | Keypoint detection (`goodFeaturesToTrack`, ORB), descriptor matching, sparse Lucas–Kanade optical flow, track validation, re-detection after loss, failure-case analysis |
| W4 | PyTorch, pretrained ResNet-18, transfer learning (frozen backbone + limited fine-tuning), domain-shift evaluation |
| W5 | Pretrained detectors (Faster R-CNN ResNet-50 FPN, SSDLite320-MobileNetV3), confidence thresholds, detection → robot action, IoU / precision / recall evaluation |
| W6 | Stereo geometry, disparity → metric depth, point clouds, 3D object location (mostly conceptual here — the e-puck has one camera) |
| W7 | ORB correspondences, Essential matrix + RANSAC, relative pose, visual-odometry trajectory, keyframes, loop closure (not required — GPS + IMU are provided; say so in the report) |
| W8 | Webots API (`getDevice`, `enable`, `robot.step`), differential drive via `set_speed`, camera BGRA→BGR, HSV detection + moments centroid, **proportional (P) steering** from normalised horizontal image error, SEARCH rotation when target not visible, `ps0`–`ps7` thresholds tuned by logging real readings, behaviour priority (Safety > Following > Search), **A\* on a 4-connected grid with Manhattan heuristic**, grid cells → waypoints |
| Any | Standard Python: `numpy`, `json`, `math`, `pathlib`, `logging`, `dataclasses`; `matplotlib` for report figures |

**Forbidden — either not taught, or banned by the brief:**

- Webots Camera Recognition node, Supervisor API, any simulator ground-truth object identity
- Reading `.wbt` files, texture filenames/URLs, or instructor files to infer the target's station
- Hard-coded target→station mapping, pre-recorded routes, timed wheel-command sequences
- Training a detector or network from scratch; YOLO, transformers, CLIP, SAM, or any foundation model
- ROS/ROS2, reinforcement learning, EKF/particle filters/full SLAM stacks, RRT/PRM/D\* (A\* only), MPC
- PID beyond the plain P-controller taught in Week 8
- Absolute or machine-specific file paths; changing the supplied folder structure

If a team member later wants something outside the allowed list, the pattern is a separate issue labelled `needs-tutor-approval` — never bake it silently into a task.

## 4. Work streams (3 members)

Tag every issue with exactly one stream:

- **`stream:vision`** — camera handling, target identification, distractor rejection, vision evaluation
- **`stream:navigation`** — occupancy grid, A\*, waypoint following, obstacle avoidance, motion primitives
- **`stream:integration`** — mission state machine, timing/telemetry, test matrix, report, presentation, submission packaging

Balance the workload roughly evenly across the three. Note in the backlog index that the rubric requires **all members to understand the whole system** for Q&A, so each stream owner must also review the other streams' pull requests.

## 5. Issue anatomy (use this template exactly)

Each issue is a markdown file with YAML front-matter:

```markdown
---
title: "[Nav] Implement A* path planning on the 40x40 occupancy grid"
labels: [stream:navigation, type:feature, priority:P0]
milestone: "M3 - Navigation"
stream: navigation
depends_on: ["[Nav] Load occupancy grid and verify world<->grid conversion"]
estimate: "M"
---

## Why
One sentence on what this unlocks for the mission.

## Rubric link
Which rubric line this feeds — e.g. "Technical approach, implementation and system integration (9 marks)".

## Scope
- Bullet list of exactly what to build, in terms of the provided helpers
  (`GRID`, `world_to_grid`, `set_speed`, `get_pose`, `camera_bgr`, `proximity_values`).

## Acceptance criteria
- [ ] Testable statement 1 (must be checkable by running something, not by opinion)
- [ ] Testable statement 2
- [ ] No forbidden technique used (see backlog constraints)

## Evidence for the report
Name the artefact this produces: a figure, a table, a logged run, a screenshot.

## Course reference
Week N workshop, Part N — the specific lab step this technique comes from.

## Out of scope
What deliberately belongs to another issue.
```

Rules for quality:

- **Titles**: `[Vision] / [Nav] / [Sys] / [Docs]` prefix, imperative, under 70 characters.
- **Acceptance criteria**: 3–6 per issue, each objectively checkable ("A\* returns a path of grid cells from start to goal that contains no cell with value 1" — not "A\* works well").
- **Estimates**: `S` (< 2 h), `M` (half a day), `L` (a full day or more). No issue larger than `L`; split it instead.
- **Every issue must name its course reference.** If you cannot point to a week and lab part, the task is out of scope — cut it or reshape it.
- **Every issue must name a report artefact.** The report is 35 of 60 marks, so evidence is produced as work happens, not reconstructed at the end.

## 6. Milestones

Create these, in order:

1. `M0 - Setup` — repo, environment, working agreement
2. `M1 - Sensing and motion baseline` — devices, motion primitives, pose helpers, proximity safety
3. `M2 - Target identification` — the vision problem
4. `M3 - Navigation` — grid, A\*, waypoint following, avoidance
5. `M4 - Mission integration` — state machine, stopping rule, telemetry
6. `M5 - Evaluation and deliverables` — test matrix, failure analysis, report, presentation, submission

## 7. Suggested backlog (validate against the brief, then adapt)

Aim for **18–25 issues total**. Below is a starting map — merge, split or rename as the brief demands, but do not drop a requirement.

**M0** — repo structure with the Webots package committed unchanged; README with Webots R2025a + conda Python setup (per Workshop 8 Part 1); team working agreement covering branch naming, PR review and a running contribution log (feeds the rubric's contribution table).

**M1** — confirm world runs and log devices/timestep/camera resolution; motion primitives on top of `set_speed` (forward, turn, rotate in place, safe stop); pose utilities (yaw normalisation, distance and bearing to a world point, pose → grid cell); proximity safety check with thresholds tuned by logging real `ps0`–`ps7` values.

**M2** — decide the identification approach and record the decision (ORB + descriptor matching against the eight reference PNGs, per Weeks 3 and 7, **or** a ResNet-18 transfer-learning classifier, per Week 4 — one issue to choose and justify); isolate the poster region in the camera frame; implement the matching/classification itself; add a confidence threshold and "no confident match" outcome; prove distractor rejection against the B1–B5 images; build a vision evaluation harness producing an accuracy table over all 8 stations across the three worlds.

**M3** — load the grid and verify `world_to_grid`/`grid_to_world` round-trips; inflate obstacles for the robot's radius; implement A\* (4-connected, Manhattan heuristic); convert the cell path to world waypoints; waypoint-following with P control on heading error; reactive obstacle avoidance holding priority over waypoint following, including recovery back onto the path.

**M4** — station visit ordering that is computed, never hard-coded (e.g. nearest-first by path cost); the mission state machine (PLAN → NAVIGATE → OBSERVE → IDENTIFY → GOTO_OBSERVE / NEXT_STATION → STOP); final stop within 0.20 m of `observe` facing `observe_yaw`, motors halted; telemetry logging of state transitions, decisions and simulation time against the 4:00 budget.

**M5** — full test matrix (3 worlds × several targets: success/failure, completion time, collisions); at least two documented failure cases plus robustness fixes; the final report written against the rubric split (8/9/8/6/4) including the contribution table; the 10-minute presentation plus a rehearsed live demo inside 4:00; submission packaging (report separate from the zip, relative paths only, clean run from a fresh clone).

## 8. Coverage check (do this before creating anything)

Produce `.github/issues/BACKLOG.md` containing:

- an index table: issue number, title, stream, milestone, estimate, dependencies
- a **requirements coverage table**: every bullet in the brief's §6 "Project Task and Requirements" and §9 "Submission and Demonstration Requirements" in the left column, and the issue(s) covering it on the right — no empty cells
- a **rubric coverage table**: each of the 8 rubric lines (5 report criteria, 2 deductions, 3 presentation criteria) mapped to issues
- a short "constraints" section restating the allowed/forbidden toolbox, so the rules live in the repo

If a requirement has no issue, add one. If an issue maps to no requirement, delete it.

## 9. Output — two phases, stop between them

**Phase 1 (do now):**

1. Write each issue to `.github/issues/NN-short-slug.md` using the template above.
2. Write `.github/issues/BACKLOG.md` with the index and both coverage tables.
3. Write `.github/issues/create_issues.sh` — an idempotent script that creates the labels, creates the milestones via `gh api repos/:owner/:repo/milestones`, then creates each issue with `gh issue create --title ... --body-file ... --label ... --milestone ...` in dependency order.
4. Print a summary: issue count, per-stream split, per-milestone split, and any requirement you found hard to cover.
5. **Stop and wait for approval.** Do not run `gh` yet.

**Phase 2 (only after I say go):**

1. Run `create_issues.sh` against `NoraStoklasa/robotics`.
2. Because `depends_on` uses titles, afterwards replace those with real `#N` references using `gh issue edit`.
3. Print the list of created issue URLs.

## 10. Anti-patterns — do not do these

- Vague acceptance criteria ("works reliably", "is robust", "good accuracy")
- Issues that require a technique from outside the Weeks 1–8 toolbox
- Rebuilding provided helpers (`set_speed`, `get_pose`, `camera_bgr`, `world_to_grid`, …)
- Inventing Webots API calls — if unsure, quote the line from the starter controller or Workshop 8 instead
- One giant "implement the controller" issue, or 40 micro-issues that each take ten minutes
- Any task whose result would be a hard-coded target→station mapping or a fixed route
- Writing implementation code in this session — the deliverable is the backlog

Ask me before proceeding if anything in the brief contradicts these instructions.
