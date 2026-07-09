# Issue 078: Frontend QA Template Pack

**Status: in_progress** — created 2026-07-09, spec 2026-07-09, plan 2026-07-09.
**Priority: p2**

## Summary

Add reusable frontend QA planning templates for Storybook required states, MSW fixture catalogs, API contract mapping, Playwright smoke matrices, and QA evidence checklists.

## Source

- Type: user product direction
- Link: local Codex session
- Date: 2026-07-09

## Opportunity

Frontend implementation quality depends on shared examples and verification surfaces. When Storybook states, mocked API fixtures, smoke flows, and QA evidence are not defined before execution, agents can implement UI that looks done but is hard to validate. ModuFlow should make these artifacts easy to request and easy to attach to a plan.

## Scope

### In

- Templates for:
  - Storybook required states
  - MSW fixture catalog
  - API contract mapping
  - Playwright smoke matrix
  - QA evidence checklist
- Guidance for when each template is required, optional, or not applicable.
- Integration into `product:plan`, `product:design`, `product:prototype`, or `product:review` command docs as appropriate.
- Lightweight examples that do not assume a specific frontend framework beyond common web-app concepts.

### Out

- Installing Storybook/MSW/Playwright into target projects.
- Writing project-specific stories or tests.
- Making frontend QA templates mandatory for backend-only issues.
- Building a web UI for template editing.

## Acceptance Criteria

- Template files exist under `templates/` or another established ModuFlow template location.
- Command docs explain when to use each template.
- A frontend issue plan can link to the required states, fixture catalog, smoke matrix, and evidence checklist.
- The templates preserve traceability back to the issue/spec.
- Validation passes with the new templates.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

Starting files/components for the executing agent.

- `templates/`
- `commands/product-plan.md`
- `commands/product-design.md`
- `commands/product-prototype.md`
- `commands/product-review.md`
- `skills/design-prototype-bridge/SKILL.md`

## Scope Fence

Do NOT touch (files, behaviors, or decisions out of bounds for this issue).

- Do not add framework-specific dependencies.
- Do not modify generated dashboard rendering.
- Do not implement the execute readiness gate here; use `077-implementation-readiness-gate`.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/078-frontend-qa-template-pack/spec.md`
- [x] plan → `specs/078-frontend-qa-template-pack/plan.md`
- [x] execute → frontend QA templates, validation list, command docs
- [x] review → `specs/078-frontend-qa-template-pack/review.md`

## Related Issues

- blocks: `077-implementation-readiness-gate`
- blocked_by:
- duplicates:
- follows_up: `046-planning-artifact-templates`, `057-korean-human-review-packet`
- supersedes:
- related: `076-product-context-interview-and-readiness-loop`, `079-plan-discipline-skill-matrix`

## Sessions

- 2026-07-09: User requested Storybook/MSW/Playwright/QA templates as default ModuFlow planning aids for frontend work.

## Links

- Spec: `specs/078-frontend-qa-template-pack/spec.md`
- Status: `specs/078-frontend-qa-template-pack/status.md`
- Sessions: `sessions/078-frontend-qa-template-pack/`
- Roadmap: `workspace/roadmap.md`

## PR

- Draft PR: https://github.com/dongwonlee222/moduflow/pull/15
- Base: `codex/077-implementation-readiness-gate`

## Next Command

`product:pr 078-frontend-qa-template-pack`
