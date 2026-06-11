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

## Commands

In Codex, call these through `@ModuFlow` without the leading slash, for example `@ModuFlow product:start`.

- `/product:start`: initialize ModuFlow in a project
- `/product:migrate`: safely adopt an existing project without moving files
- `/product:profile`: create project ownership, environment, and integration metadata
- `/product:inbox`: capture raw requests
- `/product:opportunity`: shape the problem/opportunity
- `/product:issue`: create or update a Git issue artifact
- `/product:spec`: create the spec/PRD
- `/product:analyze`: run metrics/data analysis
- `/product:design`: create UX/design brief
- `/product:prototype`: create or review prototype
- `/product:roadmap`: update Now/Next/Later roadmap view
- `/product:plan`: create execution plan and tasks
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

## Validate

```bash
python3 scripts/validate_moduflow.py .
```

For existing projects with their own folder structure, start with a dry-run migration plan:

```bash
python3 scripts/project_migrate.py /path/to/project --mode mapped
```

For project profile metadata, create missing files only:

```bash
python3 scripts/project_profile.py /path/to/project --write
```

See `INSTALL.md` for Claude/Codex install notes.
