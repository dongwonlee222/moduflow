# ModuFlow

ModuFlow is a Git-native PM execution orchestrator.

It keeps product work in Git, then uses skills/plugins as replaceable adapters:

- Claude Productivity: dashboard/view inspiration
- Claude Product Management: PM artifact patterns
- GitHub Spec Kit: spec, plan, and task structure
- Superpowers: subagent execution, review, and verification
- Codex Product Design: UX brief, ideation, prototype bridge
- Data Analytics: metrics, diagnostics, dashboards, reports
- Documents/Presentations/Spreadsheets: PM-ready artifacts

## Principle

Git is the source of truth. Dashboards, web views, generated docs, and updates are views over Git artifacts.

## Git Preflight

`product:start` must confirm the target project root and Git state before writing project artifacts.

- Local Git repo is required for Spec Kit-style execution.
- GitHub remote and `gh` auth are optional unless issue/PR/release sync is requested.
- Without GitHub sync, ModuFlow runs in `git-files` mode.

## Project Footprint

ModuFlow keeps the project footprint light. A normal target project gets PM artifacts and state only:

```text
.moduflow/
workspace/
issues/
specs/
knowledge/
workflow/
```

Optional project files may be added only when the user asks for that integration, such as `AGENTS.md`, `.github/workflows/`, or project-specific docs.

Tooling stays in the ModuFlow plugin/source package and should not be copied into normal target projects:

```text
commands/
scripts/
skills/
templates/
workers/
adapters/
vendor/
assets/
overlays/
tests/
```

In short: the plugin owns commands, scripts, templates, skills, adapters, and runtime assets; the project owns product-management artifacts, project state, and intentionally selected integration files.

## Commands

**Start here:** `/moduflow` is the single entry point — you only need to remember this one.
Run it with no arguments to see status, the next recommended action, and a quick command list.
Pass natural language to route, for example `/moduflow 시작`, `/moduflow 루프`, `/moduflow 상태`, or `/moduflow 003 완료`.
The `product:*` commands below remain available for direct access.

In Codex, call these through `@ModuFlow` without the leading slash. The default simple surface is:

```text
@ModuFlow 상태
@ModuFlow 다음
@ModuFlow 이거 해줘: 결제 우선순위 정리
@ModuFlow 완료
```

Direct commands remain available for precision, for example `@ModuFlow product:start` or `@ModuFlow product:spec 020-user-facing-simple-loop-ux`.
Short aliases are also supported, for example `@ModuFlow status`, `@ModuFlow issue`, or `@ModuFlow 상태`.

- `/moduflow`: entry point — status, next action, and routing for everything below
- `/product:start`: initialize ModuFlow in a project
- `/product:migrate`: safely adopt an existing project without moving files
- `/product:profile`: create project ownership, environment, and integration metadata
- `/product:knowledge`: initialize knowledge evidence artifacts
- `/product:decision`: create a decision record
- `/product:research`: create a research artifact
- `/product:benchmark`: create a benchmark artifact
- `/product:report`: create a report artifact
- `/product:evidence`: review evidence for an issue or spec
- `/product:portfolio`: initialize or render a multi-project portfolio workspace
- `/product:projects`: inspect registered projects in a portfolio workspace
- `/product:issues`: inspect all issues in the current project
- `/product:weekly`: generate a weekly portfolio status
- `/product:handoff`: initialize team workflow artifacts or create handoff records
- `/product:risks`: inspect blockers, risks, and release concerns
- `/product:inbox`: capture raw requests
- `/product:opportunity`: shape the problem/opportunity
- `/product:goal`: create or update an active goal above issues
- `/product:issue`: create or update a Git issue artifact
- `/product:spec`: create the spec/PRD
- `/product:analyze`: run metrics/data analysis
- `/product:design`: create UX/design brief
- `/product:prototype`: create or review prototype
- `/product:roadmap`: update Now/Next/Later roadmap view
- `/product:plan`: create execution plan and tasks
- `/product:loop`: recommend or run the next safe workflow step for the active goal
- `/product:workers`: generate worker assignment and parallel execution plan
- `/product:execute`: run implementation with Superpowers-style workers
- `/product:status`: show current state and next command
- `/product:review`: run PM/UX/data/QA/release review
- `/product:pr`: prepare GitHub PR
- `/product:release`: prepare release and rollback notes
- `/product:update`: create stakeholder update
- `/product:sync`: update upstream vendor references
- `/product:doctor`: validate local ModuFlow setup

## Source Updates

Upstream sources are tracked in `vendor.lock.json`. Local changes belong in `overlays/` and `adapters/`, so upstream updates can be pulled without rewriting Dongwon-specific process rules.

## Goal Loop

The goal loop is a thin layer above issues. `product:goal` records the objective and completion criteria, while `product:loop` reads Git artifacts and recommends the next existing ModuFlow command. `product:loop --step` may run one safe step, then stops for review.

## Validate

```bash
python3 scripts/validate_moduflow.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/release_check.py .
```

For existing projects with their own folder structure, start with a dry-run migration plan:

```bash
python3 scripts/project_migrate.py /path/to/project --mode mapped
```

For project profile metadata, create missing files only:

```bash
python3 scripts/project_profile.py /path/to/project --write
```

For knowledge evidence artifacts, initialize the structure and create linked evidence:

```bash
python3 scripts/project_knowledge.py /path/to/project --write
python3 scripts/project_knowledge.py /path/to/project --kind decision --title "Payment priority" --issue-id 003-payment
```

For a multi-project portfolio workspace:

```bash
python3 scripts/project_portfolio.py /path/to/portfolio --write
python3 scripts/project_portfolio.py /path/to/portfolio --render
```

For team workflow artifacts:

```bash
python3 scripts/project_workflow.py /path/to/project --write
python3 scripts/project_workflow.py /path/to/project --record --issue-id 005-team-workflow --state ready-for-review --owner "Owner"
```

For worker orchestration:

```bash
python3 scripts/worker_orchestrator.py 007-worker-orchestration --write
```

Worker tasks can declare file/dependency metadata directly in `tasks.md`:

```text
- [ ] Implementation: update planner [files: scripts/worker_orchestrator.py]
- [ ] QA: verify routing [files: tests/test_worker_orchestration.py] [depends: T01]
```

See `INSTALL.md` for Claude/Codex install notes.
