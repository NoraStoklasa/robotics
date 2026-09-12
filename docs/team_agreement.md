# Team Agreement

Recorded per issue [01](.github/issues/01-repo-environment-working-agreement.md), from the Week 8 day-one team meeting.
Answer every question below as a group and commit this file — do not leave it as a discussion that only happened in chat.

## Ownership

| Area | Primary owner | Backup |
|---|---|---|
| Perception / target identification | | |
| Navigation / planning | | |
| Control, safety and integration | | |

Workshop's suggested split (override with a stated reason if the group organises differently):
A = perception and target identification, B = navigation and planning, C = control, safety and integration.

**Reason for any change from the suggested split:**

## Shared architecture

Where does the architecture live? → `docs/architecture.md` (issue [26](.github/issues/26-architecture-and-component-contracts.md)).
Confirm here once all three members have reviewed and approved it, with the date:

- [ ] Architecture approved by all three members on: ____

## Interfaces between components

Confirm here once settled in `docs/interfaces.md` (issue 26):

- [ ] Vision → navigation signature agreed
- [ ] Navigation → control signature agreed

## How will changes be tested before integration?

(e.g. unit-level test per module before it's wired into the state machine; who reviews; what "tested" means for this project)

## How will decisions and failures be recorded?

Decision log: `docs/decision_log.md`. Failure log: `docs/failure_log.md` (issue [27](.github/issues/27-decision-and-failure-logs.md)).
Rule: no decision counts unless it has a row with a criterion and a measured number behind it.

## When will full end-to-end tests start?

Fixed date for the first end-to-end mission skeleton (issue [29](.github/issues/29-early-end-to-end-skeleton.md)), decided **now**, not negotiated later:

**Date:** ____

## How will disagreements be handled?

Rule from the workshop: never "my method is better" — define what *better* means for this project (identification accuracy, completion time, collision rate, robustness across the three starts), run a small experiment, and log the number that decided it.

## How will every member learn the complete system?

(e.g. weekly walkthroughs, cross-stream PR review requirement, rehearsed Q&A — see issue 24)

Weekly meeting slot: ____
Weekly five questions (answered every week from M0 to M5, logged at the top of `docs/decision_log.md`):
1. What did we complete?
2. What evidence do we have?
3. What failed?
4. What is blocking us?
5. What will we do next?
