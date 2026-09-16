# Contribution Log

Running table of who did what. Grows into the report's contribution table (rubric: missing
evidence of teamwork and individual contributions is a -3 deduction).

| Date | Member | Issue | What they did |
|---|---|---|---|
| 2026-09-16 | Nora | #9 | Evaluated the finished target identifier against the saved station captures and all 20 distractor textures; caught that confidence-only rejection still allowed 4 distractors, then added/documented the same-reference reject check that brought distractor false-accepts to 0/20 while preserving 7/8 best captured station accuracy |
| 2026-09-16 | Nora | #8 | Started the target-identification implementation: carried forward the Issue #6 ResNet-18 choice into `identify(crop)`, added confidence/margin rejection with `NO_MATCH`, and generated the first Issue #8 evidence table (84/84 valid returns, 7/8 best-crop target accuracy, 18/18 no-poster crops rejected) |
| 2026-09-16 | Nora | #7 | Reviewed the "closed" Issue #7 and correctly rejected it: caught that the IoU criterion was realistically failing on a strict reading (not just a mean-based caveat), a dangling reference to a notes file that didn't exist, and a labelling-tool resume bug that silently discarded prior work -- pointed at the 3 specific unclipped failures as the real problem to fix rather than accept. That review directed the fix that took unclipped IoU from 12/15 to 15/15 (100%) passing |
| 2026-09-16 | Nora | #7 | Drove the negative-frame rotation sweep in Webots (18 real frames, no poster aimed at); hand-labelled the ground-truth poster box on 20 real frames independently (a `cv2.selectROI` tool, not generated) for the IoU test, which caught a real bug (a degenerate candidate winning by size across many unrelated frames) that visual inspection alone had missed; reviewed and confirmed each subsequent fix against real numbers |
| 2026-09-15 | Nora | #6 | Drove the 3-world evaluation-capture sweep in Webots (84 frames across all 8 stations, planned by an A* multi-station route); reviewed and corrected the ORB-vs-ResNet-18 comparison as real bugs surfaced (a crop-detector failure that was silently corrupting results, an inaccurate claim about the cause, a "trade-off" framing that didn't match the actual numbers); chose ResNet-18 (71.1% vs ORB's 53.9% top-1, and faster) |
| 2026-09-15 | Nora | #5 | Drove the capture sweeps for stations S1 and S3 in Webots (0.295-1.30 m standoffs, +/-15 deg offsets), measured poster bounding boxes vs distance, confirmed the poster does not fit the frame at the real 0.295 m observe distance, and recommended a 0.80-1.30 m identification standoff band, cross-checked between both stations |
| 2026-09-15 | Kithmini | #10 | Verified grid metadata, full world-grid conversion checks, free start/observe cells, and generated the grid overlay/report |
| 2026-09-14 | Nora | #4 | Logged proximity readings for wall/barrier/station obstacle classes, plotted reading vs. distance, chose and justified `WARN`/`STOP` from the data (closed with one criterion — the 0.06 m warning margin — found physically unreachable and documented as such) |
| 2026-09-14 | Nora | #3 | Implemented the motion primitives (`drive_forward`, `turn_left`, `turn_right`, `rotate_in_place`, `stop`) and pose utilities (`normalise_angle`, `distance_to`, `bearing_to`, `pose_to_cell`); measured and recorded the motion baseline |
| 2026-09-14 | Nora | #1 | Scaffolded `README.md`, `CONTRIBUTING.md`, this log |
| 2026-09-14 | Nora | #2 | Verified worlds A/B/C run cleanly, recorded device baseline |
