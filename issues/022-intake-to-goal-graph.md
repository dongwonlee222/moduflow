# Issue 022: Intake To Goal Graph

**Status: done** — completed 2026-06-18.

## Summary

Turn loose user requests into goal-linked issue graphs across development, planning, design, data, documentation, and operations without forcing users to choose artifact types manually.

## Source

- Type: product direction
- Link: user discussion, 2026-06-17
- Date: 2026-06-17

## Lifecycle

- Phase: completed
- Created: 2026-06-17
- Started: 2026-06-18
- Target End:
- Completed: 2026-06-18
- Last Updated: 2026-06-18

## Opportunity

The plugin should let users say what they want, then classify, attach, split, and prioritize work under a goal. This is the layer that makes ModuFlow useful beyond Spec Kit and coding agents.

## Scope

### In

- Request classification: dev, planning, design, data, docs, ops, research, business.
- Existing goal attachment vs new goal creation decision.
- Duplicate/related/blocks/follows_up detection before creating issues.
- Issue candidate generation from raw notes, business plans, research, and design feedback.
- Roadmap queue update rules.

### Out

- Full semantic search service.
- External product management SaaS sync.

## Acceptance Criteria

- `이거 해줘` can create or attach work with minimal questions.
- Large requests become a goal plus multiple issues.
- Small requests can remain standalone issues.
- Related issues are linked instead of duplicated.
- Roadmap and goal state reflect newly created issue candidates.

## Workflow Tasks

- [x] spec → `specs/022-intake-to-goal-graph/spec.md`
- [x] plan → `specs/022-intake-to-goal-graph/plan.md`
- [x] execute → intake classifier + issue graph creation rules
- [x] review → duplicate/attach/split scenario tests

## Related Issues

- blocks:
- blocked_by: `019-loop-kernel-and-state-model`, `020-user-facing-simple-loop-ux`
- duplicates:
- follows_up: `013-business-plan-skill`
- supersedes:
- related: `003-knowledge-evidence-layer`, `004-portfolio-workspace`

## Sessions

- 2026-06-17: Defined ModuFlow as a plugin that absorbs varied work into goals.
- 2026-06-18: Shipped deterministic intake router, related issue detection, large request issue candidates, and inbox write mode.

## Links

- Spec: `specs/022-intake-to-goal-graph/spec.md`
- Status: `specs/022-intake-to-goal-graph/status.md`
- Sessions: `sessions/022-intake-to-goal-graph/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:status`
