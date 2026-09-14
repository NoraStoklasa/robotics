# Change Log

Every AI assistant (Claude, Codex, Copilot, or any other tool) that changes code, docs or config in this
repo appends one row here before ending its turn — see `AGENTS.md` for the rule. Newest entries first.
Keep each entry to one short line of *what* and one of *why*; the diff itself lives in git history.

| Date | Tool | What changed | Why |
|---|---|---|---|
| 2026-09-14 | Claude Code | Updated "Summarise when an issue is finished" format in `AGENTS.md` to include what/how/why, not just what | User wants finished-issue summaries to restate the issue and explain the approach, not just list outcomes |
| 2026-09-14 | Claude Code | Removed the temporary drive/rotate measurement block from `main()`; added `docs/motion_baseline.md` | Issue #3 done — measured numbers captured (0.1 m/s forward, 0.997 rad/s rotation, 0 m lateral drift), `main()` back to idle for the next issue |
| 2026-09-14 | Claude Code | Added motion primitives (`drive_forward`, `turn_left`, `turn_right`, `rotate_in_place`, `stop`), pose utilities (`normalise_angle`, `distance_to`, `bearing_to`, `pose_to_cell`), and a temporary drive/rotate measurement routine in `main()` | Issue #3 — shared motion layer for later navigation issues; measurement routine will produce the numbers for `docs/motion_baseline.md` |
| 2026-09-14 | Claude Code | Updated `docs/team_agreement.md` ownership section for a 2-person team, removed unfilled date/meeting-slot placeholders, filled member names into `docs/contribution_log.md` | Team is Nora + Kithmini, not 3 as the template assumed; no fixed per-stream owner, both work across streams |
| 2026-09-14 | Claude Code | Added "Summarise when an issue is finished" section to `AGENTS.md` | So finished-issue summaries come out in one copy-paste-ready format for the shared team Word doc |
| 2026-09-14 | Claude Code | Added temporary basic-timestep/start-pose prints to `group_project_controller.py`; added `docs/device_baseline.md` | Issue #2 — recorded device baseline across worlds A/B/C, all start poses within tolerance of `CONFIG["starts"]` |
| 2026-09-14 | Claude Code | Added `README.md`, `CONTRIBUTING.md`, `docs/contribution_log.md` | Issue #1 setup — reproducible install steps, PR/review rules and a running contribution record; team-specific parts of `team_agreement.md` (names, ownership, dates) left for the team meeting |
