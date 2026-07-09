# Issue 079: Plan Discipline and Skill Matrix

**Status: backlog** — created 2026-07-09.
**Priority: p1**

## Summary

Make `product:plan` automatically surface the recommended Superpowers disciplines and ModuFlow adapter skills for each issue or task, so agents know when to use writing-plans, TDD, review, verification, product design, data analysis, or frontend QA supports.

## Source

- Type: user product direction
- Link: local Codex session
- Date: 2026-07-09

## Opportunity

ModuFlow already contains Superpowers and multiple adapter bridges, but the user currently has to know when each discipline should be activated. Planning should make that explicit. A plan should not only list tasks; it should state the execution discipline that each task needs.

## Scope

### In

- `product:plan` output section for recommended discipline/skill matrix.
- Per-task or per-stream recommendations, for example:
  - writing-plans
  - TDD
  - product-design
  - data-analysis
  - Storybook/MSW
  - Playwright/QA
  - review
  - verification-before-completion
- Mapping guidance based on issue content, expected files, risk, and artifact types.
- Documentation in `skills/superpowers-execution-bridge/SKILL.md` and relevant command docs.
- Non-binding recommendations; the coordinator still applies judgment.

### Out

- Dispatching subagents automatically.
- Hardcoding model names.
- Making every task use every discipline.
- Building a full recommendation engine with external services.

## Acceptance Criteria

- New plans include a visible `Recommended Discipline` or equivalent section.
- The matrix can recommend skills/adapters by task or work stream.
- The matrix distinguishes planning, implementation, QA, review, and verification concerns.
- The recommendation language is host-agnostic and avoids hardcoded model names.
- Existing validation and release checks pass.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

Starting files/components for the executing agent.

- `commands/product-plan.md`
- `skills/superpowers-execution-bridge/SKILL.md`
- `skills/pm-execution-router/SKILL.md`
- `adapters/*.yaml`
- `templates/`
- `scripts/worker_orchestrator.py`

## Scope Fence

Do NOT touch (files, behaviors, or decisions out of bounds for this issue).

- Do not implement execute readiness gates here; use `077-implementation-readiness-gate`.
- Do not add frontend QA template files here; use `078-frontend-qa-template-pack`.
- Do not change issue lifecycle states.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [ ] spec → `specs/079-plan-discipline-skill-matrix/spec.md`
- [ ] plan → `specs/079-plan-discipline-skill-matrix/plan.md`
- [ ] execute → PR / commits
- [ ] review → review notes

## Related Issues

- blocks: `077-implementation-readiness-gate`
- blocked_by:
- duplicates:
- follows_up: `067-upstream-adapter-absorption`, `073-project-constitution-steering`
- supersedes:
- related: `076-product-context-interview-and-readiness-loop`, `078-frontend-qa-template-pack`

## Sessions

- 2026-07-09: User emphasized that ModuFlow already contains Superpowers, but should expose when each discipline should be used during early development planning.

## Links

- Spec: `specs/079-plan-discipline-skill-matrix/spec.md`
- Status: `specs/079-plan-discipline-skill-matrix/status.md`
- Sessions: `sessions/079-plan-discipline-skill-matrix/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 079-plan-discipline-skill-matrix`
