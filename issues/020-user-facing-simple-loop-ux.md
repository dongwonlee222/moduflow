# Issue 020: User-Facing Simple Loop UX

**Status: done** — completed 2026-06-18.

## Summary

Keep ModuFlow simple for plugin users by exposing a tiny natural-language surface while hiding goal, issue, spec, plan, worker, and Git machinery behind the loop.

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

If ModuFlow asks users to choose between goal, issue, spec, plan, workers, roadmap, and Git concepts too early, it becomes more complex than the tools it orchestrates. Installed plugin UX should feel like a PM assistant: status, next, do this, done.

## Scope

### In

- Define default commands/users phrases: `상태`, `다음`, `이거 해줘`, `완료`.
- Route natural language into goal/issue/spec/plan/workers internally.
- Limit clarifying questions to one when safe assumptions are possible.
- Standardize concise status output: current goal, linked issue, next action, decision needed.
- Preserve advanced direct commands for power users.

### Out

- New UI dashboard application.
- Replacing existing `product:*` commands.

## Acceptance Criteria

- New users can start from `@ModuFlow 이거 해줘: ...` without knowing ModuFlow internals.
- `@ModuFlow 다음` runs/recommends one safe loop step.
- `@ModuFlow 상태` shows only high-signal state by default.
- Outputs do not expose internal artifact complexity unless needed.
- Ambiguous requests ask one concise question or create a safe inbox/opportunity entry.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books.

- [x] spec → `specs/020-user-facing-simple-loop-ux/spec.md`
- [x] plan → `specs/020-user-facing-simple-loop-ux/plan.md`
- [x] execute → command/router/skill UX updates
- [x] review → natural-language routing examples and regression checks

## Related Issues

- blocks:
- blocked_by: `019-loop-kernel-and-state-model`
- duplicates:
- follows_up: `009-moduflow-hub-command`
- supersedes:
- related: `022-intake-to-goal-graph`

## Sessions

- 2026-06-17: Established external UX principle: internal graph, external simplicity.

## Links

- Spec: `specs/020-user-facing-simple-loop-ux/spec.md`
- Status: `specs/020-user-facing-simple-loop-ux/status.md`
- Sessions: `sessions/020-user-facing-simple-loop-ux/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 021-git-binding-and-execution-backend`
