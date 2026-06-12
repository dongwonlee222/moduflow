---
name: index
description: Use when the ModuFlow plugin is at-mentioned directly, or when the user says product:start, product:status, start, status, inbox, issue, spec, roadmap, plan, workers, execute, review, release, doctor, ModuFlow, 모두플로우, 모두의 플로우, 상태, 시작, 이슈, 스펙, 로드맵, 실행, 리뷰, PM workflow, roadmap workflow, Git issue workflow, or asks to start/manage product execution with Git-native issues and specs.
---

# ModuFlow Index

ModuFlow routes product work through Git-native artifacts.

## Codex Invocation

Codex reserves leading `/` for native slash commands. Treat these as equivalent:

- `product:start`
- `/product:start`
- `start`
- `시작`
- `ModuFlow 시작`
- `모두플로우 시작`

Prefer short aliases after `@ModuFlow`:

- `@ModuFlow status`
- `@ModuFlow start`
- `@ModuFlow issue`
- `@ModuFlow spec`
- `@ModuFlow plan`
- `@ModuFlow workers`
- `@ModuFlow execute`
- `@ModuFlow doctor`
- `@ModuFlow 상태`
- `@ModuFlow 시작`
- `@ModuFlow 이슈`

## Natural Language Invocation

Accept Korean natural language after `@ModuFlow` and route to the smallest useful command or lifecycle action.

Read-only examples:

- `@ModuFlow 상태 보여줘`, `현재 상황 알려줘`, `다음에 뭐 하지?`: `product:status`
- `@ModuFlow 전체 이슈 보여줘`, `이슈 목록`, `진행 중인 이슈 뭐야?`: `product:issues` behavior
- `@ModuFlow 검사해줘`, `doctor 돌려줘`, `설정 괜찮아?`: `product:doctor`
- `@ModuFlow 로드맵 보여줘`, `우선순위 뭐야?`: `product:roadmap`

Mutating examples:

- `@ModuFlow 003 시작해줘`, `003 이슈 시작`: issue `003` start
- `@ModuFlow 003에 진행 내용 추가해줘: ...`: issue `003` update
- `@ModuFlow 003 잠시 멈춰줘`: issue `003` pause
- `@ModuFlow 003 다시 시작해줘`: issue `003` resume
- `@ModuFlow 003 완료 처리해줘`: issue `003` complete
- `@ModuFlow 새 이슈 만들어줘: ...`: `product:issue`, after checking existing issues

For mutating lifecycle actions, update the issue file, `.moduflow/state.json`, `workspace/dashboard.md`, `workspace/issues.md` when present, and `workspace/roadmap.md` when priority/state changed.

If the target issue is ambiguous, ask one concise clarification before mutating files.

## Command Map

- `product:start`: initialize project artifacts
- `product:migrate`: plan or apply a safe migration for an existing project
- `product:profile`: create or inspect project profile metadata
- `product:knowledge`: initialize or inspect project knowledge artifacts
- `product:decision`: create a decision record
- `product:research`: create a research artifact
- `product:benchmark`: create a benchmark artifact
- `product:report`: create a report artifact
- `product:evidence`: review evidence for an issue or spec
- `product:portfolio`: initialize or render a multi-project portfolio workspace
- `product:projects`: inspect registered projects in a portfolio workspace
- `product:issues`: inspect all issues in the current project
- `product:weekly`: generate a weekly portfolio status
- `product:handoff`: initialize team workflow artifacts or create handoff records
- `product:risks`: inspect blockers, risks, and release concerns
- `product:inbox`: capture raw requests
- `product:opportunity`: shape opportunity/problem
- `product:issue`: create or update Git issue artifact
- `product:spec`: create spec/PRD
- `product:analyze`: run metrics/data analysis
- `product:design`: create UX/design brief
- `product:prototype`: create or review prototype
- `product:roadmap`: update roadmap view
- `product:plan`: create execution plan/tasks
- `product:execute`: run implementation workflow
- `product:status`: show state and next action
- `product:review`: review PM/UX/data/QA/release gates
- `product:pr`: prepare PR
- `product:release`: prepare release
- `product:update`: create stakeholder update
- `product:sync`: inspect or update upstream sources
- `product:doctor`: validate setup

## Short Alias Map

- `start`, `시작`: `product:start`
- `status`, `상태`: `product:status`
- `doctor`, `검사`: `product:doctor`
- `migrate`, `마이그레이션`: `product:migrate`
- `profile`, `프로필`: `product:profile`
- `knowledge`, `지식`: `product:knowledge`
- `decision`, `결정`: `product:decision`
- `research`, `리서치`: `product:research`
- `benchmark`, `벤치마크`: `product:benchmark`
- `report`, `리포트`: `product:report`
- `portfolio`, `포트폴리오`: `product:portfolio`
- `issues`, `이슈목록`, `전체이슈`: `product:issues`
- `weekly`, `주간`: `product:weekly`
- `handoff`, `인수인계`: `product:handoff`
- `risks`, `리스크`: `product:risks`
- `inbox`, `인박스`: `product:inbox`
- `issue`, `이슈`: `product:issue`
- `spec`, `스펙`: `product:spec`
- `roadmap`, `로드맵`: `product:roadmap`
- `plan`, `계획`: `product:plan`
- `workers`, `워커`: `product:workers`
- `execute`, `실행`: `product:execute`
- `review`, `리뷰`: `product:review`
- `release`, `릴리즈`: `product:release`
- `update`, `공유`: `product:update`

## Behavior

1. Identify the project root before writing files.
2. Run Git preflight before `product:start`, `product:migrate`, `product:profile`, `product:issue`, `product:spec`, `product:plan`, `product:execute`, `product:pr`, or `product:release`.
3. If no project root is clear, ask for the target project.
4. Check existing issues before creating a new issue.
5. Keep Git as the source of truth.
6. Treat status, issues, doctor, roadmap, and portfolio as read-only unless the user asks to update/fix.
7. Treat start, update, pause, resume, complete, create, plan, execute, review, release, and sync as mutating workflows.
8. Always end with the next recommended ModuFlow command.
