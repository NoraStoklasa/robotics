# Agent Instructions — 3006ICT Group Project

These instructions apply to any AI coding assistant working in this repository — Claude Code, Codex,
GitHub Copilot, or similar. Tool-specific files (`CLAUDE.md`, `.github/copilot-instructions.md`) point
here rather than repeating this content, so keep this the one place these rules live.

## Log every change

After any change to code, docs or config — a new file, an edited controller function, an updated
doc — append one row to `docs/change_log.md` before ending your turn. Each entry is two short lines:
**what** changed and **why**. No pasted diff and no essay; git history already has the detail.

Skip this for read-only exploration or for answering a question with no file edits.

If the change is itself an engineering decision or a failed test run, also write it to the log built
for that (see below) — the change log does not replace those.

## Where things already live

- `docs/decision_log.md` — engineering decisions with a stated criterion and measured evidence (issue 27).
- `docs/failure_log.md` — failed test runs, logged the same day they happen (issue 27).
- `docs/architecture.md`, `docs/interfaces.md` — system design, agreed before implementation (issue 26).
- `docs/team_agreement.md` — ownership split and team working agreement (issue 01).
- `.github/issues/` — local source of truth for the GitHub issue backlog; `BACKLOG.md` there has the
  requirement/rubric coverage tables and the full constraint list.

## Constraints

See `.github/issues/BACKLOG.md` §5 for the complete allowed-toolbox (Weeks 1–8 only) and forbidden list.
In short: no Webots Camera Recognition or Supervisor ground truth, no hard-coded target-to-station
mapping, no absolute or machine-specific file paths, no changes to the supplied assessment world.
