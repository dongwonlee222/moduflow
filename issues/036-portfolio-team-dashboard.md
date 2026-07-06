# Issue 036: Portfolio Team Dashboard

**Status: done** — all workflow tasks checked; status.md shows validation and release checks passed. Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

Reflect per-project team workflow state in portfolio dashboards so small teams can see active work, review queues, blockers, and next actions across projects.

## Source

- Type: user feedback / product direction
- Link: conversation, 2026-06-26
- Date: 2026-06-26

## Lifecycle

- Phase: status
- Created: 2026-06-26
- Started: 2026-06-26
- Target End:
- Completed: 2026-06-26
- Last Updated: 2026-06-26

## Opportunity

Issue 035 added project-local team workflow state, but portfolio dashboards still only showed project state from `.moduflow/state.json`. A small team or TF needs the cross-project 현황판 to show who is working on what and what is waiting for review.

## Scope

### In

- Read each registered project's `workflow/team-state.json` when rendering portfolio status.
- Add active work and review columns to `portfolio-dashboard.md`.
- Add active/review/done team summaries to weekly status.
- Keep project-local Git artifacts as the source of truth.

### Out

- Building a hosted dashboard service.
- Replacing project-local dashboards.
- Requiring GitHub sync.

## Acceptance Criteria

- Portfolio status collection includes active/review/done team summaries per project.
- Portfolio dashboard shows active work and review queue columns.
- Weekly status includes project team workflow summaries.
- Existing portfolio tests and release checks pass.

## Workflow Tasks

- [x] spec -> captured in this issue
- [x] plan -> update `scripts/project_portfolio.py`
- [x] execute -> portfolio team-state collection and rendering
- [x] review -> tests and release checks
- [x] release -> version 0.2.15

## Related Issues

- follows_up: `035-team-issue-branch-pr-workflow`
- related: `024-artifact-schema-and-doctor-gates`

## Sessions

- 2026-06-26: User noted that the team workflow should also be reflected in the project-by-project dashboard.

## Links

- Status: `specs/036-portfolio-team-dashboard/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
