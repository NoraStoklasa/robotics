---
title: "[Sys] Draw the system architecture and agree the component contracts"
labels: [stream:integration, type:docs, priority:P0]
milestone: "M0 - Setup"
stream: integration
depends_on: ["[Sys] Set up the repo, Python environment and working agreement"]
estimate: "M"
---

## Why
The Week 8 workshop names this the single most important idea of the project: "your components need to communicate — what exactly does the vision system give to navigation? ... This decision should have been made early. Otherwise you will be spending days developing two components that cannot communicate properly." It also names the anti-pattern to avoid: starting by putting every idea into one large Python file, or asking an AI tool to generate the whole project at once.

## Rubric link
Technical approach, implementation and system integration (9 marks); Clarity and technical explanation (7 marks); Q&A and individual understanding (8 marks).

## Scope
- Draw a **one-page architecture figure** before any group code is written: the modules (perception, station search, planning, waypoint following, safety override, mission state machine, telemetry), the data that flows between them, and where each supplied helper sits.
- For **every** module write a four-line component contract — the workshop's exact framing:
  - **Input** — what it receives, in what units and frame.
  - **Output** — what it produces, with the concrete Python type.
  - **Assumptions** — what must be true for it to work (for example: the map uses grid coordinates, pose comes from GPS and IMU, the poster fills at least N pixels).
  - **Failure behaviour** — what it does when it cannot produce a valid answer (for example: navigation returns `None` when no path exists, and the state machine treats that as `NO_MATCH` for that station).
- Settle the two interfaces the workshop calls out explicitly:
  - vision → navigation: is it an image coordinate, a station ID, a confidence, or a candidate location? Pick one and write the signature down.
  - navigation → control: a single waypoint, a desired heading, or a full path? Pick one and write the signature down.
- Record the state list and transitions here as a diagram; issue 16 implements it rather than inventing it.
- Commit as `docs/architecture.md` with the figure, plus `docs/interfaces.md` holding the contract table.
- Every member reviews and approves this document — it is the shared model the presentation Q&A examines.

## Acceptance criteria
- [ ] `docs/architecture.md` contains a one-page figure showing every module and every arrow between them, and no module lacks an arrow in and an arrow out.
- [ ] `docs/interfaces.md` lists input, output, assumptions and failure behaviour for every module in the figure.
- [ ] The vision→navigation and navigation→control signatures are written as concrete Python type annotations, and the code in issues 08, 13 and 16 matches them.
- [ ] The state diagram in `docs/architecture.md` names the same states that `group_project_controller.py` later implements.
- [ ] All three members have approved the document, recorded in `docs/contribution_log.md`.

## Evidence for the report
The architecture figure and the contract table go straight into the report's technical-approach section and the presentation deck.

## Course reference
Week 8 workshop, "Engineering practice for the group project" — define a simple component contract (input, output, assumptions, failure behaviour) and agree the interfaces before development, not after.

## Out of scope
Implementing any module; this issue produces the agreement the implementation issues work against.
