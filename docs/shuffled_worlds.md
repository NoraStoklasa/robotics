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

**Re-run in full on 2026-09-17** after the `camera` reference-similarity floor was added
(`docs/decision_log.md`). Method unchanged from the section above: `config/assessment_mission.json` set to
the target under test, the named world launched headlessly, the printed `MISSION:` trace read; no
controller edit between runs, and `assessment_mission.json` was restored to its original value afterwards.
A run passes if it reaches `MISSION: FINAL STOP` at the station that actually carries the target's poster
in that shuffled world, within 0.20 m of that station's `observe` position.

| World | Target | Its station here | Its station in training | Result | Distance to observe | Completion time | Stations inspected | Previous result (pre-2026-09-17) |
|---|---|---|---|---|---|---|---|---|
| A | soda_can | S2 | S1 | **Pass** | 0.099 m | 32.58 s | 2 | Pass (0.068 m) |
| A | running_shoe | S7 | S6 | **Pass** | 0.099 m | 191.52 s | 8 | Pass (0.020 m) |
| B | soda_can | S8 | S1 | **Pass** | 0.098 m | 53.63 s | 2 | Pass (0.010 m) |
| A | camera | S6 | S5 | **Pass** | 0.018 m | 57.28 s | 3 | **Fail** (correct label at 0.76/0.75/0.69, never 3 agreeing frames) |
| B | backpack | S6 | S3 | **Pass** | 0.098 m | 88.35 s | 4 | **Fail** (confidence stuck 0.24-0.35) |
| C | wall_clock | S7 | S8 | **Pass** | 0.099 m | 147.84 s | 7 | **Fail** (confidence flat 0.00 across 12 frames) |
| A | wall_clock | S1 | S8 | **Pass** | 0.097 m | 150.88 s | 7 | **Fail** (confidence 0.24-0.36 even at S1) |
| C | soda_can | S2 | S1 | **Pass** | 0.070 m | 109.06 s | 5 | **Fail** (confidence stuck 0.25-0.26) |

**8 of 8 runs now pass, up from 3 of 8.** Every run finished inside the 240 s budget (worst 191.52 s) and
well inside the 0.20 m tolerance (worst 0.099 m). All three acceptance criteria are still satisfied, and
now by every row rather than three of them: at least three shuffled worlds exist under `test_worlds/` (all
three are full derangements), the official worlds are untouched, and every run used a target whose station
differs from its training-world station.

### What changed between the two sets of runs

Several things changed between the original runs and this re-run, so **the recovery cannot be attributed
to any single fix** — do not claim in the report that the `camera` floor fixed these five:

- The `camera` per-label reference-similarity floor (2026-09-17, `docs/decision_log.md`). This directly
  explains the `test_start_B` / `headphones` case in `docs/failure_log.md`, but only two of the five rows
  above involve a `camera` prediction at all.
- The consensus rule the original rows were written against was **3 consecutive agreeing frames**; the
  current code uses **3 of the last 5** (`IDENTIFY_CONSENSUS_FRAMES` / `IDENTIFY_WINDOW_FRAMES`), which
  tolerates an isolated bad frame. This most likely explains the `camera` @ S6 row, which originally
  failed with the correct label at real confidence purely for want of a consecutive streak.
- The retry-from-observe-pose path is doing visible work. In the `camera` @ S6 run, the backed-off
  identify pose produced 20 frames of `NO_MATCH` at 0.00 confidence (i.e. `find_poster_region` found no
  crop at all), and the retry from the closer observe pose then read `camera` at 0.95/0.95/0.96 and
  confirmed on three frames. The same mechanism plausibly accounts for the two `wall_clock` rows, whose
  original symptom was also flat 0.00 confidence.

A clean attribution would need each fix re-tested in isolation against these eight pairs, which has not
been done.

## What the original failures showed (historical -- all eight now pass; kept as the record of what was investigated at the time)

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
