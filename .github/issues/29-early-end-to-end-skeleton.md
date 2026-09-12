---
title: "[Sys] Run the first end-to-end mission skeleton with stubbed components"
labels: [stream:integration, type:feature, priority:P0]
milestone: "M2 - Target identification"
stream: integration
depends_on: ["[Nav] Implement motion primitives and pose utilities", "[Nav] Load the occupancy grid and verify world-grid conversion", "[Sys] Draw the system architecture and agree the component contracts"]
estimate: "M"
---

## Why
The Week 8 workshop names late integration as the main way group projects fail: "imagine three students working independently for two weeks, everything looks good, and then you try to connect those components and the robot doesn't work — now you have three possible sources of failure with very limited time." The fix it prescribes is an early integration that is deliberately simple: "your first integrated system does not need to be perfect. In fact, it is better to be simple. Get something just running and then improve it."

This issue exists so that integration happens at M2, not at M4. Issue 16 then replaces the stubs with the real components against an interface that is already proven.

## Rubric link
Technical approach, implementation and system integration (9 marks); Live code/system demonstration (10 marks).

## Scope
- Build the smallest controller that runs the whole mission loop end to end, using the contracts agreed in issue 26 and **stubs** in place of unfinished work:
  - perception stub: returns a fixed or randomly chosen station ID with a fixed confidence, through the real vision→navigation signature.
  - planning stub: a straight-line or hand-listed waypoint sequence is acceptable if A* is not ready.
  - control: the real `set_speed` and pose helpers from issue 03 — this layer is not stubbed.
- The loop must actually drive: start → pick a station → navigate towards it → "identify" → go to the observe position → stop.
- Print the state on every transition and the value crossing each interface, so a wrong hand-off is visible in the console.
- Agree and record the **date of this first end-to-end run** in the team agreement, as the workshop instructs.
- Keep the stubs in the repo behind a flag so any component can be stubbed again later to isolate a failure — this is the diagnostic tool for "where did the first incorrect decision occur?"

## Acceptance criteria
- [ ] The skeleton runs from at least one supplied start to a full stop at some station's observe position, without a human touching anything after Run.
- [ ] Every interface from `docs/interfaces.md` is exercised at least once and its value printed.
- [ ] Replacing the perception stub with a different fixed station ID changes which station the robot stops at, with no other code change — proving the interface, not the stub, drives the behaviour.
- [ ] The run completes inside the 4:00 simulation-time limit, or the overrun is logged in `docs/failure_log.md` with a diagnosis.
- [ ] Any contract in `docs/interfaces.md` that this run proved wrong is corrected there, and issue 26's document is updated.
- [ ] Each stub can be re-enabled by a single flag, documented in the README.

## Evidence for the report
The date and log of the first end-to-end run, plus the interface corrections it forced, are concrete evidence of an iterative build-test-integrate cycle in the integration chapter.

## Course reference
Week 8 workshop, "Integrate your components early" and the build → test → integrate → improve cycle; Workshop 8 Part 5, combining behaviours into one controller.

## Out of scope
The real state machine, real matcher and real planner — issues 16, 08 and 12 respectively. This issue deliberately ships something worse than those, earlier.
