---
title: "[Sys] Keep a decision log and a failure log from day one"
labels: [stream:integration, type:chore, priority:P0]
milestone: "M0 - Setup"
stream: integration
depends_on: ["[Sys] Set up the repo, Python environment and working agreement"]
estimate: "S"
---

## Why
The Week 8 workshop is blunt about this: "keep a decision log ... this is one of the most valuable engineering habits" and "otherwise, when you finish the project and then start drafting the report, you will lose the chance to document those very important insights." Failures are described as engineering evidence, not embarrassment. Issue 21 writes the failure chapter — it can only do that if the raw material was captured while the work happened.

## Rubric link
Experimental evaluation, results and discussion (8 marks); Project complexity and robustness (6 marks); Missing evidence of teamwork and individual contributions (-3 deduction).

## Scope
- Create `docs/decision_log.md` as a running table: date, decision, options considered, the criterion used, the evidence or measurement that settled it, who decided.
- Create `docs/failure_log.md` as a running table: date, what was tested, what failed, suspected cause, what was changed, what happened afterwards.
- Adopt the workshop's rule for disagreements: never "my method is better" — define what *better* means for this project (identification accuracy, completion time, collision rate, robustness across the three starts), run a small experiment, and log the number that decided it.
- Every research-type issue (04, 05, 06, 11) must append its outcome to `docs/decision_log.md` as part of its own acceptance criteria — a decision that exists only in a chat message does not count.
- Every test run that fails, including during development, gets a row in `docs/failure_log.md` the same day.
- Adopt the workshop's five-question meeting format and record the answers weekly at the top of `docs/decision_log.md`: what did we complete, what evidence do we have, what failed, what is blocking us, what will we do next.

## Acceptance criteria
- [ ] Both files exist and are committed before any implementation issue is closed.
- [ ] By the end of M3 the decision log holds at least one row from each of issues 04, 05, 06 and 11, each naming its deciding criterion and the measured evidence.
- [ ] The failure log holds at least six rows by the end of M4, spanning both vision and navigation.
- [ ] Every row in the decision log names a criterion and a number, not a preference.
- [ ] Weekly meeting notes exist for every week from M0 to M5, each answering all five questions.

## Evidence for the report
`docs/decision_log.md` supplies the design-rationale section; `docs/failure_log.md` is the raw material issue 21 turns into the failure-cases chapter. Both are direct evidence of teamwork.

## Course reference
Week 8 workshop, "Engineering practice for the group project" — decision logs, failure logs, evidence-based resolution of disagreements, and the five-question engineering meeting.

## Out of scope
Writing the report's failure-analysis chapter — that is issue 21, which consumes these logs.
