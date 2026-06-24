---
name: index
description: Use when the ModuFlow plugin is at-mentioned directly, or when the user says product:start, product:goal, product:loop, product:status, start, goal, loop, status, inbox, issue, spec, roadmap, plan, workers, execute, review, release, doctor, business plan, Lean Canvas, persona, user scenario, pitch deck, ModuFlow, 모두플로우, 모두의 플로우, 목표, 루프, 상태, 시작, 이슈, 스펙, 로드맵, 실행, 리뷰, 사업계획서, 사업구상, 비즈니스 모델, 린 캔버스, 페르소나, 사용자 시나리오, PM workflow, roadmap workflow, goal loop workflow, Git issue workflow, or asks to start/manage product execution with Git-native issues and specs.
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
- `@ModuFlow goal`
- `@ModuFlow loop`
- `@ModuFlow issue`
- `@ModuFlow spec`
- `@ModuFlow plan`
- `@ModuFlow workers`
- `@ModuFlow execute`
- `@ModuFlow doctor`
- `@ModuFlow 상태`
- `@ModuFlow 시작`
- `@ModuFlow 목표`
- `@ModuFlow 루프`
- `@ModuFlow 이슈`

## Default Simple Aliases

Resolve these broad user intents before exposing workflow internals:

- `상태`, `status`, `현재 상황` → concise `product:status`.
- `다음`, `next`, `루프` → read-only `product:loop` recommendation.
- `다음 실행`, `한 단계 진행` → one safe `product:loop --step` mutation.
- `이거 해줘: <request>` → use intake routing semantics: classify, check existing issues, attach to active work when related, recommend/create issue candidates for new work, or write an inbox routing record when confidence is low.
- `완료`, `done` → guarded completion; verify required artifacts and validation before closing a step or issue. If gates are missing, recommend the next verification command instead.

Exact `product:*` input (direct product command) is the power-user escape hatch. Honor it directly instead of re-routing through a broad alias.

## Natural Language Invocation

Accept Korean natural language after `@ModuFlow` and route to the smallest useful command or lifecycle action.

Read-only examples:

- `@ModuFlow 상태 보여줘`, `현재 상황 알려줘`, `다음에 뭐 하지?`: `product:status`
- `@ModuFlow 전체 이슈 보여줘`, `이슈 목록`, `진행 중인 이슈 뭐야?`: `product:issues` behavior
- `@ModuFlow 검사해줘`, `doctor 돌려줘`, `설정 괜찮아?`: `product:doctor`
- `@ModuFlow 로드맵 보여줘`, `우선순위 뭐야?`: `product:roadmap`
- `@ModuFlow 목표 뭐야`, `현재 목표`: `product:goal` read/update behavior
- `@ModuFlow 다음`, `다음 단계 알아서 골라줘`, `루프 돌려줘`: read-only `product:loop`
- `@ModuFlow 사업계획서로 정리해줘`, `Lean Canvas 만들어줘`, `페르소나 사용자 시나리오 정리해줘`: use `moduflow:business-plan` after opportunity shaping when structured artifacts are requested

Mutating examples:

- `@ModuFlow 003 시작해줘`, `003 이슈 시작`: issue `003` start
- `@ModuFlow 003에 진행 내용 추가해줘: ...`: issue `003` update
- `@ModuFlow 003 잠시 멈춰줘`: issue `003` pause
- `@ModuFlow 003 다시 시작해줘`: issue `003` resume
- `@ModuFlow 003 완료 처리해줘`: guarded issue `003` completion after required artifacts and verification are present
- `@ModuFlow 새 이슈 만들어줘: ...`: `product:issue`, after checking existing issues
- `@ModuFlow 이 사업계획서를 검증 이슈로 쪼개줘`: `moduflow:business-plan` then `product:issue` candidates

For mutating lifecycle actions, update the issue file, `.moduflow/state.json`, `workspace/dashboard.md`, `workspace/issues.md` when present, and `workspace/roadmap.md` when priority/state changed.

If the target issue is ambiguous, ask one concise clarification before mutating files.

## Command Map

- `product:start`: initialize project artifacts
- `product:migrate`: plan or apply a safe migration for an existing project
- `product:profile`: create or inspect project profile metadata
- `product:memory`: initialize, write, search, or retrieve portable project memory
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
- `product:goal`: create or update an active goal above issues
- `product:issue`: create or update Git issue artifact
- `product:spec`: create spec/PRD
- `product:analyze`: run metrics/data analysis
- `product:design`: create UX/design brief
- `product:prototype`: create or review prototype
- `product:roadmap`: update roadmap view
- `product:plan`: create execution plan/tasks
- `product:loop`: recommend or run the next safe workflow step
- `product:execute`: run implementation workflow
- `product:status`: show state and next action
- `product:review`: review PM/UX/data/QA/release gates
- `product:pr`: prepare PR
- `product:release`: prepare release
- `product:update`: create stakeholder update
- `product:sync`: inspect or update upstream sources
- `product:doctor`: validate setup
- `moduflow:business-plan`: create business-plan artifacts, persona scenarios, diagrams, review outputs, export outlines, and issue/spec candidates

## Short Alias Map

- `start`, `시작`: `product:start`
- `status`, `상태`: `product:status`
- `doctor`, `검사`: `product:doctor`
- `migrate`, `마이그레이션`: `product:migrate`
- `profile`, `프로필`: `product:profile`
- `memory`, `메모리`, `장기기억`: `product:memory`
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
- `goal`, `목표`: `product:goal`
- `issue`, `이슈`: `product:issue`
- `spec`, `스펙`: `product:spec`
- `roadmap`, `로드맵`: `product:roadmap`
- `plan`, `계획`: `product:plan`
- `loop`, `루프`: `product:loop`
- `workers`, `워커`: `product:workers`
- `execute`, `실행`: `product:execute`
- `review`, `리뷰`: `product:review`
- `release`, `릴리즈`: `product:release`
- `business-plan`, `사업계획서`, `사업구상`, `린캔버스`, `페르소나`: `moduflow:business-plan`
- `update`, `공유`: `product:update`

## Behavior

1. Identify the project root before writing files.
2. Run Git preflight before `product:start`, `product:migrate`, `product:profile`, `product:issue`, `product:spec`, `product:plan`, `product:execute`, `product:pr`, or `product:release`.
3. If no project root is clear, ask for the target project.
4. Check existing issues before creating a new issue. For loose requests, use the `moduflow.intake-routing.v1` shape from `scripts/project_intake.py` when available.
5. Keep Git as the source of truth.
6. Treat status, issues, doctor, roadmap, and portfolio as read-only unless the user asks to update/fix.
7. Treat start, update, pause, resume, complete, create, plan, execute, review, release, and sync as mutating workflows.
8. Always end with the next recommended ModuFlow command.
9. Keep the loop wired. `product:start` MUST create `workspace/loop-state.json`. On any command, if `loop-state.json` is missing, treat it as a setup defect and recreate it from `templates/workspace/loop-state.json` before proceeding. Every mutating workflow updates `loop-state.json` (`next_command`, `status`, `last_action`, `updated`) so the next loop step is never lost.
10. Track every artifact as work. No spec, plan, design, or review is produced off the books. Each artifact-producing step is a checked task under the owning issue's **Workflow Tasks** checklist, linked to its file. One issue = one deliverable; workflow steps are tasks inside it, not separate top-level issues (avoids the regress where a "write spec" issue needs its own spec). When you run `product:spec`/`product:plan`/`product:design`/`product:review`, update the corresponding task box + artifact link in the issue.
