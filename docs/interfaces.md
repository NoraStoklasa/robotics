# Component Interfaces

Per issue [26](.github/issues/26-architecture-and-component-contracts.md). For every module: Input, Output, Assumptions, Failure behaviour.
Code in issues 08, 13 and 16 must match these signatures exactly — if implementation forces a change, update this file in the same pull request.

## The two interfaces the workshop calls out explicitly

### Vision → Navigation

**Signature:** `def identify(crop) -> tuple[str, float]:`

- **Input:** BGR poster crop returned from `find_poster_region(image)`.
- **Output:** `(label, confidence)`, where `label` is one of `CONFIG["target_labels"]` or the exact sentinel `NO_MATCH`.
- **Assumptions:** The crop is non-empty and already centred on a plausible poster region; target class names are read from `CONFIG["target_labels"]`; reference images live at `textures/target_<label>.png`.
- **Failure behaviour:** Return `NO_MATCH` when the classifier is unavailable, the crop is invalid, the best confidence is below `MIN_CONFIDENCE`, the best-vs-runner-up margin is below `MIN_CONFIDENCE_MARGIN`, or the crop does not pass the same-reference sanity check for the predicted label; the mission state machine must treat `NO_MATCH` as "inspect the next station", not as a target.

### Navigation → Control

**Signature:** `def follow_path(waypoints, base_speed=BASE_SPEED, kp=KP_HEADING):` — full simplified
waypoint list, not a single waypoint or a bare heading.

