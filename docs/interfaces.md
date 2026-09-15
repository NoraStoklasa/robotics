# Component Interfaces

Per issue [26](.github/issues/26-architecture-and-component-contracts.md). For every module: Input, Output, Assumptions, Failure behaviour.
Code in issues 08, 13 and 16 must match these signatures exactly — if implementation forces a change, update this file in the same pull request.

## The two interfaces the workshop calls out explicitly

### Vision → Navigation

**Signature:** `def identify(crop) -> tuple[str, float]:`

- **Input:** BGR poster crop returned from `find_poster_region(image)`.
- **Output:** `(label, confidence)`, where `label` is one of `CONFIG["target_labels"]` or the exact sentinel `NO_MATCH`.
- **Assumptions:** The crop is non-empty and already centred on a plausible poster region; target class names are read from `CONFIG["target_labels"]`; reference images live at `textures/target_<label>.png`.
- **Failure behaviour:** Return `NO_MATCH` when the classifier is unavailable, the crop is invalid, the best confidence is below `MIN_CONFIDENCE`, or the best-vs-runner-up margin is below `MIN_CONFIDENCE_MARGIN`; the mission state machine must treat `NO_MATCH` as "inspect the next station", not as a target.

### Navigation → Control

**Signature:** fill in — single waypoint? desired heading? full path?

- **Input:**
- **Output:**
- **Assumptions:**
- **Failure behaviour:**

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
