# Portfolio Workspace Spec

## Problem

Project-local ModuFlow state is useful, but users working across many projects need one central place to see active work, blockers, next commands, and project ownership.

## Users

- Owners managing multiple ModuFlow projects.
- Agents preparing weekly summaries or portfolio status.
- Team members scanning cross-project progress.

## Goals

- Add a central portfolio workspace structure.
- Define a `projects.json` registry.
- Read project-local `.moduflow/state.json`, `.moduflow/project-profile.md`, and `workspace/dashboard.md`.
- Render portfolio dashboard and weekly status files.
- Preserve project-local Git as the source of truth.

## Non-Goals

- Hosted web dashboard.
- Cross-repo writes without explicit user approval.
- Replacing project-local issue/spec artifacts.

## Artifact Structure

```text
portfolio/
  projects.json
  portfolio-dashboard.md
  portfolio-roadmap.md
  weekly-status.md
```

## Requirements

- `scripts/project_portfolio.py` supports dry-run workspace initialization.
- `scripts/project_portfolio.py --write` creates missing portfolio files only.
- `projects.json` contains project `id`, `name`, `path`, `status`, and `owner`.
- Portfolio status reads each project `.moduflow/state.json`.
- Portfolio status reads owner from `projects.json` first, then project profile when present.
- Existing files are never overwritten.
- Commands exist for `product:portfolio`, `product:projects`, and `product:weekly`.

## Acceptance Criteria

- A portfolio workspace can list multiple project paths.
- Dashboard rendering includes project phase, blockers, next command, owner, and path.
- Missing project files are represented as warnings instead of hard failures.
- Validator requires the new commands, script, and templates.

## Next Command

`product:plan 004-portfolio-workspace`
