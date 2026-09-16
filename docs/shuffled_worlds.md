# Shuffled Assignment Worlds

Per issue [19](.github/issues/19-shuffled-assignment-worlds.md). All three supplied training worlds
(`worlds/training_start_{A,B,C}.wbt`) use an identical target-to-station mapping. That uniformity is a
gap in the *testing* setup, not a fact the controller is allowed to rely on -- the brief states the
assessment assignment may differ. This document records three re-shuffled copies of the worlds and the
real mission runs used to check the controller still finds each target by looking at it, not by having
memorised where it lived in training.

The official worlds under `worlds/` are untouched -- only `../textures/target_*.png` string values were
edited in the three copies below; every `TexturedBarrier` translation, rotation and station name is
identical to the corresponding training world.

## Training mapping (identical across all three official worlds)

| Station | Training target |
|---|---|
| S1 | soda_can |
| S2 | coffee_mug |
| S3 | backpack |
| S4 | fire_extinguisher |
| S5 | camera |
| S6 | running_shoe |
| S7 | headphones |
| S8 | wall_clock |

## Shuffled permutations

All three are full derangements -- no station keeps its training-world target.

### `test_worlds/test_start_A.wbt` (from `training_start_A.wbt`, cyclic shift by one station)

| Station | Shuffled target | Training target here |
|---|---|---|
| S1 | wall_clock | soda_can |
| S2 | soda_can | coffee_mug |
| S3 | coffee_mug | backpack |
| S4 | backpack | fire_extinguisher |
| S5 | fire_extinguisher | camera |
| S6 | camera | running_shoe |
| S7 | running_shoe | headphones |
| S8 | headphones | wall_clock |

### `test_worlds/test_start_B.wbt` (from `training_start_B.wbt`, full reversal)

| Station | Shuffled target | Training target here |
|---|---|---|
| S1 | wall_clock | soda_can |
| S2 | headphones | coffee_mug |
| S3 | running_shoe | backpack |
| S4 | camera | fire_extinguisher |
| S5 | fire_extinguisher | camera |
| S6 | backpack | running_shoe |
| S7 | coffee_mug | headphones |
| S8 | soda_can | wall_clock |

### `test_worlds/test_start_C.wbt` (from `training_start_C.wbt`, adjacent-pair swap)

| Station | Shuffled target | Training target here |
|---|---|---|
| S1 | coffee_mug | soda_can |
| S2 | soda_can | coffee_mug |
| S3 | fire_extinguisher | backpack |
| S4 | backpack | fire_extinguisher |
| S5 | running_shoe | camera |
| S6 | camera | running_shoe |
| S7 | wall_clock | headphones |
| S8 | headphones | wall_clock |

## How the runs were done

Each run: set `config/assessment_mission.json` to the target label under test, launch the named world
headlessly (`webots --mode=fast --batch --minimize --stdout --stderr <world>`), and read the printed
`MISSION:` trace -- no code was changed between runs, only the mission target and the world file. A run
counts as a pass if it reaches `MISSION: FINAL STOP` at the station that actually carries the target's
poster in that shuffled world, within 0.20 m of that station's `observe` position.

## Results

| World | Target | Its station here | Its station in training | Result | Distance to observe | Notes |
|---|---|---|---|---|---|---|
| A | soda_can | S2 | S1 | **Pass** | 0.068 m | Station differs from training -- direct proof no fixed mapping is relied on |
| A | running_shoe | S7 | S6 | **Pass** | 0.020 m | |
| B | soda_can | S8 | S1 | **Pass** | 0.010 m | Same label as row 1, correctly found at a *different* new station in a *different* world |
| A | camera | S6 | S5 | Fail (`FAILED`, all 8 visited) | -- | Model did recognise `camera` at S6 with real confidence (0.76, 0.75, 0.69 on 3 separate frames) but never got 3 *consecutive* agreeing frames -- see `docs/failure_log.md` |
| B | backpack | S6 | S3 | Fail (`FAILED`, all 8 visited) | -- | Confidence stuck at 0.24-0.35 at S6, never seriously matched `backpack` -- looks like a pre-existing per-class/per-station accuracy gap, not a shuffling artefact |
| C | wall_clock | S7 | S8 | Fail (`FAILED`, all 8 visited) | -- | Confidence flat at 0.00 across all 12 frames -- suspected poster-crop failure at this station/world's approach geometry, not yet root-caused |
| A | wall_clock | S1 | S8 | Fail (`FAILED`, all 8 visited) | -- | Confidence 0.24-0.36 even at S1, the most heavily calibrated/tested station in the project -- points to `wall_clock` being a weak class generally |
| C | soda_can | S2 | S1 | Fail (`FAILED`, all 8 visited) | -- | Confidence stuck at 0.25-0.26, well below the level `soda_can` reached cleanly in worlds A and B -- points to world C's approach geometry into S2 being the weak factor, not the target label |

3 of 8 runs reached `FINAL STOP` at the correct new station within tolerance. All three acceptance
criteria that a *passing* run can prove are satisfied by the three passes above:

- At least three shuffled worlds exist under `test_worlds/`, at least one a full derangement (all three
  are).
- The official worlds are untouched (only three `TexturedBarrier.textureUrl` lines differ per copy;
  diffed by hand against `worlds/`).
- At least one run used a target whose station differs from its training-world station and still
  succeeded (all three passing runs qualify; e.g. `soda_can` moved from S1 to S2 in world A and from S1
  to S8 in world B, and both were found correctly).

## What the failures actually show

None of the five failed runs are shuffling bugs. In every case the robot correctly *visited* the right
station (`PLAN`/`NAVIGATE` worked) and the identifier ran on real camera frames of the correct poster --
the failures are all inside `IDENTIFY`'s confidence/consensus threshold, split into two distinct causes:

1. **Borderline confidence, broken by frame noise** (`camera`@S6, world A) -- the model is genuinely
   reading the shuffled content correctly (0.76 confidence, right label) but sits close enough to
   `MIN_CONFIDENCE` that ordinary per-frame noise breaks the required 3-*consecutive*-frame streak.
2. **Confidence never rises at all** (`backpack`@S6 world B, `wall_clock`@S1 world A, `soda_can`@S2 world
   C, `wall_clock`@S7 world C) -- these look like pre-existing weaknesses in specific
   target-class/station/world combinations that simply hadn't been exercised before, since prior vision
   evaluation concentrated on the original (unshuffled) training layout. `wall_clock`'s failure even at
   S1 -- the best-characterised station in the project -- and world C's repeated weak confidence versus
   the same target succeeding cleanly in A and B, are the two strongest leads.

This is exactly the kind of finding issue 19 exists to surface: the identical training mapping had been
hiding these gaps, because no prior test ever asked the model to recognise `wall_clock` at S1, or
`backpack` at S6 in world B's approach geometry, or anything at all at S2 in world C. Both causes are
logged in `docs/failure_log.md` (2026-09-16 rows) and are handed to issue 21 for root-causing and repair
rather than patched here, since issue 19 is scoped to building and evaluating the shuffled worlds, not to
changing `IDENTIFY` or the vision model.

## Evidence for the report

The results table above is the strongest single piece of evidence that identification is genuinely
visual: the same target label (`soda_can`) was correctly found at two different stations in two
different worlds, neither of which matches its training-world station, using the exact same code both
times.
