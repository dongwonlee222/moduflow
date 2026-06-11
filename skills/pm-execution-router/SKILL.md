---
name: pm-execution-router
description: Use when a user gives product, roadmap, issue, spec, execution, PR, release, or stakeholder-update work and ModuFlow should choose the next product command or workflow step.
---

# PM Execution Router

Route requests through the smallest useful ModuFlow step.

## Routing

- Raw idea, feedback, bug, or loose note: `/product:inbox` (`inbox`, `인박스`)
- Existing project adoption or different folder structure: `/product:migrate` (`migrate`, `마이그레이션`)
- Project owner, environment, link, or integration metadata: `/product:profile` (`profile`, `프로필`)
- Benchmarks, reports, decisions, research, data notes, or references: `/product:knowledge` (`knowledge`, `지식`)
- Evidence review for an issue/spec/roadmap item: `/product:evidence` (`evidence`, `근거`)
- Multi-project overview, central dashboard, or weekly cross-project status: `/product:portfolio` (`portfolio`, `포트폴리오`)
- Team ownership, review state, approval, or handoff: `/product:handoff` (`handoff`, `인수인계`)
- Blockers, risks, or release concerns: `/product:risks` (`risks`, `리스크`)
- Problem shaping: `/product:opportunity` (`opportunity`, `기회`)
- Durable work item: `/product:issue` (`issue`, `이슈`)
- PRD/spec: `/product:spec` (`spec`, `스펙`)
- Metrics or evidence: `/product:analyze` (`analyze`, `분석`)
- UX or prototype: `/product:design` then `/product:prototype` (`design`, `prototype`, `디자인`, `프로토타입`)
- Priority/timing: `/product:roadmap` (`roadmap`, `로드맵`)
- Implementation preparation: `/product:plan` (`plan`, `계획`)
- Worker assignment: `/product:workers` (`workers`, `워커`)
- Build work: `/product:execute` (`execute`, `실행`)
- Progress question: `/product:status` (`status`, `상태`)
- Setup validation: `/product:doctor` (`doctor`, `검사`)
- Quality gate: `/product:review` (`review`, `리뷰`)
- Pull request: `/product:pr` (`pr`, `피알`)
- Deploy/release: `/product:release` (`release`, `릴리즈`)
- Stakeholder communication: `/product:update` (`update`, `공유`)

When running inside Codex, accept bare aliases after `@ModuFlow` and resolve them to the matching `product:*` command. Always end with the next recommended command.
