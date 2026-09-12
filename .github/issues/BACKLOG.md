# 3006ICT Group Project — Issue Backlog

Vision-Guided Autonomous Search and Navigation in Webots. 29 issues across 3 streams and 6 milestones.

**Revised after the Week 8 online lab** (8 September 2026). That session was half Webots tutorial and half engineering-practice
guidance for this project, and four of its themes had no home in the original backlog: a one-page architecture with written
component contracts agreed *before* coding (26), a running decision and failure log kept from day one rather than reconstructed
in the final week (27), a deliberately crude end-to-end integration at M2 instead of first contact at M4 (29), and a standing
AI-usage and external-resource register (28). Fifteen existing issues were amended; the details are in section 7.

**Team rule:** every pull request needs a review from an owner of a *different* stream. The rubric awards 8 marks for
"Q&A and individual understanding" and expects every member to explain the **whole** system, not only their own part.
Cross-stream review is how that understanding gets built as the work happens, rather than the night before.

---

## 1. Index

| # | Title | Stream | Milestone | Est | Depends on |
|---|---|---|---|---|---|
| 01 | [Sys] Set up the repo, Python environment and working agreement | integration | M0 | M | — |
| 26 | [Sys] Draw the system architecture and agree the component contracts | integration | M0 | M | 01 |
| 27 | [Sys] Keep a decision log and a failure log from day one | integration | M0 | S | 01 |
| 28 | [Docs] Maintain the AI-usage and external-resource register | integration | M0 | S | 01 |
| 02 | [Sys] Verify all three worlds run and record the device baseline | integration | M1 | S | 01 |
| 03 | [Nav] Implement motion primitives and pose utilities | navigation | M1 | M | 02 |
| 04 | [Nav] Calibrate ps0-ps7 obstacle thresholds from logged readings | navigation | M1 | M | 03 |
| 05 | [Vision] Measure poster appearance against standoff distance | vision | M2 | M | 03 |
| 06 | [Vision] Choose and record the target-identification approach | vision | M2 | M | 05 |
| 07 | [Vision] Isolate the poster region in the camera frame | vision | M2 | M | 05 |
| 08 | [Vision] Identify the target with confidence and a no-match outcome | vision | M2 | L | 06, 07 |
| 09 | [Vision] Evaluate identification accuracy and distractor rejection | vision | M2 | L | 08 |
| 29 | [Sys] Run the first end-to-end mission skeleton with stubbed components | integration | M2 | M | 03, 10, 26 |
| 10 | [Nav] Load the occupancy grid and verify world-grid conversion | navigation | M3 | S | 03 |
| 11 | [Nav] Choose and validate an obstacle clearance strategy | navigation | M3 | M | 10 |
| 12 | [Nav] Implement A* on the 4-connected occupancy grid | navigation | M3 | M | 11 |
| 13 | [Nav] Follow a waypoint path with P-controlled heading | navigation | M3 | L | 12 |
| 14 | [Nav] Add reactive obstacle avoidance with recovery to the path | navigation | M3 | L | 13, 04 |
| 15 | [Nav] Compute the station visit order from planned path cost | navigation | M4 | M | 12 |
| 16 | [Sys] Implement the mission state machine | integration | M4 | L | 29, 08, 14, 15 |
| 17 | [Sys] Implement the final stop rule at the observation position | integration | M4 | M | 16 |
| 18 | [Sys] Log telemetry and enforce the 4:00 mission time budget | integration | M4 | M | 16 |
| 19 | [Vision] Build shuffled-assignment worlds to prove no fixed mapping | vision | M5 | M | 16 |
| 20 | [Sys] Run the full mission test matrix | integration | M5 | L | 17, 18 |
| 21 | [Sys] Document failure cases and robustness fixes | integration | M5 | M | 20, 09, 27 |
| 22 | [Docs] Write the vision chapters of the report | vision | M5 | L | 09, 19 |
| 23 | [Docs] Write the navigation and integration chapters | navigation | M5 | L | 20 |
| 24 | [Docs] Build the presentation and rehearse the live demo | integration | M5 | M | 20, 19 |
| 25 | [Docs] Assemble the report, contribution table and submission package | integration | M5 | L | 22, 23, 21 |

