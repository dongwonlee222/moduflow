# Issue 023: Worker Routing And Isolation

**Status: done** — complete.

## Summary

Upgrade worker planning so tasks route to the right worker and parallel execution is based on actual file and dependency isolation, not just worker domain count.

## Source

- Type: internal review + product direction
- Link: user discussion, 2026-06-17
- Date: 2026-06-17

## Lifecycle

- Phase: complete
- Created: 2026-06-17
- Started: 2026-06-19
- Target End:
- Completed: 2026-06-19
- Last Updated: 2026-06-19

## Opportunity

Workers are useful only when ModuFlow can safely split work. Current routing is keyword-order based and parallel eligibility is too coarse. This risks wrong worker selection and file conflicts.

## Scope

### In

- Task metadata for expected files or file globs.
- Worker rule priority and conflict resolution.
- Dead worker detection between `workers/` files and assignment rules.
- Parallel eligibility based on disjoint files, dependencies, and shared-state risk.
- Worktree isolation and merge order design.

### Out

- Full autonomous multi-agent execution without human review.
- Cross-repo parallel execution.

## Acceptance Criteria

- `acceptance` and similar ambiguous keywords route predictably.
- Every worker file is assignable or explicitly marked inactive.
- Parallel mode requires non-overlapping file sets and no shared-state conflict.
- Worker plan includes merge order.
- Unsafe parallel plans fall back to sequential.

## Workflow Tasks

- [x] spec → `specs/023-worker-routing-and-isolation/spec.md`
- [x] plan → `specs/023-worker-routing-and-isolation/plan.md`
- [x] execute → worker_orchestrator and worker docs updates
- [x] review → routing conflict and parallel eligibility tests

## Related Issues

- blocks:
- blocked_by: `019-loop-kernel-and-state-model`, `021-git-binding-and-execution-backend`
- duplicates:
- follows_up: `007-worker-orchestration`
- supersedes: `015-worker-disjoint-isolation`, `016-worker-keyword-and-dead`
- related:

## Sessions

- 2026-06-19: Completed metadata-aware worker routing, file isolation checks, merge order output, and dead-worker detection.
- 2026-06-17: Consolidated worker safety issues under one execution routing issue.

## Links

- Spec: `specs/023-worker-routing-and-isolation/spec.md`
- Status: `specs/023-worker-routing-and-isolation/status.md`
- Sessions: `sessions/023-worker-routing-and-isolation/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:status`