- **Input:** `waypoints`, a list of `(x, y)` world coordinates from `path_to_waypoints(simplify_path(astar(...)))`
  (Issues #11-#13), already excluding the robot's own starting cell.
- **Output:** none returned; it is a generator driving `set_speed()` as a side effect once per
  `next()` call, yielding the `(x, y)` waypoint currently being driven to so a caller can log it.
  Raises `StopIteration` once every waypoint has been reached within `WAYPOINT_TOLERANCE`.
- **Assumptions:** called once per Webots control step (one `next()` per `robot.step(timestep)`);
  `waypoints` is collision-free on `PLANNING_GRID`; the caller does not issue wheel commands directly
  while a `follow_path` generator is active, so `set_speed()`'s single clamp stays authoritative.
- **Failure behaviour:** an empty `waypoints` list makes the generator a no-op that returns
  immediately (no motion, no error) — callers should check for an empty A* result themselves before
  calling `follow_path`, since that means no path was found.

## All other modules

### Perception

**Signature:** `def identify_at_station(current_station_id) -> tuple[str, float]:`

- **Input:** the station ID currently being observed. Internally captures `camera_bgr()`, runs
  `vision_utils.find_poster_region()`, then `vision_utils.identify()` on the resulting crop -- or, if
  `STUB_PERCEPTION` (Issue #29) is set, returns the stub's fixed answer instead, through the same
  `(label, confidence)` shape.
- **Output:** `(label, confidence)`, same contract as `identify()` above.
- **Assumptions:** called only while stationary at (or very near) a station's `observe` position, so
  the camera has a plausible view of that station's poster.
- **Failure behaviour:** `find_poster_region()` returning `None` (no plausible poster region found)
  produces `(NO_MATCH, 0.0)`, the same as a confident-but-wrong classification -- `IDENTIFY` treats
  both identically, since either way this frame gives no usable evidence.

### Station search / visit ordering

**Signature:** `def next_station(current_pose, unvisited, grid) -> dict:`

- **Input:** current `(x, y, ...)` world pose; `unvisited`, the station dicts not yet inspected;
  `grid`, the planning grid (Issue #11 policy).
- **Output:** the station dict reached by the shortest `astar` path from the current cell. Ties break
  by station ID, so repeated calls with the same input are deterministic (Issue #15).
- **Assumptions:** `unvisited` is non-empty; `PLAN` checks this itself and goes to `FAILED` rather
  than calling `next_station` on an empty list.
- **Failure behaviour:** if every remaining station is unreachable from the current cell (`astar`
  returns `[]` for all of them), the function still returns the least-bad candidate rather than
  `None` -- `NAVIGATE`'s own step budget is what catches an actually-unreachable choice and returns
  to `PLAN` with that station marked visited, rather than this function silently guessing.

### Global planning (A*)

**Signature:** `def plan_path_to(x_goal, y_goal) -> tuple[list, list]:` (used directly by `NAVIGATE`
via `Navigator`, which calls the equivalent internal replanning logic)

- **Input:** a goal world coordinate; reads the robot's current pose itself via `pose_to_cell()`.
- **Output:** `(waypoints, raw_path)` -- simplified world waypoints (Issue #13) and the raw A* cell
  path (Issue #12), planned on `PLANNING_GRID` (Issue #11).
- **Assumptions:** the goal cell is on the map; the start cell may be temporarily marked blocked by
  the Issue #11 clearance margin (not a real obstacle), which this function patches around itself.
- **Failure behaviour:** an unreachable goal returns `([], [])`; `Navigator` treats an empty path as
  `SEARCH` (rotate and retry), not a crash.

### Waypoint following

See "Navigation -> Control" above (`follow_path`) -- `Navigator` (Issue #14) wraps it with the same
per-step contract, adding safety override on top rather than replacing it.

### Safety override

**Signature:** `def select_behaviour(left_warn, right_warn, left_stop, right_stop, has_path) -> str:`

- **Input:** boolean WARN/STOP flags per side from `proximity_values()` against the calibrated
  thresholds (Issue #4), and whether a path currently exists.
- **Output:** one of `"STOP"`, `"AVOID"`, `"FOLLOW"`, `"SEARCH"`, in that priority order (Safety >
  Path following > Search, Workshop 8 Part 5).
- **Assumptions:** called once per control step from within `Navigator.step()`; never called directly
  by the mission state machine, which only ever asks `Navigator` "are you done yet?"
  (`Navigator.done()`).
- **Failure behaviour:** if no path exists and none can be planned (`SEARCH`), `Navigator` rotates and
  retries rather than stopping dead or raising; `NAVIGATE`'s step budget is the mission-level backstop
  if `SEARCH` never resolves.

### Mission state machine

**Signature:** `class Mission:` with `step()` (call once per `robot.step(timestep)`) and `done()`.

- **Input:** none per call -- reads `get_pose()`, `proximity_values()` and the camera internally
  through the components it drives (`next_station`, `Navigator`, `identify_at_station`).
- **Output:** none returned; drives `set_speed()` as a side effect (via the components above) and
  exposes `self.state` (one of `PLAN`, `NAVIGATE`, `OBSERVE`, `IDENTIFY`, `GOTO_OBSERVE`,
  `FINAL_ALIGN`, `FINAL_HOLD`, `STOP`, `FAILED`) and `done()` (`True` once `STOP` or `FAILED`).
- **Assumptions:** `MISSION["target"]` is read once at controller start-up (`target`, from
  `group_project_controller.py`'s module scope), never re-read mid-mission.
- **Failure behaviour:** see `docs/architecture.md`'s state table -- every non-terminal state has a
  named response to its component failing or returning nothing. `NAVIGATE` and `IDENTIFY` failures
  shrink `unvisited` and return to `PLAN`, which cannot loop forever since `PLAN` on an empty
  `unvisited` goes to `FAILED`. `GOTO_OBSERVE` and `FINAL_ALIGN` failures (Issue #17: can't close to
  `ARRIVAL_TOLERANCE`, or can't align to `observe_yaw`, within the step budget) go straight to
  `FAILED` instead, since the target is already confirmed by that point and there is no other
  station left to retry.

### Telemetry

**Signature:** `class TelemetryLogger:` (`telemetry.py`) with `log_step(**fields)` (interval row) and
`log_summary(**fields)` (one row per run); `Mission` owns one instance and calls both.

- **Input:** `Mission` passes `sim_time` (from `robot.getTime()`, never wall-clock), `state`, pose,
  current station id, identification label/confidence, `Navigator`'s active behaviour and the max
  proximity reading to `log_step()` every `TELEMETRY_LOG_INTERVAL_STEPS` control steps (not every
  step, per Issue #18's "keep logging cheap" scope); it passes start id, target, final station,
  final distance, completion time and outcome to `log_summary()` exactly once, when `Mission.done()`
  first becomes `True`.
- **Output:** one interval CSV per run under `runs/` (gitignored), and one appended row per run in
  the committed `docs/data/mission_summary.csv` -- the source table for the report's completion-time
  figures.
- **Assumptions:** `TELEMETRY_ENABLED` (env var, default on) gates both files; when off, `log_step()`
  and `log_summary()` are no-ops so the rest of `Mission` doesn't need its own on/off branching.
  Interval rows are written and flushed as they're logged, not buffered, so a run stopped mid-mission
  (e.g. pressing Webots' Stop) still leaves a usable partial interval CSV.
- **Failure behaviour:** `TIME_BUDGET` (240 s, the assessment's 4:00 limit) is checked every step
  from `Mission.step()` regardless of the current state; exceeding it forces `FAILED` with outcome
  `TIMEOUT`. `BUDGET_WARN_FRACTIONS` (50/75/90%) each print one warning, once. Past
  `DEGRADED_MODE_FRACTION` (90%) of the budget, if `PLAN` holds a target sighting confident enough to
  count as a candidate (`DEGRADED_MIN_CONFIDENCE`) but never confirmed by full IDENTIFY consensus, it
  commits straight to that station's `observe` instead of continuing to inspect remaining stations --
  trading a full search for a plausible answer rather than risking `TIMEOUT` with nothing to show.
