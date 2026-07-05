# Issue 019: Loop Kernel And State Model

**Status: done** — completed 2026-06-18.

## Summary

Design and implement the core ModuFlow loop kernel so a plugin-installed user can move from a simple request to goal, issue graph, next action, and completion state without learning internal workflow commands.

## Source

- Type: product direction
- Link: user discussion, 2026-06-17
- Date: 2026-06-17

## Lifecycle

- Phase: completed
- Created: 2026-06-17
- Started:
- Target End:
- Completed: 2026-06-18
- Last Updated: 2026-06-18

## Opportunity

ModuFlow currently has issue, spec, plan, task, worker, and status artifacts, but the loop is mostly instruction-level. Users need one simple PM loop while ModuFlow internally maintains durable state and chooses the next safe step.

## Scope

### In

- Define Project, Roadmap, Goal, Issue, Task, Worker, Git relationships.
- Support Goal 1:N Issue with active issue selection.
- Define loop statuses: active, needs_decision, blocked, done.
- Add attempts and repeated-step guard.
- Decide canonical state ownership between `.moduflow/state.json`, goal state, loop-state, dashboard, and roadmap.
- Make dashboard and roadmap views derived or explicitly reconciled.

### Out

- Full external agent backend execution.
- GitHub issue/PR write automation.
- Worker worktree isolation implementation.

## Acceptance Criteria

- A goal can supervise multiple issues while preserving one active issue and one next command.
- Loop state has a stable cursor/id comparable to a durable thread.
- `product:loop` can recommend the next step from artifacts without asking users to understand internals.
- Repeated identical next actions trip `needs_decision` instead of looping indefinitely.
- Doctor or validation can detect dashboard/state drift.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/019-loop-kernel-and-state-model/spec.md`
- [x] plan → `specs/019-loop-kernel-and-state-model/plan.md`
- [x] execute → loop kernel/state model implementation
- [x] review → loop state drift and attempts guard tests
- [x] release → update plugin cache and install notes if command behavior changes

## Related Issues

- blocks: `020-user-facing-simple-loop-ux`, `021-git-binding-and-execution-backend`, `022-intake-to-goal-graph`, `023-worker-routing-and-isolation`, `024-artifact-schema-and-doctor-gates`
- blocked_by:
- duplicates:
- follows_up: `011-workflow-task-tracking`
- supersedes: `014-loop-attempts-guard`, `017-goal-multi-issue`, `018-state-single-source`
- related: `008-daily-work-log-and-gbrain-pilot`

## Sessions

- 2026-06-17: Defined ModuFlow as a user-simple goal-loop PM orchestrator.

## Links

- Spec: `specs/019-loop-kernel-and-state-model/spec.md`
- Status: `specs/019-loop-kernel-and-state-model/status.md`
- Sessions: `sessions/019-loop-kernel-and-state-model/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 020-user-facing-simple-loop-ux`
