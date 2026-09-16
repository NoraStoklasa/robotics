---
title: "[Vision] Build shuffled-assignment worlds to prove no fixed mapping"
labels: [stream:vision, type:test, priority:P0]
milestone: "M5 - Evaluation and deliverables"
stream: vision
depends_on: ["[Sys] Implement the mission state machine"]
estimate: "M"
---

## Why
**All three supplied training worlds use the same target-to-station assignment**, so a system that quietly learned that mapping would pass every local test and then fail in assessment, where the assignment changes.

## Rubric link
Project complexity and robustness (6 marks); Experimental evaluation, results and discussion (8 marks).

## Scope
Verify the finding first. In `worlds/training_start_A.wbt`, `_B` and `_C`, the `TexturedBarrier` nodes carry an identical mapping in all three files:

`S1` soda_can, `S2` coffee_mug, `S3` backpack, `S4` fire_extinguisher, `S5` camera, `S6` running_shoe, `S7` headphones, `S8` wall_clock.

Station coordinates are identical across the three worlds; only the robot start pose differs. The brief states the assessment assignment may differ, so this uniformity is a testing gap, not a fact to rely on.

Tasks:
- Copy the training worlds into `test_worlds/` and permute the `textureUrl` values across the eight `station_S*` nodes to create at least three distinct assignments. The brief permits copies of the training worlds for development and testing; the official worlds stay untouched.
- Include at least one permutation that is a derangement, leaving no station holding its original target.
- Write `docs/shuffled_worlds.md` recording each permutation and the expected station for each of the eight targets.
- Run the full controller against these worlds and confirm it finds the target at its new station.

## Acceptance criteria
- [x] At least three shuffled worlds exist under `test_worlds/`, and at least one is a full derangement. (All three -- `test_start_A/B/C.wbt` -- are full derangements: cyclic shift, reversal, and adjacent-pair swap respectively; no station keeps its training-world target in any of them.)
- [x] `diff` between `worlds/` and the original supplied package shows no change to the official worlds. (Only the 8 `textureUrl` lines differ per copy; every translation, rotation and station name matches the source training world.)
- [ ] For each shuffled world, the controller stops within 0.20 m of the correct `observe` position for at least three different mission targets, with no code change between runs. **Not fully met** -- 3 of 8 real Webots runs passed (2 in world A, 1 in world B, 0 in world C so far), all well within tolerance (0.010-0.068 m). The 5 failures were traced to `IDENTIFY`'s confidence/consensus threshold at specific target/station/world combinations never exercised before the shuffle existed (e.g. `wall_clock` never classifies confidently even at S1, the best-characterised station in the project; world C's approach into S2 gave `soda_can` only 0.25-0.26 confidence versus a clean pass in A/B) -- not a shuffling bug. See `docs/shuffled_worlds.md` and the 2026-09-16 rows in `docs/failure_log.md`; handed to issue 21 rather than fixed here, since this issue is scoped to building/evaluating the worlds, not to `IDENTIFY`.
- [x] At least one run uses a target whose station differs from its training-world station, and the robot still succeeds. (`soda_can` moved from S1 to S2 in world A, and separately from S1 to S8 in world B; both real runs reached `FINAL STOP` there, 0.068 m and 0.010 m from `observe`.)
- [x] `docs/shuffled_worlds.md` tabulates every permutation and the observed result.

## Evidence for the report
The shuffled-world results table — the strongest single piece of evidence that identification is genuinely visual and no fixed mapping is relied on.

## Course reference
Week 4 — domain-shift evaluation and the principle that a model must be tested outside the distribution it was developed against.

## Out of scope
Timing and collision statistics across the official worlds — that is `[Sys] Run the full mission test matrix`.
