# Issue 004: Portfolio Workspace

## Summary

Create a central workspace for tracking multiple ModuFlow projects and building a portfolio-level dashboard.

## Source

- Type: product direction
- Link: user conversation
- Date: 2026-06-11

## Opportunity

Users working across many projects need one place to see active projects, blocked work, upcoming releases, decisions, and next actions.

## Scope

### In

- Define `projects.json` registry.
- Add portfolio dashboard and roadmap templates.
- Add `product:portfolio`, `product:projects`, and `product:weekly` command definitions.
- Read project-local `.moduflow/state.json` and `workspace/dashboard.md` files.

### Out

- Hosted web dashboard.
- Cross-repo writes without explicit user approval.

## Acceptance Criteria

- A central workspace can list multiple project paths.
- Portfolio status can summarize current phase, blockers, next command, and owner for each project.
- The system preserves project-local Git as source of truth.

## Links

- Spec: `specs/004-portfolio-workspace/spec.md`
- Status: `specs/004-portfolio-workspace/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 004-portfolio-workspace`