**Split by stream:** vision 7 (05–09, 19, 22) · navigation 9 (03, 04, 10–15, 23) · integration 13 (01, 02, 16–18, 20, 21, 24–29)

**Split by milestone:** M0 = 4 · M1 = 3 · M2 = 6 · M3 = 5 · M4 = 4 · M5 = 7

**Critical path:** 01 → 26 → 02 → 03 → 10 → 29 → 11 → 12 → 13 → 14 → 16 → 17 → 20 → 23 → 25

Issue 29 now sits on the critical path deliberately. It is cheap and its output is throwaway, but it moves the first integration
failure from M4 to M2, which is the whole point of it.

---

## 2. Requirements coverage — brief §6 "Project Task and Requirements"

| Requirement (brief §6) | Issues |
|---|---|
| System operates autonomously after Run; no manual steering or keyboard control | 16, 20, 24, 29 |
| RGB camera must determine which station shows the target, among distractors | 05, 06, 07, 08, 09 |
| Same controller works from designated starts without mission-specific changes | 02, 16, 20, 25 |
| System stays functional when the target-to-station assignment changes | 08, 19, 20 |
| No contact with arena walls, B1–B5 barriers or station structures | 04, 11, 14, 20 |
| After identification, reach the designated observation position and stop | 13, 17 |
| No hard-coded target→station map, pre-recorded route or timed wheel sequence | 08, 15, 19 |
| No Camera Recognition, ground-truth identity or equivalent | 06, 08, 22, 25 |
| No reading of .wbt, texture URLs/filenames or project metadata to infer the station | 06, 08, 22, 25 |
| Mission success within the 4:00 simulation-time limit | 18, 20, 24 |
| Official world geometry, stations, arrangement and assets unmodified (copies OK) | 19, 25 |
| Reproducible from submitted files, no machine-specific absolute paths | 01, 25 |
| Success criterion: e-puck centre within 0.20 m of `observe`, no collision, stopped | 17, 20 |

## 3. Requirements coverage — brief §9 "Submission and Demonstration Requirements"

| Requirement (brief §9) | Issues |
|---|---|
| Final report as PDF/DOCX, uploaded separately, **not** inside the ZIP | 25 |
| Reproducible code ZIP; no env folders, model weights or large temp files; relative paths | 25 |
| Supplied folder structure kept; any added files included or documented | 01, 25 |
| Demo uses the submitted controller; instructor sets the world and mission target | 24, 25 |
| No edits, manual steering, pausing, restarting or resetting once the run starts | 16, 20, 24 |
| Live demo on an instructor-selected mission, unchanged controller, within 4:00 | 18, 24 |
| All members able to explain the whole project and answer questions on it | 01, 24, 26, 29 |

Report content required by §7 — problem and idea (22, 23) · design rationale (06, 11, 22, 23) · technical approach and
integration (08, 12–16, 23) · evaluation over the three supplied missions with success/failure and completion time (20) ·
meaningful failure cases (21) · contribution statement or table (01, 25) · limitations and improvements (21, 25) ·
acknowledgement of external resources per §10 (06, 22, 25).

## 4. Rubric coverage

| Rubric line | Marks | Issues |
|---|---|---|
| **Report** — Problem understanding, project idea and design rationale | 8 | 05, 06, 11, 22, 23, 26, 27 |
| **Report** — Technical approach, implementation and system integration | 9 | 07, 08, 12, 13, 14, 16, 17, 23, 26, 29 |
| **Report** — Experimental evaluation, results and discussion | 8 | 09, 15, 18, 20, 21, 22, 27 |
| **Report** — Project complexity and robustness | 6 | 04, 09, 11, 14, 19, 21 |
| **Report** — Overall writing quality and report presentation | 4 | 22, 23, 25 |
| **Report** — Missing evidence of teamwork and individual contributions | −3 | 01, 25, 27, 29 |
| **Report** — Poor format deduction | −2 | 25 |
| **Presentation** — Clarity and technical explanation | 7 | 24 |
| **Presentation** — Live code/system demonstration | 10 | 14, 17, 20, 24, 29 |
| **Presentation** — Q&A and individual understanding | 8 | 01, 24, 26, 29 |

