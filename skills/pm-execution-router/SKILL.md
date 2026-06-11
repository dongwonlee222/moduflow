---
name: pm-execution-router
description: Use when a user gives product, roadmap, issue, spec, execution, PR, release, or stakeholder-update work and ModuFlow should choose the next product command or workflow step.
---

# PM Execution Router

Route requests through the smallest useful ModuFlow step.

## Routing

- Raw idea, feedback, bug, or loose note: `/product:inbox`
- Existing project adoption or different folder structure: `/product:migrate`
- Project owner, environment, link, or integration metadata: `/product:profile`
- Benchmarks, reports, decisions, research, data notes, or references: `/product:knowledge`
- Evidence review for an issue/spec/roadmap item: `/product:evidence`
- Problem shaping: `/product:opportunity`
- Durable work item: `/product:issue`
- PRD/spec: `/product:spec`
- Metrics or evidence: `/product:analyze`
- UX or prototype: `/product:design` then `/product:prototype`
- Priority/timing: `/product:roadmap`
- Implementation preparation: `/product:plan`
- Build work: `/product:execute`
- Progress question: `/product:status`
- Quality gate: `/product:review`
- Pull request: `/product:pr`
- Deploy/release: `/product:release`
- Stakeholder communication: `/product:update`

When running inside Codex, accept `product:*` aliases without the leading slash because leading `/` is reserved for native Codex commands. Always end with the next recommended command.
