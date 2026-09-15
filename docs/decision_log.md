# Decision Log

Per issue [27](.github/issues/27-decision-and-failure-logs.md). A decision that exists only in a chat message does not count.
Every row must name a **criterion** and a **measured number**, not a preference.

Research-type issues (04, 05, 06, 11) must each append at least one row here as part of their own acceptance criteria.

## Weekly five-question check-in

Log the answers at the top of this section each week, newest first.

### Week of ____

1. What did we complete?
2. What evidence do we have?
3. What failed?
4. What is blocking us?
5. What will we do next?

---

## Decisions

| Date | Decision | Options considered | Criterion used | Evidence / measurement | Decided by |
|---|---|---|---|---|---|
| 2026-09-15 | Chose ResNet-18 (frozen backbone, retrained head) over ORB for target identification (Issue #6) | Option A: ORB keypoints + ratio-test matching; Option B: ImageNet-pretrained ResNet-18, frozen backbone, retrained `Linear(512,8)` head on augmented references | Higher top-1 accuracy on a real held-out test set of captured frames from all 8 stations, AND lower per-frame runtime against the 32 ms control timestep, AND accuracy concentrated in the distance range where identification actually happens (close/mid-range on approach) | 84 real frames captured across all 3 worlds/8 stations (`docs/data/vision_eval_captures/`); 8 excluded for an unreliable crop (see `docs/decision_vision_approach.md`). ResNet-18: 54/76 = 71.1% top-1, 9.1 ms/frame. ORB: 41/76 = 53.9%, 20.5 ms/frame. Not a uniform win: ORB scored better at the single longest distance tested (1.0 m, n=14) -- stated plainly in the record rather than smoothed over | Claude Code, from real captured/scored data — see `docs/decision_vision_approach.md` |
| 2026-09-14 | Set `WARN = 120`, `STOP = 300` for `ps0`-`ps7` (Issue #4) | Workshop's example value (~80); a higher pair tuned to the wall's late, sharp rise; the measured pair below | WARN must sit clearly above the ~65-95 sensor noise floor seen with no obstacle present; STOP must sit below the weakest real contact reading measured (barrier B1's resting contact, 355) so it reliably fires for every obstacle class, not just the strongest | Logged wall, barrier B1 and station S4 approaches to real distance (`docs/data/proximity_*.csv`, plotted in `docs/data/proximity_calibration.png`). All three stay flat (~65-95) until roughly 0.03-0.10 m from contact, then rise sharply. Max reading at contact: wall 1764, station S4 1769, barrier B1 (corner-on) only 355 | Claude Code, from logged Webots data — see `docs/proximity_calibration.md` |
| 2026-09-14 | Confirmed `STOP = 300` still holds after re-testing B1 at 3 approach angles (Issue #4 follow-up) | Re-tune `STOP` down to chase the higher transient spikes seen (up to 1538); or keep 300 | The wedged/settled reading (not the momentary spike on first contact) is the only reliably reproducible signal — `STOP` must sit below the lowest settled value seen across all attempts, not the highest spike | 3 more B1 approaches at x-offsets -0.08/0.0/+0.08 (`docs/data/proximity_barrier_B1_angles.csv`). All 4 B1 attempts now on record: transient peaks 355-1538 (no pattern by offset), settled/wedged readings consistently ~350-382 | Claude Code, from logged Webots data — see `docs/proximity_calibration.md` |
| 2026-09-14 | Revised `STOP` from 300 down to 150, after extending the angle sweep to all 3 obstacle classes (9 approaches total) apparently found a worse case than B1 | Keep 300 (only validated against B1); lower to 150 (validated against the apparent new worst case) | STOP must sit below the weakest near-contact reading found across *every* obstacle class tested, not just the one that happened to be checked first | Wall approach at +0.08 m offset reached only 207 right at contact and was still rising (`docs/data/proximity_wall_angles.csv`). **This evidence turned out to be invalid — see the next row.** | Claude Code, from logged Webots data — see `docs/proximity_calibration.md` |
| 2026-09-14 | **Correction**: the wall's 207 reading was a test bug, not a real sensor property — `STOP = 150` re-justified from corrected data instead | Revert to 300 (original, now also unverified against a full sweep); keep 150 but re-verify with a bug-free method | Same as above, but the offset target must be computed from a fixed reference (the true start / the wall's known coordinate), not recomputed from the robot's current position after each back-off, which drifts | Bug: offset targets recomputed from post-backoff position drifted up to 0.14 m off the true wall (confirmed from logged target coordinates); see `docs/failure_log.md`. Re-ran with `wall_offset_target()` (9 offsets) and `fixed_direction()` (station S4, 7 offsets): wall now spikes >1000 at every offset, no weak case; station S4's weakest verified case reached 226 at contact (crosses 150 with ~0.007 m margin); B1 unaffected by the bug, still ~350-380 | Claude Code, from logged Webots data — see `docs/proximity_calibration.md` |