Note: the rubric has 10 scored lines in total — 5 report criteria, 2 report deductions and 3 presentation criteria.

---

## 5. Constraints

### Allowed toolbox — Weeks 1–8 only

| Week | Techniques |
|---|---|
| W1 | OpenCV basics, BGR/HSV, `cv2.inRange`, masks, contours, bounding boxes, centroid/moments, rule-based action from image position |
| W2 | Pinhole camera model, intrinsics `K`, 3D→pixel projection, back-projection with known depth, image/camera/robot/world frames |
| W3 | `goodFeaturesToTrack`, ORB, descriptor matching, sparse Lucas–Kanade optical flow, track validation, re-detection, failure analysis |
| W4 | PyTorch, pretrained ResNet-18, transfer learning (frozen backbone + limited fine-tuning), domain-shift evaluation |
| W5 | Pretrained detectors (Faster R-CNN ResNet-50 FPN, SSDLite320-MobileNetV3), confidence thresholds, detection→action, IoU/precision/recall |
| W6 | Stereo geometry, disparity→depth, point clouds, 3D object location — largely conceptual here, the e-puck has one camera |
| W7 | ORB correspondences, essential matrix + RANSAC, relative pose, VO trajectory, keyframes, loop closure — **not required**, GPS + IMU are provided; say so in the report |
| W8 | Webots API, differential drive via `set_speed`, BGRA→BGR, HSV + moments centroid, P steering from normalised image error, SEARCH rotation, ps0–ps7 thresholds tuned from logged readings, priority Safety > Following > Search, A* 4-connected with Manhattan heuristic, cells→waypoints |
| Any | numpy, json, math, pathlib, logging, dataclasses; matplotlib for report figures |

### Forbidden

- Webots Camera Recognition node, Supervisor API, any simulator ground-truth object identity
- Reading `.wbt` files, texture filenames/URLs or instructor files to infer the target's station
- Hard-coded target→station mapping, pre-recorded routes, timed wheel-command sequences
- Training a detector or network from scratch; YOLO, transformers, CLIP, SAM, any foundation model
- ROS/ROS2, reinforcement learning, EKF/particle filters/full SLAM stacks, RRT/PRM/D* (A* only), MPC
- PID beyond the plain P controller taught in Week 8
- Absolute or machine-specific file paths; changing the supplied folder structure

**Legitimate use of the reference images.** The eight images in `textures/target_*.png` are a supplied project resource
and may be used as templates or training data — the brief lists reference target images among the provided materials.
What is forbidden is reading *which texture is attached to which station*. Loading `target_soda_can.png` to learn what a
soda can looks like is fine; parsing `training_start_A.wbt` to discover that `station_S1` carries it is not.

**Anything outside this list** goes in a separate issue labelled `needs-tutor-approval`. Never fold it silently into a task.

### Never rebuild these — already provided

`set_speed(left, right)` · `get_pose()` · `camera_bgr()` · `proximity_values()` · `world_to_grid(x, y)` ·
`grid_to_world(row, col)` · `station_by_id` · `start_by_id` · `CONFIG` · `GRID` · `MISSION["target"]`

Group work goes in the `# Group implementation` / `# TO DO` sections of `group_project_controller.py`.

---

## 6. Three findings that shaped this backlog

Each was verified against the supplied files, and each is baked into a specific issue rather than left to be
discovered late.

**1. One-cell obstacle inflation makes half the stations unreachable.** A breadth-first reachability check over the
4-connected grid shows the raw grid connects all three starts to all eight `observe` cells — but inflating obstacles by
one cell for the robot radius, the standard move, seals every corridor into the interior pocket and makes `S2`, `S4`,
`S6` and `S8` unreachable. The `observe` cells stay free; the corridors close. Selective inflation — inflate by one,
then restore raw values within a Chebyshev radius of 4 cells or more around each `observe` — restores all eight.
Issue **11** makes this a decision with a reachability test attached.

**2. All three training worlds share one target-to-station assignment.** `training_start_A/B/C.wbt` all use
S1 soda_can, S2 coffee_mug, S3 backpack, S4 fire_extinguisher, S5 camera, S6 running_shoe, S7 headphones, S8 wall_clock;
only the start pose differs. A system that quietly learned that mapping would pass every local test and fail in
assessment, where the brief says the assignment may change. Issue **19** builds shuffled copies to close the gap.

