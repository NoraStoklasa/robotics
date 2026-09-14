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

## Explain in plain English

The team is learning this material, not just shipping it. When you pick up or discuss an issue from
`.github/issues/`, explain in the chat, in simple English, before diving into code:

- **What the issue is asking for**, in a sentence or two — skip the jargon in the issue file itself.
- **What needs to be done**, as a short plain list, not the full acceptance-criteria wording.
- **Why it matters** — what it plugs into, or what breaks without it.

If the issue touches a concept that isn't obvious (e.g. what a moment/centroid is, why A* needs a
heuristic, what proportional control does), explain that concept simply too, in a sentence or two, the
first time it comes up — don't assume it's already understood. Keep this in the chat response, short and
conversational; it is not something that goes into the repo files.

## Summarise when an issue is finished

When an issue is closed (or a meaningful chunk of it is done), write a short summary in the chat, in
this exact format, so any team member can copy-paste it straight into the shared Word doc:

```
**Issue N — Issue title**
- bullet, plain English, what was done and why
- bullet
- (if code was added/changed) a short fenced code block of the key snippet
- bullet noting anything still outstanding, if relevant
```

Keep bullets short and non-technical where possible — this is for the report and for teammates who
didn't write the code, not a commit message. Only include a code snippet if it's genuinely useful to
show (a key function, a config change) — don't paste whole files.
