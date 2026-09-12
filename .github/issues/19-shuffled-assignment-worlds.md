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
- [ ] At least three shuffled worlds exist under `test_worlds/`, and at least one is a full derangement.
- [ ] `diff` between `worlds/` and the original supplied package shows no change to the official worlds.
- [ ] For each shuffled world, the controller stops within 0.20 m of the correct `observe` position for at least three different mission targets, with no code change between runs.
- [ ] At least one run uses a target whose station differs from its training-world station, and the robot still succeeds.
- [ ] `docs/shuffled_worlds.md` tabulates every permutation and the observed result.

## Evidence for the report
The shuffled-world results table — the strongest single piece of evidence that identification is genuinely visual and no fixed mapping is relied on.

## Course reference
Week 4 — domain-shift evaluation and the principle that a model must be tested outside the distribution it was developed against.

## Out of scope
Timing and collision statistics across the official worlds — that is `[Sys] Run the full mission test matrix`.
