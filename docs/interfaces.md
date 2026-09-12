# Component Interfaces

Per issue [26](.github/issues/26-architecture-and-component-contracts.md). For every module: Input, Output, Assumptions, Failure behaviour.
Code in issues 08, 13 and 16 must match these signatures exactly — if implementation forces a change, update this file in the same pull request.

## The two interfaces the workshop calls out explicitly

### Vision → Navigation

**Signature:** `def identify(crop) -> tuple[...]:` — fill in the real type.

- **Input:**
- **Output:**
- **Assumptions:**
- **Failure behaviour:**

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
