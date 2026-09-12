---
title: "[Docs] Maintain the AI-usage and external-resource register"
labels: [stream:integration, type:docs, priority:P1]
milestone: "M0 - Setup"
stream: integration
depends_on: ["[Sys] Set up the repo, Python environment and working agreement"]
estimate: "S"
---

## Why
The Week 8 workshop closes on academic integrity and responsible AI use as a design principle of the project, and warns specifically against "please generate the whole project code" — "all the members in the team will suffer from a mistake made by every member." The brief also requires acknowledgement of external resources. Both are far cheaper to satisfy as a running record than as a reconstruction in the final week.

## Rubric link
Overall writing quality and report presentation (4 marks); Missing evidence of teamwork and individual contributions (-3 deduction); Q&A and individual understanding (8 marks).

## Scope
- Create `docs/external_resources.md` with two tables.
  - **AI tool usage**: date, member, tool, what it was asked for, what was accepted, and what the member verified or changed before accepting it.
  - **External resources**: pretrained weights, code snippets, tutorials, library versions, and the supplied course material — each with its source and licence where applicable.
- Adopt the team rule the workshop implies: AI-generated code is never merged unattended. The owning member must be able to explain every line in the presentation Q&A, because the examiners ask individuals about their own components.
- Record which pretrained model (if any) issue 06 selects, where it comes from, and how a marker obtains it — the weights themselves must not be in the submitted ZIP.
- Fold this register into the report's acknowledgement section at issue 25.

## Acceptance criteria
- [ ] `docs/external_resources.md` exists from M0 and is updated in the same pull request as any work that used an external resource or AI assistance.
- [ ] Every pretrained model, third-party snippet and non-standard library used in the final controller appears in the table with its source.
- [ ] No row records generated code that its owning member cannot explain; spot-checked during the Q&A rehearsal in issue 24.
- [ ] The report's acknowledgement section is generated from this file, not written from memory.

## Evidence for the report
`docs/external_resources.md` becomes the acknowledgement section and backs the contribution table.

## Course reference
Week 8 workshop, "Academic integrity and responsible AI usage"; group project brief section 10.

## Out of scope
Choosing the identification method — that is issue 06. This issue records what that choice depends on.
