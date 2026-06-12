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
- Current project issue overview: `/product:issues` (`issues`, `이슈목록`, `전체이슈`, `전체 이슈`)
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

## Korean Natural Language Routing

Route common Korean phrases directly:

- "상태 보여줘", "현재 상황", "다음에 뭐 하지?": `/product:status`
- "전체 이슈 보여줘", "이슈 목록", "진행 중인 이슈": `/product:issues`
- "검사해줘", "doctor 돌려줘", "설정 괜찮아?": `/product:doctor`
- "로드맵 보여줘", "우선순위": `/product:roadmap`
- "새 이슈 만들어줘", "이거 이슈로 등록": `/product:issue` after existing-issue check
- "<issue id> 시작해줘": issue lifecycle start
- "<issue id> 진행 내용 추가", "<issue id> 업데이트": issue lifecycle update
- "<issue id> 멈춰줘", "<issue id> pause": issue lifecycle pause
- "<issue id> 다시 시작", "<issue id> resume": issue lifecycle resume
- "<issue id> 완료 처리": issue lifecycle complete

## Mutation Rules

Read-only by default:

- status
- issues list
- doctor
- roadmap view
- portfolio view

Mutate files when the user asks to:

- create an issue
- start/update/pause/resume/complete an issue
- create or update spec/plan/tasks
- execute/review/release
- fix doctor findings
- sync upstream sources

For issue lifecycle mutations, update:

- `issues/<issue>.md`
- `.moduflow/state.json`
- `workspace/dashboard.md`
- `workspace/issues.md` when present
- `workspace/roadmap.md` when priority/state changed

Before creating a new issue, scan existing issues for overlap. If a likely match exists, recommend updating or linking the existing issue instead of creating a duplicate.
