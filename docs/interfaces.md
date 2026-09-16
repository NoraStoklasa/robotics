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

- **Input:**
- **Output:**
- **Assumptions:**
- **Failure behaviour:**

### Station search / visit ordering

- **Input:**
- **Output:**
- **Assumptions:**
- **Failure behaviour:**

### Global planning (A*)

- **Input:**
- **Output:**
- **Assumptions:**
- **Failure behaviour:**

### Waypoint following

- **Input:**
- **Output:**
- **Assumptions:**
- **Failure behaviour:**

### Safety override

- **Input:**
- **Output:**
- **Assumptions:**
- **Failure behaviour:**

### Mission state machine

- **Input:**
- **Output:**
- **Assumptions:**
- **Failure behaviour:**

### Telemetry

- **Input:**
- **Output:**
- **Assumptions:**
- **Failure behaviour:**
