---
title: "[Sys] Set up the repo, Python environment and working agreement"
labels: [stream:integration, type:chore, priority:P0]
milestone: "M0 - Setup"
stream: integration
depends_on: []
estimate: "M"
---

## Why
Gives all three members an identical, reproducible starting point and creates the contribution record the rubric asks for.

## Rubric link
Missing evidence of teamwork and individual contributions (-3 deduction); Q&A and individual understanding (8 marks).

## Scope
- Commit `3006ICT_group_project_webots/` to the repo **exactly as supplied**, with `worlds/`, `controllers/`, `config/`, `maps/`, `protos/`, `targets/`, `textures/` and `tools/` unchanged.
- Add `.gitignore` covering `__pycache__/`, `*.pyc`, `.DS_Store`, `*.pth`, `runs/`, `logs/`.
- Write `README.md` recording: Webots R2025a install, the conda environment, the `sys.executable` path procedure, and where to paste it (Webots -> Preferences -> General -> Python command; on macOS Webots -> Preferences). Quote the Workshop 8 Part 1 wording rather than inventing steps.
- Record in the README that the project is run by opening a `worlds/*.wbt` file and pressing Run — the controller is `group_project_controller`, already named in every supplied world.
- Write `CONTRIBUTING.md` with: branch naming (`stream/short-slug`), one pull request per issue, and the rule that **each pull request needs a review from an owner of a different stream** (the rubric examines every member on the whole system).
- Start `docs/contribution_log.md` as a running table: date, member, issue, what they did. This becomes the report's contribution table.
- Hold the **day-one team meeting** the Week 8 workshop prescribes and commit its outcome as `docs/team_agreement.md`:
  - Primary ownership, with the workshop's suggested split as the starting point: member A perception and target identification, member B navigation and planning, member C control, safety and integration. The group may organise differently with a stated reason.
  - A named backup for each area — who helps if the owner is stuck.
  - The explicit rule that **testing and understanding the complete system belongs to everyone**, not to the owner alone; the workshop is emphatic that this is one system, not three assignments stapled together.
  - The agreed **date of the first end-to-end integration run** (issue 29), fixed now rather than negotiated later.
  - A weekly meeting slot using the workshop's five questions: what did we complete, what evidence do we have, what failed, what is blocking us, what will we do next.

## Acceptance criteria
- [ ] `git status` is clean after a fresh clone, and `diff -r` between the committed `3006ICT_group_project_webots/` and the original supplied folder reports no differences.
- [ ] `python tools/check_python_environment.py` runs from a fresh clone and reports the environment as OK.
- [ ] `python -c "import cv2, numpy, matplotlib; print('ok')"` succeeds in the documented conda environment.
- [ ] `README.md` states the exact Webots version (R2025a) and contains no absolute path belonging to a specific team member's machine.
- [ ] `CONTRIBUTING.md` states the cross-stream review rule, and `docs/contribution_log.md` exists with at least one row per member.
- [ ] `docs/team_agreement.md` names a primary owner and a backup for each of perception, navigation and integration, and states a calendar date for the first end-to-end integration run.

## Evidence for the report
`docs/contribution_log.md` (grows into the report's contribution table) and a screenshot of the Webots Python-command preference pane for the setup appendix.

## Course reference
Week 8 workshop, "Group engineering practice" — clear ownership plus shared knowledge, roles agreed on day one, and the first-integration date fixed up front. Workshop 8, Part 1 — configuring the Webots Python command and confirming the controller starts without device-name errors.

## Out of scope
The architecture figure and component contracts (issue 26), the decision and failure logs (issue 27) and the AI-usage register (issue 28) are separate M0 issues that build on this one.
Verifying the three worlds actually load and run — that is `[Sys] Verify all three worlds run and record the device baseline`.
