# ModuFlow

ModuFlow is a product execution loop that helps AI agents keep product context from goal to execution and verification.

In Korean:

```text
모두플로는 AI가 제품 맥락을 잊지 않고 목표부터 실행, 검증까지 이어가게 해주는 작업 루프입니다.
```

It connects ideas to goals, specs, issues, execution plans, reviews, and releases. Every work record is kept as Markdown/JSON inside the repo and versioned with Git, so product intent, decisions, evidence, and next actions survive across agent sessions.

## Method

ModuFlow keeps AI work aligned through five operating methods:

- **Spec-first planning**: clarify the goal, scope, non-goals, and acceptance criteria before asking an agent to build.
- **Issue-driven execution**: split product intent into traceable issues, plans, tasks, and worker handoffs.
- **Review-gated completion**: do not accept "done" until review, verification, and release evidence are recorded.
- **Evidence-based decisions**: keep decisions, benchmarks, analysis, and context as durable repo files.
- **Git-versioned memory**: treat the repo as the durable record for goals, specs, issues, reviews, and releases.

## Adapter Sources

ModuFlow uses external workflow sources through replaceable adapters tracked in `vendor.lock.json` and `adapters/*.yaml`:

- GitHub Spec Kit: spec, plan, and task structure.
- Superpowers: brainstorming, planning, TDD, subagent execution, review, and verification discipline.
- Anthropic Knowledge Work Plugins: product-management and productivity workflow patterns.
- Codex Product Design: UX brief, ideation, prototype, and image-to-code bridge.
- Codex Data Analytics: KPI design, metric diagnostics, dashboards, and reports.
- Codex Documents / Presentations / Spreadsheets: docx/xlsx/pptx artifact output bridge.

ModuFlow is packaged for both Claude and Codex (`.claude-plugin/` and `.codex-plugin/`). The adapters keep those upstream workflows replaceable while preserving the same ModuFlow product loop.

## Principle

Git is the source of truth. Dashboards, web views, generated docs, and updates are views over repo files, not separate product state.

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
memory/
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

### Core path (start here — these five cover a whole work cycle)

- `/moduflow`: entry point — status, next action, and routing for everything below
- `/product:start`: initialize ModuFlow in a project
- `/product:goal`: create or update an active goal above issues
- `/product:issue`: create or update a Git issue artifact
- `/product:status`: show current state and next command
- `/product:loop`: recommend or run the next safe workflow step — when unsure, run this

### Build cycle (the loop recommends these when an issue is ready to move)

- `/product:spec`: create the spec/PRD
- `/product:plan`: create execution plan and tasks
- `/product:execute`: run implementation with Superpowers-style workers
- `/product:review`: run PM/UX/data/QA/release review
- `/product:pr`: prepare GitHub PR
- `/product:release`: prepare release and rollback notes

### On-demand (reach for these when the work calls for them)

- Intake and shaping: `/product:inbox` (capture raw requests), `/product:opportunity` (shape the problem)
- Evidence and knowledge: `/product:knowledge`, `/product:memory`, `/product:production` (recurring production records/playbooks), `/product:decision`, `/product:research`, `/product:benchmark`, `/product:report`, `/product:evidence`
- Analysis and design: `/product:analyze` (metrics/data), `/product:design` (UX brief), `/product:prototype`
- Views and planning: `/product:roadmap` (Now/Next/Later), `/product:issues` (inspect all issues), `/product:risks` (blockers and release concerns)
- Portfolio and team: `/product:portfolio`, `/product:projects`, `/product:weekly`, `/product:handoff`, `/product:update` (stakeholder update), `/product:workers` (parallel execution plan)
- Project setup and health: `/product:migrate` (adopt an existing project), `/product:profile`, `/product:memory`, `/product:sync` (upstream vendor references), `/product:doctor` (validate setup)

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

For portable project memory, initialize the structure and create searchable entries:

```bash
python3 scripts/project_memory.py /path/to/project --write
python3 scripts/project_memory.py /path/to/project --kind decision --title "Use repo-local memory" --issue-id 030-project-memory-layer --summary "Keep memory portable inside the repo."
python3 scripts/project_memory.py /path/to/project --search "portable memory"
```

For recurring production records and human-approved playbooks:

```bash
python3 scripts/project_production.py /path/to/project --init
python3 scripts/project_production.py /path/to/project --search "mobile banner" --type banner --channel home-popup
```

For legacy knowledge evidence artifacts, initialize the structure and create linked evidence:

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
