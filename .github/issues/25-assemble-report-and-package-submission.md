---
title: "[Docs] Assemble the report, contribution table and submission package"
labels: [stream:integration, type:docs, priority:P0]
milestone: "M5 - Evaluation and deliverables"
stream: integration
depends_on: ["[Docs] Write the vision chapters of the report", "[Docs] Write the navigation and integration chapters", "[Sys] Document failure cases and robustness fixes"]
estimate: "L"
---

## Why
Two of the rubric lines are pure deductions for format and missing teamwork evidence — both are avoidable, and both are lost at the last minute.

## Rubric link
Overall writing quality and report presentation (4 marks); Missing evidence of teamwork and individual contributions (-3); Poor format deduction (-2).

## Scope
- Merge the stream chapters into one report with a consistent voice, numbering and figure style, covering: problem and project idea, design rationale, technical approach, implementation and integration, experimental evaluation, discussion, limitations and improvements.
- Build the contribution table from `docs/contribution_log.md`: each member, their responsibilities, and how the work was integrated.
- Export the report as PDF or DOCX for **separate** upload; it must not go inside the ZIP.
- Build the code ZIP: the project package with the group's controller, excluding `runs/`, `__pycache__/`, `.DS_Store`, model weights and large temporary files. If a pretrained model is required, document how to obtain it rather than shipping the weights.
- Build the acknowledgement section from `docs/external_resources.md` (issue 28), covering every pretrained model, third-party snippet, library and AI-assisted contribution, as the brief's academic-integrity section and the Week 8 workshop's responsible-AI-use principle require.
- Verify the supplied folder structure is unchanged and that any added files are documented in the README.
- Run the reproducibility check: clone fresh into a new directory, follow the README, and run one mission end to end.

## Acceptance criteria
- [ ] `grep -rnE '/Users/|/home/|C:\\\\' ` over all committed Python returns no absolute path.
- [ ] A fresh clone into a new directory runs one complete mission successfully with no file edits beyond `config/assessment_mission.json`.
- [ ] The ZIP contains no `runs/`, `__pycache__/`, `.DS_Store` or model-weight files, verified by listing its contents.
- [ ] The report is exported as a separate PDF or DOCX and is not present inside the ZIP.
- [ ] The contribution table names all three members with distinct responsibilities and is backed by the commit history.
- [ ] The report includes limitations and possible improvements, and acknowledges all external code, models and libraries.
- [ ] The acknowledgement section matches `docs/external_resources.md` row for row, with nothing used in the final controller left out.

## Evidence for the report
This issue produces the final submitted artefacts: the report file and the code ZIP.

## Course reference
Workshop 8 submission format — code as a ZIP, results document uploaded separately and not zipped; the same split the group project requires.

## Out of scope
Writing new technical content; this issue assembles, verifies and packages what exists.
