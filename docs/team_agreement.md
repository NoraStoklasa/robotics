# Team Agreement

Recorded per issue [01](.github/issues/01-repo-environment-working-agreement.md), from the Week 8 day-one team meeting.

**Team:** Nora Stoklasa, Kithmini (2 members).

## Ownership

No fixed one-person-per-stream split — with a 2-person team, both members work across perception,
navigation and integration together rather than each owning a stream alone.

**Reason for departing from the workshop's suggested 3-way split:** only 2 team members.

## Shared architecture

Where does the architecture live? → `docs/architecture.md` (issue [26](.github/issues/26-architecture-and-component-contracts.md)).
Confirm here once both members have reviewed and approved it, with the date:

- [ ] Architecture approved by both members on: ____

## First end-to-end run

Per issue [29](.github/issues/29-early-end-to-end-skeleton.md) and the Week 8 workshop's "integrate
early" advice.

- **Date:** 2026-09-16
- **What ran:** `run_mission_skeleton()` in `group_project_controller.py` — start at world A, pick a
  station by path cost (Issue #15), navigate with safety override (Issue #14), identify (real vision,
  Issue #8, or the `STUB_PERCEPTION` stub), stop on a match or continue, `FAILED` if all 8 come back
  `NO_MATCH`.
- **Result:** ran clean from start to a full stop with the perception stub, from start to `FAILED`
  with the stub set to never match (all 8 stations visited, 173.8 s elapsed — 66.2 s under the 240 s
  budget), and once with real (non-stubbed) vision end to end (correctly identified `running_shoe`/S6,
  `camera`/S5, `headphones`/S7; missed `soda_can`/S1 — consistent with the 7/8 accuracy already
  recorded in `docs/vision_evaluation.md`, not a new defect).
- **Stub swap proven:** changing only `STUB_MATCH_STATION` from `S8` to `S4` (an environment variable,
  no code change) changed which station the robot stopped at, exactly as required.

## Interfaces between components

Confirm here once settled in `docs/interfaces.md` (issue 26):

- [ ] Vision → navigation signature agreed
- [ ] Navigation → control signature agreed

## How will changes be tested before integration?

(e.g. unit-level test per module before it's wired into the state machine; who reviews; what "tested" means for this project)

## How will decisions and failures be recorded?

Decision log: `docs/decision_log.md`. Failure log: `docs/failure_log.md` (issue [27](.github/issues/27-decision-and-failure-logs.md)).
Rule: no decision counts unless it has a row with a criterion and a measured number behind it.

## How will disagreements be handled?

Rule from the workshop: never "my method is better" — define what *better* means for this project (identification accuracy, completion time, collision rate, robustness across the three starts), run a small experiment, and log the number that decided it.

## How will every member learn the complete system?

(e.g. weekly walkthroughs, cross-stream PR review requirement, rehearsed Q&A — see issue 24)

Weekly five questions (answered every week from M0 to M5, logged at the top of `docs/decision_log.md`):
1. What did we complete?
2. What evidence do we have?
3. What failed?
4. What is blocking us?
5. What will we do next?
