# Contribution Log

Running table of who did what. Grows into the report's contribution table (rubric: missing
evidence of teamwork and individual contributions is a -3 deduction).

| Date | Member | Issue | What they did |
|---|---|---|---|
| 2026-09-15 | Nora | #5 | Drove the capture sweeps for stations S1 and S3 in Webots (0.295-1.30 m standoffs, +/-15 deg offsets), measured poster bounding boxes vs distance, confirmed the poster does not fit the frame at the real 0.295 m observe distance, and recommended a 0.80-1.30 m identification standoff band, cross-checked between both stations |
| 2026-09-15 | Kithmini | #10 | Verified grid metadata, full world-grid conversion checks, free start/observe cells, and generated the grid overlay/report |
| 2026-09-14 | Nora | #4 | Logged proximity readings for wall/barrier/station obstacle classes, plotted reading vs. distance, chose and justified `WARN`/`STOP` from the data (closed with one criterion — the 0.06 m warning margin — found physically unreachable and documented as such) |
| 2026-09-14 | Nora | #3 | Implemented the motion primitives (`drive_forward`, `turn_left`, `turn_right`, `rotate_in_place`, `stop`) and pose utilities (`normalise_angle`, `distance_to`, `bearing_to`, `pose_to_cell`); measured and recorded the motion baseline |
| 2026-09-14 | Nora | #1 | Scaffolded `README.md`, `CONTRIBUTING.md`, this log |
| 2026-09-14 | Nora | #2 | Verified worlds A/B/C run cleanly, recorded device baseline |
