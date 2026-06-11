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
4. Keep Git as the source of truth.
5. Always end with the next recommended ModuFlow command.
