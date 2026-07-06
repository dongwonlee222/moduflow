# Issue 005: Team Workflow

**Status: done** — `scripts/project_workflow.py` shipped in the 0.1.x era; status.md shows all verification passed. Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

Add team-ready workflow states, review gates, roles, approvals, and handoff artifacts.

## Source

- Type: product direction
- Link: user conversation
- Date: 2026-06-11

## Opportunity

When multiple people use ModuFlow, artifacts need explicit ownership, review status, approval history, and release readiness.

## Scope

### In

- Define standard states: draft, ready-for-review, approved, in-progress, blocked, released, archived.
- Define common roles: owner, reviewer, implementer, approver, stakeholder.
- Add review, approval, release, and handoff templates.
- Add `product:handoff` and `product:risks` command definitions.

### Out

- Enterprise permission enforcement.
- Replacing GitHub branch protections.

## Acceptance Criteria

- Issues and specs can show owner, reviewers, approval status, and blockers.
- Release and review flows can be audited from Git artifacts.
- Team workflow remains useful in git-files mode.

## Links

- Spec: `specs/005-team-workflow/spec.md`
- Status: `specs/005-team-workflow/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 005-team-workflow`
