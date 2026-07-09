---
name: pm-execution-router
description: Use when a user gives product, roadmap, issue, spec, execution, PR, release, or stakeholder-update work and ModuFlow should choose the next product command or workflow step.
---

# PM Execution Router

Route requests through the smallest useful ModuFlow step.

## Default Simple Aliases

Prefer these aliases for broad user intent before asking the user to choose among internal workflow commands:

- `상태`, `status`, `현재 상황` → concise `/product:status`.
- `다음`, `next`, `루프` → read-only `/product:loop` recommendation.
- `다음 실행`, `한 단계 진행` → one safe `/product:loop --step` mutation.
- `이거 해줘: <request>` → run intake routing semantics: classify, check overlap, attach to active loop, create/recommend issue candidates, or use inbox with at most one clarification.
- `완료`, `done` → guarded completion; do not close a step or issue unless artifacts and verification gates are present.

Exact `product:*` input (direct product command) is a direct command and should bypass broad alias routing.

## Fast Path Shaping Router

Before creating new product work, choose the smallest useful path:

- **Fast path**: clear, bounded, low-risk requests go directly to `/product:issue`; do not run an interview.
- **Short shaping path**: ambiguous or broad requests ask 1-3 concise questions, then promote the answer to issue/spec/goal context.
- **Panel path**: strategic, high-risk, or product-direction requests may use multiple perspectives internally, but show only the compressed 1-3 user-facing questions.

Never expose raw panel notes. Never make interview mandatory for all issues. If the user asks for speed, create a bounded discovery issue with explicit unknowns instead of blocking.

## Planning Discipline Surface

After `product:spec`, `product:plan` should surface the recommended execution
disciplines for the issue or task streams. The matrix should make implicit
adapter choices visible, for example writing-plans, TDD, product-design,
data-analysis, Storybook/MSW, Playwright/QA, review, and
verification-before-completion. This is guidance only; readiness blocking
belongs to `077-implementation-readiness-gate`.

## Routing

- Raw idea, feedback, bug, or loose note: `/product:inbox` (`inbox`, `인박스`)
- Existing project adoption or different folder structure: `/product:migrate` (`migrate`, `마이그레이션`)
- Project owner, environment, link, or integration metadata: `/product:profile` (`profile`, `프로필`)
- Portable project memory, deliverables, decisions, evidence, meetings, releases, operating notes, or long-term project context: `/product:memory` (`memory`, `메모리`, `장기기억`)
- Legacy knowledge folders, benchmarks, reports, decisions, research, data notes, or references: `/product:knowledge` (`knowledge`, `지식`)
- Evidence review for an issue/spec/roadmap item: `/product:evidence` (`evidence`, `근거`)
- Multi-project overview, central dashboard, or weekly cross-project status: `/product:portfolio` (`portfolio`, `포트폴리오`)
- Current project issue overview: `/product:issues` (`issues`, `이슈목록`, `전체이슈`, `전체 이슈`)
- Team ownership, review state, approval, or handoff: `/product:handoff` (`handoff`, `인수인계`)
- Blockers, risks, or release concerns: `/product:risks` (`risks`, `리스크`)
- Problem shaping: `/product:opportunity` (`opportunity`, `기회`)
- Durable goal above one or more issues: `/product:goal` (`goal`, `목표`)
- Business planning, Lean Canvas, business model, persona scenarios, pitch deck outlines, PDF/PPT export preparation, or business validation issue candidates: `moduflow:business-plan` after `/product:opportunity` when idea shaping is needed
- Durable work item: `/product:issue` (`issue`, `이슈`)
- PRD/spec: `/product:spec` (`spec`, `스펙`)
- Metrics or evidence: `/product:analyze` (`analyze`, `분석`)
- UX or prototype: `/product:design` then `/product:prototype` (`design`, `prototype`, `디자인`, `프로토타입`)
- Priority/timing: `/product:roadmap` (`roadmap`, `로드맵`)
- Implementation preparation: `/product:plan` (`plan`, `계획`)
- Goal-aware next-step routing: `/product:loop` (`loop`, `루프`)
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
- "목표 만들어줘", "현재 목표", "이 목표로 진행": `/product:goal`
- "다음", "다음 단계 알아서 골라줘", "루프 돌려줘": read-only `/product:loop`
- "다음 실행", "한 단계 진행": one safe `/product:loop --step`
- "새 이슈 만들어줘", "이거 이슈로 등록": `/product:issue` after existing-issue check
- "사업계획서", "사업구상", "사업 아이디어", "비즈니스 모델", "린 캔버스", "Lean Canvas": `moduflow:business-plan`; use `/product:opportunity` first if the idea is still raw
- "페르소나", "사용자 시나리오", "고객여정지도": `moduflow:business-plan` persona and journey artifacts
- "사업계획서 PDF", "피치덱", "PPT", "덱 목차": `moduflow:business-plan` export-ready source, then delegate rendering to Documents, Presentations, or PDF plugins
- "검증 이슈로 쪼개줘", "가설을 이슈로 만들어줘": `moduflow:business-plan` then `/product:issue` candidates
- "<issue id> 시작해줘": issue lifecycle start
- "<issue id> 진행 내용 추가", "<issue id> 업데이트": issue lifecycle update
- "<issue id> 멈춰줘", "<issue id> pause": issue lifecycle pause
- "<issue id> 다시 시작", "<issue id> resume": issue lifecycle resume
- "<issue id> 완료 처리": guarded issue lifecycle complete after required artifacts and verification are present

## Mutation Rules

Read-only by default:

- status
- issues list
- doctor
- roadmap view
- portfolio view

Mutate files when the user asks to:

- create an issue
- create or update a goal
- run one safe loop step
- start/update/pause/resume/complete an issue
- create or update spec/plan/tasks
- execute/review/release
- fix doctor findings
- sync upstream sources

For issue lifecycle mutations, update:

- `issues/<issue>.md`
- `.moduflow/state.json`
- `workspace/goal.md` and `workspace/loop-state.json` for goal loop workflows
- `workspace/dashboard.md`
- `workspace/issues.md` when present
- `workspace/roadmap.md` when priority/state changed

Before creating a new issue, scan existing issues for overlap. If a likely match exists, recommend updating or linking the existing issue instead of creating a duplicate. Large multi-domain requests should become a goal plus issue candidates before full issue files are written.
