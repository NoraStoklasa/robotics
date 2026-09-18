# Report -> code map

Cross-reference between `3006ICT_Group_Project_Report.pdf` and the controller
source. Every function/block listed here also carries a `# Report Section
X.Y -- ...` comment at the same location in the code, so the two stay in
sync — search the code for `Report Section` to jump straight to a spot, or
use this file to go the other way (report section -> code).

All paths are relative to
`3006ICT_group_project_webots/controllers/group_project_controller/`.

| Report section | What it covers | File | Line | Function / block |
|---|---|---|---|---|
| **2.3** How far away the robot should stand | 0.80-1.30 m standoff band, backoff logic | `group_project_controller.py` | 103 | `IDENTIFY_BACKOFF_DISTANCE` constants |
| **2.3** | | `group_project_controller.py` | 290 | `identify_position_for()` |
| **2.3** | | `vision_utils.py` | 221 | `_expanded_close_crop()` (close-range widening, ties to the standoff band) |
| **2.4** How much clearance to leave around obstacles | Selective inflation, radius 4 (Table 4, Figure 6) | `project_utils.py` | 85 | `inflate_grid()` |
| **2.4** | | `project_utils.py` | 106 | `selective_inflation()` |
| **2.4** | | `project_utils.py` | 127 | `apply_clearance_policy()` |
| **2.4** | | `group_project_controller.py` | 82 | `PLANNING_GRID` / `STATION_OBSERVE_CELLS` setup |
| **2.5** Which order to visit the stations | Nearest-first by A* cost (Table 5) | `project_utils.py` | 259 | `next_station()` |
| **2.5** | | `group_project_controller.py` | 1010 | `Mission._plan()` |
| **2.6** What we deliberately did not build | No visual SLAM (pose from GPS/InertialUnit) | `group_project_controller.py` | 147 | `get_pose()` |
| **3** System architecture and interfaces | Supplied Webots e-puck interface | `group_project_controller.py` | 35 | Webots setup block |
| **3** | | `group_project_controller.py` | 132 | Provided low-level helpers block |
| **3** | | `project_utils.py` | 40 | `station_by_id()` / `start_by_id()` |
| **3.1** The two interfaces we agreed first | `identify(crop) -> (label, confidence)` (Listing 1) | `vision_utils.py` | 566 | `identify()` |
| **3.1** | `follow_path(waypoints, ...)` (Listing 1) | `group_project_controller.py` | 365 | `follow_path()` |
| **3.2** What every component promises | Perception's NO_MATCH contract | `vision_utils.py` | 547 | `no_match_result()` |
| **3.2** | Telemetry component contract | `telemetry.py` | 1, 30, 60, 73 | module docstring, `TelemetryLogger`, `log_step()`, `log_summary()` |
| **3.2** | Telemetry calls from the mission | `group_project_controller.py` | 868 | `Mission._log_telemetry_row()` |
| **3.3** How the system was actually built | Perception stub (16 Sept end-to-end run) | `group_project_controller.py` | 620 | Perception stub block, `stub_identify()` |
| **3.3** | | `group_project_controller.py` | 658 | `identify_at_station()` |
| **3.3** | Main integration loop | `group_project_controller.py` | 1213 | `main()` |
| **4.1** Finding the poster in the frame | Barrier-first detector (Figure 8, Table 7) | `vision_utils.py` | 1, 68, 109, 151, 196, 221, 250, 258 | module docstring through `find_poster_region()` |
| **4.1/4.4** | Multi-candidate retry at identify time | `vision_utils.py` | 630 | `identify_frame()` |
| **4.2** Naming the target | ResNet 18 classifier (Table 2) | `vision_utils.py` | 385 | `_TargetIdentifier` class |
| **4.2** | | `vision_utils.py` | 535 | `_get_identifier()` |
| **4.2/4.3** | Scoring a crop | `vision_utils.py` | 498 | `_TargetIdentifier.score()` |
| **4.3** Knowing when to say nothing | Confidence/margin gates (Listing 2) | `vision_utils.py` | 346 | `MIN_CONFIDENCE`, `MIN_CONFIDENCE_MARGIN` |
| **4.3** | Reference-similarity gate | `vision_utils.py` | 355, 461, 485 | `MIN_REFERENCE_SIMILARITY`, `_reference_features()`, `_reference_similarity()` |
| **4.3** | Three-gate accept/reject decision (Listing 2) | `vision_utils.py` | 568 | `identify()` body |
| **4.3** | 3-of-5 frame consensus rule | `group_project_controller.py` | 697, 1077 | `IDENTIFY_CONSENSUS_FRAMES` constants, `Mission._identify()` |
| **4.4** Following the rules | No Camera Recognition, raw pixels only | `group_project_controller.py` | 156 | `camera_bgr()` |
| **5.1** The map and the grid | World <-> grid conversion | `project_utils.py` | 19, 32 | `world_to_grid()`, `grid_to_world()` |
| **5.1** | | `group_project_controller.py` | 282 | `pose_to_cell()` |
| **5.2** Planning a route | A* heuristic and search | `project_utils.py` | 147, 154 | `heuristic()`, `astar()` |
| **5.2** | Waypoint simplification | `project_utils.py` | 215 | `simplify_path()` |
| **5.2** | Grid path -> world waypoints | `project_utils.py` | 241 | `path_to_waypoints()` |
| **5.2** | Per-mission planning call (+ Section 8.4 cell-patch fix) | `group_project_controller.py` | 327 | `plan_path_to()` |
| **5.3** Following the path | Tuned constants (Table 9) | `group_project_controller.py` | 96 | `KP_HEADING`, `BASE_SPEED`, `WAYPOINT_TOLERANCE` |
| **5.3** | Drive primitives | `group_project_controller.py` | 203 | `drive_forward()` etc. |
| **5.3** | Angle/distance helpers | `group_project_controller.py` | 231 | `normalise_angle()`, `distance_to()`, `bearing_to()` |
| **5.3** | Proportional controller (Listing 3, incl. the left/right sign-bug fix) | `group_project_controller.py` | 368 | `follow_path()` |
| **5.4** The safety layer | WARN/STOP thresholds (Table 10) | `group_project_controller.py` | 67 | `WARN`, `STOP` constants |
| **5.4** | Avoidance/recovery constants | `group_project_controller.py` | 113 | `FRONT_LEFT_PS` block through `STUCK_MIN_DISPLACEMENT` |
| **5.4** | Reading the sensors | `group_project_controller.py` | 167, 177, 187 | `proximity_values()`, `any_sensor_above()`, `largest_reading()` |
| **5.4** | Which way to turn away | `group_project_controller.py` | 399 | `turn_away_direction()` |
| **5.4** | Priority function (Listing 4) | `group_project_controller.py` | 416 | `select_behaviour()` |
| **5.4** | Full reactive layer + stuck detector | `group_project_controller.py` | 430, 527 | `Navigator` class, stuck-detector block |
| **5.5** Choosing the next station | (see 2.5 above — same function) | `project_utils.py` | 259 | `next_station()` |
| **6** Mission state machine | State machine overview (Figure 12) | `group_project_controller.py` | 672, 735 | State-machine comment block, `Mission` class |
| **6** | One control step | `group_project_controller.py` | 981 | `Mission.step()` |
| **6.1** Per-state behaviour (Table 11) | PLAN | `group_project_controller.py` | 1010 | `Mission._plan()` |
| **6.1** | NAVIGATE | `group_project_controller.py` | 1032 | `Mission._navigate()` |
| **6.1** | OBSERVE (+ Section 8.3 heading bug fix) | `group_project_controller.py` | 262, 272, 1047 | `yaw_error_to()`, `rotate_towards_yaw()`, `Mission._observe()` |
| **6.1** | IDENTIFY | `group_project_controller.py` | 1077 | `Mission._identify()` |
| **6.1** | GOTO_OBSERVE | `group_project_controller.py` | 1145 | `Mission._goto_observe()` |
| **6.1** | FINAL_ALIGN | `group_project_controller.py` | 1170 | `Mission._final_align()` |
| **6.1** | FINAL_HOLD, STOP, FAILED | `group_project_controller.py` | 1188 | `Mission._final_hold()` |
| **6.1** | Orange "return to PLAN" arrows | `group_project_controller.py` | 793 | `Mission._skip_current_station()` |
| **6.2** Stopping in the right place | Arrival tolerance / final hold constants | `group_project_controller.py` | 709 | `ARRIVAL_TOLERANCE`, `FINAL_HOLD_STEPS` |
| **6.2** | | `group_project_controller.py` | 1145, 1188 | `Mission._goto_observe()`, `Mission._final_hold()` |
| **6.3** The time budget and degraded mode | Budget/degraded-mode constants | `group_project_controller.py` | 718 | `TIME_BUDGET`, `DEGRADED_MODE_FRACTION` block |
| **6.3** | Budget check | `group_project_controller.py` | 813 | `Mission._check_time_budget()` |
| **6.3** | Degraded mode | `group_project_controller.py` | 832 | `Mission._check_degraded_mode()` |
| **6.3** | Candidate evidence | `group_project_controller.py` | 859 | `Mission._note_candidate()` |
| **6.4** Every constant we tuned | MAX_SPEED | `group_project_controller.py` | 64 | `MAX_SPEED` |
| **6.4** | Consensus-frame constants | `group_project_controller.py` | 697 | `IDENTIFY_CONSENSUS_FRAMES` block |
| **7.1** How we tested | Start-pose labelling for the test matrix | `project_utils.py` | 60 | `nearest_start_id()` |
| **7.2** Mission results | Telemetry summary row / console result block | `group_project_controller.py` | 898 | `Mission._finish()` |
| **7.2** | | `telemetry.py` | 73 | `TelemetryLogger.log_summary()` |
| **7.4** Rejecting distractors | Per-label similarity floor (Table 16, Stages 3-4) | `vision_utils.py` | 362 | `MIN_REFERENCE_SIMILARITY_BY_LABEL` |
| **8.1** Vision: confidently wrong (camera/headphones) | Same per-label floor as 7.4 | `vision_utils.py` | 362 | `MIN_REFERENCE_SIMILARITY_BY_LABEL` |
| **8.2** Vision: right but not allowed to say so (coffee_mug) | Same per-label floor as 7.4 | `vision_utils.py` | 362 | `MIN_REFERENCE_SIMILARITY_BY_LABEL` |
| **8.3** Navigation: right place, facing the wrong way | The OBSERVE heading-alignment fix | `group_project_controller.py` | 262, 1047 | `yaw_error_to()`, `Mission._observe()` |
| **8.4** Two navigation bugs | Stuck detector false trigger (60 -> 200 steps) | `group_project_controller.py` | 113, 527 | `STUCK_WINDOW_STEPS`, stuck-detector block in `Navigator.step()` |
| **8.4** | Planner refusing a safe cell | `group_project_controller.py` | 327 | `plan_path_to()` |
| **9.1/9.2** Robustness | State-machine failure-path coverage | `group_project_controller.py` | 672-1211 | Whole `Mission` class |

## Notes

- Sections **1**, **10**, **11**, **12**, **13** (introduction, limitations,
  contributions, acknowledgements, conclusion) are narrative/planning content
  with no single corresponding code block, so they are not listed above.
- Where one function serves two report sections (e.g. `next_station()` for
  both 2.5 and 5.5, or the per-label similarity floor for 7.4/8.1/8.2), it is
  listed once per section so it is findable either way.
- Search the codebase for the literal string `Report Section` to find every
  in-code marker; this file is generated from that same set of comments.