**3. The camera is 160×120 and sits low, and the poster sits high.** Each station barrier is 0.50 × 0.06 × 0.28 m with
a 0.22 × 0.22 m poster centred about 0.145 m above the floor; every `observe` position is about 0.295 m from the poster
face with `observe_yaw` pointing straight at it. Whether the whole poster fits in frame at that range depends on the
e-puck's camera height and field of view, which Webots was not available here to confirm. Issue **05** measures it
before any matcher is chosen, because the answer sets the identification standoff.

---

## 7. What the Week 8 online lab changed

The 8 September 2026 online lab (Lei Wang) spent roughly half its time on engineering practice for this project rather than on
Webots mechanics. The technical constraints in section 5 were unaffected — nothing in the session narrowed or widened the
Weeks 1–8 toolbox, and the tutor confirmed in the closing Q&A that the group project method is "fully freedom" within the brief.
What changed is process, and process is directly graded here.

### Four new issues

| # | Issue | The lab's words |
|---|---|---|
| 26 | Architecture figure and component contracts | "This decision should have been made early. Otherwise you will be spending days developing two components that cannot communicate properly." Every module gets input, output, assumptions, failure behaviour. |
| 27 | Decision log and failure log from day one | "Otherwise, when you finish the project and then start drafting the report, you will lose the chance to document those very important insights." |
| 28 | AI-usage and external-resource register | Academic integrity and responsible AI use were named as a design principle; "please generate the whole project code" was named as the bad practice to avoid. |
| 29 | First end-to-end skeleton at M2 | "Your first integrated system does not need to be perfect. In fact, it is better to be simple." Late integration is named as the main failure mode of group projects. |

### Fifteen amended issues

| # | What was added |
|---|---|
| 01 | Day-one team agreement: primary owner plus backup per area, the suggested A/B/C split, the rule that testing and system understanding belong to everyone, the five-question weekly meeting, and a fixed calendar date for the first end-to-end run. |
| 02 | Confirm the GPS and InertialUnit device names (the lab states the project e-puck carries both); list which load-time warnings are safely ignorable; record that supplied worlds, maps and assets are never modified. |
| 03 | One single place where wheel speeds are clamped — the lab's named engineering pattern; `stop()` as a deliberate always-available behaviour. |
| 06 | Justify with evidence why the Part 3 colour threshold is inadequate here; state the accuracy-versus-runtime trade-off with both numbers; log the decision in `docs/decision_log.md`. |
| 08 | Must match the agreed vision→navigation signature; docstring carries the four contract lines. |
| 11 | Clearance policy recorded as a decision-log row with its reachability numbers. |
| 13 | Commands routed through the motion layer's single clamp; matches the agreed navigation→control signature. |
| 16 | Reframed as *replacing the stubs from 29*, not starting from blank; states taken from `docs/architecture.md`; every state needs a defined response to component failure. |
| 20 | Every matrix run under assessment conditions — no menu, keyboard, pause, reset or restart after Run; results broken down by test dimension. |
| 21 | Curates the running failure log rather than collecting failures for the first time; each case must name *where the first incorrect decision occurred*. |
| 22 | No success-only chapter; at least one perception failure written up with diagnosis. |
| 23 | Opens with the architecture figure and contract table; narrates the build-test-integrate cycle with dates; sources rationale from the decision log. |
| 24 | Q&A bank aimed at individuals and at design justification, tied back to Weeks 1–8 material; assessment interaction rules rehearsed until automatic. |
| 25 | Acknowledgement section generated from the external-resource register, row for row. |

### Recorded but not actioned

- **Webots R2025a, conda, and the Python-command preference pane** — already covered by issue 01; the lab added no step that was missing.
- **A\* and the grid walkthrough (Workshop 8 Part 6)** — already issues 10–12. The lab confirmed the project is expected to reuse
  this, which is reassurance rather than new scope.
- **The suggested three-way role split** — folded into issue 01 rather than given its own issue, since the lab presented it as a
  suggestion the group may override with a reason.
