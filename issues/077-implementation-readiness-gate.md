# Issue 077: Implementation Readiness Gate

**Status: backlog** — created 2026-07-09.
**Priority: p1**

## Summary

Add an implementation-readiness check before `product:execute` so agents do not start implementation until API contracts, test strategy, frontend fixtures, smoke checks, and permission models are explicit enough for reliable execution.

## Source

- Type: user product direction
- Link: local Codex session
- Date: 2026-07-09

## Opportunity

ModuFlow already routes issue → spec → plan → execute, and it already absorbs Superpowers execution discipline. The weak point is the transition into implementation: `product:execute` can begin before the plan has enough concrete execution contracts. This is especially risky for web application work, where unclear API contracts, missing fixtures, and undefined smoke tests cause agents to drift or overbuild.

## Scope

### In

- `product:execute` preflight or command guidance that checks implementation readiness before dispatching work.
- Readiness checklist fields for:
  - API contract mapping
  - test strategy
  - Storybook required states, when frontend UI is in scope
  - MSW fixture baseline, when API-backed UI is in scope
  - Playwright smoke matrix, when user flows are in scope
  - permission/role model, when access control is in scope
  - release/rollback verification condition
- Report-only first version: warn and recommend plan/spec updates rather than blocking all execution.
- Machine-readable readiness result that `product:loop` and future MCP surfaces can read.

### Out

- Making Storybook, MSW, or Playwright mandatory for non-frontend work.
- Running browser tests inside this issue.
- Replacing `product:review` or release gates.
- Introducing app-framework-specific assumptions.

## Acceptance Criteria

- `product:execute` guidance includes an implementation-readiness step before worker dispatch.
- Missing contracts are reported as concrete gaps, not vague warnings.
- Frontend-specific checks apply only when the issue/spec indicates UI work.
- Readiness status can be recorded in `specs/<issue>/status.md` or a nearby machine-readable artifact.
- `product:loop` can recommend returning to `product:plan` when readiness gaps are severe.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

Starting files/components for the executing agent.

- `commands/product-execute.md`
- `commands/product-plan.md`
- `commands/product-loop.md`
- `skills/superpowers-execution-bridge/SKILL.md`
- `scripts/project_execution.py`
- `scripts/spec_consistency.py`
- `templates/`
- `tests/`

## Scope Fence

Do NOT touch (files, behaviors, or decisions out of bounds for this issue).

- Do not make readiness a hard blocker in v1 unless explicitly approved.
- Do not add frontend template pack details here; use `078-frontend-qa-template-pack`.
- Do not rename existing commands.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [ ] spec → `specs/077-implementation-readiness-gate/spec.md`
- [ ] plan → `specs/077-implementation-readiness-gate/plan.md`
- [ ] execute → PR / commits
- [ ] review → review notes

## Related Issues

- blocks:
- blocked_by: `076-product-context-interview-and-readiness-loop`
- duplicates:
- follows_up: `067-upstream-adapter-absorption`, `070-spec-consistency-analyze`
- supersedes:
- related: `078-frontend-qa-template-pack`, `079-plan-discipline-skill-matrix`

## Sessions

- 2026-07-09: User requested execute-before gate coverage for API contracts, test strategy, Storybook/MSW fixtures, Playwright smoke checks, and permission/role models.

## Links

- Spec: `specs/077-implementation-readiness-gate/spec.md`
- Status: `specs/077-implementation-readiness-gate/status.md`
- Sessions: `sessions/077-implementation-readiness-gate/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 077-implementation-readiness-gate`
